"""Route F22: đọc nhật ký kiểm toán (chỉ admin) và CRUD hồ sơ PIR."""

from __future__ import annotations

import re
from collections.abc import Callable

from fastapi import Depends, FastAPI, Request

from portal_api.audit_log import AuditLog, InvalidAuditEntry
from portal_api.auth import AccessJwtVerifier, AuthenticationError, AuthenticationUnavailable, Principal
from portal_api.pir import InvalidPirProfile, PirStore
from portal_api.reports_api import _json_body
from portal_api.service import ApiFailure
from portal_api.settings import Settings

JWT_HEADER = "Cf-Access-Jwt-Assertion"
ADMIN_ROLES = frozenset({"admin"})
PIR_VIEW_ROLES = frozenset({"analyst", "admin"})
UNAVAILABLE = ("governance_unavailable", "Dịch vụ nhật ký/PIR tạm thời không sẵn sàng")
AUDIT_FILTERS = {"actor", "action", "target", "since", "until", "limit"}
UTC_STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def is_governance_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in ("/api/audit", "/api/pir"))


def _audit_query(request: Request) -> dict[str, object]:
    params = request.query_params
    if set(params) - AUDIT_FILTERS or any(len(params.getlist(key)) != 1 for key in params):
        raise ApiFailure(422, "invalid_audit_query", "Query nhật ký không hợp lệ")
    query: dict[str, object] = {}
    for key in ("actor", "action", "target"):
        value = params.get(key)
        if value is not None:
            if not 1 <= len(value) <= 256:
                raise ApiFailure(422, "invalid_audit_query", "Query nhật ký không hợp lệ")
            query[key] = value
    for key in ("since", "until"):
        value = params.get(key)
        if value is not None:
            if not UTC_STAMP.match(value):
                raise ApiFailure(422, "invalid_audit_query", "Query nhật ký không hợp lệ")
            query[key] = value
    raw_limit = params.get("limit", "50")
    if not raw_limit.isascii() or not raw_limit.isdigit() or not 1 <= int(raw_limit) <= 200:
        raise ApiFailure(422, "invalid_audit_query", "Query nhật ký không hợp lệ")
    query["limit"] = int(raw_limit)
    return query


def register_governance_routes(
    app: FastAPI,
    *,
    settings: Settings,
    verifier: AccessJwtVerifier,
    audit_log: AuditLog | None,
    pir_store: PirStore | None,
) -> None:
    """Gắn route F22; thiếu kho thì trả 503 (fail-closed). Nhật ký không có route ghi/xóa."""

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

    def configured_audit() -> AuditLog:
        if audit_log is None:
            raise ApiFailure(503, *UNAVAILABLE)
        return audit_log

    def configured_pir() -> PirStore:
        if pir_store is None:
            raise ApiFailure(503, *UNAVAILABLE)
        return pir_store

    def audit_pir(principal: Principal, action: str) -> None:
        if audit_log is not None:
            try:
                audit_log.record(principal.subject, action, "pir:profile", "success")
            except InvalidAuditEntry:
                pass

    admin_role = Depends(role_dependency(ADMIN_ROLES))
    pir_view_role = Depends(role_dependency(PIR_VIEW_ROLES))

    @app.get("/api/audit")
    def list_audit(request: Request, principal: Principal = admin_role):
        return {"items": configured_audit().list_entries(**_audit_query(request))}

    @app.get("/api/audit/verify")
    def verify_audit(principal: Principal = admin_role):
        report = configured_audit().verify_chain()
        return {"ok": report.ok, "checked": report.checked, "broken_at": report.broken_at}

    @app.get("/api/pir")
    def get_pir(principal: Principal = pir_view_role):
        profile = configured_pir().get()
        if profile is None:
            raise ApiFailure(404, "pir_not_found", "Chưa có hồ sơ PIR")
        return profile

    @app.put("/api/pir")
    async def put_pir(request: Request, principal: Principal = admin_role):
        body = await _json_body(request, settings)
        try:
            profile = configured_pir().put(body, principal.subject)
        except InvalidPirProfile as exc:
            raise ApiFailure(422, "invalid_pir_profile", "Hồ sơ PIR không hợp lệ") from exc
        audit_pir(principal, "pir.put")
        return profile

    @app.delete("/api/pir", status_code=204)
    def delete_pir(request: Request, principal: Principal = admin_role):
        if request.headers.get("origin") != settings.portal_origin:
            raise ApiFailure(403, "forbidden", "Origin không được phép")
        if not configured_pir().delete():
            raise ApiFailure(404, "pir_not_found", "Chưa có hồ sơ PIR")
        audit_pir(principal, "pir.delete")
