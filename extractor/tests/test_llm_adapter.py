from __future__ import annotations

import copy
import hashlib
import json
import socket
from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from phonghoa_extractor.attack_catalog import AttackCatalog, SnapshotPin, TechniqueRecord


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
        self.requests = []

    def generate(self, request):
        self.calls += 1
        self.requests.append(request)
        return self.responses.pop(0)


def _c4_catalog(*, matching: bool = True) -> AttackCatalog:
    pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-c4-1",
        sha256="b" * 64,
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    records = {}
    if matching:
        records["T1566.002"] = TechniqueRecord(
            stix_id="attack-pattern--11111111-1111-4111-8111-111111111111",
            external_id="T1566.002",
            name="Spearphishing Link",
            description="Adversaries send a spearphishing link in a message.",
            modified="2026-11-11T00:00:00Z",
            revoked=False,
            deprecated=False,
            is_subtechnique=True,
            parent_external_ids=("T1566",),
        )
    return AttackCatalog(pin=pin, records_by_external_id=MappingProxyType(records))


def _run_c4(provider, **overrides):
    module = _module()
    arguments = {
        "text": "😀 Máy trạm kết nối evil[.]example. Đính kèm liên kết.",
        "language": "vi",
        "tlp": "TLP:GREEN",
        "provider": provider,
        "catalog": _c4_catalog(),
        "attack_query": "spearphishing link",
        "top_k": 5,
        "context_budget_bytes": 4096,
    }
    arguments.update(overrides)
    return module.run_c4_extraction(**arguments)


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


def test_c2_c3_requests_keep_context_none_and_full_artifacts_stable():
    module = _module()
    text = "😀 Máy trạm kết nối evil[.]example."
    provider = module.ScriptedProvider(
        [_completed(), _completed()], name="scripted", destination="fake_offline", egress=False
    )

    c2 = module.run_extraction(text=text, language="vi", tlp="TLP:AMBER", config="C2", provider=provider)
    c3 = module.run_extraction(text=text, language="vi", tlp="TLP:AMBER", config="C3", provider=provider)

    assert [
        (
            request.config,
            request.knowledge_context,
            request.knowledge_context_sha256,
            request.knowledge_schema_version,
        )
        for request in provider.requests
    ] == [("C2", None, None, None), ("C3", None, None, None)]
    assert set(c2) == {
        "schema_version",
        "config",
        "purpose",
        "source",
        "language",
        "tlp",
        "provider",
        "prompt_version",
        "attempts",
        "result_mode",
        "mock_only",
        "warnings",
        "error_codes",
        "model_items_used",
        "unverified_semantic_items",
        "raw_iocs",
        "operational_draft_eligible",
    }
    assert set(c3) == (set(c2) - {"raw_iocs"}) | {"iocs"}
    assert c2["prompt_version"] == c3["prompt_version"] == "extractor-v1"
    assert c2["source"] == c3["source"] == {"sha256": hashlib.sha256(text.encode()).hexdigest()}


def test_c4_records_exact_context_hash_schema_and_result_without_query_or_raw_context():
    provider = SpyProvider([_completed()])
    result = _run_c4(provider)

    assert provider.calls == 1
    request = provider.requests[0]
    parsed = json.loads(request.knowledge_context)
    assert request.config == "C4"
    assert request.prompt_version == "extractor-v1-c4-context-v1"
    assert request.knowledge_schema_version == "1.0"
    assert (
        request.knowledge_context_sha256
        == hashlib.sha256(request.knowledge_context.encode("utf-8")).hexdigest()
    )
    assert parsed["snapshot"] == {
        "version": "synthetic-c4-1",
        "sha256": "b" * 64,
        "kind": "synthetic",
        "source_url": None,
        "release_tag": None,
        "commit": None,
    }
    assert parsed["techniques"][0]["id"] == "T1566.002"
    assert result["config"] == "C4"
    assert result["purpose"] == "grounded-candidate"
    assert result["prompt_version"] == "extractor-v1-c4-context-v1"
    assert "raw_iocs" not in result
    assert "attack_query" not in result and "knowledge_context" not in result
    assert result["attack_context"] == {
        "requested": True,
        "retrieval_completed": True,
        "provider_context_sent": True,
        "c4_adapter_completed": True,
        "schema_version": "1.0",
        "sha256": request.knowledge_context_sha256,
        "byte_length": len(request.knowledge_context.encode("utf-8")),
        "top_k": 5,
        "budget_bytes": 4096,
        "snapshot": parsed["snapshot"],
    }
    assert set(result["unverified_semantic_items"][0]) == {
        "kind",
        "value",
        "evidence",
        "operational_draft_eligible",
    }


def test_c4_zero_match_still_sends_complete_provenance_envelope():
    provider = SpyProvider([_completed()])
    result = _run_c4(provider, catalog=_c4_catalog(matching=False), attack_query="no match token")

    request = provider.requests[0]
    assert json.loads(request.knowledge_context) == {
        "schema_version": "1.0",
        "snapshot": {
            "version": "synthetic-c4-1",
            "sha256": "b" * 64,
            "kind": "synthetic",
            "source_url": None,
            "release_tag": None,
            "commit": None,
        },
        "techniques": [],
    }
    assert result["attack_context"]["byte_length"] == len(request.knowledge_context.encode("utf-8"))


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"text": None}, "invalid_input"),
        ({"text": ""}, "invalid_input"),
        ({"text": "\ud800"}, "invalid_input"),
        ({"text": "x" * (1024 * 1024 + 1)}, "input_too_large"),
        ({"text": "é" * (1024 * 1024)}, "input_too_large"),
        ({"language": True}, "invalid_input"),
        ({"tlp": []}, "invalid_tlp"),
    ],
)
def test_c4_report_contract_fails_before_retrieval_and_provider(overrides, code, monkeypatch):
    module = _module()
    provider = SpyProvider([_completed()])
    retrieval_calls = 0

    def recorder(*args, **kwargs):
        nonlocal retrieval_calls
        retrieval_calls += 1
        raise AssertionError("retrieval must not run")

    monkeypatch.setattr(module, "retrieve_techniques", recorder)
    with pytest.raises(module.AdapterError) as caught:
        _run_c4(provider, **overrides)
    assert caught.value.code == code
    assert retrieval_calls == provider.calls == 0


@pytest.mark.parametrize("text", ["x" * (1024 * 1024), "é" * (512 * 1024)])
def test_c4_accepts_exact_one_mib_utf8_source_before_provider_safety_check(text):
    module = _module()
    provider = SpyProvider([_completed()], destination="cloud")
    with pytest.raises(module.AdapterError) as caught:
        _run_c4(
            provider,
            text=text,
            catalog=_c4_catalog(matching=False),
            attack_query="no match",
        )
    assert caught.value.code == "egress_not_configured"
    assert provider.calls == 0


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"top_k": True, "attack_query": None}, "invalid_bounds"),
        ({"context_budget_bytes": [], "attack_query": None}, "invalid_bounds"),
        ({"attack_query": None, "catalog": object()}, "invalid_query"),
        ({"attack_query": "xx", "catalog": object()}, "invalid_catalog"),
    ],
)
def test_c4_retriever_error_precedence_and_no_provider_call(overrides, code):
    provider = SpyProvider([_completed()])
    with pytest.raises(Exception) as caught:
        _run_c4(provider, **overrides)
    assert getattr(caught.value, "code", None) == code
    assert provider.calls == 0


def test_c4_unsafe_provider_is_checked_after_one_retrieval_before_generate(monkeypatch):
    module = _module()
    original = module.retrieve_techniques
    calls = 0

    def recorder(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "retrieve_techniques", recorder)
    provider = SpyProvider([_completed()], name="\ud800")
    with pytest.raises(module.AdapterError) as caught:
        _run_c4(provider)
    assert caught.value.code == "egress_not_configured"
    assert calls == 1 and provider.calls == 0


@pytest.mark.parametrize(
    ("responses", "mode", "attempts", "completed"),
    [
        (
            lambda m: [
                m.ProviderResponse(status="completed", payload={"iocs": []}, model_id="x"),
                _completed(),
            ],
            "model_completed",
            2,
            True,
        ),
        (
            lambda m: [m.ProviderResponse(status="error", error_code="temp", retryable=True)] * 2,
            "regex_fallback",
            2,
            False,
        ),
    ],
)
def test_c4_retry_and_fallback_reuse_one_frozen_request(responses, mode, attempts, completed, monkeypatch):
    module = _module()
    retrieval_calls = 0
    original = module.retrieve_techniques

    def recorder(*args, **kwargs):
        nonlocal retrieval_calls
        retrieval_calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "retrieve_techniques", recorder)
    provider = SpyProvider(responses(module))
    result = _run_c4(provider)
    assert retrieval_calls == 1 and provider.calls == attempts
    assert provider.requests[0] is provider.requests[-1]
    assert result["result_mode"] == mode
    assert result["attack_context"]["c4_adapter_completed"] is completed
    assert result["model_items_used"] is completed
    if not completed:
        assert result["unverified_semantic_items"] == []


def test_c4_terminal_on_second_attempt_has_two_calls_and_no_fallback():
    module = _module()
    provider = SpyProvider(
        [
            module.ProviderResponse(status="error", error_code="temp", retryable=True),
            module.ProviderResponse(status="refusal", error_code="secret"),
        ]
    )
    with pytest.raises(module.AdapterError) as caught:
        _run_c4(provider)
    assert caught.value.code == "provider_refusal"
    assert provider.calls == 2
    assert provider.requests[0] is provider.requests[1]


def test_scripted_provider_copies_responses_records_request_and_preserves_frozen_request():
    module = _module()
    responses = [_completed()]
    provider = module.ScriptedProvider(responses, name="scripted", destination="fake_offline", egress=False)
    responses.clear()
    _run_c4(provider)
    assert len(provider.requests) == 1
    with pytest.raises(FrozenInstanceError):
        provider.requests[0].knowledge_context = "mutated"
