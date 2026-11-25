"""Adapter mỏng từ HTTP sang core review SQLite."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import ValidationError

from phonghoa_extractor.store import (
    Actor,
    DraftConflictError,
    DraftDatabaseNotFoundError,
    DraftInputError,
    DraftNotFoundError,
    DraftPolicyError,
    DraftSQLiteError,
    DraftStoreError,
)
from portal_api.auth import Principal
from portal_api.schemas import (
    JSON_SAFE_INTEGER,
    DecisionRequest,
    DecisionRequestV1,
    DecisionResponse,
    DecisionResponseV1,
    DraftDetail,
    DraftDetailV1,
    DraftPage,
    DraftPageV1,
    SelectionSaveRequest,
    SelectionView,
)
from portal_api.settings import Settings


class ApiFailure(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message


def _translate_core_error(exc: DraftStoreError, *, database_missing_unavailable: bool = False) -> ApiFailure:
    if database_missing_unavailable and isinstance(exc, DraftDatabaseNotFoundError):
        return ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng")
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


def _selection_view(result: Any) -> dict[str, Any]:
    value = {
        "review_version": result.review_version,
        "selection_version": result.selection_version,
        "selected_indices": list(result.selected_indices),
        "selected_sha256": result.selected_sha256,
        "saved_by_subject": result.saved_by_subject,
        "saved_at": result.saved_at,
        "changed": result.changed,
        "ai_extracted_count": result.ai_extracted_count,
        "ai_eligible_count": result.ai_eligible_count,
        "human_deselected_count": result.human_deselected_count,
        "selection_save_count": result.selection_save_count,
    }
    return SelectionView.model_validate(value).model_dump(mode="json")


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

    def list_v1(self, *, limit: int, before_id: int | None) -> dict[str, Any]:
        try:
            value = self.store.list_drafts_with_selection_version(
                self.settings.db_path,
                limit=limit,
                before_id=before_id,
                timeout=self.settings.sqlite_timeout,
            )
            return DraftPageV1.model_validate(value).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc, database_missing_unavailable=True) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc

    def detail_v1(self, draft_id: int) -> dict[str, Any]:
        try:
            value = self.store.get_draft_with_selection(
                self.settings.db_path, draft_id, timeout=self.settings.sqlite_timeout
            )
            mapped = {**value, "selection": _selection_view(value["selection"])}
            return DraftDetailV1.model_validate(mapped).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc, database_missing_unavailable=True) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc

    def save_selection_v1(
        self, draft_id: int, principal: Principal, request: SelectionSaveRequest
    ) -> dict[str, Any]:
        try:
            result = self.store.save_selection(
                self.settings.db_path,
                draft_id,
                actor=Actor(subject=principal.subject, roles=frozenset(principal.roles)),
                selected_indices=request.selected_indices,
                expected_version=request.expected_version,
                timeout=self.settings.sqlite_timeout,
                max_version=JSON_SAFE_INTEGER,
            )
            return _selection_view(result)
        except DraftStoreError as exc:
            raise _translate_core_error(exc, database_missing_unavailable=True) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc

    def decide_v1(self, draft_id: int, principal: Principal, request: DecisionRequestV1) -> dict[str, Any]:
        try:
            result = self.store.decide_draft_with_selection(
                self.settings.db_path,
                draft_id,
                actor=Actor(subject=principal.subject, roles=frozenset(principal.roles)),
                decision=request.decision,
                expected_version=request.expected_version,
                reason=request.reason,
                timeout=self.settings.sqlite_timeout,
                max_version=JSON_SAFE_INTEGER,
            )
            value = {
                "draft_id": result.draft_id,
                "status": result.status,
                "version": result.version,
                "decided_by_subject": result.decided_by_subject,
                "decided_at": result.decided_at,
                "reason": result.reason,
                "selection_version": result.selection_version,
                "selected_indices": list(result.selected_indices),
                "selected_sha256": result.selected_sha256,
            }
            return DecisionResponseV1.model_validate(value).model_dump(mode="json")
        except DraftStoreError as exc:
            raise _translate_core_error(exc, database_missing_unavailable=True) from exc
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiFailure(503, "review_unavailable", "Dịch vụ duyệt tạm thời không sẵn sàng") from exc
