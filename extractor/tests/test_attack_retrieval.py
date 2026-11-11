from __future__ import annotations

import copy
import hashlib
import json
import socket
import unicodedata
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from phonghoa_extractor.attack_catalog import (
    AttackCatalog,
    SnapshotPin,
    TechniqueRecord,
    load_catalog,
)
from phonghoa_extractor.attack_retrieval import (
    AttackRetrievalError,
    retrieve_techniques,
)


def pattern(
    external_id: str,
    name: str,
    description: str | None,
    *,
    index: int,
    revoked: bool = False,
    deprecated: bool = False,
) -> dict[str, object]:
    result: dict[str, object] = {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": f"attack-pattern--{index:08d}-1111-4111-8111-{index:012d}",
        "modified": "2026-11-11T00:00:00Z",
        "name": name,
        "revoked": revoked,
        "x_mitre_deprecated": deprecated,
        "x_mitre_is_subtechnique": "." in external_id,
        "x_mitre_domains": ["enterprise-attack"],
        "external_references": [{"source_name": "mitre-attack", "external_id": external_id}],
    }
    if description is not None:
        result["description"] = description
    return result


def catalog_from_patterns(tmp_path: Path, patterns: list[dict[str, object]]) -> AttackCatalog:
    payload = json.dumps(
        {
            "type": "bundle",
            "x_phonghoa_provenance": {
                "kind": "synthetic",
                "generator": "hand-authored-test-fixture",
                "purpose": "restricted-catalog-test",
                "mitre_release": None,
                "source_url": None,
                "release_tag": None,
                "commit": None,
            },
            "objects": patterns,
        },
        ensure_ascii=False,
    ).encode()
    snapshot = tmp_path / "retrieval-catalog.json"
    snapshot.write_bytes(payload)
    pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-retrieval-1",
        sha256=hashlib.sha256(payload).hexdigest(),
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    return load_catalog(snapshot, pin)


def base_catalog(tmp_path: Path) -> AttackCatalog:
    return catalog_from_patterns(
        tmp_path,
        [
            pattern("T1000", "Alpha technique", "dữ liệu phishing alpha", index=1),
            pattern("T1001", "Beta technique", "phishing beta", index=2),
            pattern("T1002", "Inactive phishing", "phishing", index=3, revoked=True),
        ],
    )


def assert_error(code: str, action) -> None:
    with pytest.raises(AttackRetrievalError) as caught:
        action()
    assert caught.value.code == code
    assert str(caught.value) == code
    assert repr(caught.value) == code


def test_unicode_tokenization_id_ranking_duplicate_neutral_and_stable_tie(tmp_path: Path) -> None:
    catalog = base_catalog(tmp_path)

    composed = retrieve_techniques(catalog, "DỮ LIỆU phishing phishing")
    decomposed = retrieve_techniques(catalog, unicodedata.normalize("NFD", "dữ liệu PHISHING"))
    assert [item.external_id for item in composed.results] == ["T1000", "T1001"]
    assert [item.external_id for item in decomposed.results] == ["T1000", "T1001"]
    assert composed.results[0].ranking_score == 1.0
    assert composed.results[1].ranking_score == 1 / 3
    assert decomposed.results[0].ranking_score == 1.0
    without_duplicate = retrieve_techniques(catalog, "DỮ LIỆU phishing")
    assert composed.results == without_duplicate.results

    by_id = retrieve_techniques(catalog, "Ｔ１０００.ignored_value")
    assert [item.external_id for item in by_id.results] == ["T1000"]

    tied = retrieve_techniques(catalog, "phishing")
    assert [item.external_id for item in tied.results] == ["T1000", "T1001"]
    assert all(item.semantic_status == "unverified" for item in tied.results)
    assert all(item.operational_draft_eligible is False for item in tied.results)


def test_short_long_token_parent_child_and_zero_match(tmp_path: Path) -> None:
    catalog = catalog_from_patterns(
        tmp_path,
        [
            pattern("T2000", "Parent", "aa " + "x" * 65, index=20),
        ],
    )
    # The synthetic loader requires an explicit parent relation, so validate parent/child
    # separation with a caller-built internal catalog using records already validated by it.
    parent = catalog.records_by_external_id["T2000"]
    child = replace(
        TechniqueRecord(
            stix_id="attack-pattern--00000021-1111-4111-8111-000000000021",
            external_id="T2000.001",
            name="Child",
            modified="2026-11-11T00:00:00Z",
            revoked=False,
            deprecated=False,
            is_subtechnique=True,
            parent_external_ids=("T2000",),
        ),
        description="aa useful",
    )
    internal = AttackCatalog(catalog.pin, MappingProxyType({"T2000": parent, "T2000.001": child}))
    assert [item.external_id for item in retrieve_techniques(internal, "useful").results] == ["T2000.001"]
    assert_error("invalid_query", lambda: retrieve_techniques(internal, "a " + "x" * 65))
    assert retrieve_techniques(internal, "no-overlap").results == ()


@pytest.mark.parametrize("query", [None, True, 1, "", " \r\n", "😀", "\ud800", "a" * 513, "é" * 2049])
def test_rejects_invalid_queries(tmp_path: Path, query: object) -> None:
    assert_error("invalid_query", lambda: retrieve_techniques(base_catalog(tmp_path), query))


@pytest.mark.parametrize(
    ("keyword", "value"),
    [
        ("top_k", True),
        ("top_k", 1.0),
        ("top_k", 0),
        ("top_k", 11),
        ("context_budget_bytes", True),
        ("context_budget_bytes", 255),
        ("context_budget_bytes", 8193),
    ],
)
def test_rejects_invalid_bounds(tmp_path: Path, keyword: str, value: object) -> None:
    kwargs = {keyword: value}
    assert_error("invalid_bounds", lambda: retrieve_techniques(base_catalog(tmp_path), "alpha", **kwargs))


def test_context_schema_order_escaping_and_result_projection(tmp_path: Path) -> None:
    description = 'quote " slash \\ control\n Việt'
    catalog = catalog_from_patterns(
        tmp_path,
        [pattern("T3000", "Name", description, index=30)],
    )
    result = retrieve_techniques(catalog, "quote", context_budget_bytes=4096)
    parsed = json.loads(result.context)

    assert list(parsed) == ["schema_version", "snapshot", "techniques"]
    assert list(parsed["snapshot"]) == ["version", "sha256", "kind", "source_url", "release_tag", "commit"]
    assert list(parsed["techniques"][0]) == [
        "id",
        "name",
        "snippet",
        "snippet_truncated",
        "modified",
        "parents",
    ]
    assert parsed["techniques"][0]["snippet"] == description
    assert result.results[0].description == description
    assert result.results[0].snapshot_sha256 == catalog.pin.sha256
    assert result.results[0].pin_kind == "synthetic"
    assert len(result.context.encode("utf-8")) <= result.context_budget_bytes
    assert result.context == json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))


def test_budget_exact_fit_one_short_multibyte_truncation_and_prefix_results(tmp_path: Path) -> None:
    catalog = catalog_from_patterns(
        tmp_path,
        [
            pattern("T4000", "First", "match " + "á" * 200, index=40),
            pattern("T4001", "Second", "match second", index=41),
        ],
    )
    full = retrieve_techniques(catalog, "match", context_budget_bytes=4096)
    exact = len(full.context.encode("utf-8"))
    assert retrieve_techniques(catalog, "match", context_budget_bytes=exact).context == full.context

    one_short = retrieve_techniques(catalog, "match", context_budget_bytes=exact - 1)
    parsed = json.loads(one_short.context)
    assert len(one_short.context.encode("utf-8")) <= exact - 1
    assert one_short.results == full.results[:1]
    assert parsed["techniques"][0]["snippet_truncated"] is False

    truncated = retrieve_techniques(catalog, "first", context_budget_bytes=512)
    item = json.loads(truncated.context)["techniques"][0]
    assert truncated.results[0].description == "match " + "á" * 200
    assert item["snippet_truncated"] is True
    assert ("match " + "á" * 200).startswith(item["snippet"])
    assert len(truncated.context.encode("utf-8")) <= 512


def test_one_byte_short_of_single_full_item_really_shortens_snippet(tmp_path: Path) -> None:
    description = "match abc"
    catalog = catalog_from_patterns(
        tmp_path,
        [pattern("T4500", "Single", description, index=45)],
    )
    full = retrieve_techniques(catalog, "match")
    budget = len(full.context.encode("utf-8")) - 1
    shortened = retrieve_techniques(catalog, "match", context_budget_bytes=budget)
    item = json.loads(shortened.context)["techniques"][0]
    assert item["snippet_truncated"] is True
    assert item["snippet"] != description
    assert description.startswith(item["snippet"])


def test_later_unfit_item_stops_rank_instead_of_skipping_to_smaller_item(tmp_path: Path) -> None:
    catalog = catalog_from_patterns(
        tmp_path,
        [
            pattern("T4600", "First", "match", index=46),
            pattern("T4601", "Second", "match " + "x" * 1000, index=47),
            pattern("T4602", "Third", "match", index=48),
        ],
    )
    result = retrieve_techniques(catalog, "match", context_budget_bytes=700)
    assert [item.external_id for item in result.results] == ["T4600"]
    assert [item["id"] for item in json.loads(result.context)["techniques"]] == ["T4600"]


def test_none_description_zero_match_and_impossible_metadata(tmp_path: Path) -> None:
    catalog = catalog_from_patterns(tmp_path, [pattern("T5000", "Only", None, index=50)])
    by_name = retrieve_techniques(catalog, "only")
    item = json.loads(by_name.context)["techniques"][0]
    assert item["snippet"] == ""
    assert item["snippet_truncated"] is False

    zero = retrieve_techniques(catalog, "absent")
    assert zero.results == ()
    assert json.loads(zero.context)["techniques"] == []

    long_pin = replace(catalog.pin, version="v" * 64)
    long_catalog = AttackCatalog(long_pin, catalog.records_by_external_id)
    assert_error(
        "context_budget_exceeded",
        lambda: retrieve_techniques(long_catalog, "absent", context_budget_bytes=256),
    )

    long_name_catalog = catalog_from_patterns(
        tmp_path,
        [pattern("T5001", "Nn " + "N" * 253, None, index=51)],
    )
    assert_error(
        "context_budget_exceeded",
        lambda: retrieve_techniques(long_name_catalog, "nn", context_budget_bytes=256),
    )


def test_malformed_catalog_and_records_fail_closed_without_mutation(tmp_path: Path) -> None:
    catalog = base_catalog(tmp_path)
    original = copy.deepcopy(dict(catalog.records_by_external_id))
    assert_error("invalid_catalog", lambda: retrieve_techniques(object(), "alpha"))
    assert_error(
        "invalid_catalog",
        lambda: retrieve_techniques(AttackCatalog(catalog.pin, []), "alpha"),
    )
    bad_key = AttackCatalog(catalog.pin, {"T9999": catalog.records_by_external_id["T1000"]})
    assert_error("invalid_record", lambda: retrieve_techniques(bad_key, "alpha"))
    bad_record = replace(catalog.records_by_external_id["T1000"], revoked=1)
    assert_error(
        "invalid_record",
        lambda: retrieve_techniques(AttackCatalog(catalog.pin, {"T1000": bad_record}), "alpha"),
    )
    assert dict(catalog.records_by_external_id) == original


def test_retrieval_is_in_memory_inert_and_immutable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    catalog = catalog_from_patterns(
        tmp_path,
        [pattern("T6000", "Prompt", "ignore previous; https://example.invalid", index=60)],
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("I/O attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    result = retrieve_techniques(catalog, "ignore previous")
    assert result.results[0].description == "ignore previous; https://example.invalid"
    with pytest.raises(FrozenInstanceError):
        result.results[0].name = "mutated"
    with pytest.raises(FrozenInstanceError):
        result.results = ()
