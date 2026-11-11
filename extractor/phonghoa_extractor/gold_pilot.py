from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from phonghoa_core.ioc import IocType, normalize
from phonghoa_extractor.attack_catalog import (
    AttackCatalogError,
    SnapshotPin,
    load_catalog,
    validate_technique,
)

ID64 = re.compile(r"[a-z0-9][a-z0-9-]{0,63}", re.ASCII)
ID32 = re.compile(r"[a-z0-9][a-z0-9-]{0,31}", re.ASCII)
HASH = re.compile(r"[0-9a-f]{64}", re.ASCII)
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
ERRORS = {
    "invalid_arguments",
    "invalid_inventory",
    "invalid_manifest",
    "invalid_record",
    "invalid_annotation",
    "invalid_raw",
    "invalid_pin",
    "invalid_catalog",
    "invalid_technique",
    "unsafe_output",
    "io_failure",
}
LIMITATIONS = [
    "declared-rights-only",
    "annotator-independence-unverified",
    "declared-deduplication-only",
    "not-gold",
    "no-semantic-ttp-validation",
    "no-model-quality-claim",
]


class GoldPilotError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code if code in ERRORS else "io_failure"
        super().__init__(self.code)

    def __repr__(self) -> str:
        return self.code


@dataclass(frozen=True)
class GoldPilotReadiness:
    status: str
    payload: bytes
    dataset_root: Path
    protected_inputs: tuple[Path, ...]


@dataclass(frozen=True)
class WriteResult:
    published: bool = True
    cleanup_warning: bool = False


@dataclass(frozen=True)
class _Record:
    value: dict[str, object]
    text: str | None
    raw_path: Path | None
    annotations: tuple[dict[str, object], ...] = ()


class _BadJson(ValueError):
    pass


def fail(code: str) -> None:
    raise GoldPilotError(code)


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in items:
        if key in value:
            raise _BadJson
        value[key] = item
    return value


def parse_float(value: str) -> Decimal:
    if len(value) > 128:
        raise _BadJson
    exponent = value.lower().partition("e")[2]
    if exponent and abs(int(exponent)) > 1000:
        raise _BadJson
    return Decimal(value)


def safe_file(path: Path, code: str) -> os.stat_result:
    try:
        info = path.lstat()
    except FileNotFoundError:
        fail(code)
    except (OSError, ValueError):
        fail("io_failure")
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_file_attributes & REPARSE:
        fail(code)
    return info


def safe_dir(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        fail("invalid_inventory")
    except (OSError, ValueError):
        fail("io_failure")
    if not stat.S_ISDIR(info.st_mode) or info.st_file_attributes & REPARSE:
        fail("invalid_inventory")


def read(path: Path, limit: int, code: str) -> bytes:
    safe_file(path, code)
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except (OSError, ValueError):
        fail("io_failure")
    if len(raw) > limit:
        fail(code)
    return raw


def load_json(path: Path, limit: int, code: str) -> tuple[dict[str, object], bytes]:
    raw = read(path, limit, code)
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(code)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(_BadJson()),
            parse_int=lambda x: int(x) if len(x.lstrip("-")) <= 128 else (_ for _ in ()).throw(_BadJson()),
            parse_float=parse_float,
        )
    except (UnicodeError, ValueError, RecursionError, _BadJson):
        fail(code)
    if type(value) is not dict:
        fail(code)
    return value, raw


def exact(
    value: object, required: set[str], code: str, optional: set[str] = frozenset()
) -> dict[str, object]:
    if type(value) is not dict or not required <= set(value) or not set(value) <= required | optional:
        fail(code)
    return value


def text(value: object, code: str, minimum: int = 1, maximum: int = 2048) -> str:
    if (
        type(value) is not str
        or not minimum <= len(value) <= maximum
        or "\x00" in value
        or any(0xD800 <= ord(char) <= 0xDFFF for char in value)
    ):
        fail(code)
    return value


def identifier(value: object, pattern: re.Pattern[str], code: str) -> str:
    result = text(value, code, maximum=64)
    if pattern.fullmatch(result) is None:
        fail(code)
    return result


def digest(value: object, code: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or HASH.fullmatch(value) is None:
        fail(code)
    return value


def day(value: object, code: str) -> date:
    if type(value) is not str or DATE.fullmatch(value) is None:
        fail(code)
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(code)


def inventory(root: Path) -> list[Path]:
    if not isinstance(root, Path):
        fail("invalid_arguments")
    safe_dir(root)
    allowed = {"records", "annotations", "raw", "adjudications", "suggestions"}
    seen: set[str] = set()
    files: list[Path] = []
    total = 0
    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name)
        for entry in entries:
            info = entry.lstat()
            if info.st_file_attributes & REPARSE:
                fail("invalid_inventory")
            if entry.is_dir():
                if entry.name not in allowed:
                    fail("invalid_inventory")
                seen.add(entry.name)
                children = sorted(entry.iterdir(), key=lambda item: item.name)
                if entry.name in {"adjudications", "suggestions"} and children:
                    fail("invalid_inventory")
                for child in children:
                    total += safe_file(child, "invalid_inventory").st_size
                    files.append(child)
            elif entry.name in {"manifest.json", ".gitignore"}:
                total += safe_file(entry, "invalid_inventory").st_size
                files.append(entry)
            else:
                fail("invalid_inventory")
            if len(files) > 22 or total > 8 * 1024 * 1024:
                fail("invalid_inventory")
    except GoldPilotError:
        raise
    except OSError:
        fail("io_failure")
    if not {"records", "annotations", "raw"} <= seen or root / "manifest.json" not in files:
        fail("invalid_inventory")
    if root / ".gitignore" in files and (root / ".gitignore").stat().st_size > 4096:
        fail("invalid_inventory")
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def parse_manifest(root: Path) -> tuple[dict[str, object], bytes]:
    value, raw = load_json(root / "manifest.json", 256 * 1024, "invalid_manifest")
    exact(
        value, {"schema_version", "dataset_id", "purpose", "provenance", "document_count"}, "invalid_manifest"
    )
    identifier(value["dataset_id"], ID64, "invalid_manifest")
    if (
        value["schema_version"] != "gold-pilot-v1"
        or value["purpose"] != "human-annotation-pilot"
        or value["provenance"] not in {"synthetic-fixture", "human-supplied"}
        or type(value["document_count"]) is not int
        or value["document_count"] != 5
    ):
        fail("invalid_manifest")
    return value, raw


def parse_pin(path: Path) -> tuple[SnapshotPin, bytes]:
    value, raw = load_json(path, 16 * 1024, "invalid_pin")
    exact(
        value,
        {"kind", "version", "sha256", "source_url", "release_tag", "commit", "provenance"},
        "invalid_pin",
    )
    try:
        return SnapshotPin(**value), raw
    except TypeError:
        fail("invalid_pin")


def parse_source(value: object) -> dict[str, object]:
    source = exact(
        value,
        {"url", "publisher", "published_date", "retrieved_at", "source_license", "storage_right"},
        "invalid_record",
    )
    url = text(source["url"], "invalid_record")
    parsed = urlsplit(url)
    publisher = text(source["publisher"], "invalid_record", maximum=256)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or any(char.isspace() or ord(char) < 32 for char in url)
        or any(ord(char) < 32 or ord(char) == 127 for char in publisher)
    ):
        fail("invalid_record")
    if day(source["published_date"], "invalid_record") > day(source["retrieved_at"], "invalid_record"):
        fail("invalid_record")
    if source["source_license"] not in {
        "public-domain",
        "cc-by-4.0",
        "cc-by-sa-4.0",
        "publisher-permission",
        "unknown",
    } or source["storage_right"] not in {"repo-allowed", "local-only", "link-only", "prohibited"}:
        fail("invalid_record")
    if source["storage_right"] == "prohibited" or (
        source["source_license"] == "unknown" and source["storage_right"] != "link-only"
    ):
        fail("invalid_record")
    return source


def parse_record(root: Path, path: Path, pin: SnapshotPin) -> _Record:
    value, _ = load_json(path, 256 * 1024, "invalid_record")
    required = {
        "schema_version",
        "id",
        "source",
        "language",
        "tlp",
        "raw",
        "duplicate_group",
        "split",
        "attack",
    }
    exact(value, required, "invalid_record", {"translation_of"})
    record_id = identifier(value["id"], ID64, "invalid_record")
    source = parse_source(value["source"])
    if (
        path.name != f"{record_id}.meta.json"
        or value["schema_version"] != "gold-pilot-v1"
        or value["language"] not in {"vi", "en"}
        or value["tlp"] not in {"TLP:CLEAR", "TLP:GREEN"}
        or value["split"] != "pilot"
    ):
        fail("invalid_record")
    identifier(value["duplicate_group"], ID64, "invalid_record")
    if "translation_of" in value:
        identifier(value["translation_of"], ID64, "invalid_record")
    attack = exact(value["attack"], {"version", "sha256"}, "invalid_record")
    if (
        text(attack["version"], "invalid_record", maximum=64) != pin.version
        or digest(attack["sha256"], "invalid_record") != pin.sha256
    ):
        fail("invalid_record")
    raw = exact(value["raw"], {"present", "sha256"}, "invalid_record")
    if type(raw["present"]) is not bool:
        fail("invalid_record")
    expected = digest(raw["sha256"], "invalid_record", nullable=True)
    raw_path = root / "raw" / f"{record_id}.txt"
    if not raw["present"]:
        if expected is not None or raw_path.exists():
            fail("invalid_record")
        return _Record(value, None, None)
    if expected is None or source["storage_right"] == "link-only":
        fail("invalid_record")
    try:
        normalized = (
            read(raw_path, 512 * 1024, "invalid_raw")
            .decode("utf-8")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
    except UnicodeError:
        fail("invalid_raw")
    text(normalized, "invalid_raw", 0, 512 * 1024)
    if hashlib.sha256(normalized.encode()).hexdigest() != expected:
        fail("invalid_raw")
    return _Record(value, normalized, raw_path)


def evidence_list(value: object, raw: str, expected_ioc=None) -> None:
    if type(value) is not list or not 1 <= len(value) <= 16:
        fail("invalid_annotation")
    seen = set()
    for evidence in value:
        item = exact(evidence, {"start", "end", "quote_sha256"}, "invalid_annotation")
        start, end = item["start"], item["end"]
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(raw)
            or end - start > 2048
        ):
            fail("invalid_annotation")
        marker = (start, end, item["quote_sha256"])
        quote = raw[start:end]
        if marker in seen or hashlib.sha256(quote.encode()).hexdigest() != digest(
            item["quote_sha256"], "invalid_annotation"
        ):
            fail("invalid_annotation")
        seen.add(marker)
        if expected_ioc is not None:
            try:
                actual = normalize(quote)
            except (TypeError, ValueError):
                fail("invalid_annotation")
            if actual != expected_ioc:
                fail("invalid_annotation")


def parse_annotation(path: Path, record: _Record, catalog) -> dict[str, object]:
    value, _ = load_json(path, 256 * 1024, "invalid_annotation")
    required = {
        "schema_version",
        "id",
        "annotator_id",
        "annotated_at",
        "attack_version",
        "raw_sha256",
        "iocs",
        "ttps",
    }
    exact(value, required, "invalid_annotation", {"no_findings"})
    annotator = identifier(value["annotator_id"], ID32, "invalid_annotation")
    record_id = record.value["id"]
    if (
        path.name != f"{record_id}.{annotator}.json"
        or value["schema_version"] != "gold-pilot-v1"
        or value["id"] != record_id
        or record.text is None
    ):
        fail("invalid_annotation")
    if (
        value["attack_version"] != record.value["attack"]["version"]
        or digest(value["raw_sha256"], "invalid_annotation") != record.value["raw"]["sha256"]
        or day(value["annotated_at"], "invalid_annotation")
        < day(record.value["source"]["retrieved_at"], "invalid_annotation")
    ):
        fail("invalid_annotation")
    if (
        type(value["iocs"]) is not list
        or type(value["ttps"]) is not list
        or len(value["iocs"]) > 256
        or len(value["ttps"]) > 256
        or ("no_findings" in value and type(value["no_findings"]) is not bool)
    ):
        fail("invalid_annotation")
    empty = not value["iocs"] and not value["ttps"]
    if (empty and value.get("no_findings") is not True) or (not empty and value.get("no_findings") is True):
        fail("invalid_annotation")
    ioc_seen = set()
    for item in value["iocs"]:
        ioc = exact(item, {"type", "value", "role", "evidence"}, "invalid_annotation")
        if ioc["type"] not in {kind.value for kind in IocType} or ioc["role"] not in {
            "attacker",
            "victim",
            "benign",
        }:
            fail("invalid_annotation")
        declared = text(ioc["value"], "invalid_annotation")
        try:
            normalized = normalize(declared)
        except (TypeError, ValueError):
            fail("invalid_annotation")
        canonical = (normalized.type.value, normalized.value, ioc["role"])
        if canonical != (ioc["type"], declared, ioc["role"]) or canonical in ioc_seen:
            fail("invalid_annotation")
        ioc_seen.add(canonical)
        evidence_list(ioc["evidence"], record.text, normalized)
    ttp_seen = set()
    for item in value["ttps"]:
        ttp = exact(item, {"attack_id", "evidence"}, "invalid_annotation")
        lookup = validate_technique(catalog, ttp["attack_id"])
        if lookup.catalog_status != "active" or ttp["attack_id"] in ttp_seen:
            fail("invalid_technique")
        ttp_seen.add(ttp["attack_id"])
        evidence_list(ttp["evidence"], record.text)
    return value


def agreement(annotations: tuple[dict[str, object], ...], kind: str) -> dict[str, object]:
    if len(annotations) != 2:
        return {"status": "unavailable", "intersection": None, "union": None, "ratio": None}
    if kind == "ioc":
        sets = [
            {
                (item["type"], item["value"], item["role"])
                for item in annotation["iocs"]
                if item["role"] == "attacker"
            }
            for annotation in annotations
        ]
    else:
        sets = [{item["attack_id"] for item in annotation["ttps"]} for annotation in annotations]
    union, intersection = sets[0] | sets[1], sets[0] & sets[1]
    return {
        "status": "available" if union else "both_empty",
        "intersection": len(intersection),
        "union": len(union),
        "ratio": round(len(intersection) / len(union), 6) if union else None,
    }


def record_output(record: _Record) -> dict[str, object]:
    source = record.value["source"]
    reasons = []
    if source["source_license"] == "unknown" or source["storage_right"] == "link-only":
        reasons.append("NEEDS_RIGHTS")
    if record.text is None:
        reasons.append("NEEDS_LOCAL_RAW")
    if len(record.annotations) < 2:
        reasons.append("NEEDS_SECOND_ANNOTATION")
    ready = not reasons
    return {
        "id": record.value["id"],
        "status": "READY_FOR_ADJUDICATION" if ready else "NOT_READY",
        "reasons": reasons,
        "ioc_agreement": agreement(record.annotations if ready else (), "ioc"),
        "ttp_agreement": agreement(record.annotations if ready else (), "ttp"),
        "ttp_catalog_status": "active"
        if any(annotation["ttps"] for annotation in record.annotations)
        else "no_techniques",
        "semantic_status": "unverified",
    }


def cohort(records: list[dict[str, object]]) -> dict[str, object]:
    ready = [item for item in records if item["status"] == "READY_FOR_ADJUDICATION"]

    def combine(kind: str) -> dict[str, object]:
        if not ready:
            return {"status": "unavailable", "intersection": None, "union": None, "ratio": None}
        intersection = sum(item[f"{kind}_agreement"]["intersection"] for item in ready)
        union = sum(item[f"{kind}_agreement"]["union"] for item in ready)
        return {
            "status": "available" if union else "both_empty",
            "intersection": intersection,
            "union": union,
            "ratio": round(intersection / union, 6) if union else None,
        }

    return {
        "evaluated_record_count": len(ready),
        "ioc_agreement": combine("ioc"),
        "ttp_agreement": combine("ttp"),
        "deduplication": "declared-only",
    }


def validate_gold_pilot(dataset: Path, snapshot: Path, pin_path: Path) -> GoldPilotReadiness:
    files = inventory(dataset)
    manifest, _ = parse_manifest(dataset)
    pin, pin_bytes = parse_pin(pin_path)
    if (manifest["provenance"] == "synthetic-fixture") != (pin.kind == "synthetic"):
        fail("invalid_pin")
    snapshot_bytes = read(snapshot, 64 * 1024 * 1024, "invalid_catalog")
    try:
        catalog = load_catalog(snapshot, pin)
    except AttackCatalogError as error:
        if error.code == "snapshot_io_error":
            fail("io_failure")
        fail("invalid_pin" if error.code == "invalid_pin" else "invalid_catalog")
    record_paths = [path for path in files if path.parent.name == "records"]
    if len(record_paths) != 5:
        fail("invalid_inventory")
    records = {}
    for path in record_paths:
        record = parse_record(dataset, path, pin)
        if record.value["id"] in records:
            fail("invalid_record")
        records[record.value["id"]] = record
    for record_id, record in records.items():
        original_id = record.value.get("translation_of")
        if original_id is not None:
            original = records.get(original_id)
            if (
                original is None
                or original_id == record_id
                or original.value.get("translation_of") is not None
                or original.value["duplicate_group"] != record.value["duplicate_group"]
            ):
                fail("invalid_record")
    annotation_paths = [path for path in files if path.parent.name == "annotations"]
    grouped = {record_id: [] for record_id in records}
    for path in annotation_paths:
        record_id = path.name.split(".", 1)[0]
        if record_id not in records:
            fail("invalid_inventory")
        grouped[record_id].append(parse_annotation(path, records[record_id], catalog))
        if len(grouped[record_id]) > 2:
            fail("invalid_annotation")
    rebuilt = {}
    for record_id, record in records.items():
        annotations = tuple(sorted(grouped[record_id], key=lambda item: item["annotator_id"]))
        if len({item["annotator_id"] for item in annotations}) != len(annotations) or (
            record.text is None and annotations
        ):
            fail("invalid_annotation")
        rebuilt[record_id] = _Record(record.value, record.text, record.raw_path, annotations)
    expected = {
        dataset / "manifest.json",
        *record_paths,
        *annotation_paths,
        *(record.raw_path for record in rebuilt.values() if record.raw_path),
    }
    if dataset / ".gitignore" in files:
        expected.add(dataset / ".gitignore")
    if set(files) != expected:
        fail("invalid_inventory")
    outputs = [record_output(rebuilt[key]) for key in sorted(rebuilt)]
    summary = cohort(outputs)
    reasons = ["RECORDS_NOT_READY"] if any(item["status"] == "NOT_READY" for item in outputs) else []
    if not reasons and summary["ioc_agreement"]["union"] + summary["ttp_agreement"]["union"] == 0:
        reasons.append("NO_FINDINGS_ONLY")
    status = "READY_FOR_ADJUDICATION" if not reasons else "NOT_READY"
    fingerprint = [
        [path.relative_to(dataset).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()]
        for path in files
    ]
    dataset_hash = hashlib.sha256(
        json.dumps(fingerprint, ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()
    value = {
        "schema_version": "gold-pilot-readiness-v1",
        "status": status,
        "reasons": reasons,
        "dataset_id": manifest["dataset_id"],
        "provenance": manifest["provenance"],
        "document_count": 5,
        "dataset_input_sha256": dataset_hash,
        "attack_pin_sha256": hashlib.sha256(pin_bytes).hexdigest(),
        "attack_snapshot_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
        "catalog_kind": pin.kind,
        "records": outputs,
        "cohort": summary,
        "limitations": LIMITATIONS,
    }
    payload = (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        + b"\n"
    )
    return GoldPilotReadiness(status, payload, dataset.resolve(), tuple([*files, pin_path, snapshot]))


def same(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=False) == right.resolve(strict=False) or (
            left.exists() and right.exists() and os.path.samefile(left, right)
        )
    except (OSError, ValueError):
        fail("io_failure")


def write_readiness(
    report: GoldPilotReadiness, output: Path, *, protected_inputs: tuple[Path, ...] = ()
) -> WriteResult:
    if (
        type(report) is not GoldPilotReadiness
        or not isinstance(output, Path)
        or type(protected_inputs) is not tuple
    ):
        fail("invalid_arguments")
    safe_dir(output.parent)
    if output.exists() or output.is_symlink():
        fail("unsafe_output")
    resolved = output.resolve(strict=False)
    if resolved == report.dataset_root or report.dataset_root in resolved.parents:
        fail("unsafe_output")
    if any(
        not isinstance(item, Path) or same(output, item)
        for item in (*report.protected_inputs, *protected_inputs)
    ):
        fail("unsafe_output")
    temporary = None
    committed = False
    warning = False
    try:
        descriptor, name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(report.payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)
        committed = True
    except FileExistsError:
        fail("unsafe_output")
    except OSError:
        fail("io_failure")
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                warning = committed
    return WriteResult(cleanup_warning=warning)
