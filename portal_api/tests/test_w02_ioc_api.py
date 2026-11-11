from __future__ import annotations

import base64
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import ValidationError

from phonghoa_core import Ioc, IocType, normalize
from portal_api.app import JWT_HEADER, create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.ioc_lookup import (
    AssetFact,
    LookupRecord,
    LookupService,
    LookupUnavailable,
    RelatedFact,
    SourceFact,
)
from portal_api.schemas import IocLookupResponse
from portal_api.settings import Settings

NOW = datetime(2026, 11, 11, tzinfo=UTC)
GREEN_SOURCE = SourceFact(
    source_id="alpha",
    name="Synthetic Alpha",
    reliability=0.8,
    first_seen=NOW,
    last_seen=NOW,
    tlp="TLP:GREEN",
)
AMBER_SOURCE = SourceFact(
    source_id="amber",
    name="Synthetic Amber",
    reliability=0.6,
    first_seen=NOW,
    last_seen=NOW,
    tlp="TLP:AMBER",
)
EVIL_DOMAIN = Ioc(IocType.DOMAIN, "evil.example")
ISSUER = "https://access.synthetic.test"
AUDIENCE = "synthetic-audience"
JWKS_URL = f"{ISSUER}/cdn-cgi/access/certs"
PORTAL_ORIGIN = "https://portal.synthetic.test"


class FixtureLookupPort:
    def __init__(self, records: dict[Ioc, LookupRecord] | None = None):
        self.records = records or {}
        self.calls: list[tuple[Ioc, frozenset[str]]] = []

    def lookup(self, ioc: Ioc, allowed_tlps: frozenset[str]) -> LookupRecord | None:
        self.calls.append((ioc, allowed_tlps))
        return self.records.get(ioc)


class ExplodingLookupPort:
    def lookup(self, _ioc: Ioc, _allowed_tlps: frozenset[str]) -> LookupRecord | None:
        raise TimeoutError("synthetic adapter timeout with secret detail")


def _b64uint(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(size, "big")).rstrip(b"=").decode("ascii")


@pytest.fixture(scope="session")
def rsa_keys() -> tuple[Any, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private_key.public_key().public_numbers()
    return private_key, {
        "kty": "RSA",
        "kid": "synthetic-key-1",
        "use": "sig",
        "alg": "RS256",
        "n": _b64uint(public.n),
        "e": _b64uint(public.e),
    }


class LocalJwksClient:
    def __init__(self, jwk: dict[str, str]):
        self.jwk = jwk

    def get_signing_key_from_jwt(self, token: str):
        header = jwt.get_unverified_header(token)
        if header.get("kid") != self.jwk["kid"]:
            raise jwt.PyJWKClientError("unknown synthetic kid")
        return jwt.PyJWK.from_dict(self.jwk)


class UnavailableJwksClient:
    def get_signing_key_from_jwt(self, _token: str):
        raise jwt.PyJWKClientConnectionError("synthetic network outage")


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "drafts.sqlite",
        access_issuer=ISSUER,
        access_audience=AUDIENCE,
        access_jwks_url=JWKS_URL,
        portal_origin=PORTAL_ORIGIN,
        roles_by_subject={
            "it-sub": frozenset({"it"}),
            "analyst-sub": frozenset({"analyst"}),
            "admin-sub": frozenset({"admin"}),
            "multi-sub": frozenset({"it", "analyst"}),
            "leader-sub": frozenset({"leader"}),
        },
        sqlite_timeout=0.01,
    )


def _token(private_key, subject: str, **extra: Any) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "nbf": now - timedelta(seconds=1),
        "exp": now + timedelta(minutes=5),
        **extra,
    }
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "synthetic-key-1"},
    )


def _client(
    tmp_path: Path,
    rsa_keys,
    port: object | None,
    *,
    jwks_client: object | None = None,
) -> tuple[TestClient, Any]:
    private_key, jwk = rsa_keys
    settings = _settings(tmp_path)
    verifier = AccessJwtVerifier(
        settings,
        jwks_client=jwks_client if jwks_client is not None else LocalJwksClient(jwk),
    )
    app = create_app(settings, object(), verifier=verifier, lookup_port=port)
    return TestClient(app, raise_server_exceptions=False), private_key


def _auth(private_key, subject: str = "it-sub", **extra: Any) -> dict[str, str]:
    return {JWT_HEADER: _token(private_key, subject, **extra)}


def _assert_w02_headers(response) -> None:
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"].lower() == JWT_HEADER.lower()


def _assert_error(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": message}}
    _assert_w02_headers(response)


def _record(
    *,
    record_tlp: str = "TLP:GREEN",
    sources: tuple[SourceFact, ...] = (GREEN_SOURCE,),
    related: tuple[RelatedFact, ...] = (),
    assets: tuple[AssetFact, ...] = (),
) -> LookupRecord:
    return LookupRecord(
        ioc=EVIL_DOMAIN,
        record_tlp=record_tlp,
        sources=sources,
        related=related,
        assets=assets,
        as_of=NOW,
    )


def _service(port: FixtureLookupPort) -> LookupService:
    return LookupService(port)


def test_lookup_returns_exact_allowlisted_fixture_without_calling_adapter():
    port = FixtureLookupPort()

    response = _service(port).lookup("8.8.8.8", frozenset({"it"}))

    assert response.model_dump(mode="json") == {
        "ioc": {"type": "ipv4", "value": "8.8.8.8", "display": "8[.]8[.]8[.]8"},
        "state": "allowlisted",
        "found": False,
        "allowlisted": True,
        "score": {
            "value": 0,
            "level": "low",
            "reason": "IOC nằm trong allowlist (hạ tầng hợp pháp) nên điểm = 0.",
            "parts": None,
        },
        "sources": [],
        "related": {"techniques": [], "malware": [], "actors": []},
        "asset_match": {"matched": False, "assets": []},
        "tlp": "TLP:CLEAR",
    }
    assert port.calls == []


def test_lookup_returns_exact_not_found_fixture():
    port = FixtureLookupPort()

    response = _service(port).lookup("unknown.example", frozenset({"it"}))

    assert response.model_dump(mode="json") == {
        "ioc": {"type": "domain", "value": "unknown.example", "display": "unknown[.]example"},
        "state": "not_found",
        "found": False,
        "allowlisted": False,
        "score": None,
        "sources": [],
        "related": {"techniques": [], "malware": [], "actors": []},
        "asset_match": {"matched": False, "assets": []},
        "tlp": None,
    }
    assert port.calls == [(Ioc(IocType.DOMAIN, "unknown.example"), frozenset({"TLP:CLEAR", "TLP:GREEN"}))]


def test_it_response_is_invariant_when_hidden_facts_change():
    hidden_related = RelatedFact(kind="malware", value="Hidden Family", tlp="TLP:AMBER")
    hidden_asset = AssetFact(name="hidden.internal", tlp="TLP:RED")
    base = _record(
        sources=(GREEN_SOURCE, AMBER_SOURCE),
        related=(hidden_related,),
        assets=(hidden_asset,),
    )
    mutated = replace(
        base,
        sources=(
            GREEN_SOURCE,
            replace(
                AMBER_SOURCE,
                reliability=0.01,
                name="Changed Hidden",
                first_seen=NOW - timedelta(days=1),
                last_seen=NOW - timedelta(days=1),
            ),
            replace(AMBER_SOURCE, source_id="second-hidden", name="Second Hidden"),
        ),
        related=(replace(hidden_related, value="Changed Family"),),
        assets=(replace(hidden_asset, name="changed.internal"),),
    )

    first = _service(FixtureLookupPort({EVIL_DOMAIN: base})).lookup("evil.example", frozenset({"it"}))
    second = _service(FixtureLookupPort({EVIL_DOMAIN: mutated})).lookup("evil.example", frozenset({"it"}))

    assert first == second
    assert first.model_dump(mode="json") == {
        "ioc": {"type": "domain", "value": "evil.example", "display": "evil[.]example"},
        "state": "found",
        "found": True,
        "allowlisted": False,
        "score": {
            "value": 40,
            "level": "medium",
            "reason": (
                "Nguồn tin cậy 0.80 × 1 nguồn xác nhận (0.50) × thấy lần cuối 0 ngày trước (1.00) = 40 điểm"
            ),
            "parts": {
                "reliability": 0.8,
                "confirmation": 0.5,
                "freshness": 1.0,
                "asset": 1.0,
            },
        },
        "sources": [
            {
                "name": "Synthetic Alpha",
                "first_seen": "2026-11-11T00:00:00Z",
                "last_seen": "2026-11-11T00:00:00Z",
                "tlp": "TLP:GREEN",
            }
        ],
        "related": {"techniques": [], "malware": [], "actors": []},
        "asset_match": {"matched": False, "assets": []},
        "tlp": "TLP:GREEN",
    }


def test_analyst_sees_all_authorized_facts_and_recomputed_score():
    port = FixtureLookupPort(
        {
            EVIL_DOMAIN: _record(
                sources=(GREEN_SOURCE, AMBER_SOURCE),
                related=(
                    RelatedFact(kind="technique", value="T1566.001", tlp="TLP:GREEN"),
                    RelatedFact(kind="actor", value="Synthetic Actor", tlp="TLP:AMBER"),
                ),
                assets=(AssetFact(name="mail.example", tlp="TLP:AMBER"),),
            )
        }
    )

    response = _service(port).lookup("evil.example", frozenset({"analyst"}))

    assert response.found is True
    assert response.score is not None
    assert response.score.value == 69
    assert response.score.parts is not None
    assert response.score.parts.reliability == 0.7
    assert len(response.sources) == 2
    assert response.related.techniques == ["T1566.001"]
    assert response.related.actors == ["Synthetic Actor"]
    assert response.asset_match.model_dump() == {"matched": True, "assets": ["mail.example"]}
    assert response.tlp == "TLP:AMBER"


def test_record_marking_outside_role_is_indistinguishable_from_absent():
    hidden = _record(record_tlp="TLP:AMBER", sources=(GREEN_SOURCE,))

    hidden_response = _service(FixtureLookupPort({EVIL_DOMAIN: hidden})).lookup(
        "evil.example", frozenset({"it"})
    )
    absent_response = _service(FixtureLookupPort()).lookup("evil.example", frozenset({"it"}))

    assert hidden_response == absent_response
    assert hidden_response.state == "not_found"


def test_hidden_record_does_not_expose_invalid_nested_fact_as_error():
    hidden = _record(
        record_tlp="TLP:AMBER",
        sources=(replace(GREEN_SOURCE, tlp="TLP:UNKNOWN"),),
    )

    hidden_response = _service(FixtureLookupPort({EVIL_DOMAIN: hidden})).lookup(
        "evil.example", frozenset({"it"})
    )
    absent_response = _service(FixtureLookupPort()).lookup("evil.example", frozenset({"it"}))

    assert hidden_response == absent_response


def test_identical_visible_source_ids_are_deduplicated():
    record = _record(sources=(GREEN_SOURCE, GREEN_SOURCE))

    response = _service(FixtureLookupPort({EVIL_DOMAIN: record})).lookup(
        "evil.example", frozenset({"analyst"})
    )

    assert len(response.sources) == 1
    assert response.score is not None
    assert response.score.parts is not None
    assert response.score.parts.confirmation == 0.5


def test_conflicting_visible_source_ids_fail_closed():
    conflict = replace(GREEN_SOURCE, reliability=0.2)
    record = _record(sources=(GREEN_SOURCE, conflict))

    with pytest.raises(LookupUnavailable):
        _service(FixtureLookupPort({EVIL_DOMAIN: record})).lookup("evil.example", frozenset({"analyst"}))


@pytest.mark.parametrize(
    "record",
    [
        _record(record_tlp="TLP:UNKNOWN"),
        _record(sources=(replace(GREEN_SOURCE, reliability=True),)),
        _record(sources=(replace(GREEN_SOURCE, first_seen=datetime(2026, 11, 11)),)),
        _record(sources=(replace(GREEN_SOURCE, first_seen=NOW.replace(day=12)),)),
        replace(_record(), ioc=Ioc(IocType.DOMAIN, "other.example")),
    ],
    ids=["unknown-tlp", "bool-reliability", "naive-time", "reversed-time", "wrong-ioc"],
)
def test_malformed_adapter_records_fail_closed(record: LookupRecord):
    with pytest.raises(LookupUnavailable):
        _service(FixtureLookupPort({EVIL_DOMAIN: record})).lookup("evil.example", frozenset({"analyst"}))


def test_response_schema_rejects_extra_fields_and_boolean_score():
    valid = _service(FixtureLookupPort({EVIL_DOMAIN: _record()})).lookup(
        "evil.example", frozenset({"analyst"})
    )
    payload = valid.model_dump(mode="json")
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        IocLookupResponse.model_validate(payload)

    payload.pop("unexpected")
    payload["score"]["value"] = True
    with pytest.raises(ValidationError):
        IocLookupResponse.model_validate(payload)


@pytest.mark.parametrize("state", ["allowlisted", "not_found"])
def test_response_schema_allows_local_asset_match_without_changing_lookup_state(state):
    response = (
        _service(FixtureLookupPort()).lookup("8.8.8.8", frozenset({"it"}))
        if state == "allowlisted"
        else _service(FixtureLookupPort()).lookup("unknown.example", frozenset({"it"}))
    )
    payload = response.model_dump(mode="json")
    payload["asset_match"] = {"matched": True, "assets": ["congty.vn"]}

    validated = IocLookupResponse.model_validate(payload)

    assert validated.state == state
    assert validated.asset_match.assets == ["congty.vn"]


@pytest.mark.parametrize(
    ("raw", "ioc_type"),
    [
        ("8.8.8.9", "ipv4"),
        ("2001:4860:4860::8844", "ipv6"),
        ("evil.example", "domain"),
        ("https://evil.example/path", "url"),
        ("attacker@evil.example", "email"),
        ("d41d8cd98f00b204e9800998ecf8427e", "md5"),
        ("da39a3ee5e6b4b0d3255bfef95601890afd80709", "sha1"),
        ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "sha256"),
    ],
)
def test_lookup_supports_all_contract_ioc_types(raw: str, ioc_type: str):
    ioc = normalize(raw)
    record = replace(_record(), ioc=ioc)

    response = _service(FixtureLookupPort({ioc: record})).lookup(raw, frozenset({"analyst"}))

    assert response.ioc.type == ioc_type


@pytest.mark.parametrize(
    "tlp",
    ["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"],
)
def test_analyst_output_supports_all_contract_tlp_markings(tlp: str):
    source = replace(GREEN_SOURCE, tlp=tlp)
    record = _record(record_tlp=tlp, sources=(source,))

    response = _service(FixtureLookupPort({EVIL_DOMAIN: record})).lookup(
        "evil.example", frozenset({"analyst"})
    )

    assert response.tlp == tlp


def test_http_it_get_returns_exact_found_fixture_and_security_headers(tmp_path, rsa_keys):
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        FixtureLookupPort(
            {
                EVIL_DOMAIN: _record(
                    sources=(GREEN_SOURCE, AMBER_SOURCE),
                    related=(RelatedFact("actor", "Hidden Actor", "TLP:AMBER"),),
                    assets=(AssetFact("hidden.internal", "TLP:RED"),),
                )
            }
        ),
    )

    response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key))

    assert response.status_code == 200
    assert response.json() == {
        "ioc": {"type": "domain", "value": "evil.example", "display": "evil[.]example"},
        "state": "found",
        "found": True,
        "allowlisted": False,
        "score": {
            "value": 40,
            "level": "medium",
            "reason": (
                "Nguồn tin cậy 0.80 × 1 nguồn xác nhận (0.50) × thấy lần cuối 0 ngày trước (1.00) = 40 điểm"
            ),
            "parts": {
                "reliability": 0.8,
                "confirmation": 0.5,
                "freshness": 1.0,
                "asset": 1.0,
            },
        },
        "sources": [
            {
                "name": "Synthetic Alpha",
                "first_seen": "2026-11-11T00:00:00Z",
                "last_seen": "2026-11-11T00:00:00Z",
                "tlp": "TLP:GREEN",
            }
        ],
        "related": {"techniques": [], "malware": [], "actors": []},
        "asset_match": {"matched": False, "assets": []},
        "tlp": "TLP:GREEN",
    }
    _assert_w02_headers(response)


@pytest.mark.parametrize(
    ("path", "headers", "subject", "status", "code", "message"),
    [
        (
            "/api/ioc?unexpected=x",
            {},
            None,
            401,
            "authentication_required",
            "Cần xác thực hợp lệ",
        ),
        (
            "/api/ioc?unexpected=x",
            {},
            "leader-sub",
            403,
            "forbidden",
            "Tài khoản chưa được cấp quyền tra cứu IOC",
        ),
    ],
)
def test_http_auth_and_role_run_before_query_validation(
    tmp_path, rsa_keys, path, headers, subject, status, code, message
):
    client, private_key = _client(tmp_path, rsa_keys, FixtureLookupPort())
    request_headers = headers if subject is None else _auth(private_key, subject)

    response = client.get(path, headers=request_headers)

    _assert_error(response, status, code, message)


def test_http_does_not_trust_client_role_claim_or_email_header(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, FixtureLookupPort())
    headers = _auth(private_key, "leader-sub", role="admin", email="admin@example.test")
    headers["Cf-Access-Authenticated-User-Email"] = "admin@example.test"
    headers["X-Role"] = "admin"

    response = client.get("/api/ioc?value=evil.example&role=admin", headers=headers)

    _assert_error(
        response,
        403,
        "forbidden",
        "Tài khoản chưa được cấp quyền tra cứu IOC",
    )


def test_http_expired_jwt_is_authentication_required(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, FixtureLookupPort())
    headers = _auth(private_key, "it-sub", exp=datetime.now(UTC) - timedelta(minutes=1))

    response = client.get("/api/ioc?value=evil.example", headers=headers)

    _assert_error(response, 401, "authentication_required", "Cần xác thực hợp lệ")


@pytest.mark.parametrize(
    "query",
    [
        "",
        "?value=",
        "?value=a&value=b",
        "?value=evil.example&extra=x",
        "?value=" + "a" * 4097,
        "?value=https%3A%2F%2Fevil.example%2F" + "a" * 2049,
    ],
    ids=["missing", "empty", "duplicate", "unknown-key", "raw-bound", "canonical-bound"],
)
def test_http_rejects_non_exact_or_out_of_bounds_query(tmp_path, rsa_keys, query):
    client, private_key = _client(tmp_path, rsa_keys, FixtureLookupPort())

    response = client.get(f"/api/ioc{query}", headers=_auth(private_key))

    _assert_error(response, 422, "invalid_ioc", "IOC không hợp lệ")


def test_http_private_ip_has_distinct_stable_error(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, FixtureLookupPort())

    response = client.get("/api/ioc?value=192.168.1.1", headers=_auth(private_key))

    _assert_error(response, 422, "private_ip", "IP nội bộ không thể tra cứu")


def test_http_missing_adapter_only_fails_after_allowlist(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, None)

    allowed = client.get("/api/ioc?value=8.8.8.8", headers=_auth(private_key))
    unavailable = client.get("/api/ioc?value=evil.example", headers=_auth(private_key))

    assert allowed.status_code == 200
    assert allowed.json()["state"] == "allowlisted"
    _assert_w02_headers(allowed)
    _assert_error(
        unavailable,
        503,
        "lookup_unavailable",
        "Dịch vụ tra cứu tạm thời không sẵn sàng",
    )


def test_http_adapter_exception_is_sanitized(tmp_path, rsa_keys):
    client, private_key = _client(tmp_path, rsa_keys, ExplodingLookupPort())

    response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key))

    _assert_error(
        response,
        503,
        "lookup_unavailable",
        "Dịch vụ tra cứu tạm thời không sẵn sàng",
    )
    assert "secret" not in response.text
    assert "timeout" not in response.text


def test_http_malformed_adapter_record_is_lookup_unavailable(tmp_path, rsa_keys):
    malformed = _record(sources=(replace(GREEN_SOURCE, tlp="TLP:UNKNOWN"),))
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        FixtureLookupPort({EVIL_DOMAIN: malformed}),
    )

    response = client.get(
        "/api/ioc?value=evil.example",
        headers=_auth(private_key, "analyst-sub"),
    )

    _assert_error(
        response,
        503,
        "lookup_unavailable",
        "Dịch vụ tra cứu tạm thời không sẵn sàng",
    )


def test_http_jwks_outage_maps_to_lookup_unavailable(tmp_path, rsa_keys):
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        FixtureLookupPort(),
        jwks_client=UnavailableJwksClient(),
    )

    response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key))

    _assert_error(
        response,
        503,
        "lookup_unavailable",
        "Dịch vụ tra cứu tạm thời không sẵn sàng",
    )


def test_http_multi_role_uses_highest_tlp_permission(tmp_path, rsa_keys):
    record = _record(record_tlp="TLP:AMBER", sources=(AMBER_SOURCE,))
    client, private_key = _client(
        tmp_path,
        rsa_keys,
        FixtureLookupPort({EVIL_DOMAIN: record}),
    )

    it_response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key, "it-sub"))
    multi_response = client.get("/api/ioc?value=evil.example", headers=_auth(private_key, "multi-sub"))

    assert it_response.status_code == 200
    assert it_response.json()["state"] == "not_found"
    assert multi_response.status_code == 200
    assert multi_response.json()["state"] == "found"
    assert multi_response.json()["tlp"] == "TLP:AMBER"
    _assert_w02_headers(it_response)
    _assert_w02_headers(multi_response)
