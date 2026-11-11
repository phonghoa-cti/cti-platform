from __future__ import annotations

import importlib
import sqlite3
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from phonghoa_core import Ioc, IocType, normalize
from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.tests import test_w02_ioc_api as w02_test_api
from portal_api.tests.test_w02_ioc_api import (
    GREEN_SOURCE,
    LocalJwksClient,
    _auth,
    _record,
    _settings,
)

assets = importlib.import_module("portal_api.assets")


@pytest.fixture(scope="session")
def rsa_keys():
    return w02_test_api.rsa_keys.__wrapped__()


def _store(tmp_path):
    store = assets.AssetStore(tmp_path / "assets.sqlite", timeout=0.01)
    store.initialize()
    return store


def _client(tmp_path, rsa_keys, *, asset_store=None, lookup_port=None, subjects=None):
    private_key, jwk = rsa_keys
    settings = _settings(tmp_path)
    if subjects is not None:
        settings = replace(settings, roles_by_subject=subjects)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    app = create_app(
        settings,
        object(),
        verifier=verifier,
        lookup_port=lookup_port,
        asset_store=asset_store,
    )
    return TestClient(app, raise_server_exceptions=False), private_key


def _mutation_headers(private_key, subject="it-sub"):
    return {**_auth(private_key, subject), "Origin": "https://portal.synthetic.test"}


def _replace_active_row(store, assignments, params=()):
    with sqlite3.connect(store.path) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(f"UPDATE assets SET {assignments} WHERE deleted_at IS NULL", params)


def _row_counts(store):
    with sqlite3.connect(store.path) as connection:
        return (
            connection.execute("SELECT count(*) FROM assets").fetchone()[0],
            connection.execute("SELECT count(*) FROM asset_audit").fetchone()[0],
        )


def test_store_canonicalizes_domain_and_cidr_and_audits_atomically(tmp_path):
    store = _store(tmp_path)

    domain = store.create("domain", "NgânHàng.VN.", "trụ sở", "it-sub")
    network = store.create("ip_range", "2001:4860:4860::/48", "IPv6", "it-sub")

    assert domain.value == "xn--ngnhng-ltan.vn"
    assert network.value == "2001:4860:4860::/48"
    assert [item.value for item in store.list()] == [domain.value, network.value]
    with sqlite3.connect(store.path) as connection:
        rows = connection.execute(
            "SELECT action, actor_subject, before_json, after_json FROM asset_audit ORDER BY id"
        ).fetchall()
    assert rows[0][0:3] == ("asset_created", "it-sub", None)
    assert '"canonical_value":"xn--ngnhng-ltan.vn"' in rows[0][3]


@pytest.mark.parametrize(
    ("asset_type", "value"),
    [
        ("domain", "https://example.com/path"),
        ("domain", "*.example.com"),
        ("domain", "singlelabel"),
        ("domain", "user@example.com"),
        ("domain", "evil[.]example"),
        ("ip_range", "8.8.8.1/24"),
        ("ip_range", "8.8.8.8"),
        ("ip_range", "not-a-network/24"),
    ],
)
def test_store_rejects_structurally_invalid_assets(tmp_path, asset_type, value):
    store = _store(tmp_path)

    with pytest.raises(assets.InvalidAsset):
        store.create(asset_type, value, "", "it-sub")

    assert store.list() == ()


def test_store_enforces_active_duplicate_version_and_rollback(tmp_path):
    store = _store(tmp_path)
    created = store.create("domain", "Example.COM.", "first", "it-sub")

    with pytest.raises(assets.AssetExists):
        store.create("domain", "example.com", "duplicate", "it-sub")
    with pytest.raises(assets.AssetConflict):
        store.update(created.id, "domain", "other.example", "changed", 2, "analyst-sub")

    unchanged = store.list()[0]
    assert unchanged.value == "example.com"
    assert unchanged.note == "first"
    assert unchanged.version == 1
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT count(*) FROM asset_audit").fetchone()[0] == 1

    updated = store.update(created.id, "domain", "other.example", "changed", 1, "analyst-sub")
    assert updated.version == 2
    store.delete(created.id, 2, "admin-sub")
    assert store.list() == ()
    with pytest.raises(assets.AssetNotFound):
        store.delete(created.id, 2, "admin-sub")


def test_snapshot_matches_domain_url_email_and_network_boundaries(tmp_path):
    store = _store(tmp_path)
    store.create("domain", "congty.vn", "", "it-sub")
    store.create("ip_range", "203.0.113.0/24", "", "it-sub")
    store.create("ip_range", "2001:4860:4860::/48", "", "it-sub")
    snapshot = store.snapshot()

    assert snapshot.match(normalize("mail.congty.vn")) == ("congty.vn",)
    assert snapshot.match(normalize("https://mail.congty.vn/a?b=1")) == ("congty.vn",)
    assert snapshot.match(normalize("user@congty.vn")) == ("congty.vn",)
    assert snapshot.match(normalize("evilcongty.vn")) == ()
    assert snapshot.match(normalize("congty.vn.evil.test")) == ()
    assert snapshot.match(Ioc(IocType.IPV4, "203.0.113.8")) == ("203.0.113.0/24",)
    assert snapshot.match(Ioc(IocType.IPV4, "198.51.100.8")) == ()
    assert snapshot.match(Ioc(IocType.IPV6, "2001:4860:4860::8")) == ("2001:4860:4860::/48",)
    assert snapshot.match(Ioc(IocType.SHA256, "a" * 64)) == ()


def test_assets_routes_are_opt_in_and_auth_precedes_query_or_store(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys)

    unavailable = client.get("/api/assets", headers=_auth(private_key))
    unauthenticated = client.get("/api/assets?bad=x")
    forbidden = client.post(
        "/api/assets",
        headers={
            **_mutation_headers(private_key, "leader-sub"),
            "X-Role": "admin",
            "Cf-Access-Authenticated-User-Email": "admin@example.test",
        },
        content=b"not-json",
    )

    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "assets_unavailable"
    assert unauthenticated.status_code == 401
    assert forbidden.status_code == 403
    for response in (unavailable, unauthenticated, forbidden):
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"].lower() == "cf-access-jwt-assertion"


def test_assets_http_crud_exact_validation_and_conflicts(tmp_path, rsa_keys):
    store = _store(tmp_path)
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    headers = _mutation_headers(private_key)

    created = client.post(
        "/api/assets",
        headers=headers,
        json={"type": "domain", "value": "CONGTY.VN.", "note": "owned"},
    )
    duplicate = client.post(
        "/api/assets",
        headers=headers,
        json={"type": "domain", "value": "congty.vn", "note": "x"},
    )
    bad = client.post(
        "/api/assets",
        headers=headers,
        json={"type": "domain", "value": "congty.vn", "note": "x", "extra": True},
    )
    listed = client.get("/api/assets?type=domain", headers=_auth(private_key))

    assert created.status_code == 201
    item = created.json()
    assert item["value"] == "congty.vn"
    assert item["created_by"] == "it-sub"
    assert item["version"] == 1
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "asset_exists"
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "invalid_asset"
    assert listed.json() == {"items": [item]}

    stale = client.put(
        f"/api/assets/{item['id']}",
        headers=headers,
        json={
            "type": "domain",
            "value": "new.congty.vn",
            "note": "new",
            "expected_version": 2,
        },
    )
    updated = client.put(
        f"/api/assets/{item['id']}",
        headers=headers,
        json={
            "type": "domain",
            "value": "new.congty.vn",
            "note": "new",
            "expected_version": 1,
        },
    )
    deleted = client.delete(f"/api/assets/{item['id']}?expected_version=2", headers=headers)

    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "asset_conflict"
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_assets_http_rejects_body_limit_and_repeated_or_extra_query(tmp_path, rsa_keys):
    store = _store(tmp_path)
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    headers = {**_mutation_headers(private_key), "Content-Type": "application/json"}

    too_large = client.post("/api/assets", headers=headers, content=b"{" + b" " * 8192)
    repeated = client.get("/api/assets?type=domain&type=domain", headers=_auth(private_key))
    extra = client.get("/api/assets?extra=x", headers=_auth(private_key))

    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "request_too_large"
    assert repeated.status_code == 422
    assert extra.status_code == 422


@pytest.mark.parametrize("asset_id", ["0", "1.0", "true", "9007199254740992"])
def test_assets_put_rejects_invalid_path_id_with_asset_error(tmp_path, rsa_keys, asset_id):
    store = _store(tmp_path)
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)

    response = client.put(
        f"/api/assets/{asset_id}",
        headers=_mutation_headers(private_key),
        json={
            "type": "domain",
            "value": "congty.vn",
            "note": "",
            "expected_version": 1,
        },
    )

    assert response.status_code == 422
    assert response.json() == {"error": {"code": "invalid_asset", "message": "Tài sản không hợp lệ"}}


@pytest.mark.parametrize("expected_version", ["0", "1.0", "true", "9007199254740992"])
def test_assets_delete_rejects_invalid_version_with_asset_error(tmp_path, rsa_keys, expected_version):
    store = _store(tmp_path)
    asset = store.create("domain", "congty.vn", "", "it-sub")
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)

    response = client.delete(
        f"/api/assets/{asset.id}?expected_version={expected_version}",
        headers=_mutation_headers(private_key),
    )

    assert response.status_code == 422
    assert response.json() == {"error": {"code": "invalid_asset", "message": "Tài sản không hợp lệ"}}


def test_store_failure_uses_route_specific_unavailable_error(tmp_path, rsa_keys):
    class BrokenStore:
        def list(self, _asset_type=None):
            raise sqlite3.DatabaseError("synthetic path and secret detail")

        def snapshot(self):
            raise sqlite3.DatabaseError("synthetic path and secret detail")

    client, private_key = _client(tmp_path, rsa_keys, asset_store=BrokenStore())

    assets_response = client.get("/api/assets", headers=_auth(private_key))
    lookup_response = client.get("/api/ioc?value=unknown.example", headers=_auth(private_key))

    assert assets_response.status_code == 503
    assert assets_response.json()["error"]["code"] == "assets_unavailable"
    assert lookup_response.status_code == 503
    assert lookup_response.json()["error"]["code"] == "lookup_unavailable"
    assert "secret" not in assets_response.text + lookup_response.text


def test_w02_asset_snapshot_applies_to_allowlisted_not_found_and_found(tmp_path, rsa_keys):
    store = _store(tmp_path)
    store.create("domain", "congty.vn", "", "it-sub")
    port = type(
        "Port",
        (),
        {
            "calls": [],
            "lookup": lambda self, ioc, allowed: (
                self.calls.append((ioc, allowed))
                or (
                    replace(_record(), ioc=ioc, sources=(GREEN_SOURCE,))
                    if ioc.value == "https://found.congty.vn/path"
                    else None
                )
            ),
        },
    )()
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store, lookup_port=port)
    auth = _auth(private_key)

    allowlisted = client.get("/api/ioc?value=mail.congty.vn", headers=auth)
    not_found = client.get("/api/ioc?value=https://unknown.congty.vn/path", headers=auth)
    found = client.get("/api/ioc?value=https://found.congty.vn/path", headers=auth)

    assert allowlisted.json()["state"] == "allowlisted"
    assert allowlisted.json()["asset_match"] == {"matched": True, "assets": ["congty.vn"]}
    assert not_found.json()["state"] == "not_found"
    assert not_found.json()["asset_match"] == {"matched": True, "assets": ["congty.vn"]}
    assert found.json()["state"] == "found"
    assert found.json()["asset_match"] == {"matched": True, "assets": ["congty.vn"]}
    assert found.json()["score"]["parts"]["asset"] == 1.3
    assert [call[0].value for call in port.calls] == [
        "https://unknown.congty.vn/path",
        "https://found.congty.vn/path",
    ]


def test_default_allowlist_survives_asset_deletion(tmp_path, rsa_keys):
    store = _store(tmp_path)
    asset = store.create("domain", "google.com", "", "it-sub")
    store.delete(asset.id, asset.version, "it-sub")
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store, lookup_port=None)

    response = client.get("/api/ioc?value=mail.google.com", headers=_auth(private_key))

    assert response.status_code == 200
    assert response.json()["state"] == "allowlisted"
    assert response.json()["asset_match"] == {"matched": False, "assets": []}


def test_hidden_record_remains_not_found_but_keeps_local_asset(tmp_path, rsa_keys):
    store = _store(tmp_path)
    store.create("domain", "congty.vn", "", "it-sub")
    raw = "https://hidden.congty.vn/path"
    hidden = replace(_record(record_tlp="TLP:AMBER"), ioc=normalize(raw))
    port = type("Port", (), {"lookup": lambda self, _ioc, _allowed: hidden})()
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store, lookup_port=port)

    response = client.get(f"/api/ioc?value={raw}", headers=_auth(private_key))

    assert response.json()["state"] == "not_found"
    assert response.json()["asset_match"] == {"matched": True, "assets": ["congty.vn"]}


@pytest.mark.parametrize(
    ("assignments", "params"),
    [
        ("type='technology'", ()),
        ("canonical_value='com'", ()),
        ("canonical_value='EXAMPLE.com'", ()),
        ("type='ip_range', canonical_value='203.0.113.1/24'", ()),
        ("id=9007199254740992", ()),
        ("version=9007199254740992", ()),
        ("note=?", ("n" * 501,)),
        ("created_by=?", ("s" * 513,)),
        ("created_at=''", ()),
    ],
)
def test_store_reads_fail_closed_for_invalid_active_rows(tmp_path, assignments, params):
    store = _store(tmp_path)
    store.create("domain", "example.com", "", "it-sub")
    _replace_active_row(store, assignments, params)

    with pytest.raises(assets.AssetsUnavailable):
        store.list()
    with pytest.raises(assets.AssetsUnavailable):
        store.snapshot()


def test_lookup_rejects_invalid_snapshot_before_adapter_call(tmp_path, rsa_keys):
    store = _store(tmp_path)
    store.create("domain", "example.com", "", "it-sub")
    _replace_active_row(store, "canonical_value='com'")

    class Port:
        calls = 0

        def lookup(self, _ioc, _allowed):
            self.calls += 1
            return None

    port = Port()
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store, lookup_port=port)

    response = client.get("/api/ioc?value=attacker.com", headers=_auth(private_key))

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "lookup_unavailable"
    assert port.calls == 0


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_mutation_read_rejects_invalid_stored_row_without_changes(tmp_path, operation):
    store = _store(tmp_path)
    item = store.create("domain", "example.com", "", "it-sub")
    _replace_active_row(store, "created_by=?", ("s" * 513,))
    before_counts = _row_counts(store)

    with pytest.raises(assets.AssetsUnavailable):
        if operation == "update":
            store.update(item.id, "domain", "new.example", "", item.version, "it-sub")
        else:
            store.delete(item.id, item.version, "it-sub")

    assert _row_counts(store) == before_counts
    with sqlite3.connect(store.path) as connection:
        row = connection.execute(
            "SELECT canonical_value,deleted_at,version FROM assets WHERE id=?", (item.id,)
        ).fetchone()
    assert row == ("example.com", None, 1)


def test_actor_bound_is_checked_before_all_mutation_transactions(tmp_path):
    store = _store(tmp_path)
    actor_512 = "s" * 512
    item = store.create("domain", "example.com", "", actor_512)
    assert item.created_by == actor_512
    before_counts = _row_counts(store)

    with pytest.raises(assets.InvalidAsset):
        store.create("domain", "second.example", "", "s" * 513)
    with pytest.raises(assets.InvalidAsset):
        store.update(item.id, "domain", "new.example", "", item.version, "s" * 513)
    with pytest.raises(assets.InvalidAsset):
        store.delete(item.id, item.version, "s" * 513)

    assert _row_counts(store) == before_counts
    assert store.list() == (item,)


def test_http_rejects_long_verified_subject_without_commit(tmp_path, rsa_keys):
    subject = "s" * 513
    store = _store(tmp_path)
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        asset_store=store,
        subjects={subject: frozenset({"it"})},
    )

    response = client.post(
        "/api/assets",
        headers=_mutation_headers(private_key, subject),
        json={"type": "domain", "value": "subject.example", "note": ""},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_asset"
    assert subject not in response.text
    assert _row_counts(store) == (0, 0)


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_version_increment_overflow_rolls_back_without_audit(tmp_path, operation):
    store = _store(tmp_path)
    item = store.create("domain", "example.com", "", "it-sub")
    maximum = 2**53 - 1
    _replace_active_row(store, "version=?", (maximum,))
    before_counts = _row_counts(store)

    with pytest.raises(assets.AssetsUnavailable):
        if operation == "update":
            store.update(item.id, "domain", "new.example", "", maximum, "it-sub")
        else:
            store.delete(item.id, maximum, "it-sub")

    assert _row_counts(store) == before_counts
    with sqlite3.connect(store.path) as connection:
        row = connection.execute(
            "SELECT canonical_value,deleted_at,version FROM assets WHERE id=?", (item.id,)
        ).fetchone()
    assert row == ("example.com", None, maximum)


def test_create_output_id_overflow_rolls_back_without_audit(tmp_path):
    store = _store(tmp_path)
    now = "2026-11-11T00:00:00Z"
    maximum = 2**53 - 1
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "INSERT INTO assets(id,type,canonical_value,note,version,created_by,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (maximum, "domain", "seed.example", "", 1, "seed", now, now),
        )

    with pytest.raises(assets.AssetsUnavailable):
        store.create("domain", "overflow.example", "", "it-sub")

    assert _row_counts(store) == (1, 0)


@pytest.mark.parametrize(
    ("name_length", "expected_status"),
    [(128, 200), (129, 200), (253, 200), (254, 503)],
)
def test_asset_fact_name_uses_253_character_bound(tmp_path, rsa_keys, name_length, expected_status):
    record = _record(assets=(w02_test_api.AssetFact(name="a" * name_length, tlp="TLP:GREEN"),))
    port = w02_test_api.FixtureLookupPort({w02_test_api.EVIL_DOMAIN: record})
    client, private_key = _client(tmp_path, rsa_keys, lookup_port=port)

    response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key))

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["asset_match"]["assets"] == ["a" * name_length]
    else:
        assert response.json()["error"]["code"] == "lookup_unavailable"


@pytest.mark.parametrize("operation", ["create", "update"])
def test_audit_integrity_failure_is_unavailable_and_rolls_back(tmp_path, rsa_keys, operation):
    store = _store(tmp_path)
    item = None
    if operation == "update":
        item = store.create("domain", "before.example", "", "it-sub")
    before_counts = _row_counts(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_asset_audit BEFORE INSERT ON asset_audit "
            "BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END"
        )
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    body = {"type": "domain", "value": "after.example", "note": ""}

    if operation == "create":
        response = client.post("/api/assets", headers=_mutation_headers(private_key), json=body)
    else:
        response = client.put(
            f"/api/assets/{item.id}",
            headers=_mutation_headers(private_key),
            json={**body, "expected_version": item.version},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "assets_unavailable"
    assert _row_counts(store) == before_counts
    if item is not None:
        assert store.list() == (item,)


@pytest.mark.parametrize("operation", ["create", "update"])
def test_true_active_duplicate_is_conflict_without_extra_audit(tmp_path, rsa_keys, operation):
    store = _store(tmp_path)
    first = store.create("domain", "duplicate.example", "", "it-sub")
    second = None
    if operation == "update":
        second = store.create("domain", "other.example", "", "it-sub")
    before_counts = _row_counts(store)
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    body = {"type": "domain", "value": "duplicate.example", "note": ""}

    if operation == "create":
        response = client.post("/api/assets", headers=_mutation_headers(private_key), json=body)
    else:
        response = client.put(
            f"/api/assets/{second.id}",
            headers=_mutation_headers(private_key),
            json={**body, "expected_version": second.version},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "asset_exists"
    assert _row_counts(store) == before_counts
    assert store.list() == ((first,) if second is None else (first, second))


@pytest.mark.parametrize("operation", ["create", "update"])
def test_unrelated_unique_failure_is_unavailable_and_rolls_back(tmp_path, rsa_keys, operation):
    store = _store(tmp_path)
    item = store.create("domain", "company.example", "", "it-sub")
    before_counts = _row_counts(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute("CREATE TABLE synthetic_guard (value TEXT UNIQUE)")
        connection.execute("INSERT INTO synthetic_guard VALUES ('taken')")
        action = "INSERT" if operation == "create" else "UPDATE"
        connection.execute(
            f"CREATE TRIGGER unrelated_unique BEFORE {action} ON assets "
            "BEGIN INSERT INTO synthetic_guard VALUES ('taken'); END"
        )
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    body = {"type": "domain", "value": "company.example", "note": "changed"}

    if operation == "create":
        response = client.post("/api/assets", headers=_mutation_headers(private_key), json=body)
    else:
        response = client.put(
            f"/api/assets/{item.id}",
            headers=_mutation_headers(private_key),
            json={**body, "expected_version": item.version},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "assets_unavailable"
    assert "synthetic_guard" not in response.text
    assert _row_counts(store) == before_counts
    assert store.list() == (item,)


@pytest.mark.parametrize("operation", ["create", "update"])
def test_non_unique_asset_trigger_wins_over_existing_duplicate(tmp_path, rsa_keys, operation):
    store = _store(tmp_path)
    store.create("domain", "duplicate.example", "", "it-sub")
    item = None
    if operation == "update":
        item = store.create("domain", "other.example", "", "it-sub")
    before_counts = _row_counts(store)
    with sqlite3.connect(store.path) as connection:
        action = "INSERT" if operation == "create" else "UPDATE"
        connection.execute(
            f"CREATE TRIGGER reject_asset_write BEFORE {action} ON assets "
            "BEGIN SELECT RAISE(ABORT, 'synthetic asset trigger failure'); END"
        )
    client, private_key = _client(tmp_path, rsa_keys, asset_store=store)
    body = {"type": "domain", "value": "duplicate.example", "note": ""}

    if operation == "create":
        response = client.post("/api/assets", headers=_mutation_headers(private_key), json=body)
    else:
        response = client.put(
            f"/api/assets/{item.id}",
            headers=_mutation_headers(private_key),
            json={**body, "expected_version": item.version},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "assets_unavailable"
    assert _row_counts(store) == before_counts
