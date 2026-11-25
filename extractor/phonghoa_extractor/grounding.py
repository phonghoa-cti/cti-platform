"""Bước 5–7 của X01: đối chiếu bằng chứng, kiểm tra mã ATT&CK, lọc allowlist.

Nguyên tắc: AI đề xuất, CODE kiểm tra. Mục nào không tìm thấy trong văn bản gốc bị coi là "bịa" và loại.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from phonghoa_core.allowlist import Allowlist
from phonghoa_core.ioc import normalize
from phonghoa_extractor.evidence import find_evidence_span

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


def ground_iocs(raw_items: list[dict], source_text: str, allowlist: Allowlist | None = None) -> list[Item]:
    """raw_items: [{"type", "value", "evidence"}] do LLM trả về."""
    allow = allowlist or Allowlist.default()
    out: list[Item] = []
    for raw in raw_items:
        raw_value = raw.get("value")
        raw_evidence = raw.get("evidence")
        item = Item(
            "ioc",
            raw_value if isinstance(raw_value, str) else "",
            raw_evidence if isinstance(raw_evidence, str) else "",
        )
        item.extra["span"] = None
        if not isinstance(raw_value, str) or (raw_evidence is not None and not isinstance(raw_evidence, str)):
            item.keep, item.status, item.note = False, "khong_hop_le", "value/evidence phải là chuỗi"
            out.append(item)
            continue
        try:
            ioc = normalize(item.value)
        except ValueError as exc:
            item.keep, item.status, item.note = False, "khong_hop_le", str(exc)
            out.append(item)
            continue
        item.value, item.extra["type"] = ioc.value, ioc.type.value
        declared_type = raw.get("type")
        if declared_type is not None and declared_type != ioc.type.value:
            item.keep, item.status, item.note = False, "khong_hop_le", "type không khớp value"
        elif not item.evidence:
            item.keep, item.status, item.note = False, "bia", "thiếu evidence nguyên văn"
        elif (span := find_evidence_span(source_text, item.evidence, ioc)) is None:
            item.keep, item.status, item.note = False, "bia", "evidence không khớp IOC trong văn bản gốc"
        else:
            item.extra["span"] = span
        if item.keep and allow.contains(ioc):
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
    positions: dict[tuple[str, str, str], int] = {}
    result: list[Item] = []
    for it in items:
        key = (it.kind, str(it.extra.get("type", "")), it.value)
        if key not in positions:
            positions[key] = len(result)
            result.append(it)
        else:
            current = result[positions[key]]
            if it.extra.get("span") is not None and current.extra.get("span") is None:
                result[positions[key]] = it
    return result
