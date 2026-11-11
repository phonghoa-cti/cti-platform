"""Kho công nghệ W04 cục bộ, tách biệt khỏi tài sản domain/CIDR."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

JSON_SAFE_INTEGER = 2**53 - 1
MAX_TECHNOLOGIES = 1000


class InvalidTechnology(ValueError):
    """Dữ liệu technology hoặc actor không hợp lệ."""


class TechnologyExists(RuntimeError):
    """Identity technology đang hoạt động đã tồn tại."""


class TechnologyNotFound(RuntimeError):
    """Không tìm thấy technology đang hoạt động."""


class TechnologyConflict(RuntimeError):
    """Version technology đã thay đổi."""


class TechnologiesUnavailable(RuntimeError):
    """Kho technology không thể trả kết quả đầy đủ, an toàn."""


@dataclass(frozen=True)
class Technology:
    id: int
    vendor: str
    product: str
    software_version: str
    note: str
    created_by: str
    created_at: str
    updated_at: str
    version: int


class TechnologyStore:
    """Mở rồi đóng một kết nối SQLite cho từng thao tác."""

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = Path(path)
        self.timeout = timeout

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE name IN "
                    "('technology_assets','technology_asset_audit',"
                    "'technology_assets_active_identity','w04_technology_migrations')"
                )
            }
            required = {
                "technology_assets",
                "technology_asset_audit",
                "technology_assets_active_identity",
                "w04_technology_migrations",
            }
            if not names:
                self._create_schema(connection)
            elif names != required:
                raise TechnologiesUnavailable("partial technology schema")
            self._validate_schema(connection)
            connection.commit()
        except TechnologiesUnavailable:
            if connection is not None:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise TechnologiesUnavailable("technology migration failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE technology_assets(
                id INTEGER PRIMARY KEY,
                vendor TEXT NOT NULL,
                vendor_key TEXT NOT NULL,
                product TEXT NOT NULL,
                product_key TEXT NOT NULL,
                software_version TEXT NOT NULL,
                note TEXT NOT NULL,
                record_version INTEGER NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX technology_assets_active_identity
            ON technology_assets(vendor_key,product_key,software_version)
            WHERE deleted_at IS NULL
            """
        )
        connection.execute(
            """
            CREATE TABLE technology_asset_audit(
                id INTEGER PRIMARY KEY,
                at TEXT NOT NULL,
                actor_subject TEXT NOT NULL,
                action TEXT NOT NULL CHECK(action IN
                    ('technology_created','technology_updated','technology_deleted')),
                technology_id INTEGER NOT NULL,
                before_json TEXT NULL,
                after_json TEXT NULL
            )
            """
        )
        connection.execute("CREATE TABLE w04_technology_migrations(version INTEGER NOT NULL UNIQUE)")
        connection.execute("INSERT INTO w04_technology_migrations(version) VALUES(1)")

    @staticmethod
    def _validate_schema(connection: sqlite3.Connection) -> None:
        expected_assets = [
            ("id", "INTEGER", 0, 1),
            ("vendor", "TEXT", 1, 0),
            ("vendor_key", "TEXT", 1, 0),
            ("product", "TEXT", 1, 0),
            ("product_key", "TEXT", 1, 0),
            ("software_version", "TEXT", 1, 0),
            ("note", "TEXT", 1, 0),
            ("record_version", "INTEGER", 1, 0),
            ("created_by", "TEXT", 1, 0),
            ("created_at", "TEXT", 1, 0),
            ("updated_at", "TEXT", 1, 0),
            ("deleted_at", "TEXT", 0, 0),
        ]
        expected_audit = [
            ("id", "INTEGER", 0, 1),
            ("at", "TEXT", 1, 0),
            ("actor_subject", "TEXT", 1, 0),
            ("action", "TEXT", 1, 0),
            ("technology_id", "INTEGER", 1, 0),
            ("before_json", "TEXT", 0, 0),
            ("after_json", "TEXT", 0, 0),
        ]
        expected_marker = [("version", "INTEGER", 1, 0)]

        def columns(table: str) -> list[tuple[object, ...]]:
            return [
                (row[1], row[2].upper(), row[3], row[5])
                for row in connection.execute(f"PRAGMA table_info({table})")
            ]

        if columns("technology_assets") != expected_assets:
            raise TechnologiesUnavailable("incompatible technology assets schema")
        if columns("technology_asset_audit") != expected_audit:
            raise TechnologiesUnavailable("incompatible technology audit schema")
        if columns("w04_technology_migrations") != expected_marker:
            raise TechnologiesUnavailable("incompatible technology marker schema")
        marker = connection.execute("SELECT version FROM w04_technology_migrations").fetchall()
        if marker != [(1,)]:
            raise TechnologiesUnavailable("incompatible technology marker")
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name='technology_assets_active_identity'"
        ).fetchone()
        normalized = "" if row is None or row[0] is None else "".join(row[0].lower().split())
        required = (
            "createuniqueindextechnology_assets_active_identity"
            "ontechnology_assets(vendor_key,product_key,software_version)"
            "wheredeleted_atisnull"
        )
        if normalized != required:
            raise TechnologiesUnavailable("incompatible technology identity index")

    def list(self) -> tuple[Technology, ...]:
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT id,vendor,vendor_key,product,product_key,software_version,note,"
                    "created_by,created_at,updated_at,record_version "
                    "FROM technology_assets WHERE deleted_at IS NULL ORDER BY id LIMIT ?",
                    (MAX_TECHNOLOGIES + 1,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise TechnologiesUnavailable("technology read failure") from exc
        if len(rows) > MAX_TECHNOLOGIES:
            raise TechnologiesUnavailable("too many active technologies")
        return tuple(_technology_from_row(row) for row in rows)

    def create(
        self,
        vendor: str,
        product: str,
        software_version: str,
        note: str,
        actor: str,
    ) -> Technology:
        vendor, vendor_key = _name_and_key(vendor, 128)
        product, product_key = _name_and_key(product, 256)
        software_version = _software_version(software_version)
        _validate_note_actor(note, actor)
        now = _now()
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute(
                "SELECT count(*) FROM technology_assets WHERE deleted_at IS NULL"
            ).fetchone()[0]
            if isinstance(count, bool) or not isinstance(count, int) or count >= MAX_TECHNOLOGIES:
                raise TechnologiesUnavailable("technology limit reached")
            try:
                cursor = connection.execute(
                    "INSERT INTO technology_assets"
                    "(vendor,vendor_key,product,product_key,software_version,note,record_version,"
                    "created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,1,?,?,?)",
                    (vendor, vendor_key, product, product_key, software_version, note, actor, now, now),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_write_integrity(exc)
            technology = _validated_technology(
                Technology(
                    cursor.lastrowid,
                    vendor,
                    product,
                    software_version,
                    note,
                    actor,
                    now,
                    now,
                    1,
                )
            )
            self._audit(connection, "technology_created", technology.id, actor, None, technology)
            connection.commit()
            return technology
        except (InvalidTechnology, TechnologyExists, TechnologiesUnavailable):
            if connection is not None:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise TechnologiesUnavailable("technology storage failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def update(
        self,
        technology_id: int,
        vendor: str,
        product: str,
        software_version: str,
        note: str,
        expected_version: int,
        actor: str,
    ) -> Technology:
        _validate_id_version(technology_id, expected_version)
        vendor, vendor_key = _name_and_key(vendor, 128)
        product, product_key = _name_and_key(product, 256)
        software_version = _software_version(software_version)
        _validate_note_actor(note, actor)
        now = _now()
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            before = self._active(connection, technology_id)
            if before is None:
                raise TechnologyNotFound("technology not found")
            if before.version != expected_version:
                raise TechnologyConflict("stale technology version")
            updated = _validated_technology(
                Technology(
                    before.id,
                    vendor,
                    product,
                    software_version,
                    note,
                    before.created_by,
                    before.created_at,
                    now,
                    _next_version(before.version),
                )
            )
            try:
                connection.execute(
                    "UPDATE technology_assets SET vendor=?,vendor_key=?,product=?,product_key=?,"
                    "software_version=?,note=?,record_version=?,updated_at=? "
                    "WHERE id=? AND deleted_at IS NULL",
                    (
                        vendor,
                        vendor_key,
                        product,
                        product_key,
                        software_version,
                        note,
                        updated.version,
                        now,
                        technology_id,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_write_integrity(exc)
            self._audit(connection, "technology_updated", technology_id, actor, before, updated)
            connection.commit()
            return updated
        except (
            InvalidTechnology,
            TechnologyExists,
            TechnologyNotFound,
            TechnologyConflict,
            TechnologiesUnavailable,
        ):
            if connection is not None:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise TechnologiesUnavailable("technology storage failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def delete(self, technology_id: int, expected_version: int, actor: str) -> None:
        _validate_id_version(technology_id, expected_version)
        _validate_note_actor("", actor)
        now = _now()
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            before = self._active(connection, technology_id)
            if before is None:
                raise TechnologyNotFound("technology not found")
            if before.version != expected_version:
                raise TechnologyConflict("stale technology version")
            next_version = _next_version(before.version)
            connection.execute(
                "UPDATE technology_assets SET deleted_at=?,updated_at=?,record_version=? WHERE id=?",
                (now, now, next_version, technology_id),
            )
            self._audit(connection, "technology_deleted", technology_id, actor, before, None)
            connection.commit()
        except (InvalidTechnology, TechnologyNotFound, TechnologyConflict, TechnologiesUnavailable):
            if connection is not None:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise TechnologiesUnavailable("technology storage failure") from exc
        finally:
            if connection is not None:
                connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _active(connection: sqlite3.Connection, technology_id: int) -> Technology | None:
        row = connection.execute(
            "SELECT id,vendor,vendor_key,product,product_key,software_version,note,"
            "created_by,created_at,updated_at,record_version "
            "FROM technology_assets WHERE id=? AND deleted_at IS NULL",
            (technology_id,),
        ).fetchone()
        return None if row is None else _technology_from_row(row)

    @staticmethod
    def _raise_write_integrity(error: sqlite3.IntegrityError) -> None:
        identity = (
            "UNIQUE constraint failed: technology_assets.vendor_key, "
            "technology_assets.product_key, technology_assets.software_version"
        )
        if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE and str(error) == identity:
            raise TechnologyExists("active technology exists") from error
        raise TechnologiesUnavailable("technology integrity failure") from error

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        action: str,
        technology_id: int,
        actor: str,
        before: Technology | None,
        after: Technology | None,
    ) -> None:
        compact = {"ensure_ascii": False, "separators": (",", ":")}
        connection.execute(
            "INSERT INTO technology_asset_audit"
            "(at,actor_subject,action,technology_id,before_json,after_json) VALUES(?,?,?,?,?,?)",
            (
                _now(),
                actor,
                action,
                technology_id,
                None if before is None else json.dumps(asdict(before), **compact),
                None if after is None else json.dumps(asdict(after), **compact),
            ),
        )


def _name_and_key(value: object, maximum: int) -> tuple[str, str]:
    display = _bounded_visible(value, maximum)
    return display, display.casefold()


def _software_version(value: object) -> str:
    return _bounded_visible(value, 128)


def _bounded_visible(value: object, maximum: int) -> str:
    if not isinstance(value, str) or any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in value):
        raise InvalidTechnology("invalid technology text")
    trimmed = value.strip()
    if not 1 <= len(trimmed) <= maximum:
        raise InvalidTechnology("invalid technology text")
    return trimmed


def _validate_note_actor(note: object, actor: object) -> None:
    if not isinstance(note, str) or len(note) > 500:
        raise InvalidTechnology("invalid technology note")
    if not isinstance(actor, str) or not 1 <= len(actor) <= 512 or not actor.strip():
        raise InvalidTechnology("invalid technology actor")


def _validate_id_version(technology_id: object, version: object) -> None:
    for value in (technology_id, version):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= JSON_SAFE_INTEGER:
            raise InvalidTechnology("invalid technology id or version")


def _technology_from_row(row: tuple[object, ...]) -> Technology:
    try:
        (
            technology_id,
            vendor,
            vendor_key,
            product,
            product_key,
            software_version,
            note,
            created_by,
            created_at,
            updated_at,
            record_version,
        ) = row
        technology = _validated_technology(
            Technology(
                technology_id,
                vendor,
                product,
                software_version,
                note,
                created_by,
                created_at,
                updated_at,
                record_version,
            )
        )
        if vendor_key != technology.vendor.casefold() or product_key != technology.product.casefold():
            raise InvalidTechnology("invalid stored technology key")
        return technology
    except (InvalidTechnology, TypeError, ValueError) as exc:
        raise TechnologiesUnavailable("invalid stored technology") from exc


def _validated_technology(technology: Technology) -> Technology:
    try:
        _validate_id_version(technology.id, technology.version)
        if _name_and_key(technology.vendor, 128)[0] != technology.vendor:
            raise InvalidTechnology("non-canonical vendor")
        if _name_and_key(technology.product, 256)[0] != technology.product:
            raise InvalidTechnology("non-canonical product")
        if _software_version(technology.software_version) != technology.software_version:
            raise InvalidTechnology("non-canonical software version")
        _validate_note_actor(technology.note, technology.created_by)
        _validate_timestamp(technology.created_at)
        _validate_timestamp(technology.updated_at)
    except InvalidTechnology as exc:
        raise TechnologiesUnavailable("invalid technology output") from exc
    return technology


def _validate_timestamp(value: object) -> None:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise InvalidTechnology("invalid timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidTechnology("invalid timestamp") from exc
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise InvalidTechnology("invalid timestamp")


def _next_version(version: int) -> int:
    if version >= JSON_SAFE_INTEGER:
        raise TechnologiesUnavailable("technology version overflow")
    return version + 1


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
