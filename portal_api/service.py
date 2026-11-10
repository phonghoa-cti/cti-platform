"""Adapter mỏng từ HTTP sang core review SQLite."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import ValidationError

from phonghoa_extractor.store import (
    Actor,
    DraftConflictError,
    DraftInputError,
    DraftNotFoundError,
    DraftPolicyError,
    DraftSQLiteError,
    DraftStoreError,
)
from portal_api.auth import Principal
from portal_api.schemas import DecisionRequest, DecisionResponse, DraftDetail, DraftPage
from portal_api.settings import Settings


class ApiFailure(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message


def _translate_core_error(exc: DraftStoreError) -> ApiFailure:
    if isinstance(exc, DraftPolicyError):
        return ApiFailure(403, "forbidden", "Không được phép quyết định draft này")
    if isinstance(exc, DraftNotFoundError):
        return ApiFailure(404, "draft_not_found", "Không tìm thấy draft")
    if isinstance(exc, DraftConflictError):
        return ApiFailure(409, "draft_conflict", "Draft đã được quyết định hoặc phiên bản đã cũ")
    if isinstance(exc, DraftInputError):
        return ApiFailure(422, "invalid_request", "Yêu cầu không hợp lệ")
    if isinstance(exc, DraftSQLiteError):
        return ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng")
    return ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng")


class ReviewService:
    def __init__(self, settings: Settings, store: Any):
        self.settings = settings
        self.store = store

    def list(self, *, limit: int, before_id: int | None) -> dict[str, Any]:
        try:
            value = self.store.list_drafts(
                self.settings.db_path,
                limit=limit,
                before_id=before_id,
                timeout=self.settings.sqlite_timeout,
            )
            return DraftPage.model_validate(value).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc

    def detail(self, draft_id: int) -> dict[str, Any]:
        try:
            value = self.store.get_draft(
                self.settings.db_path, draft_id, timeout=self.settings.sqlite_timeout
            )
            return DraftDetail.model_validate(value).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc

    def decide(self, draft_id: int, principal: Principal, request: DecisionRequest) -> dict[str, Any]:
        try:
            result = self.store.decide_draft(
                self.settings.db_path,
                draft_id,
                actor=Actor(subject=principal.subject, roles=frozenset(principal.roles)),
                decision=request.decision,
                expected_version=request.expected_version,
                reason=request.reason,
                timeout=self.settings.sqlite_timeout,
            )
            return DecisionResponse.model_validate(asdict(result)).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc
