"""Audit TTP hậu xử lý, thuần offline, không suy diễn ngữ nghĩa."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Literal

from phonghoa_extractor.attack_catalog import AttackCatalog, TechniqueLookup, validate_technique

_MAX_SOURCE_BYTES = 1024 * 1024
_MAX_ITEMS = 500
_MAX_FIELD_BYTES = 8192
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_ITEM_KEYS = {"kind", "value", "evidence", "operational_draft_eligible"}
_KINDS = {"technique", "malware", "actor"}


class TtpAuditError(ValueError):
    """Lỗi ổn định chỉ mang mã, không mang dữ liệu CTI."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return self.code


@dataclass(frozen=True)
class TechniqueAudit:
    item_index: int
    kind: Literal["technique"]
    value: str
    evidence: str
    evidence_span: tuple[int, int] | None
    source_sha256: str
    config: Literal["C2", "C3"]
    quote_status: Literal["matched", "missing", "not_found", "ambiguous"]
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"]
    reason_code: str
    pin_kind: Literal["synthetic", "official"]
    snapshot_version: str
    snapshot_sha256: str
    semantic_status: Literal["unverified"]
    operational_draft_eligible: Literal[False]


@dataclass(frozen=True)
class _Projection:
    config: Literal["C2", "C3"]
    source_sha256: str
    mode: Literal["model_completed", "regex_fallback"]
    items: list[dict[str, object]]


def _fail(code: str) -> None:
    raise TtpAuditError(code)


def _validate_source(source_text: object) -> bytes:
    if type(source_text) is not str or not source_text:
        _fail("invalid_source_text")
    if len(source_text) > _MAX_SOURCE_BYTES:
        _fail("input_too_large")
    try:
        encoded = source_text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _fail("invalid_source_text")
    if len(encoded) > _MAX_SOURCE_BYTES:
        _fail("input_too_large")
    return encoded


def _validate_projection(adapter_result: object) -> _Projection:
    if type(adapter_result) is not dict:
        _fail("invalid_adapter_result")
    config = adapter_result.get("config")
    source = adapter_result.get("source")
    provider = adapter_result.get("provider")
    mode = adapter_result.get("result_mode")
    model_items_used = adapter_result.get("model_items_used")
    items = adapter_result.get("unverified_semantic_items")
    if not _valid_projection_header(adapter_result, config, source, provider):
        _fail("invalid_adapter_result")
    if not _valid_mode(mode, model_items_used) or type(items) is not list:
        _fail("invalid_adapter_result")
    if len(items) > _MAX_ITEMS:
        _fail("input_too_large")
    return _Projection(config=config, source_sha256=source["sha256"], mode=mode, items=items)


def _valid_projection_header(result: dict, config: object, source: object, provider: object) -> bool:
    valid_hash = (
        type(source) is dict
        and set(source) == {"sha256"}
        and type(source.get("sha256")) is str
        and _SHA256.fullmatch(source["sha256"]) is not None
    )
    return (
        type(result.get("schema_version")) is str
        and result["schema_version"] == "1.0"
        and type(config) is str
        and config in {"C2", "C3"}
        and result.get("mock_only") is True
        and valid_hash
        and type(provider) is dict
        and type(provider.get("destination")) is str
        and provider["destination"] == "fake_offline"
        and provider.get("egress") is False
    )


def _valid_mode(mode: object, model_items_used: object) -> bool:
    if type(mode) is not str:
        return False
    return (mode == "model_completed" and model_items_used is True) or (
        mode == "regex_fallback" and model_items_used is False
    )


def _validate_items(items: list[object], mode: str) -> list[dict[str, object]]:
    validated: list[dict[str, object]] = []
    for item in items:
        if type(item) is not dict or set(item) != _ITEM_KEYS:
            _fail("invalid_adapter_result")
        kind = item["kind"]
        value = item["value"]
        evidence = item["evidence"]
        if type(kind) is not str or kind not in _KINDS:
            _fail("invalid_adapter_result")
        _validate_field(value)
        _validate_field(evidence)
        if item["operational_draft_eligible"] is not False:
            _fail("invalid_adapter_result")
        validated.append(item)
    if mode == "regex_fallback" and validated:
        _fail("invalid_adapter_result")
    return validated


def _validate_field(value: object) -> None:
    if type(value) is not str:
        _fail("invalid_adapter_result")
    if len(value) > _MAX_FIELD_BYTES:
        _fail("input_too_large")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _fail("invalid_adapter_result")
    if len(encoded) > _MAX_FIELD_BYTES:
        _fail("input_too_large")


def _quote(source_text: str, evidence: str) -> tuple[str, tuple[int, int] | None]:
    if evidence == "":
        return "missing", None
    first = source_text.find(evidence)
    if first < 0:
        return "not_found", None
    if source_text.find(evidence, first + 1) >= 0:
        return "ambiguous", None
    return "matched", (first, first + len(evidence))


def _reason(quote_status: str, lookup: TechniqueLookup) -> str:
    quote_reasons = {
        "missing": "missing_evidence",
        "not_found": "evidence_not_in_source",
        "ambiguous": "evidence_ambiguous",
    }
    if quote_status != "matched":
        return quote_reasons[quote_status]
    if lookup.reason_code == "catalog_active":
        return "catalog_active_and_quote_matched"
    return lookup.reason_code


def _audit_item(
    *,
    item_index: int,
    item: dict[str, object],
    source_text: str,
    projection: _Projection,
    catalog: AttackCatalog,
) -> TechniqueAudit:
    value = item["value"]
    evidence = item["evidence"]
    quote_status, span = _quote(source_text, evidence)
    lookup = validate_technique(catalog, value)
    return TechniqueAudit(
        item_index=item_index,
        kind="technique",
        value=value,
        evidence=evidence,
        evidence_span=span,
        source_sha256=projection.source_sha256,
        config=projection.config,
        quote_status=quote_status,
        catalog_status=lookup.catalog_status,
        reason_code=_reason(quote_status, lookup),
        pin_kind=lookup.pin_kind,
        snapshot_version=lookup.snapshot_version,
        snapshot_sha256=lookup.snapshot_sha256,
        semantic_status="unverified",
        operational_draft_eligible=False,
    )


def audit_techniques(
    *, adapter_result: dict[str, object], source_text: str, catalog: AttackCatalog
) -> tuple[TechniqueAudit, ...]:
    """Kiểm source, quote và catalog; không cấp quyền draft hay xác nhận ngữ nghĩa."""
    source_bytes = _validate_source(source_text)
    if type(catalog) is not AttackCatalog:
        _fail("invalid_catalog")
    projection = _validate_projection(adapter_result)
    actual_hash = hashlib.sha256(source_bytes).hexdigest()
    if projection.source_sha256 != actual_hash:
        _fail("source_mismatch")
    items = _validate_items(projection.items, projection.mode)
    return tuple(
        _audit_item(
            item_index=index,
            item=item,
            source_text=source_text,
            projection=projection,
            catalog=catalog,
        )
        for index, item in enumerate(items)
        if item["kind"] == "technique"
    )
