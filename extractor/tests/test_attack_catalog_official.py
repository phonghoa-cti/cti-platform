from __future__ import annotations

import json
import os
import shutil
import socket
from pathlib import Path

import pytest

import phonghoa_extractor.attack_catalog as attack_catalog
from phonghoa_extractor.attack_catalog import (
    AttackCatalogError,
    SnapshotPin,
    load_catalog,
    validate_technique,
)

OFFICIAL_SHA256 = "539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5"
OFFICIAL_COMMIT = "f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7"
OFFICIAL_SOURCE_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/"
    f"{OFFICIAL_COMMIT}/enterprise-attack/enterprise-attack-20.1.json"
)
OFFICIAL_BYTES = 55_277_605
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "attack_official"


def official_values() -> dict[str, object]:
    return {
        "kind": "official",
        "version": "20.1",
        "sha256": OFFICIAL_SHA256,
        "source_url": OFFICIAL_SOURCE_URL,
        "release_tag": "v20.1",
        "commit": OFFICIAL_COMMIT,
        "provenance": "mitre-attack-stix-data",
    }


def official_pin() -> SnapshotPin:
    values = json.loads((FIXTURE_DIR / "official-pin.json").read_text(encoding="utf-8"))
    return SnapshotPin(**values)


@pytest.fixture(scope="module")
def official_snapshot() -> Path:
    configured = os.environ.get("PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT")
    if configured is None:
        pytest.skip("set PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT to the pinned MITRE v20.1 asset")
    snapshot = Path(configured)
    if not snapshot.is_file():
        pytest.fail("PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT is not a readable file")
    return snapshot


def test_public_loader_reads_pinned_official_v20_1_without_semantic_eligibility(
    official_snapshot: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network egress attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    catalog = load_catalog(official_snapshot, official_pin())

    assert len(catalog.records_by_external_id) == 867
    assert sum(record.is_subtechnique for record in catalog.records_by_external_id.values()) == 497
    statuses = [
        validate_technique(catalog, external_id).catalog_status
        for external_id in catalog.records_by_external_id
    ]
    assert statuses.count("active") == 706
    assert statuses.count("inactive") == 161

    active = validate_technique(catalog, "T1001")
    child = validate_technique(catalog, "T1001.001")
    inactive = validate_technique(catalog, "T1002")
    unknown = validate_technique(catalog, "T0000")
    malformed = validate_technique(catalog, " T1001")

    assert active.catalog_status == "active"
    assert catalog.records_by_external_id["T1001"].description
    assert child.catalog_status == "active"
    assert child.is_subtechnique is True
    assert child.parent_external_ids == ("T1001",)
    assert inactive.catalog_status == "inactive"
    assert unknown.catalog_status == "unknown"
    assert malformed.catalog_status == "not_checked"
    for result in (active, child, inactive, unknown, malformed):
        assert result.semantic_status == "unverified"
        assert result.operational_draft_eligible is False


_MISSING = object()


@pytest.mark.parametrize("field", list(official_values()))
@pytest.mark.parametrize("bad_value", [_MISSING, None, [], {}, True, 1])
def test_rejects_missing_or_wrong_type_official_field_before_snapshot_io(
    field: str,
    bad_value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pin = official_pin()
    if bad_value is _MISSING:
        object.__delattr__(pin, field)
    else:
        object.__setattr__(pin, field, bad_value)

    def forbidden(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("_read_snapshot must not run for an invalid pin")

    monkeypatch.setattr(attack_catalog, "_read_snapshot", forbidden)
    with pytest.raises(AttackCatalogError, match="^invalid_pin$") as caught:
        load_catalog(Path("marker-must-not-open"), pin)
    assert caught.value.code == "invalid_pin"


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("kind", "synthetic"),
        ("version", "20.2"),
        ("sha256", OFFICIAL_SHA256.upper()),
        ("source_url", OFFICIAL_SOURCE_URL.replace("https://", "http://")),
        ("source_url", OFFICIAL_SOURCE_URL.replace("raw.githubusercontent.com", "example.com")),
        ("source_url", OFFICIAL_SOURCE_URL.replace("mitre-attack/attack-stix-data", "other/repo")),
        ("source_url", OFFICIAL_SOURCE_URL.replace(OFFICIAL_COMMIT, "master")),
        ("source_url", OFFICIAL_SOURCE_URL.replace("enterprise-attack/", "mobile-attack/")),
        ("source_url", OFFICIAL_SOURCE_URL.replace("20.1.json", "20.2.json")),
        ("source_url", f"{OFFICIAL_SOURCE_URL}?download=1"),
        ("source_url", f"{OFFICIAL_SOURCE_URL}#fragment"),
        ("source_url", OFFICIAL_SOURCE_URL.replace("https://", "https://user@example.com@")),
        ("source_url", OFFICIAL_SOURCE_URL.replace("enterprise-attack", "enterprise%2Dattack")),
        ("release_tag", "v20.2"),
        ("commit", "0" * 40),
        ("provenance", "other-provenance"),
    ],
)
def test_rejects_noncanonical_official_metadata_before_snapshot_io(
    field: str,
    bad_value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = official_values()
    values[field] = bad_value
    pin = SnapshotPin(**values)

    def forbidden(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("_read_snapshot must not run for an invalid pin")

    monkeypatch.setattr(attack_catalog, "_read_snapshot", forbidden)
    with pytest.raises(AttackCatalogError, match="^invalid_pin$") as caught:
        load_catalog(Path("marker-must-not-open"), pin)
    assert caught.value.code == "invalid_pin"


def test_rejects_extra_official_pin_metadata_before_snapshot_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pin = official_pin()
    object.__setattr__(pin, "unreviewed_metadata", "marker")

    def forbidden(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("_read_snapshot must not run for an invalid pin")

    monkeypatch.setattr(attack_catalog, "_read_snapshot", forbidden)
    with pytest.raises(AttackCatalogError, match="^invalid_pin$") as caught:
        load_catalog(Path("marker-must-not-open"), pin)
    assert caught.value.code == "invalid_pin"


def test_official_snapshot_hash_mismatch_is_detected_before_json_parse(
    official_snapshot: Path,
    tmp_path: Path,
) -> None:
    changed = tmp_path / "changed-enterprise-attack-20.1.json"
    shutil.copyfile(official_snapshot, changed)
    with changed.open("r+b") as stream:
        first_byte = stream.read(1)
        stream.seek(0)
        stream.write(b"[" if first_byte != b"[" else b"{")

    with pytest.raises(AttackCatalogError, match="^snapshot_hash_mismatch$") as caught:
        load_catalog(changed, official_pin())
    assert caught.value.code == "snapshot_hash_mismatch"


def test_official_snapshot_respects_caller_size_bound(official_snapshot: Path) -> None:
    assert official_snapshot.stat().st_size == OFFICIAL_BYTES
    with pytest.raises(AttackCatalogError, match="^snapshot_too_large$") as caught:
        load_catalog(official_snapshot, official_pin(), max_bytes=OFFICIAL_BYTES - 1)
    assert caught.value.code == "snapshot_too_large"
