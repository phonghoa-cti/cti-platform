"""Read model W03-S2 ghép CVE, công nghệ và trạng thái trong một snapshot chỉ đọc."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime

from portal_api.cves import (
    CVE_ID,
    MAX_RESPONSE_BYTES,
    NOTICE,
    CveQuery,
    CveReadPort,
    CvesUnavailable,
    _canonical_bytes,
    _rank_matches,
    _summary_item,
    _validate_dataset,
)
from portal_api.cves_status import CveStatusStore, StatusUnavailable, _record_from_row
from portal_api.technologies import (
    JSON_SAFE_INTEGER,
    MAX_TECHNOLOGIES,
    TechnologiesUnavailable,
    Technology,
    TechnologyStore,
    _technology_from_row,
)

CURSOR_KIND = "w03-status-view"
MAX_CURSOR_BYTES = 1024
STATUS_FILTERS = {"unset", "open", "patching", "patched", "not_affected", "review_required"}
PERSISTED_STATUSES = ("unset", "open", "patching", "patched", "not_affected")


class InvalidCveStatusQuery(ValueError):
    """Query/cursor không đúng hợp đồng W03-S2."""


class CveStatusViewUnavailable(RuntimeError):
    """Dataset hoặc snapshot SQLite không thể đọc an toàn."""


class CveStatusTechnologyNotFound(RuntimeError):
    """Technology active được lọc không tồn tại."""


class CveStatusSnapshotChanged(RuntimeError):
    """Cursor thuộc snapshot cũ."""


@dataclass(frozen=True)
class CveStatusQuery:
    kev: bool | None
    asset_id: int | None
    q: str | None
    status: str | None
    limit: int
    cursor: Mapping[str, object] | None


def parse_cve_status_query(request, view: str) -> CveStatusQuery:
    if len(request.scope.get("query_string", b"")) > 4096:
        raise InvalidCveStatusQuery("query too large")
    allowed = {"kev", "asset_id", "q", "status", "limit", "cursor"}
    if set(request.query_params) - allowed:
        raise InvalidCveStatusQuery("unknown query")
    if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise InvalidCveStatusQuery("repeated query")
    raw_kev = request.query_params.get("kev")
    if raw_kev is not None and raw_kev not in {"true", "false"}:
        raise InvalidCveStatusQuery("invalid kev")
    kev = None if raw_kev is None else raw_kev == "true"
    asset_id = _decimal(request.query_params.get("asset_id"), JSON_SAFE_INTEGER)
    limit = _decimal(request.query_params.get("limit", "25"), 100) or 25
    raw_q = request.query_params.get("q")
    q = None
    if raw_q is not None:
        if _has_control(raw_q):
            raise InvalidCveStatusQuery("invalid q")
        q = raw_q.strip()
        if not 1 <= len(q) <= 128:
            raise InvalidCveStatusQuery("invalid q")
    status = request.query_params.get("status")
    if status is not None and status not in STATUS_FILTERS:
        raise InvalidCveStatusQuery("invalid status")
    context = _context(view, kev, asset_id, q, status, limit)
    cursor = _decode_cursor(request.query_params.get("cursor"))
    if cursor is not None and cursor["context"] != context:
        raise InvalidCveStatusQuery("cursor context mismatch")
    return CveStatusQuery(kev, asset_id, q, status, limit, cursor)


class CveStatusViewService:
    def __init__(
        self,
        port: CveReadPort,
        store: CveStatusStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.port = port
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))

    def read(self, query: CveStatusQuery, view: str) -> dict[str, object]:
        as_of_date = self._as_of_date()
        try:
            dataset, dataset_hash, dataset_id = _validate_dataset(self.port.list_candidates())
            technologies, records = self._read_sqlite_snapshot()
        except (CvesUnavailable, StatusUnavailable, TechnologiesUnavailable) as exc:
            raise CveStatusViewUnavailable("dependency unavailable") from exc
        except Exception as exc:
            raise CveStatusViewUnavailable("dependency read failure") from exc
        if query.asset_id is not None and not any(item.id == query.asset_id for item in technologies):
            raise CveStatusTechnologyNotFound("technology not found")

        base_query = CveQuery(query.kev, query.asset_id, query.q, query.limit, None)
        ranked = _rank_matches(dataset["candidates"], technologies, base_query)
        relations = self._attach_status(ranked, technologies, records, dataset_id)
        snapshot = _snapshot(dataset_hash, dataset_id, technologies, records, as_of_date)
        if query.cursor is not None and query.cursor["snapshot"] != snapshot:
            raise CveStatusSnapshotChanged("snapshot changed")

        summary = self._summary(ranked, relations, as_of_date, view)
        filtered = [item for item in ranked if self._matches_filter(item, query.status)]
        start = self._cursor_start(filtered, query.cursor)
        page = filtered[start : start + query.limit + 1]
        visible = page[: query.limit]
        next_cursor = None
        if len(page) > query.limit:
            next_cursor = _encode_cursor(
                snapshot,
                _context(view, query.kev, query.asset_id, query.q, query.status, query.limit),
                visible[-1]["cve_id"],
            )
        items = [_summary_item(item) if view == "summary" else item for item in visible]
        result = {
            "view": view,
            "items": items,
            "summary": summary,
            "page": {"next_cursor": next_cursor, "limit": query.limit},
            "source": {
                "kind": "synthetic",
                "dataset_id": dataset_id,
                "source_as_of": dataset["source_as_of"],
                "retrieved_at": dataset["retrieved_at"],
            },
            "notice": NOTICE,
        }
        if len(_canonical_bytes(result)) > MAX_RESPONSE_BYTES:
            raise CveStatusViewUnavailable("response too large")
        return result

    def _as_of_date(self) -> str:
        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise CveStatusViewUnavailable("invalid clock")
        return value.astimezone(UTC).date().isoformat()

    def _read_sqlite_snapshot(self) -> tuple[tuple[Technology, ...], dict[tuple[object, ...], dict]]:
        connection = None
        try:
            connection = self.store._connect_ro()
            connection.execute("BEGIN")
            TechnologyStore._validate_schema(connection)
            CveStatusStore._validate_schema(connection)
            rows = connection.execute(
                "SELECT id,vendor,vendor_key,product,product_key,software_version,note,created_by,"
                "created_at,updated_at,record_version FROM technology_assets "
                "WHERE deleted_at IS NULL ORDER BY id LIMIT ?",
                (MAX_TECHNOLOGIES + 1,),
            ).fetchall()
            if len(rows) > MAX_TECHNOLOGIES:
                raise TechnologiesUnavailable("too many active technologies")
            technologies = tuple(_technology_from_row(row) for row in rows)
            records = self._read_status_rows(connection)
            return technologies, records
        except (sqlite3.Error, TechnologiesUnavailable, StatusUnavailable):
            raise
        finally:
            if connection is not None:
                if connection.in_transaction:
                    connection.rollback()
                connection.close()

    def _read_status_rows(self, connection: sqlite3.Connection) -> dict[tuple[object, ...], dict]:
        rows = connection.execute(
            "SELECT technology_id,cve_id,vendor_key,product_key,status,status_version,note,updated_at,"
            "updated_by,context_json FROM cve_status_records "
            "ORDER BY technology_id,cve_id,vendor_key,product_key"
        ).fetchall()
        records = {}
        for row in rows:
            keys = tuple(row[:4])
            record = _record_from_row(tuple(row[4:]), keys)
            records[keys] = record
        return records

    @staticmethod
    def _attach_status(ranked, technologies, records, dataset_id):
        technology_by_id = {item.id: item for item in technologies}
        relations = []
        for item in ranked:
            for match in item["matches"]:
                technology = technology_by_id[match["technology_id"]]
                keys = (
                    technology.id,
                    item["cve_id"],
                    technology.vendor.casefold(),
                    technology.product.casefold(),
                )
                record = records.get(keys)
                review_required = record is not None and (
                    record["context"]["technology_record_version"] != technology.version
                    or record["context"]["dataset_id"] != dataset_id
                )
                match.update(
                    {
                        "status": None if record is None else record["status"],
                        "status_version": None if record is None else record["status_version"],
                        "status_updated_at": None if record is None else record["updated_at"],
                        "review_required": review_required,
                    }
                )
                relations.append(match)
        return relations

    @staticmethod
    def _matches_filter(item, status):
        if status is None:
            return True
        if status == "review_required":
            return any(match["review_required"] for match in item["matches"])
        if status == "unset":
            return any(match["status"] is None for match in item["matches"])
        return any(match["status"] == status for match in item["matches"])

    @staticmethod
    def _summary(ranked, relations, as_of_date, view):
        actionable = [
            item
            for item in ranked
            if any(
                match["status"] in {None, "open", "patching"} or match["review_required"]
                for match in item["matches"]
            )
        ]
        summary = {
            "matched_cves": len(ranked),
            "kev_cves": sum(1 for item in ranked if item["kev"]),
            "actionable_cves": len(actionable),
            "overdue_kev_cves": sum(
                1
                for item in actionable
                if item["kev"] and item["kev_due_date"] is not None and item["kev_due_date"] < as_of_date
            ),
            "as_of_date": as_of_date,
        }
        if view == "detail":
            summary["status_relations"] = {
                status: sum(
                    1
                    for relation in relations
                    if (relation["status"] is None if status == "unset" else relation["status"] == status)
                )
                for status in PERSISTED_STATUSES
            }
            summary["review_required_relations"] = sum(
                1 for relation in relations if relation["review_required"]
            )
        return summary

    @staticmethod
    def _cursor_start(filtered, cursor):
        if cursor is None:
            return 0
        positions = [index for index, item in enumerate(filtered) if item["cve_id"] == cursor["after"]]
        if len(positions) != 1:
            raise InvalidCveStatusQuery("cursor position invalid")
        return positions[0] + 1


def _context(view, kev, asset_id, q, status, limit):
    return {
        "view": view,
        "kev": kev,
        "asset_id": asset_id,
        "q": q,
        "status": status,
        "limit": limit,
        "domain": CURSOR_KIND,
    }


def _snapshot(dataset_hash, dataset_id, technologies, records, as_of_date):
    technology_hash = hashlib.sha256(_canonical_bytes([asdict(item) for item in technologies])).hexdigest()
    status_hash = hashlib.sha256(
        _canonical_bytes(
            [
                {"key": key, "record": record}
                for key, record in sorted(records.items(), key=lambda item: item[0])
            ]
        )
    ).hexdigest()
    return {
        "dataset": dataset_hash,
        "dataset_id": dataset_id,
        "technologies": technology_hash,
        "statuses": status_hash,
        "as_of_date": as_of_date,
    }


def _encode_cursor(snapshot, context, after):
    raw = _canonical_bytes(
        {"v": 1, "kind": CURSOR_KIND, "snapshot": snapshot, "context": context, "after": after}
    )
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    if len(encoded) > MAX_CURSOR_BYTES:
        raise CveStatusViewUnavailable("cursor too large")
    return encoded


def _decode_cursor(value):
    if value is None:
        return None
    if not value.isascii() or not 1 <= len(value) <= MAX_CURSOR_BYTES or "=" in value:
        raise InvalidCveStatusQuery("invalid cursor")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        parsed = json.loads(raw.decode("utf-8"), parse_constant=_reject_json_constant)
        canonical = _canonical_bytes(parsed)
    except (TypeError, ValueError, UnicodeDecodeError, UnicodeEncodeError, json.JSONDecodeError) as exc:
        raise InvalidCveStatusQuery("invalid cursor") from exc
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value or raw != canonical:
        raise InvalidCveStatusQuery("noncanonical cursor")
    if (
        not isinstance(parsed, dict)
        or set(parsed) != {"v", "kind", "snapshot", "context", "after"}
        or parsed["v"] != 1
        or type(parsed["v"]) is not int
        or parsed["kind"] != CURSOR_KIND
        or not isinstance(parsed["snapshot"], dict)
        or set(parsed["snapshot"]) != {"dataset", "dataset_id", "technologies", "statuses", "as_of_date"}
        or not isinstance(parsed["context"], dict)
        or set(parsed["context"]) != {"view", "kev", "asset_id", "q", "status", "limit", "domain"}
        or not isinstance(parsed["after"], str)
        or not CVE_ID.fullmatch(parsed["after"])
    ):
        raise InvalidCveStatusQuery("invalid cursor")
    snapshot = parsed["snapshot"]
    context = parsed["context"]
    if (
        not all(
            isinstance(snapshot[key], str)
            for key in ("dataset", "dataset_id", "technologies", "statuses", "as_of_date")
        )
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot["dataset"])
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot["dataset_id"])
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot["technologies"])
        or not re.fullmatch(r"[0-9a-f]{64}", snapshot["statuses"])
        or not _valid_wire_date(snapshot["as_of_date"])
        or not isinstance(context["domain"], str)
        or context["domain"] != CURSOR_KIND
        or not isinstance(context["view"], str)
        or context["view"] not in {"detail", "summary"}
        or (context["kev"] is not None and type(context["kev"]) is not bool)
        or (
            context["asset_id"] is not None
            and (type(context["asset_id"]) is not int or not 1 <= context["asset_id"] <= JSON_SAFE_INTEGER)
        )
        or not _valid_context_q(context["q"])
        or (
            context["status"] is not None
            and (not isinstance(context["status"], str) or context["status"] not in STATUS_FILTERS)
        )
        or type(context["limit"]) is not int
        or not 1 <= context["limit"] <= 100
    ):
        raise InvalidCveStatusQuery("invalid cursor")
    return parsed


def _decimal(value, maximum):
    if value is None:
        return None
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise InvalidCveStatusQuery("invalid integer")
    parsed = int(value)
    if parsed > maximum:
        raise InvalidCveStatusQuery("invalid integer")
    return parsed


def _has_control(value):
    return any(unicodedata.category(char) in {"Cc", "Cs"} for char in value)


def _reject_json_constant(_value):
    raise ValueError("nonfinite JSON number")


def _valid_wire_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _valid_context_q(value):
    if value is None:
        return True
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or _has_control(value):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True
