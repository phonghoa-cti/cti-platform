"""F22: nhật ký kiểm toán hợp nhất, chỉ ghi thêm, có chuỗi băm để phát hiện sửa/xóa.

Mỗi dòng lưu ``prev_hash`` (hash của dòng trước) và ``row_hash`` = SHA-256 của nội dung
chuẩn hóa + ``prev_hash``. Sửa, xóa hay chèn giữa chuỗi đều làm ``verify_chain`` báo lỗi.
Chuỗi băm chỉ phát hiện, không ngăn được người có quyền ghi file viết lại toàn bộ chuỗi;
cần sao lưu/đối chiếu hash đầu chuỗi ra ngoài (xem spec F22).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

GENESIS_HASH = "0" * 64
RESULTS = ("success", "failure", "denied")
MAX_TEXT = 256
MAX_DETAIL_BYTES = 4_096
MAX_PAGE = 200

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  target TEXT NOT NULL,
  result TEXT NOT NULL,
  detail TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  row_hash TEXT NOT NULL UNIQUE
);
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
"""


class InvalidAuditEntry(ValueError):
    """Dữ liệu nhật ký không hợp lệ (quá dài, ký tự điều khiển, result lạ)."""


@dataclass(frozen=True)
class ChainReport:
    """Kết quả kiểm chuỗi: ``ok`` và id dòng đầu tiên bị lệch (nếu có)."""

    ok: bool
    checked: int
    broken_at: int | None = None


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _clean(value: object, label: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_TEXT:
        raise InvalidAuditEntry(label)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise InvalidAuditEntry(label)
    return value


def _row_hash(fields: Mapping[str, str], prev_hash: str) -> str:
    content = {**fields, "prev_hash": prev_hash}
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuditLog:
    """SQLite riêng cho nhật ký; trigger chặn UPDATE/DELETE qua SQL thông thường."""

    def __init__(
        self, path: str | Path, *, timeout: float = 5.0, clock: Callable[[], datetime] = _utc_now
    ) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.clock = clock

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def record(
        self,
        actor: object,
        action: object,
        target: object,
        result: object,
        detail: Mapping[str, object] | None = None,
    ) -> dict:
        """Ghi một dòng; khóa ghi (BEGIN IMMEDIATE) để hai tiến trình không rẽ nhánh chuỗi."""
        if result not in RESULTS:
            raise InvalidAuditEntry("result")
        detail_json = json.dumps(dict(detail or {}), sort_keys=True, ensure_ascii=False, default=str)
        if len(detail_json.encode("utf-8")) > MAX_DETAIL_BYTES:
            raise InvalidAuditEntry("detail")
        fields = {
            "at": self.clock().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actor": _clean(actor, "actor"),
            "action": _clean(action, "action"),
            "target": _clean(target, "target"),
            "result": str(result),
            "detail": detail_json,
        }
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            last = connection.execute("SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
            prev_hash = last["row_hash"] if last else GENESIS_HASH
            row_hash = _row_hash(fields, prev_hash)
            cursor = connection.execute(
                "INSERT INTO audit_log(at,actor,action,target,result,detail,prev_hash,row_hash)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (*fields.values(), prev_hash, row_hash),
            )
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        return {"id": cursor.lastrowid, **fields, "prev_hash": prev_hash, "row_hash": row_hash}

    def list_entries(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        target: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Đọc mới nhất trước; bộ lọc so khớp chính xác, thời gian so chuỗi ISO UTC."""
        clauses: list[str] = []
        params: list[object] = []
        for column, value in (("actor", actor), ("action", action), ("target", target)):
            if value is not None:
                clauses.append(f"{column}=?")
                params.append(value)
        if since is not None:
            clauses.append("at>=?")
            params.append(since)
        if until is not None:
            clauses.append("at<=?")
            params.append(until)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, min(limit, MAX_PAGE)))
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM audit_log{where} ORDER BY id DESC LIMIT ?", params
            ).fetchall()
        return [{**dict(row), "detail": json.loads(row["detail"])} for row in rows]

    def verify_chain(self) -> ChainReport:
        """Tính lại toàn bộ chuỗi; dừng ở dòng đầu tiên sai hash hoặc sai liên kết."""
        prev_hash = GENESIS_HASH
        checked = 0
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
        for row in rows:
            fields = {key: row[key] for key in ("at", "actor", "action", "target", "result", "detail")}
            if row["prev_hash"] != prev_hash or row["row_hash"] != _row_hash(fields, prev_hash):
                return ChainReport(ok=False, checked=checked, broken_at=row["id"])
            prev_hash = row["row_hash"]
            checked += 1
        return ChainReport(ok=True, checked=checked)
