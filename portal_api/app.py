"""FastAPI factory cho API duyệt W05 và tra cứu IOC W02."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from portal_api.assets import (
    AssetConflict,
    AssetExists,
    AssetNotFound,
    AssetStore,
    AssetsUnavailable,
    InvalidAsset,
)
from portal_api.auth import (
    AccessJwtVerifier,
    AuthenticationError,
    AuthenticationUnavailable,
    Principal,
)
from portal_api.ioc_lookup import (
    InvalidIoc,
    IocLookupPort,
    LookupService,
    LookupUnavailable,
    PrivateIoc,
)
from portal_api.schemas import (
    JSON_SAFE_INTEGER,
    SQLITE_MAX_INTEGER,
    AssetCreateRequest,
    AssetPage,
    AssetUpdateRequest,
    AssetView,
    DecisionRequest,
    DecisionRequestV1,
    DecisionResponse,
    DecisionResponseV1,
    DraftDetail,
    DraftDetailV1,
    DraftPage,
    DraftPageV1,
    IocLookupResponse,
    SelectionSaveRequest,
    SelectionView,
)
from portal_api.service import ApiFailure, ReviewService
from portal_api.settings import Settings

JWT_HEADER = "Cf-Access-Jwt-Assertion"
ALLOWED_ROLES = {"analyst", "admin"}
LOOKUP_ROLES = {"it", "analyst", "admin"}
POSITIVE_INTEGER = re.compile(r"[1-9][0-9]*\Z")
V1_BODY_LIMIT = 65_536
ASSET_BODY_LIMIT = 8_192


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _is_review_path(path: str) -> bool:
    return path.startswith("/api/drafts") or path.startswith("/api/v1/drafts")


def _is_lookup_path(path: str) -> bool:
    return path == "/api/ioc"


def _is_assets_path(path: str) -> bool:
    return path == "/api/assets" or path.startswith("/api/assets/")


def _parse_positive_integer(value: str, label: str, *, maximum: int = SQLITE_MAX_INTEGER) -> int:
    if not isinstance(value, str) or not POSITIVE_INTEGER.fullmatch(value):
        raise ApiFailure(422, "invalid_request", f"{label} không hợp lệ")
    if len(value) > len(str(maximum)):
        raise ApiFailure(422, "invalid_request", f"{label} không hợp lệ")
    parsed = int(value)
    if parsed > maximum:
        raise ApiFailure(422, "invalid_request", f"{label} không hợp lệ")
    return parsed


def _parse_list_query(request: Request, *, maximum: int = SQLITE_MAX_INTEGER) -> tuple[int, int | None]:
    allowed = {"limit", "before_id"}
    if set(request.query_params) - allowed:
        raise ApiFailure(422, "invalid_request", "Query không hợp lệ")
    for key in allowed:
        if len(request.query_params.getlist(key)) > 1:
            raise ApiFailure(422, "invalid_request", "Query không hợp lệ")
    raw_limit = request.query_params.get("limit", "20")
    limit = _parse_positive_integer(raw_limit, "limit", maximum=maximum)
    if limit > 100:
        raise ApiFailure(422, "invalid_request", "limit không hợp lệ")
    raw_before = request.query_params.get("before_id")
    before_id = (
        _parse_positive_integer(raw_before, "before_id", maximum=maximum) if raw_before is not None else None
    )
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


async def _read_limited_json(request: Request, limit: int) -> Any:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise ApiFailure(413, "request_too_large", "Nội dung yêu cầu quá lớn")
        chunks.append(chunk)
    return json.loads(b"".join(chunks))


async def _read_v1_json(request: Request) -> Any:
    return await _read_limited_json(request, V1_BODY_LIMIT)


def create_app(
    settings: Settings,
    store: Any,
    *,
    verifier: AccessJwtVerifier | None = None,
    lookup_port: IocLookupPort | None = None,
    asset_store: AssetStore | None = None,
) -> FastAPI:
    """Tạo app; cấu hình đã được Settings kiểm fail-closed trước đó."""

    app = FastAPI(title="Phong Hỏa W05 API", version="0.1.0")
    jwt_verifier = verifier or AccessJwtVerifier(settings)
    service = ReviewService(settings, store)
    lookup_service = LookupService(lookup_port, asset_store=asset_store)

    @app.middleware("http")
    async def review_headers(request: Request, call_next):
        response = await call_next(request)
        if (
            _is_review_path(request.url.path)
            or _is_lookup_path(request.url.path)
            or _is_assets_path(request.url.path)
        ):
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
        if _is_lookup_path(request.url.path):
            response = _error(
                503,
                "lookup_unavailable",
                "Dịch vụ tra cứu tạm thời không sẵn sàng",
            )
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = JWT_HEADER
            return response
        if _is_assets_path(request.url.path):
            response = _error(503, "assets_unavailable", "Dịch vụ tài sản tạm thời không sẵn sàng")
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = JWT_HEADER
            return response
        if _is_review_path(request.url.path):
            response = _error(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng")
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = JWT_HEADER
            return response
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

    def require_lookup_role(request: Request) -> Principal:
        token = request.headers.get(JWT_HEADER)
        try:
            principal = jwt_verifier.verify(token)
        except AuthenticationUnavailable as exc:
            raise ApiFailure(
                503,
                "lookup_unavailable",
                "Dịch vụ tra cứu tạm thời không sẵn sàng",
            ) from exc
        except AuthenticationError as exc:
            raise ApiFailure(401, "authentication_required", "Cần xác thực hợp lệ") from exc
        if not principal.roles.intersection(LOOKUP_ROLES):
            raise ApiFailure(
                403,
                "forbidden",
                "Tài khoản chưa được cấp quyền tra cứu IOC",
            )
        return principal

    def require_assets_role(request: Request) -> Principal:
        token = request.headers.get(JWT_HEADER)
        try:
            principal = jwt_verifier.verify(token)
        except AuthenticationUnavailable as exc:
            raise ApiFailure(
                503,
                "assets_unavailable",
                "Dịch vụ tài sản tạm thời không sẵn sàng",
            ) from exc
        except AuthenticationError as exc:
            raise ApiFailure(401, "authentication_required", "Cần xác thực hợp lệ") from exc
        if not principal.roles.intersection(LOOKUP_ROLES):
            raise ApiFailure(403, "forbidden", "Tài khoản chưa được cấp quyền quản lý tài sản")
        return principal

    def configured_asset_store() -> AssetStore:
        if asset_store is None:
            raise ApiFailure(503, "assets_unavailable", "Dịch vụ tài sản tạm thời không sẵn sàng")
        return asset_store

    def asset_failure(exc: Exception) -> ApiFailure:
        if isinstance(exc, InvalidAsset):
            return ApiFailure(422, "invalid_asset", "Tài sản không hợp lệ")
        if isinstance(exc, AssetExists):
            return ApiFailure(409, "asset_exists", "Tài sản đã tồn tại")
        if isinstance(exc, AssetNotFound):
            return ApiFailure(404, "asset_not_found", "Không tìm thấy tài sản")
        if isinstance(exc, AssetConflict):
            return ApiFailure(409, "asset_conflict", "Tài sản đã thay đổi")
        if isinstance(exc, AssetsUnavailable):
            return ApiFailure(503, "assets_unavailable", "Dịch vụ tài sản tạm thời không sẵn sàng")
        raise exc

    def as_asset_view(item) -> AssetView:
        return AssetView.model_validate(asdict(item))

    @app.get("/api/ioc", response_model=IocLookupResponse)
    def lookup_ioc(
        request: Request,
        principal: Principal = Depends(require_lookup_role),  # noqa: B008
    ):
        if set(request.query_params) != {"value"} or len(request.query_params.getlist("value")) != 1:
            raise ApiFailure(422, "invalid_ioc", "IOC không hợp lệ")
        raw = request.query_params["value"]
        try:
            return lookup_service.lookup(raw, principal.roles)
        except PrivateIoc as exc:
            raise ApiFailure(422, "private_ip", "IP nội bộ không thể tra cứu") from exc
        except InvalidIoc as exc:
            raise ApiFailure(422, "invalid_ioc", "IOC không hợp lệ") from exc
        except LookupUnavailable as exc:
            raise ApiFailure(
                503,
                "lookup_unavailable",
                "Dịch vụ tra cứu tạm thời không sẵn sàng",
            ) from exc

    @app.get("/api/assets", response_model=AssetPage)
    def list_assets(
        request: Request,
        _principal: Principal = Depends(require_assets_role),  # noqa: B008
    ):
        store = configured_asset_store()
        if set(request.query_params) - {"type"} or len(request.query_params.getlist("type")) > 1:
            raise ApiFailure(422, "invalid_asset", "Query tài sản không hợp lệ")
        asset_type = request.query_params.get("type")
        if asset_type is not None and asset_type not in {"domain", "ip_range"}:
            raise ApiFailure(422, "invalid_asset", "Query tài sản không hợp lệ")
        try:
            return AssetPage(items=[as_asset_view(item) for item in store.list(asset_type)])
        except Exception as exc:
            raise asset_failure(exc) from exc

    @app.post("/api/assets", response_model=AssetView, status_code=201)
    async def create_asset(
        request: Request,
        principal: Principal = Depends(require_assets_role),  # noqa: B008
    ):
        store = configured_asset_store()
        _require_origin(request, settings)
        _require_json(request)
        try:
            body = AssetCreateRequest.model_validate(await _read_limited_json(request, ASSET_BODY_LIMIT))
            return as_asset_view(store.create(body.type, body.value, body.note, principal.subject))
        except ApiFailure:
            raise
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError, ValueError) as exc:
            if isinstance(exc, InvalidAsset):
                raise asset_failure(exc) from exc
            raise ApiFailure(422, "invalid_asset", "Tài sản không hợp lệ") from exc
        except Exception as exc:
            raise asset_failure(exc) from exc

    @app.put("/api/assets/{asset_id}", response_model=AssetView)
    async def update_asset(
        request: Request,
        asset_id: str,
        principal: Principal = Depends(require_assets_role),  # noqa: B008
    ):
        store = configured_asset_store()
        parsed_id = _parse_positive_integer(asset_id, "asset_id", maximum=JSON_SAFE_INTEGER)
        _require_origin(request, settings)
        _require_json(request)
        try:
            body = AssetUpdateRequest.model_validate(await _read_limited_json(request, ASSET_BODY_LIMIT))
            return as_asset_view(
                store.update(
                    parsed_id,
                    body.type,
                    body.value,
                    body.note,
                    body.expected_version,
                    principal.subject,
                )
            )
        except ApiFailure:
            raise
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError, ValueError) as exc:
            if isinstance(exc, InvalidAsset):
                raise asset_failure(exc) from exc
            raise ApiFailure(422, "invalid_asset", "Tài sản không hợp lệ") from exc
        except Exception as exc:
            raise asset_failure(exc) from exc

    @app.delete("/api/assets/{asset_id}", status_code=204)
    def delete_asset(
        request: Request,
        asset_id: str,
        principal: Principal = Depends(require_assets_role),  # noqa: B008
    ):
        store = configured_asset_store()
        parsed_id = _parse_positive_integer(asset_id, "asset_id", maximum=JSON_SAFE_INTEGER)
        _require_origin(request, settings)
        if (
            set(request.query_params) != {"expected_version"}
            or len(request.query_params.getlist("expected_version")) != 1
        ):
            raise ApiFailure(422, "invalid_asset", "Query tài sản không hợp lệ")
        expected_version = _parse_positive_integer(
            request.query_params["expected_version"],
            "expected_version",
            maximum=JSON_SAFE_INTEGER,
        )
        try:
            store.delete(parsed_id, expected_version, principal.subject)
        except Exception as exc:
            raise asset_failure(exc) from exc
        return Response(status_code=204)

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

    @app.get("/api/v1/drafts", response_model=DraftPageV1)
    def list_drafts_v1(
        request: Request,
        _principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        limit, before_id = _parse_list_query(request, maximum=JSON_SAFE_INTEGER)
        return service.list_v1(limit=limit, before_id=before_id)

    @app.get("/api/v1/drafts/{draft_id}", response_model=DraftDetailV1)
    def get_draft_v1(
        draft_id: str,
        _principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        parsed_id = _parse_positive_integer(draft_id, "draft_id", maximum=JSON_SAFE_INTEGER)
        return service.detail_v1(parsed_id)

    @app.post(
        "/api/v1/drafts/{draft_id}/selection",
        response_model=SelectionView,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/SelectionSaveRequest"}}
                },
            }
        },
    )
    async def save_selection_v1(
        request: Request,
        draft_id: str,
        principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        parsed_id = _parse_positive_integer(draft_id, "draft_id", maximum=JSON_SAFE_INTEGER)
        _require_origin(request, settings)
        _require_json(request)
        try:
            body = SelectionSaveRequest.model_validate(await _read_v1_json(request))
        except ApiFailure:
            raise
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ") from exc
        return service.save_selection_v1(parsed_id, principal, body)

    @app.post(
        "/api/v1/drafts/{draft_id}/decision",
        response_model=DecisionResponseV1,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/DecisionRequestV1"}}
                },
            }
        },
    )
    async def decide_draft_v1(
        request: Request,
        draft_id: str,
        principal: Principal = Depends(require_review_role),  # noqa: B008
    ):
        parsed_id = _parse_positive_integer(draft_id, "draft_id", maximum=JSON_SAFE_INTEGER)
        _require_origin(request, settings)
        _require_json(request)
        try:
            body = DecisionRequestV1.model_validate(await _read_v1_json(request))
        except ApiFailure:
            raise
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ") from exc
        return service.decide_v1(parsed_id, principal, body)

    default_openapi = app.openapi

    def openapi_with_manual_body_schema():
        schema = default_openapi()
        schema.setdefault("components", {}).setdefault("schemas", {})["DecisionRequest"] = (
            DecisionRequest.model_json_schema(ref_template="#/components/schemas/{model}")
        )
        schema["components"]["schemas"]["DecisionRequestV1"] = DecisionRequestV1.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        schema["components"]["schemas"]["SelectionSaveRequest"] = SelectionSaveRequest.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        return schema

    app.openapi = openapi_with_manual_body_schema
    return app
