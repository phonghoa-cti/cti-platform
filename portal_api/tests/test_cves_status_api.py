from __future__ import annotations

import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.cves_status import CveStatusStore
from portal_api.technologies import TechnologyStore
from portal_api.tests import test_w02_ioc_api as w02
from portal_api.tests.test_w02_ioc_api import LocalJwksClient, _auth, _settings


@pytest.fixture(scope="session")
def rsa_keys():
    return w02.rsa_keys.__wrapped__()


class StaticPort:
    def __init__(self):
        self.calls = 0
        self.dataset = {
            "kind": "synthetic",
            "kev_snapshot_complete": True,
            "source_as_of": "2026-11-01T00:00:00Z",
            "retrieved_at": "2026-11-01T01:00:00Z",
            "candidates": [
                {
                    "cve_id": "CVE-2026-2001",
                    "title": "Synthetic CVE",
                    "affected_products": [{"vendor": "Fortinet", "product": "FortiOS"}],
                    "kev": {
                        "known_exploited": True,
                        "source": "CISA KEV synthetic sample",
                        "as_of": "2026-11-01",
                        "due_date": "2026-11-15",
                    },
                    "epss": {"score": 0.9, "percentile": 0.95, "as_of": "2026-11-01"},
                    "cvss": {"base_score": 9.8, "version": "3.1"},
                    "published_at": "2026-10-01T00:00:00Z",
                    "advisory_url": "https://example.invalid/CVE-2026-2001",
                }
            ],
        }

    def list_candidates(self):
        self.calls += 1
        return copy.deepcopy(self.dataset)


def _setup(tmp_path, rsa_keys):
    tech = TechnologyStore(tmp_path / "status.sqlite", timeout=0.2)
    tech.initialize()
    technology = tech.create("Fortinet", "FortiOS", "7.2", "private", "seed")
    status = CveStatusStore(tech.path, timeout=0.2)
    status.initialize()
    port = StaticPort()
    settings = replace(
        _settings(tmp_path),
        roles_by_subject={
            "it-sub": frozenset({"it"}),
            "leader-sub": frozenset({"leader"}),
            "viewer-sub": frozenset({"viewer"}),
        },
    )
    private_key, jwk = rsa_keys
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(
        create_app(
            settings,
            object(),
            verifier=verifier,
            cve_port=port,
            technology_store=tech,
            cve_status_store=status,
        ),
        raise_server_exceptions=False,
    )
    return client, private_key, tech, status, port, technology


def _path(technology_id=1):
    return f"/api/cves/CVE-2026-2001/technologies/{technology_id}/status"


def _headers(key, subject="it-sub"):
    return {
        **_auth(key, subject),
        "origin": "https://portal.synthetic.test",
        "content-type": "application/json",
    }


def _body(context, version=0, status="open", note="Đã kiểm tra"):
    return {
        "status": status,
        "note": note,
        "expected_status_version": version,
        "expected_technology_record_version": context["technology_record_version"],
        "expected_dataset_id": context["dataset_id"],
    }


def _snapshot(path):
    with sqlite3.connect(path) as connection:
        return (
            connection.execute("SELECT * FROM cve_status_records").fetchall(),
            connection.execute("SELECT * FROM cve_status_audit").fetchall(),
        )


def _wire(response):
    return {
        "status": response.status_code,
        "headers": {"cache-control": response.headers["cache-control"], "vary": response.headers["vary"]},
        "body": response.json(),
    }


def test_unset_commit_history_and_stale_replay(tmp_path, rsa_keys):
    client, key, _tech, status, port, technology = _setup(tmp_path, rsa_keys)
    unset = client.get(_path(technology.id), headers=_auth(key))
    context = unset.json()["context"]
    committed = client.put(_path(), headers=_headers(key), json=_body(context))
    replay = client.put(_path(), headers=_headers(key), json=_body(context))
    history = client.get(_path() + "-history?limit=25", headers=_auth(key))
    assert unset.status_code == 200 and unset.json()["record"] is None
    assert committed.status_code == 200 and committed.json()["record"]["status_version"] == 1
    assert committed.json()["record"]["updated_by"] == "it-sub" and committed.json()["audit_id"] == 1
    assert (replay.status_code, replay.json()["error"]["code"]) == (409, "status_version_conflict")
    assert history.json()["items"][0]["event"] == "created" and history.json()["items"][0]["before"] is None
    assert port.calls == 4 and len(_snapshot(status.path)[1]) == 1


def test_context_drift_is_409_without_status_mutation_and_get_marks_review(tmp_path, rsa_keys):
    client, key, tech, status, _port, technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    assert client.put(_path(), headers=_headers(key), json=_body(context)).status_code == 200
    before = _snapshot(status.path)
    tech.update(technology.id, "Fortinet", "FortiOS", "7.2", "changed", 1, "seed")
    stale = client.put(_path(), headers=_headers(key), json=_body(context, 1, "patched"))
    read = client.get(_path(), headers=_auth(key))
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "status_context_changed")
    assert read.status_code == 200 and read.json()["review_required"] is True
    assert _snapshot(status.path) == before


def test_transitions_reopen_same_state_and_first_write_race(tmp_path, rsa_keys):
    client, key, _tech, status, _port, _technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    for version, state in enumerate(("open", "patching", "patched", "not_affected", "open", "open")):
        response = client.put(
            _path(), headers=_headers(key), json=_body(context, version, state, f"note-{version}")
        )
        assert response.status_code == 200 and response.json()["record"]["status_version"] == version + 1
    assert len(_snapshot(status.path)[1]) == 6

    other = TechnologyStore(tmp_path / "race.sqlite", timeout=1)
    other.initialize()
    other.create("Fortinet", "FortiOS", "7.2", "x", "seed")
    race_store = CveStatusStore(other.path, timeout=1)
    race_store.initialize()
    ctx = context | {"technology_id": 1, "technology_record_version": 1}

    def write(note):
        try:
            return race_store.put("CVE-2026-2001", 1, ctx, "open", note, 0, "it-sub")[1]
        except Exception as exc:
            return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, ("one", "two")))
    assert sorted(str(value) for value in results) == ["1", "StatusVersionConflict"]
    assert tuple(map(len, _snapshot(other.path))) == (1, 1)


def test_auth_protocol_bounds_and_unconfigured_fail_closed(tmp_path, rsa_keys):
    client, key, tech, status, port, technology = _setup(tmp_path, rsa_keys)
    before = _snapshot(status.path)
    assert client.get(_path() + "?bad=1").status_code == 401
    assert client.get(_path() + "?bad=1", headers=_auth(key, "leader-sub")).status_code == 403
    assert client.get(_path(), headers=_auth(key, "viewer-sub")).status_code == 403
    assert port.calls == 0
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    bad_origin = client.put(
        _path(), headers={**_auth(key), "content-type": "application/json"}, json=_body(context)
    )
    bad_media = client.put(
        _path(), headers={**_auth(key), "origin": "https://portal.synthetic.test"}, content=b"{}"
    )
    extra = client.put(_path(), headers=_headers(key), json={**_body(context), "actor": "forged"})
    huge = client.put(_path(), headers=_headers(key), content=b'{"note":"' + b"a" * 17000 + b'"}')
    assert [(x.status_code, x.json()["error"]["code"]) for x in (bad_origin, bad_media, extra, huge)] == [
        (403, "forbidden"),
        (415, "unsupported_media_type"),
        (422, "invalid_status_request"),
        (413, "request_too_large"),
    ]
    assert _snapshot(status.path) == before
    settings = _settings(tmp_path)
    private_key, jwk = rsa_keys
    no_status = TestClient(
        create_app(
            settings,
            object(),
            verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk)),
            cve_port=port,
            technology_store=tech,
        ),
        raise_server_exceptions=False,
    )
    unavailable = no_status.get(_path(technology.id), headers=_auth(private_key))
    assert (unavailable.status_code, unavailable.json()["error"]["code"]) == (503, "status_unavailable")


def test_history_pages_and_cursor_snapshot_conflict(tmp_path, rsa_keys):
    client, key, _tech, _status, _port, _technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    for version, state in enumerate(("open", "patching", "patched")):
        assert (
            client.put(
                _path(), headers=_headers(key), json=_body(context, version, state, str(version))
            ).status_code
            == 200
        )
    first = client.get(_path() + "-history?limit=2", headers=_auth(key))
    cursor = first.json()["page"]["next_cursor"]
    second = client.get(_path() + f"-history?limit=2&cursor={cursor}", headers=_auth(key))
    assert [x["audit_id"] for x in first.json()["items"]] == [3, 2]
    assert [x["audit_id"] for x in second.json()["items"]] == [1]
    assert (
        client.put(_path(), headers=_headers(key), json=_body(context, 3, "open", "new")).status_code == 200
    )
    stale = client.get(_path() + f"-history?limit=2&cursor={cursor}", headers=_auth(key))
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "status_snapshot_changed")


def test_failure_between_status_and_audit_and_response_cap_roll_back(tmp_path, rsa_keys, monkeypatch):
    client, key, _tech, status, _port, _technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    before = _snapshot(status.path)

    def fail_audit(*_args):
        raise sqlite3.OperationalError("synthetic audit failure")

    monkeypatch.setattr(CveStatusStore, "_insert_audit", staticmethod(fail_audit))
    failed = client.put(_path(), headers=_headers(key), json=_body(context))
    assert (failed.status_code, failed.json()["error"]["code"]) == (503, "status_unavailable")
    assert _snapshot(status.path) == before

    monkeypatch.undo()
    import portal_api.cves_status as status_module

    monkeypatch.setattr(status_module, "MAX_RESPONSE_BYTES", 1)
    capped = client.put(_path(), headers=_headers(key), json=_body(context))
    assert (capped.status_code, capped.json()["error"]["code"]) == (503, "status_unavailable")
    assert _snapshot(status.path) == before


def test_schema_damage_dataset_and_identity_drift_fail_closed(tmp_path, rsa_keys):
    client, key, tech, status, port, technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    assert client.put(_path(), headers=_headers(key), json=_body(context)).status_code == 200
    before = _snapshot(status.path)

    port.dataset["retrieved_at"] = "2026-11-01T02:00:00Z"
    drifted = client.get(_path(), headers=_auth(key))
    assert drifted.status_code == 200 and drifted.json()["review_required"] is True
    stale_dataset = client.put(_path(), headers=_headers(key), json=_body(context, 1, "patched"))
    assert (stale_dataset.status_code, stale_dataset.json()["error"]["code"]) == (
        409,
        "status_context_changed",
    )
    assert _snapshot(status.path) == before

    tech.update(technology.id, "Other", "Product", "1", "changed", 1, "seed")
    missing = client.get(_path(), headers=_auth(key))
    changed = client.put(_path(), headers=_headers(key), json=_body(context, 1, "patched"))
    assert (missing.status_code, missing.json()["error"]["code"]) == (404, "status_relation_not_found")
    assert (changed.status_code, changed.json()["error"]["code"]) == (409, "status_context_changed")
    assert _snapshot(status.path) == before

    tech.update(technology.id, "Fortinet", "FortiOS", "7.2", "restored", 2, "seed")
    with sqlite3.connect(status.path) as connection:
        connection.execute("UPDATE w03_status_migrations SET version=2")
    unavailable = client.get(_path(), headers=_auth(key))
    assert (unavailable.status_code, unavailable.json()["error"]["code"]) == (503, "status_unavailable")


@pytest.mark.parametrize("query", ["?limit=0", "?limit=101", "?limit=1&limit=2", "?cursor=%%%", "?other=1"])
def test_history_rejects_invalid_query_and_cursor(tmp_path, rsa_keys, query):
    client, key, _tech, status, _port, _technology = _setup(tmp_path, rsa_keys)
    before = _snapshot(status.path)
    response = client.get(_path() + "-history" + query, headers=_auth(key))
    assert (response.status_code, response.json()["error"]["code"]) == (422, "invalid_status_request")
    assert _snapshot(status.path) == before


def test_note_controls_actor_forgery_and_safe_integer_bounds_do_not_write(tmp_path, rsa_keys):
    client, key, _tech, status, _port, _technology = _setup(tmp_path, rsa_keys)
    context = client.get(_path(), headers=_auth(key)).json()["context"]
    before = _snapshot(status.path)
    bodies = [
        _body(context) | {"note": "bad\u0085note"},
        _body(context) | {"note": "x" * 1001},
        _body(context) | {"expected_status_version": True},
        _body(context) | {"expected_status_version": 2**53},
        _body(context) | {"updated_by": "forged"},
    ]
    for body in bodies:
        response = client.put(_path(), headers=_headers(key), json=body)
        assert (response.status_code, response.json()["error"]["code"]) == (422, "invalid_status_request")
    assert _snapshot(status.path) == before


def test_checked_in_status_wire_fixtures_come_from_real_api(tmp_path, rsa_keys, monkeypatch):
    import portal_api.cves_status as status_module

    monkeypatch.setattr(status_module, "_now", lambda: "2026-11-12T00:00:00.000000Z")
    client, key, tech, _status, port, _technology = _setup(tmp_path, rsa_keys)
    fixture_dir = Path(__file__).parent / "fixtures"
    unset = _wire(client.get(_path(), headers=_auth(key)))
    context = unset["body"]["context"]
    committed = _wire(client.put(_path(), headers=_headers(key), json=_body(context)))
    for version, state in ((1, "patching"), (2, "patched")):
        client.put(_path(), headers=_headers(key), json=_body(context, version, state, f"note-{version}"))
    page1 = _wire(client.get(_path() + "-history?limit=2", headers=_auth(key)))
    cursor = page1["body"]["page"]["next_cursor"]
    page2 = _wire(client.get(_path() + f"-history?limit=2&cursor={cursor}", headers=_auth(key)))
    conflict = _wire(client.put(_path(), headers=_headers(key), json=_body(context)))
    tech.update(1, "Fortinet", "FortiOS", "7.2", "changed", 1, "seed")
    review = _wire(client.get(_path(), headers=_auth(key)))
    settings = _settings(tmp_path)
    private_key, jwk = rsa_keys
    no_status = TestClient(
        create_app(
            settings,
            object(),
            verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk)),
            cve_port=port,
            technology_store=tech,
        ),
        raise_server_exceptions=False,
    )
    unavailable = _wire(no_status.get(_path(), headers=_auth(private_key)))
    actual = {
        "unset": unset,
        "committed": committed,
        "review-required": review,
        "history-2pages": {"page1": page1, "page2": page2},
        "conflict": conflict,
        "unavailable": unavailable,
    }
    for name, response in actual.items():
        expected = json.loads((fixture_dir / f"w03-status-{name}.json").read_text(encoding="utf-8"))
        assert response == expected
