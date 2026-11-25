"""Đọc CVE mẫu W03-R và đối chiếu tên công nghệ theo hợp đồng chỉ đọc."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
import sqlite3
import unicodedata
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urlsplit

from portal_api.technologies import (
    JSON_SAFE_INTEGER,
    MAX_TECHNOLOGIES,
    TechnologiesUnavailable,
    Technology,
    TechnologyStore,
    _technology_from_row,
)

MAX_CANDIDATES = 1000
MAX_PRODUCTS = 20
MAX_FIXTURE_BYTES = 4 * 1024 * 1024
MAX_CURSOR_BYTES = 1024
MAX_RESPONSE_BYTES = 1024 * 1024
CVE_ID = re.compile(r"CVE-[0-9]{4}-[0-9]{4,}\Z")
WIRE_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z")
WIRE_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
NOTICE = "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá."
SYNTHETIC_KEV_SOURCE = "CISA KEV synthetic sample"


class InvalidCveQuery(ValueError):
    """Query/cursor không đúng hợp đồng."""


class CvesUnavailable(RuntimeError):
    """Nguồn CVE hoặc snapshot công nghệ không thể đọc an toàn."""


class CveTechnologyNotFound(RuntimeError):
    """Technology active được lọc không tồn tại."""


class CveSnapshotChanged(RuntimeError):
    """Cursor thuộc snapshot cũ."""


class CveReadPort(Protocol):
    def list_candidates(self) -> object: ...


@dataclass(frozen=True)
class CveDataset:
    kind: object
    kev_snapshot_complete: object
    source_as_of: object
    retrieved_at: object
    candidates: object
    dataset_id: str | None = None


@dataclass(frozen=True)
class CveQuery:
    kev: bool | None
    asset_id: int | None
    q: str | None
    limit: int
    cursor: Mapping[str, object] | None


class FixtureCveReadPort:
    """Adapter fixture bounded; dataset_id luôn lấy từ bytes thật."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def list_candidates(self) -> CveDataset:
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_FIXTURE_BYTES + 1)
            if len(raw) > MAX_FIXTURE_BYTES:
                raise CvesUnavailable("fixture too large")
            parsed = json.loads(raw.decode("utf-8"))
        except CvesUnavailable:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CvesUnavailable("fixture unavailable") from exc
        if not isinstance(parsed, dict) or set(parsed) != {
            "kind",
            "kev_snapshot_complete",
            "source_as_of",
            "retrieved_at",
            "candidates",
        }:
            raise CvesUnavailable("invalid fixture")
        return CveDataset(
            kind=parsed.get("kind"),
            kev_snapshot_complete=parsed.get("kev_snapshot_complete"),
            source_as_of=parsed.get("source_as_of"),
            retrieved_at=parsed.get("retrieved_at"),
            candidates=parsed.get("candidates"),
            dataset_id="sha256:" + hashlib.sha256(raw).hexdigest(),
        )


class ReadOnlyTechnologyStore(TechnologyStore):
    """TechnologyStore dùng cùng validation nhưng SQLite chỉ được mở mode=ro."""

    @classmethod
    def from_store(cls, store: TechnologyStore) -> ReadOnlyTechnologyStore:
        return cls(store.path, timeout=store.timeout)

    def _connect(self) -> sqlite3.Connection:
        absolute = self.path.resolve().as_posix()
        uri = f"file:{quote(absolute, safe='/:')}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=self.timeout, isolation_level=None)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def list(self) -> tuple[Technology, ...]:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN")
            self._validate_schema(connection)
            rows = connection.execute(
                "SELECT id,vendor,vendor_key,product,product_key,software_version,note,"
                "created_by,created_at,updated_at,record_version "
                "FROM technology_assets WHERE deleted_at IS NULL ORDER BY id LIMIT ?",
                (MAX_TECHNOLOGIES + 1,),
            ).fetchall()
            if len(rows) > MAX_TECHNOLOGIES:
                raise TechnologiesUnavailable("too many active technologies")
            return tuple(_technology_from_row(row) for row in rows)
        except TechnologiesUnavailable:
            raise
        except sqlite3.Error as exc:
            raise TechnologiesUnavailable("technology read failure") from exc
        finally:
            if connection is not None:
                if connection.in_transaction:
                    connection.rollback()
                connection.close()


def parse_cve_query(request, view: str) -> CveQuery:
    if len(request.scope.get("query_string", b"")) > 4096:
        raise InvalidCveQuery("query too large")
    allowed = {"kev", "asset_id", "q", "limit", "cursor"}
    if set(request.query_params) - allowed:
        raise InvalidCveQuery("unknown query")
    if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise InvalidCveQuery("repeated query")

    raw_kev = request.query_params.get("kev")
    if raw_kev is not None and raw_kev not in {"true", "false"}:
        raise InvalidCveQuery("invalid kev")
    kev = None if raw_kev is None else raw_kev == "true"
    asset_id = _decimal(request.query_params.get("asset_id"), JSON_SAFE_INTEGER)
    limit = _decimal(request.query_params.get("limit", "25"), 100)
    if limit is None:
        limit = 25
    raw_q = request.query_params.get("q")
    q = None
    if raw_q is not None:
        if _has_control(raw_q):
            raise InvalidCveQuery("invalid q")
        q = raw_q.strip()
        if not 1 <= len(q) <= 128:
            raise InvalidCveQuery("invalid q")
    cursor = _decode_cursor(request.query_params.get("cursor"))
    if cursor is not None and cursor["context"] != _context_hash(view, kev, asset_id, q, limit):
        raise InvalidCveQuery("cursor context mismatch")
    return CveQuery(kev=kev, asset_id=asset_id, q=q, limit=limit, cursor=cursor)


class CveReadService:
    def __init__(self, port: CveReadPort, store: TechnologyStore) -> None:
        self.port = port
        self.store = ReadOnlyTechnologyStore.from_store(store)

    def read(self, query: CveQuery, view: str) -> dict[str, object]:
        try:
            raw_dataset = self.port.list_candidates()
            dataset, dataset_hash, dataset_id = _validate_dataset(raw_dataset)
            technologies = self.store.list()
        except CvesUnavailable:
            raise
        except Exception as exc:
            raise CvesUnavailable("dependency read failure") from exc

        if query.asset_id is not None and not any(item.id == query.asset_id for item in technologies):
            raise CveTechnologyNotFound("technology not found")
        snapshot = _snapshot_hash(dataset_hash, technologies)
        if query.cursor is not None and query.cursor["snapshot"] != snapshot:
            raise CveSnapshotChanged("snapshot changed")

        ranked = _rank_matches(dataset["candidates"], technologies, query)
        start = 0
        if query.cursor is not None:
            after = query.cursor["after"]
            positions = [index for index, item in enumerate(ranked) if item["cve_id"] == after]
            if len(positions) != 1:
                raise InvalidCveQuery("cursor position invalid")
            start = positions[0] + 1
        page = ranked[start : start + query.limit + 1]
        visible = page[: query.limit]
        next_cursor = None
        if len(page) > query.limit:
            next_cursor = _encode_cursor(
                snapshot,
                _context_hash(view, query.kev, query.asset_id, query.q, query.limit),
                visible[-1]["cve_id"],
            )
        items = [_summary_item(item) if view == "summary" else item for item in visible]
        result: dict[str, object] = {
            "view": view,
            "items": items,
            "summary": {
                "matched_cves": len(ranked),
                "kev_cves": sum(1 for item in ranked if item["kev"]),
            },
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
            raise CvesUnavailable("response too large")
        return result


def _validate_dataset(raw: object) -> tuple[dict[str, object], str, str]:
    supplied_id: str | None = None
    if isinstance(raw, CveDataset):
        supplied_id = raw.dataset_id
        raw = {key: value for key, value in asdict(raw).items() if key != "dataset_id"}
    if not isinstance(raw, dict) or set(raw) != {
        "kind",
        "kev_snapshot_complete",
        "source_as_of",
        "retrieved_at",
        "candidates",
    }:
        raise CvesUnavailable("invalid dataset")
    if raw["kind"] != "synthetic" or raw["kev_snapshot_complete"] is not True:
        raise CvesUnavailable("incomplete synthetic dataset")
    source_as_of = _timestamp(raw["source_as_of"], required=True)
    retrieved_at = _timestamp(raw["retrieved_at"], required=True)
    candidates = raw["candidates"]
    if not isinstance(candidates, list) or len(candidates) > MAX_CANDIDATES:
        raise CvesUnavailable("invalid candidates")
    validated = [_candidate(value) for value in candidates]
    ids = [item["cve_id"] for item in validated]
    if len(ids) != len(set(ids)):
        raise CvesUnavailable("duplicate cve")
    dataset = {
        "kind": "synthetic",
        "kev_snapshot_complete": True,
        "source_as_of": source_as_of,
        "retrieved_at": retrieved_at,
        "candidates": validated,
    }
    fingerprint = hashlib.sha256(_canonical_bytes(dataset)).hexdigest()
    dataset_id = supplied_id or f"sha256:{fingerprint}"
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", dataset_id):
        raise CvesUnavailable("invalid dataset id")
    return dataset, fingerprint, dataset_id


def _candidate(value: object) -> dict[str, object]:
    keys = {
        "cve_id",
        "title",
        "affected_products",
        "kev",
        "epss",
        "cvss",
        "published_at",
        "advisory_url",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise CvesUnavailable("invalid candidate")
    cve_id = _text(value["cve_id"], 64, trim=False)
    if not CVE_ID.fullmatch(cve_id):
        raise CvesUnavailable("invalid cve id")
    title = _text(value["title"], 300)
    products = value["affected_products"]
    if not isinstance(products, list) or not 1 <= len(products) <= MAX_PRODUCTS:
        raise CvesUnavailable("invalid products")
    validated_products = [_product(product) for product in products]
    pairs = [(item["vendor_key"], item["product_key"]) for item in validated_products]
    if len(pairs) != len(set(pairs)):
        raise CvesUnavailable("duplicate product")
    kev = _kev(value["kev"])
    epss = _epss(value["epss"])
    cvss = _cvss(value["cvss"])
    return {
        "cve_id": cve_id,
        "title": title,
        "affected_products": validated_products,
        "kev": kev,
        "epss": epss,
        "cvss": cvss,
        "published_at": _timestamp(value["published_at"], required=False),
        "advisory_url": _url(value["advisory_url"]),
    }


def _product(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"vendor", "product"}:
        raise CvesUnavailable("invalid product")
    vendor = _text(value["vendor"], 128)
    product = _text(value["product"], 256)
    return {
        "vendor": vendor,
        "product": product,
        "vendor_key": vendor.casefold(),
        "product_key": product.casefold(),
    }


def _kev(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"known_exploited", "source", "as_of", "due_date"}:
        raise CvesUnavailable("invalid kev")
    known = value["known_exploited"]
    if type(known) is not bool:
        raise CvesUnavailable("invalid kev")
    due = _date(value["due_date"], required=False)
    if not known and due is not None:
        raise CvesUnavailable("invalid kev due")
    return {
        "known_exploited": known,
        "source": _synthetic_kev_source(value["source"]),
        "as_of": _date(value["as_of"], required=True),
        "due_date": due,
    }


def _epss(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"score", "percentile", "as_of"}:
        raise CvesUnavailable("invalid epss")
    score = _finite(value["score"], 0, 1, nullable=True)
    percentile = _finite(value["percentile"], 0, 1, nullable=True)
    as_of = _date(value["as_of"], required=False)
    if score is None and (percentile is not None or as_of is not None):
        raise CvesUnavailable("invalid empty epss")
    if score is not None and as_of is None:
        raise CvesUnavailable("invalid epss date")
    return {"score": score, "percentile": percentile, "as_of": as_of}


def _cvss(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"base_score", "version"}:
        raise CvesUnavailable("invalid cvss")
    score = _finite(value["base_score"], 0, 10, nullable=True)
    version = value["version"]
    if (score is None and version is not None) or (score is not None and version not in {"3.1", "4.0"}):
        raise CvesUnavailable("invalid cvss")
    return {"base_score": score, "version": version}


def _rank_matches(
    candidates: object, technologies: tuple[Technology, ...], query: CveQuery
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    selected = technologies
    if query.asset_id is not None:
        selected = tuple(item for item in technologies if item.id == query.asset_id)
    for candidate in candidates:
        matches = []
        pairs = {(item["vendor_key"], item["product_key"]) for item in candidate["affected_products"]}
        for technology in selected:
            if (technology.vendor.casefold(), technology.product.casefold()) in pairs:
                matches.append(
                    {
                        "technology_id": technology.id,
                        "vendor": technology.vendor,
                        "product": technology.product,
                        "software_version": technology.software_version,
                        "match_reason": "vendor_product_exact_casefold",
                        "version_assessment": "not_performed",
                    }
                )
        if not matches:
            continue
        if query.kev is not None and candidate["kev"]["known_exploited"] is not query.kev:
            continue
        if (
            query.q is not None
            and query.q.casefold() not in (candidate["cve_id"] + " " + candidate["title"]).casefold()
        ):
            continue
        matches.sort(key=lambda item: item["technology_id"])
        results.append(
            {
                "cve_id": candidate["cve_id"],
                "title": candidate["title"],
                "kev": candidate["kev"]["known_exploited"],
                "kev_due_date": candidate["kev"]["due_date"],
                "kev_as_of": candidate["kev"]["as_of"],
                "epss_score": candidate["epss"]["score"],
                "epss_percentile": candidate["epss"]["percentile"],
                "epss_as_of": candidate["epss"]["as_of"],
                "cvss_base_score": candidate["cvss"]["base_score"],
                "cvss_version": candidate["cvss"]["version"],
                "published_at": candidate["published_at"],
                "advisory_url": candidate["advisory_url"],
                "matches": matches,
            }
        )
    results.sort(key=_rank_key)
    for priority, item in enumerate(results, 1):
        item["priority"] = priority
    return results


def _rank_key(item: dict[str, object]) -> tuple[object, ...]:
    epss = item["epss_score"]
    cvss = item["cvss_base_score"]
    published = item["published_at"]
    return (
        not item["kev"],
        epss is None,
        0 if epss is None else -epss,
        cvss is None,
        0 if cvss is None else -cvss,
        published is None,
        0 if published is None else -datetime.fromisoformat(published[:-1]).replace(tzinfo=UTC).timestamp(),
        item["cve_id"],
    )


def _summary_item(item: dict[str, object]) -> dict[str, object]:
    return {
        "cve_id": item["cve_id"],
        "title": item["title"],
        "kev": item["kev"],
        "epss_score": item["epss_score"],
        "cvss_base_score": item["cvss_base_score"],
        "priority": item["priority"],
        "match_count": len(item["matches"]),
    }


def _snapshot_hash(dataset_hash: str, technologies: tuple[Technology, ...]) -> str:
    content = {"dataset": dataset_hash, "technologies": [asdict(item) for item in technologies]}
    return hashlib.sha256(_canonical_bytes(content)).hexdigest()


def _context_hash(view: str, kev: object, asset_id: object, q: object, limit: int) -> str:
    content = {"view": view, "kev": kev, "asset_id": asset_id, "q": q, "limit": limit}
    return hashlib.sha256(_canonical_bytes(content)).hexdigest()


def _encode_cursor(snapshot: str, context: str, after: object) -> str:
    raw = _canonical_bytes({"v": 1, "snapshot": snapshot, "context": context, "after": after})
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode_cursor(value: str | None) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not value.isascii() or not 1 <= len(value) <= MAX_CURSOR_BYTES or "=" in value:
        raise InvalidCveQuery("invalid cursor")
    try:
        padding = "=" * (-len(value) % 4)
        raw = base64.b64decode(value + padding, altchars=b"-_", validate=True)
        parsed = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidCveQuery("invalid cursor") from exc
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value:
        raise InvalidCveQuery("non-canonical cursor")
    if not isinstance(parsed, dict) or set(parsed) != {"v", "snapshot", "context", "after"}:
        raise InvalidCveQuery("invalid cursor")
    if parsed["v"] != 1 or type(parsed["v"]) is not int:
        raise InvalidCveQuery("invalid cursor")
    if not all(isinstance(parsed[key], str) for key in ("snapshot", "context", "after")):
        raise InvalidCveQuery("invalid cursor")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", parsed["snapshot"])
        or not re.fullmatch(r"[0-9a-f]{64}", parsed["context"])
        or not CVE_ID.fullmatch(parsed["after"])
    ):
        raise InvalidCveQuery("invalid cursor")
    try:
        canonical = _canonical_bytes(parsed)
    except (TypeError, ValueError) as exc:
        raise InvalidCveQuery("invalid cursor") from exc
    if raw != canonical:
        raise InvalidCveQuery("non-canonical cursor json")
    return parsed


def _decimal(value: str | None, maximum: int) -> int | None:
    if value is None:
        return None
    if not re.fullmatch(r"[1-9][0-9]*", value) or len(value) > len(str(maximum)):
        raise InvalidCveQuery("invalid integer")
    parsed = int(value)
    if parsed > maximum:
        raise InvalidCveQuery("invalid integer")
    return parsed


def _text(value: object, maximum: int, *, trim: bool = True) -> str:
    if not isinstance(value, str) or _has_control(value):
        raise CvesUnavailable("invalid text")
    result = value.strip() if trim else value
    if not 1 <= len(result) <= maximum or (trim and result != value.strip()):
        raise CvesUnavailable("invalid text")
    return result


def _synthetic_kev_source(value: object) -> str:
    if value != SYNTHETIC_KEV_SOURCE:
        raise CvesUnavailable("invalid synthetic kev source")
    return SYNTHETIC_KEV_SOURCE


def _has_control(value: str) -> bool:
    return any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in value)


def _finite(value: object, minimum: float, maximum: float, *, nullable: bool) -> float | int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CvesUnavailable("invalid number")
    if not minimum <= value <= maximum:
        raise CvesUnavailable("number out of range")
    return value


def _timestamp(value: object, *, required: bool) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not WIRE_TIMESTAMP.fullmatch(value):
        raise CvesUnavailable("invalid timestamp")
    try:
        datetime.fromisoformat(value[:-1])
    except ValueError as exc:
        raise CvesUnavailable("invalid timestamp") from exc
    return value


def _date(value: object, *, required: bool) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not WIRE_DATE.fullmatch(value):
        raise CvesUnavailable("invalid date")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise CvesUnavailable("invalid date") from exc
    return value


def _url(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 2048 or _has_control(value):
        raise CvesUnavailable("invalid url")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
        username = parsed.username
        password = parsed.password
    except ValueError as exc:
        raise CvesUnavailable("invalid url") from exc
    authority = parsed.netloc
    if (
        parsed.scheme != "https"
        or not authority
        or not hostname
        or username is not None
        or password is not None
        or any(character.isspace() for character in authority)
        or "\\" in authority
        or "%" in authority
    ):
        raise CvesUnavailable("invalid url")
    del port  # Access above validates numeric syntax and the 0..65535 range.
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
