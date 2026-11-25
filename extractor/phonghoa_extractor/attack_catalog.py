from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Literal


@dataclass(frozen=True)
class SnapshotPin:
    kind: Literal["synthetic", "official"]
    version: str
    sha256: str
    source_url: str | None
    release_tag: str | None
    commit: str | None
    provenance: Literal["hand-authored-test-fixture", "mitre-attack-stix-data"]


@dataclass(frozen=True)
class TechniqueRecord:
    stix_id: str
    external_id: str
    name: str
    modified: str
    revoked: bool
    deprecated: bool
    is_subtechnique: bool
    parent_external_ids: tuple[str, ...]
    description: str | None = None


@dataclass(frozen=True)
class AttackCatalog:
    pin: SnapshotPin
    records_by_external_id: Mapping[str, TechniqueRecord]


@dataclass(frozen=True)
class TechniqueLookup:
    normalized_id: str | None
    syntax_valid: bool
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"]
    reason_code: str
    pin_kind: Literal["synthetic", "official"]
    snapshot_version: str
    snapshot_sha256: str
    external_id: str | None
    name: str | None
    is_subtechnique: bool | None
    parent_external_ids: tuple[str, ...]
    semantic_status: Literal["unverified"] = "unverified"
    operational_draft_eligible: bool = False


class AttackCatalogError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return self.code


@dataclass(frozen=True)
class _PatternVersion:
    raw: dict[str, object]
    stix_id: str
    external_id: str
    name: str
    modified: str
    modified_key: tuple[int, ...]
    revoked: bool
    deprecated: bool
    is_subtechnique: bool
    enterprise: bool


@dataclass(frozen=True)
class _RelationshipVersion:
    raw: dict[str, object]
    stix_id: str
    modified_key: tuple[int, ...]
    revoked: bool
    deprecated: bool
    source_ref: str
    target_ref: str


_TECHNIQUE_ID = re.compile(r"T[0-9]{4}(?:\.[0-9]{3})?", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_STIX_ID = re.compile(
    r"(?P<type>attack-pattern|relationship)--"
    r"(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.ASCII,
)
_UTC_TIMESTAMP = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,18}))?Z",
    re.ASCII,
)
_ALLOWED_DOMAINS = {"enterprise-attack", "mobile-attack", "ics-attack"}
_EXPECTED_PROVENANCE = {
    "kind": "synthetic",
    "generator": "hand-authored-test-fixture",
    "purpose": "restricted-catalog-test",
    "mitre_release": None,
    "source_url": None,
    "release_tag": None,
    "commit": None,
}
_PIN_FIELDS = {
    "kind",
    "version",
    "sha256",
    "source_url",
    "release_tag",
    "commit",
    "provenance",
}
_OFFICIAL_PIN = {
    "kind": "official",
    "version": "20.1",
    "sha256": "539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5",
    "source_url": (
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/"
        "f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7/"
        "enterprise-attack/enterprise-attack-20.1.json"
    ),
    "release_tag": "v20.1",
    "commit": "f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7",
    "provenance": "mitre-attack-stix-data",
}
_MAX_BYTES = 64 * 1024 * 1024


class _InvalidJson(ValueError):
    pass


def _fail(code: str) -> None:
    raise AttackCatalogError(code)


def _validate_pin(pin: SnapshotPin, max_bytes: int) -> None:
    if type(pin) is not SnapshotPin:
        _fail("invalid_pin")
    if set(vars(pin)) != _PIN_FIELDS:
        _fail("invalid_pin")
    if type(max_bytes) is not int or not 1 <= max_bytes <= _MAX_BYTES:
        _fail("invalid_pin")
    if pin.kind == "official":
        values = vars(pin)
        if any(type(value) is not str for value in values.values()) or values != _OFFICIAL_PIN:
            _fail("invalid_pin")
        return
    if type(pin.kind) is not str or pin.kind != "synthetic":
        _fail("invalid_pin")
    if (
        type(pin.version) is not str
        or not 1 <= len(pin.version) <= 64
        or not pin.version.isascii()
        or any(ord(character) < 32 or ord(character) == 127 for character in pin.version)
    ):
        _fail("invalid_pin")
    if type(pin.sha256) is not str or _SHA256.fullmatch(pin.sha256) is None:
        _fail("invalid_pin")
    if pin.provenance != "hand-authored-test-fixture":
        _fail("invalid_pin")
    if any(value is not None for value in (pin.source_url, pin.release_tag, pin.commit)):
        _fail("invalid_pin")


def _read_snapshot(snapshot: Path, max_bytes: int) -> bytes:
    if not isinstance(snapshot, Path):
        _fail("snapshot_io_error")
    try:
        with snapshot.open("rb") as stream:
            payload = stream.read(max_bytes + 1)
    except FileNotFoundError:
        _fail("snapshot_not_found")
    except (OSError, ValueError):
        _fail("snapshot_io_error")
    if len(payload) > max_bytes:
        _fail("snapshot_too_large")
    return payload


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidJson
        result[key] = value
    return result


def _parse_int(value: str) -> int:
    if len(value.lstrip("-")) > 128:
        raise _InvalidJson
    return int(value)


def _parse_float(value: str) -> Decimal:
    if len(value) > 128:
        raise _InvalidJson
    exponent = value.lower().partition("e")[2]
    if exponent and abs(int(exponent)) > 1000:
        raise _InvalidJson
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise _InvalidJson from error
    if not parsed.is_finite():
        raise _InvalidJson
    return parsed


def _parse_json(payload: bytes) -> object:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        _fail("invalid_utf8")
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=lambda _value: (_ for _ in ()).throw(_InvalidJson()),
            parse_int=_parse_int,
            parse_float=_parse_float,
        )
    except (json.JSONDecodeError, _InvalidJson, RecursionError, ValueError):
        _fail("invalid_json")
    stack = [(parsed, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > 256:
            _fail("invalid_json")
        if type(value) is dict:
            stack.extend((child, depth + 1) for child in value.values())
        elif type(value) is list:
            stack.extend((child, depth + 1) for child in value)
    return parsed


def _lifecycle(item: dict[str, object], field: str, code: str) -> bool:
    value = item.get(field, False)
    if type(value) is not bool:
        _fail(code)
    return value


def _stix_id(value: object, expected_type: str, code: str) -> str:
    if type(value) is not str:
        _fail(code)
    match = _STIX_ID.fullmatch(value)
    if match is None or match.group("type") != expected_type:
        _fail(code)
    return value


def _timestamp(value: object, code: str) -> tuple[str, tuple[int, ...]]:
    if type(value) is not str:
        _fail(code)
    match = _UTC_TIMESTAMP.fullmatch(value)
    if match is None:
        _fail(code)
    parts = tuple(int(match.group(name)) for name in ("year", "month", "day", "hour", "minute", "second"))
    try:
        datetime(*parts)
    except ValueError:
        _fail(code)
    fraction = (match.group("fraction") or "").ljust(18, "0")
    return value, (*parts, int(fraction or "0"))


def _external_id(item: dict[str, object], code: str) -> str:
    references = item.get("external_references")
    if type(references) is not list:
        _fail(code)
    mitre_ids: list[str] = []
    for reference in references:
        if type(reference) is not dict or type(reference.get("source_name")) is not str:
            _fail(code)
        if reference["source_name"] == "mitre-attack":
            value = reference.get("external_id")
            if type(value) is not str or _TECHNIQUE_ID.fullmatch(value) is None:
                _fail(code)
            mitre_ids.append(value)
    if len(mitre_ids) != 1:
        _fail(code)
    return mitre_ids[0]


def _description(item: dict[str, object], code: str) -> str | None:
    if "description" not in item:
        return None
    value = item["description"]
    if type(value) is not str:
        _fail(code)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        _fail(code)
    if len(encoded) > 32 * 1024:
        _fail(code)
    return value or None


def _parse_pattern(item: dict[str, object]) -> _PatternVersion:
    code = "invalid_attack_pattern"
    stix_id = _stix_id(item.get("id"), "attack-pattern", code)
    if item.get("spec_version") != "2.1":
        _fail(code)
    name = item.get("name")
    if type(name) is not str or not name or len(name) > 256:
        _fail(code)
    modified, modified_key = _timestamp(item.get("modified"), code)
    revoked = _lifecycle(item, "revoked", code)
    deprecated = _lifecycle(item, "x_mitre_deprecated", code)
    is_subtechnique = item.get("x_mitre_is_subtechnique")
    if type(is_subtechnique) is not bool:
        _fail(code)
    domains = item.get("x_mitre_domains")
    if type(domains) is not list or not domains:
        _fail(code)
    if any(type(domain) is not str or domain not in _ALLOWED_DOMAINS for domain in domains):
        _fail(code)
    external_id = _external_id(item, code)
    if ("." in external_id) != is_subtechnique:
        _fail(code)
    return _PatternVersion(
        raw=item,
        stix_id=stix_id,
        external_id=external_id,
        name=name,
        modified=modified,
        modified_key=modified_key,
        revoked=revoked,
        deprecated=deprecated,
        is_subtechnique=is_subtechnique,
        enterprise="enterprise-attack" in domains,
    )


def _parse_relationship(item: dict[str, object]) -> _RelationshipVersion | None:
    code = "invalid_relationship"
    relationship_type = item.get("relationship_type")
    if type(relationship_type) is not str:
        _fail(code)
    if relationship_type != "subtechnique-of":
        return None
    stix_id = _stix_id(item.get("id"), "relationship", code)
    if item.get("spec_version") != "2.1":
        _fail(code)
    _, modified_key = _timestamp(item.get("modified"), code)
    return _RelationshipVersion(
        raw=item,
        stix_id=stix_id,
        modified_key=modified_key,
        revoked=_lifecycle(item, "revoked", code),
        deprecated=_lifecycle(item, "x_mitre_deprecated", code),
        source_ref=_stix_id(item.get("source_ref"), "attack-pattern", code),
        target_ref=_stix_id(item.get("target_ref"), "attack-pattern", code),
    )


def _canonical_patterns(items: list[_PatternVersion]) -> dict[str, _PatternVersion]:
    grouped: dict[str, list[_PatternVersion]] = defaultdict(list)
    for item in items:
        grouped[item.stix_id].append(item)
    current: dict[str, _PatternVersion] = {}
    for stix_id, versions in grouped.items():
        if len({version.external_id for version in versions}) != 1:
            _fail("duplicate_conflict")
        current[stix_id] = _select_version(versions)
    return current


def _canonical_relationships(
    items: list[_RelationshipVersion],
) -> dict[str, _RelationshipVersion]:
    grouped: dict[str, list[_RelationshipVersion]] = defaultdict(list)
    for item in items:
        grouped[item.stix_id].append(item)
    return {stix_id: _select_version(versions) for stix_id, versions in grouped.items()}


def _json_equal(first: object, second: object) -> bool:
    if type(first) is bool or type(second) is bool:
        return type(first) is bool and type(second) is bool and first == second
    if isinstance(first, (int, Decimal)) or isinstance(second, (int, Decimal)):
        return isinstance(first, (int, Decimal)) and isinstance(second, (int, Decimal)) and first == second
    if type(first) is dict or type(second) is dict:
        return (
            type(first) is dict
            and type(second) is dict
            and first.keys() == second.keys()
            and all(_json_equal(first[key], second[key]) for key in first)
        )
    if type(first) is list or type(second) is list:
        return (
            type(first) is list
            and type(second) is list
            and len(first) == len(second)
            and all(_json_equal(left, right) for left, right in zip(first, second, strict=True))
        )
    return type(first) is type(second) and first == second


def _select_version(versions):
    unique = []
    for version in versions:
        if not any(_json_equal(version.raw, existing.raw) for existing in unique):
            unique.append(version)
    ordered = sorted(unique, key=lambda version: version.modified_key)
    for previous, following in zip(ordered, ordered[1:], strict=False):
        if previous.modified_key == following.modified_key:
            _fail("duplicate_conflict")
    revoked_seen = False
    for version in ordered:
        if revoked_seen and not version.revoked:
            _fail("duplicate_conflict")
        revoked_seen = revoked_seen or version.revoked
    return ordered[-1]


def _validate_bundle(value: object, pin_kind: Literal["synthetic", "official"]) -> list[dict[str, object]]:
    if type(value) is not dict or value.get("type") != "bundle":
        _fail("invalid_bundle")
    if pin_kind == "synthetic" and value.get("x_phonghoa_provenance") != _EXPECTED_PROVENANCE:
        _fail("invalid_bundle")
    objects = value.get("objects")
    if type(objects) is not list:
        _fail("invalid_bundle")
    members: list[dict[str, object]] = []
    for member in objects:
        if type(member) is not dict or type(member.get("type")) is not str:
            _fail("invalid_member")
        members.append(member)
    return members


def _build_parent_map(
    enterprise: dict[str, _PatternVersion],
    relationships: dict[str, _RelationshipVersion],
) -> dict[str, set[str]]:
    parents: dict[str, set[str]] = defaultdict(set)
    for edge in relationships.values():
        if edge.revoked or edge.deprecated:
            continue
        child = enterprise.get(edge.source_ref)
        parent = enterprise.get(edge.target_ref)
        if child is None or parent is None:
            _fail("parent_conflict")
        if (
            child.stix_id == parent.stix_id
            or not child.is_subtechnique
            or parent.is_subtechnique
            or child.external_id.split(".", 1)[0] != parent.external_id
        ):
            _fail("parent_conflict")
        parents[child.stix_id].add(parent.stix_id)
    for child in enterprise.values():
        parent_ids = parents.get(child.stix_id, set())
        if len(parent_ids) > 1:
            _fail("parent_conflict")
        inactive = child.revoked or child.deprecated
        if child.is_subtechnique and not inactive:
            if len(parent_ids) != 1:
                _fail("parent_conflict")
            parent = enterprise[next(iter(parent_ids))]
            if parent.revoked or parent.deprecated:
                _fail("parent_conflict")
    return parents


def _build_records(
    patterns: dict[str, _PatternVersion],
    relationships: dict[str, _RelationshipVersion],
) -> Mapping[str, TechniqueRecord]:
    enterprise = {stix_id: item for stix_id, item in patterns.items() if item.enterprise}
    external_ids = [item.external_id for item in enterprise.values()]
    if len(external_ids) != len(set(external_ids)):
        _fail("duplicate_conflict")
    parents = _build_parent_map(enterprise, relationships)
    records = {
        item.external_id: TechniqueRecord(
            stix_id=item.stix_id,
            external_id=item.external_id,
            name=item.name,
            modified=item.modified,
            revoked=item.revoked,
            deprecated=item.deprecated,
            is_subtechnique=item.is_subtechnique,
            parent_external_ids=tuple(
                sorted(enterprise[parent_id].external_id for parent_id in parents.get(item.stix_id, set()))
            ),
            description=_description(item.raw, "invalid_attack_pattern"),
        )
        for item in enterprise.values()
    }
    return MappingProxyType(dict(records))


def load_catalog(
    snapshot: Path,
    pin: SnapshotPin,
    *,
    max_bytes: int = 64 * 1024 * 1024,
) -> AttackCatalog:
    _validate_pin(pin, max_bytes)
    payload = _read_snapshot(snapshot, max_bytes)
    if hashlib.sha256(payload).hexdigest() != pin.sha256:
        _fail("snapshot_hash_mismatch")
    members = _validate_bundle(_parse_json(payload), pin.kind)
    patterns: list[_PatternVersion] = []
    relationships: list[_RelationshipVersion] = []
    for member in members:
        if member["type"] == "attack-pattern":
            patterns.append(_parse_pattern(member))
        elif member["type"] == "relationship":
            parsed = _parse_relationship(member)
            if parsed is not None:
                relationships.append(parsed)
    records = _build_records(
        _canonical_patterns(patterns),
        _canonical_relationships(relationships),
    )
    return AttackCatalog(pin=pin, records_by_external_id=records)


def _lookup_result(
    catalog: AttackCatalog,
    *,
    normalized_id: str | None,
    syntax_valid: bool,
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"],
    reason_code: str,
    record: TechniqueRecord | None = None,
) -> TechniqueLookup:
    return TechniqueLookup(
        normalized_id=normalized_id,
        syntax_valid=syntax_valid,
        catalog_status=catalog_status,
        reason_code=reason_code,
        pin_kind=catalog.pin.kind,
        snapshot_version=catalog.pin.version,
        snapshot_sha256=catalog.pin.sha256,
        external_id=record.external_id if record else None,
        name=record.name if record else None,
        is_subtechnique=record.is_subtechnique if record else None,
        parent_external_ids=record.parent_external_ids if record else (),
    )


def validate_technique(catalog: AttackCatalog, supplied_id: object) -> TechniqueLookup:
    if type(supplied_id) is not str or _TECHNIQUE_ID.fullmatch(supplied_id) is None:
        return _lookup_result(
            catalog,
            normalized_id=None,
            syntax_valid=False,
            catalog_status="not_checked",
            reason_code="invalid_technique_id",
        )
    record = catalog.records_by_external_id.get(supplied_id)
    if record is None:
        return _lookup_result(
            catalog,
            normalized_id=supplied_id,
            syntax_valid=True,
            catalog_status="unknown",
            reason_code="unknown_technique_id",
        )
    inactive = record.revoked or record.deprecated
    return _lookup_result(
        catalog,
        normalized_id=supplied_id,
        syntax_valid=True,
        catalog_status="inactive" if inactive else "active",
        reason_code="catalog_inactive" if inactive else "catalog_active",
        record=record,
    )
