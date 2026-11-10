"""Adapter C2/C3 ngoại tuyến: phản hồi model là dữ liệu phải kiểm trước khi dùng."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from phonghoa_core.extract import extract_iocs
from phonghoa_extractor.evidence import quote_for_ioc
from phonghoa_extractor.grounding import Item, ground_iocs

SCHEMA_VERSION = "x01-extraction-response/1.0"
PROMPT_VERSION = "extractor-v1"
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_ITEMS = 500
MAX_FIELD_BYTES = 8 * 1024
MAX_METADATA_LENGTH = 256
TLP_LABELS = {"TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}
IOC_TYPES = {"domain", "ipv4", "ipv6", "url", "email", "md5", "sha1", "sha256"}
ROLES = {"attacker", "victim", "benign"}
ROOT_KEYS = {"iocs", "techniques", "malware", "actors"}
TECHNIQUE_ID = re.compile(r"^T\d{4}(?:\.\d{3})?$")


class AdapterError(ValueError):
    """Lỗi ổn định không mang raw response hay nội dung CTI."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Lỗi adapter: {code}")


@dataclass(frozen=True)
class ProviderRequest:
    text: str
    language: Literal["vi", "en"]
    tlp: str
    config: Literal["C2", "C3"]
    schema_version: str = SCHEMA_VERSION
    prompt_version: str = PROMPT_VERSION


@dataclass(frozen=True)
class ProviderResponse:
    status: object
    payload: object | None = None
    model_id: object = ""
    usage: object | None = None
    retryable: object = False
    error_code: object | None = None


class LLMProvider(Protocol):
    name: object
    destination: object
    egress: object

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class ScriptedProvider:
    """Provider deterministic chỉ trả chuỗi response đã nạp trong bộ nhớ."""

    def __init__(
        self, responses: list[ProviderResponse], *, name: object, destination: object, egress: object
    ):
        self.responses = list(responses)
        self.name = name
        self.destination = destination
        self.egress = egress
        self.calls = 0

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        del request
        self.calls += 1
        if not self.responses:
            return ProviderResponse(status="error", error_code="script_exhausted", retryable=False)
        return self.responses.pop(0)


def validate_payload(payload: object) -> dict[str, list[dict[str, str]]]:
    """Kiểm đúng schema X01 nhỏ; không cố làm JSON Schema engine tổng quát."""
    if not isinstance(payload, dict) or set(payload) != ROOT_KEYS:
        raise AdapterError("invalid_response")
    _check_serialized_size(payload)
    validators = {
        "iocs": _validate_ioc,
        "techniques": _validate_technique,
        "malware": lambda item: _validate_named(item, "name"),
        "actors": lambda item: _validate_named(item, "name"),
    }
    result: dict[str, list[dict[str, str]]] = {}
    for key, validator in validators.items():
        items = payload[key]
        if not isinstance(items, list) or len(items) > MAX_ITEMS:
            raise AdapterError("invalid_response")
        result[key] = [validator(item) for item in items]
    return result


def run_extraction(
    *,
    text: str,
    language: str,
    tlp: object,
    config: str,
    provider: LLMProvider,
) -> dict[str, Any]:
    """Chạy C2/C3 bằng provider không egress, retry một lần rồi fallback C1."""
    request = _validate_request(text, language, tlp, config)
    provider_name = _validate_provider(provider)
    errors: list[str] = []
    for attempt in (1, 2):
        try:
            response = provider.generate(request)
        except Exception:
            errors.append("provider_error")
            continue
        try:
            payload, model_id = _consume_response(response)
        except _RetryableError as exc:
            errors.append(exc.code)
            continue
        return _model_result(request, provider_name, payload, model_id, attempt)
    return _fallback_result(request, provider_name, errors)


class _RetryableError(AdapterError):
    pass


def _validate_request(text: str, language: str, tlp: object, config: str) -> ProviderRequest:
    if (
        not isinstance(text, str)
        or not text
        or not isinstance(language, str)
        or language not in {"vi", "en"}
        or not isinstance(config, str)
        or config not in {"C2", "C3"}
    ):
        raise AdapterError("invalid_input")
    canonical_tlp = _canonical_tlp(tlp)
    return ProviderRequest(text=text, language=language, tlp=canonical_tlp, config=config)  # type: ignore[arg-type]


def _canonical_tlp(tlp: object) -> str:
    if not isinstance(tlp, str):
        raise AdapterError("invalid_tlp")
    label = tlp.strip().upper()
    if not label.startswith("TLP:"):
        label = f"TLP:{label}"
    if label not in TLP_LABELS:
        raise AdapterError("invalid_tlp")
    return label


def _validate_provider(provider: LLMProvider) -> str:
    name = provider.name
    valid_name = isinstance(name, str) and 0 < len(name.encode("utf-8")) <= MAX_METADATA_LENGTH
    safe_destination = provider.destination == "fake_offline" and isinstance(provider.destination, str)
    safe_egress = provider.egress is False
    if not valid_name or not safe_destination or not safe_egress:
        raise AdapterError("egress_not_configured")
    return name


def _consume_response(response: object) -> tuple[dict[str, list[dict[str, str]]], str]:
    if not isinstance(response, ProviderResponse) or not isinstance(response.status, str):
        raise _RetryableError("invalid_response")
    if response.status == "refusal":
        raise AdapterError("provider_refusal")
    if response.status == "incomplete":
        raise AdapterError("provider_incomplete")
    if response.status == "error":
        return _handle_provider_error(response)
    if response.status != "completed" or response.retryable is not False:
        raise _RetryableError("invalid_response")
    model_id = _bounded_metadata(response.model_id)
    if response.error_code is not None or response.usage not in (None, {}):
        raise _RetryableError("invalid_response")
    try:
        payload = validate_payload(response.payload)
    except AdapterError as exc:
        raise _RetryableError("invalid_response") from exc
    return payload, model_id


def _handle_provider_error(response: ProviderResponse) -> tuple[dict[str, list[dict[str, str]]], str]:
    _bounded_metadata(response.error_code)
    if response.payload is not None or response.model_id not in (None, "") or response.usage is not None:
        raise _RetryableError("invalid_response")
    if response.retryable is True:
        raise _RetryableError("provider_error")
    if response.retryable is not False:
        raise _RetryableError("invalid_response")
    raise AdapterError("provider_error")


def _bounded_metadata(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_METADATA_LENGTH:
        raise _RetryableError("invalid_response")
    return value


def _model_result(
    request: ProviderRequest,
    provider_name: str,
    payload: dict[str, list[dict[str, str]]],
    model_id: str,
    attempts: int,
) -> dict[str, Any]:
    result = _base_result(request, provider_name, model_id, attempts, "model_completed", [])
    result["model_items_used"] = True
    result["unverified_semantic_items"] = _semantic_items(payload)
    if request.config == "C2":
        result["raw_iocs"] = payload["iocs"]
        result["operational_draft_eligible"] = False
    else:
        result["iocs"] = _grounded_iocs(request.text, payload["iocs"])
        result["operational_draft_eligible"] = True
    return result


def _fallback_result(request: ProviderRequest, provider_name: str, errors: list[str]) -> dict[str, Any]:
    result = _base_result(request, provider_name, "unavailable", 2, "regex_fallback", errors)
    result["model_items_used"] = False
    result["unverified_semantic_items"] = []
    regex_items = _regex_items(request.text)
    if request.config == "C2":
        result["raw_iocs"] = regex_items
        result["operational_draft_eligible"] = False
    else:
        result["iocs"] = _grounded_iocs(request.text, regex_items, include_regex=False)
        result["operational_draft_eligible"] = True
    return result


def _base_result(
    request: ProviderRequest,
    provider_name: str,
    model_id: str,
    attempts: int,
    mode: str,
    errors: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "config": request.config,
        "purpose": "evaluation-only" if request.config == "C2" else "grounded-candidate",
        "source": {"sha256": hashlib.sha256(request.text.encode("utf-8")).hexdigest()},
        "language": request.language,
        "tlp": request.tlp,
        "provider": {
            "name": provider_name,
            "model_id": model_id,
            "destination": "fake_offline",
            "egress": False,
        },
        "prompt_version": request.prompt_version,
        "attempts": attempts,
        "result_mode": mode,
        "mock_only": True,
        "warnings": [],
        "error_codes": list(errors),
    }


def _grounded_iocs(text: str, model_items: list[dict[str, str]], *, include_regex: bool = True) -> list[dict]:
    raw_items = list(model_items)
    if include_regex:
        raw_items.extend(_regex_items(text))
    return [_serialize_item(item) for item in ground_iocs(raw_items, text)]


def _regex_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for ioc in extract_iocs(text):
        quote = quote_for_ioc(text, ioc)
        evidence = quote[0] if quote is not None else ""
        items.append({"type": ioc.type.value, "value": ioc.value, "role": "attacker", "evidence": evidence})
    return items


def _serialize_item(item: Item) -> dict[str, Any]:
    span = item.extra.get("span")
    return {
        "kind": item.kind,
        "type": item.extra.get("type"),
        "value": item.value,
        "evidence": item.evidence,
        "span": list(span) if span is not None else None,
        "keep": item.keep,
        "status": item.status,
        "warning": item.note or None,
    }


def _semantic_items(payload: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key, kind, value_key in (
        ("techniques", "technique", "id"),
        ("malware", "malware", "name"),
        ("actors", "actor", "name"),
    ):
        for item in payload[key]:
            result.append(
                {
                    "kind": kind,
                    "value": item[value_key],
                    "evidence": item["evidence"],
                    "operational_draft_eligible": False,
                }
            )
    return result


def _check_serialized_size(payload: dict) -> None:
    try:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AdapterError("invalid_response") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise AdapterError("invalid_response")


def _validate_ioc(item: object) -> dict[str, str]:
    value = _validate_exact_strings(item, {"type", "value", "role", "evidence"})
    if value["type"] not in IOC_TYPES or value["role"] not in ROLES:
        raise AdapterError("invalid_response")
    return value


def _validate_technique(item: object) -> dict[str, str]:
    value = _validate_exact_strings(item, {"id", "evidence"})
    if not TECHNIQUE_ID.fullmatch(value["id"]):
        raise AdapterError("invalid_response")
    return value


def _validate_named(item: object, name_key: str) -> dict[str, str]:
    return _validate_exact_strings(item, {name_key, "evidence"})


def _validate_exact_strings(item: object, keys: set[str]) -> dict[str, str]:
    if not isinstance(item, dict) or set(item) != keys:
        raise AdapterError("invalid_response")
    result: dict[str, str] = {}
    for key in keys:
        value = item[key]
        if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_FIELD_BYTES:
            raise AdapterError("invalid_response")
        result[key] = value
    return result
