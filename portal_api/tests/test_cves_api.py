from __future__ import annotations

import base64
import copy
import hashlib
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portal_api import cves
from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier, AuthenticationUnavailable
from portal_api.technologies import TechnologyStore
from portal_api.tests import test_w02_ioc_api as w02_test_api
from portal_api.tests.test_w02_ioc_api import LocalJwksClient, _auth, _settings


@pytest.fixture(scope="session")
def rsa_keys():
    return w02_test_api.rsa_keys.__wrapped__()


def test_route_is_opt_in_after_authentication(tmp_path, rsa_keys):
    private_key, jwk = rsa_keys
    settings = _settings(tmp_path)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, object(), verifier=verifier), raise_server_exceptions=False)

    response = client.get("/api/cves", headers=_auth(private_key))

    assert (response.status_code, response.json()["error"]["code"]) == (503, "cves_unavailable")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"].lower() == "cf-access-jwt-assertion"


class StaticPort:
    def __init__(self, dataset):
        self.dataset = dataset
        self.calls = 0

    def list_candidates(self):
        self.calls += 1
        return copy.deepcopy(self.dataset)


def _candidate(
    cve_id="CVE-2026-1000",
    *,
    vendor="Fortinet",
    product="FortiOS",
    kev=True,
    epss=0.9,
    cvss=9.8,
    published_at="2026-10-01T00:00:00Z",
):
    return {
        "cve_id": cve_id,
        "title": f"Synthetic {cve_id}",
        "affected_products": [{"vendor": vendor, "product": product}],
        "kev": {
            "known_exploited": kev,
            "source": "CISA KEV synthetic sample",
            "as_of": "2026-11-01",
            "due_date": "2026-11-15" if kev else None,
        },
        "epss": {
            "score": epss,
            "percentile": None if epss is None else min(1.0, epss + 0.05),
            "as_of": None if epss is None else "2026-11-01",
        },
        "cvss": {
            "base_score": cvss,
            "version": None if cvss is None else "3.1",
        },
        "published_at": published_at,
        "advisory_url": f"https://example.invalid/{cve_id}",
    }


def _dataset(candidates=None):
    return {
        "kind": "synthetic",
        "kev_snapshot_complete": True,
        "source_as_of": "2026-11-01T00:00:00Z",
        "retrieved_at": "2026-11-01T01:00:00Z",
        "candidates": [_candidate()] if candidates is None else candidates,
    }


def _store(tmp_path, *rows):
    store = TechnologyStore(tmp_path / "technologies.sqlite", timeout=0.01)
    store.initialize()
    for vendor, product, version in rows:
        store.create(vendor, product, version, "kept-private", "seed-sub")
    return store


def _fixed_store(tmp_path, *rows):
    store = TechnologyStore(tmp_path / "technologies.sqlite", timeout=0.01)
    store.initialize()
    stamp = "2026-11-01T00:00:00Z"
    with sqlite3.connect(store.path) as connection:
        connection.executemany(
            "INSERT INTO technology_assets(vendor,vendor_key,product,product_key,software_version,note,"
            "record_version,created_by,created_at,updated_at,deleted_at) VALUES(?,?,?,?,?,?,1,?,?,?,NULL)",
            [
                (
                    vendor,
                    vendor.casefold(),
                    product,
                    product.casefold(),
                    version,
                    "kept-private",
                    "seed-sub",
                    stamp,
                    stamp,
                )
                for vendor, product, version in rows
            ],
        )
    return store


def _sql_snapshot(store):
    with sqlite3.connect(store.path) as connection:
        return {
            "schema": connection.execute(
                "SELECT type,name,sql FROM sqlite_master ORDER BY type,name"
            ).fetchall(),
            "rows": connection.execute("SELECT * FROM technology_assets").fetchall(),
            "audit": connection.execute("SELECT * FROM technology_asset_audit").fetchall(),
            "version": connection.execute("PRAGMA user_version").fetchone(),
        }


def _wire(response):
    return {
        "status": response.status_code,
        "headers": {
            "cache-control": response.headers["cache-control"],
            "vary": response.headers["vary"],
        },
        "body": response.json(),
    }


def _client(tmp_path, rsa_keys, *, port=None, store=None, roles=None):
    private_key, jwk = rsa_keys
    settings = _settings(tmp_path)
    if roles is not None:
        settings = replace(settings, roles_by_subject=roles)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(
        create_app(
            settings,
            object(),
            verifier=verifier,
            cve_port=port,
            technology_store=store,
        ),
        raise_server_exceptions=False,
    )
    return client, private_key


def _get(client, private_key, query="", subject="it-sub"):
    return client.get(f"/api/cves{query}", headers=_auth(private_key, subject))


def test_auth_and_query_precede_dependencies_and_leader_asset_is_forbidden(tmp_path, rsa_keys):
    port = StaticPort(_dataset())
    roles = {
        "it-sub": frozenset({"it"}),
        "leader-sub": frozenset({"leader"}),
        "none-sub": frozenset({"viewer"}),
    }
    client, private_key = _client(tmp_path, rsa_keys, port=port, roles=roles)

    missing_auth = client.get("/api/cves?bad=x")
    forbidden = _get(client, private_key, "?bad=x", "none-sub")
    invalid_query = _get(client, private_key, "?limit=1.0")
    leader_asset = _get(client, private_key, "?asset_id=1", "leader-sub")

    assert (missing_auth.status_code, missing_auth.json()["error"]["code"]) == (
        401,
        "authentication_required",
    )
    assert (forbidden.status_code, forbidden.json()["error"]["code"]) == (403, "forbidden")
    assert (invalid_query.status_code, invalid_query.json()["error"]["code"]) == (
        422,
        "invalid_cve_query",
    )
    assert (leader_asset.status_code, leader_asset.json()["error"]["code"]) == (403, "forbidden")
    assert port.calls == 0


def test_verifier_unavailable_is_cves_unavailable_before_dependencies(tmp_path, rsa_keys):
    class UnavailableVerifier:
        def verify(self, _token):
            raise AuthenticationUnavailable("synthetic outage")

    port = StaticPort(_dataset())
    store = TechnologyStore(tmp_path / "must-not-open.sqlite")
    settings = _settings(tmp_path)
    app = create_app(
        settings,
        object(),
        verifier=UnavailableVerifier(),
        cve_port=port,
        technology_store=store,
    )
    response = TestClient(app, raise_server_exceptions=False).get(
        "/api/cves?limit=0",
        headers={"Cf-Access-Jwt-Assertion": "synthetic"},
    )

    assert (response.status_code, response.json()["error"]["code"]) == (503, "cves_unavailable")
    assert port.calls == 0
    assert not store.path.exists()


@pytest.mark.parametrize(
    "query",
    [
        "?bad=x",
        "?kev=true&kev=false",
        "?kev=1",
        "?asset_id=0",
        "?asset_id=01",
        "?asset_id=9007199254740992",
        "?limit=0",
        "?limit=101",
        "?limit=+1",
        "?q=%00",
        "?q=",
        "?cursor=%25%25%25",
    ],
)
def test_strict_query_is_rejected_before_port(tmp_path, rsa_keys, query):
    port = StaticPort(_dataset())
    client, private_key = _client(tmp_path, rsa_keys, port=port, store=_store(tmp_path))

    response = _get(client, private_key, query)

    assert (response.status_code, response.json()["error"]["code"]) == (422, "invalid_cve_query")
    assert port.calls == 0


def test_detail_matching_unicode_casefold_versions_ranking_and_null_zero(tmp_path, rsa_keys):
    candidates = [
        _candidate("CVE-2026-1004", vendor="STRASSE", product="Gateway", kev=False, epss=0.0, cvss=0.0),
        _candidate("CVE-2026-1003", kev=False, epss=None, cvss=None, published_at=None),
        _candidate("CVE-2026-1002", kev=False, epss=0.7, cvss=8.0),
        _candidate("CVE-2026-1001", kev=True, epss=0.1, cvss=5.0),
    ]
    store = _store(
        tmp_path, ("Fortinet", "FortiOS", "7.2"), ("fortinet", "fortios", "7.4"), ("Straße", "Gateway", "1")
    )
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset(candidates)), store=store)

    response = _get(client, private_key, "?limit=100")

    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "detail"
    assert [item["cve_id"] for item in body["items"]] == [
        "CVE-2026-1001",
        "CVE-2026-1002",
        "CVE-2026-1004",
        "CVE-2026-1003",
    ]
    assert [item["priority"] for item in body["items"]] == [1, 2, 3, 4]
    assert [match["software_version"] for match in body["items"][0]["matches"]] == ["7.2", "7.4"]
    assert body["items"][2]["epss_score"] == 0.0
    assert body["items"][3]["epss_score"] is None
    assert body["summary"] == {"matched_cves": 4, "kev_cves": 1}
    assert set(body) == {"view", "items", "summary", "page", "source", "notice"}


def test_summary_and_mixed_role_do_not_leak_assets(tmp_path, rsa_keys):
    roles = {
        "leader-sub": frozenset({"leader"}),
        "mixed-sub": frozenset({"leader", "analyst"}),
    }
    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"))
    port = StaticPort(_dataset([_candidate()]))
    client, private_key = _client(tmp_path, rsa_keys, port=port, store=store, roles=roles)

    summary = _get(client, private_key, subject="leader-sub")
    detail = _get(client, private_key, subject="mixed-sub")

    assert summary.status_code == detail.status_code == 200
    assert summary.json()["view"] == "summary"
    assert set(summary.json()["items"][0]) == {
        "cve_id",
        "title",
        "kev",
        "epss_score",
        "cvss_base_score",
        "priority",
        "match_count",
    }
    assert "Fortinet" not in summary.text and "7.2" not in summary.text
    assert detail.json()["view"] == "detail"
    assert detail.json()["items"][0]["matches"][0]["technology_id"] == 1


def test_ranking_uses_real_fractional_time_then_cve_id_for_ties(tmp_path, rsa_keys):
    candidates = [
        _candidate("CVE-2026-1003", kev=False, epss=0.5, cvss=5.0, published_at="2026-10-01T00:00:00Z"),
        _candidate(
            "CVE-2026-1002",
            kev=False,
            epss=0.5,
            cvss=5.0,
            published_at="2026-10-01T00:00:00.100000Z",
        ),
        _candidate(
            "CVE-2026-1001",
            kev=False,
            epss=0.5,
            cvss=5.0,
            published_at="2026-10-01T00:00:00.100000Z",
        ),
        _candidate(
            "CVE-2026-1004",
            kev=False,
            epss=0.5,
            cvss=5.0,
            published_at="2026-10-01T00:00:00.900000Z",
        ),
    ]
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        port=StaticPort(_dataset(candidates)),
        store=_store(tmp_path, ("Fortinet", "FortiOS", "7.2")),
    )

    response = _get(client, private_key)

    assert [item["cve_id"] for item in response.json()["items"]] == [
        "CVE-2026-1004",
        "CVE-2026-1001",
        "CVE-2026-1002",
        "CVE-2026-1003",
    ]


def test_asset_not_found_is_404_but_existing_unmatched_is_empty(tmp_path, rsa_keys):
    store = _store(tmp_path, ("Other", "Product", "1"))
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset()), store=store)

    missing = _get(client, private_key, "?asset_id=2")
    unmatched = _get(client, private_key, "?asset_id=1")

    assert (missing.status_code, missing.json()["error"]["code"]) == (404, "technology_not_found")
    assert unmatched.status_code == 200
    assert unmatched.json()["items"] == []


def test_pagination_cursor_is_stable_and_snapshot_change_is_409(tmp_path, rsa_keys):
    candidates = [
        _candidate(f"CVE-2026-{1000 + index}", kev=False, epss=(20 - index) / 20) for index in range(12)
    ]
    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"))
    port = StaticPort(_dataset(candidates))
    client, private_key = _client(tmp_path, rsa_keys, port=port, store=store)

    first = _get(client, private_key, "?limit=5")
    cursor = first.json()["page"]["next_cursor"]
    second = _get(client, private_key, f"?limit=5&cursor={cursor}")
    last = _get(client, private_key, f"?limit=5&cursor={second.json()['page']['next_cursor']}")
    wrong_context = _get(client, private_key, f"?limit=6&cursor={cursor}")
    tampered = _get(client, private_key, f"?limit=5&cursor={cursor[:-1]}A")
    store.create("Extra", "Product", "1", "", "seed-sub")
    changed = _get(client, private_key, f"?limit=5&cursor={cursor}")

    assert [len(first.json()["items"]), len(second.json()["items"]), len(last.json()["items"])] == [5, 5, 2]
    assert last.json()["page"]["next_cursor"] is None
    all_ids = [item["cve_id"] for response in (first, second, last) for item in response.json()["items"]]
    assert len(all_ids) == len(set(all_ids)) == 12
    assert (wrong_context.status_code, wrong_context.json()["error"]["code"]) == (422, "invalid_cve_query")
    assert (tampered.status_code, tampered.json()["error"]["code"]) == (422, "invalid_cve_query")
    assert (changed.status_code, changed.json()["error"]["code"]) == (409, "cve_snapshot_changed")


def test_cursor_rejects_missing_after_and_cross_role_context(tmp_path, rsa_keys):
    roles = {"it-sub": frozenset({"it"}), "leader-sub": frozenset({"leader"})}
    port = StaticPort(_dataset([_candidate("CVE-2026-1001"), _candidate("CVE-2026-1002")]))
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        port=port,
        store=_fixed_store(tmp_path, ("Fortinet", "FortiOS", "7.2")),
        roles=roles,
    )
    detail = _get(client, private_key, "?limit=1", "it-sub")
    detail_cursor = detail.json()["page"]["next_cursor"]
    raw = base64.urlsafe_b64decode(detail_cursor + "=" * (-len(detail_cursor) % 4))
    parsed = json.loads(raw)
    noncanonical = (
        base64.urlsafe_b64encode(json.dumps(parsed, indent=1).encode("utf-8")).rstrip(b"=").decode("ascii")
    )
    parsed["after"] = "CVE-2099-9999"
    missing_after = (
        base64.urlsafe_b64encode(json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        .rstrip(b"=")
        .decode("ascii")
    )
    summary = _get(client, private_key, "?limit=1", "leader-sub")

    missing = _get(client, private_key, f"?limit=1&cursor={missing_after}", "it-sub")
    noncanonical_response = _get(
        client,
        private_key,
        f"?limit=1&cursor={noncanonical}",
        "it-sub",
    )
    cross_role = _get(
        client,
        private_key,
        f"?limit=1&cursor={summary.json()['page']['next_cursor']}",
        "it-sub",
    )

    assert (missing.status_code, missing.json()["error"]["code"]) == (422, "invalid_cve_query")
    assert (
        noncanonical_response.status_code,
        noncanonical_response.json()["error"]["code"],
    ) == (422, "invalid_cve_query")
    assert (cross_role.status_code, cross_role.json()["error"]["code"]) == (422, "invalid_cve_query")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.update(kind="real"),
        lambda data: data.update(kev_snapshot_complete=False),
        lambda data: data.update(source_as_of="2026-02-30T00:00:00Z"),
        lambda data: data["candidates"].append(copy.deepcopy(data["candidates"][0])),
        lambda data: data["candidates"][0]["kev"].update(known_exploited=1),
        lambda data: data["candidates"][0]["epss"].update(score=True),
        lambda data: data["candidates"][0]["epss"].update(score=float("nan")),
        lambda data: data["candidates"][0]["cvss"].update(base_score=11),
        lambda data: data["candidates"][0].update(advisory_url="http://example.invalid/x"),
        lambda data: data["candidates"][0]["affected_products"].append(
            {"vendor": "FORTINET", "product": "fortios"}
        ),
        lambda data: data.update(
            candidates=[_candidate(f"CVE-2026-{10000 + index}") for index in range(1001)]
        ),
        lambda data: data["candidates"][0].update(
            affected_products=[{"vendor": "V", "product": f"P{index}"} for index in range(21)]
        ),
    ],
)
def test_invalid_dataset_fails_closed(tmp_path, rsa_keys, mutate):
    data = _dataset()
    mutate(data)
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        port=StaticPort(data),
        store=_store(tmp_path, ("Fortinet", "FortiOS", "7.2")),
    )

    response = _get(client, private_key)

    assert (response.status_code, response.json()["error"]["code"]) == (503, "cves_unavailable")


@pytest.mark.parametrize("case", ["product_too_long", "ambiguous_kev_source"])
def test_w03_synthetic_product_and_source_contract_fails_closed(tmp_path, rsa_keys, case):
    data = _dataset()
    product = "P" * 129 if case == "product_too_long" else "FortiOS"
    data["candidates"][0]["affected_products"][0]["product"] = product
    if case == "ambiguous_kev_source":
        data["candidates"][0]["kev"]["source"] = "CISA KEV"
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        port=StaticPort(data),
        store=_store(tmp_path, ("Fortinet", product, "7.2")),
    )

    response = _get(client, private_key)

    assert (response.status_code, response.json()["error"]["code"]) == (503, "cves_unavailable")


def test_read_does_not_create_missing_database_or_modify_sql_state(tmp_path, rsa_keys):
    missing = TechnologyStore(tmp_path / "missing.sqlite")
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset()), store=missing)
    unavailable = _get(client, private_key)

    assert unavailable.status_code == 503
    assert not missing.path.exists()

    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"))
    before = _sql_snapshot(store)
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset()), store=store)
    assert _get(client, private_key).status_code == 200
    after = _sql_snapshot(store)
    assert after == before


def test_dependency_failures_do_not_modify_sql_state(tmp_path, rsa_keys):
    candidates = [_candidate("CVE-2026-1001"), _candidate("CVE-2026-1002")]
    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"))
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset(candidates)), store=store)

    before_404 = _sql_snapshot(store)
    missing = _get(client, private_key, "?asset_id=2")
    assert _sql_snapshot(store) == before_404

    first = _get(client, private_key, "?limit=1")
    cursor = first.json()["page"]["next_cursor"]
    store.create("Extra", "Product", "1", "", "seed-sub")
    before_409 = _sql_snapshot(store)
    changed = _get(client, private_key, f"?limit=1&cursor={cursor}")

    assert (missing.status_code, missing.json()["error"]["code"]) == (404, "technology_not_found")
    assert (changed.status_code, changed.json()["error"]["code"]) == (409, "cve_snapshot_changed")
    assert _sql_snapshot(store) == before_409


def test_fixture_port_hashes_exact_bytes_and_rejects_more_than_four_mib(tmp_path):
    raw = json.dumps(_dataset(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fixture = tmp_path / "fixture.json"
    fixture.write_bytes(raw)
    adapter_type = getattr(cves, "FixtureCveReadPort", None)

    assert adapter_type is not None
    dataset = adapter_type(fixture).list_candidates()
    assert dataset.dataset_id == "sha256:" + hashlib.sha256(raw).hexdigest()

    too_large = tmp_path / "too-large.json"
    too_large.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    with pytest.raises(cves.CvesUnavailable):
        adapter_type(too_large).list_candidates()

    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps({**_dataset(), "unexpected": True}), encoding="utf-8")
    with pytest.raises(cves.CvesUnavailable):
        adapter_type(extra).list_candidates()


def test_checked_in_fixture_runs_through_real_api(tmp_path, rsa_keys):
    fixture = cves.FixtureCveReadPort(Path(__file__).parent / "fixtures" / "w03-cves-synthetic.json")
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        port=fixture,
        store=_store(tmp_path, ("Fortinet", "FortiOS", "7.2")),
    )

    response = _get(client, private_key)

    assert response.status_code == 200
    assert [item["cve_id"] for item in response.json()["items"]] == ["CVE-2026-1001", "CVE-2026-1002"]
    expected_hash = hashlib.sha256(fixture.path.read_bytes()).hexdigest()
    assert response.json()["source"]["dataset_id"] == f"sha256:{expected_hash}"


def test_checked_in_wire_fixtures_equal_real_api_responses(tmp_path, rsa_keys):
    fixture_dir = Path(__file__).parent / "fixtures"
    port = cves.FixtureCveReadPort(fixture_dir / "w03-cves-synthetic.json")
    roles = {"it-sub": frozenset({"it"}), "leader-sub": frozenset({"leader"})}
    store = _fixed_store(tmp_path / "wire", ("Fortinet", "FortiOS", "7.2"))
    client, private_key = _client(tmp_path / "wire", rsa_keys, port=port, store=store, roles=roles)

    actual = {
        "detail": _wire(_get(client, private_key, "?limit=1", "it-sub")),
        "summary": _wire(_get(client, private_key, "?limit=1", "leader-sub")),
        "error": _wire(_get(client, private_key, "?limit=0", "it-sub")),
    }
    cursor = actual["detail"]["body"]["page"]["next_cursor"]
    store.create("Extra", "Product", "1", "", "seed-sub")
    actual["cursor-changed"] = _wire(_get(client, private_key, f"?limit=1&cursor={cursor}", "it-sub"))
    empty_store = _fixed_store(tmp_path / "empty")
    empty_client, empty_key = _client(
        tmp_path / "empty",
        rsa_keys,
        port=port,
        store=empty_store,
        roles=roles,
    )
    actual["empty"] = _wire(_get(empty_client, empty_key, subject="it-sub"))

    for name, response in actual.items():
        expected = json.loads((fixture_dir / f"w03-wire-{name}.json").read_text(encoding="utf-8"))
        assert response == expected


def test_response_over_one_mib_fails_closed(tmp_path, rsa_keys):
    store = _store(tmp_path)
    stamp = "2026-11-01T00:00:00Z"
    with sqlite3.connect(store.path) as connection:
        connection.executemany(
            "INSERT INTO technology_assets(vendor,vendor_key,product,product_key,software_version,note,"
            "record_version,created_by,created_at,updated_at,deleted_at) VALUES(?,?,?,?,?,?,1,?,?,?,NULL)",
            [
                ("Fortinet", "fortinet", "FortiOS", "fortios", str(index), "", "seed", stamp, stamp)
                for index in range(1000)
            ],
        )
    candidates = [_candidate(f"CVE-2026-{10000 + index}") for index in range(26)]
    client, private_key = _client(tmp_path, rsa_keys, port=StaticPort(_dataset(candidates)), store=store)

    response = _get(client, private_key)

    assert (response.status_code, response.json()["error"]["code"]) == (503, "cves_unavailable")
