from __future__ import annotations

import base64
import json
import math
import socket
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft
from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.settings import Settings, SettingsError

ISSUER = "https://access.synthetic.test"
AUDIENCE = "synthetic-audience"
JWKS_URL = f"{ISSUER}/cdn-cgi/access/certs"
PORTAL_ORIGIN = "https://portal.synthetic.test:8443"
JWT_HEADER = "Cf-Access-Jwt-Assertion"


def _b64uint(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(size, "big")).rstrip(b"=").decode("ascii")


@pytest.fixture(scope="session")
def rsa_keys() -> tuple[Any, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private_key.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": "synthetic-key-1",
        "use": "sig",
        "alg": "RS256",
        "n": _b64uint(public.n),
        "e": _b64uint(public.e),
    }
    return private_key, jwk


class LocalJwksClient:
    def __init__(self, jwk: dict[str, str]):
        self.jwk = jwk
        self.calls = 0

    def get_signing_key_from_jwt(self, token: str):
        self.calls += 1
        header = jwt.get_unverified_header(token)
        if header.get("kid") != self.jwk["kid"]:
            raise jwt.PyJWKClientError("unknown synthetic kid")
        return jwt.PyJWK.from_dict(self.jwk)


class UnavailableJwksClient:
    def get_signing_key_from_jwt(self, _token: str):
        raise jwt.PyJWKClientConnectionError("synthetic network outage")


def make_settings(db: Path, roles: dict[str, frozenset[str]] | None = None) -> Settings:
    return Settings(
        db_path=db,
        access_issuer=ISSUER,
        access_audience=AUDIENCE,
        access_jwks_url=JWKS_URL,
        portal_origin=PORTAL_ORIGIN,
        roles_by_subject=roles
        or {
            "analyst-sub": frozenset({"analyst"}),
            "admin-sub": frozenset({"admin"}),
            "it-sub": frozenset({"it"}),
            "author-sub": frozenset({"analyst"}),
        },
        sqlite_timeout=0.01,
    )


def sign_token(
    private_key,
    *,
    subject: Any = "analyst-sub",
    issuer: str = ISSUER,
    audience: Any = AUDIENCE,
    expires: timedelta = timedelta(minutes=5),
    algorithm: str = "RS256",
    key_id: str = "synthetic-key-1",
    extra: dict[str, Any] | None = None,
    omit: set[str] = frozenset(),
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now - timedelta(seconds=1),
        "exp": now + expires,
    }
    claims.update(extra or {})
    for name in omit:
        claims.pop(name, None)
    key = private_key if algorithm == "RS256" else "synthetic-hmac-secret-that-is-long-enough"
    return jwt.encode(claims, key, algorithm=algorithm, headers={"kid": key_id})


def sign_with_wrong_rsa_key(**kwargs) -> str:
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return sign_token(wrong_key, **kwargs)


def unsigned_token() -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": "analyst-sub", "iss": ISSUER, "aud": AUDIENCE, "exp": now + timedelta(minutes=5)},
        key="",
        algorithm="none",
        headers={"kid": "synthetic-key-1"},
    )


def auth_headers(token: str) -> dict[str, str]:
    return {JWT_HEADER: token}


def save_three_drafts(db: Path) -> tuple[int, int, int]:
    ids = []
    for index, creator in enumerate(("author-sub", "analyst-sub", "other-author"), start=1):
        draft = build_regex_draft(
            f"Synthetic report {index} 😀 evil{index}.example",
            source=f"synthetic-{index}.txt",
            language="vi",
        )
        ids.append(store.save_draft(db, draft, created_by_subject=creator))
    return tuple(ids)


@pytest.fixture
def api(tmp_path: Path, rsa_keys):
    db = tmp_path / "drafts.sqlite"
    draft_ids = save_three_drafts(db)
    private_key, jwk = rsa_keys
    settings = make_settings(db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)
    return client, db, draft_ids, private_key


def assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status
    assert response.json().keys() == {"error"}
    assert response.json()["error"].keys() == {"code", "message"}
    assert response.json()["error"]["code"] == code
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"].lower() == JWT_HEADER.lower()


def test_valid_signed_analyst_lists_pending_summaries_without_content(api):
    client, _, draft_ids, private_key = api
    response = client.get("/api/drafts?limit=2", headers=auth_headers(sign_token(private_key)))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == list(reversed(draft_ids[1:]))
    assert response.json()["next_before_id"] == draft_ids[1]
    for item in response.json()["items"]:
        assert not {"text", "items", "evidence", "findings"}.intersection(item)
    assert "evil" not in response.text


def test_valid_signed_admin_reads_payload_pending_and_separate_review(api):
    client, _, draft_ids, private_key = api
    token = sign_token(private_key, subject="admin-sub", extra={"role": "it"})
    response = client.get(f"/api/drafts/{draft_ids[0]}", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["review"] == {
        "status": "pending",
        "version": 0,
        "created_by_subject": "author-sub",
        "decided_by_subject": None,
        "decided_at": None,
        "reason": None,
    }
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("audience", [AUDIENCE, [AUDIENCE], ["extra-audience", AUDIENCE]])
def test_valid_signed_token_accepts_exact_audience_string_or_array_membership(api, audience):
    client, _, _, private_key = api

    response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key, audience=audience)))

    assert response.status_code == 200


@pytest.mark.parametrize(
    "token_factory",
    [
        lambda key: "not-a-jwt",
        lambda key: sign_token(key, expires=timedelta(seconds=-1)),
        lambda key: sign_token(key, issuer="https://wrong.synthetic.test"),
        lambda key: sign_token(key, audience="wrong-audience"),
        lambda key: sign_token(key, audience=[]),
        lambda key: sign_token(key, audience=["wrong-audience"]),
        lambda key: sign_token(key, audience=[AUDIENCE, ""]),
        lambda key: sign_token(key, audience=[AUDIENCE, 7]),
        lambda key: sign_token(key, audience=[[AUDIENCE]]),
        lambda key: sign_token(key, subject=""),
        lambda key: sign_token(key, omit={"sub"}),
        lambda key: sign_token(key, omit={"exp"}),
        lambda key: sign_token(key, omit={"iss"}),
        lambda key: sign_token(key, omit={"aud"}),
        lambda key: sign_token(key, key_id="unknown-key"),
        lambda key: sign_token(key, algorithm="HS256"),
        lambda key: unsigned_token(),
        lambda key: sign_with_wrong_rsa_key(),
        lambda key: sign_token(key, extra={"exp": "9999999999"}),
        lambda key: sign_token(key, extra={"iat": True}),
        lambda key: sign_token(key, extra={"nbf": math.inf}),
        lambda key: sign_token(key, extra={"iat": datetime.now(UTC) + timedelta(minutes=10)}),
        lambda key: sign_token(key, extra={"nbf": datetime.now(UTC) + timedelta(minutes=10)}),
    ],
)
def test_invalid_tokens_return_same_sanitized_401_without_store_access(tmp_path, rsa_keys, token_factory):
    private_key, jwk = rsa_keys
    missing_db = tmp_path / "must-not-be-opened.sqlite"
    settings = make_settings(missing_db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.get("/api/drafts", headers=auth_headers(token_factory(private_key)))

    assert_error(response, 401, "authentication_required")
    assert not missing_db.exists()
    assert response.json()["error"]["message"] == "Cần xác thực hợp lệ"


def test_missing_token_is_401_before_invalid_query_or_database_access(tmp_path: Path, rsa_keys):
    _, jwk = rsa_keys
    missing_db = tmp_path / "missing.sqlite"
    settings = make_settings(missing_db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.get("/api/drafts?limit=bad")

    assert_error(response, 401, "authentication_required")
    assert not missing_db.exists()


def test_jwks_connection_failure_is_sanitized_503_not_invalid_token(tmp_path: Path, rsa_keys):
    private_key, _ = rsa_keys
    missing_db = tmp_path / "missing.sqlite"
    settings = make_settings(missing_db)
    verifier = AccessJwtVerifier(settings, jwks_client=UnavailableJwksClient())
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key)))

    assert_error(response, 503, "review_unavailable")
    assert not missing_db.exists()


def test_authentication_runs_before_post_origin_media_and_body_validation(tmp_path: Path, rsa_keys):
    _, jwk = rsa_keys
    missing_db = tmp_path / "missing.sqlite"
    settings = make_settings(missing_db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.post("/api/drafts/not-an-id/decision", content=b"not json")

    assert_error(response, 401, "authentication_required")
    assert not missing_db.exists()


@pytest.mark.parametrize("subject", ["unknown-sub", "it-sub"])
def test_server_side_role_absent_or_it_returns_403_even_if_token_claims_admin(api, subject):
    client, db, _, private_key = api
    before = db.read_bytes()
    token = sign_token(private_key, subject=subject, extra={"roles": ["admin"]})

    response = client.get("/api/drafts", headers=auth_headers(token))

    assert_error(response, 403, "forbidden")
    assert db.read_bytes() == before


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/drafts?limit=0", "invalid_request"),
        ("/api/drafts?limit=true", "invalid_request"),
        ("/api/drafts?limit=101", "invalid_request"),
        ("/api/drafts?before_id=0", "invalid_request"),
        ("/api/drafts?before_id=true", "invalid_request"),
        ("/api/drafts/not-an-id", "invalid_request"),
        (f"/api/drafts/{2**63}", "invalid_request"),
    ],
)
def test_invalid_query_and_path_values_return_exact_422(api, path, expected):
    client, _, _, private_key = api
    response = client.get(path, headers=auth_headers(sign_token(private_key)))
    assert_error(response, 422, expected)


@pytest.mark.parametrize(
    "path",
    [
        "/api/drafts?limit=" + "9" * 5000,
        "/api/drafts?before_id=" + "9" * 5000,
        "/api/drafts/" + "9" * 5000,
    ],
)
def test_oversized_integer_inputs_return_422_before_store_access(tmp_path, rsa_keys, path):
    private_key, jwk = rsa_keys
    missing_db = tmp_path / "must-not-be-opened.sqlite"
    settings = make_settings(missing_db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.get(path, headers=auth_headers(sign_token(private_key)))

    assert_error(response, 422, "invalid_request")
    assert not missing_db.exists()


@pytest.mark.parametrize(
    "body",
    [
        {"decision": "approve", "expected_version": True},
        {"decision": "approve", "expected_version": 0, "reason": "not allowed"},
        {"decision": "reject", "expected_version": 0},
        {"decision": "reject", "expected_version": 0, "reason": []},
        {"decision": "other", "expected_version": 0},
        {"decision": "approve", "expected_version": 0, "subject": "attacker"},
        {"decision": "approve", "expected_version": 0, "role": "admin"},
        {"decision": "approve", "expected_version": 0, "email": "x@example.test"},
    ],
)
def test_post_body_is_exact_and_rejects_bool_version_wrong_reason_and_identity_fields(api, body):
    client, db, draft_ids, private_key = api
    before = db.read_bytes()
    response = client.post(
        f"/api/drafts/{draft_ids[0]}/decision",
        headers={**auth_headers(sign_token(private_key, subject="admin-sub")), "Origin": PORTAL_ORIGIN},
        json=body,
    )
    assert_error(response, 422, "invalid_request")
    assert db.read_bytes() == before


@pytest.mark.parametrize(
    "content_type", [None, "text/plain", "application/problem+json", "application/jsonx"]
)
def test_post_requires_application_json_before_body_or_store_access(api, content_type):
    client, db, draft_ids, private_key = api
    before = db.read_bytes()
    headers = {**auth_headers(sign_token(private_key, subject="admin-sub")), "Origin": PORTAL_ORIGIN}
    if content_type:
        headers["Content-Type"] = content_type
    response = client.post(
        f"/api/drafts/{draft_ids[0]}/decision",
        headers=headers,
        content=b'{"decision":"approve","expected_version":0}',
    )
    assert_error(response, 415, "unsupported_media_type")
    assert db.read_bytes() == before


def test_post_accepts_application_json_with_charset(api):
    client, _, draft_ids, private_key = api
    response = client.post(
        f"/api/drafts/{draft_ids[0]}/decision",
        headers={
            **auth_headers(sign_token(private_key, subject="admin-sub")),
            "Origin": PORTAL_ORIGIN,
            "Content-Type": "application/json; charset=utf-8",
        },
        content=b'{"decision":"approve","expected_version":0}',
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "origin",
    [
        None,
        "null",
        "https://evil.synthetic.test",
        f"{PORTAL_ORIGIN}.evil.test",
        f"{PORTAL_ORIGIN}/path",
        "https://user@portal.synthetic.test:8443",
        f"{PORTAL_ORIGIN}, https://evil.test",
    ],
)
def test_post_requires_one_exact_valid_origin_without_writing(api, origin):
    client, db, draft_ids, private_key = api
    before = db.read_bytes()
    headers = auth_headers(sign_token(private_key, subject="admin-sub"))
    if origin is not None:
        headers["Origin"] = origin
    response = client.post(
        f"/api/drafts/{draft_ids[0]}/decision",
        headers=headers,
        json={"decision": "approve", "expected_version": 0},
    )
    assert_error(response, 403, "forbidden")
    assert db.read_bytes() == before


def test_analyst_cannot_approve_own_or_unknown_creator_and_audit_stays_empty(api):
    client, db, draft_ids, private_key = api
    legacy_id = store.save_draft(
        db, build_regex_draft("legacy evil.example", source="legacy.txt", language="vi")
    )
    for draft_id in (draft_ids[1], legacy_id):
        response = client.post(
            f"/api/drafts/{draft_id}/decision",
            headers={**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN},
            json={"decision": "approve", "expected_version": 0},
        )
        assert_error(response, 403, "forbidden")
    connection = sqlite3.connect(db)
    try:
        assert connection.execute("SELECT COUNT(*) FROM draft_audit").fetchone()[0] == 0
    finally:
        connection.close()


def test_unsupported_kept_kind_maps_to_403_without_audit(api):
    client, db, _, private_key = api
    draft = build_regex_draft("evil.example", source="unsupported.txt", language="vi")
    draft["items"][0]["kind"] = "ttp"
    draft_id = store.save_draft(db, draft, created_by_subject="author-sub")
    response = client.post(
        f"/api/drafts/{draft_id}/decision",
        headers={**auth_headers(sign_token(private_key, subject="admin-sub")), "Origin": PORTAL_ORIGIN},
        json={"decision": "approve", "expected_version": 0},
    )
    assert_error(response, 403, "forbidden")


def test_analyst_can_reject_own_draft_with_trimmed_reason_and_one_audit(api):
    client, db, draft_ids, private_key = api
    response = client.post(
        f"/api/drafts/{draft_ids[1]}/decision",
        headers={**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN},
        json={"decision": "reject", "expected_version": 0, "reason": "  Thiếu ngữ cảnh  "},
    )
    assert response.status_code == 200
    assert response.json() == {
        "draft_id": draft_ids[1],
        "status": "rejected",
        "version": 1,
        "decided_by_subject": "analyst-sub",
        "decided_at": response.json()["decided_at"],
        "reason": "Thiếu ngữ cảnh",
    }
    connection = sqlite3.connect(db)
    try:
        audit = connection.execute("SELECT actor_subject, reason FROM draft_audit").fetchall()
    finally:
        connection.close()
    assert audit == [("analyst-sub", "Thiếu ngữ cảnh")]


def test_admin_approves_other_creator_once_preserving_payload_and_repeat_is_409(api):
    client, db, draft_ids, private_key = api
    draft_id = draft_ids[0]
    before_payload = (
        sqlite3.connect(db).execute("SELECT payload_json FROM drafts WHERE id = ?", (draft_id,)).fetchone()[0]
    )
    headers = {**auth_headers(sign_token(private_key, subject="admin-sub")), "Origin": PORTAL_ORIGIN}

    approved = client.post(
        f"/api/drafts/{draft_id}/decision",
        headers=headers,
        json={"decision": "approve", "expected_version": 0},
    )
    repeated = client.post(
        f"/api/drafts/{draft_id}/decision",
        headers=headers,
        json={"decision": "approve", "expected_version": 0},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["version"] == 1
    assert_error(repeated, 409, "draft_conflict")
    connection = sqlite3.connect(db)
    try:
        after_payload = connection.execute(
            "SELECT payload_json FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()[0]
        assert connection.execute("SELECT COUNT(*) FROM draft_audit").fetchone()[0] == 1
    finally:
        connection.close()
    assert after_payload == before_payload
    assert json.loads(after_payload)["status"] == "pending"


def test_unknown_authenticated_id_is_404(api):
    client, _, _, private_key = api
    response = client.get("/api/drafts/999999", headers=auth_headers(sign_token(private_key)))
    assert_error(response, 404, "draft_not_found")


@pytest.mark.parametrize("mode", ["missing", "corrupt", "future"])
def test_database_unavailable_or_unsupported_schema_is_sanitized_503(tmp_path, rsa_keys, mode):
    private_key, jwk = rsa_keys
    db = tmp_path / f"{mode}.sqlite"
    if mode == "corrupt":
        db.write_bytes(b"not sqlite and secret marker")
    elif mode == "future":
        db.touch()
        connection = sqlite3.connect(db)
        connection.execute("PRAGMA user_version = 99")
        connection.commit()
        connection.close()
    settings = make_settings(db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)
    response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key)))
    assert_error(response, 503, "review_unavailable")
    assert "secret marker" not in response.text
    assert str(db) not in response.text


def test_unexpected_store_error_is_sanitized_503_with_no_store_headers(tmp_path, rsa_keys, caplog):
    class UnexpectedStore:
        @staticmethod
        def list_drafts(*_args, **_kwargs):
            raise RuntimeError("SYNTHETIC-SENSITIVE-MARKER")

    private_key, jwk = rsa_keys
    settings = make_settings(tmp_path / "unused.sqlite")
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(
        create_app(settings, UnexpectedStore(), verifier=verifier), raise_server_exceptions=False
    )

    response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key)))

    assert_error(response, 503, "review_unavailable")
    assert "SYNTHETIC-SENSITIVE-MARKER" not in response.text
    assert "SYNTHETIC-SENSITIVE-MARKER" not in caplog.text


def test_locked_database_is_sanitized_503(api):
    client, db, _, private_key = api
    locker = sqlite3.connect(db, timeout=0.01)
    try:
        locker.execute("BEGIN EXCLUSIVE")
        response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key)))
    finally:
        locker.rollback()
        locker.close()
    assert_error(response, 503, "review_unavailable")


def test_unexpected_persisted_item_status_returns_503_not_partial_detail(api):
    client, db, draft_ids, private_key = api
    connection = sqlite3.connect(db)
    try:
        payload = json.loads(
            connection.execute("SELECT payload_json FROM drafts WHERE id = ?", (draft_ids[0],)).fetchone()[0]
        )
        payload["items"][0]["status"] = "future-status"
        connection.execute(
            "UPDATE drafts SET payload_json = ? WHERE id = ?",
            (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")), draft_ids[0]),
        )
        connection.commit()
    finally:
        connection.close()
    response = client.get(f"/api/drafts/{draft_ids[0]}", headers=auth_headers(sign_token(private_key)))
    assert_error(response, 503, "review_unavailable")
    assert "future-status" not in response.text


def test_all_success_and_error_responses_are_no_store_and_no_wildcard_cors(api):
    client, _, draft_ids, private_key = api
    token = sign_token(private_key)
    responses = [
        client.get("/api/drafts", headers=auth_headers(token)),
        client.get(f"/api/drafts/{draft_ids[0]}", headers=auth_headers(token)),
        client.get("/api/drafts/0", headers=auth_headers(token)),
    ]
    for response in responses:
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"].lower() == JWT_HEADER.lower()
        assert response.headers.get("access-control-allow-origin") != "*"


def test_openapi_has_no_subject_role_or_email_request_fields(api):
    client, _, _, _ = api
    schema = client.get("/openapi.json").json()
    decision_schema = schema["components"]["schemas"]["DecisionRequest"]
    assert set(decision_schema["properties"]) == {"decision", "expected_version", "reason"}
    serialized = json.dumps(schema["paths"]["/api/drafts/{draft_id}/decision"])
    assert "Cf-Access-Authenticated-User-Email" not in serialized
    assert "X-API-Key" not in serialized


@pytest.mark.parametrize(
    "kwargs",
    [
        {"access_issuer": ""},
        {"access_issuer": "http://access.synthetic.test"},
        {"access_issuer": "https://access.synthetic.test/"},
        {"access_jwks_url": "http://access.synthetic.test/certs"},
        {"access_jwks_url": "https://other.synthetic.test/certs"},
        {"access_audience": ""},
        {"portal_origin": "null"},
        {"portal_origin": "https://user@portal.synthetic.test"},
        {"portal_origin": "https://portal.synthetic.test/path"},
    ],
)
def test_invalid_or_missing_settings_fail_app_factory_closed(tmp_path: Path, kwargs):
    values = {
        "db_path": tmp_path / "db.sqlite",
        "access_issuer": ISSUER,
        "access_audience": AUDIENCE,
        "access_jwks_url": JWKS_URL,
        "portal_origin": PORTAL_ORIGIN,
        "roles_by_subject": {},
    }
    values.update(kwargs)
    with pytest.raises(SettingsError):
        Settings(**values)


def test_settings_from_environment_requires_every_value_and_server_side_role_json(tmp_path: Path):
    with pytest.raises(SettingsError):
        Settings.from_env({})

    env = {
        "W05_DB_PATH": str(tmp_path / "drafts.sqlite"),
        "CF_ACCESS_ISSUER": ISSUER,
        "CF_ACCESS_AUD": AUDIENCE,
        "CF_ACCESS_JWKS_URL": JWKS_URL,
        "PORTAL_ORIGIN": PORTAL_ORIGIN,
        "W05_ROLES_JSON": json.dumps({"analyst-sub": ["analyst"], "it-sub": ["it"]}),
    }
    settings = Settings.from_env(env)

    assert settings.db_path == tmp_path / "drafts.sqlite"
    assert settings.roles_by_subject == {
        "analyst-sub": frozenset({"analyst"}),
        "it-sub": frozenset({"it"}),
    }
    with pytest.raises(SettingsError):
        Settings.from_env({**env, "W05_ROLES_JSON": "not-json"})


def test_injected_jwks_verification_never_uses_network(tmp_path, rsa_keys, monkeypatch):
    private_key, jwk = rsa_keys
    db = tmp_path / "db.sqlite"
    save_three_drafts(db)
    settings = make_settings(db)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: pytest.fail("network used"))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)

    response = client.get("/api/drafts", headers=auth_headers(sign_token(private_key)))

    assert response.status_code == 200


def test_raw_token_and_report_text_are_absent_from_errors_and_logs(api, caplog):
    client, _, _, private_key = api
    marker = "RAW-TOKEN-MARKER"
    bad_token = sign_token(private_key) + marker
    response = client.get("/api/drafts", headers=auth_headers(bad_token))
    combined = response.text + "\n" + caplog.text
    assert marker not in combined
    assert "Synthetic report" not in combined
    assert "evil1.example" not in combined


def test_v1_list_and_detail_expose_exact_atomic_selection_shape(api):
    client, _db, draft_ids, private_key = api
    headers = auth_headers(sign_token(private_key))
    page = client.get("/api/v1/drafts", headers=headers)
    assert page.status_code == 200
    assert set(page.json()["items"][0]) == {
        "id",
        "created_at",
        "status",
        "source",
        "language",
        "tlp",
        "item_count",
        "injection_warning",
        "review_status",
        "review_version",
        "selection_version",
    }
    detail = client.get(f"/api/v1/drafts/{draft_ids[0]}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["review"]["version"] == detail.json()["selection"]["review_version"] == 0
    assert detail.json()["selection"]["selection_version"] == 0
    assert detail.json()["selection"]["selected_indices"] == [0]
    assert "draft_id" not in detail.json()["selection"]
    assert detail.headers["cache-control"] == "no-store"


def test_v1_selection_changed_noop_and_reject_return_committed_snapshots(api):
    client, db, draft_ids, private_key = api
    headers = {**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN}
    draft_id = draft_ids[0]
    changed = client.post(
        f"/api/v1/drafts/{draft_id}/selection",
        headers=headers,
        json={"expected_version": 0, "selected_indices": []},
    )
    assert changed.status_code == 200
    assert changed.json()["changed"] is True
    assert changed.json()["review_version"] == changed.json()["selection_version"] == 1
    assert changed.json()["selected_indices"] == []
    assert "draft_id" not in changed.json()
    noop = client.post(
        f"/api/v1/drafts/{draft_id}/selection",
        headers=headers,
        json={"expected_version": 1, "selected_indices": []},
    )
    assert noop.status_code == 200
    assert noop.json()["changed"] is False
    with sqlite3.connect(db) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM draft_selection_audit WHERE draft_id=?", (draft_id,)
            ).fetchone()[0]
            == 1
        )
    empty_approve = client.post(
        f"/api/v1/drafts/{draft_id}/decision",
        headers=headers,
        json={"decision": "approve", "expected_version": 1},
    )
    assert_error(empty_approve, 403, "forbidden")
    rejected = client.post(
        f"/api/v1/drafts/{draft_id}/decision",
        headers=headers,
        json={"decision": "reject", "expected_version": 1, "reason": "  Không đủ bằng chứng  "},
    )
    assert rejected.status_code == 200
    assert rejected.json()["version"] == 2
    assert rejected.json()["selection_version"] == 1
    assert rejected.json()["selected_indices"] == []
    assert rejected.json()["reason"] == "Không đủ bằng chứng"


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"expected_version": 0, "selected_indices": [0, 0]}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [True]}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": None}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": "0"}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [{}]}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [-1]}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [2**53]}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [], "subject": "spoof"}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": list(range(1025))}, 422, "invalid_request"),
        ({"expected_version": 0, "selected_indices": [999]}, 403, "forbidden"),
    ],
)
def test_v1_selection_rejects_invalid_or_noneligible_input_without_mutation(api, body, status, code):
    client, db, draft_ids, private_key = api
    before = db.read_bytes()
    response = client.post(
        f"/api/v1/drafts/{draft_ids[0]}/selection",
        headers={**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN},
        json=body,
    )
    assert_error(response, status, code)
    assert db.read_bytes() == before


def test_v1_streaming_body_limit_accepts_boundary_and_rejects_one_byte_over(api):
    client, _db, draft_ids, private_key = api
    headers = {
        **auth_headers(sign_token(private_key)),
        "Origin": PORTAL_ORIGIN,
        "Content-Type": "application/json",
    }
    core = b'{"expected_version":0,"selected_indices":[0]}'
    boundary = b" " * (65536 - len(core)) + core
    accepted = client.post(
        f"/api/v1/drafts/{draft_ids[0]}/selection",
        headers=headers,
        content=(part for part in (boundary[:1000], boundary[1000:])),
    )
    assert accepted.status_code == 200
    oversized = b" " + boundary
    rejected = client.post(
        f"/api/v1/drafts/{draft_ids[1]}/selection",
        headers=headers,
        content=(part for part in (oversized[:13], oversized[13:])),
    )
    assert_error(rejected, 413, "request_too_large")


def test_v1_missing_database_is_503_but_missing_row_is_404(tmp_path: Path, rsa_keys):
    missing = tmp_path / "missing.sqlite"
    private_key, jwk = rsa_keys
    settings = make_settings(missing)
    verifier = AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))
    client = TestClient(create_app(settings, store, verifier=verifier), raise_server_exceptions=False)
    headers = auth_headers(sign_token(private_key))
    assert_error(client.get("/api/v1/drafts", headers=headers), 503, "review_unavailable")
    db = tmp_path / "exists.sqlite"
    store.save_draft(db, build_regex_draft("x.example", source="x.txt", language="vi"))
    settings = make_settings(db)
    client = TestClient(
        create_app(settings, store, verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))),
        raise_server_exceptions=False,
    )
    assert_error(client.get("/api/v1/drafts/999", headers=headers), 404, "draft_not_found")


def test_missing_database_keeps_legacy_decision_404_while_v1_decision_is_503(tmp_path: Path, rsa_keys):
    missing = tmp_path / "missing-decision.sqlite"
    private_key, jwk = rsa_keys
    settings = make_settings(missing)
    client = TestClient(
        create_app(settings, store, verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))),
        raise_server_exceptions=False,
    )
    headers = {**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN}
    body = {"decision": "reject", "expected_version": 0, "reason": "x"}

    assert_error(client.post("/api/drafts/1/decision", headers=headers, json=body), 404, "draft_not_found")
    assert_error(
        client.post("/api/v1/drafts/1/decision", headers=headers, json=body),
        503,
        "review_unavailable",
    )


def test_v1_adapter_passes_json_safe_cap(api, monkeypatch):
    client, _db, draft_ids, private_key = api
    seen: list[tuple[str, int]] = []
    original_save = store.save_selection
    original_decide = store.decide_draft_with_selection

    def save(*args, **kwargs):
        seen.append(("save", kwargs["max_version"]))
        return original_save(*args, **kwargs)

    def decide(*args, **kwargs):
        seen.append(("decide", kwargs["max_version"]))
        return original_decide(*args, **kwargs)

    monkeypatch.setattr(store, "save_selection", save)
    monkeypatch.setattr(store, "decide_draft_with_selection", decide)
    monkeypatch.setattr(store, "get_draft_with_selection", lambda *_args, **_kwargs: pytest.fail("reread"))
    headers = {**auth_headers(sign_token(private_key)), "Origin": PORTAL_ORIGIN}
    saved = client.post(
        f"/api/v1/drafts/{draft_ids[0]}/selection",
        headers=headers,
        json={"expected_version": 0, "selected_indices": [0]},
    )
    assert saved.status_code == 200
    decided = client.post(
        f"/api/v1/drafts/{draft_ids[1]}/decision",
        headers=headers,
        json={"decision": "reject", "expected_version": 0, "reason": "x"},
    )
    assert decided.status_code == 200
    assert seen == [("save", 2**53 - 1), ("decide", 2**53 - 1)]


@pytest.mark.parametrize(
    ("headers", "status", "code"),
    [
        ({}, 401, "authentication_required"),
        ({"Content-Type": "application/json"}, 401, "authentication_required"),
    ],
)
def test_v1_authentication_precedes_mutation_validation(api, headers, status, code):
    client, _db, draft_ids, _private_key = api
    response = client.post(f"/api/v1/drafts/{draft_ids[0]}/selection", headers=headers, content=b"not json")
    assert_error(response, status, code)


@pytest.mark.parametrize(
    ("extra_headers", "status", "code"),
    [
        ({}, 403, "forbidden"),
        ({"Origin": "https://wrong.test"}, 403, "forbidden"),
        ({"Origin": PORTAL_ORIGIN}, 415, "unsupported_media_type"),
        ({"Origin": PORTAL_ORIGIN, "Content-Type": "text/plain"}, 415, "unsupported_media_type"),
    ],
)
def test_v1_mutations_require_origin_and_json(api, extra_headers, status, code):
    client, _db, draft_ids, private_key = api
    response = client.post(
        f"/api/v1/drafts/{draft_ids[0]}/selection",
        headers={**auth_headers(sign_token(private_key)), **extra_headers},
        content=b"{}",
    )
    assert_error(response, status, code)


def test_v1_output_above_json_safe_integer_fails_closed(api, monkeypatch):
    client, _db, draft_ids, private_key = api
    original = store.get_draft_with_selection

    def unsafe(*args, **kwargs):
        value = original(*args, **kwargs)
        value["selection"] = replace(value["selection"], review_version=2**53)
        return value

    monkeypatch.setattr(store, "get_draft_with_selection", unsafe)
    response = client.get(f"/api/v1/drafts/{draft_ids[0]}", headers=auth_headers(sign_token(private_key)))
    assert_error(response, 503, "review_unavailable")


def test_v1_mixed_schema_is_503_and_read_does_not_mutate(api):
    client, db, _draft_ids, private_key = api
    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA user_version = 1")
    before = db.read_bytes()
    response = client.get("/api/v1/drafts", headers=auth_headers(sign_token(private_key)))
    assert_error(response, 503, "review_unavailable")
    assert db.read_bytes() == before


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/drafts?limit=1&limit=2",
        "/api/v1/drafts?unknown=1",
        f"/api/v1/drafts/{2**53}",
    ],
)
def test_v1_rejects_repeated_unknown_or_unsafe_query_and_path(api, path):
    client, _db, _draft_ids, private_key = api
    response = client.get(path, headers=auth_headers(sign_token(private_key)))
    assert_error(response, 422, "invalid_request")
