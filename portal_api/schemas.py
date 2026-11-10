"""Hợp đồng JSON exact cho W05 API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

SQLITE_MAX_INTEGER = 2**63 - 1
JSON_SAFE_INTEGER = 2**53 - 1
MAX_SELECTION_INDICES = 1024
SafeNonNegativeInt = Annotated[StrictInt, Field(ge=0, le=JSON_SAFE_INTEGER)]
SafePositiveInt = Annotated[StrictInt, Field(ge=1, le=JSON_SAFE_INTEGER)]


class ExactModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Source(ExactModel):
    name: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DraftSummary(ExactModel):
    id: Annotated[StrictInt, Field(ge=1, le=SQLITE_MAX_INTEGER)]
    created_at: str
    status: Literal["pending"]
    source: Source
    language: Literal["vi", "en"]
    tlp: Literal["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"]
    item_count: Annotated[StrictInt, Field(ge=0)]
    injection_warning: bool
    review_status: Literal["pending"]
    review_version: Literal[0]


class DraftPage(ExactModel):
    items: list[DraftSummary]
    next_before_id: Annotated[StrictInt, Field(ge=1, le=SQLITE_MAX_INTEGER)] | None


class DraftItem(ExactModel):
    kind: str
    type: str
    value: str
    span: Annotated[list[Annotated[StrictInt, Field(ge=0)]], Field(min_length=2, max_length=2)] | None
    evidence: str
    keep: bool
    warning: str | None
    status: Literal["ok", "allowlist", "bia"]

    @model_validator(mode="after")
    def supported_kept_kind(self):
        if self.keep and self.kind != "ioc":
            raise ValueError("kept item kind is unsupported")
        return self


class Finding(ExactModel):
    paragraph: Annotated[StrictInt, Field(ge=1)]
    rule: str
    excerpt: str


class Review(ExactModel):
    status: Literal["pending", "approved", "rejected"]
    version: Annotated[StrictInt, Field(ge=0, le=1)]
    created_by_subject: str | None
    decided_by_subject: str | None
    decided_at: str | None
    reason: str | None


class DraftDetail(ExactModel):
    id: Annotated[StrictInt, Field(ge=1, le=SQLITE_MAX_INTEGER)]
    created_at: str
    schema_version: Literal["1.0"]
    status: Literal["pending"]
    source: Source
    language: Literal["vi", "en"]
    tlp: Literal["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"]
    text: str
    items: list[DraftItem]
    injection_warning: bool
    findings: list[Finding]
    model: str
    cost_tokens: Annotated[StrictInt, Field(ge=0)]
    review: Review


class DecisionRequest(ExactModel):
    decision: Literal["approve", "reject"]
    expected_version: Annotated[StrictInt, Field(ge=0, le=SQLITE_MAX_INTEGER)]
    reason: str | None = None

    @model_validator(mode="after")
    def reason_matches_decision(self):
        if self.decision == "approve" and self.reason is not None:
            raise ValueError("approve does not accept reason")
        if self.decision == "reject":
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("reject requires reason")
            self.reason = self.reason.strip()
        return self


class DecisionResponse(ExactModel):
    draft_id: Annotated[StrictInt, Field(ge=1, le=SQLITE_MAX_INTEGER)]
    status: Literal["approved", "rejected"]
    version: Literal[1]
    decided_by_subject: str
    decided_at: str
    reason: str | None


class DraftSummaryV1(ExactModel):
    id: SafePositiveInt
    created_at: str
    status: Literal["pending"]
    source: Source
    language: Literal["vi", "en"]
    tlp: Literal["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"]
    item_count: SafeNonNegativeInt
    injection_warning: bool
    review_status: Literal["pending"]
    review_version: SafeNonNegativeInt
    selection_version: SafeNonNegativeInt


class DraftPageV1(ExactModel):
    items: list[DraftSummaryV1]
    next_before_id: SafePositiveInt | None


class DraftItemV1(ExactModel):
    kind: str
    type: str
    value: str
    span: Annotated[list[SafeNonNegativeInt], Field(min_length=2, max_length=2)] | None
    evidence: str
    keep: bool
    warning: str | None
    status: Literal["ok", "allowlist", "bia"]

    @model_validator(mode="after")
    def supported_kept_kind(self):
        if self.keep and self.kind != "ioc":
            raise ValueError("kept item kind is unsupported")
        return self


class FindingV1(ExactModel):
    paragraph: SafePositiveInt
    rule: str
    excerpt: str


class ReviewV1(ExactModel):
    status: Literal["pending", "approved", "rejected"]
    version: SafeNonNegativeInt
    created_by_subject: str | None
    decided_by_subject: str | None
    decided_at: str | None
    reason: str | None


class SelectionView(ExactModel):
    review_version: SafeNonNegativeInt
    selection_version: SafeNonNegativeInt
    selected_indices: list[SafeNonNegativeInt]
    selected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    saved_by_subject: str | None
    saved_at: str | None
    changed: bool
    ai_extracted_count: SafeNonNegativeInt
    ai_eligible_count: SafeNonNegativeInt
    human_deselected_count: SafeNonNegativeInt
    selection_save_count: SafeNonNegativeInt


class DraftDetailV1(ExactModel):
    id: SafePositiveInt
    created_at: str
    schema_version: Literal["1.0"]
    status: Literal["pending"]
    source: Source
    language: Literal["vi", "en"]
    tlp: Literal["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"]
    text: str
    items: list[DraftItemV1]
    injection_warning: bool
    findings: list[FindingV1]
    model: str
    cost_tokens: SafeNonNegativeInt
    review: ReviewV1
    selection: SelectionView


class SelectionSaveRequest(ExactModel):
    expected_version: SafeNonNegativeInt
    selected_indices: Annotated[list[SafeNonNegativeInt], Field(max_length=MAX_SELECTION_INDICES)]

    @model_validator(mode="after")
    def unique_indices(self):
        if len(set(self.selected_indices)) != len(self.selected_indices):
            raise ValueError("selected_indices must be unique")
        return self


class DecisionRequestV1(ExactModel):
    decision: Literal["approve", "reject"]
    expected_version: SafeNonNegativeInt
    reason: str | None = None

    @model_validator(mode="after")
    def reason_matches_decision(self):
        if self.decision == "approve" and self.reason is not None:
            raise ValueError("approve does not accept reason")
        if self.decision == "reject":
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("reject requires reason")
            self.reason = self.reason.strip()
        return self


class DecisionResponseV1(ExactModel):
    draft_id: SafePositiveInt
    status: Literal["approved", "rejected"]
    version: SafeNonNegativeInt
    decided_by_subject: str
    decided_at: str
    reason: str | None
    selection_version: SafeNonNegativeInt
    selected_indices: list[SafeNonNegativeInt]
    selected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
