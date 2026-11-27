"""Route F21: xem báo cáo, quản lý danh sách nhận, outbox duyệt rồi mới gửi."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse

from portal_api.auth import AccessJwtVerifier, AuthenticationError, AuthenticationUnavailable, Principal
from portal_api.cves import CveReadService, CvesUnavailable
from portal_api.dissemination import (
    DisseminationStore,
    InvalidRecipient,
    OutboxEmpty,
    OutboxNotFound,
    OutboxPolicyError,
    OutboxStateError,
    RecipientExists,
    RecipientNotFound,
)
from portal_api.reports import InvalidReportRequest, build_weekly_vulnerability_report, render_report_html
from portal_api.senders import MessageSender
from portal_api.service import ApiFailure
from portal_api.settings import Settings

JWT_HEADER = "Cf-Access-Jwt-Assertion"
VIEW_ROLES = frozenset({"it", "analyst", "admin"})
PREPARE_ROLES = frozenset({"analyst", "admin"})
ADMIN_ROLES = frozenset({"admin"})
BODY_LIMIT = 4_096
REPORT_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'"
)
UNAVAILABLE = ("reports_unavailable", "Dịch vụ báo cáo tạm thời không sẵn sàng")


def is_reports_path(path: str) -> bool:
    return any(
        path == prefix or path.startswith(prefix + "/") for prefix in ("/api/reports", "/api/dissemination")
    )


def _parse_id(value: str) -> int:
    if not value.isascii() or not value.isdigit() or value.startswith("0") or len(value) > 15:
        raise ApiFailure(404, "not_found", "Không tìm thấy")
    return int(value)


async def _json_body(request: Request, settings: Settings) -> dict[str, Any]:
    if request.headers.get("origin") != settings.portal_origin:
        raise ApiFailure(403, "forbidden", "Origin không được phép")
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type != "application/json":
        raise ApiFailure(415, "unsupported_media_type", "Chỉ nhận application/json")
    raw = b""
    async for chunk in request.stream():
        raw += chunk
        if len(raw) > BODY_LIMIT:
            raise ApiFailure(413, "request_too_large", "Nội dung yêu cầu quá lớn")
    try:
        body = json.loads(raw or b"{}")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ") from exc
    if not isinstance(body, dict):
        raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ")
    return body


def _outbox_failure(exc: Exception) -> ApiFailure:
    if isinstance(exc, OutboxNotFound):
        return ApiFailure(404, "outbox_not_found", "Không tìm thấy lô gửi")
    if isinstance(exc, OutboxPolicyError):
        return ApiFailure(403, "forbidden", "Người tạo lô không được tự duyệt")
    if isinstance(exc, OutboxEmpty):
        return ApiFailure(409, "no_recipients", "Chưa có người nhận đang hoạt động")
    if isinstance(exc, OutboxStateError):
        return ApiFailure(409, "outbox_state_conflict", "Trạng thái hoặc nội dung lô đã thay đổi")
    raise exc


def register_report_routes(
    app: FastAPI,
    *,
    settings: Settings,
    verifier: AccessJwtVerifier,
    cve_service: CveReadService | None,
    store: DisseminationStore | None,
    senders: Mapping[str, MessageSender],
    tenant_name: str,
    clock: Callable[[], datetime] | None = None,
) -> None:
    """Gắn route F21 vào app hiện có; thiếu phụ thuộc thì trả 503 (fail-closed)."""

    def role_dependency(roles: frozenset[str]) -> Callable[[Request], Principal]:
        def require(request: Request) -> Principal:
            try:
                principal = verifier.verify(request.headers.get(JWT_HEADER))
            except AuthenticationUnavailable as exc:
                raise ApiFailure(503, *UNAVAILABLE) from exc
            except AuthenticationError as exc:
                raise ApiFailure(401, "authentication_required", "Cần xác thực hợp lệ") from exc
            if not principal.roles.intersection(roles):
                raise ApiFailure(403, "forbidden", "Tài khoản chưa được cấp quyền")
            return principal

        return require

    def configured_store() -> DisseminationStore:
        if store is None:
            raise ApiFailure(503, *UNAVAILABLE)
        return store

    def build_report(tlp: str | None = None) -> dict[str, Any]:
        if cve_service is None:
            raise ApiFailure(503, *UNAVAILABLE)
        kwargs: dict[str, Any] = {"tenant_name": tenant_name}
        if tlp is not None:
            kwargs["tlp"] = tlp
        if clock is not None:
            kwargs["clock"] = clock
        try:
            return build_weekly_vulnerability_report(cve_service, **kwargs)
        except InvalidReportRequest as exc:
            raise ApiFailure(422, "invalid_report_request", "Tham số báo cáo không hợp lệ") from exc
        except CvesUnavailable as exc:
            raise ApiFailure(503, *UNAVAILABLE) from exc

    view_role = Depends(role_dependency(VIEW_ROLES))
    prepare_role = Depends(role_dependency(PREPARE_ROLES))
    admin_role = Depends(role_dependency(ADMIN_ROLES))

    @app.get("/api/reports/weekly-vulnerability", response_class=HTMLResponse)
    def weekly_report_html(request: Request, principal: Principal = view_role):
        if set(request.query_params) - {"tlp"}:
            raise ApiFailure(422, "invalid_report_request", "Tham số báo cáo không hợp lệ")
        report = build_report(request.query_params.get("tlp"))
        response = HTMLResponse(render_report_html(report))
        response.headers["Content-Security-Policy"] = REPORT_CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/api/dissemination/recipients")
    def list_recipients(principal: Principal = prepare_role):
        return {"items": configured_store().list_recipients()}

    @app.post("/api/dissemination/recipients", status_code=201)
    async def add_recipient(request: Request, principal: Principal = admin_role):
        body = await _json_body(request, settings)
        if set(body) != {"display_name", "channel", "address"}:
            raise ApiFailure(422, "invalid_recipient", "Người nhận không hợp lệ")
        try:
            return configured_store().add_recipient(
                body["display_name"], body["channel"], body["address"], principal.subject
            )
        except InvalidRecipient as exc:
            raise ApiFailure(422, "invalid_recipient", "Người nhận không hợp lệ") from exc
        except RecipientExists as exc:
            raise ApiFailure(409, "recipient_exists", "Người nhận đã tồn tại") from exc

    @app.delete("/api/dissemination/recipients/{recipient_id}", status_code=204)
    def remove_recipient(recipient_id: str, request: Request, principal: Principal = admin_role):
        if request.headers.get("origin") != settings.portal_origin:
            raise ApiFailure(403, "forbidden", "Origin không được phép")
        try:
            configured_store().deactivate_recipient(_parse_id(recipient_id), principal.subject)
        except RecipientNotFound as exc:
            raise ApiFailure(404, "recipient_not_found", "Không tìm thấy người nhận") from exc

    @app.post("/api/dissemination/outbox", status_code=201)
    async def create_outbox(request: Request, principal: Principal = prepare_role):
        body = await _json_body(request, settings)
        if set(body) - {"tlp"} or not isinstance(body.get("tlp", ""), str):
            raise ApiFailure(422, "invalid_report_request", "Tham số báo cáo không hợp lệ")
        report = build_report(body.get("tlp"))
        try:
            return configured_store().create_batch(report, principal.subject)
        except (OutboxEmpty, OutboxStateError) as exc:
            raise _outbox_failure(exc) from exc

    @app.get("/api/dissemination/outbox/{batch_id}")
    def preview_outbox(batch_id: str, principal: Principal = prepare_role):
        try:
            return configured_store().get_batch(_parse_id(batch_id))
        except OutboxNotFound as exc:
            raise _outbox_failure(exc) from exc

    @app.post("/api/dissemination/outbox/{batch_id}/decision")
    async def decide_outbox(batch_id: str, request: Request, principal: Principal = admin_role):
        body = await _json_body(request, settings)
        if set(body) != {"decision", "content_hash"} or not all(isinstance(v, str) for v in body.values()):
            raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ")
        try:
            return configured_store().decide(
                _parse_id(batch_id), principal.subject, body["decision"], body["content_hash"]
            )
        except (OutboxNotFound, OutboxPolicyError, OutboxStateError) as exc:
            raise _outbox_failure(exc) from exc

    @app.post("/api/dissemination/outbox/{batch_id}/send")
    async def send_outbox(batch_id: str, request: Request, principal: Principal = admin_role):
        body = await _json_body(request, settings)
        if body != {"confirm": True}:
            raise ApiFailure(422, "confirmation_required", "Cần xác nhận gửi")
        try:
            return configured_store().send_batch(_parse_id(batch_id), principal.subject, senders)
        except (OutboxNotFound, OutboxStateError) as exc:
            raise _outbox_failure(exc) from exc
