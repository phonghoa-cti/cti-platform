"""Nhập envelope X01 đã có vào hàng chờ W05 mà không sửa payload."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from phonghoa_extractor import store

ENVELOPE_SCHEMA_VERSION = "x01-local-ingest/1.0"
MAX_ENVELOPE_BYTES = 16 * 1024 * 1024
MAX_RAW_BYTES = 8 * 1024 * 1024
MAX_TEXT_CODEPOINTS = 1_000_000
MAX_PAGES = 50
MAX_PAGE_CODEPOINTS = 100_000
MAX_JSON_DEPTH = 64
PDF_SEPARATOR = "\n\f\n"
ROOT_KEYS = {"schema_version", "input", "draft"}
INPUT_KEYS = {
    "format",
    "display_name",
    "raw_sha256",
    "raw_bytes",
    "canonical_text_sha256",
    "page_count",
    "page_text_ranges",
}


class IngestEnvelopeError(store.DraftInputError):
    """Lỗi envelope đóng, chỉ mang mã an toàn cho CLI."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class IngestWriteError(store.DraftSQLiteError):
    """Schema hợp lệ nhưng transaction nhập đã thất bại."""


@dataclass(frozen=True)
class IngestProvenance:
    draft_id: int
    envelope_schema_version: str
    envelope_sha256: str
    input_format: Literal["text", "pdf"]
    display_name: str
    raw_sha256: str
    raw_bytes: int
    canonical_text_sha256: str
    page_count: int | None
    page_text_ranges: tuple[tuple[int, int], ...] | None


@dataclass(frozen=True)
class IngestQueueResult:
    draft_id: int
    result: Literal["imported", "duplicate"]


class _DuplicateKey(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey
        result[key] = value
    return result


def _reject_nonfinite(_value: str) -> None:
    raise ValueError("nonfinite")


def _validate_json_tree(value: Any, depth: int = 0, active: set[int] | None = None) -> None:
    active = set() if active is None else active
    if isinstance(value, str):
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise IngestEnvelopeError("invalid_utf8") from exc
        return
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise IngestEnvelopeError("invalid_json")
        return
    if type(value) not in {dict, list}:
        raise IngestEnvelopeError("invalid_envelope")
    if depth + 1 > MAX_JSON_DEPTH:
        raise IngestEnvelopeError("json_too_deep")
    identity = id(value)
    if identity in active:
        raise IngestEnvelopeError("invalid_envelope")
    active.add(identity)
    try:
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise IngestEnvelopeError("invalid_envelope")
                _validate_json_tree(key, depth + 1, active)
                _validate_json_tree(item, depth + 1, active)
        else:
            for item in value:
                _validate_json_tree(item, depth + 1, active)
    finally:
        active.remove(identity)


def _has_unc_prefix(path: Path) -> bool:
    return str(path).startswith(("\\\\", "//"))


def _validate_directory(path: Path) -> None:
    info = path.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & reparse:
        raise OSError("reparse")
    if not stat.S_ISDIR(info.st_mode):
        raise OSError("not-directory")


def _validate_regular_local(path: Path) -> None:
    if _has_unc_prefix(path) or (path.drive and not path.is_absolute()):
        raise OSError("network-or-drive-relative")
    if path.is_absolute():
        current = Path(path.anchor)
        _validate_directory(current)
        parts = path.parts[1:-1]
    else:
        current = Path.cwd()
        if _has_unc_prefix(current):
            raise OSError("network-cwd")
        for ancestor in (current, *current.parents):
            _validate_directory(ancestor)
        parts = path.parts[:-1]
    for part in parts:
        if part in {"", "."}:
            continue
        current = current.parent if part == ".." else current / part
        _validate_directory(current)
    info = path.lstat()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (
        stat.S_ISLNK(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & reparse
        or not stat.S_ISREG(info.st_mode)
    ):
        raise OSError("not-regular")


def paths_refer_to_same_file(first: Path, second: Path) -> bool:
    try:
        return os.path.samefile(first, second)
    except OSError:
        return first.resolve(strict=False) == second.resolve(strict=False)


def load_ingest_envelope(path: str | Path) -> dict[str, Any]:
    """Đọc một lần file envelope local với cap cứng và JSON strict."""

    file_path = Path(path)
    try:
        _validate_regular_local(file_path)
        with file_path.open("rb") as handle:
            raw = handle.read(MAX_ENVELOPE_BYTES + 1)
    except OSError as exc:
        raise IngestEnvelopeError("envelope_read_failed") from exc
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise IngestEnvelopeError("envelope_too_large")
    try:
        decoded = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise IngestEnvelopeError("invalid_utf8") from exc
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except _DuplicateKey as exc:
        raise IngestEnvelopeError("duplicate_json_key") from exc
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise IngestEnvelopeError("invalid_json") from exc
    _validate_json_tree(value)
    if type(value) is not dict:
        raise IngestEnvelopeError("invalid_envelope")
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise IngestEnvelopeError("invalid_envelope") from exc


def _valid_name(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and all(char not in "/\\" and ord(char) >= 32 and ord(char) != 127 for char in value)
    )


def _validate_input_metadata(input_value: Any, draft: dict[str, Any]) -> dict[str, Any]:
    if type(input_value) is not dict or set(input_value) != INPUT_KEYS:
        raise IngestEnvelopeError("invalid_input_metadata")
    input_format = input_value["format"]
    display_name = input_value["display_name"]
    raw_hash = input_value["raw_sha256"]
    raw_bytes = input_value["raw_bytes"]
    canonical_hash = input_value["canonical_text_sha256"]
    if input_format not in {"text", "pdf"} or not _valid_name(display_name):
        raise IngestEnvelopeError("invalid_input_metadata")
    if not isinstance(raw_hash, str) or store.SHA256_RE.fullmatch(raw_hash) is None:
        raise IngestEnvelopeError("invalid_input_metadata")
    if type(raw_bytes) is not int or not 0 <= raw_bytes <= MAX_RAW_BYTES:
        raise IngestEnvelopeError("invalid_input_metadata")
    if not isinstance(canonical_hash, str) or store.SHA256_RE.fullmatch(canonical_hash) is None:
        raise IngestEnvelopeError("invalid_input_metadata")
    source = draft.get("source")
    text = draft.get("text")
    if type(source) is not dict or type(text) is not str:
        raise IngestEnvelopeError("invalid_draft")
    try:
        encoded = text.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise IngestEnvelopeError("invalid_utf8") from exc
    if len(text) > MAX_TEXT_CODEPOINTS:
        raise IngestEnvelopeError("invalid_provenance")
    if (
        display_name != source.get("name")
        or canonical_hash != source.get("sha256")
        or canonical_hash != hashlib.sha256(encoded).hexdigest()
    ):
        raise IngestEnvelopeError("invalid_provenance")

    page_count = input_value["page_count"]
    ranges = input_value["page_text_ranges"]
    if input_format == "text":
        if page_count is not None or ranges is not None:
            raise IngestEnvelopeError("invalid_provenance")
        if raw_hash != canonical_hash or raw_bytes != len(encoded):
            raise IngestEnvelopeError("invalid_provenance")
        return input_value
    if type(page_count) is not int or not 1 <= page_count <= MAX_PAGES:
        raise IngestEnvelopeError("invalid_provenance")
    if type(ranges) is not list or len(ranges) != page_count:
        raise IngestEnvelopeError("invalid_provenance")
    normalized: list[tuple[int, int]] = []
    for value in ranges:
        if type(value) is not list or len(value) != 2 or any(type(part) is not int for part in value):
            raise IngestEnvelopeError("invalid_provenance")
        start, end = value
        if not 0 <= start <= end <= len(text) or end - start > MAX_PAGE_CODEPOINTS:
            raise IngestEnvelopeError("invalid_provenance")
        normalized.append((start, end))
    if normalized[0][0] != 0 or normalized[-1][1] != len(text):
        raise IngestEnvelopeError("invalid_provenance")
    if any(
        text[left[1] : right[0]] != PDF_SEPARATOR
        for left, right in zip(normalized, normalized[1:], strict=False)
    ):
        raise IngestEnvelopeError("invalid_provenance")
    if not any(text[start:end].strip() for start, end in normalized):
        raise IngestEnvelopeError("invalid_provenance")
    return input_value


def _validate_envelope(envelope: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    if not isinstance(envelope, Mapping):
        raise IngestEnvelopeError("invalid_envelope")
    value = dict(envelope)
    _validate_json_tree(value)
    if set(value) != ROOT_KEYS or value.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        raise IngestEnvelopeError("invalid_envelope")
    draft = value.get("draft")
    if type(draft) is not dict:
        raise IngestEnvelopeError("invalid_draft")
    _validate_input_metadata(value.get("input"), draft)
    try:
        store._validate_draft(draft)
    except store.DraftStoreError as exc:
        raise IngestEnvelopeError("invalid_draft") from exc
    serialized = _canonical_json(value)
    return value, hashlib.sha256(serialized.encode("utf-8", "strict")).hexdigest()


def _validate_database_path(path: Path) -> None:
    try:
        _validate_regular_local(path)
    except OSError as exc:
        raise store.DraftSQLiteError("Database local existing regular không hợp lệ") from exc


def _provenance_values(envelope: dict[str, Any], digest: str) -> tuple[Any, ...]:
    input_value = envelope["input"]
    ranges = input_value["page_text_ranges"]
    ranges_json = None if ranges is None else json.dumps(ranges, separators=(",", ":"))
    return (
        envelope["schema_version"],
        digest,
        input_value["format"],
        input_value["display_name"],
        input_value["raw_sha256"],
        input_value["raw_bytes"],
        input_value["canonical_text_sha256"],
        input_value["page_count"],
        ranges_json,
    )


def _decode_provenance(row: tuple[Any, ...], payload: dict[str, Any]) -> IngestProvenance:
    draft_id, schema, digest, input_format, name, raw_hash, raw_bytes, canonical, count, ranges_json = row
    try:
        ranges = None if ranges_json is None else json.loads(ranges_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise store.DraftSQLiteError("Provenance ranges JSON không hợp lệ") from exc
    input_value = {
        "format": input_format,
        "display_name": name,
        "raw_sha256": raw_hash,
        "raw_bytes": raw_bytes,
        "canonical_text_sha256": canonical,
        "page_count": count,
        "page_text_ranges": ranges,
    }
    envelope = {"schema_version": schema, "input": input_value, "draft": payload}
    try:
        validated, expected = _validate_envelope(envelope)
    except IngestEnvelopeError as exc:
        raise store.DraftSQLiteError("Provenance row không hợp lệ") from exc
    if expected != digest or not store._is_int(draft_id) or draft_id < 1:
        raise store.DraftSQLiteError("Provenance envelope hash/draft_id không hợp lệ")
    normalized_ranges = validated["input"]["page_text_ranges"]
    return IngestProvenance(
        draft_id=draft_id,
        envelope_schema_version=schema,
        envelope_sha256=digest,
        input_format=input_format,
        display_name=name,
        raw_sha256=raw_hash,
        raw_bytes=raw_bytes,
        canonical_text_sha256=canonical,
        page_count=count,
        page_text_ranges=(
            None if normalized_ranges is None else tuple(tuple(item) for item in normalized_ranges)
        ),
    )


def save_ingested_envelope(
    db_path: str | Path,
    envelope: Mapping[str, Any],
    *,
    created_by_subject: str,
    timeout: float = 5.0,
) -> IngestQueueResult:
    """Migrate rồi ghi draft+provenance trong một transaction riêng."""

    timeout = store._validate_timeout(timeout)
    creator = store._validate_subject(created_by_subject, "created_by_subject")
    validated, digest = _validate_envelope(envelope)
    path = Path(db_path)
    _validate_database_path(path)
    connection: sqlite3.Connection | None = None
    writing = False
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=rw", uri=True, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        store._migrate_connection(connection)
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("PRAGMA user_version").fetchone()[0] != store.STORE_SCHEMA_VERSION:
            raise store.DraftSQLiteError("Database chưa ở schema v3")
        store._validate_v3_schema(connection)
        row = connection.execute(
            "SELECT p.draft_id,p.envelope_schema_version,p.envelope_sha256,p.input_format,"
            "p.display_name,p.raw_sha256,p.raw_bytes,p.canonical_text_sha256,p.page_count,"
            "p.page_text_ranges_json,d.payload_json,d.created_by_subject "
            "FROM draft_ingest_provenance p JOIN drafts d ON d.id=p.draft_id "
            "WHERE p.envelope_sha256=?",
            (digest,),
        ).fetchone()
        if row is not None:
            try:
                payload = json.loads(row[10])
            except (TypeError, json.JSONDecodeError) as exc:
                raise store.DraftSQLiteError("Payload draft provenance không hợp lệ") from exc
            provenance = _decode_provenance(row[:10], payload)
            if row[11] != creator:
                raise store.DraftConflictError("Envelope đã thuộc creator khác")
            connection.rollback()
            return IngestQueueResult(provenance.draft_id, "duplicate")

        draft = validated["draft"]
        writing = True
        payload = _canonical_json(draft)
        cursor = connection.execute(
            "INSERT INTO drafts (created_at,payload_json,schema_version,status,source_sha256,"
            "created_by_subject) VALUES (?,?,?,?,?,?)",
            (
                datetime.now(UTC).isoformat(),
                payload,
                store.SCHEMA_VERSION,
                store.PENDING_STATUS,
                draft["source"]["sha256"],
                creator,
            ),
        )
        draft_id = cursor.lastrowid
        if draft_id is None:
            raise store.DraftSQLiteError("SQLite không trả draft_id")
        connection.execute(
            "INSERT INTO draft_ingest_provenance (draft_id,envelope_schema_version,"
            "envelope_sha256,input_format,display_name,raw_sha256,raw_bytes,"
            "canonical_text_sha256,page_count,page_text_ranges_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (draft_id, *_provenance_values(validated, digest)),
        )
        store._commit(connection)
        return IngestQueueResult(draft_id, "imported")
    except store.DraftStoreError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        error_type = IngestWriteError if writing else store.DraftSQLiteError
        raise error_type("Lỗi SQLite ingest") from exc
    finally:
        if connection is not None:
            connection.close()


def get_ingest_provenance(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> IngestProvenance:
    """Đọc provenance mode=ro trong cùng snapshot với payload draft."""

    timeout = store._validate_timeout(timeout)
    if not store._is_int(draft_id) or not 1 <= draft_id <= store.SQLITE_MAX_INTEGER:
        raise store.DraftInputError("draft_id phải là số nguyên dương")
    path = Path(db_path)
    _validate_database_path(path)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=timeout)
        connection.execute("BEGIN")
        if connection.execute("PRAGMA user_version").fetchone()[0] != store.STORE_SCHEMA_VERSION:
            raise store.DraftSQLiteError("Provenance yêu cầu schema v3")
        store._validate_v3_schema(connection)
        row = connection.execute(
            "SELECT p.draft_id,p.envelope_schema_version,p.envelope_sha256,p.input_format,"
            "p.display_name,p.raw_sha256,p.raw_bytes,p.canonical_text_sha256,p.page_count,"
            "p.page_text_ranges_json,d.payload_json FROM draft_ingest_provenance p "
            "JOIN drafts d ON d.id=p.draft_id WHERE p.draft_id=?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise store.DraftNotFoundError("Draft không có ingest provenance")
        try:
            payload = json.loads(row[10])
        except (TypeError, json.JSONDecodeError) as exc:
            raise store.DraftSQLiteError("Payload draft provenance không hợp lệ") from exc
        return _decode_provenance(row[:10], payload)
    except store.DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise store.DraftSQLiteError("Lỗi đọc SQLite provenance") from exc
    finally:
        if connection is not None:
            connection.close()
