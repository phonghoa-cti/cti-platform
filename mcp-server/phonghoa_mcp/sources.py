"""Cổng dữ liệu chỉ đọc: fixture và OpenCTI/portal."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from phonghoa_core import Ioc, normalize
from portal_api.ioc_lookup import IT_TLPS, LookupRecord, LookupService, SourceFact

NOTICE = "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá."
AS_OF = datetime(2026, 11, 26, tzinfo=UTC)
MAX_ROWS = 100


class SourceUnavailable(RuntimeError):
    """Không thể đọc nguồn hoặc chưa cấu hình quyền đọc."""


class ReadSource(Protocol):
    mode: str

    def ioc(self, value: Ioc) -> dict: ...
    def cves(self, technology: str | None, kev_only: bool, limit: int) -> dict: ...
    def drafts(self, limit: int) -> dict: ...
    def reports(self, query: str, limit: int) -> dict: ...
    def events(self, since: datetime, limit: int) -> dict: ...
    def now(self) -> datetime: ...


def visible(row: dict) -> bool:
    return row.get("tlp") in IT_TLPS


def page(rows: list, limit: int, *, partial: bool = False) -> dict:
    return {"items": rows[:limit], "partial": partial or len(rows) > limit}


def lookup_payload(value: Ioc, result: dict) -> dict:
    # Không đưa dạng raw (có thể bấm được) sang agent.
    return {**result, "ioc": {"type": value.type.value, "display": value.display()}}


class FixtureSource:
    mode = "fixture"

    def __init__(self) -> None:
        path = Path(__file__).with_name("fixture.json")
        self._data = json.loads(path.read_text(encoding="utf-8"))
        self._lookup = LookupService(self)

    def now(self) -> datetime:
        return AS_OF

    def lookup(self, ioc: Ioc, allowed_tlps: frozenset[str]) -> LookupRecord | None:
        for row in self._data["iocs"]:
            if row["tlp"] not in allowed_tlps or normalize(row["value"]) != ioc:
                continue
            fact = SourceFact("fixture-1", "Nguồn giả lập", 0.9, AS_OF, AS_OF, row["tlp"])
            return LookupRecord(ioc, row["tlp"], (fact,), (), (), AS_OF)
        return None

    def ioc(self, value: Ioc) -> dict:
        result = self._lookup.lookup(value.value, frozenset({"it"})).model_dump(mode="json")
        return lookup_payload(value, result)

    def cves(self, technology: str | None, kev_only: bool, limit: int) -> dict:
        rows = [
            row
            for row in self._data["cves"]
            if visible(row)
            and (not kev_only or row["kev"])
            and (
                technology is None
                or technology.casefold() in {row["technology"].casefold(), row["asset"].casefold()}
            )
        ]
        return {**page(rows, limit), "notice": NOTICE, "dataset_kind": "synthetic"}

    def drafts(self, limit: int) -> dict:
        rows = [row for row in self._data["drafts"] if visible(row) and row["status"] == "pending"]
        return page(rows, limit)

    def reports(self, query: str, limit: int) -> dict:
        rows = [
            row
            for row in self._data["reports"]
            if visible(row) and query.casefold() in (row["name"] + " " + row["description"]).casefold()
        ]
        return page(rows, limit)

    def events(self, since: datetime, limit: int) -> dict:
        rows = [
            row
            for row in self._data["events"]
            if visible(row) and since < datetime.fromisoformat(row["timestamp"])
        ]
        return page(rows, limit)


def _tlp(row: dict) -> str | None:
    markings = row.get("objectMarking")
    if not isinstance(markings, list) or not markings:
        return None
    labels = [item.get("definition") if isinstance(item, dict) else None for item in markings]
    # TLP:WHITE là cách ghi CLEAR của STIX 2.1 cũ.
    labels = ["TLP:CLEAR" if label == "TLP:WHITE" else label for label in labels]
    if not all(isinstance(label, str) and label in IT_TLPS for label in labels):
        return None
    return "TLP:GREEN" if "TLP:GREEN" in labels else "TLP:CLEAR"


def _text(row: dict, key: str, size: int = 256) -> str:
    value = row.get(key)
    return value[:size] if isinstance(value, str) else ""


def _retry(call):
    for attempt in range(2):
        try:
            return call()
        except Exception:
            if attempt == 0:
                time.sleep(0.25)
    raise SourceUnavailable("read failed")


class PortalReader:
    """Chỉ gọi các GET cố định; token phải thuộc tài khoản đọc tối thiểu."""

    def __init__(self, url: str, token: str) -> None:
        self._url = _https_url(url)
        self._token = token

    def get(self, path: str, params: dict) -> dict:
        if path not in {"/api/ioc", "/api/cves", "/api/drafts"}:
            raise SourceUnavailable("route not permitted")

        def read():
            with httpx.Client(timeout=5, follow_redirects=False, trust_env=False) as client:
                with client.stream(
                    "GET",
                    self._url + path,
                    params=params,
                    headers={"Cf-Access-Jwt-Assertion": self._token, "X-API-Key": self._token},
                ) as response:
                    response.raise_for_status()
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 1024 * 1024:
                            raise SourceUnavailable("response too large")
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise SourceUnavailable("invalid response")
                return result

        return _retry(read)


class OpenCtiSource:
    """Đọc bằng SDK pycti; không dùng mutation, không tải URL của báo cáo."""

    mode = "opencti"

    def __init__(self, client, portal: PortalReader | None = None) -> None:
        self._client = client
        self._portal = portal
        self._cache: dict = {}

    def now(self) -> datetime:
        return datetime.now(UTC)

    def _list(self, entity: str, **kwargs) -> list:
        key = (entity, json.dumps(kwargs, sort_keys=True))
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached is not None and now - cached[0] < 30:
            return cached[1]
        api = getattr(self._client, entity)
        rows = _retry(lambda: api.list(first=MAX_ROWS, getAll=False, **kwargs))
        if (
            not isinstance(rows, list)
            or len(rows) > MAX_ROWS
            or not all(isinstance(row, dict) for row in rows)
        ):
            raise SourceUnavailable("invalid list response")
        if len(self._cache) >= 64:
            self._cache.clear()
        self._cache[key] = (now, rows)
        return rows

    def _portal_read(self, path: str, params: dict) -> dict:
        if self._portal is None:
            raise SourceUnavailable("portal read endpoint not configured")
        return self._portal.get(path, params)

    def ioc(self, value: Ioc) -> dict:
        if self._portal is not None:
            result = self._portal_read("/api/ioc", {"value": value.value})
            if result.get("state") == "found" and not visible(result):
                return lookup_payload(value, {"state": "not_found", "score": None, "sources": []})
            return lookup_payload(
                value,
                {
                    "state": result.get("state"),
                    "score": result.get("score"),
                    "sources": [r for r in result.get("sources", []) if visible(r)],
                    "tlp": result.get("tlp"),
                },
            )
        rows = self._list(
            "stix_cyber_observable",
            search=value.value,
            customAttributes="id observable_value objectMarking { definition }",
        )
        matches = [row for row in rows if _tlp(row) and row.get("observable_value") == value.value]
        return lookup_payload(
            value,
            {
                "state": "found" if matches else "not_found",
                "score": None,
                "sources": [{"name": "OpenCTI", "id": _text(row, "id"), "tlp": _tlp(row)} for row in matches],
                "reason": "Chưa có facts nguồn để tính điểm Phong Hỏa; không suy điểm từ confidence.",
                "partial": len(rows) == MAX_ROWS,
            },
        )

    def cves(self, technology: str | None, kev_only: bool, limit: int) -> dict:
        params = {"limit": MAX_ROWS}
        if kev_only:
            params["kev"] = "true"
        data = self._portal_read("/api/cves", params)
        if data.get("view") != "detail":
            raise SourceUnavailable("detail view required")
        rows = []
        for row in data["items"]:
            matches = row["matches"]
            if technology is not None:
                matches = [
                    m
                    for m in matches
                    if technology.casefold()
                    in {
                        str(m.get("product", "")).casefold(),
                        str(m.get("technology_id", "")),
                        (str(m.get("vendor", "")) + " " + str(m.get("product", ""))).casefold(),
                    }
                ]
            if matches and (not kev_only or row.get("kev") is True):
                rows.append(
                    {
                        "id": row["cve_id"],
                        "title": row["title"],
                        "kev": row["kev"],
                        "matches": [
                            {"technology_id": m["technology_id"], "product": m["product"]} for m in matches
                        ],
                    }
                )
        return {
            **page(rows, limit, partial=bool(data["page"]["next_cursor"])),
            "notice": NOTICE,
            "dataset_kind": data["source"]["kind"],
        }

    def drafts(self, limit: int) -> dict:
        data = self._portal_read("/api/drafts", {"limit": MAX_ROWS})
        rows = [
            {
                "id": row["id"],
                "status": "pending",
                "tlp": row["tlp"],
                "source": row["source"]["name"],
                "item_count": row["item_count"],
                "injection_warning": row["injection_warning"],
            }
            for row in data["items"]
            if visible(row) and row["status"] == "pending"
        ]
        return page(rows, limit, partial=data["next_before_id"] is not None)

    def reports(self, query: str, limit: int) -> dict:
        rows = self._list(
            "report",
            search=query,
            customAttributes="id name description published objectMarking { definition }",
        )
        items = [
            {
                "id": _text(row, "id"),
                "name": _text(row, "name"),
                "description": _text(row, "description", 1500),
                "published": _text(row, "published"),
                "tlp": _tlp(row),
            }
            for row in rows
            if _tlp(row)
        ]
        return page(items, limit, partial=len(rows) == MAX_ROWS)

    def events(self, since: datetime, limit: int) -> dict:
        # Chưa có event stream Wazuh/KEV/IOC liên quan tài sản live.
        raise SourceUnavailable("live event stream not configured")


def _https_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise SourceUnavailable("HTTPS endpoint required")
    if parts.query or parts.fragment:
        raise SourceUnavailable("invalid endpoint")
    return value.rstrip("/")


def source_from_env() -> ReadSource:
    mode = os.environ.get("PHONGHOA_MCP_SOURCE", "fixture")
    if mode == "fixture":
        return FixtureSource()
    if mode != "opencti":
        raise SourceUnavailable("unknown source")
    url, token = os.environ.get("OPENCTI_URL"), os.environ.get("OPENCTI_TOKEN")
    if not url or not token:
        raise SourceUnavailable("missing OpenCTI configuration")
    from pycti import OpenCTIApiClient

    client = OpenCTIApiClient(_https_url(url), token, ssl_verify=True, requests_timeout=5, log_level="error")
    portal_url, portal_token = os.environ.get("PHONGHOA_PORTAL_URL"), os.environ.get("PHONGHOA_PORTAL_TOKEN")
    if bool(portal_url) != bool(portal_token):
        raise SourceUnavailable("incomplete portal configuration")
    portal = PortalReader(portal_url, portal_token) if portal_url and portal_token else None
    return OpenCtiSource(client, portal)
