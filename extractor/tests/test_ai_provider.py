import json

import pytest

from phonghoa_extractor.ai_provider import (
    AiPolicyError,
    LocalOpenAICompatProvider,
    ensure_tlp_allowed,
    provider_from_env,
)


def test_no_env_means_offline_default():
    assert provider_from_env({}) is None


def test_env_builds_local_provider():
    env = {"PHONGHOA_AI_BASE_URL": "http://127.0.0.1:11434/v1", "PHONGHOA_AI_MODEL": "qwen2.5:7b"}
    provider = provider_from_env(env)
    assert isinstance(provider, LocalOpenAICompatProvider)
    assert provider.is_local is True
    assert provider.model == "qwen2.5:7b"


def test_env_requires_model():
    with pytest.raises(AiPolicyError):
        provider_from_env({"PHONGHOA_AI_BASE_URL": "http://localhost:11434/v1"})


def test_remote_host_is_marked_non_local():
    provider = LocalOpenAICompatProvider("https://api.example.com/v1", "m")
    assert provider.is_local is False


@pytest.mark.parametrize("tlp", ["TLP:AMBER", "amber", "TLP:AMBER+STRICT", "TLP:RED"])
def test_amber_red_refused_for_non_local(tlp):
    provider = LocalOpenAICompatProvider("https://api.example.com/v1", "m")
    with pytest.raises(AiPolicyError):
        ensure_tlp_allowed(tlp, provider)


def test_amber_allowed_for_local_and_clear_for_remote():
    ensure_tlp_allowed("TLP:RED", LocalOpenAICompatProvider("http://localhost:11434/v1", "m"))
    ensure_tlp_allowed("TLP:CLEAR", LocalOpenAICompatProvider("https://api.example.com/v1", "m"))


def test_unknown_tlp_rejected():
    with pytest.raises(AiPolicyError):
        ensure_tlp_allowed("TLP:PURPLE", None)


def test_complete_uses_injected_transport_without_network():
    seen = {}

    def transport(url, body, timeout):
        seen.update(url=url, body=json.loads(body), timeout=timeout)
        return json.dumps({"choices": [{"message": {"content": "xin chào"}}]}).encode()

    provider = LocalOpenAICompatProvider("http://localhost:11434/v1", "m", transport=transport)
    assert provider.complete("hỏi") == "xin chào"
    assert seen["url"] == "http://localhost:11434/v1/chat/completions"
    assert seen["body"]["model"] == "m"
    assert seen["timeout"] > 0


def test_complete_rejects_malformed_response():
    provider = LocalOpenAICompatProvider("http://localhost:1/v1", "m", transport=lambda u, b, t: b"{}")
    with pytest.raises(AiPolicyError):
        provider.complete("x")
