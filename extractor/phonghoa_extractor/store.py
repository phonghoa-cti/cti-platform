"""Lưu và đọc bản nháp pending trong SQLite cục bộ."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from phonghoa_core.ioc import normalize
from phonghoa_extractor.evidence import find_ioc_occurrences

SCHEMA_VERSION = "1.0"
PENDING_STATUS = "pending"
TLP_VALUES = {"TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}
TOP_LEVEL_KEYS = {
    "schema_version",
    "status",
    "source",
    "language",
    "tlp",
    "text",
    "items",
    "injection_warning",
    "findings",
    "model",
    "cost_tokens",
}
ITEM_KEYS = {"kind", "type", "value", "span", "evidence", "keep", "warning", "status"}
FINDING_KEYS = {"paragraph", "rule", "excerpt"}
SOURCE_KEYS = {"name", "sha256"}
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SQLITE_MAX_INTEGER = 2**63 - 1
SELECTION_SCHEMA_VERSION = 2
STORE_SCHEMA_VERSION = 3
REVIEW_STATUSES = {"pending", "approved", "rejected"}
ALLOWED_REVIEW_ROLES = {"analyst", "admin"}
LEGACY_DRAFT_COLUMNS = {
    "id",
    "created_at",
    "payload_json",
    "schema_version",
    "status",
    "source_sha256",
}
REVIEW_DRAFT_COLUMNS = LEGACY_DRAFT_COLUMNS | {
    "created_by_subject",
    "review_status",
    "review_version",
    "decided_by_subject",
    "decided_at",
    "decision_reason",
}
SELECTION_DRAFT_COLUMNS = REVIEW_DRAFT_COLUMNS | {"selection_version"}
AUDIT_COLUMNS = {
    "id",
    "draft_id",
    "action",
    "at",
    "actor_subject",
    "expected_version",
    "previous_status",
    "new_status",
    "previous_version",
    "new_version",
    "reason",
    "selection_version",
    "selected_indices_json",
    "selected_sha256",
}
SELECTION_AUDIT_COLUMNS = {
    "id",
    "draft_id",
    "selection_version",
    "review_version",
    "action",
    "at",
    "actor_subject",
    "selected_indices_json",
    "selected_sha256",
}
INGEST_PROVENANCE_COLUMNS = {
    "draft_id",
    "envelope_schema_version",
    "envelope_sha256",
    "input_format",
    "display_name",
    "raw_sha256",
    "raw_bytes",
    "canonical_text_sha256",
    "page_count",
    "page_text_ranges_json",
}


class DraftStoreError(ValueError):
    """Lỗi dữ liệu hoặc lỗi SQLite có thể trình bày cho người dùng CLI."""


class DraftInputError(DraftStoreError):
    """Đầu vào API lõi không hợp lệ."""


class DraftPolicyError(DraftStoreError):
    """Actor không được phép thực hiện quyết định."""


class DraftNotFoundError(DraftStoreError):
    """Database hoặc draft không tồn tại."""


class DraftDatabaseNotFoundError(DraftNotFoundError):
    """Database không tồn tại; API v1 phân biệt với draft không tồn tại."""


class DraftConflictError(DraftStoreError):
    """Draft đã thay đổi so với phiên bản caller mong đợi."""


class DraftSQLiteError(DraftStoreError):
    """Schema hoặc thao tác SQLite thất bại."""


@dataclass(frozen=True)
class Actor:
    """Danh tính opaque đã được caller tin cậy cung cấp cho policy offline."""

    subject: str
    roles: frozenset[str]


@dataclass(frozen=True)
class DraftReviewResult:
    """Kết quả quyết định cục bộ; không biểu thị đã nhập OpenCTI."""

    draft_id: int
    status: Literal["approved", "rejected"]
    version: int
    decided_by_subject: str
    decided_at: str
    reason: str | None


@dataclass(frozen=True)
class DraftSelectionResult:
    """Snapshot lựa chọn IOC hiệu lực của một draft."""

    draft_id: int
    review_version: int
    selection_version: int
    selected_indices: tuple[int, ...]
    selected_sha256: str
    saved_by_subject: str | None
    saved_at: str | None
    changed: bool
    ai_extracted_count: int
    ai_eligible_count: int
    human_deselected_count: int
    selection_save_count: int


@dataclass(frozen=True)
class DraftReviewSelectionResult:
    """Kết quả quyết định cùng snapshot selection đã ghi vào final audit."""

    draft_id: int
    status: Literal["approved", "rejected"]
    version: int
    decided_by_subject: str
    decided_at: str
    reason: str | None
    selection_version: int
    selected_indices: tuple[int, ...]
    selected_sha256: str


@dataclass(frozen=True)
class ApprovedExportSnapshot:
    """Snapshot final approved tự đủ để tạo artifact STIX ngoại tuyến."""

    draft_id: int
    payload: Mapping[str, Any]
    approved_audit_id: int
    review_version: int
    decided_at: str
    final_selection_version: int
    selected_indices: tuple[int, ...]
    selected_sha256: str
    decided_by_subject: str = field(repr=False)


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise DraftStoreError(f"{label} sai trường: thiếu={missing}, thừa={extra}")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_kept_ioc(item: dict[str, Any], index: int, text: str, start: int, end: int) -> None:
    try:
        expected = normalize(item["value"])
    except ValueError as exc:
        raise DraftStoreError(f"items[{index}].value không phải IOC hợp lệ") from exc
    if item["type"] != expected.type.value:
        raise DraftStoreError(f"items[{index}].type không khớp value")
    occurrences = find_ioc_occurrences(text, expected)
    if not any(start <= token_start and token_end <= end for token_start, token_end in occurrences):
        raise DraftStoreError(f"items[{index}] IOC không nằm trong span evidence")


def _validate_draft(draft: Any) -> None:
    if not isinstance(draft, dict):
        raise DraftStoreError("draft phải là JSON object")
    _require_exact_keys(draft, TOP_LEVEL_KEYS, "draft")
    if draft["schema_version"] != SCHEMA_VERSION:
        raise DraftStoreError(f"schema_version phải là {SCHEMA_VERSION}")
    if draft["status"] != PENDING_STATUS:
        raise DraftStoreError(f"status phải là {PENDING_STATUS}")

    source = draft["source"]
    if not isinstance(source, dict):
        raise DraftStoreError("source phải là object")
    _require_exact_keys(source, SOURCE_KEYS, "source")
    if not isinstance(source["name"], str) or not source["name"]:
        raise DraftStoreError("source.name phải là chuỗi không rỗng")
    if not isinstance(source["sha256"], str) or not SHA256_RE.fullmatch(source["sha256"]):
        raise DraftStoreError("source.sha256 phải là SHA-256 chữ thường")

    text = draft["text"]
    if not isinstance(text, str):
        raise DraftStoreError("text phải là chuỗi")
    expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if source["sha256"] != expected_hash:
        raise DraftStoreError("source.sha256 không khớp text")
    if not isinstance(draft["language"], str) or draft["language"] not in {"vi", "en"}:
        raise DraftStoreError("language phải là vi hoặc en")
    if not isinstance(draft["tlp"], str) or draft["tlp"] not in TLP_VALUES:
        raise DraftStoreError("tlp không hợp lệ")
    if not isinstance(draft["injection_warning"], bool):
        raise DraftStoreError("injection_warning phải là boolean")
    if not isinstance(draft["model"], str) or not draft["model"]:
        raise DraftStoreError("model phải là chuỗi không rỗng")
    if not _is_int(draft["cost_tokens"]) or draft["cost_tokens"] < 0:
        raise DraftStoreError("cost_tokens phải là số nguyên không âm")

    findings = draft["findings"]
    if not isinstance(findings, list):
        raise DraftStoreError("findings phải là list")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise DraftStoreError(f"findings[{index}] phải là object")
        _require_exact_keys(finding, FINDING_KEYS, f"findings[{index}]")
        if not _is_int(finding["paragraph"]) or finding["paragraph"] < 1:
            raise DraftStoreError(f"findings[{index}].paragraph không hợp lệ")
        if not all(isinstance(finding[key], str) for key in ("rule", "excerpt")):
            raise DraftStoreError(f"findings[{index}] chứa giá trị không phải chuỗi")

    items = draft["items"]
    if not isinstance(items, list):
        raise DraftStoreError("items phải là list")
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise DraftStoreError(f"items[{index}] phải là object")
        _require_exact_keys(item, ITEM_KEYS, f"items[{index}]")
        for key in ("kind", "type", "value", "evidence", "status"):
            if not isinstance(item[key], str):
                raise DraftStoreError(f"items[{index}].{key} phải là chuỗi")
        if not isinstance(item["keep"], bool):
            raise DraftStoreError(f"items[{index}].keep phải là boolean")
        if item["warning"] is not None and not isinstance(item["warning"], str):
            raise DraftStoreError(f"items[{index}].warning phải là chuỗi hoặc null")
        span = item["span"]
        if span is None:
            if item["keep"]:
                raise DraftStoreError(f"items[{index}] keep=true phải có span")
            continue
        if not isinstance(span, list) or len(span) != 2 or not all(_is_int(part) for part in span):
            raise DraftStoreError(f"items[{index}].span phải là [start, end]")
        start, end = span
        if start < 0 or end < start or end > len(text):
            raise DraftStoreError(f"items[{index}].span ngoài phạm vi text")
        if text[start:end] != item["evidence"]:
            raise DraftStoreError(f"items[{index}].span không khớp evidence")
        if item["keep"] and item["kind"] == "ioc":
            _validate_kept_ioc(item, index, text, start, end)


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _table_info(connection: sqlite3.Connection, table: str) -> dict[str, tuple[Any, ...]]:
    return {row[1]: row for row in connection.execute(f"PRAGMA table_info({table})")}


def _table_sql(connection: sqlite3.Connection, table: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    if row is None or not isinstance(row[0], str):
        raise DraftSQLiteError(f"Schema thiếu bảng {table}")
    return " ".join(row[0].lower().split())


def _has_check(table_sql: str, expression: str) -> bool:
    return re.search(rf"check\s*\(\s*{expression}\s*\)", table_sql) is not None


def _index_columns(connection: sqlite3.Connection, index_name: str) -> list[tuple[str, int]]:
    quoted_name = index_name.replace('"', '""')
    return [
        (row[2], row[3]) for row in connection.execute(f'PRAGMA index_xinfo("{quoted_name}")') if row[5] == 1
    ]


def _has_unique_draft_audit_index(connection: sqlite3.Connection) -> bool:
    for row in connection.execute("PRAGMA index_list(draft_audit)"):
        _, name, unique, _, partial = row
        if unique == 1 and partial == 0 and _index_columns(connection, name) == [("draft_id", 0)]:
            return True
    return False


def _has_audit_foreign_key(connection: sqlite3.Connection) -> bool:
    foreign_keys: dict[int, list[tuple[str, str, str]]] = {}
    for row in connection.execute("PRAGMA foreign_key_list(draft_audit)"):
        foreign_keys.setdefault(row[0], []).append((row[2], row[3], row[4]))

    return len(foreign_keys) == 1 and next(iter(foreign_keys.values())) == [("drafts", "draft_id", "id")]


def _has_queue_index(connection: sqlite3.Connection) -> bool:
    for row in connection.execute("PRAGMA index_list(drafts)"):
        _, name, unique, _, partial = row
        if name == "idx_drafts_review_queue":
            return (
                unique == 0
                and partial == 0
                and _index_columns(connection, name)
                == [
                    ("review_status", 0),
                    ("id", 1),
                ]
            )
    return False


def _has_unique_index(connection: sqlite3.Connection, table: str, columns: list[str]) -> bool:
    for row in connection.execute(f'PRAGMA index_list("{table}")'):
        _, name, unique, _, partial = row
        if unique == 1 and partial == 0:
            actual = [column for column, _ in _index_columns(connection, name)]
            if actual == columns:
                return True
    return False


def _has_selection_foreign_key(connection: sqlite3.Connection) -> bool:
    rows = list(connection.execute("PRAGMA foreign_key_list(draft_selection_audit)"))
    return len(rows) == 1 and (rows[0][2], rows[0][3], rows[0][4]) == (
        "drafts",
        "draft_id",
        "id",
    )


def _has_provenance_foreign_key(connection: sqlite3.Connection) -> bool:
    rows = list(connection.execute("PRAGMA foreign_key_list(draft_ingest_provenance)"))
    return len(rows) == 1 and (rows[0][2], rows[0][3], rows[0][4]) == (
        "drafts",
        "draft_id",
        "id",
    )


def _commit(connection: sqlite3.Connection) -> None:
    """Điểm commit nhỏ để test chứng minh rollback khi commit thất bại."""

    connection.commit()


def _create_current_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            status TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            created_by_subject TEXT,
            review_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (review_status IN ('pending', 'approved', 'rejected')),
            review_version INTEGER NOT NULL DEFAULT 0 CHECK (review_version >= 0),
            selection_version INTEGER NOT NULL DEFAULT 0 CHECK (selection_version >= 0),
            decided_by_subject TEXT,
            decided_at TEXT,
            decision_reason TEXT
        )
        """
    )


def _create_audit_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS draft_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL UNIQUE REFERENCES drafts(id),
            action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
            at TEXT NOT NULL,
            actor_subject TEXT NOT NULL,
            expected_version INTEGER NOT NULL,
            previous_status TEXT NOT NULL,
            new_status TEXT NOT NULL,
            previous_version INTEGER NOT NULL,
            new_version INTEGER NOT NULL,
            reason TEXT,
            selection_version INTEGER,
            selected_indices_json TEXT,
            selected_sha256 TEXT
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_drafts_review_queue ON drafts(review_status, id DESC)")


def _create_selection_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS draft_selection_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL REFERENCES drafts(id),
            selection_version INTEGER NOT NULL,
            review_version INTEGER NOT NULL,
            action TEXT NOT NULL CHECK (action = 'save_selection'),
            at TEXT NOT NULL,
            actor_subject TEXT NOT NULL,
            selected_indices_json TEXT NOT NULL,
            selected_sha256 TEXT NOT NULL,
            UNIQUE(draft_id, selection_version),
            UNIQUE(draft_id, review_version)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_draft_selection_audit_draft_version "
        "ON draft_selection_audit(draft_id, selection_version DESC)"
    )


def _create_provenance_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE draft_ingest_provenance (
            draft_id INTEGER PRIMARY KEY REFERENCES drafts(id),
            envelope_schema_version TEXT NOT NULL,
            envelope_sha256 TEXT NOT NULL UNIQUE,
            input_format TEXT NOT NULL CHECK (input_format IN ('text','pdf')),
            display_name TEXT NOT NULL,
            raw_sha256 TEXT NOT NULL,
            raw_bytes INTEGER NOT NULL,
            canonical_text_sha256 TEXT NOT NULL,
            page_count INTEGER,
            page_text_ranges_json TEXT
        )
        """
    )


def _validate_v1_schema(connection: sqlite3.Connection) -> None:
    drafts_info = _table_info(connection, "drafts")
    audit_info = _table_info(connection, "draft_audit")
    if set(drafts_info) != REVIEW_DRAFT_COLUMNS:
        raise DraftSQLiteError("Schema drafts review bị hỏng hoặc không được hỗ trợ")
    if set(audit_info) != AUDIT_COLUMNS - {
        "selection_version",
        "selected_indices_json",
        "selected_sha256",
    }:
        raise DraftSQLiteError("Schema draft_audit bị hỏng hoặc không được hỗ trợ")
    drafts_sql = _table_sql(connection, "drafts")
    audit_sql = _table_sql(connection, "draft_audit")
    review_status = drafts_info["review_status"]
    review_version = drafts_info["review_version"]
    if review_status[3] != 1 or review_status[4] != "'pending'":
        raise DraftSQLiteError("Schema review_status thiếu NOT NULL/DEFAULT")
    if review_version[3] != 1 or review_version[4] != "0":
        raise DraftSQLiteError("Schema review_version thiếu NOT NULL/DEFAULT")
    if not _has_check(
        drafts_sql,
        r"review_status\s+in\s*\(\s*'pending'\s*,\s*'approved'\s*,\s*'rejected'\s*\)",
    ) or not _has_check(drafts_sql, r"review_version\s*>=\s*0"):
        raise DraftSQLiteError("Schema drafts thiếu CHECK review state/version")
    if audit_info["draft_id"][3] != 1 or audit_info["action"][3] != 1:
        raise DraftSQLiteError("Schema draft_audit thiếu NOT NULL")
    if not _has_check(audit_sql, r"action\s+in\s*\(\s*'approve'\s*,\s*'reject'\s*\)"):
        raise DraftSQLiteError("Schema draft_audit thiếu CHECK action")
    if not _has_unique_draft_audit_index(connection):
        raise DraftSQLiteError("Schema draft_audit thiếu UNIQUE draft_id")
    if not _has_audit_foreign_key(connection):
        raise DraftSQLiteError("Schema draft_audit thiếu FK draft_id")
    if not _has_queue_index(connection):
        raise DraftSQLiteError("Schema drafts thiếu index review queue")


def _validate_v2_schema(connection: sqlite3.Connection) -> None:
    drafts_info = _table_info(connection, "drafts")
    audit_info = _table_info(connection, "draft_audit")
    selection_info = _table_info(connection, "draft_selection_audit")
    if set(drafts_info) != SELECTION_DRAFT_COLUMNS:
        raise DraftSQLiteError("Schema drafts selection bị hỏng hoặc không được hỗ trợ")
    if set(audit_info) != AUDIT_COLUMNS:
        raise DraftSQLiteError("Schema draft_audit selection bị hỏng hoặc không được hỗ trợ")
    if set(selection_info) != SELECTION_AUDIT_COLUMNS:
        raise DraftSQLiteError("Schema draft_selection_audit bị hỏng hoặc không được hỗ trợ")
    _validate_common_review_schema(connection, drafts_info, audit_info)
    selection_sql = _table_sql(connection, "draft_selection_audit")
    required_selection_columns = SELECTION_AUDIT_COLUMNS - {"id"}
    if any(selection_info[column][3] != 1 for column in required_selection_columns):
        raise DraftSQLiteError("Schema selection audit thiếu NOT NULL bắt buộc")
    selection_version = drafts_info["selection_version"]
    if selection_version[3] != 1 or selection_version[4] != "0":
        raise DraftSQLiteError("Schema selection_version thiếu NOT NULL/DEFAULT")
    if not _has_check(_table_sql(connection, "drafts"), r"selection_version\s*>=\s*0"):
        raise DraftSQLiteError("Schema drafts thiếu CHECK selection_version")
    if not _has_check(selection_sql, r"action\s*=\s*'save_selection'"):
        raise DraftSQLiteError("Schema selection audit thiếu CHECK action")
    if not _has_unique_index(connection, "draft_selection_audit", ["draft_id", "selection_version"]):
        raise DraftSQLiteError("Schema selection audit thiếu UNIQUE selection version")
    if not _has_unique_index(connection, "draft_selection_audit", ["draft_id", "review_version"]):
        raise DraftSQLiteError("Schema selection audit thiếu UNIQUE review version")
    if not _has_selection_foreign_key(connection):
        raise DraftSQLiteError("Schema selection audit thiếu FK draft_id")
    if not _has_queue_index(connection):
        raise DraftSQLiteError("Schema drafts thiếu index review queue")
    _validate_v2_audit_rows(connection)


def _validate_v3_schema(connection: sqlite3.Connection) -> None:
    _validate_v2_schema(connection)
    info = _table_info(connection, "draft_ingest_provenance")
    if set(info) != INGEST_PROVENANCE_COLUMNS:
        raise DraftSQLiteError("Schema provenance bị hỏng hoặc không được hỗ trợ")
    required = INGEST_PROVENANCE_COLUMNS - {"draft_id", "page_count", "page_text_ranges_json"}
    if any(info[column][3] != 1 for column in required) or info["draft_id"][5] != 1:
        raise DraftSQLiteError("Schema provenance thiếu NOT NULL/PRIMARY KEY")
    if not _has_unique_index(connection, "draft_ingest_provenance", ["envelope_sha256"]):
        raise DraftSQLiteError("Schema provenance thiếu UNIQUE envelope_sha256")
    if not _has_provenance_foreign_key(connection):
        raise DraftSQLiteError("Schema provenance thiếu FK draft_id")
    table_sql = _table_sql(connection, "draft_ingest_provenance")
    if not _has_check(table_sql, r"input_format\s+in\s*\(\s*'text'\s*,\s*'pdf'\s*\)"):
        raise DraftSQLiteError("Schema provenance thiếu CHECK input_format")
    from phonghoa_extractor.ingest_queue import _decode_provenance

    rows = connection.execute(
        "SELECT p.draft_id,p.envelope_schema_version,p.envelope_sha256,p.input_format,"
        "p.display_name,p.raw_sha256,p.raw_bytes,p.canonical_text_sha256,p.page_count,"
        "p.page_text_ranges_json,d.payload_json FROM draft_ingest_provenance p "
        "JOIN drafts d ON d.id=p.draft_id ORDER BY p.draft_id"
    ).fetchall()
    linked_count = connection.execute("SELECT COUNT(*) FROM draft_ingest_provenance").fetchone()[0]
    if len(rows) != linked_count:
        raise DraftSQLiteError("Provenance có draft_id mồ côi")
    for row in rows:
        try:
            payload = json.loads(row[10])
        except (TypeError, json.JSONDecodeError) as exc:
            raise DraftSQLiteError("Payload provenance không hợp lệ") from exc
        _decode_provenance(row[:10], payload)


def _validate_current_schema(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == SELECTION_SCHEMA_VERSION:
        _validate_v2_schema(connection)
        return
    if version == STORE_SCHEMA_VERSION:
        _validate_v3_schema(connection)
        return
    raise DraftSQLiteError("Schema database không hợp lệ; cần migrate rõ ràng")


def _validate_canonical_indices(serialized: Any, digest: Any) -> tuple[int, ...]:
    try:
        decoded = json.loads(serialized)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DraftSQLiteError("Selection JSON không hợp lệ") from exc
    if (
        not isinstance(decoded, list)
        or any(not _is_int(item) or item < 0 for item in decoded)
        or decoded != sorted(decoded)
        or len(decoded) != len(set(decoded))
    ):
        raise DraftSQLiteError("Selection indices không canonical")
    canonical = json.dumps(decoded, separators=(",", ":"))
    expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if serialized != canonical or digest != expected_hash:
        raise DraftSQLiteError("Selection JSON/hash không canonical")
    return tuple(decoded)


def _validate_v2_audit_rows(connection: sqlite3.Connection) -> None:
    for selection_version, serialized, digest in connection.execute(
        "SELECT selection_version, selected_indices_json, selected_sha256 FROM draft_audit"
    ):
        values = (selection_version, serialized, digest)
        if all(value is None for value in values):
            continue
        if any(value is None for value in values) or not _is_int(selection_version) or selection_version < 0:
            raise DraftSQLiteError("Final audit selection snapshot không hợp lệ")
        _validate_canonical_indices(serialized, digest)
    for selection_version, review_version, serialized, digest in connection.execute(
        "SELECT selection_version, review_version, selected_indices_json, selected_sha256 "
        "FROM draft_selection_audit ORDER BY draft_id, selection_version"
    ):
        if not _is_int(selection_version) or selection_version < 1 or review_version != selection_version:
            raise DraftSQLiteError("Selection audit version không hợp lệ")
        _validate_canonical_indices(serialized, digest)


def _validate_common_review_schema(
    connection: sqlite3.Connection,
    drafts_info: dict[str, tuple[Any, ...]],
    audit_info: dict[str, tuple[Any, ...]],
) -> None:
    drafts_sql = _table_sql(connection, "drafts")
    audit_sql = _table_sql(connection, "draft_audit")
    if drafts_info["review_status"][3] != 1 or drafts_info["review_status"][4] != "'pending'":
        raise DraftSQLiteError("Schema review_status thiếu NOT NULL/DEFAULT")
    if drafts_info["review_version"][3] != 1 or drafts_info["review_version"][4] != "0":
        raise DraftSQLiteError("Schema review_version thiếu NOT NULL/DEFAULT")
    if not _has_check(
        drafts_sql,
        r"review_status\s+in\s*\(\s*'pending'\s*,\s*'approved'\s*,\s*'rejected'\s*\)",
    ):
        raise DraftSQLiteError("Schema drafts thiếu CHECK review state")
    if not _has_check(drafts_sql, r"review_version\s*>=\s*0"):
        raise DraftSQLiteError("Schema drafts thiếu CHECK review version")
    if audit_info["draft_id"][3] != 1 or audit_info["action"][3] != 1:
        raise DraftSQLiteError("Schema draft_audit thiếu NOT NULL")
    if not _has_check(audit_sql, r"action\s+in\s*\(\s*'approve'\s*,\s*'reject'\s*\)"):
        raise DraftSQLiteError("Schema draft_audit thiếu CHECK action")
    if not _has_unique_draft_audit_index(connection) or not _has_audit_foreign_key(connection):
        raise DraftSQLiteError("Schema draft_audit thiếu UNIQUE/FK draft_id")


def _schema_mode(connection: sqlite3.Connection) -> Literal["legacy", "v1", "current"]:
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version > STORE_SCHEMA_VERSION:
        raise DraftSQLiteError(f"Phiên bản database {user_version} chưa được hỗ trợ")
    draft_columns = _table_columns(connection, "drafts")
    if user_version == 0 and draft_columns == LEGACY_DRAFT_COLUMNS:
        return "legacy"
    if user_version == 1:
        _validate_v1_schema(connection)
        return "v1"
    if user_version in {SELECTION_SCHEMA_VERSION, STORE_SCHEMA_VERSION}:
        _validate_current_schema(connection)
        return "current"
    raise DraftSQLiteError("Schema database không hợp lệ; cần migrate rõ ràng")


def _migrate_connection(connection: sqlite3.Connection) -> None:
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version > STORE_SCHEMA_VERSION or user_version not in {0, 1, 2, 3}:
        raise DraftSQLiteError(f"Phiên bản database {user_version} chưa được hỗ trợ")
    if user_version == STORE_SCHEMA_VERSION:
        _validate_v3_schema(connection)
        return

    if user_version in {0, 1}:
        connection.execute("BEGIN IMMEDIATE")
        try:
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
            if user_version in {0, 1}:
                draft_columns = _table_columns(connection, "drafts")
                if user_version == 0 and draft_columns and draft_columns != LEGACY_DRAFT_COLUMNS:
                    raise DraftSQLiteError("Schema drafts legacy bị hỏng hoặc không được hỗ trợ")
                if user_version == 1:
                    _validate_v1_schema(connection)
                if not draft_columns:
                    _create_current_schema(connection)
                    _create_audit_schema(connection)
                    _create_selection_schema(connection)
                elif user_version == 0:
                    connection.execute("ALTER TABLE drafts ADD COLUMN created_by_subject TEXT")
                    connection.execute(
                        "ALTER TABLE drafts ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending' "
                        "CHECK (review_status IN ('pending', 'approved', 'rejected'))"
                    )
                    connection.execute(
                        "ALTER TABLE drafts ADD COLUMN review_version INTEGER NOT NULL DEFAULT 0 "
                        "CHECK (review_version >= 0)"
                    )
                    connection.execute("ALTER TABLE drafts ADD COLUMN decided_by_subject TEXT")
                    connection.execute("ALTER TABLE drafts ADD COLUMN decided_at TEXT")
                    connection.execute("ALTER TABLE drafts ADD COLUMN decision_reason TEXT")
                    _create_audit_schema(connection)
                if draft_columns:
                    connection.execute(
                        "ALTER TABLE drafts ADD COLUMN selection_version INTEGER NOT NULL DEFAULT 0 "
                        "CHECK (selection_version >= 0)"
                    )
                if user_version == 1:
                    connection.execute("ALTER TABLE draft_audit ADD COLUMN selection_version INTEGER")
                    connection.execute("ALTER TABLE draft_audit ADD COLUMN selected_indices_json TEXT")
                    connection.execute("ALTER TABLE draft_audit ADD COLUMN selected_sha256 TEXT")
                _create_selection_schema(connection)
                _validate_v2_schema(connection)
                connection.execute(f"PRAGMA user_version = {SELECTION_SCHEMA_VERSION}")
                _commit(connection)
            else:
                connection.rollback()
        except (sqlite3.Error, DraftStoreError):
            connection.rollback()
            raise

    connection.execute("BEGIN IMMEDIATE")
    try:
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if user_version == SELECTION_SCHEMA_VERSION:
            _validate_v2_schema(connection)
            _create_provenance_schema(connection)
            _validate_v3_schema(connection)
            connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION}")
            _commit(connection)
        elif user_version == STORE_SCHEMA_VERSION:
            _validate_v3_schema(connection)
            connection.rollback()
        else:
            raise DraftSQLiteError(f"Phiên bản database {user_version} chưa được hỗ trợ")
    except (sqlite3.Error, DraftStoreError):
        connection.rollback()
        raise


def _validate_timeout(timeout: Any) -> float:
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise DraftStoreError("timeout phải là số hữu hạn không âm")
    try:
        is_finite = math.isfinite(timeout)
    except OverflowError:
        is_finite = False
    if not is_finite or timeout < 0:
        raise DraftStoreError("timeout phải là số hữu hạn không âm")
    return float(timeout)


def _validate_max_version(max_version: Any) -> int:
    if not _is_int(max_version) or not 0 <= max_version <= SQLITE_MAX_INTEGER:
        raise DraftInputError("max_version phải là số nguyên trong miền INTEGER SQLite")
    return max_version


def _validate_subject(subject: Any, label: str, *, nullable: bool = False) -> str | None:
    if subject is None and nullable:
        return None
    if not isinstance(subject, str) or not subject.strip():
        raise DraftInputError(f"{label} phải là chuỗi không rỗng")
    return subject


def _decode_payload_row(row: tuple[Any, ...]) -> tuple[dict[str, Any], int, str]:
    draft_id, created_at, schema_version, row_status, source_sha256, payload_json = row[:6]
    if not _is_int(draft_id) or draft_id < 1:
        raise DraftStoreError("Metadata draft không hợp lệ")
    try:
        payload = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DraftStoreError(f"Payload draft ID {draft_id} không phải JSON hợp lệ") from exc
    _validate_draft(payload)
    if (
        schema_version != payload["schema_version"]
        or row_status != payload["status"]
        or source_sha256 != payload["source"]["sha256"]
    ):
        raise DraftStoreError(f"Metadata draft ID {draft_id} không khớp payload")
    try:
        created_time = datetime.fromisoformat(created_at)
    except (TypeError, ValueError) as exc:
        raise DraftStoreError(f"created_at của draft ID {draft_id} không hợp lệ") from exc
    if created_time.utcoffset() is None:
        raise DraftStoreError(f"created_at của draft ID {draft_id} phải có múi giờ")
    return payload, draft_id, created_at


def _default_review() -> dict[str, Any]:
    return {
        "status": "pending",
        "version": 0,
        "created_by_subject": None,
        "decided_by_subject": None,
        "decided_at": None,
        "reason": None,
    }


def _decode_review(row: tuple[Any, ...], mode: Literal["legacy", "v1", "current"]) -> dict[str, Any]:
    if mode == "legacy":
        return _default_review()
    created_by, status, version, decided_by, decided_at, reason = row[6:12]
    if created_by is not None:
        _validate_subject(created_by, "created_by_subject")
    if status not in REVIEW_STATUSES or not _is_int(version) or version < 0:
        raise DraftStoreError("Metadata review không hợp lệ")
    if mode == "v1" and version != (0 if status == "pending" else 1):
        raise DraftStoreError("Metadata review v1 không hợp lệ")
    if len(row) >= 13:
        selection_version = row[12]
        if not _is_int(selection_version) or selection_version < 0:
            raise DraftStoreError("Metadata selection version không hợp lệ")
        expected_version = selection_version if status == "pending" else selection_version + 1
        if version != expected_version:
            raise DraftStoreError("Metadata review/selection version không hợp lệ")
    if status == "pending":
        if any(value is not None for value in (decided_by, decided_at, reason)):
            raise DraftStoreError("Metadata review pending không hợp lệ")
    else:
        if version < 1:
            raise DraftStoreError("Metadata review đã quyết định không hợp lệ")
        _validate_subject(decided_by, "decided_by_subject")
        try:
            decided_time = datetime.fromisoformat(decided_at)
        except (TypeError, ValueError) as exc:
            raise DraftStoreError("decided_at không hợp lệ") from exc
        if decided_time.utcoffset() is None:
            raise DraftStoreError("decided_at phải có múi giờ")
        if status == "approved" and reason is not None:
            raise DraftStoreError("Metadata approve không được có reason")
        if status == "rejected" and (not isinstance(reason, str) or not reason.strip()):
            raise DraftStoreError("Metadata reject phải có reason")
    return {
        "status": status,
        "version": version,
        "created_by_subject": created_by,
        "decided_by_subject": decided_by,
        "decided_at": decided_at,
        "reason": reason,
    }


def _decode_draft_row(
    row: tuple[Any, ...], mode: Literal["legacy", "v1", "current"]
) -> tuple[dict[str, Any], int, str, dict[str, Any]]:
    payload, draft_id, created_at = _decode_payload_row(row)
    return payload, draft_id, created_at, _decode_review(row, mode)


def _draft_summary(row: tuple[Any, ...], mode: Literal["legacy", "v1", "current"]) -> dict[str, Any]:
    payload, draft_id, created_at, review = _decode_draft_row(row, mode)
    return {
        "id": draft_id,
        "created_at": created_at,
        "status": payload["status"],
        "source": dict(payload["source"]),
        "language": payload["language"],
        "tlp": payload["tlp"],
        "item_count": len(payload["items"]),
        "injection_warning": payload["injection_warning"],
        "review_status": review["status"],
        "review_version": review["version"],
    }


def migrate_store(db_path: str | Path, *, timeout: float = 5.0) -> None:
    """Nâng database đã tồn tại lên schema review; lần hai không đổi dữ liệu."""

    timeout = _validate_timeout(timeout)
    path = Path(db_path)
    if not path.is_file():
        raise DraftNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        _migrate_connection(connection)
    except DraftStoreError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise DraftSQLiteError(f"Lỗi SQLite migration: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def save_draft(
    db_path: str | Path,
    draft: dict[str, Any],
    *,
    created_by_subject: str | None = None,
    timeout: float = 5.0,
) -> int:
    """Thêm một draft mới và trả ID; không sửa hoặc gộp bản ghi cũ."""

    timeout = _validate_timeout(timeout)
    _validate_draft(draft)
    created_by_subject = _validate_subject(created_by_subject, "created_by_subject", nullable=True)
    path = Path(db_path)
    payload = json.dumps(draft, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    created_at = datetime.now(UTC).isoformat()
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        _migrate_connection(connection)
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """
            INSERT INTO drafts (
                created_at, payload_json, schema_version, status, source_sha256, created_by_subject
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                payload,
                SCHEMA_VERSION,
                PENDING_STATUS,
                draft["source"]["sha256"],
                created_by_subject,
            ),
        )
        draft_id = cursor.lastrowid
        _commit(connection)
        if draft_id is None:
            raise DraftStoreError("SQLite không trả ID cho draft")
        return draft_id
    except DraftStoreError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise DraftSQLiteError(f"Lỗi SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def get_draft(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> dict[str, Any]:
    """Đọc một draft bằng kết nối SQLite chỉ đọc, không tự tạo database."""

    timeout = _validate_timeout(timeout)
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftStoreError("ID phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftStoreError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        mode = _schema_mode(connection)
        is_v2 = connection.execute("PRAGMA user_version").fetchone()[0] >= SELECTION_SCHEMA_VERSION
        review_columns = (
            ", created_by_subject, review_status, review_version, "
            "decided_by_subject, decided_at, decision_reason" + (", selection_version" if is_v2 else "")
            if mode != "legacy"
            else ""
        )
        row = connection.execute(
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json "
            + review_columns
            + " "
            "FROM drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, stored_id, created_at, review = _decode_draft_row(row, mode)
        return {**payload, "id": stored_id, "created_at": created_at, "review": review}
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def list_drafts(
    db_path: str | Path,
    *,
    limit: int = 20,
    before_id: int | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Liệt kê summary draft pending theo ID giảm dần bằng kết nối chỉ đọc."""

    timeout = _validate_timeout(timeout)
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise DraftStoreError("limit phải là số nguyên từ 1 đến 100")
    if before_id is not None and (not _is_int(before_id) or not 1 <= before_id <= SQLITE_MAX_INTEGER):
        raise DraftStoreError("before_id phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftStoreError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        mode = _schema_mode(connection)
        is_v2 = connection.execute("PRAGMA user_version").fetchone()[0] >= SELECTION_SCHEMA_VERSION
        review_columns = (
            ", created_by_subject, review_status, review_version, "
            "decided_by_subject, decided_at, decision_reason" + (", selection_version" if is_v2 else "")
            if mode != "legacy"
            else ""
        )
        query = (
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json "
            + review_columns
            + " FROM drafts WHERE "
            + ("review_status" if mode != "legacy" else "status")
            + " = ?"
        )
        parameters: list[Any] = [PENDING_STATUS]
        if before_id is not None:
            query += " AND id < ?"
            parameters.append(before_id)
        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit + 1)
        rows = connection.execute(query, parameters).fetchall()
        has_more = len(rows) > limit
        items = [_draft_summary(row, mode) for row in rows[:limit]]
        next_before_id = items[-1]["id"] if has_more else None
        return {"items": items, "next_before_id": next_before_id}
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def get_draft_with_selection(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> dict[str, Any]:
    """Đọc detail và selection v2 trong cùng một SQLite snapshot."""

    timeout = _validate_timeout(timeout)
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftInputError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftDatabaseNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=timeout)
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Chức năng selection yêu cầu migrate database lên v2")
        _validate_current_schema(connection)
        connection.execute("BEGIN")
        row = connection.execute(
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json, "
            "created_by_subject, review_status, review_version, decided_by_subject, decided_at, "
            "decision_reason, selection_version FROM drafts WHERE id=?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, stored_id, created_at, review = _decode_draft_row(row, "current")
        selection = _load_effective_selection(
            connection, draft_id, payload, review["status"], review["version"], row[12]
        )
        return {
            **payload,
            "id": stored_id,
            "created_at": created_at,
            "review": review,
            "selection": selection,
        }
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite selection: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def list_drafts_with_selection_version(
    db_path: str | Path,
    *,
    limit: int = 20,
    before_id: int | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Liệt kê pending v2 với selection_version, không đổi contract legacy."""

    timeout = _validate_timeout(timeout)
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise DraftInputError("limit phải là số nguyên từ 1 đến 100")
    if before_id is not None and (not _is_int(before_id) or not 1 <= before_id <= SQLITE_MAX_INTEGER):
        raise DraftInputError("before_id phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftDatabaseNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=timeout)
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Chức năng selection yêu cầu migrate database lên v2")
        _validate_current_schema(connection)
        query = (
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json, "
            "created_by_subject, review_status, review_version, decided_by_subject, decided_at, "
            "decision_reason, selection_version FROM drafts WHERE review_status = ?"
        )
        parameters: list[Any] = [PENDING_STATUS]
        if before_id is not None:
            query += " AND id < ?"
            parameters.append(before_id)
        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit + 1)
        rows = connection.execute(query, parameters).fetchall()
        has_more = len(rows) > limit
        items = [{**_draft_summary(row, "current"), "selection_version": row[12]} for row in rows[:limit]]
        return {"items": items, "next_before_id": items[-1]["id"] if has_more else None}
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite selection: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def _validate_actor(actor: Any) -> Actor:
    if not isinstance(actor, Actor):
        raise DraftInputError("actor phải là Actor")
    _validate_subject(actor.subject, "actor.subject")
    if not isinstance(actor.roles, frozenset) or not all(
        isinstance(role, str) and role for role in actor.roles
    ):
        raise DraftInputError("actor.roles phải là frozenset chuỗi")
    if not actor.roles.intersection(ALLOWED_REVIEW_ROLES):
        raise DraftPolicyError("Actor cần role analyst hoặc admin")
    return actor


def _eligible_ioc_indices(payload: dict[str, Any]) -> tuple[int, ...]:
    _validate_draft(payload)
    return tuple(
        index
        for index, item in enumerate(payload["items"])
        if item["kind"] == "ioc" and item["keep"] is True and item["status"] == "ok"
    )


def _canonical_selection(indices: Sequence[int]) -> tuple[tuple[int, ...], str, str]:
    normalized = tuple(sorted(indices))
    serialized = json.dumps(normalized, separators=(",", ":"))
    return normalized, serialized, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _validate_selection_input(
    draft_id: Any, actor: Any, selected_indices: Any, expected_version: Any
) -> tuple[Actor, tuple[int, ...]]:
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftInputError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    if not _is_int(expected_version) or not 0 <= expected_version <= SQLITE_MAX_INTEGER:
        raise DraftInputError("expected_version phải là số nguyên không âm trong miền INTEGER SQLite")
    actor = _validate_actor(actor)
    if not isinstance(selected_indices, (list, tuple)):
        raise DraftInputError("selected_indices phải là list hoặc tuple")
    if any(not _is_int(index) or not 0 <= index <= SQLITE_MAX_INTEGER for index in selected_indices):
        raise DraftInputError("Mỗi selected index phải là INTEGER SQLite không âm")
    if len(set(selected_indices)) != len(selected_indices):
        raise DraftInputError("selected_indices không được trùng")
    return actor, tuple(sorted(selected_indices))


def _selection_result(
    *,
    draft_id: int,
    payload: dict[str, Any],
    review_version: int,
    selection_version: int,
    selected: tuple[int, ...],
    selected_hash: str,
    saved_by: str | None,
    saved_at: str | None,
    save_count: int,
    changed: bool,
) -> DraftSelectionResult:
    eligible = _eligible_ioc_indices(payload)
    return DraftSelectionResult(
        draft_id=draft_id,
        review_version=review_version,
        selection_version=selection_version,
        selected_indices=selected,
        selected_sha256=selected_hash,
        saved_by_subject=saved_by,
        saved_at=saved_at,
        changed=changed,
        ai_extracted_count=sum(item["kind"] == "ioc" for item in payload["items"]),
        ai_eligible_count=len(eligible),
        human_deselected_count=len(eligible) - len(selected),
        selection_save_count=save_count,
    )


def _load_effective_selection(
    connection: sqlite3.Connection,
    draft_id: int,
    payload: dict[str, Any],
    review_status: str,
    review_version: int,
    selection_version: int,
) -> DraftSelectionResult:
    if not _is_int(selection_version) or selection_version < 0:
        raise DraftSQLiteError("selection_version không hợp lệ")
    expected_review = selection_version if review_status == "pending" else selection_version + 1
    if review_version != expected_review:
        raise DraftSQLiteError("Invariant review/selection version không hợp lệ")
    eligible = _eligible_ioc_indices(payload)
    count = connection.execute(
        "SELECT COUNT(*) FROM draft_selection_audit WHERE draft_id=?", (draft_id,)
    ).fetchone()[0]
    if count != selection_version:
        raise DraftSQLiteError("Lịch sử selection không liên tiếp")
    if selection_version == 0:
        selected, serialized, selected_hash = _canonical_selection(eligible)
        return _selection_result(
            draft_id=draft_id,
            payload=payload,
            review_version=review_version,
            selection_version=0,
            selected=selected,
            selected_hash=selected_hash,
            saved_by=None,
            saved_at=None,
            save_count=0,
            changed=False,
        )
    row = connection.execute(
        "SELECT selection_version, review_version, at, actor_subject, "
        "selected_indices_json, selected_sha256 FROM draft_selection_audit "
        "WHERE draft_id=? ORDER BY selection_version DESC LIMIT 1",
        (draft_id,),
    ).fetchone()
    if row is None or row[0] != selection_version or row[1] != selection_version:
        raise DraftSQLiteError("Selection pointer không khớp event")
    try:
        decoded = json.loads(row[4])
    except (TypeError, json.JSONDecodeError) as exc:
        raise DraftSQLiteError("Selection event JSON không hợp lệ") from exc
    if not isinstance(decoded, list) or any(not _is_int(item) for item in decoded):
        raise DraftSQLiteError("Selection event indices không hợp lệ")
    selected, serialized, selected_hash = _canonical_selection(decoded)
    if list(selected) != decoded or serialized != row[4] or selected_hash != row[5]:
        raise DraftSQLiteError("Selection event canonical/hash không hợp lệ")
    if not set(selected).issubset(eligible):
        raise DraftSQLiteError("Selection event chứa IOC không eligible")
    _validate_subject(row[3], "selection actor")
    try:
        if datetime.fromisoformat(row[2]).utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise DraftSQLiteError("Selection event time không hợp lệ") from exc
    return _selection_result(
        draft_id=draft_id,
        payload=payload,
        review_version=review_version,
        selection_version=selection_version,
        selected=selected,
        selected_hash=selected_hash,
        saved_by=row[3],
        saved_at=row[2],
        save_count=count,
        changed=False,
    )


def get_effective_selection(
    db_path: str | Path, draft_id: int, *, timeout: float = 5.0
) -> DraftSelectionResult:
    """Đọc snapshot selection bằng read transaction, không migrate database."""

    timeout = _validate_timeout(timeout)
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftInputError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=timeout)
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Chức năng selection yêu cầu migrate database lên v2")
        _validate_current_schema(connection)
        connection.execute("BEGIN")
        row = connection.execute(
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json, "
            "created_by_subject, review_status, review_version, decided_by_subject, decided_at, "
            "decision_reason, selection_version FROM drafts WHERE id=?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, _, _, review = _decode_draft_row(row, "current")
        return _load_effective_selection(
            connection, draft_id, payload, review["status"], review["version"], row[12]
        )
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite selection: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def save_selection(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    selected_indices: Sequence[int],
    expected_version: int,
    timeout: float = 5.0,
    max_version: int = SQLITE_MAX_INTEGER,
) -> DraftSelectionResult:
    """Lưu snapshot IOC được chọn và audit trong cùng write transaction."""

    timeout = _validate_timeout(timeout)
    max_version = _validate_max_version(max_version)
    actor, normalized = _validate_selection_input(draft_id, actor, selected_indices, expected_version)
    path = Path(db_path)
    if not path.is_file():
        raise DraftDatabaseNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=rw", uri=True, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Chức năng selection yêu cầu migrate database lên v2")
        _validate_current_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json, "
            "created_by_subject, review_status, review_version, decided_by_subject, decided_at, "
            "decision_reason, selection_version FROM drafts WHERE id=?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, _, _, review = _decode_draft_row(row, "current")
        if review["status"] != "pending" or review["version"] != expected_version:
            raise DraftConflictError("Draft đã kết thúc hoặc expected_version đã stale")
        current = _load_effective_selection(
            connection, draft_id, payload, review["status"], review["version"], row[12]
        )
        eligible = set(_eligible_ioc_indices(payload))
        if not set(normalized).issubset(eligible):
            raise DraftPolicyError("selected_indices chứa IOC không eligible")
        if normalized == current.selected_indices:
            return current
        if expected_version >= max_version or row[12] >= max_version:
            raise DraftConflictError("Version đã đạt giới hạn INTEGER SQLite")
        new_version = expected_version + 1
        new_selection_version = row[12] + 1
        selected, serialized, selected_hash = _canonical_selection(normalized)
        saved_at = datetime.now(UTC).isoformat()
        cursor = connection.execute(
            "UPDATE drafts SET review_version=?, selection_version=? "
            "WHERE id=? AND review_status='pending' AND review_version=?",
            (new_version, new_selection_version, draft_id, expected_version),
        )
        if cursor.rowcount != 1:
            raise DraftConflictError("Draft đã thay đổi trong khi lưu selection")
        connection.execute(
            "INSERT INTO draft_selection_audit "
            "(draft_id, selection_version, review_version, action, at, actor_subject, "
            "selected_indices_json, selected_sha256) VALUES (?, ?, ?, 'save_selection', ?, ?, ?, ?)",
            (
                draft_id,
                new_selection_version,
                new_version,
                saved_at,
                actor.subject,
                serialized,
                selected_hash,
            ),
        )
        _commit(connection)
        return _selection_result(
            draft_id=draft_id,
            payload=payload,
            review_version=new_version,
            selection_version=new_selection_version,
            selected=selected,
            selected_hash=selected_hash,
            saved_by=actor.subject,
            saved_at=saved_at,
            save_count=current.selection_save_count + 1,
            changed=True,
        )
    except DraftStoreError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise DraftSQLiteError(f"Lỗi SQLite selection: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def get_approved_export_snapshot(
    db_path: str | Path, draft_id: int, *, timeout: float = 5.0
) -> ApprovedExportSnapshot:
    """Đọc final approve audit trong một transaction SQLite chỉ đọc, không migrate."""

    timeout = _validate_timeout(timeout)
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftInputError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    path = Path(db_path)
    if not path.is_file():
        raise DraftDatabaseNotFoundError(f"Database không tồn tại: {path}")

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=timeout)
        connection.execute("BEGIN")
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Export yêu cầu database schema v2")
        _validate_current_schema(connection)
        row = connection.execute(
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json, "
            "created_by_subject, review_status, review_version, decided_by_subject, decided_at, "
            "decision_reason, selection_version FROM drafts WHERE id=?",
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, stored_id, _created_at, review = _decode_draft_row(row, "current")
        if review["status"] != "approved" or review["reason"] is not None:
            raise DraftPolicyError("Chỉ export draft final approved không có reason")
        creator = review["created_by_subject"]
        reviewer = review["decided_by_subject"]
        if creator is None or reviewer is None or creator == reviewer:
            raise DraftPolicyError("Final approve phải có người tạo và người duyệt khác nhau")
        selection_version = row[12]
        if review["version"] != selection_version + 1:
            raise DraftSQLiteError("Review version không khớp final selection version")

        audit_rows = connection.execute(
            "SELECT id, action, at, actor_subject, expected_version, previous_status, new_status, "
            "previous_version, new_version, reason, selection_version, selected_indices_json, "
            "selected_sha256 FROM draft_audit WHERE draft_id=?",
            (draft_id,),
        ).fetchall()
        if len(audit_rows) != 1:
            raise DraftSQLiteError("Draft phải có đúng một final approve audit")
        audit = audit_rows[0]
        if not _is_int(audit[0]) or audit[0] < 1:
            raise DraftSQLiteError("Final approve audit ID không hợp lệ")
        expected_audit = (
            "approve",
            review["decided_at"],
            reviewer,
            review["version"] - 1,
            "pending",
            "approved",
            review["version"] - 1,
            review["version"],
            None,
            selection_version,
        )
        if audit[1:11] != expected_audit:
            raise DraftSQLiteError("Final approve audit không khớp review state")
        selected = _validate_canonical_indices(audit[11], audit[12])
        eligible = _eligible_ioc_indices(payload)
        if not selected or not set(selected).issubset(eligible):
            raise DraftPolicyError("Final selection phải là tập con IOC eligible không rỗng")

        selection_rows = connection.execute(
            "SELECT selection_version, review_version, action, at, actor_subject, "
            "selected_indices_json, selected_sha256 FROM draft_selection_audit "
            "WHERE draft_id=? ORDER BY selection_version",
            (draft_id,),
        ).fetchall()
        if len(selection_rows) != selection_version:
            raise DraftSQLiteError("Lịch sử selection không liên tiếp")
        if selection_version == 0:
            default_selected, serialized, digest = _canonical_selection(eligible)
            if selected != default_selected or audit[11] != serialized or audit[12] != digest:
                raise DraftSQLiteError("Final selection mặc định không khớp IOC eligible")
        else:
            latest_selected: tuple[int, ...] = ()
            for expected_version, selection_row in enumerate(selection_rows, start=1):
                event_selected = _validate_canonical_indices(selection_row[5], selection_row[6])
                if (
                    selection_row[0] != expected_version
                    or selection_row[1] != expected_version
                    or selection_row[2] != "save_selection"
                    or not set(event_selected).issubset(eligible)
                ):
                    raise DraftSQLiteError("Selection audit event/version không hợp lệ")
                _validate_subject(selection_row[4], "selection actor")
                try:
                    if datetime.fromisoformat(selection_row[3]).utcoffset() is None:
                        raise ValueError
                except (TypeError, ValueError) as exc:
                    raise DraftSQLiteError("Selection audit time không hợp lệ") from exc
                latest_selected = event_selected
            latest = selection_rows[-1]
            if (
                latest[0] != selection_version
                or latest[1] != selection_version
                or latest[2] != "save_selection"
                or latest_selected != selected
                or latest[5] != audit[11]
                or latest[6] != audit[12]
            ):
                raise DraftSQLiteError("Final selection audit không khớp approve audit")

        return ApprovedExportSnapshot(
            draft_id=stored_id,
            payload=deepcopy(payload),
            approved_audit_id=audit[0],
            review_version=review["version"],
            decided_at=review["decided_at"],
            final_selection_version=selection_version,
            selected_indices=selected,
            selected_sha256=audit[12],
            decided_by_subject=reviewer,
        )
    except DraftStoreError:
        raise
    except sqlite3.Error as exc:
        raise DraftSQLiteError(f"Lỗi đọc SQLite export: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def _validate_decision_input(
    draft_id: Any,
    actor: Any,
    decision: Any,
    expected_version: Any,
    reason: Any,
) -> str | None:
    if not _is_int(draft_id) or not 1 <= draft_id <= SQLITE_MAX_INTEGER:
        raise DraftInputError("draft_id phải là số nguyên dương trong miền INTEGER SQLite")
    if not _is_int(expected_version) or not 0 <= expected_version <= SQLITE_MAX_INTEGER:
        raise DraftInputError("expected_version phải là số nguyên không âm trong miền INTEGER SQLite")
    if not isinstance(actor, Actor):
        raise DraftInputError("actor phải là Actor")
    _validate_subject(actor.subject, "actor.subject")
    if not isinstance(actor.roles, frozenset) or not all(
        isinstance(role, str) and role for role in actor.roles
    ):
        raise DraftInputError("actor.roles phải là frozenset chuỗi")
    if not actor.roles.intersection(ALLOWED_REVIEW_ROLES):
        raise DraftPolicyError("Actor cần role analyst hoặc admin")
    if not isinstance(decision, str) or decision not in {"approve", "reject"}:
        raise DraftInputError("decision phải là approve hoặc reject")
    if decision == "approve":
        if reason is not None:
            raise DraftInputError("approve không nhận reason")
        return None
    if not isinstance(reason, str) or not reason.strip():
        raise DraftInputError("reject bắt buộc reason không rỗng")
    return reason.strip()


def _validate_approval_policy(payload: dict[str, Any], review: dict[str, Any], actor: Actor) -> None:
    creator = review["created_by_subject"]
    if creator is None:
        raise DraftPolicyError("Không thể approve draft chưa biết tác giả")
    if creator == actor.subject:
        raise DraftPolicyError("Người tạo không được tự duyệt draft")
    unsupported = sorted(
        {item["kind"] for item in payload["items"] if item["keep"] and item["kind"] != "ioc"}
    )
    if unsupported:
        raise DraftPolicyError(f"Không thể approve item kind chưa hỗ trợ: {unsupported}")


def _decide_draft_with_selection(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    decision: Literal["approve", "reject"],
    expected_version: int,
    reason: str | None = None,
    timeout: float = 5.0,
    max_version: int = SQLITE_MAX_INTEGER,
) -> DraftReviewSelectionResult:
    """Quyết định draft cục bộ và audit trong một transaction; không gọi mạng."""

    timeout = _validate_timeout(timeout)
    max_version = _validate_max_version(max_version)
    normalized_reason = _validate_decision_input(draft_id, actor, decision, expected_version, reason)
    path = Path(db_path)
    if not path.is_file():
        raise DraftDatabaseNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=rw"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        _schema_mode(connection)
        if connection.execute("PRAGMA user_version").fetchone()[0] not in {
            SELECTION_SCHEMA_VERSION,
            STORE_SCHEMA_VERSION,
        }:
            raise DraftSQLiteError("Database cần migrate lên v2 trước khi quyết định")
        _validate_current_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT id, created_at, schema_version, status, source_sha256, payload_json,
                   created_by_subject, review_status, review_version,
                   decided_by_subject, decided_at, decision_reason, selection_version
            FROM drafts WHERE id = ?
            """,
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, _, _, review = _decode_draft_row(row, "current")
        if review["status"] != "pending" or review["version"] != expected_version:
            raise DraftConflictError("Draft đã được quyết định hoặc expected_version đã stale")
        selection = _load_effective_selection(
            connection, draft_id, payload, review["status"], review["version"], row[12]
        )
        if decision == "approve":
            _validate_approval_policy(payload, review, actor)
            if not selection.selected_indices:
                raise DraftPolicyError("Không thể approve selection rỗng")
        if expected_version >= max_version:
            raise DraftConflictError("Version đã đạt giới hạn INTEGER SQLite")

        decided_at = datetime.now(UTC).isoformat()
        new_status = "approved" if decision == "approve" else "rejected"
        cursor = connection.execute(
            """
            UPDATE drafts
            SET review_status = ?, review_version = review_version + 1,
                decided_by_subject = ?, decided_at = ?, decision_reason = ?
            WHERE id = ? AND review_status = 'pending' AND review_version = ?
            """,
            (
                new_status,
                actor.subject,
                decided_at,
                normalized_reason,
                draft_id,
                expected_version,
            ),
        )
        if cursor.rowcount != 1:
            raise DraftConflictError("Draft đã thay đổi trong khi quyết định")
        connection.execute(
            """
            INSERT INTO draft_audit (
                draft_id, action, at, actor_subject, expected_version,
                previous_status, new_status, previous_version, new_version, reason,
                selection_version, selected_indices_json, selected_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft_id,
                decision,
                decided_at,
                actor.subject,
                expected_version,
                "pending",
                new_status,
                expected_version,
                expected_version + 1,
                normalized_reason,
                selection.selection_version,
                json.dumps(selection.selected_indices, separators=(",", ":")),
                selection.selected_sha256,
            ),
        )
        _commit(connection)
        return DraftReviewSelectionResult(
            draft_id=draft_id,
            status=new_status,
            version=expected_version + 1,
            decided_by_subject=actor.subject,
            decided_at=decided_at,
            reason=normalized_reason,
            selection_version=selection.selection_version,
            selected_indices=selection.selected_indices,
            selected_sha256=selection.selected_sha256,
        )
    except DraftStoreError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise DraftSQLiteError(f"Lỗi SQLite review: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def decide_draft_with_selection(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    decision: Literal["approve", "reject"],
    expected_version: int,
    reason: str | None = None,
    timeout: float = 5.0,
    max_version: int = SQLITE_MAX_INTEGER,
) -> DraftReviewSelectionResult:
    """Quyết định và trả đúng snapshot selection đã commit vào final audit."""

    return _decide_draft_with_selection(
        db_path,
        draft_id,
        actor=actor,
        decision=decision,
        expected_version=expected_version,
        reason=reason,
        timeout=timeout,
        max_version=max_version,
    )


def decide_draft(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    decision: Literal["approve", "reject"],
    expected_version: int,
    reason: str | None = None,
    timeout: float = 5.0,
    max_version: int = SQLITE_MAX_INTEGER,
) -> DraftReviewResult:
    """Wrapper legacy giữ nguyên sáu field kết quả quyết định."""

    result = _decide_draft_with_selection(
        db_path,
        draft_id,
        actor=actor,
        decision=decision,
        expected_version=expected_version,
        reason=reason,
        timeout=timeout,
        max_version=max_version,
    )
    return DraftReviewResult(
        draft_id=result.draft_id,
        status=result.status,
        version=result.version,
        decided_by_subject=result.decided_by_subject,
        decided_at=result.decided_at,
        reason=result.reason,
    )
