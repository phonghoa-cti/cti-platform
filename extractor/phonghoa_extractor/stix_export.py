"""Xuất final approved snapshot thành một bundle STIX 2.1 ngoại tuyến."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from phonghoa_core.ioc import IocType, normalize
from phonghoa_extractor import store

SCO_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")
CONFIG_KEYS = {
    "schema_version",
    "id_namespace_uuid",
    "name",
    "identity_class",
    "created",
    "tlp",
}
CONFIG_TLPS = {"TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}
CHILD_NAMESPACE_NAMES = {
    "identity": "phonghoa:w05:stix:1:identity",
    "report": "phonghoa:w05:stix:1:report",
    "bundle": "phonghoa:w05:stix:1:bundle",
}
TLP_MARKINGS = {
    "TLP:CLEAR": (
        "TLP:WHITE",
        "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9",
        "white",
    ),
    "TLP:GREEN": (
        "TLP:GREEN",
        "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da",
        "green",
    ),
    "TLP:AMBER": (
        "TLP:AMBER",
        "marking-definition--f88d31f6-486f-44da-b317-01333bde0b82",
        "amber",
    ),
    "TLP:RED": (
        "TLP:RED",
        "marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed",
        "red",
    ),
}
SCO_TYPES = {
    IocType.IPV4: "ipv4-addr",
    IocType.IPV6: "ipv6-addr",
    IocType.DOMAIN: "domain-name",
    IocType.URL: "url",
    IocType.EMAIL: "email-addr",
    IocType.MD5: "file",
    IocType.SHA1: "file",
    IocType.SHA256: "file",
}
HASH_NAMES = {IocType.MD5: "MD5", IocType.SHA1: "SHA-1", IocType.SHA256: "SHA-256"}


class StixExportError(ValueError):
    """Lỗi export an toàn để CLI trình bày mà không lộ dữ liệu nhạy cảm."""


class PublicationCleanupError(StixExportError):
    """Output đã publish nhưng tên temp do tiến trình tạo chưa xóa được."""


@dataclass(frozen=True)
class ExporterConfig:
    schema_version: str
    id_namespace_uuid: uuid.UUID
    name: str
    identity_class: str
    created: str
    tlp: str
    sha256: str


@dataclass(frozen=True)
class BundleArtifact:
    bytes: bytes
    provenance: dict[str, Any]
    object_count: int
    sha256: str


@dataclass(frozen=True)
class ExportResult:
    draft_id: int
    bundle_sha256: str
    object_count: int


def _reject_floats_and_surrogates(value: Any, label: str = "JSON") -> None:
    if isinstance(value, float):
        raise StixExportError(f"{label} không hỗ trợ số thực")
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise StixExportError(f"{label} chứa Unicode surrogate không hợp lệ") from exc
        return
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise StixExportError(f"{label} chỉ nhận key chuỗi")
        for key, item in value.items():
            _reject_floats_and_surrogates(key, label)
            _reject_floats_and_surrogates(item, label)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_floats_and_surrogates(item, label)


def _canonical_json(value: Any) -> str:
    _reject_floats_and_surrogates(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise StixExportError("Giá trị không thể serialize thành JSON canonical") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_utc_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise StixExportError(f"{label} phải là timestamp có múi giờ")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StixExportError(f"{label} không hợp lệ") from exc
    if parsed.utcoffset() is None:
        raise StixExportError(f"{label} phải có múi giờ")
    parsed = parsed.astimezone(UTC)
    timespec = "microseconds" if parsed.microsecond % 1000 else "milliseconds"
    return parsed.isoformat(timespec=timespec).replace("+00:00", "Z")


def validate_exporter_config(value: Any) -> ExporterConfig:
    """Kiểm config exact trước khi dùng làm namespace/Identity."""

    if not isinstance(value, dict) or set(value) != CONFIG_KEYS:
        raise StixExportError("Exporter config phải có đúng tập field schema v1")
    if value["schema_version"] != "1":
        raise StixExportError("Exporter config schema_version phải là 1")
    try:
        namespace = uuid.UUID(value["id_namespace_uuid"])
    except (AttributeError, TypeError, ValueError) as exc:
        raise StixExportError("id_namespace_uuid không hợp lệ") from exc
    if namespace.int == 0 or namespace == SCO_NAMESPACE:
        raise StixExportError("id_namespace_uuid phải khác nil và namespace SCO")
    if not isinstance(value["name"], str) or not value["name"].strip():
        raise StixExportError("Exporter name phải là chuỗi không rỗng")
    if value["identity_class"] != "organization":
        raise StixExportError("identity_class v1 chỉ hỗ trợ organization")
    created = _normalize_utc_timestamp(value["created"], "created")
    if value["tlp"] not in CONFIG_TLPS:
        raise StixExportError("Exporter config TLP không hợp lệ")
    canonical_value = {
        "schema_version": "1",
        "id_namespace_uuid": str(namespace),
        "name": value["name"],
        "identity_class": "organization",
        "created": created,
        "tlp": value["tlp"],
    }
    return ExporterConfig(
        schema_version="1",
        id_namespace_uuid=namespace,
        name=value["name"],
        identity_class="organization",
        created=created,
        tlp=value["tlp"],
        sha256=_sha256_text(_canonical_json(canonical_value)),
    )


def load_exporter_config(path: str | Path) -> ExporterConfig:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StixExportError("Không đọc được exporter config JSON") from exc
    return validate_exporter_config(value)


def _stix_id(object_type: str, namespace: uuid.UUID, name: str) -> str:
    return f"{object_type}--{uuid.uuid5(namespace, name)}"


def _child_namespace(config: ExporterConfig, kind: str) -> uuid.UUID:
    return uuid.uuid5(config.id_namespace_uuid, CHILD_NAMESPACE_NAMES[kind])


def _sco_from_item(item: Mapping[str, Any], marking_id: str) -> tuple[dict[str, Any], tuple[str, str]]:
    if item.get("kind") != "ioc" or item.get("keep") is not True or item.get("status") != "ok":
        raise StixExportError("Final selection chỉ được chứa IOC eligible")
    try:
        normalized = normalize(item.get("value"))
    except (TypeError, ValueError) as exc:
        raise StixExportError("Final selection chứa IOC không hợp lệ") from exc
    if item.get("type") != normalized.type.value or normalized.type not in SCO_TYPES:
        raise StixExportError("Final selection chứa loại IOC không hỗ trợ")

    if normalized.type in HASH_NAMES:
        id_properties: dict[str, Any] = {"hashes": {HASH_NAMES[normalized.type]: normalized.value}}
    else:
        id_properties = {"value": normalized.value}
    object_type = SCO_TYPES[normalized.type]
    sco = {
        "type": object_type,
        "spec_version": "2.1",
        "id": _stix_id(object_type, SCO_NAMESPACE, _canonical_json(id_properties)),
        **id_properties,
        "object_marking_refs": [marking_id],
    }
    return sco, (normalized.type.value, normalized.value)


def _validate_snapshot(snapshot: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(snapshot, store.ApprovedExportSnapshot):
        raise StixExportError("snapshot phải là ApprovedExportSnapshot")
    if (
        isinstance(snapshot.draft_id, bool)
        or not isinstance(snapshot.draft_id, int)
        or snapshot.draft_id < 1
        or isinstance(snapshot.approved_audit_id, bool)
        or not isinstance(snapshot.approved_audit_id, int)
        or snapshot.approved_audit_id < 1
    ):
        raise StixExportError("Snapshot ID không hợp lệ")
    try:
        payload = json.loads(_canonical_json(snapshot.payload))
        store._validate_draft(payload)
    except store.DraftStoreError as exc:
        raise StixExportError("Snapshot payload không hợp lệ") from exc
    if (
        not isinstance(snapshot.selected_indices, tuple)
        or not snapshot.selected_indices
        or any(isinstance(index, bool) or not isinstance(index, int) for index in snapshot.selected_indices)
        or tuple(sorted(set(snapshot.selected_indices))) != snapshot.selected_indices
    ):
        raise StixExportError("Snapshot selection không canonical hoặc rỗng")
    serialized_selection = _canonical_json(list(snapshot.selected_indices))
    if _sha256_text(serialized_selection) != snapshot.selected_sha256:
        raise StixExportError("Snapshot selection hash không hợp lệ")
    if any(index < 0 or index >= len(payload["items"]) for index in snapshot.selected_indices):
        raise StixExportError("Snapshot selection index ngoài payload")
    return payload, _normalize_utc_timestamp(snapshot.decided_at, "decided_at")


def build_bundle(snapshot: store.ApprovedExportSnapshot, config: ExporterConfig) -> BundleArtifact:
    """Tạo và tự kiểm một bundle deterministic trong bộ nhớ."""

    if not isinstance(config, ExporterConfig):
        raise StixExportError("config chưa được validate")
    payload, decided_at = _validate_snapshot(snapshot)
    source_tlp = payload["tlp"]
    if source_tlp != config.tlp:
        raise StixExportError("Exporter config TLP phải bằng snapshot TLP")
    if source_tlp == "TLP:AMBER+STRICT":
        raise StixExportError("TLP:AMBER+STRICT chưa được phép export trong profile v1")
    stix_tlp, marking_id, marking_value = TLP_MARKINGS[source_tlp]

    payload_sha = _sha256_text(_canonical_json(payload))
    provenance = {
        "format_version": "1",
        "source_sha256": payload["source"]["sha256"],
        "payload_sha256": payload_sha,
        "draft_id": snapshot.draft_id,
        "approved_audit_id": snapshot.approved_audit_id,
        "review_version": snapshot.review_version,
        "selection_version": snapshot.final_selection_version,
        "selected_indices": list(snapshot.selected_indices),
        "selected_sha256": snapshot.selected_sha256,
        "decided_at": decided_at,
        "exporter_config_sha256": config.sha256,
        "source_tlp": source_tlp,
        "stix_tlp": stix_tlp,
    }
    provenance_json = _canonical_json(provenance)
    provenance_sha = _sha256_text(provenance_json)
    identity_id = _stix_id("identity", _child_namespace(config, "identity"), config.sha256)
    report_id = _stix_id("report", _child_namespace(config, "report"), provenance_sha)
    marking = {
        "type": "marking-definition",
        "spec_version": "2.1",
        "id": marking_id,
        "created": "2017-01-20T00:00:00.000Z",
        "name": stix_tlp,
        "definition_type": "tlp",
        "definition": {"tlp": marking_value},
    }
    identity = {
        "type": "identity",
        "spec_version": "2.1",
        "id": identity_id,
        "created": config.created,
        "modified": config.created,
        "name": config.name,
        "identity_class": config.identity_class,
        "object_marking_refs": [marking_id],
    }

    scos: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index in snapshot.selected_indices:
        sco, dedupe_key = _sco_from_item(payload["items"][index], marking_id)
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            scos.append(sco)
    if not scos:
        raise StixExportError("Final selection không tạo được SCO")
    report = {
        "type": "report",
        "spec_version": "2.1",
        "id": report_id,
        "created_by_ref": identity_id,
        "created": decided_at,
        "modified": decided_at,
        "name": "Phong Hoa approved offline IOC export",
        "description": "Offline export of locally approved IOC data; no import or observation is asserted.",
        "published": decided_at,
        "report_types": ["threat-report"],
        "object_refs": [identity_id, *(sco["id"] for sco in scos)],
        "object_marking_refs": [marking_id],
        "external_references": [
            {
                "source_name": "phong-hoa-approved-snapshot",
                "external_id": provenance_sha,
                "description": provenance_json,
            }
        ],
    }
    objects = [marking, identity, *scos, report]
    ordered_ids = [obj["id"] for obj in objects]
    bundle_id = _stix_id(
        "bundle",
        _child_namespace(config, "bundle"),
        _canonical_json(ordered_ids),
    )
    bundle = {"type": "bundle", "id": bundle_id, "objects": objects}
    _validate_bundle_structure(bundle)
    bundle_bytes = (_canonical_json(bundle) + "\n").encode("utf-8")
    return BundleArtifact(
        bytes=bundle_bytes,
        provenance=provenance,
        object_count=len(objects),
        sha256=hashlib.sha256(bundle_bytes).hexdigest(),
    )


def _validate_bundle_structure(bundle: Mapping[str, Any]) -> None:
    if set(bundle) != {"type", "id", "objects"} or bundle["type"] != "bundle":
        raise StixExportError("Bundle structure không hợp lệ")
    objects = bundle["objects"]
    if not isinstance(objects, list) or len(objects) < 4:
        raise StixExportError("Bundle thiếu object bắt buộc")
    ids = [obj.get("id") for obj in objects]
    if any(not isinstance(object_id, str) for object_id in ids) or len(ids) != len(set(ids)):
        raise StixExportError("Bundle object ID không hợp lệ hoặc trùng")
    by_id = {obj["id"]: obj for obj in objects}
    if [obj["type"] for obj in objects[:2]] != ["marking-definition", "identity"]:
        raise StixExportError("Bundle order không hợp lệ")
    report = objects[-1]
    if report.get("type") != "report" or report.get("created_by_ref") not in by_id:
        raise StixExportError("Report reference không hợp lệ")
    if report.get("object_refs") != ids[1:-1]:
        raise StixExportError("Report object_refs không khớp ordered objects")
    marking_id = objects[0]["id"]
    for obj in objects[1:]:
        if obj.get("object_marking_refs") != [marking_id]:
            raise StixExportError("Object marking reference không hợp lệ")


def _normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _is_reparse(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _protected_aliases(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    protected: list[Path] = []
    for raw in paths:
        path = Path(raw)
        protected.extend(
            (path, Path(str(path) + "-wal"), Path(str(path) + "-shm"), Path(str(path) + "-journal"))
        )
    return tuple(protected)


def _validate_output_target(output: Path, protected_paths: Sequence[str | Path]) -> None:
    parent = output.parent
    if not parent.is_dir():
        raise StixExportError("Thư mục output phải tồn tại")
    if any(path.is_symlink() or _is_reparse(path) for path in (parent, *parent.parents)):
        raise StixExportError("Thư mục output symbolic/reparse không được hỗ trợ")
    protected = _protected_aliases(protected_paths)
    normalized = _normalized_path(output)
    if any(normalized == _normalized_path(path) for path in protected):
        raise StixExportError("Output trùng đường dẫn được bảo vệ")
    if output.is_symlink() or _is_reparse(output):
        raise StixExportError("Output symbolic/reparse không được hỗ trợ")
    if output.exists():
        if not output.is_file():
            raise StixExportError("Output tồn tại nhưng không phải regular file")
        for protected_path in protected:
            if protected_path.exists():
                try:
                    if output.samefile(protected_path):
                        raise StixExportError("Output là alias của file được bảo vệ")
                except OSError as exc:
                    raise StixExportError("Không kiểm được alias output") from exc


def _compare_existing(output: Path, data: bytes, protected_paths: Sequence[str | Path] = ()) -> None:
    _validate_output_target(output, protected_paths)
    try:
        existing = output.read_bytes()
    except OSError as exc:
        raise StixExportError("Không đọc được output đã tồn tại") from exc
    if existing != data:
        raise StixExportError("Output đã tồn tại với nội dung khác")


def publish_bytes(
    output_path: str | Path,
    data: bytes,
    *,
    protected_paths: Sequence[str | Path] = (),
    before_link: Callable[[], object] | None = None,
) -> None:
    """Publish complete bytes bằng hardlink tạo mới; không replace/truncate output."""

    if not isinstance(data, bytes):
        raise StixExportError("Dữ liệu publish phải là bytes")
    output = Path(output_path)
    _validate_output_target(output, protected_paths)
    if output.exists():
        _compare_existing(output, data, protected_paths)
        return

    temp: Path | None = None
    descriptor: int | None = None
    for _attempt in range(32):
        candidate = output.parent / f".{output.name}.{uuid.uuid4().hex}.tmp"
        try:
            descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY, 0o600)
            temp = candidate
            break
        except FileExistsError:
            continue
        except OSError as exc:
            raise StixExportError("Không tạo được temp file cùng thư mục output") from exc
    if temp is None or descriptor is None:
        raise StixExportError("Không tạo được temp file độc quyền")

    published = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if before_link is not None:
            before_link()
        try:
            os.link(temp, output)
            published = True
        except FileExistsError:
            _compare_existing(output, data, protected_paths)
        except OSError as exc:
            raise StixExportError("Không publish được output bằng hardlink") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
        except OSError as exc:
            if published:
                raise PublicationCleanupError("Output đã publish nhưng cleanup temp chưa hoàn tất") from exc
            raise StixExportError("Publish thất bại và cleanup temp chưa hoàn tất") from exc


def export_approved(
    *,
    db_path: str | Path,
    draft_id: int,
    exporter_config_path: str | Path,
    output_path: str | Path,
    timeout: float = 5.0,
) -> ExportResult:
    if isinstance(draft_id, bool) or not isinstance(draft_id, int) or not 1 <= draft_id <= 2**63 - 1:
        raise StixExportError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout < 0
    ):
        raise StixExportError("timeout phải là số hữu hạn không âm")
    config_path = Path(exporter_config_path)
    output = Path(output_path)
    _validate_output_target(output, (db_path, config_path))
    config = load_exporter_config(config_path)
    snapshot = store.get_approved_export_snapshot(db_path, draft_id, timeout=timeout)
    artifact = build_bundle(snapshot, config)
    publish_bytes(output, artifact.bytes, protected_paths=(db_path, config_path))
    return ExportResult(snapshot.draft_id, artifact.sha256, artifact.object_count)
