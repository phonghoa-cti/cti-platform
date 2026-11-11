from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.schemas import TechnologyPage, TechnologyView
from portal_api.technologies import TechnologyStore
from portal_api.tests import test_w02_ioc_api as w02_test_api
from portal_api.tests.test_w02_ioc_api import LocalJwksClient, _auth, _settings


@pytest.fixture(scope="session")
def rsa_keys():
    return w02_test_api.rsa_keys.__wrapped__()


def _store(tmp_path):
    store = TechnologyStore(tmp_path / "technologies.sqlite", timeout=0.01)
    store.initialize()
    return store


def _client(tmp_path, rsa_keys, *, technology_store=None, subjects=None):
    private_key, jwk = rsa_keys
    settings = _settings(tmp_path)
    if subjects is not None:
        settings = replace(settings, roles_by_subject=subjects)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    app = create_app(settings, object(), verifier=verifier, technology_store=technology_store)
    return TestClient(app, raise_server_exceptions=False), private_key


def _headers(private_key, subject="it-sub", *, origin=True):
    headers = _auth(private_key, subject)
    if origin:
        headers["Origin"] = "https://portal.synthetic.test"
    return headers


def test_routes_are_opt_in_and_auth_role_precede_query_body_and_store(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys)

    unauthenticated = client.get("/api/assets/technologies?bad=x")
    forbidden = client.post(
        "/api/assets/technologies",
        headers={**_headers(private_key, "leader-sub"), "X-Role": "admin"},
        content=b"not-json",
    )
    unavailable = client.get("/api/assets/technologies", headers=_auth(private_key))
    mutation_unavailable = client.post(
        "/api/assets/technologies",
        headers=_headers(private_key),
        json={
            "vendor": "Fortinet",
            "product": "FortiOS",
            "software_version": "7",
            "note": "",
        },
    )

    assert (unauthenticated.status_code, unauthenticated.json()["error"]["code"]) == (
        401,
        "authentication_required",
    )
    assert (forbidden.status_code, forbidden.json()["error"]["code"]) == (403, "forbidden")
    assert (unavailable.status_code, unavailable.json()["error"]["code"]) == (
        503,
        "assets_unavailable",
    )
    assert (mutation_unavailable.status_code, mutation_unavailable.json()["error"]["code"]) == (
        503,
        "assets_unavailable",
    )
    for response in (unauthenticated, forbidden, unavailable, mutation_unavailable):
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"].lower() == "cf-access-jwt-assertion"


@pytest.mark.parametrize("subject", ["it-sub", "analyst-sub", "admin-sub", "multi-sub"])
def test_it_analyst_admin_and_multi_role_can_manage_technologies(tmp_path, rsa_keys, subject):
    subjects = {
        "it-sub": frozenset({"it"}),
        "analyst-sub": frozenset({"analyst"}),
        "admin-sub": frozenset({"admin"}),
        "multi-sub": frozenset({"leader", "it"}),
    }
    client, private_key = _client(tmp_path, rsa_keys, technology_store=_store(tmp_path), subjects=subjects)

    response = client.post(
        "/api/assets/technologies",
        headers=_headers(private_key, subject),
        json={"vendor": "Fortinet", "product": "FortiOS", "software_version": "7.2.1", "note": ""},
    )

    assert response.status_code == 201
    assert set(response.json()) == {
        "id",
        "vendor",
        "product",
        "software_version",
        "note",
        "created_by",
        "created_at",
        "updated_at",
        "version",
    }


def test_http_crud_duplicate_conflict_delete_and_recreate(tmp_path, rsa_keys):
    store = _store(tmp_path)
    client, private_key = _client(tmp_path, rsa_keys, technology_store=store)
    headers = _headers(private_key)
    body = {"vendor": " Fortinet ", "product": " FortiOS ", "software_version": " 7.2.1 ", "note": "VPN"}

    created = client.post("/api/assets/technologies", headers=headers, json=body)
    duplicate = client.post("/api/assets/technologies", headers=headers, json={**body, "vendor": "FORTINET"})
    listed = client.get("/api/assets/technologies", headers=_auth(private_key))
    item = created.json()
    stale = client.put(
        f"/api/assets/technologies/{item['id']}",
        headers=headers,
        json={**body, "note": "new", "expected_version": 2},
    )
    updated = client.put(
        f"/api/assets/technologies/{item['id']}",
        headers=headers,
        json={**body, "note": "new", "expected_version": 1},
    )
    deleted = client.delete(f"/api/assets/technologies/{item['id']}?expected_version=2", headers=headers)
    recreated = client.post("/api/assets/technologies", headers=headers, json=body)

    assert created.status_code == 201
    assert item["software_version"] == "7.2.1"
    assert item["version"] == 1
    assert listed.json() == {"items": [item]}
    assert (duplicate.status_code, duplicate.json()["error"]["code"]) == (409, "technology_exists")
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "technology_conflict")
    assert updated.status_code == 200 and updated.json()["version"] == 2
    assert deleted.status_code == 204 and deleted.content == b""
    assert recreated.status_code == 201 and recreated.json()["id"] > item["id"]

    missing = client.delete("/api/assets/technologies/999?expected_version=1", headers=headers)
    assert (missing.status_code, missing.json()["error"]["code"]) == (
        404,
        "technology_not_found",
    )


@pytest.mark.parametrize(
    ("method", "url", "kwargs", "status", "code"),
    [
        ("get", "/api/assets/technologies?bad=x", {}, 422, "invalid_technology"),
        ("get", "/api/assets/technologies?x=1&x=2", {}, 422, "invalid_technology"),
        ("post", "/api/assets/technologies", {"content": b"{}"}, 403, "forbidden"),
        (
            "post",
            "/api/assets/technologies",
            {"headers": {"Origin": "https://portal.synthetic.test"}, "content": b"{}"},
            415,
            "unsupported_media_type",
        ),
        (
            "post",
            "/api/assets/technologies",
            {
                "headers": {"Origin": "https://portal.synthetic.test", "Content-Type": "application/json"},
                "content": b"x" * 8193,
            },
            413,
            "request_too_large",
        ),
        (
            "post",
            "/api/assets/technologies",
            {
                "json": {
                    "vendor": "Fortinet",
                    "product": "FortiOS",
                    "software_version": "7",
                    "note": "",
                    "extra": 1,
                }
            },
            422,
            "invalid_technology",
        ),
        ("put", "/api/assets/technologies/0", {"json": {}}, 422, "invalid_technology"),
        ("put", f"/api/assets/technologies/{2**53}", {"json": {}}, 422, "invalid_technology"),
        (
            "delete",
            "/api/assets/technologies/1?expected_version=1&expected_version=2",
            {},
            422,
            "invalid_technology",
        ),
    ],
)
def test_http_precedence_and_validation(method, url, kwargs, status, code, tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, technology_store=_store(tmp_path))
    supplied = kwargs.pop("headers", {})
    headers = {**_headers(private_key, origin=False), **supplied}
    if method in {"post", "put", "delete"} and "Origin" not in headers and status != 403:
        headers["Origin"] = "https://portal.synthetic.test"

    response = getattr(client, method)(url, headers=headers, **kwargs)

    assert (response.status_code, response.json()["error"]["code"]) == (status, code)


def test_origin_precedes_bad_path_query_body_and_store(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys)
    headers = _headers(private_key, origin=False)

    update = client.put("/api/assets/technologies/not-an-id", headers=headers, content=b"not-json")
    delete = client.delete("/api/assets/technologies/not-an-id?bad=x", headers=headers)

    assert (update.status_code, update.json()["error"]["code"]) == (403, "forbidden")
    assert (delete.status_code, delete.json()["error"]["code"]) == (403, "forbidden")


def test_subject_512_is_accepted_and_513_rejected_before_write(tmp_path, rsa_keys):
    store = _store(tmp_path)
    subjects = {"x" * 512: frozenset({"it"}), "y" * 513: frozenset({"it"})}
    client, private_key = _client(tmp_path, rsa_keys, technology_store=store, subjects=subjects)
    body = {"vendor": "Fortinet", "product": "FortiOS", "software_version": "7", "note": ""}

    accepted = client.post("/api/assets/technologies", headers=_headers(private_key, "x" * 512), json=body)
    rejected = client.post(
        "/api/assets/technologies",
        headers=_headers(private_key, "y" * 513),
        json={**body, "software_version": "8"},
    )

    assert accepted.status_code == 201
    assert (rejected.status_code, rejected.json()["error"]["code"]) == (422, "invalid_technology")
    assert len(store.list()) == 1


def test_technology_mutations_do_not_change_domain_assets_or_w02_lookup(tmp_path, rsa_keys):
    store = _store(tmp_path)
    client, private_key = _client(tmp_path, rsa_keys, technology_store=store)
    headers = _headers(private_key)

    created = client.post(
        "/api/assets/technologies",
        headers=headers,
        json={"vendor": "Fortinet", "product": "FortiOS", "software_version": "7", "note": ""},
    )
    updated = client.put(
        f"/api/assets/technologies/{created.json()['id']}",
        headers=headers,
        json={
            "vendor": "Fortinet",
            "product": "FortiOS",
            "software_version": "7",
            "note": "new",
            "expected_version": 1,
        },
    )
    deleted = client.delete(
        f"/api/assets/technologies/{created.json()['id']}?expected_version=2", headers=headers
    )
    domain_route = client.get("/api/assets", headers=_auth(private_key))

    assert [created.status_code, updated.status_code, deleted.status_code] == [201, 200, 204]
    assert domain_route.status_code == 503
    assert domain_route.json()["error"]["code"] == "assets_unavailable"


def test_frontend_wire_fixture_matches_exact_response_models_and_error_contract():
    fixture_path = Path(__file__).parent / "fixtures" / "technology-wire.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    TechnologyView.model_validate(fixture["created"]["body"])
    TechnologyPage.model_validate(fixture["list"]["body"])
    assert {fixture[name]["status"] for name in ("duplicate", "conflict")} == {409}
    assert fixture["unavailable"]["status"] == 503
    assert [fixture[name]["body"]["error"]["code"] for name in ("duplicate", "conflict", "unavailable")] == [
        "technology_exists",
        "technology_conflict",
        "assets_unavailable",
    ]
