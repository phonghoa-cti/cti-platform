"""Hợp đồng JSON exact cho W05 API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

SQLITE_MAX_INTEGER = 2**63 - 1


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
