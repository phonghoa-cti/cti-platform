from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from phonghoa_extractor.attack_catalog import (
    AttackCatalogError,
    SnapshotPin,
    load_catalog,
    validate_technique,
)

PARENT_STIX_ID = "attack-pattern--11111111-1111-4111-8111-111111111111"
CHILD_STIX_ID = "attack-pattern--22222222-2222-4222-8222-222222222222"
INACTIVE_STIX_ID = "attack-pattern--33333333-3333-4333-8333-333333333333"
RELATIONSHIP_ID = "relationship--44444444-4444-4444-8444-444444444444"


def pattern(
    stix_id: str,
    external_id: str,
    *,
    name: str = "Synthetic technique",
    modified: str = "2026-11-11T00:00:00.1234567Z",
    revoked: bool = False,
    deprecated: bool = False,
    subtechnique: bool | None = None,
    domains: list[object] | None = None,
) -> dict[str, object]:
    if subtechnique is None:
        subtechnique = "." in external_id
    return {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": stix_id,
        "modified": modified,
        "name": name,
        "revoked": revoked,
        "x_mitre_deprecated": deprecated,
        "x_mitre_is_subtechnique": subtechnique,
        "x_mitre_domains": domains if domains is not None else ["enterprise-attack"],
        "external_references": [{"source_name": "mitre-attack", "external_id": external_id}],
    }


def relationship(
    *,
    relationship_id: str = RELATIONSHIP_ID,
    modified: str = "2026-11-11T00:00:00.1234567Z",
    source_ref: str = CHILD_STIX_ID,
    target_ref: str = PARENT_STIX_ID,
    revoked: bool = False,
    deprecated: bool = False,
    relationship_type: object = "subtechnique-of",
) -> dict[str, object]:
    return {
        "type": "relationship",
        "spec_version": "2.1",
        "id": relationship_id,
        "modified": modified,
        "relationship_type": relationship_type,
        "source_ref": source_ref,
        "target_ref": target_ref,
        "revoked": revoked,
        "x_mitre_deprecated": deprecated,
    }


def provenance() -> dict[str, object]:
    return {
        "kind": "synthetic",
        "generator": "hand-authored-test-fixture",
        "purpose": "restricted-catalog-test",
        "mitre_release": None,
        "source_url": None,
        "release_tag": None,
        "commit": None,
    }


def bundle(objects: list[object]) -> dict[str, object]:
    return {
        "type": "bundle",
        "x_phonghoa_provenance": provenance(),
        "objects": objects,
    }


def valid_objects() -> list[dict[str, object]]:
    return [
        pattern(PARENT_STIX_ID, "T1000", name="Synthetic parent"),
        pattern(CHILD_STIX_ID, "T1000.001", name="Synthetic child"),
        pattern(
            INACTIVE_STIX_ID,
            "T2000",
            name="Synthetic inactive",
            revoked=True,
        ),
        relationship(),
    ]


_DEFAULT = object()


def write_snapshot(
    tmp_path: Path,
    value: object = _DEFAULT,
    *,
    raw: bytes | None = None,
) -> tuple[Path, SnapshotPin]:
    selected = bundle(valid_objects()) if value is _DEFAULT else value
    payload = raw if raw is not None else json.dumps(selected).encode()
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_bytes(payload)
    pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-1",
        sha256=hashlib.sha256(payload).hexdigest(),
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    return snapshot, pin


def assert_error(code: str, action) -> None:
    with pytest.raises(AttackCatalogError) as caught:
        action()
    assert caught.value.code == code
    assert str(caught.value) == code
    assert repr(caught.value) == code


def test_loads_active_inactive_unknown_and_invalid_without_semantic_eligibility(
    tmp_path: Path,
) -> None:
    snapshot, pin = write_snapshot(tmp_path)
    catalog = load_catalog(snapshot, pin)

    active = validate_technique(catalog, "T1000.001")
    inactive = validate_technique(catalog, "T2000")
    unknown = validate_technique(catalog, "T9999")
    invalid = validate_technique(catalog, " T1000")

    assert (active.catalog_status, active.reason_code) == ("active", "catalog_active")
    assert active.parent_external_ids == ("T1000",)
    assert active.semantic_status == "unverified"
    assert active.operational_draft_eligible is False
    assert (inactive.catalog_status, inactive.reason_code) == (
        "inactive",
        "catalog_inactive",
    )
    assert inactive.external_id == "T2000"
    assert (unknown.catalog_status, unknown.reason_code) == (
        "unknown",
        "unknown_technique_id",
    )
    assert unknown.external_id is None
    assert (invalid.normalized_id, invalid.syntax_valid, invalid.catalog_status) == (
        None,
        False,
        "not_checked",
    )
    assert invalid.reason_code == "invalid_technique_id"


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("kind", "official"),
        ("kind", 1),
        ("version", ""),
        ("version", "x\n"),
        ("version", "x" * 65),
        ("version", 1),
        ("sha256", "A" * 64),
        ("sha256", "0" * 63),
        ("sha256", 1),
        ("provenance", "mitre-attack-stix-data"),
        ("source_url", "https://example.invalid"),
        ("release_tag", "v1"),
        ("commit", "deadbeef"),
    ],
)
def test_rejects_invalid_pin_before_file_io(field: str, bad_value: object) -> None:
    values = {
        "kind": "synthetic",
        "version": "synthetic-1",
        "sha256": "0" * 64,
        "source_url": None,
        "release_tag": None,
        "commit": None,
        "provenance": "hand-authored-test-fixture",
    }
    values[field] = bad_value
    pin = SnapshotPin(**values)

    assert_error("invalid_pin", lambda: load_catalog(Path("marker-do-not-open"), pin))


@pytest.mark.parametrize("bad_max", [True, 1.0, "10", 0, 64 * 1024 * 1024 + 1])
def test_rejects_invalid_max_bytes_before_file_io(bad_max: object) -> None:
    pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-1",
        sha256="0" * 64,
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )

    assert_error(
        "invalid_pin",
        lambda: load_catalog(Path("marker-do-not-open"), pin, max_bytes=bad_max),
    )


def test_file_error_codes_do_not_leak_path_or_exception(tmp_path: Path, monkeypatch) -> None:
    missing = tmp_path / "private-marker.json"
    _, pin = write_snapshot(tmp_path)
    assert_error("snapshot_not_found", lambda: load_catalog(missing, pin))

    def denied(*_args, **_kwargs):
        raise OSError("secret-marker")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(AttackCatalogError) as caught:
        load_catalog(missing, pin)
    assert caught.value.code == "snapshot_io_error"
    assert "secret-marker" not in str(caught.value)
    assert "private-marker" not in repr(caught.value)


def test_size_and_hash_are_checked_before_decoding_or_parsing(tmp_path: Path) -> None:
    snapshot, pin = write_snapshot(tmp_path, raw=b"not-json")
    assert_error(
        "snapshot_too_large",
        lambda: load_catalog(snapshot, pin, max_bytes=2),
    )

    wrong_pin = SnapshotPin(
        kind=pin.kind,
        version=pin.version,
        sha256="0" * 64,
        source_url=None,
        release_tag=None,
        commit=None,
        provenance=pin.provenance,
    )
    assert_error("snapshot_hash_mismatch", lambda: load_catalog(snapshot, wrong_pin))


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"\xff", "invalid_utf8"),
        (b'{"type":"bundle","type":"bundle","objects":[]}', "invalid_json"),
        (b'{"type":"bundle","objects":[],"n":NaN}', "invalid_json"),
        (b'{"type":"bundle","objects":[],"n":Infinity}', "invalid_json"),
        (b'{"type":"bundle","objects":[],"n":1e999999}', "invalid_json"),
        (b'{"type":"bundle","objects":[],"n":' + b"9" * 200 + b"}", "invalid_json"),
    ],
)
def test_rejects_unsafe_json_with_safe_error(tmp_path: Path, raw: bytes, code: str) -> None:
    snapshot, pin = write_snapshot(tmp_path, raw=raw)
    assert_error(code, lambda: load_catalog(snapshot, pin))


def test_rejects_excessive_json_nesting_safely(tmp_path: Path) -> None:
    raw = b"[" * 1200 + b"0" + b"]" * 1200
    snapshot, pin = write_snapshot(tmp_path, raw=raw)
    assert_error("invalid_json", lambda: load_catalog(snapshot, pin))


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {"type": "not-bundle", "objects": []},
        {"type": "bundle", "objects": {}},
        {"type": "bundle", "objects": [], "x_phonghoa_provenance": {}},
    ],
)
def test_rejects_invalid_bundle_shapes(tmp_path: Path, value: object) -> None:
    snapshot, pin = write_snapshot(tmp_path, value)
    assert_error("invalid_bundle", lambda: load_catalog(snapshot, pin))


@pytest.mark.parametrize("member", [None, True, 1, [], {}, {"type": 1}])
def test_rejects_invalid_member_shapes(tmp_path: Path, member: object) -> None:
    snapshot, pin = write_snapshot(tmp_path, bundle([member]))
    assert_error("invalid_member", lambda: load_catalog(snapshot, pin))


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("id", "attack-pattern--not-a-uuid"),
        ("spec_version", "2.0"),
        ("name", ""),
        ("name", "x" * 257),
        ("modified", "2026-11-11T00:00:00+00:00"),
        ("modified", "2026-02-30T00:00:00Z"),
        ("modified", "2026-11-11T00:00:60Z"),
        ("revoked", 1),
        ("x_mitre_deprecated", None),
        ("x_mitre_is_subtechnique", "false"),
        ("x_mitre_domains", []),
        ("x_mitre_domains", ["enterprise-attack", 1]),
        ("x_mitre_domains", ["unknown-attack"]),
        ("external_references", []),
    ],
)
def test_rejects_invalid_attack_pattern_fields(tmp_path: Path, field: str, bad_value: object) -> None:
    item = pattern(PARENT_STIX_ID, "T1000")
    item[field] = bad_value
    snapshot, pin = write_snapshot(tmp_path, bundle([item]))
    assert_error("invalid_attack_pattern", lambda: load_catalog(snapshot, pin))


def test_requires_one_valid_mitre_reference_and_matching_subtechnique_flag(
    tmp_path: Path,
) -> None:
    item = pattern(PARENT_STIX_ID, "T1000")
    item["external_references"] = [
        {"source_name": "mitre-attack", "external_id": "T1000"},
        {"source_name": "mitre-attack", "external_id": "T1001"},
    ]
    snapshot, pin = write_snapshot(tmp_path, bundle([item]))
    assert_error("invalid_attack_pattern", lambda: load_catalog(snapshot, pin))

    mismatch = pattern(PARENT_STIX_ID, "T1000.001", subtechnique=False)
    snapshot, pin = write_snapshot(tmp_path, bundle([mismatch]))
    assert_error("invalid_attack_pattern", lambda: load_catalog(snapshot, pin))


def test_accepts_canonical_uuid_syntax_without_imposing_uuid_version(tmp_path: Path) -> None:
    syntactic_uuid = "attack-pattern--aaaaaaaa-aaaa-0aaa-0aaa-aaaaaaaaaaaa"
    snapshot, pin = write_snapshot(tmp_path, bundle([pattern(syntactic_uuid, "T3000")]))
    assert "T3000" in load_catalog(snapshot, pin).records_by_external_id


def test_validates_domains_before_filtering_non_enterprise_patterns(tmp_path: Path) -> None:
    bad = pattern(PARENT_STIX_ID, "T1000", domains=["mobile-attack", 1])
    snapshot, pin = write_snapshot(tmp_path, bundle([bad]))
    assert_error("invalid_attack_pattern", lambda: load_catalog(snapshot, pin))

    mobile = pattern(PARENT_STIX_ID, "T1000", domains=["mobile-attack"])
    snapshot, pin = write_snapshot(tmp_path, bundle([mobile]))
    assert load_catalog(snapshot, pin).records_by_external_id == {}


def test_selects_newest_version_independent_of_order_and_preserves_fraction(
    tmp_path: Path,
) -> None:
    older = pattern(
        PARENT_STIX_ID,
        "T1000",
        name="Older",
        modified="2026-11-11T00:00:00.1234567Z",
    )
    newer = pattern(
        PARENT_STIX_ID,
        "T1000",
        name="Newer",
        modified="2026-11-11T00:00:00.1234568Z",
    )
    for objects in ([older, newer], [newer, older]):
        snapshot, pin = write_snapshot(tmp_path, bundle(objects))
        record = load_catalog(snapshot, pin).records_by_external_id["T1000"]
        assert record.name == "Newer"
        assert record.modified == "2026-11-11T00:00:00.1234568Z"


def test_fractional_timestamp_equivalence_conflicts_when_payload_differs(tmp_path: Path) -> None:
    first = pattern(PARENT_STIX_ID, "T1000", name="First", modified="2026-11-11T00:00:00.1Z")
    second = pattern(PARENT_STIX_ID, "T1000", name="Second", modified="2026-11-11T00:00:00.10Z")
    snapshot, pin = write_snapshot(tmp_path, bundle([first, second]))
    assert_error("duplicate_conflict", lambda: load_catalog(snapshot, pin))


def test_exact_duplicate_ignores_json_key_order(tmp_path: Path) -> None:
    item = pattern(PARENT_STIX_ID, "T1000")
    reordered = dict(reversed(list(item.items())))
    snapshot, pin = write_snapshot(tmp_path, bundle([item, reordered]))
    assert set(load_catalog(snapshot, pin).records_by_external_id) == {"T1000"}


def test_rejects_equal_time_payload_conflict_external_id_collision_and_resurrection(
    tmp_path: Path,
) -> None:
    first = pattern(PARENT_STIX_ID, "T1000", name="First")
    second = pattern(PARENT_STIX_ID, "T1000", name="Second")
    snapshot, pin = write_snapshot(tmp_path, bundle([first, second]))
    assert_error("duplicate_conflict", lambda: load_catalog(snapshot, pin))

    other_stix = pattern(CHILD_STIX_ID, "T1000", subtechnique=False)
    snapshot, pin = write_snapshot(tmp_path, bundle([first, other_stix]))
    assert_error("duplicate_conflict", lambda: load_catalog(snapshot, pin))

    revoked = pattern(
        PARENT_STIX_ID,
        "T1000",
        modified="2026-11-10T00:00:00Z",
        revoked=True,
    )
    revived = pattern(
        PARENT_STIX_ID,
        "T1000",
        modified="2026-11-11T00:00:00Z",
    )
    snapshot, pin = write_snapshot(tmp_path, bundle([revoked, revived]))
    assert_error("duplicate_conflict", lambda: load_catalog(snapshot, pin))


def test_newest_revoked_version_is_inactive(tmp_path: Path) -> None:
    older = pattern(PARENT_STIX_ID, "T1000", modified="2026-11-10T00:00:00Z")
    newer = pattern(
        PARENT_STIX_ID,
        "T1000",
        modified="2026-11-11T00:00:00Z",
        revoked=True,
    )
    snapshot, pin = write_snapshot(tmp_path, bundle([older, newer]))
    result = validate_technique(load_catalog(snapshot, pin), "T1000")
    assert result.catalog_status == "inactive"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda item: item.update(id="relationship--not-a-uuid"),
        lambda item: item.update(spec_version="2.0"),
        lambda item: item.update(modified="2026-11-11"),
        lambda item: item.update(source_ref="attack-pattern--not-a-uuid"),
        lambda item: item.update(target_ref=1),
        lambda item: item.update(revoked=1),
        lambda item: item.update(x_mitre_deprecated=None),
        lambda item: item.update(relationship_type=1),
    ],
)
def test_rejects_invalid_relevant_relationship_fields(tmp_path: Path, mutate) -> None:
    edge = relationship()
    mutate(edge)
    snapshot, pin = write_snapshot(tmp_path, bundle([*valid_objects()[:2], edge]))
    assert_error("invalid_relationship", lambda: load_catalog(snapshot, pin))


def test_ignores_non_relevant_relationship_after_minimum_shape_check(tmp_path: Path) -> None:
    edge = {"type": "relationship", "relationship_type": "uses", "marker": object.__name__}
    snapshot, pin = write_snapshot(tmp_path, bundle([edge]))
    assert load_catalog(snapshot, pin).records_by_external_id == {}


@pytest.mark.parametrize(
    "objects",
    [
        [pattern(CHILD_STIX_ID, "T1000.001")],
        [
            *valid_objects()[:2],
            relationship(target_ref="attack-pattern--99999999-9999-4999-8999-999999999999"),
        ],
        [*valid_objects()[:2], relationship(source_ref=PARENT_STIX_ID, target_ref=CHILD_STIX_ID)],
        [*valid_objects()[:2], relationship(target_ref=CHILD_STIX_ID)],
        [
            pattern(PARENT_STIX_ID, "T1000"),
            pattern(CHILD_STIX_ID, "T2000.001"),
            relationship(),
        ],
        [
            pattern(PARENT_STIX_ID, "T1000", revoked=True),
            pattern(CHILD_STIX_ID, "T1000.001"),
            relationship(),
        ],
    ],
)
def test_rejects_invalid_parent_graphs(tmp_path: Path, objects: list[object]) -> None:
    snapshot, pin = write_snapshot(tmp_path, bundle(objects))
    assert_error("parent_conflict", lambda: load_catalog(snapshot, pin))


def test_inactive_child_may_omit_edge_or_point_to_inactive_parent(tmp_path: Path) -> None:
    child = pattern(CHILD_STIX_ID, "T1000.001", revoked=True)
    snapshot, pin = write_snapshot(tmp_path, bundle([child]))
    catalog = load_catalog(snapshot, pin)
    assert catalog.records_by_external_id["T1000.001"].parent_external_ids == ()

    parent = pattern(PARENT_STIX_ID, "T1000", revoked=True)
    snapshot, pin = write_snapshot(tmp_path, bundle([parent, child, relationship()]))
    catalog = load_catalog(snapshot, pin)
    assert catalog.records_by_external_id["T1000.001"].parent_external_ids == ("T1000",)


def test_revoked_relationship_version_cannot_be_resurrected(tmp_path: Path) -> None:
    revoked = relationship(modified="2026-11-10T00:00:00Z", revoked=True)
    revived = relationship(modified="2026-11-11T00:00:00Z")
    snapshot, pin = write_snapshot(tmp_path, bundle([*valid_objects()[:2], revoked, revived]))
    assert_error("duplicate_conflict", lambda: load_catalog(snapshot, pin))


def test_catalog_records_and_results_are_immutable_copies(tmp_path: Path) -> None:
    objects = valid_objects()
    snapshot, pin = write_snapshot(tmp_path, bundle(objects))
    catalog = load_catalog(snapshot, pin)
    objects[0]["name"] = "Mutated after load"

    assert catalog.records_by_external_id["T1000"].name == "Synthetic parent"
    with pytest.raises(TypeError):
        catalog.records_by_external_id["T9999"] = catalog.records_by_external_id["T1000"]
    with pytest.raises(FrozenInstanceError):
        catalog.records_by_external_id["T1000"].name = "Mutated"
    with pytest.raises(FrozenInstanceError):
        validate_technique(catalog, "T1000").name = "Mutated"


@pytest.mark.parametrize(
    "supplied",
    [None, True, 1000, b"T1000", "t1000", "T１０００", "T1000\n", "T1000.01"],
)
def test_lookup_never_coerces_or_trims_invalid_input(tmp_path: Path, supplied: object) -> None:
    snapshot, pin = write_snapshot(tmp_path)
    result = validate_technique(load_catalog(snapshot, pin), supplied)
    assert result.normalized_id is None
    assert result.reason_code == "invalid_technique_id"


def test_loading_catalog_has_no_network_egress(tmp_path: Path, monkeypatch) -> None:
    snapshot, pin = write_snapshot(tmp_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("network egress attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert validate_technique(load_catalog(snapshot, pin), "T1000").catalog_status == "active"


def test_committed_fixtures_prove_valid_and_intentionally_broken_inputs() -> None:
    fixture_dir = Path(__file__).parents[1] / "attack" / "fixtures"
    valid_snapshot = fixture_dir / "synthetic-catalog.json"
    valid_payload = valid_snapshot.read_bytes()
    valid_pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-1",
        sha256=hashlib.sha256(valid_payload).hexdigest(),
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    catalog = load_catalog(valid_snapshot, valid_pin)
    assert set(catalog.records_by_external_id) == {"T1000", "T1000.001", "T2000"}

    invalid_snapshot = fixture_dir / "invalid-duplicate-key.json"
    invalid_payload = invalid_snapshot.read_bytes()
    invalid_pin = SnapshotPin(
        kind="synthetic",
        version="synthetic-invalid-duplicate-key",
        sha256=hashlib.sha256(invalid_payload).hexdigest(),
        source_url=None,
        release_tag=None,
        commit=None,
        provenance="hand-authored-test-fixture",
    )
    assert_error("invalid_json", lambda: load_catalog(invalid_snapshot, invalid_pin))
