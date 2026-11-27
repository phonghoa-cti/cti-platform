"""Test F21: báo cáo lỗ hổng tuần, mẫu thư, danh sách nhận và outbox duyệt rồi gửi (offline)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from portal_api.cves import CveReadService
from portal_api.dissemination import (
    DisseminationStore,
    InvalidRecipient,
    OutboxPolicyError,
    OutboxStateError,
)
from portal_api.email_templates import TemplateError, clean_text, render_message
from portal_api.reports import build_weekly_vulnerability_report, render_report_html
from portal_api.senders import SenderError, SenderSettingsError, SmtpSettings
from portal_api.tests import test_w02_ioc_api as w02_test_api
from portal_api.tests.test_cves_api import StaticPort, _candidate, _dataset, _store
from portal_api.tests.test_w02_ioc_api import PORTAL_ORIGIN, LocalJwksClient, _auth, _settings

XSS = "<script>alert(1)</script>"
NOW = datetime(2026, 11, 27, 8, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def rsa_keys():
    return w02_test_api.rsa_keys.__wrapped__()


class FakeSender:
    def __init__(self, fail: bool = False):
        self.sent = []
        self.fail = fail

    def send(self, message):
        if self.fail:
            raise SenderError("boom")
        self.sent.append(message)


def _service(tmp_path, candidates=None):
    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"), ("Microsoft", "Exchange", "2019"))
    return CveReadService(StaticPort(_dataset(candidates)), store)


def _candidates():
    return [
        _candidate("CVE-2026-1000", kev=True, cvss=9.8),
        _candidate("CVE-2026-1001", vendor="Microsoft", product="Exchange", kev=False, cvss=7.5, epss=0.1),
        _candidate("CVE-2026-1002", vendor="Nobody", product="Nothing", kev=True),
    ]


def _report(tmp_path, **kwargs):
    return build_weekly_vulnerability_report(
        _service(tmp_path, _candidates()), tenant_name="Công ty ABC", clock=lambda: NOW, **kwargs
    )


def _dstore(tmp_path):
    store = DisseminationStore(tmp_path / "dissemination.sqlite", timeout=0.01, clock=lambda: NOW)
    store.initialize()
    return store


# --- Báo cáo ------------------------------------------------------------------------------


def test_report_counts_only_cves_matching_assets(tmp_path):
    report = _report(tmp_path)

    assert report["matched_cves"] == 2
    assert report["kev_cves"] == 1
    assert [item["cve_id"] for item in report["items"]] == ["CVE-2026-1000", "CVE-2026-1001"]
    assert report["severity"] == {"critical": 1, "high": 1, "medium": 0, "low": 0, "unknown": 0}
    assert report["affected_technologies"] == 2
    assert report["tlp"] == "TLP:AMBER"
    assert report["period_label"] == "2026-11-20 → 2026-11-27"
    assert report["content_hash"].startswith("sha256:")


def test_report_rejects_unknown_tlp(tmp_path):
    from portal_api.reports import InvalidReportRequest

    with pytest.raises(InvalidReportRequest):
        _report(tmp_path, tlp="TLP:RED")


def test_report_html_escapes_untrusted_feed_text(tmp_path):
    candidate = _candidate("CVE-2026-2000")
    candidate["title"] = XSS
    report = build_weekly_vulnerability_report(
        _service(tmp_path, [candidate]), tenant_name='ABC "><img src=x>', clock=lambda: NOW
    )

    page = render_report_html(report)

    assert "<script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "<img" not in page
    assert "@media print" in page
    assert "Báo cáo lỗ hổng tuần" in page


def test_report_html_handles_empty_match(tmp_path):
    report = build_weekly_vulnerability_report(
        _service(tmp_path, [_candidate(vendor="X", product="Y")]), tenant_name="ABC", clock=lambda: NOW
    )

    assert report["matched_cves"] == 0
    assert "Không có CVE nào khớp" in render_report_html(report)


# --- Mẫu thư ------------------------------------------------------------------------------


def _email_vars(**overrides):
    values = {
        "tenant_name": "ABC",
        "period_label": "2026-11-20 → 2026-11-27",
        "matched_cves": 2,
        "kev_cves": 1,
        "tlp": "TLP:AMBER",
    }
    values.update(overrides)
    return values


def test_email_template_escapes_html_and_strips_header_injection():
    rows = [{"cve_id": "CVE-2026-1", "title": XSS, "kev_label": "KEV", "cvss": 9.8}]

    message = render_message("weekly_vulnerability_email", _email_vars(tenant_name="A\r\nBcc: x@y.z"), rows)

    assert "\n" not in message.subject and "\r" not in message.subject
    assert "<script>" not in message.html
    assert "&lt;script&gt;" in message.html
    assert XSS in message.text  # text/plain không diễn giải HTML
    assert "A Bcc: x@y.z" in message.subject  # gộp thành một dòng, không tạo header mới


def test_email_template_rejects_unknown_variables_and_templates():
    with pytest.raises(TemplateError):
        render_message("weekly_vulnerability_email", {**_email_vars(), "extra": "x"})
    with pytest.raises(TemplateError):
        render_message("user_supplied", {})


def test_dollar_sign_in_value_is_not_reinterpreted():
    message = render_message("weekly_vulnerability_email", _email_vars(tenant_name="$tlp ${kev_cves}"))
    assert "$tlp ${kev_cves}" in message.text


def test_clean_text_removes_control_characters():
    assert clean_text("a‮b\x00c\n d") == "a b c d"


# --- SMTP ---------------------------------------------------------------------------------


def test_smtp_settings_from_env_only_and_repr_hides_password():
    env = {
        "F21_SMTP_HOST": "smtp.example.invalid",
        "F21_SMTP_USERNAME": "user",
        "F21_SMTP_PASSWORD": "super-secret",
        "F21_SMTP_FROM": "noreply@example.invalid",
    }
    settings = SmtpSettings.from_env(env)
    assert settings.port == 587
    assert "super-secret" not in repr(settings)
    with pytest.raises(SenderSettingsError):
        SmtpSettings.from_env({})


# --- Danh sách nhận và outbox ---------------------------------------------------------------


def test_recipient_validation(tmp_path):
    store = _dstore(tmp_path)
    store.add_recipient("IT Lead", "email", "it@abc.example", "admin-sub")
    store.add_recipient("Nhóm Telegram", "telegram", "-100123", "admin-sub")
    for args in (
        ("X", "sms", "1"),
        ("X", "email", "a@b.c\r\nBcc: z@z.zz"),
        ("X", "telegram", "@name"),
        ("", "email", "a@b.cd"),
    ):
        with pytest.raises(InvalidRecipient):
            store.add_recipient(*args, "admin-sub")
    assert [item["channel"] for item in store.list_recipients()] == ["email", "telegram"]


def test_outbox_requires_approval_by_other_person_before_send(tmp_path):
    store = _dstore(tmp_path)
    store.add_recipient("IT Lead", "email", "it@abc.example", "admin-sub")
    store.add_recipient("Nhóm Telegram", "telegram", "-100123", "admin-sub")
    batch = store.create_batch(_report(tmp_path), "analyst-sub")
    sender = FakeSender()

    assert batch["status"] == "pending_approval"
    with pytest.raises(OutboxStateError):
        store.send_batch(batch["id"], "admin-sub", {"email": sender})
    with pytest.raises(OutboxPolicyError):
        store.decide(batch["id"], "analyst-sub", "approve", batch["content_hash"])
    with pytest.raises(OutboxStateError):
        store.decide(batch["id"], "admin-sub", "approve", "sha256:" + "0" * 64)
    assert sender.sent == []

    store.decide(batch["id"], "admin-sub", "approve", batch["content_hash"])
    result = store.send_batch(batch["id"], "admin-sub", {"email": sender})

    assert [m.address for m in sender.sent] == ["it@abc.example"]
    assert [m["status"] for m in result["messages"]] == ["sent", "skipped"]
    assert result["status"] == "partially_failed"
    telegram = result["messages"][1]["text_body"]
    assert "CVE-2026" not in telegram  # Telegram chỉ thông báo tối thiểu
    with pytest.raises(OutboxStateError):
        store.send_batch(batch["id"], "admin-sub", {"email": sender})
    actions = [entry["action"] for entry in store.audit_entries(batch["id"])]
    assert actions == ["outbox_created", "outbox_approved", "outbox_send_started", "outbox_send_finished"]


def test_failed_send_is_recorded(tmp_path):
    store = _dstore(tmp_path)
    store.add_recipient("IT Lead", "email", "it@abc.example", "admin-sub")
    batch = store.create_batch(_report(tmp_path), "analyst-sub")
    store.decide(batch["id"], "admin-sub", "approve", batch["content_hash"])

    result = store.send_batch(batch["id"], "admin-sub", {"email": FakeSender(fail=True)})

    assert result["messages"][0]["status"] == "failed"
    assert result["messages"][0]["error_code"] == "send_failed"


def test_rejected_batch_cannot_be_sent(tmp_path):
    store = _dstore(tmp_path)
    store.add_recipient("IT Lead", "email", "it@abc.example", "admin-sub")
    batch = store.create_batch(_report(tmp_path), "analyst-sub")
    store.decide(batch["id"], "admin-sub", "reject", batch["content_hash"])
    with pytest.raises(OutboxStateError):
        store.send_batch(batch["id"], "admin-sub", {"email": FakeSender()})


# --- API ----------------------------------------------------------------------------------


def _client(tmp_path, rsa_keys, sender):
    _, jwk = rsa_keys
    settings = _settings(tmp_path)
    store = _store(tmp_path, ("Fortinet", "FortiOS", "7.2"), ("Microsoft", "Exchange", "2019"))
    dstore = _dstore(tmp_path)
    app = create_app(
        settings,
        object(),
        verifier=AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk)),
        technology_store=store,
        cve_port=StaticPort(_dataset(_candidates())),
        dissemination_store=dstore,
        message_senders={"email": sender},
        report_tenant_name="Công ty ABC",
        report_clock=lambda: NOW,
    )
    return TestClient(app, raise_server_exceptions=False)


def _post(client, private_key, path, body, subject="admin-sub"):
    headers = {**_auth(private_key, subject), "Origin": PORTAL_ORIGIN, "Content-Type": "application/json"}
    return client.post(path, json=body, headers=headers)


def test_api_report_html_has_csp_and_requires_role(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys, FakeSender())

    response = client.get("/api/reports/weekly-vulnerability", headers=_auth(private_key, "it-sub"))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert "CVE-2026-1000" in response.text
    assert client.get("/api/reports/weekly-vulnerability").status_code == 401
    denied = client.get("/api/reports/weekly-vulnerability", headers=_auth(private_key, "leader-sub"))
    assert denied.status_code == 403


def test_api_full_flow_preview_approve_send(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    sender = FakeSender()
    client = _client(tmp_path, rsa_keys, sender)
    recipient = {"display_name": "IT Lead", "channel": "email", "address": "it@abc.example"}

    assert (
        _post(client, private_key, "/api/dissemination/recipients", recipient, "analyst-sub").status_code
        == 403
    )
    assert _post(client, private_key, "/api/dissemination/recipients", recipient).status_code == 201
    created = _post(client, private_key, "/api/dissemination/outbox", {}, "analyst-sub")
    assert created.status_code == 201
    batch = created.json()
    preview = client.get(
        f"/api/dissemination/outbox/{batch['id']}", headers=_auth(private_key, "analyst-sub")
    )
    assert preview.json()["messages"][0]["subject"].startswith("[Phong Hỏa][TLP:AMBER]")

    send_path = f"/api/dissemination/outbox/{batch['id']}/send"
    assert _post(client, private_key, send_path, {"confirm": True}).status_code == 409
    decision_path = f"/api/dissemination/outbox/{batch['id']}/decision"
    approve = {"decision": "approve", "content_hash": batch["content_hash"]}
    assert _post(client, private_key, decision_path, approve).status_code == 200
    assert sender.sent == []
    assert _post(client, private_key, send_path, {}).status_code == 422
    sent = _post(client, private_key, send_path, {"confirm": True})

    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"
    assert len(sender.sent) == 1


def test_api_rejects_cross_origin_writes(tmp_path, rsa_keys):
    private_key, _ = rsa_keys
    client = _client(tmp_path, rsa_keys, FakeSender())
    headers = {**_auth(private_key, "admin-sub"), "Origin": "https://evil.example"}
    body = {"display_name": "X", "channel": "email", "address": "x@abc.example"}

    response = client.post("/api/dissemination/recipients", json=body, headers=headers)

    assert response.status_code == 403
