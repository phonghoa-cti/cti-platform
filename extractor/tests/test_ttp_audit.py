from __future__ import annotations

import copy
import hashlib
import socket
import sqlite3
from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from phonghoa_extractor.attack_catalog import (
    AttackCatalog,
    SnapshotPin,
    TechniqueRecord,
)
from phonghoa_extractor.llm_adapter import (
    ProviderResponse,
    ScriptedProvider,
    run_c4_extraction,
    run_extraction,
)
from phonghoa_extractor.ttp_audit import TechniqueAudit, TtpAuditError, audit_techniques

SOURCE = "😀 First quote for T1000.001.\r\nMalware Sample and Actor Example."
SOURCE_HASH = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()


def _catalog() -> AttackCatalog:
    pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-audit-1",
        sha256="a" * 64,
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    records = {
        "T1000": TechniqueRecord(
            stix_id="attack-pattern--11111111-1111-4111-8111-111111111111",
            external_id="T1000",
            name="Active",
            modified="2026-11-11T00:00:00Z",
            revoked=False,
            deprecated=False,
            is_subtechnique=False,
            parent_external_ids=(),
        ),
        "T1000.001": TechniqueRecord(
            stix_id="attack-pattern--22222222-2222-4222-8222-222222222222",
            external_id="T1000.001",
            name="Active child",
            modified="2026-11-11T00:00:00Z",
            revoked=False,
            deprecated=False,
            is_subtechnique=True,
            parent_external_ids=("T1000",),
        ),
        "T2000": TechniqueRecord(
            stix_id="attack-pattern--33333333-3333-4333-8333-333333333333",
            external_id="T2000",
            name="Inactive",
            modified="2026-11-11T00:00:00Z",
            revoked=True,
            deprecated=False,
            is_subtechnique=False,
            parent_external_ids=(),
        ),
    }
    return AttackCatalog(pin=pin, records_by_external_id=MappingProxyType(records))


def _item(
    kind: str = "technique",
    value: str = "T1000.001",
    evidence: str = "First quote for T1000.001.",
) -> dict[str, object]:
    return {
        "kind": kind,
        "value": value,
        "evidence": evidence,
        "operational_draft_eligible": False,
    }


def _result(
    source: str = SOURCE,
    *,
    config: str = "C3",
    mode: str = "model_completed",
    items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "config": config,
        "mock_only": True,
        "source": {"sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()},
        "provider": {"destination": "fake_offline", "egress": False, "name": "ignored"},
        "result_mode": mode,
        "model_items_used": mode == "model_completed",
        "unverified_semantic_items": [_item()] if items is None else items,
        "operational_draft_eligible": config == "C3",
    }


def _assert_error(code: str, action, *, marker: str = "") -> None:
    with pytest.raises(TtpAuditError) as caught:
        action()
    assert caught.value.code == code
    assert str(caught.value) == code
    assert repr(caught.value) == code
    if marker:
        assert marker not in str(caught.value)
        assert marker not in repr(caught.value)


@pytest.mark.parametrize("config", ["C2", "C3"])
def test_public_adapter_path_audits_only_techniques_without_another_provider_call(config: str) -> None:
    payload = {
        "iocs": [],
        "techniques": [{"id": "T1000.001", "evidence": "First quote for T1000.001."}],
        "malware": [{"name": "Sample", "evidence": "Malware Sample"}],
        "actors": [{"name": "Example", "evidence": "Actor Example"}],
    }
    provider = ScriptedProvider(
        [ProviderResponse(status="completed", payload=payload, model_id="scripted-v1")],
        name="scripted",
        destination="fake_offline",
        egress=False,
    )
    adapter_result = run_extraction(
        text=SOURCE,
        language="en",
        tlp="TLP:AMBER",
        config=config,
        provider=provider,
    )

    audits = audit_techniques(
        adapter_result=adapter_result,
        source_text=SOURCE,
        catalog=_catalog(),
    )

    assert provider.calls == 1
    assert len(audits) == 1
    assert isinstance(audits[0], TechniqueAudit)
    assert audits[0].item_index == 0
    assert audits[0].value == "T1000.001"
    assert audits[0].source_sha256 == SOURCE_HASH
    assert audits[0].config == config
    assert audits[0].quote_status == "matched"
    assert audits[0].catalog_status == "active"
    assert audits[0].pin_kind == "synthetic"
    assert audits[0].snapshot_version == "synthetic-audit-1"
    assert audits[0].snapshot_sha256 == "a" * 64
    assert audits[0].semantic_status == "unverified"
    assert audits[0].operational_draft_eligible is False


@pytest.mark.parametrize(
    ("mode", "items"),
    [
        ("model_completed", [_item()]),
        ("model_completed", []),
        ("regex_fallback", []),
    ],
)
def test_source_hash_mismatch_precedes_output_and_fallback(mode: str, items: list[dict]) -> None:
    result = _result("Source A same quote", mode=mode, items=items)
    _assert_error(
        "source_mismatch",
        lambda: audit_techniques(
            adapter_result=result,
            source_text="Source B same quote",
            catalog=_catalog(),
        ),
    )


@pytest.mark.parametrize("source", ["😀x\r\ny", "é", "e\u0301"])
def test_source_hash_uses_exact_utf8_and_span_uses_unicode_code_points(source: str) -> None:
    evidence = source[1:] if source.startswith("😀") else source
    audits = audit_techniques(
        adapter_result=_result(source, items=[_item(evidence=evidence)]),
        source_text=source,
        catalog=_catalog(),
    )
    start = source.find(evidence)
    assert audits[0].evidence_span == (start, start + len(evidence))
    assert audits[0].source_sha256 == hashlib.sha256(source.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(schema_version=1),
        lambda value: value.update(schema_version="2.0"),
        lambda value: value.update(config=True),
        lambda value: value.update(config="C5"),
        lambda value: value.update(mock_only=1),
        lambda value: value.pop("source"),
        lambda value: value.update(source={"sha256": "a" * 63}),
        lambda value: value.update(source={"sha256": "A" * 64}),
        lambda value: value.update(source={"sha256": "a" * 64, "extra": False}),
        lambda value: value.update(source=[]),
        lambda value: value.update(provider={"destination": "cloud", "egress": False}),
        lambda value: value.update(provider={"destination": "fake_offline", "egress": 0}),
        lambda value: value.update(result_mode="model_completed", model_items_used=False),
        lambda value: value.update(result_mode="regex_fallback", model_items_used=True),
        lambda value: value.update(result_mode=[]),
        lambda value: value.update(unverified_semantic_items={}),
    ],
)
def test_projection_rejects_wrong_shapes_and_exact_values(mutate) -> None:
    marker = "RAW_PROJECTION_MARKER"
    result = _result(items=[])
    result["ignored"] = marker
    mutate(result)
    _assert_error(
        "invalid_adapter_result",
        lambda: audit_techniques(
            adapter_result=result,
            source_text=SOURCE,
            catalog=_catalog(),
        ),
        marker=marker,
    )


@pytest.mark.parametrize(
    "item",
    [
        [],
        {"kind": "technique", "value": "T1000", "evidence": "x"},
        {**_item(), "extra": "x"},
        {**_item(), "kind": "campaign"},
        {**_item(), "value": 1000},
        {**_item(), "evidence": None},
        {**_item(), "operational_draft_eligible": 0},
        _item(kind="malware", evidence="\ud800"),
        _item(kind="actor", value="\ud800"),
    ],
)
def test_every_mixed_item_is_structurally_validated_before_filtering(item: object) -> None:
    _assert_error(
        "invalid_adapter_result",
        lambda: audit_techniques(
            adapter_result=_result(items=[item]),  # type: ignore[list-item]
            source_text=SOURCE,
            catalog=_catalog(),
        ),
    )


@pytest.mark.parametrize(
    "items",
    [
        [_item(kind="actor", value="x", evidence="x")] * 501,
        [_item(kind="malware", value="x" * 8193, evidence="x")],
        [_item(kind="actor", value="x", evidence="é" * 4097)],
    ],
)
def test_bounds_apply_before_filtering_mixed_items(items: list[dict[str, object]]) -> None:
    _assert_error(
        "input_too_large",
        lambda: audit_techniques(
            adapter_result=_result(items=items),
            source_text=SOURCE,
            catalog=_catalog(),
        ),
    )


def test_source_contract_rejects_type_empty_encoding_and_size_before_hashing() -> None:
    for source in (None, "", "\ud800"):
        _assert_error(
            "invalid_source_text",
            lambda source=source: audit_techniques(
                adapter_result=_result(),
                source_text=source,
                catalog=_catalog(),  # type: ignore[arg-type]
            ),
        )
    _assert_error(
        "input_too_large",
        lambda: audit_techniques(
            adapter_result=_result(), source_text="x" * (1024 * 1024 + 1), catalog=_catalog()
        ),
    )


@pytest.mark.parametrize(
    ("value", "evidence", "quote_status", "catalog_status", "reason"),
    [
        ("T1000", "", "missing", "active", "missing_evidence"),
        ("T1000", "absent", "not_found", "active", "evidence_not_in_source"),
        ("", "First quote for T1000.001.", "matched", "not_checked", "invalid_technique_id"),
        ("t1000", "First quote for T1000.001.", "matched", "not_checked", "invalid_technique_id"),
        (" T1000", "First quote for T1000.001.", "matched", "not_checked", "invalid_technique_id"),
        ("T１０００", "First quote for T1000.001.", "matched", "not_checked", "invalid_technique_id"),
        ("T9999", "First quote for T1000.001.", "matched", "unknown", "unknown_technique_id"),
        ("T2000", "First quote for T1000.001.", "matched", "inactive", "catalog_inactive"),
        ("T1000.001", "First quote for T1000.001.", "matched", "active", "catalog_active_and_quote_matched"),
    ],
)
def test_content_results_keep_quote_and_catalog_status_independent(
    value: str,
    evidence: str,
    quote_status: str,
    catalog_status: str,
    reason: str,
) -> None:
    audit = audit_techniques(
        adapter_result=_result(items=[_item(value=value, evidence=evidence)]),
        source_text=SOURCE,
        catalog=_catalog(),
    )[0]
    assert (audit.quote_status, audit.catalog_status, audit.reason_code) == (
        quote_status,
        catalog_status,
        reason,
    )


@pytest.mark.parametrize(
    ("source", "evidence", "status", "span", "reason"),
    [
        ("aaaa", "aaa", "ambiguous", None, "evidence_ambiguous"),
        ("one\r\none\r\n", "one\r\n", "ambiguous", None, "evidence_ambiguous"),
        ("é", "e\u0301", "not_found", None, "evidence_not_in_source"),
        ("prefix quote suffix", "quote", "matched", (7, 12), "catalog_active_and_quote_matched"),
    ],
)
def test_quote_matching_is_literal_and_counts_overlapping_occurrences(
    source: str,
    evidence: str,
    status: str,
    span: tuple[int, int] | None,
    reason: str,
) -> None:
    audit = audit_techniques(
        adapter_result=_result(source, items=[_item(value="T1000", evidence=evidence)]),
        source_text=source,
        catalog=_catalog(),
    )[0]
    assert (audit.quote_status, audit.evidence_span, audit.reason_code) == (status, span, reason)


def test_duplicates_keep_original_indexes_and_inputs_outputs_are_immutable() -> None:
    catalog = _catalog()
    result = _result(
        items=[
            _item(kind="malware", value="Sample", evidence="Malware Sample"),
            _item(),
            _item(kind="actor", value="Example", evidence="Actor Example"),
            _item(),
        ]
    )
    before_result = copy.deepcopy(result)
    before_records = dict(catalog.records_by_external_id)

    first = audit_techniques(adapter_result=result, source_text=SOURCE, catalog=catalog)
    second = audit_techniques(adapter_result=result, source_text=SOURCE, catalog=catalog)

    assert first == second
    assert [item.item_index for item in first] == [1, 3]
    assert isinstance(first, tuple)
    assert result == before_result
    assert dict(catalog.records_by_external_id) == before_records
    with pytest.raises(FrozenInstanceError):
        first[0].value = "T9999"
    with pytest.raises(TypeError):
        first[0].evidence_span[0] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        first[0].snapshot_sha256[0] = "b"  # type: ignore[index]


def test_fault_injection_data_causes_no_socket_sqlite_file_or_provider_side_effect(
    monkeypatch,
) -> None:
    marker = "FAULT_INJECTION_MARKER"
    result = _result(items=[_item(value="T1000", evidence=marker)])

    def forbidden(*_args, **_kwargs):
        raise AssertionError("side effect attempted")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr("builtins.open", forbidden)

    audit = audit_techniques(adapter_result=result, source_text=SOURCE, catalog=_catalog())[0]
    assert audit.quote_status == "not_found"
    assert audit.reason_code == "evidence_not_in_source"


def test_regex_fallback_rejects_semantic_items_and_catalog_type_is_exact() -> None:
    _assert_error(
        "invalid_adapter_result",
        lambda: audit_techniques(
            adapter_result=_result(mode="regex_fallback", items=[_item()]),
            source_text=SOURCE,
            catalog=_catalog(),
        ),
    )
    _assert_error(
        "invalid_catalog",
        lambda: audit_techniques(
            adapter_result=_result(),
            source_text=SOURCE,
            catalog=object(),  # type: ignore[arg-type]
        ),
    )


def test_public_c4_composition_audits_report_not_knowledge_and_does_not_generate_again() -> None:
    report = "😀 Report contains T1000.001 and evil[.]example."
    payload = {
        "iocs": [],
        "techniques": [
            {"id": "T1000.001", "evidence": "Report contains T1000.001"},
            {"id": "T1000", "evidence": "Active child"},
        ],
        "malware": [],
        "actors": [],
    }
    provider = ScriptedProvider(
        [ProviderResponse(status="completed", payload=payload, model_id="scripted-v1")],
        name="scripted",
        destination="fake_offline",
        egress=False,
    )

    result = run_c4_extraction(
        text=report,
        language="en",
        tlp="TLP:GREEN",
        provider=provider,
        catalog=_catalog(),
        attack_query="Active child",
        top_k=1,
        context_budget_bytes=4096,
    )
    audits = audit_techniques(adapter_result=result, source_text=report, catalog=_catalog())

    assert provider.calls == 1
    assert [audit.config for audit in audits] == ["C4", "C4"]
    assert audits[0].quote_status == "matched"
    assert audits[0].evidence_span == (2, 27)
    assert audits[1].quote_status == "not_found"
    assert audits[1].evidence_span is None
    assert all(audit.operational_draft_eligible is False for audit in audits)


def test_c4_audit_acceptance_does_not_weaken_exact_semantic_item_keys() -> None:
    result = _result(config="C4")
    result["unverified_semantic_items"] = [{**_item(), "semantic_status": "unverified"}]
    _assert_error(
        "invalid_adapter_result",
        lambda: audit_techniques(adapter_result=result, source_text=SOURCE, catalog=_catalog()),
    )
