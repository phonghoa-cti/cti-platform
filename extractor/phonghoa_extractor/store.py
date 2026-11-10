"""Lưu và đọc bản nháp pending trong SQLite cục bộ."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


class DraftStoreError(ValueError):
    """Lỗi dữ liệu hoặc lỗi SQLite có thể trình bày cho người dùng CLI."""


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


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            status TEXT NOT NULL,
            source_sha256 TEXT NOT NULL
        )
        """
    )
    connection.commit()


def save_draft(db_path: str | Path, draft: dict[str, Any], *, timeout: float = 5.0) -> int:
    """Thêm một draft mới và trả ID; không sửa hoặc gộp bản ghi cũ."""

    _validate_draft(draft)
    path = Path(db_path)
    payload = json.dumps(draft, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    created_at = datetime.now(UTC).isoformat()
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, timeout=timeout)
        _create_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """
            INSERT INTO drafts (created_at, payload_json, schema_version, status, source_sha256)
            VALUES (?, ?, ?, ?, ?)
            """,
            (created_at, payload, SCHEMA_VERSION, PENDING_STATUS, draft["source"]["sha256"]),
        )
        draft_id = cursor.lastrowid
        connection.commit()
        if draft_id is None:
            raise DraftStoreError("SQLite không trả ID cho draft")
        return draft_id
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise DraftStoreError(f"Lỗi SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def get_draft(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> dict[str, Any]:
    """Đọc một draft bằng kết nối SQLite chỉ đọc, không tự tạo database."""

    if not _is_int(draft_id) or draft_id < 1:
        raise DraftStoreError("ID phải là số nguyên dương")
    path = Path(db_path)
    if not path.is_file():
        raise DraftStoreError(f"Database không tồn tại: {path}")
    connection: sqlite3.Connection | None = None
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
        row = connection.execute(
            "SELECT payload_json, created_at FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        if row is None:
            raise DraftStoreError(f"không tìm thấy draft ID {draft_id}")
        payload = json.loads(row[0])
        if not isinstance(payload, dict):
            raise DraftStoreError(f"Payload draft ID {draft_id} không hợp lệ")
        return {**payload, "id": draft_id, "created_at": row[1]}
    except (sqlite3.Error, json.JSONDecodeError) as exc:
        raise DraftStoreError(f"Lỗi đọc SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()
