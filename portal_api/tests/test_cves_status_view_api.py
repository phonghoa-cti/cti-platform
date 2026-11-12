from __future__ import annotations

import base64
import copy
import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.cves import CveDataset
from portal_api.cves_status import CveStatusStore
from portal_api.technologies import TechnologyStore
from portal_api.tests import test_w02_ioc_api as w02
from portal_api.tests.test_w02_ioc_api import LocalJwksClient, _auth, _settings


@pytest.fixture(scope="session")
def rsa_keys():
    return w02.rsa_keys.__wrapped__()


class StaticPort:
    def __init__(self, candidates):
        self.calls = 0
        self.dataset = {
            "kind": "synthetic",
            "kev_snapshot_complete": True,
            "source_as_of": "2026-11-01T00:00:00Z",
            "retrieved_at": "2026-11-01T01:00:00Z",
            "candidates": candidates,
        }

    def list_candidates(self):
        self.calls += 1
        value = copy.deepcopy(self.dataset)
        dataset_id = value.pop("dataset_id", "sha256:" + "a" * 64)
        return CveDataset(**value, dataset_id=dataset_id)


def _candidate(cve_id, *, product="FortiOS", kev=True, due="2026-11-11", epss=0.9):
    return {
        "cve_id": cve_id,
        "title": f"Synthetic {cve_id}",
        "affected_products": [{"vendor": "Fortinet", "product": product}],
        "kev": {
            "known_exploited": kev,
            "source": "CISA KEV synthetic sample",
            "as_of": "2026-11-01",
            "due_date": due if kev else None,
        },
        "epss": {"score": epss, "percentile": epss, "as_of": "2026-11-01"},
        "cvss": {"base_score": 9.0, "version": "3.1"},
        "published_at": "2026-10-01T00:00:00Z",
        "advisory_url": f"https://example.invalid/{cve_id}",
    }


def _setup(tmp_path, rsa_keys, *, candidates=None, clock=None):
    technology = TechnologyStore(tmp_path / "status-view.sqlite", timeout=0.2)
    technology.initialize()
    first = technology.create("Fortinet", "FortiOS", "7.2", "private", "seed")
    second = technology.create("Fortinet", "FortiOS", "7.4", "private", "seed")
    technology.create("Fortinet", "FortiProxy", "7.2", "private", "seed")
    status = CveStatusStore(technology.path, timeout=0.2)
    status.initialize()
    with sqlite3.connect(technology.path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
    port = StaticPort(
        candidates
        or [
            _candidate("CVE-2026-3001"),
            _candidate("CVE-2026-3002", due="2026-11-12", epss=0.8),
            _candidate("CVE-2026-3003", kev=False, due=None, epss=0.7),
        ]
    )
    roles = {
        "it-sub": frozenset({"it"}),
        "leader-sub": frozenset({"leader"}),
        "mixed-sub": frozenset({"leader", "analyst"}),
        "viewer-sub": frozenset({"viewer"}),
    }
    settings = replace(_settings(tmp_path), roles_by_subject=roles)
    private_key, jwk = rsa_keys
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(
        create_app(
            settings,
            object(),
            verifier=verifier,
            cve_port=port,
            technology_store=technology,
            cve_status_store=status,
            cve_status_view_clock=clock or (lambda: datetime(2026, 11, 12, 0, 0, tzinfo=UTC)),
        ),
        raise_server_exceptions=False,
    )
    return client, private_key, technology, status, port, first, second


def _get(client, key, query="", subject="it-sub"):
    return client.get(f"/api/cves/status-view{query}", headers=_auth(key, subject))


def _context(technology, cve_id="CVE-2026-3001", dataset_id="sha256:" + "a" * 64):
    return {
        "technology_id": technology.id,
        "cve_id": cve_id,
        "vendor": technology.vendor,
        "product": technology.product,
        "software_version": technology.software_version,
        "technology_record_version": technology.version,
        "dataset_id": dataset_id,
    }


def _insert_status(store, technology, status, *, cve_id="CVE-2026-3001", stale=False):
    context = _context(technology, cve_id)
    if stale:
        context["technology_record_version"] = technology.version + 1
    record = {
        "status": status,
        "status_version": 1,
        "note": "private note",
        "updated_at": "2026-11-01T00:00:00Z",
        "updated_by": "analyst-sub",
        "context": context,
    }
    raw = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    after = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "INSERT INTO cve_status_records VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                technology.id,
                cve_id,
                technology.vendor.casefold(),
                technology.product.casefold(),
                status,
                1,
                "private note",
                "2026-11-01T00:00:00Z",
                "analyst-sub",
                raw,
            ),
        )
        connection.execute(
            "INSERT INTO cve_status_audit"
            "(technology_id,cve_id,vendor_key,product_key,event,before_json,after_json)"
            " VALUES(?,?,?,?, 'created',NULL,?)",
            (
                technology.id,
                cve_id,
                technology.vendor.casefold(),
                technology.product.casefold(),
                after,
            ),
        )


def _db_snapshot(path):
    with sqlite3.connect(path) as connection:
        return {
            "schema": connection.execute(
                "SELECT type,name,sql FROM sqlite_master ORDER BY type,name"
            ).fetchall(),
            "technology": connection.execute("SELECT * FROM technology_assets").fetchall(),
            "technology_audit": connection.execute("SELECT * FROM technology_asset_audit").fetchall(),
            "status": connection.execute("SELECT * FROM cve_status_records").fetchall(),
            "status_audit": connection.execute("SELECT * FROM cve_status_audit").fetchall(),
        }


def _decode(cursor):
    raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
    return json.loads(raw)


def _encode(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _wire(response):
    return {
        "status": response.status_code,
        "headers": {
            "cache-control": response.headers["cache-control"],
            "vary": response.headers["vary"],
        },
        "body": response.json(),
    }


def test_auth_leader_forbidden_filters_and_query_errors_precede_dependencies(tmp_path, rsa_keys):
    client, key, _technology, _status, port, _first, _second = _setup(tmp_path, rsa_keys)

    responses = [
        client.get("/api/cves/status-view?bad=1"),
        _get(client, key, "?bad=1", "viewer-sub"),
        _get(client, key, "?asset_id=nope", "leader-sub"),
        _get(client, key, "?status=nope", "leader-sub"),
    ]

    assert [(item.status_code, item.json()["error"]["code"]) for item in responses] == [
        (401, "authentication_required"),
        (403, "forbidden"),
        (403, "forbidden"),
        (403, "forbidden"),
    ]
    assert port.calls == 0


def test_detail_multi_relation_filter_counts_due_rank_and_mixed_role(tmp_path, rsa_keys):
    client, key, _technology, status_store, port, first, second = _setup(tmp_path, rsa_keys)
    dataset_id = "sha256:" + "a" * 64
    port.dataset["dataset_id"] = dataset_id
    _insert_status(status_store, first, "patched")
    _insert_status(status_store, second, "open", stale=True)

    response = _get(client, key, "?status=review_required&limit=100", "mixed-sub")

    assert response.status_code == 200
    body = response.json()
    assert [item["cve_id"] for item in body["items"]] == ["CVE-2026-3001"]
    assert [match["status"] for match in body["items"][0]["matches"]] == ["patched", "open"]
    assert body["items"][0]["matches"][1]["review_required"] is True
    assert body["summary"] == {
        "matched_cves": 3,
        "kev_cves": 2,
        "status_relations": {"unset": 4, "open": 1, "patching": 0, "patched": 1, "not_affected": 0},
        "review_required_relations": 1,
        "actionable_cves": 3,
        "overdue_kev_cves": 1,
        "as_of_date": "2026-11-12",
    }
    assert port.calls == 1


def test_leader_projection_is_exact_and_status_free(tmp_path, rsa_keys):
    client, key, _technology, status_store, _port, first, _second = _setup(tmp_path, rsa_keys)
    _insert_status(status_store, first, "open")

    response = _get(client, key, "?limit=1", "leader-sub")

    assert response.status_code == 200
    assert response.json()["view"] == "summary"
    assert set(response.json()["summary"]) == {
        "matched_cves",
        "kev_cves",
        "actionable_cves",
        "overdue_kev_cves",
        "as_of_date",
    }
    assert set(response.json()["items"][0]) == {
        "cve_id",
        "title",
        "kev",
        "epss_score",
        "cvss_base_score",
        "priority",
        "match_count",
    }
    assert "private note" not in response.text
    assert "analyst-sub" not in response.text


def test_cursor_context_cross_route_and_snapshot_changes(tmp_path, rsa_keys):
    day = [datetime(2026, 11, 12, tzinfo=UTC)]
    client, key, technology, status_store, port, first, _second = _setup(
        tmp_path, rsa_keys, clock=lambda: day[0]
    )
    first_page = _get(client, key, "?limit=1")
    cursor = first_page.json()["page"]["next_cursor"]
    decoded = _decode(cursor)
    assert decoded["kind"] == "w03-status-view"
    assert "as_of_date" not in decoded["context"]
    assert decoded["snapshot"]["as_of_date"] == "2026-11-12"

    wrong_context = _get(client, key, f"?limit=2&cursor={cursor}")
    cross_route = _get(client, key, "?cursor=eyJ2IjoxfQ")
    day[0] = datetime(2026, 11, 13, tzinfo=UTC)
    date_changed = _get(client, key, f"?limit=1&cursor={cursor}")
    day[0] = datetime(2026, 11, 12, tzinfo=UTC)
    _insert_status(status_store, first, "open", cve_id="CVE-2026-3002")
    status_changed = _get(client, key, f"?limit=1&cursor={cursor}")
    port.dataset["candidates"].append(_candidate("CVE-2026-3999"))
    dataset_changed = _get(client, key, f"?limit=1&cursor={cursor}")
    technology.update(first.id, "Fortinet", "FortiOS", "7.2.1", "private", first.version, "seed")
    technology_changed = _get(client, key, f"?limit=1&cursor={cursor}")

    assert [(item.status_code, item.json()["error"]["code"]) for item in (wrong_context, cross_route)] == [
        (422, "invalid_cve_status_query"),
        (422, "invalid_cve_status_query"),
    ]
    assert all(
        (item.status_code, item.json()["error"]["code"]) == (409, "status_snapshot_changed")
        for item in (date_changed, status_changed, dataset_changed, technology_changed)
    )


def test_malformed_rows_schema_missing_asset_cap_and_get_are_fail_closed_read_only(
    tmp_path, rsa_keys, monkeypatch
):
    client, key, technology, status_store, _port, first, _second = _setup(tmp_path, rsa_keys)
    before = _db_snapshot(status_store.path)
    assert _get(client, key).status_code == 200
    assert _get(client, key, "?asset_id=999").status_code == 404
    assert _db_snapshot(status_store.path) == before

    _insert_status(status_store, first, "open")
    with sqlite3.connect(status_store.path) as connection:
        connection.execute("UPDATE cve_status_records SET status='broken'")
    invalid = _get(client, key)
    assert (invalid.status_code, invalid.json()["error"]["code"]) == (503, "cves_unavailable")

    with sqlite3.connect(status_store.path) as connection:
        connection.execute("DROP INDEX cve_status_audit_relation")
    schema = _get(client, key)
    assert (schema.status_code, schema.json()["error"]["code"]) == (503, "cves_unavailable")

    with sqlite3.connect(status_store.path) as connection:
        connection.execute("UPDATE cve_status_records SET status='open'")
        connection.execute(
            "CREATE INDEX cve_status_audit_relation ON cve_status_audit"
            "(technology_id,cve_id,vendor_key,product_key,id DESC)"
        )
    monkeypatch.setattr("portal_api.cves_status_view.MAX_RESPONSE_BYTES", 20)
    cap = _get(client, key)
    assert (cap.status_code, cap.json()["error"]["code"]) == (503, "cves_unavailable")


def test_reader_keeps_one_sqlite_snapshot_when_writer_commits_between_reads(tmp_path, rsa_keys, monkeypatch):
    client, key, _technology, status_store, _port, first, _second = _setup(tmp_path, rsa_keys)
    from portal_api.cves_status_view import CveStatusViewService

    original = CveStatusViewService._read_status_rows

    def commit_then_read(service, connection):
        _insert_status(status_store, first, "open")
        return original(service, connection)

    monkeypatch.setattr(CveStatusViewService, "_read_status_rows", commit_then_read)
    response = _get(client, key)

    assert response.status_code == 200
    match = response.json()["items"][0]["matches"][0]
    assert match["status"] is None
    with sqlite3.connect(status_store.path) as connection:
        assert connection.execute("SELECT status FROM cve_status_records").fetchone() == ("open",)


def test_inactive_and_changed_identity_do_not_inherit_status_and_clock_runs_once(tmp_path, rsa_keys):
    calls = []

    def clock():
        calls.append(True)
        return datetime(2026, 11, 12, tzinfo=UTC)

    client, key, technology, status_store, port, first, second = _setup(tmp_path, rsa_keys, clock=clock)
    _insert_status(status_store, first, "patched")
    _insert_status(status_store, second, "open")
    technology.delete(second.id, second.version, "seed")
    technology.update(first.id, "Fortinet", "FortiGate", "7.2", "private", first.version, "seed")
    for candidate in port.dataset["candidates"]:
        candidate["affected_products"][0]["product"] = "FortiGate"

    response = _get(client, key)

    assert response.status_code == 200
    assert calls == [True]
    assert all(len(item["matches"]) == 1 for item in response.json()["items"])
    assert all(item["matches"][0]["status"] is None for item in response.json()["items"])


def test_cursor_rejects_noncanonical_and_invalid_after(tmp_path, rsa_keys):
    client, key, _technology, _status, _port, _first, _second = _setup(tmp_path, rsa_keys)
    first = _get(client, key, "?limit=1")
    decoded = _decode(first.json()["page"]["next_cursor"])
    decoded["after"] = "CVE-2026-9999"
    bad_after = _get(client, key, f"?limit=1&cursor={_encode(decoded)}")
    raw = json.dumps(_decode(first.json()["page"]["next_cursor"]), indent=2).encode()
    noncanonical = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    bad_canonical = _get(client, key, f"?limit=1&cursor={noncanonical}")
    assert [(item.status_code, item.json()["error"]["code"]) for item in (bad_after, bad_canonical)] == [
        (422, "invalid_cve_status_query"),
        (422, "invalid_cve_status_query"),
    ]


def test_checked_in_detail_leader_and_error_fixtures_match_real_api(tmp_path, rsa_keys):
    client, key, _technology, status_store, _port, first, second = _setup(tmp_path, rsa_keys)
    _insert_status(status_store, first, "patched")
    _insert_status(status_store, second, "open", stale=True)
    fixture_dir = Path(__file__).parent / "fixtures"
    actual = {
        "detail": _wire(_get(client, key, "?limit=100")),
        "leader": _wire(_get(client, key, "?limit=100", "leader-sub")),
        "error": _wire(_get(client, key, "?limit=0")),
    }
    expected = {
        name: json.loads((fixture_dir / f"w03-status-view-{name}.json").read_text(encoding="utf-8"))
        for name in actual
    }
    assert actual == expected
