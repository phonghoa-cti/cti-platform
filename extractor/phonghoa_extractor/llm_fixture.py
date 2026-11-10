"""Parser hẹp cho fixture provider giả lập dùng bởi CLI và evaluator."""

from __future__ import annotations

import json
from pathlib import Path

from phonghoa_extractor.llm_adapter import (
    MAX_RESPONSE_BYTES,
    AdapterError,
    ProviderResponse,
    ScriptedProvider,
)


def load_scripted_provider(path: Path) -> ScriptedProvider:
    """Đọc một fixture UTF-8 có giới hạn và trả provider chưa được gọi."""
    try:
        if path.stat().st_size > MAX_RESPONSE_BYTES:
            raise AdapterError("invalid_fixture")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError("invalid_fixture") from exc
    return scripted_provider_from_value(value)


def scripted_provider_from_value(value: object) -> ScriptedProvider:
    if not isinstance(value, dict) or set(value) != {"provider", "responses"}:
        raise AdapterError("invalid_fixture")
    metadata, responses = value["provider"], value["responses"]
    if not isinstance(metadata, dict) or set(metadata) != {"name", "destination", "egress"}:
        raise AdapterError("invalid_fixture")
    if not isinstance(responses, list) or not responses:
        raise AdapterError("invalid_fixture")
    return ScriptedProvider(
        [_response_from_value(item) for item in responses],
        name=metadata["name"],
        destination=metadata["destination"],
        egress=metadata["egress"],
    )


def _response_from_value(value: object) -> ProviderResponse:
    allowed = {"status", "payload", "model_id", "usage", "retryable", "error_code"}
    if not isinstance(value, dict) or "status" not in value or not set(value) <= allowed:
        raise AdapterError("invalid_fixture")
    return ProviderResponse(
        status=value["status"],
        payload=value.get("payload"),
        model_id=value.get("model_id", ""),
        usage=value.get("usage"),
        retryable=value.get("retryable", False),
        error_code=value.get("error_code"),
    )
