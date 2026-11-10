from __future__ import annotations

import copy
import socket

import pytest


def _module():
    try:
        from phonghoa_extractor import llm_adapter
    except ImportError:
        pytest.fail("chưa có module llm_adapter", pytrace=False)
    return llm_adapter


def _payload() -> dict:
    return {
        "iocs": [
            {
                "type": "domain",
                "value": "evil.example",
                "role": "attacker",
                "evidence": "😀 Máy trạm kết nối evil[.]example.",
            },
            {
                "type": "domain",
                "value": "ghost.example",
                "role": "attacker",
                "evidence": "Máy trạm kết nối ghost.example.",
            },
        ],
        "techniques": [{"id": "T1566.002", "evidence": "Đính kèm liên kết."}],
        "malware": [{"name": "Mẫu Thử", "evidence": "Tên Mẫu Thử."}],
        "actors": [],
    }


def _completed(payload: dict | None = None, *, model_id: object = "scripted-v1"):
    module = _module()
    return module.ProviderResponse(
        status="completed",
        payload=_payload() if payload is None else payload,
        model_id=model_id,
    )


def _run(
    provider,
    *,
    config="C3",
    language="vi",
    text="😀 Máy trạm kết nối evil[.]example.",
    tlp="TLP:AMBER",
):
    module = _module()
    return module.run_extraction(
        text=text,
        language=language,
        tlp=tlp,
        config=config,
        provider=provider,
    )


def test_valid_schema_accepts_four_exact_lists():
    module = _module()

    assert module.validate_payload({"iocs": [], "techniques": [], "malware": [], "actors": []}) == {
        "iocs": [],
        "techniques": [],
        "malware": [],
        "actors": [],
    }


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: [],
        lambda value: {key: item for key, item in value.items() if key != "actors"},
        lambda value: {**value, "extra": []},
        lambda value: {**value, "iocs": [{**value["iocs"][0], "type": "hostname"}]},
        lambda value: {**value, "iocs": [{**value["iocs"][0], "value": ""}]},
        lambda value: {**value, "iocs": [{**value["iocs"][0], "extra": "no"}]},
        lambda value: {**value, "techniques": [{"id": 1566, "evidence": "x"}]},
        lambda value: {**value, "malware": [{"name": "x", "evidence": None}]},
    ],
)
def test_schema_rejects_wrong_shape_types_enums_and_unknown_fields(mutate):
    module = _module()

    with pytest.raises(module.AdapterError) as exc:
        module.validate_payload(mutate(copy.deepcopy(_payload())))

    assert exc.value.code == "invalid_response"


@pytest.mark.parametrize(
    "payload",
    [
        {**_payload(), "iocs": [_payload()["iocs"][0]] * 501},
        {
            **_payload(),
            "iocs": [{**_payload()["iocs"][0], "evidence": "x" * 8193}],
        },
    ],
)
def test_schema_rejects_item_and_field_limits(payload):
    module = _module()

    with pytest.raises(module.AdapterError) as exc:
        module.validate_payload(payload)

    assert exc.value.code == "invalid_response"


class SpyProvider:
    def __init__(
        self,
        responses,
        *,
        name: object = "scripted",
        destination: object = "fake_offline",
        egress: object = False,
    ):
        self.responses = list(responses)
        self.name = name
        self.destination = destination
        self.egress = egress
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return self.responses.pop(0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("language", []),
        ("language", {}),
        ("language", None),
        ("language", False),
        ("language", 1),
        ("language", "fr"),
        ("config", []),
        ("config", {}),
        ("config", None),
        ("config", False),
        ("config", 1),
        ("config", "C4"),
    ],
)
def test_invalid_language_and_config_are_stable_before_provider(field, value):
    module = _module()
    provider = SpyProvider([_completed()])
    kwargs = {field: value, "text": "SOURCE_SECRET_MARKER"}

    with pytest.raises(module.AdapterError) as exc:
        _run(provider, **kwargs)

    assert exc.value.code == "invalid_input"
    assert "SOURCE_SECRET_MARKER" not in str(exc.value)
    assert provider.calls == 0


@pytest.mark.parametrize(
    ("destination", "egress"),
    [
        ("local", False),
        ("cloud", False),
        ("unknown", False),
        (None, False),
        ("fake_offline", True),
        ("fake_offline", 0),
        ("fake_offline", "false"),
    ],
)
def test_provider_metadata_is_rejected_before_generate(destination, egress):
    module = _module()
    provider = SpyProvider([_completed()], destination=destination, egress=egress)

    with pytest.raises(module.AdapterError) as exc:
        _run(provider)

    assert exc.value.code == "egress_not_configured"
    assert provider.calls == 0


@pytest.mark.parametrize("tlp", ["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"])
def test_fake_offline_accepts_every_valid_tlp_without_egress(tlp):
    provider = SpyProvider([_completed()])

    result = _run(provider, config="C2", tlp=tlp)

    assert result["tlp"] == tlp
    assert result["provider"]["destination"] == "fake_offline"
    assert result["provider"]["egress"] is False
    assert provider.calls == 1


@pytest.mark.parametrize("tlp", [None, 1, "GREENISH", "TLP:WHITE"])
def test_invalid_tlp_is_rejected_before_generate(tlp):
    module = _module()
    provider = SpyProvider([_completed()])

    with pytest.raises(module.AdapterError) as exc:
        _run(provider, tlp=tlp)

    assert exc.value.code == "invalid_tlp"
    assert provider.calls == 0


def test_c2_keeps_raw_hallucination_but_never_marks_operational():
    provider = SpyProvider([_completed()])

    result = _run(provider, config="C2")

    assert [item["value"] for item in result["raw_iocs"]] == ["evil.example", "ghost.example"]
    assert result["purpose"] == "evaluation-only"
    assert result["operational_draft_eligible"] is False
    assert result["warnings"] == []
    assert "iocs" not in result


def test_c3_grounds_unicode_evidence_and_rejects_hallucination():
    provider = SpyProvider([_completed()])

    result = _run(provider, config="C3")
    by_value = {item["value"]: item for item in result["iocs"]}

    assert by_value["evil.example"]["keep"] is True
    assert by_value["evil.example"]["span"] == [0, 34]
    assert by_value["ghost.example"]["keep"] is False
    assert by_value["ghost.example"]["status"] == "bia"
    assert result["operational_draft_eligible"] is True
    assert all(item["operational_draft_eligible"] is False for item in result["unverified_semantic_items"])


def test_no_network_is_needed_for_offline_provider(monkeypatch):
    def blocked_socket(*args, **kwargs):
        raise AssertionError("không được mở socket")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    provider = SpyProvider([_completed()])

    assert _run(provider)["result_mode"] == "model_completed"


def test_invalid_then_valid_response_retries_once():
    provider = SpyProvider([_completed({"iocs": []}), _completed()])

    result = _run(provider)

    assert provider.calls == 2
    assert result["attempts"] == 2
    assert result["result_mode"] == "model_completed"


def test_two_invalid_responses_fall_back_to_regex_without_model_items():
    provider = SpyProvider([_completed({"iocs": []}), _completed({"actors": []})])

    result = _run(provider)

    assert provider.calls == 2
    assert result["result_mode"] == "regex_fallback"
    assert result["model_items_used"] is False
    assert result["attempts"] == 2
    assert [item["value"] for item in result["iocs"]] == ["evil.example"]


def test_retryable_provider_error_then_success_uses_second_response():
    module = _module()
    provider = SpyProvider(
        [
            module.ProviderResponse(status="error", error_code="temporary", retryable=True),
            _completed(),
        ]
    )

    result = _run(provider)

    assert provider.calls == 2
    assert result["result_mode"] == "model_completed"


def test_provider_exception_is_bounded_retried_and_falls_back_without_leak():
    class RaisingProvider(SpyProvider):
        def generate(self, request):
            del request
            self.calls += 1
            raise RuntimeError("RAW_PROVIDER_SECRET_MARKER")

    provider = RaisingProvider([])

    result = _run(provider)

    assert provider.calls == 2
    assert result["result_mode"] == "regex_fallback"
    assert result["error_codes"] == ["provider_error", "provider_error"]
    assert "RAW_PROVIDER_SECRET_MARKER" not in str(result)


@pytest.mark.parametrize(
    ("status", "code"), [("refusal", "provider_refusal"), ("incomplete", "provider_incomplete")]
)
def test_refusal_and_incomplete_are_stable_non_retryable_errors(status, code):
    module = _module()
    provider = SpyProvider([module.ProviderResponse(status=status, error_code="DO_NOT_LEAK")])

    with pytest.raises(module.AdapterError) as exc:
        _run(provider)

    assert exc.value.code == code
    assert "DO_NOT_LEAK" not in str(exc.value)
    assert provider.calls == 1


@pytest.mark.parametrize(
    "response",
    [
        lambda module: module.ProviderResponse(status="completed", payload=_payload(), model_id="x" * 257),
        lambda module: module.ProviderResponse(
            status="error", error_code="SECRET_MARKER_" + "x" * 256, retryable=True
        ),
    ],
)
def test_unbounded_provider_metadata_never_leaks_raw_value(response):
    module = _module()
    provider = SpyProvider([response(module), response(module)])

    result = _run(provider)

    assert result["result_mode"] == "regex_fallback"
    assert "SECRET_MARKER" not in str(result)
