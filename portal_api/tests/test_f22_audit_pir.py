"""Test F22: nhật ký kiểm toán chuỗi băm, hồ sơ PIR và sắp xếp CVE theo PIR (offline)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from portal_api.app import create_app
from portal_api.audit_log import AuditLog, InvalidAuditEntry
from portal_api.auth import AccessJwtVerifier
from portal_api.pir import InvalidPirProfile, PirStore, score_cves, validate_profile
from portal_api.tests import test_w02_ioc_api as w02_test_api
from portal_api.tests.test_cves_api import StaticPort, _dataset
from portal_api.tests.test_cves_api import _store as _tech_store
from portal_api.tests.test_f21_reports import FakeSender, _candidates, _dstore, _post
from portal_api.tests.test_w02_ioc_api import PORTAL_ORIGIN, LocalJwksClient, _auth, _settings

NOW = datetime(2026, 11, 27, 8, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def rsa_keys():
    return w02_test_api.rsa_keys.__wrapped__()


def _log(tmp_path):
    log = AuditLog(tmp_path / "audit.sqlite", timeout=0.01, clock=lambda: NOW)
    log.initialize()
    return log


def _pir(tmp_path):
    store = PirStore(tmp_path / "pir.sqlite", timeout=0.01, clock=lambda: NOW)
    store.initialize()
    return store


# --- Nhật ký ------------------------------------------------------------------------------


def test_audit_record_uses_utc_and_chains_hashes(tmp_path):
    local = datetime(2026, 11, 27, 15, 0, tzinfo=timezone(timedelta(hours=7)))
    log = AuditLog(tmp_path / "audit.sqlite", clock=lambda: local)
    log.initialize()

    first = log.record("admin-sub", "pir.put", "pir:profile", "success", {"k": 1})
    second = log.record("admin-sub", "dissemination.send", "outbox:1", "failure")

    assert first["at"] == "2026-11-27T08:00:00Z"
    assert first["prev_hash"] == "0" * 64
    assert second["prev_hash"] == first["row_hash"]
    assert log.verify_chain().ok is True
    assert log.verify_chain().checked == 2


def test_audit_is_append_only_via_sql(tmp_path):
    log = _log(tmp_path)
    log.record("a", "x", "t", "success")
    with sqlite3.connect(log.path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE audit_log SET actor='evil'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM audit_log")


def test_audit_verify_detects_tampering(tmp_path):
    log = _log(tmp_path)
    for index in range(3):
        log.record("a", "x", f"t{index}", "success")
    with sqlite3.connect(log.path) as connection:
        connection.execute("DROP TRIGGER audit_log_no_update")
        connection.execute("UPDATE audit_log SET actor='evil' WHERE id=2")

    report = log.verify_chain()

    assert report.ok is False
    assert report.broken_at == 2
    assert report.checked == 1


def test_audit_rejects_bad_input(tmp_path):
    log = _log(tmp_path)
    with pytest.raises(InvalidAuditEntry):
        log.record("a\nb", "x", "t", "success")
    with pytest.raises(InvalidAuditEntry):
        log.record("a", "x", "t", "maybe")
    with pytest.raises(InvalidAuditEntry):
        log.record("a", "x", "t", "success", {"big": "x" * 5000})


def test_audit_list_filters_newest_first(tmp_path):
    log = _log(tmp_path)
    log.record("a", "x", "t1", "success")
    log.record("b", "y", "t2", "success")
    log.record("a", "y", "t3", "failure")

    assert [e["target"] for e in log.list_entries(actor="a")] == ["t3", "t1"]
    assert [e["target"] for e in log.list_entries(action="y", limit=1)] == ["t3"]
    assert log.list_entries(since="2027-01-01T00:00:00Z") == []


# --- PIR ----------------------------------------------------------------------------------

PROFILE = {
    "vendors": ["fortinet"],
    "products": [],
    "sectors": ["tài chính"],
    "keywords": ["exchange"],
    "min_cvss": 9.0,
}


def _item(cve_id, vendor, product, title="", cvss=None):
    return {
        "cve_id": cve_id,
        "title": title,
        "cvss_base_score": cvss,
        "matches": [{"vendor": vendor, "product": product}],
    }


def test_validate_profile_rejects_unknown_and_bad_values():
    assert validate_profile({})["min_cvss"] is None
    assert validate_profile({"vendors": ["A", "a", " A "]})["vendors"] == ["A"]
    for bad in ({"tenant": "x"}, {"vendors": "x"}, {"min_cvss": 11}, {"min_cvss": True}, {"keywords": [""]}):
        with pytest.raises(InvalidPirProfile):
            validate_profile(bad)


def test_score_cves_orders_by_pir_and_is_stable():
    profile = validate_profile(PROFILE)
    items = [
        _item("CVE-1", "Nobody", "Nothing"),
        _item("CVE-2", "Microsoft", "Exchange", title="Exchange RCE", cvss=7.5),
        _item("CVE-3", "Fortinet", "FortiOS", cvss=9.8),
        _item("CVE-4", "Nobody", "Other"),
    ]

    ranked = score_cves(items, profile)

    assert [item["cve_id"] for item in ranked] == ["CVE-3", "CVE-2", "CVE-1", "CVE-4"]
    assert ranked[0]["pir_score"] == 60
    assert ranked[0]["pir_reasons"] == ["vendor:fortinet", "cvss>=9"]
    assert "pir_score" not in items[0]


def test_pir_store_crud(tmp_path):
    store = _pir(tmp_path)
    assert store.get() is None
    saved = store.put(PROFILE, "admin-sub")
    assert saved["updated_at"] == "2026-11-27T08:00:00Z"
    assert store.get()["vendors"] == ["fortinet"]
    store.put({"keywords": ["vpn"]}, "admin-sub")
    assert store.get()["vendors"] == []
    assert store.delete() is True
    assert store.delete() is False


# --- API ----------------------------------------------------------------------------------


def _client(tmp_path, rsa_keys, *, with_stores=True):
    _, jwk = rsa_keys
    settings = _settings(tmp_path)
    app = create_app(
        settings,
        object(),
        verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk)),
        technology_store=_tech_store(
            tmp_path, ("Fortinet", "FortiOS", "7.2"), ("Microsoft", "Exchange", "2019")
        ),
        cve_port=StaticPort(_dataset(_candidates())),
        dissemination_store=_dstore(tmp_path),
        message_senders={"email": FakeSender()},
        report_clock=lambda: NOW,
        audit_log=_log(tmp_path) if with_stores else None,
        pir_store=_pir(tmp_path) if with_stores else None,
    )
    return TestClient(app, raise_server_exceptions=False)


def _put(client, private_key, body, subject="admin-sub"):
    headers = {**_auth(private_key, subject), "Origin": PORTAL_ORIGIN, "Content-Type": "application/json"}
    return client.put("/api/pir", json=body, headers=headers)


def test_api_dissemination_decide_and_send_are_audited(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys)
    recipient = {"display_name": "IT Lead", "channel": "email", "address": "it@abc.example"}
    _post(client, private_key, "/api/dissemination/recipients", recipient)
    batch = _post(client, private_key, "/api/dissemination/outbox", {}, "analyst-sub").json()
    base = f"/api/dissemination/outbox/{batch['id']}"

    assert _post(client, private_key, f"{base}/send", {"confirm": True}).status_code == 409
    approve = {"decision": "approve", "content_hash": batch["content_hash"]}
    assert _post(client, private_key, f"{base}/decision", approve).status_code == 200
    assert _post(client, private_key, f"{base}/send", {"confirm": True}).status_code == 200

    listing = client.get("/api/audit", headers=_auth(private_key, "admin-sub"))
    assert listing.status_code == 200
    assert listing.headers["cache-control"] == "no-store"
    rows = [(e["action"], e["result"]) for e in listing.json()["items"]]
    assert rows == [
        ("dissemination.send", "success"),
        ("dissemination.decide", "success"),
        ("dissemination.send", "failure"),
    ]
    verify = client.get("/api/audit/verify", headers=_auth(private_key, "admin-sub")).json()
    assert verify == {"ok": True, "checked": 3, "broken_at": None}


def test_api_audit_is_admin_only_and_read_only(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys)

    assert client.get("/api/audit").status_code == 401
    assert client.get("/api/audit", headers=_auth(private_key, "analyst-sub")).status_code == 403
    assert client.get("/api/audit?bogus=1", headers=_auth(private_key, "admin-sub")).status_code == 422
    assert (
        client.get("/api/audit?since=yesterday", headers=_auth(private_key, "admin-sub")).status_code == 422
    )
    assert client.delete("/api/audit", headers=_auth(private_key, "admin-sub")).status_code == 405


def test_api_governance_fails_closed_without_stores(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys, with_stores=False)

    assert client.get("/api/audit", headers=_auth(private_key, "admin-sub")).status_code == 503
    assert client.get("/api/pir", headers=_auth(private_key, "admin-sub")).status_code == 503


def test_api_pir_crud_roles_and_audit(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys)

    assert client.get("/api/pir", headers=_auth(private_key, "analyst-sub")).status_code == 404
    assert _put(client, private_key, PROFILE, "analyst-sub").status_code == 403
    assert _put(client, private_key, {"tenant": "x"}).status_code == 422
    assert _put(client, private_key, PROFILE).status_code == 200
    assert client.get("/api/pir", headers=_auth(private_key, "analyst-sub")).json()["vendors"] == ["fortinet"]
    no_origin = client.delete("/api/pir", headers=_auth(private_key, "admin-sub"))
    assert no_origin.status_code == 403
    deleted = client.delete("/api/pir", headers={**_auth(private_key, "admin-sub"), "Origin": PORTAL_ORIGIN})
    assert deleted.status_code == 204

    actions = [
        e["action"] for e in client.get("/api/audit", headers=_auth(private_key, "admin-sub")).json()["items"]
    ]
    assert actions == ["pir.delete", "pir.put"]


def test_api_cves_pir_flag_is_opt_in(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys)
    headers = _auth(private_key, "analyst-sub")
    default = client.get("/api/cves", headers=headers).json()
    _put(client, private_key, {"vendors": ["Microsoft"]})

    unchanged = client.get("/api/cves", headers=headers).json()
    ranked = client.get("/api/cves?pir=true", headers=headers).json()

    assert unchanged == default
    assert "pir_applied" not in unchanged
    assert ranked["pir_applied"] is True
    assert ranked["items"][0]["cve_id"] == "CVE-2026-1001"
    assert ranked["items"][0]["pir_reasons"] == ["vendor:Microsoft"]
    assert client.get("/api/cves?pir=yes", headers=headers).status_code == 422
