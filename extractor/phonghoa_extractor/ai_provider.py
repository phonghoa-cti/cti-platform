"""F20: giao diện provider LLM dùng chung cho tóm tắt (AI Insights) và hỏi đáp (NLQ).

Mặc định KHÔNG có provider nào: mọi tính năng chạy bằng luật/template ngoại tuyến (offline).
Provider tùy chọn là máy chủ tương thích OpenAI chạy cục bộ (ví dụ Ollama), cấu hình chỉ qua biến môi trường:
- PHONGHOA_AI_BASE_URL: ví dụ http://127.0.0.1:11434/v1
- PHONGHOA_AI_MODEL: tên model, ví dụ qwen2.5:7b
- PHONGHOA_AI_TIMEOUT: số giây chờ (mặc định 30)
Không đọc API key: provider cục bộ không cần, và secret không được nằm trong code.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable, Mapping
from typing import Protocol
from urllib.parse import urlparse

TLP_ORDER = ["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"]
SENSITIVE_TLP = {"TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
MAX_REPLY_BYTES = 256 * 1024

Transport = Callable[[str, bytes, float], bytes]


class AiPolicyError(ValueError):
    """Lỗi chính sách hoặc lỗi provider; thông điệp là mã ngắn, không chứa dữ liệu nhạy cảm."""


class TextProvider(Protocol):
    name: str
    is_local: bool

    def complete(self, prompt: str) -> str: ...


def canonical_tlp(tlp: object) -> str:
    if not isinstance(tlp, str):
        raise AiPolicyError("invalid_tlp")
    label = tlp.strip().upper()
    if not label.startswith("TLP:"):
        label = f"TLP:{label}"
    if label == "TLP:WHITE":  # TLP 1.0 → 2.0
        label = "TLP:CLEAR"
    if label not in TLP_ORDER:
        raise AiPolicyError("invalid_tlp")
    return label


def max_tlp(labels: list[str]) -> str:
    return max((canonical_tlp(x) for x in labels), key=TLP_ORDER.index, default="TLP:CLEAR")


def ensure_tlp_allowed(tlp: object, provider: TextProvider | None) -> str:
    """Chặn gửi dữ liệu TLP:AMBER/RED tới provider không chạy trên máy cục bộ (AGENTS.md mục 5)."""
    label = canonical_tlp(tlp)
    if provider is not None and label in SENSITIVE_TLP and not provider.is_local:
        raise AiPolicyError("tlp_blocked_non_local_provider")
    return label


def _urllib_transport(url: str, body: bytes, timeout: float) -> bytes:
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL do admin cấu hình
        return response.read(MAX_REPLY_BYTES + 1)


class LocalOpenAICompatProvider:
    """Gọi endpoint /chat/completions kiểu OpenAI; is_local chỉ đúng khi host là loopback."""

    name = "local-openai-compatible"

    def __init__(self, base_url: str, model: str, timeout: float = 30.0, transport: Transport | None = None):
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise AiPolicyError("invalid_base_url")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.is_local = parsed.hostname in LOCAL_HOSTS
        self._transport = transport or _urllib_transport

    def complete(self, prompt: str) -> str:
        body = json.dumps(
            {"model": self.model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
        ).encode()
        try:
            raw = self._transport(f"{self.base_url}/chat/completions", body, self.timeout)
        except OSError as exc:
            raise AiPolicyError("provider_unreachable") from exc
        if len(raw) > MAX_REPLY_BYTES:
            raise AiPolicyError("provider_reply_too_large")
        try:
            content = json.loads(raw)["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AiPolicyError("provider_malformed_reply") from exc
        if not isinstance(content, str):
            raise AiPolicyError("provider_malformed_reply")
        return content


def provider_from_env(env: Mapping[str, str]) -> LocalOpenAICompatProvider | None:
    """Trả về None (dùng offline) nếu chưa cấu hình PHONGHOA_AI_BASE_URL."""
    base_url = env.get("PHONGHOA_AI_BASE_URL", "").strip()
    if not base_url:
        return None
    model = env.get("PHONGHOA_AI_MODEL", "").strip()
    if not model:
        raise AiPolicyError("missing_model")
    try:
        timeout = float(env.get("PHONGHOA_AI_TIMEOUT", "30"))
    except ValueError as exc:
        raise AiPolicyError("invalid_timeout") from exc
    if not 0 < timeout <= 300:
        raise AiPolicyError("invalid_timeout")
    return LocalOpenAICompatProvider(base_url, model, timeout)


def parse_json_object(reply: str) -> dict:
    """Chỉ nhận đúng một object JSON (cho phép bọc ```json); mọi thứ khác bị từ chối."""
    text = reply.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise AiPolicyError("llm_invalid_output") from exc
    if not isinstance(payload, dict):
        raise AiPolicyError("llm_invalid_output")
    return payload
