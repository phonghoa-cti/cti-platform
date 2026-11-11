"""Trạng thái xử lý CVE theo technology, lưu cục bộ và audit nguyên tử."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from portal_api.cves import CVE_ID, CveReadPort, CvesUnavailable, _validate_dataset
from portal_api.technologies import (
    JSON_SAFE_INTEGER,
    TechnologiesUnavailable,
    Technology,
    TechnologyStore,
    _technology_from_row,
)

NOTICE = "Trạng thái do người dùng ghi nhận; không phải bằng chứng kỹ thuật đã vá hoặc không bị ảnh hưởng."
STATUSES = {"open", "patching", "patched", "not_affected"}
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_CURSOR_BYTES = 1024
WIRE_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z")


class InvalidStatusRequest(ValueError):
    """Path, body hoặc cursor không đúng contract."""


class StatusRelationNotFound(RuntimeError):
    """Technology/CVE không còn là quan hệ active exact-match."""


class StatusContextChanged(RuntimeError):
    """Expected technology hoặc dataset không còn hiện hành."""


class StatusVersionConflict(RuntimeError):
    """Optimistic status version không còn hiện hành."""


class StatusSnapshotChanged(RuntimeError):
    """Cursor history thuộc snapshot cũ."""


class StatusUnavailable(RuntimeError):
    """Store/schema/dữ liệu không thể dùng an toàn."""


@dataclass(frozen=True)
class StatusContext:
    technology_id: int
    cve_id: str
    vendor: str
    product: str
    software_version: str
    technology_record_version: int
    dataset_id: str


class CveStatusStore:
    """Store dùng cùng SQLite W04 nhưng schema và lifecycle độc lập."""

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = Path(path)
        self.timeout = timeout

    def initialize(self) -> None:
        if not self.path.exists():
            raise StatusUnavailable("technology database missing")
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect_rw()
            connection.execute("BEGIN IMMEDIATE")
            TechnologyStore._validate_schema(connection)
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE name IN "
                    "('cve_status_records','cve_status_audit','cve_status_audit_relation',"
                    "'w03_status_migrations')"
                )
            }
            required = {
                "cve_status_records",
                "cve_status_audit",
                "cve_status_audit_relation",
                "w03_status_migrations",
            }
            if not names:
                self._create_schema(connection)
            elif names != required:
                raise StatusUnavailable("partial status schema")
            self._validate_schema(connection)
            connection.commit()
        except (StatusUnavailable, TechnologiesUnavailable) as exc:
            if connection is not None:
                connection.rollback()
            raise StatusUnavailable("status migration unavailable") from exc
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise StatusUnavailable("status migration failure") from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE cve_status_records(
            technology_id INTEGER NOT NULL,cve_id TEXT NOT NULL,vendor_key TEXT NOT NULL,
            product_key TEXT NOT NULL,status TEXT NOT NULL,status_version INTEGER NOT NULL,
            note TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,
            context_json TEXT NOT NULL,
            PRIMARY KEY(technology_id,cve_id,vendor_key,product_key))"""
        )
        connection.execute(
            """CREATE TABLE cve_status_audit(
            id INTEGER PRIMARY KEY,technology_id INTEGER NOT NULL,cve_id TEXT NOT NULL,
            vendor_key TEXT NOT NULL,product_key TEXT NOT NULL,event TEXT NOT NULL,
            before_json TEXT NULL,after_json TEXT NOT NULL)"""
        )
        connection.execute(
            "CREATE INDEX cve_status_audit_relation ON cve_status_audit"
            "(technology_id,cve_id,vendor_key,product_key,id DESC)"
        )
        connection.execute("CREATE TABLE w03_status_migrations(version INTEGER NOT NULL UNIQUE)")
        connection.execute("INSERT INTO w03_status_migrations(version) VALUES(1)")

    @staticmethod
    def _validate_schema(connection: sqlite3.Connection) -> None:
        expected = {
            "cve_status_records": [
                ("technology_id", "INTEGER", 1, 1),
                ("cve_id", "TEXT", 1, 2),
                ("vendor_key", "TEXT", 1, 3),
                ("product_key", "TEXT", 1, 4),
                ("status", "TEXT", 1, 0),
                ("status_version", "INTEGER", 1, 0),
                ("note", "TEXT", 1, 0),
                ("updated_at", "TEXT", 1, 0),
                ("updated_by", "TEXT", 1, 0),
                ("context_json", "TEXT", 1, 0),
            ],
            "cve_status_audit": [
                ("id", "INTEGER", 0, 1),
                ("technology_id", "INTEGER", 1, 0),
                ("cve_id", "TEXT", 1, 0),
                ("vendor_key", "TEXT", 1, 0),
                ("product_key", "TEXT", 1, 0),
                ("event", "TEXT", 1, 0),
                ("before_json", "TEXT", 0, 0),
                ("after_json", "TEXT", 1, 0),
            ],
            "w03_status_migrations": [("version", "INTEGER", 1, 0)],
        }
        for table, wanted in expected.items():
            actual = [
                (row[1], row[2].upper(), row[3], row[5])
                for row in connection.execute(f"PRAGMA table_info({table})")
            ]
            if actual != wanted:
                raise StatusUnavailable("incompatible status schema")
        if connection.execute("SELECT version FROM w03_status_migrations").fetchall() != [(1,)]:
            raise StatusUnavailable("incompatible status marker")
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name='cve_status_audit_relation'"
        ).fetchone()
        normalized = "" if row is None or row[0] is None else "".join(row[0].lower().split())
        if normalized != (
            "createindexcve_status_audit_relationoncve_status_audit"
            "(technology_id,cve_id,vendor_key,product_key,iddesc)"
        ):
            raise StatusUnavailable("incompatible status index")

    def get(self, cve_id: str, technology_id: int, context: dict[str, object]) -> dict[str, object]:
        _validate_relation_inputs(cve_id, technology_id)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect_ro()
            connection.execute("BEGIN")
            technology = self._current_technology(connection, technology_id)
            self._validate_context_relation(technology, context, missing_is_conflict=False)
            context = _context_from_technology(technology, cve_id, str(context["dataset_id"]))
            row = self._status_row(connection, context)
            record = None if row is None else _record_from_row(row)
            result = {
                "context": context,
                "record": record,
                "review_required": record is not None
                and (
                    record["context"]["technology_record_version"] != context["technology_record_version"]
                    or record["context"]["dataset_id"] != context["dataset_id"]
                ),
                "notice": NOTICE,
            }
            _check_response(result)
            return result
        except (InvalidStatusRequest, StatusRelationNotFound, StatusUnavailable):
            raise
        except (sqlite3.Error, TechnologiesUnavailable, ValueError, TypeError) as exc:
            raise StatusUnavailable("status read failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def put(
        self,
        cve_id: str,
        technology_id: int,
        context: dict[str, object],
        status: object,
        note: object,
        expected_status_version: object,
        actor: object,
    ) -> tuple[dict[str, object], int]:
        _validate_relation_inputs(cve_id, technology_id)
        status = _status(status)
        note = _note(note)
        actor = _actor(actor)
        expected_status_version = _version(expected_status_version, allow_zero=True)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect_rw()
            connection.execute("BEGIN IMMEDIATE")
            technology = self._current_technology(connection, technology_id)
            self._validate_context_relation(technology, context, missing_is_conflict=True)
            context = _context_from_technology(technology, cve_id, str(context["dataset_id"]))
            existing_row = self._status_row(connection, context)
            before = None if existing_row is None else _record_from_row(existing_row)
            actual_version = 0 if before is None else before["status_version"]
            if actual_version != expected_status_version:
                raise StatusVersionConflict("stale status version")
            next_version = _next_version(actual_version)
            now = _now()
            after = {
                "status": status,
                "status_version": next_version,
                "note": note,
                "updated_at": now,
                "updated_by": actor,
                "context": context,
            }
            keys = _keys(context)
            if before is None:
                connection.execute(
                    "INSERT INTO cve_status_records VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (*keys, status, next_version, note, now, actor, _canonical(context).decode("utf-8")),
                )
                event = "created"
            else:
                connection.execute(
                    "UPDATE cve_status_records SET status=?,status_version=?,note=?,updated_at=?,"
                    "updated_by=?,context_json=? WHERE technology_id=? AND cve_id=?"
                    " AND vendor_key=? AND product_key=?",
                    (status, next_version, note, now, actor, _canonical(context).decode("utf-8"), *keys),
                )
                event = "changed"
            audit_id = self._insert_audit(connection, keys, event, before, after)
            result = {
                "context": context,
                "record": after,
                "review_required": False,
                "notice": NOTICE,
                "audit_id": audit_id,
            }
            _check_response(result)
            connection.commit()
            return result, audit_id
        except (InvalidStatusRequest, StatusContextChanged, StatusVersionConflict, StatusUnavailable):
            if connection is not None:
                connection.rollback()
            raise
        except (sqlite3.Error, TechnologiesUnavailable, ValueError, TypeError) as exc:
            if connection is not None:
                connection.rollback()
            raise StatusUnavailable("status write failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def history(
        self,
        cve_id: str,
        technology_id: int,
        context: dict[str, object],
        limit: int,
        cursor: str | None,
        role_key: str,
    ) -> dict[str, object]:
        _validate_relation_inputs(cve_id, technology_id)
        if not 1 <= limit <= 100:
            raise InvalidStatusRequest("invalid history limit")
        decoded = _decode_cursor(cursor)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect_ro()
            connection.execute("BEGIN")
            technology = self._current_technology(connection, technology_id)
            self._validate_context_relation(technology, context, missing_is_conflict=False)
            context = _context_from_technology(technology, cve_id, str(context["dataset_id"]))
            keys = _keys(context)
            snapshot = self._history_snapshot(connection, keys, context, role_key, limit)
            after_id = None
            if decoded is not None:
                if decoded["binding"] != _binding(keys, role_key, limit):
                    raise InvalidStatusRequest("cursor binding mismatch")
                if decoded["snapshot"] != snapshot:
                    raise StatusSnapshotChanged("history snapshot changed")
                after_id = decoded["after"]
                if (
                    connection.execute(
                        "SELECT 1 FROM cve_status_audit WHERE technology_id=? AND cve_id=? AND vendor_key=?"
                        " AND product_key=? AND id=?",
                        (*keys, after_id),
                    ).fetchone()
                    is None
                ):
                    raise InvalidStatusRequest("cursor position missing")
            sql = (
                "SELECT id,event,before_json,after_json FROM cve_status_audit WHERE technology_id=?"
                " AND cve_id=? AND vendor_key=? AND product_key=?"
            )
            params: tuple[object, ...] = keys
            if after_id is not None:
                sql += " AND id<?"
                params += (after_id,)
            rows = connection.execute(sql + " ORDER BY id DESC LIMIT ?", (*params, limit + 1)).fetchall()
            items = [_audit_item(row) for row in rows[:limit]]
            next_cursor = None
            if len(rows) > limit:
                next_cursor = _encode_cursor(snapshot, _binding(keys, role_key, limit), items[-1]["audit_id"])
            result = {
                "context": context,
                "items": items,
                "page": {"limit": limit, "next_cursor": next_cursor},
                "notice": NOTICE,
            }
            _check_response(result)
            return result
        except (InvalidStatusRequest, StatusRelationNotFound, StatusSnapshotChanged, StatusUnavailable):
            raise
        except (sqlite3.Error, TechnologiesUnavailable, ValueError, TypeError) as exc:
            raise StatusUnavailable("history read failure") from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _current_technology(connection: sqlite3.Connection, technology_id: int) -> Technology | None:
        TechnologyStore._validate_schema(connection)
        CveStatusStore._validate_schema(connection)
        row = connection.execute(
            "SELECT id,vendor,vendor_key,product,product_key,software_version,note,created_by,created_at,"
            "updated_at,record_version FROM technology_assets WHERE id=? AND deleted_at IS NULL",
            (technology_id,),
        ).fetchone()
        return None if row is None else _technology_from_row(row)

    @staticmethod
    def _validate_context_relation(
        technology: Technology | None,
        context: dict[str, object],
        *,
        missing_is_conflict: bool,
    ) -> None:
        _validate_context(context)
        if technology is None:
            if missing_is_conflict:
                raise StatusContextChanged("technology missing")
            raise StatusRelationNotFound("technology missing")
        if (technology.vendor.casefold(), technology.product.casefold()) != (
            str(context["vendor"]).casefold(),
            str(context["product"]).casefold(),
        ):
            if missing_is_conflict:
                raise StatusContextChanged("technology identity changed")
            raise StatusRelationNotFound("relation missing")
        if missing_is_conflict and technology.version != context["technology_record_version"]:
            raise StatusContextChanged("technology version changed")

    @staticmethod
    def _status_row(connection: sqlite3.Connection, context: dict[str, object]):
        return connection.execute(
            "SELECT status,status_version,note,updated_at,updated_by,context_json "
            "FROM cve_status_records WHERE technology_id=? AND cve_id=? AND vendor_key=?"
            " AND product_key=?",
            _keys(context),
        ).fetchone()

    @staticmethod
    def _insert_audit(connection, keys, event, before, after) -> int:
        compact = {"ensure_ascii": False, "sort_keys": True, "separators": (",", ":")}
        cursor = connection.execute(
            "INSERT INTO cve_status_audit"
            "(technology_id,cve_id,vendor_key,product_key,event,before_json,after_json)"
            " VALUES(?,?,?,?,?,?,?)",
            (
                *keys,
                event,
                None if before is None else json.dumps(before, **compact),
                json.dumps(after, **compact),
            ),
        )
        return _version(cursor.lastrowid)

    @staticmethod
    def _history_snapshot(connection, keys, context, role_key, limit) -> str:
        row = connection.execute(
            "SELECT COALESCE(MAX(id),0),COUNT(*) FROM cve_status_audit WHERE technology_id=? AND cve_id=?"
            " AND vendor_key=? AND product_key=?",
            keys,
        ).fetchone()
        return hashlib.sha256(
            _canonical(
                {"context": context, "role": role_key, "limit": limit, "max_id": row[0], "count": row[1]}
            )
        ).hexdigest()

    def _connect_rw(self) -> sqlite3.Connection:
        absolute = self.path.resolve().as_posix()
        connection = sqlite3.connect(
            f"file:{quote(absolute, safe='/:')}?mode=rw",
            uri=True,
            timeout=self.timeout,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _connect_ro(self) -> sqlite3.Connection:
        absolute = self.path.resolve().as_posix()
        connection = sqlite3.connect(
            f"file:{quote(absolute, safe='/:')}?mode=ro",
            uri=True,
            timeout=self.timeout,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.execute("PRAGMA foreign_keys=ON")
        return connection


class CveStatusService:
    def __init__(self, port: CveReadPort, store: CveStatusStore) -> None:
        self.port = port
        self.store = store

    def context(self, cve_id: str, technology_id: int) -> dict[str, object]:
        _validate_relation_inputs(cve_id, technology_id)
        try:
            dataset, _fingerprint, dataset_id = _validate_dataset(self.port.list_candidates())
        except CvesUnavailable as exc:
            raise StatusUnavailable("dataset unavailable") from exc
        candidate = next((item for item in dataset["candidates"] if item["cve_id"] == cve_id), None)
        if candidate is None:
            raise StatusRelationNotFound("cve missing")
        pairs = {(item["vendor_key"], item["product_key"]) for item in candidate["affected_products"]}
        technology = self._read_technology(technology_id)
        if technology is None or (technology.vendor.casefold(), technology.product.casefold()) not in pairs:
            raise StatusRelationNotFound("relation missing")
        return asdict(
            StatusContext(
                technology.id,
                cve_id,
                technology.vendor,
                technology.product,
                technology.software_version,
                technology.version,
                dataset_id,
            )
        )

    def _read_technology(self, technology_id: int) -> Technology | None:
        connection = None
        try:
            connection = self.store._connect_ro()
            connection.execute("BEGIN")
            TechnologyStore._validate_schema(connection)
            row = connection.execute(
                "SELECT id,vendor,vendor_key,product,product_key,software_version,note,created_by,created_at,"
                "updated_at,record_version FROM technology_assets WHERE id=? AND deleted_at IS NULL",
                (technology_id,),
            ).fetchone()
            return None if row is None else _technology_from_row(row)
        except (sqlite3.Error, TechnologiesUnavailable) as exc:
            raise StatusUnavailable("technology unavailable") from exc
        finally:
            if connection is not None:
                connection.close()


def _validate_relation_inputs(cve_id: object, technology_id: object) -> None:
    if not isinstance(cve_id, str) or len(cve_id) > 64 or not CVE_ID.fullmatch(cve_id):
        raise InvalidStatusRequest("invalid cve id")
    _version(technology_id)


def _validate_context(context: object) -> None:
    keys = {
        "technology_id",
        "cve_id",
        "vendor",
        "product",
        "software_version",
        "technology_record_version",
        "dataset_id",
    }
    if not isinstance(context, dict) or set(context) != keys:
        raise StatusUnavailable("invalid context")
    _validate_relation_inputs(context["cve_id"], context["technology_id"])
    _version(context["technology_record_version"])
    for key, maximum in (("vendor", 128), ("product", 256), ("software_version", 128)):
        _visible(context[key], maximum)
    if not isinstance(context["dataset_id"], str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", context["dataset_id"]
    ):
        raise StatusUnavailable("invalid dataset id")


def _keys(context: dict[str, object]) -> tuple[object, ...]:
    return (
        context["technology_id"],
        context["cve_id"],
        str(context["vendor"]).casefold(),
        str(context["product"]).casefold(),
    )


def _context_from_technology(technology: Technology, cve_id: str, dataset_id: str) -> dict[str, object]:
    return asdict(
        StatusContext(
            technology.id,
            cve_id,
            technology.vendor,
            technology.product,
            technology.software_version,
            technology.version,
            dataset_id,
        )
    )


def _record_from_row(row: tuple[object, ...]) -> dict[str, object]:
    status, version, note, updated_at, updated_by, context_raw = row
    status = _status(status)
    version = _version(version)
    note = _note(note)
    updated_by = _actor(updated_by)
    if not isinstance(updated_at, str) or not WIRE_TIMESTAMP.fullmatch(updated_at):
        raise StatusUnavailable("invalid status timestamp")
    try:
        context = json.loads(context_raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise StatusUnavailable("invalid status context") from exc
    _validate_context(context)
    return {
        "status": status,
        "status_version": version,
        "note": note,
        "updated_at": updated_at,
        "updated_by": updated_by,
        "context": context,
    }


def _audit_item(row):
    audit_id, event, before_raw, after_raw = row
    audit_id = _version(audit_id)
    if event not in {"created", "changed"}:
        raise StatusUnavailable("invalid audit event")
    try:
        before = None if before_raw is None else json.loads(before_raw)
        after = json.loads(after_raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise StatusUnavailable("invalid audit json") from exc
    _validate_record(after)
    if before is not None:
        _validate_record(before)
    if (event == "created") != (before is None):
        raise StatusUnavailable("invalid audit transition")
    return {"audit_id": audit_id, "event": event, "before": before, "after": after}


def _validate_record(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {
        "status",
        "status_version",
        "note",
        "updated_at",
        "updated_by",
        "context",
    }:
        raise StatusUnavailable("invalid audit record")
    try:
        _status(value["status"])
        _version(value["status_version"])
        _note(value["note"])
        _actor(value["updated_by"])
        _validate_context(value["context"])
    except InvalidStatusRequest as exc:
        raise StatusUnavailable("invalid audit record") from exc
    if not isinstance(value["updated_at"], str) or not WIRE_TIMESTAMP.fullmatch(value["updated_at"]):
        raise StatusUnavailable("invalid audit timestamp")


def _status(value: object) -> str:
    if not isinstance(value, str) or value not in STATUSES:
        raise InvalidStatusRequest("invalid status")
    return value


def _note(value: object) -> str:
    value = _visible(value, 1000)
    return value


def _actor(value: object) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 512 or not value.strip() or _has_control(value):
        raise InvalidStatusRequest("invalid actor")
    return value


def _visible(value: object, maximum: int) -> str:
    if not isinstance(value, str) or _has_control(value):
        raise InvalidStatusRequest("invalid text")
    value = value.strip()
    if not 1 <= len(value) <= maximum:
        raise InvalidStatusRequest("invalid text")
    return value


def _has_control(value: str) -> bool:
    return any(unicodedata.category(char) in {"Cc", "Cs"} for char in value)


def _version(value: object, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= JSON_SAFE_INTEGER:
        raise InvalidStatusRequest("invalid integer")
    return value


def _next_version(value: int) -> int:
    if value >= JSON_SAFE_INTEGER:
        raise StatusUnavailable("status version overflow")
    return value + 1


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _check_response(value: object) -> None:
    if len(_canonical(value)) > MAX_RESPONSE_BYTES:
        raise StatusUnavailable("status response too large")


def _binding(keys, role_key, limit) -> str:
    return hashlib.sha256(_canonical({"relation": keys, "role": role_key, "limit": limit})).hexdigest()


def _encode_cursor(snapshot: str, binding: str, after: int) -> str:
    return (
        base64.urlsafe_b64encode(
            _canonical({"v": 1, "snapshot": snapshot, "binding": binding, "after": after})
        )
        .rstrip(b"=")
        .decode("ascii")
    )


def _decode_cursor(value: str | None):
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not 1 <= len(value) <= MAX_CURSOR_BYTES
        or "=" in value
    ):
        raise InvalidStatusRequest("invalid cursor")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        parsed = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidStatusRequest("invalid cursor") from exc
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value or raw != _canonical(parsed):
        raise InvalidStatusRequest("noncanonical cursor")
    if (
        not isinstance(parsed, dict)
        or set(parsed) != {"v", "snapshot", "binding", "after"}
        or parsed["v"] != 1
        or type(parsed["v"]) is not int
        or not isinstance(parsed["snapshot"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", parsed["snapshot"])
        or not isinstance(parsed["binding"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", parsed["binding"])
    ):
        raise InvalidStatusRequest("invalid cursor")
    _version(parsed["after"])
    return parsed
