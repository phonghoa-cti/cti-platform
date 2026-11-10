"""FastAPI factory cho đúng ba route W05."""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from portal_api.auth import (
    AccessJwtVerifier,
    AuthenticationError,
    AuthenticationUnavailable,
    Principal,
)
from portal_api.schemas import SQLITE_MAX_INTEGER, DecisionRequest, DecisionResponse, DraftDetail, DraftPage
from portal_api.service import ApiFailure, ReviewService
from portal_api.settings import Settings

JWT_HEADER = "Cf-Access-Jwt-Assertion"
ALLOWED_ROLES = {"analyst", "admin"}
POSITIVE_INTEGER = re.compile(r"[1-9][0-9]*\Z")


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _parse_positive_integer(value: str, label: str) -> int:
    if not isinstance(value, str) or not POSITIVE_INTEGER.fullmatch(value):
        raise ApiFailure(422, "invalid_request", f"{label} không hợp lệ")
    parsed = int(value)
    if parsed > SQLITE_MAX_INTEGER:
        raise ApiFailure(422, "invalid_request", f"{label} không hợp lệ")
    return parsed


def _parse_list_query(request: Request) -> tuple[int, int | None]:
    allowed = {"limit", "before_id"}
    if set(request.query_params) - allowed:
        raise ApiFailure(422, "invalid_request", "Query không hợp lệ")
    for key in allowed:
        if len(request.query_params.getlist(key)) > 1:
            raise ApiFailure(422, "invalid_request", "Query không hợp lệ")
    raw_limit = request.query_params.get("limit", "20")
    limit = _parse_positive_integer(raw_limit, "limit")
    if limit > 100:
        raise ApiFailure(422, "invalid_request", "limit không hợp lệ")
    raw_before = request.query_params.get("before_id")
    before_id = _parse_positive_integer(raw_before, "before_id") if raw_before is not None else None
    return limit, before_id


def _require_json(request: Request) -> None:
    content_type = request.headers.get("content-type")
    if not content_type:
        raise ApiFailure(415, "unsupported_media_type", "Chỉ nhận application/json")
    parts = [part.strip() for part in content_type.split(";")]
    if parts[0].lower() != "application/json":
        raise ApiFailure(415, "unsupported_media_type", "Chỉ nhận application/json")
    if len(parts) > 2 or (len(parts) == 2 and parts[1].lower() != "charset=utf-8"):
        raise ApiFailure(415, "unsupported_media_type", "Chỉ nhận application/json")


def _require_origin(request: Request, settings: Settings) -> None:
    if request.headers.get("origin") != settings.portal_origin:
        raise ApiFailure(403, "forbidden", "Origin không được phép")


def create_app(
    settings: Settings,
    store: Any,
    *,
    verifier: AccessJwtVerifier | None = None,
) -> FastAPI:
    """Tạo app; cấu hình đã được Settings kiểm fail-closed trước đó."""

    app = FastAPI(title="Phong Hỏa W05 API", version="0.1.0")
    jwt_verifier = verifier or AccessJwtVerifier(settings)
    service = ReviewService(settings, store)

    @app.middleware("http")
    async def review_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/drafts"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = JWT_HEADER
        return response

    @app.exception_handler(ApiFailure)
    async def api_failure_handler(_request: Request, exc: ApiFailure):
        return _error(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, _exc: RequestValidationError):
        return _error(422, "invalid_request", "Yêu cầu không hợp lệ")

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, _exc: Exception):
        if request.url.path.startswith("/api/drafts"):
            return _error(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng")
        return _error(500, "internal_error", "Lỗi nội bộ")

    def require_review_role(request: Request) -> Principal:
        token = request.headers.get(JWT_HEADER)
        try:
            principal = jwt_verifier.verify(token)
        except AuthenticationUnavailable as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ xác thực tạm thời không sẵn sàng") from exc
        except AuthenticationError as exc:
            raise ApiFailure(401, "authentication_required", "Cần xác thực hợp lệ") from exc
        if not principal.roles.intersection(ALLOWED_ROLES):
            raise ApiFailure(403, "forbidden", "Tài khoản chưa được cấp quyền duyệt")
        return principal

    @app.get("/api/drafts", response_model=DraftPage)
    def list_drafts(
        request: Request,
        _principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        limit, before_id = _parse_list_query(request)
        return service.list(limit=limit, before_id=before_id)

    @app.get("/api/drafts/{draft_id}", response_model=DraftDetail)
    def get_draft(
        draft_id: str,
        _principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        return service.detail(_parse_positive_integer(draft_id, "draft_id"))

    @app.post(
        "/api/drafts/{draft_id}/decision",
        response_model=DecisionResponse,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DecisionRequest"}}},
            }
        },
    )
    async def decide_draft(
        request: Request,
        draft_id: str,
        principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        parsed_id = _parse_positive_integer(draft_id, "draft_id")
        _require_origin(request, settings)
        _require_json(request)
        try:
            raw = await request.json()
            body = DecisionRequest.model_validate(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ") from exc
        return service.decide(parsed_id, principal, body)

    default_openapi = app.openapi

    def openapi_with_manual_body_schema():
        schema = default_openapi()
        schema.setdefault("components", {}).setdefault("schemas", {})["DecisionRequest"] = (
            DecisionRequest.model_json_schema(ref_template="#/components/schemas/{model}")
        )
        return schema

    app.openapi = openapi_with_manual_body_schema
    return app
