"""Tạo bản nháp IOC C1 ngoại tuyến để analyst duyệt."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from phonghoa_core.extract import extract_iocs
from phonghoa_core.ioc import Ioc
from phonghoa_extractor.evidence import quote_for_ioc
from phonghoa_extractor.grounding import Item, ground_iocs
from phonghoa_extractor.injection import scan

_LANGUAGES = {"vi", "en"}
_TLP_LABELS = {"TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}


def build_regex_draft(
    text: str,
    source: str,
    language: str,
    tlp: str = "TLP:AMBER",
) -> dict[str, Any]:
    """Tạo draft pending; không gọi mạng, model hoặc kho dữ liệu."""
    if not isinstance(text, str):
        raise ValueError("text phải là chuỗi")
    if language not in _LANGUAGES:
        raise ValueError("language phải là vi hoặc en")
    canonical_tlp = _canonical_tlp(tlp)
    raw_items = [_raw_item(text, ioc) for ioc in extract_iocs(text)]
    grounded = ground_iocs([item for item in raw_items if item is not None], text)
    findings = scan(text)
    return {
        "schema_version": "1.0",
        "status": "pending",
        "source": {
            "name": source,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        "language": language,
        "tlp": canonical_tlp,
        "text": text,
        "items": [_serialize_item(item) for item in grounded],
        "injection_warning": bool(findings),
        "findings": [asdict(finding) for finding in findings],
        "model": "regex-C1",
        "cost_tokens": 0,
    }


def _canonical_tlp(tlp: str) -> str:
    if not isinstance(tlp, str):
        raise ValueError("TLP phải là chuỗi")
    label = tlp.strip().upper()
    if not label.startswith("TLP:"):
        label = f"TLP:{label}"
    if label not in _TLP_LABELS:
        raise ValueError(f"TLP không hợp lệ: {tlp!r}")
    return label


def _raw_item(text: str, ioc: Ioc) -> dict[str, str] | None:
    quote = quote_for_ioc(text, ioc)
    if quote is None:
        return None
    evidence, _ = quote
    return {"type": ioc.type.value, "value": ioc.value, "evidence": evidence}


def _serialize_item(item: Item) -> dict[str, Any]:
    span = item.extra.get("span")
    return {
        "kind": item.kind,
        "type": item.extra.get("type"),
        "value": item.value,
        "span": list(span) if span is not None else None,
        "evidence": item.evidence,
        "keep": item.keep,
        "warning": item.note or None,
        "status": item.status,
    }
