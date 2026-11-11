"""Kho tài sản domain/CIDR cục bộ và snapshot khớp IOC."""

from __future__ import annotations

import ipaddress
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from phonghoa_core import Ioc, IocType, normalize

ASSET_TYPES = frozenset({"domain", "ip_range"})
DOMAIN_SHAPE = re.compile(r"[^\s/@:*?\[\](){}<>,;]+\Z")
MAX_ASSETS = 1000
MAX_MATCHES = 100


class InvalidAsset(ValueError):
    """Loại, giá trị hoặc ghi chú tài sản không hợp lệ."""


class AssetExists(RuntimeError):
    """Tài sản canonical đang hoạt động đã tồn tại."""


class AssetNotFound(RuntimeError):
    """Không tìm thấy tài sản đang hoạt động."""


class AssetConflict(RuntimeError):
    """Version tài sản đã thay đổi."""


class AssetsUnavailable(RuntimeError):
    """Kho tài sản hỏng hoặc vượt giới hạn trả an toàn."""


@dataclass(frozen=True)
class Asset:
    id: int
    type: str
    value: str
    note: str
    created_by: str
    created_at: str
    updated_at: str
    version: int


@dataclass(frozen=True)
class SnapshotAsset:
    id: int
    type: str
    value: str


@dataclass(frozen=True)
class AssetSnapshot:
    assets: tuple[SnapshotAsset, ...]

    def match(self, ioc: Ioc) -> tuple[str, ...]:
        candidate = _match_candidate(ioc)
        if candidate is None:
            return ()
        kind, value = candidate
        names: list[str] = []
        for asset in self.assets:
            if asset.type != kind:
                continue
            if kind == "domain":
                matched = value == asset.value or value.endswith("." + asset.value)
            else:
                address = ipaddress.ip_address(value)
                network = ipaddress.ip_network(asset.value)
                matched = address.version == network.version and address in network
            if matched and asset.value not in names:
                names.append(asset.value)
                if len(names) > MAX_MATCHES:
                    raise AssetsUnavailable("too many matching assets")
        return tuple(names)

    def allows(self, ioc: Ioc) -> bool:
        if ioc.type is IocType.URL:
            parts = urlsplit(ioc.value)
            if parts.path not in ("", "/") or parts.query:
                return False
        return bool(self.match(ioc))


class AssetStore:
    """Mở kết nối SQLite theo thao tác; schema phải được khởi tạo tường minh."""

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = Path(path)
        self.timeout = timeout

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS assets(
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL CHECK(type IN ('domain','ip_range')),
                    canonical_value TEXT NOT NULL,
                    note TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    deleted_at TEXT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS assets_active_value
                    ON assets(type, canonical_value) WHERE deleted_at IS NULL;
                CREATE TABLE IF NOT EXISTS asset_audit(
                    id INTEGER PRIMARY KEY,
                    at TEXT NOT NULL,
                    actor_subject TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN
                        ('asset_created','asset_updated','asset_deleted')),
                    asset_id INTEGER NOT NULL,
                    before_json TEXT NULL,
                    after_json TEXT NULL
                );
                """
            )

    def list(self, asset_type: str | None = None) -> tuple[Asset, ...]:
        if asset_type is not None and asset_type not in ASSET_TYPES:
            raise InvalidAsset("invalid asset type")
        where = "deleted_at IS NULL"
        params: tuple[str, ...] = ()
        if asset_type is not None:
            where += " AND type = ?"
            params = (asset_type,)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT id,type,canonical_value,note,created_by,created_at,updated_at,version "
                f"FROM assets WHERE {where} ORDER BY id LIMIT ?",
                (*params, MAX_ASSETS + 1),
            ).fetchall()
        if len(rows) > MAX_ASSETS:
            raise AssetsUnavailable("too many active assets")
        return tuple(_asset_from_row(row) for row in rows)

    def snapshot(self) -> AssetSnapshot:
        with self._connect() as connection:
            connection.execute("BEGIN")
            rows = connection.execute(
                "SELECT id,type,canonical_value FROM assets WHERE deleted_at IS NULL ORDER BY id LIMIT ?",
                (MAX_ASSETS + 1,),
            ).fetchall()
            connection.commit()
        if len(rows) > MAX_ASSETS:
            raise AssetsUnavailable("too many active assets")
        return AssetSnapshot(tuple(SnapshotAsset(*row) for row in rows))

    def create(self, asset_type: str, value: str, note: str, actor: str) -> Asset:
        canonical = _canonical(asset_type, value)
        _validate_note_actor(note, actor)
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    "INSERT INTO assets(type,canonical_value,note,version,created_by,created_at,updated_at) "
                    "VALUES(?,?,?,1,?,?,?)",
                    (asset_type, canonical, note, actor, now, now),
                )
                asset = Asset(cursor.lastrowid, asset_type, canonical, note, actor, now, now, 1)
                self._audit(connection, "asset_created", asset.id, actor, None, asset)
                connection.commit()
                return asset
        except sqlite3.IntegrityError as exc:
            raise AssetExists("active asset exists") from exc

    def update(
        self,
        asset_id: int,
        asset_type: str,
        value: str,
        note: str,
        expected_version: int,
        actor: str,
    ) -> Asset:
        _validate_id_version(asset_id, expected_version)
        canonical = _canonical(asset_type, value)
        _validate_note_actor(note, actor)
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                before = self._active(connection, asset_id)
                if before is None:
                    raise AssetNotFound("asset not found")
                if before.version != expected_version:
                    raise AssetConflict("stale asset version")
                updated = Asset(
                    before.id,
                    asset_type,
                    canonical,
                    note,
                    before.created_by,
                    before.created_at,
                    now,
                    before.version + 1,
                )
                connection.execute(
                    "UPDATE assets SET type=?,canonical_value=?,note=?,version=?,updated_at=? "
                    "WHERE id=? AND deleted_at IS NULL",
                    (asset_type, canonical, note, updated.version, now, asset_id),
                )
                self._audit(connection, "asset_updated", asset_id, actor, before, updated)
                connection.commit()
                return updated
        except sqlite3.IntegrityError as exc:
            raise AssetExists("active asset exists") from exc

    def delete(self, asset_id: int, expected_version: int, actor: str) -> None:
        _validate_id_version(asset_id, expected_version)
        _validate_note_actor("", actor)
        now = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            before = self._active(connection, asset_id)
            if before is None:
                raise AssetNotFound("asset not found")
            if before.version != expected_version:
                raise AssetConflict("stale asset version")
            connection.execute(
                "UPDATE assets SET deleted_at=?,updated_at=?,version=version+1 WHERE id=?",
                (now, now, asset_id),
            )
            self._audit(connection, "asset_deleted", asset_id, actor, before, None)
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _active(connection: sqlite3.Connection, asset_id: int) -> Asset | None:
        row = connection.execute(
            "SELECT id,type,canonical_value,note,created_by,created_at,updated_at,version "
            "FROM assets WHERE id=? AND deleted_at IS NULL",
            (asset_id,),
        ).fetchone()
        return None if row is None else _asset_from_row(row)

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        action: str,
        asset_id: int,
        actor: str,
        before: Asset | None,
        after: Asset | None,
    ) -> None:
        compact = {"ensure_ascii": False, "separators": (",", ":")}
        connection.execute(
            "INSERT INTO asset_audit(at,actor_subject,action,asset_id,before_json,after_json) "
            "VALUES(?,?,?,?,?,?)",
            (
                _now(),
                actor,
                action,
                asset_id,
                None if before is None else json.dumps(_audit_value(before), **compact),
                None if after is None else json.dumps(_audit_value(after), **compact),
            ),
        )


def _canonical(asset_type: str, raw: str) -> str:
    if asset_type not in ASSET_TYPES or not isinstance(raw, str) or not raw:
        raise InvalidAsset("invalid asset")
    if asset_type == "ip_range":
        if "/" not in raw or raw != raw.strip():
            raise InvalidAsset("invalid network")
        try:
            return str(ipaddress.ip_network(raw, strict=True))
        except ValueError as exc:
            raise InvalidAsset("invalid network") from exc
    if raw != raw.strip() or not DOMAIN_SHAPE.fullmatch(raw) or raw.startswith("."):
        raise InvalidAsset("invalid domain shape")
    try:
        ioc = normalize(raw)
    except ValueError as exc:
        raise InvalidAsset("invalid domain") from exc
    if ioc.type is not IocType.DOMAIN or len(ioc.value) > 253:
        raise InvalidAsset("invalid domain")
    return ioc.value


def _validate_note_actor(note: object, actor: object) -> None:
    if not isinstance(note, str) or len(note) > 500:
        raise InvalidAsset("invalid note")
    if not isinstance(actor, str) or not actor:
        raise InvalidAsset("invalid actor")


def _validate_id_version(asset_id: object, version: object) -> None:
    maximum = 2**53 - 1
    for value in (asset_id, version):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise InvalidAsset("invalid id or version")


def _match_candidate(ioc: Ioc) -> tuple[str, str] | None:
    if ioc.type is IocType.DOMAIN:
        return "domain", ioc.value
    if ioc.type is IocType.EMAIL:
        return "domain", ioc.value.rsplit("@", 1)[-1]
    if ioc.type is IocType.URL:
        host = urlsplit(ioc.value).hostname or ""
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return "domain", host
        return "ip_range", host
    if ioc.type in (IocType.IPV4, IocType.IPV6):
        return "ip_range", ioc.value
    return None


def _asset_from_row(row: tuple[object, ...]) -> Asset:
    return Asset(*row)


def _audit_value(asset: Asset) -> dict[str, object]:
    value = asdict(asset)
    value["canonical_value"] = value.pop("value")
    return value


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
