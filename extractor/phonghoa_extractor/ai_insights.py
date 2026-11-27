"""F20 (F18 #7 AI Insights): tóm tắt tiếng Việt có dẫn chứng từ danh sách STIX object và/hoặc văn bản báo cáo.

Nguyên tắc:
- Mỗi nhận định (claim) phải trích ít nhất một STIX id có trong đầu vào; claim không có chứng cứ bị loại.
- Mặc định dùng template ngoại tuyến, tất định (cùng đầu vào → cùng kết quả), không gọi mạng.
- Provider LLM tùy chọn chỉ được dùng khi TLP cho phép; đầu ra LLM sai schema thì quay về template.
- Chỉ mô tả dữ liệu đã có, KHÔNG dự báo.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from hashlib import sha256

from phonghoa_core.extract import count_by_type, extract_iocs
from phonghoa_extractor.ai_provider import AiPolicyError, TextProvider, ensure_tlp_allowed, max_tlp
from phonghoa_extractor.ai_provider import parse_json_object as _parse_json
from phonghoa_extractor.injection import scan, wrap_as_data

OFFLINE_PROVIDER = "offline-template"
DISCLAIMER = (
    "Tóm tắt chỉ mô tả dữ liệu đã có, không phải dự báo; người phân tích cần kiểm tra trước khi dùng."
)
MAX_OBJECTS = 500
MAX_TEXT_CHARS = 200_000
MAX_CLAIMS = 20
MAX_CLAIM_CHARS = 500
NAMES_PER_CLAIM = 5
_REPORT_NAMESPACE = uuid.UUID("5b0c3c1e-7d1f-4f43-9d3e-2f20a0b7f020")  # namespace riêng của dự án

# Nhãn tiếng Việt cho các loại STIX thường gặp, theo thứ tự hiển thị cố định.
TYPE_LABELS = {
    "intrusion-set": "nhóm xâm nhập",
    "threat-actor": "tác nhân đe dọa",
    "campaign": "chiến dịch",
    "malware": "mã độc",
    "tool": "công cụ",
    "attack-pattern": "kỹ thuật tấn công",
    "vulnerability": "lỗ hổng",
    "indicator": "chỉ báo (indicator)",
    "report": "báo cáo",
}
# Marking-definition TLP 1.0 chuẩn trong đặc tả STIX 2.1.
TLP_MARKINGS = {
    "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9": "TLP:CLEAR",
    "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da": "TLP:GREEN",
    "marking-definition--f88d31f6-486f-44da-b317-01333bde0b82": "TLP:AMBER",
    "marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed": "TLP:RED",
}


def report_text_id(text: str) -> str:
    """Id tất định cho văn bản báo cáo không có STIX id, để claim vẫn trích được nguồn."""
    return f"report--{uuid.uuid5(_REPORT_NAMESPACE, sha256(text.encode()).hexdigest())}"


def summarize(
    objects: list[dict],
    report_text: str | None = None,
    tlp: str = "TLP:CLEAR",
    provider: TextProvider | None = None,
) -> dict:
    items = _validate_objects(objects)
    if report_text is not None and (not isinstance(report_text, str) or len(report_text) > MAX_TEXT_CHARS):
        raise ValueError("invalid_report_text")
    effective_tlp = _effective_tlp(items, tlp)
    warnings = _injection_warnings(items, report_text)
    claims = _offline_claims(items, report_text)
    used = OFFLINE_PROVIDER
    if provider is not None and claims:
        llm_claims = _try_llm(items, report_text, effective_tlp, provider, warnings)
        if llm_claims is not None:
            claims, used = llm_claims, provider.name
    return {
        "summary": _render(claims),
        "claims": claims,
        "provider": used,
        "tlp": effective_tlp,
        "time_range": _time_range(items),
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def _validate_objects(objects: list[dict]) -> list[dict]:
    if not isinstance(objects, list) or len(objects) > MAX_OBJECTS:
        raise ValueError("invalid_objects")
    for obj in objects:
        kind = obj.get("type") if isinstance(obj, dict) else None
        oid = obj.get("id") if isinstance(obj, dict) else None
        if not isinstance(kind, str) or not isinstance(oid, str) or not oid.startswith(f"{kind}--"):
            raise ValueError("invalid_stix_object")
    return sorted(objects, key=lambda o: o["id"])


def _effective_tlp(items: list[dict], tlp: str) -> str:
    labels = [tlp]
    for obj in items:
        labels += [TLP_MARKINGS[ref] for ref in obj.get("object_marking_refs", []) if ref in TLP_MARKINGS]
    return max_tlp(labels)


def _injection_warnings(items: list[dict], report_text: str | None) -> list[str]:
    texts = [str(o.get("description", "")) + "\n\n" + str(o.get("name", "")) for o in items]
    texts.append(report_text or "")
    return ["prompt_injection_suspected"] if any(scan(t) for t in texts) else []


def _offline_claims(items: list[dict], report_text: str | None) -> list[dict]:
    claims = _type_claims(items)
    window = _time_range(items)
    if window:
        dated = sorted((o for o in items if _day(o)), key=lambda o: (_day(o), o["id"]))
        text = f"Dữ liệu trải từ {window['from']} đến {window['to']} (theo trường created)."
        claims.append({"text": text, "evidence": sorted({dated[0]["id"], dated[-1]["id"]})})
    if report_text:
        claims.append(_report_claim(report_text))
    return claims


def _type_claims(items: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for obj in items:
        groups[obj["type"]].append(obj)
    order = [t for t in TYPE_LABELS if t in groups] + sorted(t for t in groups if t not in TYPE_LABELS)
    claims = []
    for kind in order:
        members = groups[kind]
        names = sorted({str(o.get("name") or o["id"]) for o in members})
        shown = ", ".join(names[:NAMES_PER_CLAIM]) + (", ..." if len(names) > NAMES_PER_CLAIM else "")
        label = TYPE_LABELS.get(kind, kind)
        claims.append(
            {"text": f"Có {len(members)} {label}: {shown}.", "evidence": [o["id"] for o in members]}
        )
    return claims


def _report_claim(report_text: str) -> dict:
    counts = count_by_type(extract_iocs(report_text))
    if counts:
        detail = ", ".join(f"{n} {kind}" for kind, n in sorted(counts.items()))
        text = f"Văn bản báo cáo chứa {sum(counts.values())} IOC nhận diện bằng regex ({detail})."
    else:
        text = "Văn bản báo cáo không có IOC nhận diện được bằng regex."
    return {"text": text, "evidence": [report_text_id(report_text)]}


def _day(obj: dict) -> str:
    value = obj.get("created")
    return value[:10] if isinstance(value, str) and len(value) >= 10 else ""


def _time_range(items: list[dict]) -> dict | None:
    days = sorted(d for d in (_day(o) for o in items) if d)
    return {"from": days[0], "to": days[-1]} if days else None


def _render(claims: list[dict]) -> str:
    if not claims:
        return "Không đủ dữ liệu để tóm tắt."
    return "\n".join(f"- {c['text']} [nguồn: {', '.join(c['evidence'])}]" for c in claims)


def _try_llm(
    items: list[dict], report_text: str | None, tlp: str, provider: TextProvider, warnings: list[str]
) -> list[dict] | None:
    allowed = {o["id"] for o in items} | ({report_text_id(report_text)} if report_text else set())
    try:
        ensure_tlp_allowed(tlp, provider)
        reply = provider.complete(_build_prompt(items, report_text))
        return _validate_claims(_parse_json(reply), allowed)
    except AiPolicyError as exc:
        warnings.append(str(exc))
        return None


def _build_prompt(items: list[dict], report_text: str | None) -> str:
    keep = ("id", "type", "name", "description", "created", "pattern", "labels")
    data = {"objects": [{k: o[k] for k in keep if k in o} for o in items]}
    if report_text:
        data["report_text"] = {"id": report_text_id(report_text), "text": report_text}
    return (
        "Bạn tóm tắt dữ liệu threat intelligence bằng tiếng Việt, chỉ mô tả, không dự báo.\n"
        'Chỉ trả về JSON: {"claims": [{"text": "...", "evidence": ["<stix id>"]}]}. '
        "Mỗi claim phải trích id có trong dữ liệu.\n" + wrap_as_data(json.dumps(data, ensure_ascii=False))
    )


def _validate_claims(payload: dict, allowed: set[str]) -> list[dict]:
    claims = payload.get("claims")
    if set(payload) != {"claims"} or not isinstance(claims, list) or not 0 < len(claims) <= MAX_CLAIMS:
        raise AiPolicyError("llm_invalid_output")
    return [_validate_claim(c, allowed) for c in claims]


def _validate_claim(claim: object, allowed: set[str]) -> dict:
    if not isinstance(claim, dict) or set(claim) != {"text", "evidence"}:
        raise AiPolicyError("llm_invalid_output")
    text, evidence = claim["text"], claim["evidence"]
    if not isinstance(text, str) or not 0 < len(text.strip()) <= MAX_CLAIM_CHARS:
        raise AiPolicyError("llm_invalid_output")
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(isinstance(e, str) and e in allowed for e in evidence)
    ):
        raise AiPolicyError("llm_invalid_output")
    return {"text": text.strip(), "evidence": sorted(set(evidence))}
