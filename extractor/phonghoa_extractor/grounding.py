"""Bước 5–7 của X01: đối chiếu bằng chứng, kiểm tra mã ATT&CK, lọc allowlist.

Nguyên tắc: AI đề xuất, CODE kiểm tra. Mục nào không tìm thấy trong văn bản gốc bị coi là "bịa" và loại.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from phonghoa_core.allowlist import Allowlist
from phonghoa_core.ioc import normalize, refang

_TECHNIQUE_ID = re.compile(r"^T\d{4}(\.\d{3})?$")


@dataclass
class Item:
    kind: str  # ioc | technique | malware | actor
    value: str
    evidence: str = ""
    keep: bool = True
    status: str = "ok"  # ok | bia | allowlist | ma_sai | khong_hop_le
    note: str = ""
    extra: dict = field(default_factory=dict)


def _squash(text: str) -> str:
    """Chuẩn hóa để so khớp: refang, chữ thường, gộp khoảng trắng."""
    return re.sub(r"\s+", " ", refang(text)).lower()


def ground_iocs(raw_items: list[dict], source_text: str, allowlist: Allowlist | None = None) -> list[Item]:
    """raw_items: [{"type", "value", "evidence"}] do LLM trả về."""
    haystack = _squash(source_text)
    allow = allowlist or Allowlist.default()
    out: list[Item] = []
    for raw in raw_items:
        item = Item("ioc", str(raw.get("value", "")), str(raw.get("evidence", "")))
        try:
            ioc = normalize(item.value)
        except ValueError as exc:
            item.keep, item.status, item.note = False, "khong_hop_le", str(exc)
            out.append(item)
            continue
        item.value, item.extra["type"] = ioc.value, ioc.type.value
        # Giá trị phải xuất hiện trong văn bản (so ở dạng đã refang, không phân biệt hoa thường).
        needle = _squash(raw.get("value", ""))
        if needle not in haystack and ioc.value.lower() not in haystack:
            item.keep, item.status, item.note = False, "bia", "không có trong văn bản gốc"
        elif allow.contains(ioc):
            item.keep, item.status, item.note = False, "allowlist", "hạ tầng hợp pháp, mặc định bỏ chọn"
        out.append(item)
    return _dedupe(out)


def ground_techniques(raw_items: list[dict], known_ids: set[str]) -> list[Item]:
    """known_ids: tập mã kỹ thuật lấy từ bộ STIX ATT&CK của MITRE (đã nạp vào OpenCTI)."""
    out: list[Item] = []
    for raw in raw_items:
        tid = str(raw.get("id", "")).strip().upper()
        item = Item("technique", tid, str(raw.get("evidence", "")))
        if not _TECHNIQUE_ID.match(tid) or tid not in known_ids:
            item.keep, item.status, item.note = False, "ma_sai", "mã kỹ thuật không tồn tại trong ATT&CK"
        out.append(item)
    return _dedupe(out)


def _dedupe(items: list[Item]) -> list[Item]:
    seen: set[tuple[str, str]] = set()
    result = []
    for it in items:
        key = (it.kind, it.value.lower())
        if key not in seen:
            seen.add(key)
            result.append(it)
    return result
