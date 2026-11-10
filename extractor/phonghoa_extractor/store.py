"""Lưu và đọc bản nháp pending trong SQLite cục bộ."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
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
STORE_SCHEMA_VERSION = 1
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
}


class DraftStoreError(ValueError):
    """Lỗi dữ liệu hoặc lỗi SQLite có thể trình bày cho người dùng CLI."""


class DraftInputError(DraftStoreError):
    """Đầu vào API lõi không hợp lệ."""


class DraftPolicyError(DraftStoreError):
    """Actor không được phép thực hiện quyết định."""


class DraftNotFoundError(DraftStoreError):
    """Database hoặc draft không tồn tại."""


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
            reason TEXT
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_drafts_review_queue ON drafts(review_status, id DESC)")


def _validate_current_schema(connection: sqlite3.Connection) -> None:
    if _table_columns(connection, "drafts") != REVIEW_DRAFT_COLUMNS:
        raise DraftSQLiteError("Schema drafts review bị hỏng hoặc không được hỗ trợ")
    if _table_columns(connection, "draft_audit") != AUDIT_COLUMNS:
        raise DraftSQLiteError("Schema draft_audit bị hỏng hoặc không được hỗ trợ")


def _schema_mode(connection: sqlite3.Connection) -> Literal["legacy", "current"]:
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version > STORE_SCHEMA_VERSION:
        raise DraftSQLiteError(f"Phiên bản database {user_version} chưa được hỗ trợ")
    draft_columns = _table_columns(connection, "drafts")
    if user_version == 0 and draft_columns == LEGACY_DRAFT_COLUMNS:
        return "legacy"
    if user_version == STORE_SCHEMA_VERSION:
        _validate_current_schema(connection)
        return "current"
    raise DraftSQLiteError("Schema database không hợp lệ; cần migrate rõ ràng")


def _migrate_connection(connection: sqlite3.Connection) -> None:
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version == STORE_SCHEMA_VERSION:
        _validate_current_schema(connection)
        return
    if user_version != 0:
        raise DraftSQLiteError(f"Phiên bản database {user_version} chưa được hỗ trợ")
    draft_columns = _table_columns(connection, "drafts")
    if draft_columns and draft_columns != LEGACY_DRAFT_COLUMNS:
        raise DraftSQLiteError("Schema drafts legacy bị hỏng hoặc không được hỗ trợ")

    connection.execute("BEGIN IMMEDIATE")
    try:
        if not draft_columns:
            _create_current_schema(connection)
        else:
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
        _validate_current_schema(connection)
        connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION}")
        _commit(connection)
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


def _decode_review(row: tuple[Any, ...], mode: Literal["legacy", "current"]) -> dict[str, Any]:
    if mode == "legacy":
        return _default_review()
    created_by, status, version, decided_by, decided_at, reason = row[6:12]
    if created_by is not None:
        _validate_subject(created_by, "created_by_subject")
    if status not in REVIEW_STATUSES or not _is_int(version) or version < 0:
        raise DraftStoreError("Metadata review không hợp lệ")
    if status == "pending":
        if version != 0 or any(value is not None for value in (decided_by, decided_at, reason)):
            raise DraftStoreError("Metadata review pending không hợp lệ")
    else:
        if version != 1:
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
    row: tuple[Any, ...], mode: Literal["legacy", "current"]
) -> tuple[dict[str, Any], int, str, dict[str, Any]]:
    payload, draft_id, created_at = _decode_payload_row(row)
    return payload, draft_id, created_at, _decode_review(row, mode)


def _draft_summary(row: tuple[Any, ...], mode: Literal["legacy", "current"]) -> dict[str, Any]:
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
    if not _is_int(draft_id) or draft_id < 1:
        raise DraftStoreError("ID phải là số nguyên dương")
    path = Path(db_path)
    if not path.is_file():
        raise DraftStoreError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        mode = _schema_mode(connection)
        review_columns = (
            ", created_by_subject, review_status, review_version, "
            "decided_by_subject, decided_at, decision_reason"
            if mode == "current"
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
        review_columns = (
            ", created_by_subject, review_status, review_version, "
            "decided_by_subject, decided_at, decision_reason"
            if mode == "current"
            else ""
        )
        query = (
            "SELECT id, created_at, schema_version, status, source_sha256, payload_json "
            + review_columns
            + " FROM drafts WHERE "
            + ("review_status" if mode == "current" else "status")
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


def decide_draft(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    decision: Literal["approve", "reject"],
    expected_version: int,
    reason: str | None = None,
    timeout: float = 5.0,
) -> DraftReviewResult:
    """Quyết định draft cục bộ và audit trong một transaction; không gọi mạng."""

    timeout = _validate_timeout(timeout)
    normalized_reason = _validate_decision_input(draft_id, actor, decision, expected_version, reason)
    path = Path(db_path)
    if not path.is_file():
        raise DraftNotFoundError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=rw"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        connection.execute("PRAGMA foreign_keys = ON")
        if _schema_mode(connection) != "current":
            raise DraftSQLiteError("Database legacy cần migrate trước khi quyết định")
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT id, created_at, schema_version, status, source_sha256, payload_json,
                   created_by_subject, review_status, review_version,
                   decided_by_subject, decided_at, decision_reason
            FROM drafts WHERE id = ?
            """,
            (draft_id,),
        ).fetchone()
        if row is None:
            raise DraftNotFoundError(f"không tìm thấy draft ID {draft_id}")
        payload, _, _, review = _decode_draft_row(row, "current")
        if review["status"] != "pending" or review["version"] != expected_version:
            raise DraftConflictError("Draft đã được quyết định hoặc expected_version đã stale")
        if decision == "approve":
            _validate_approval_policy(payload, review, actor)

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
                previous_status, new_status, previous_version, new_version, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        _commit(connection)
        return DraftReviewResult(
            draft_id=draft_id,
            status=new_status,
            version=expected_version + 1,
            decided_by_subject=actor.subject,
            decided_at=decided_at,
            reason=normalized_reason,
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
