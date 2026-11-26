"""Nạp snapshot công khai KEV + NVD, không cần OpenCTI; không tải URL trong bản tin."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from portal_api.cves import CVE_ID, CveDataset, CvesUnavailable, _validate_dataset

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "cve-feed.json"
MAX_BYTES = 64 * 1024 * 1024
MAX_PAGE_BYTES = 24 * 1024 * 1024
MAX_RECORDS = 20000
MAX_PAGES = 40
PAGE_SIZE = 500
KEV_SOURCE = "CISA KEV"
NVD_NOTICE = "This product uses data from the NVD API but is not endorsed or certified by the NVD."


class FeedError(RuntimeError):
    """Nguồn lỗi hoặc vượt giới hạn; giữ snapshot cũ."""


def _stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _stamp(parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC))


def _clean(value: str, limit: int) -> str:
    text = "".join(" " if unicodedata.category(c) in {"Cc", "Cf", "Cs"} else c for c in value)
    return " ".join(text.split())[:limit].strip()


def _retry_delay(header: str | None, attempt: int) -> float:
    delay = float(2**attempt)
    if header:
        try:
            seconds = float(int(header))
        except ValueError:
            try:
                seconds = (parsedate_to_datetime(header) - datetime.now(UTC)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                seconds = 0
        delay = max(delay, seconds)
    return delay


class Fetcher:
    """Chỉ hai endpoint cố định; TLS mặc định, không redirect, key không vào URL/log."""

    def __init__(self, client: httpx.Client) -> None:
        self.client = client
        self.deadline = time.monotonic() + 420
        self.next_nvd = 0.0

    def _wait(self, seconds: float) -> None:
        seconds = max(0, seconds)
        if time.monotonic() + seconds > self.deadline:
            raise FeedError("Hết thời gian nạp; giữ snapshot cũ")
        time.sleep(seconds)

    def _read(self, url: str, params: dict | None, headers: dict) -> dict:
        with self.client.stream(
            "GET", url, params=params, headers=headers, follow_redirects=False
        ) as response:
            response.raise_for_status()
            chunks = bytearray()
            for chunk in response.iter_bytes(65536):
                chunks.extend(chunk)
                if len(chunks) > MAX_PAGE_BYTES or time.monotonic() > self.deadline:
                    raise FeedError("Response vượt giới hạn kích thước/thời gian")
        data = json.loads(chunks)
        if not isinstance(data, dict):
            raise FeedError("JSON nguồn không phải object")
        return data

    def __call__(self, url: str, params: dict | None = None) -> dict:
        if url not in {KEV_URL, NVD_URL} or urlsplit(url).scheme != "https":
            raise FeedError("Endpoint không được phép")
        headers = {"User-Agent": "PhongHoaCTI/0.1 (academic)", "Accept": "application/json"}
        if url == NVD_URL and os.environ.get("NVD_API_KEY"):
            headers["apiKey"] = os.environ["NVD_API_KEY"]
        for attempt in range(3):
            self._wait(self.next_nvd - time.monotonic() if url == NVD_URL else 0)
            if url == NVD_URL:
                self.next_nvd = time.monotonic() + 6.1
            try:
                return self._read(url, params, headers)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise FeedError(f"HTTP {status} từ {urlsplit(url).hostname}") from None
                self._wait(_retry_delay(exc.response.headers.get("Retry-After"), attempt))
            except httpx.RequestError:
                if attempt == 2:
                    raise FeedError(f"Không kết nối được {urlsplit(url).hostname}") from None
                self._wait(2**attempt)
        raise FeedError("Hết lượt retry")


def _nvd_pages(fetch: Callable, now: datetime, days: int):
    offset = 0
    total = None
    for _ in range(MAX_PAGES):
        params = {
            "pubStartDate": (now - timedelta(days=days)).isoformat(timespec="milliseconds"),
            "pubEndDate": now.isoformat(timespec="milliseconds"),
            "resultsPerPage": PAGE_SIZE,
            "startIndex": offset,
        }
        page = fetch(NVD_URL, params)
        rows = page["vulnerabilities"]
        if total is None:
            total = page["totalResults"]
        if (
            type(total) is not int
            or not 0 <= total <= MAX_RECORDS
            or page["totalResults"] != total
            or page["startIndex"] != offset
            or not isinstance(rows, list)
            or len(rows) > PAGE_SIZE
            or offset + len(rows) > total
        ):
            raise FeedError("Phân trang NVD không nhất quán hoặc quá lớn")
        yield from rows
        offset += len(rows)
        if offset == total:
            return
        if not rows:
            raise FeedError("Thiếu trang NVD")
    raise FeedError("Vượt giới hạn trang NVD")


def _base(cve_id: str, title: str, as_of: str) -> dict:
    if not CVE_ID.fullmatch(cve_id):
        raise FeedError("CVE ID không hợp lệ")
    return {
        "cve_id": cve_id,
        "title": _clean(title, 300) or cve_id,
        "affected_products": [],
        "kev": {"known_exploited": False, "source": KEV_SOURCE, "as_of": as_of, "due_date": None},
        "epss": {"score": None, "percentile": None, "as_of": None},
        "cvss": {"base_score": None, "version": None},
        "published_at": None,
        "advisory_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        "provenance": {"sources": [], "kev_date_added": None},
    }


def _add_product(record: dict, vendor: str, product: str) -> None:
    vendor, product = _clean(vendor, 128), _clean(product, 256)
    if not vendor or not product or vendor in {"*", "-"} or product in {"*", "-"}:
        return
    pairs = {(x["vendor"].casefold(), x["product"].casefold()) for x in record["affected_products"]}
    if (vendor.casefold(), product.casefold()) not in pairs:
        record["affected_products"].append({"vendor": vendor, "product": product})


def _source(name: str, now: str) -> dict:
    if name == KEV_SOURCE:
        return {"name": name, "url": KEV_URL, "retrieved_at": now, "attribution": "CISA KEV (CC0 1.0)"}
    return {"name": "NVD", "url": NVD_URL, "retrieved_at": now, "attribution": NVD_NOTICE}


def _kev_records(feed: dict, stamp: str) -> tuple[str, dict]:
    released = _timestamp(feed["dateReleased"])
    rows = feed["vulnerabilities"]
    if not isinstance(rows, list) or not 0 < len(rows) == feed["count"] <= MAX_RECORDS:
        raise FeedError("Catalog KEV không đầy đủ")
    result = {}
    for row in rows:
        record = _base(row["cveID"], row["vulnerabilityName"], released[:10])
        if record["cve_id"] in result:
            raise FeedError("CVE trùng trong KEV")
        _add_product(record, row["vendorProject"], row["product"])
        record["kev"].update(known_exploited=True, due_date=row["dueDate"])
        record["advisory_url"] = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
        record["provenance"] = {"sources": [_source(KEV_SOURCE, stamp)], "kev_date_added": row["dateAdded"]}
        result[record["cve_id"]] = record
    return released, result


def _cpe_parts(criteria: str) -> tuple[str, str] | None:
    # CPE formatted string: chỉ lấy vendor/product, không suy luận version hoặc biểu thức wildcard.
    parts = []
    current = ""
    escaped = False
    for char in criteria:
        if escaped:
            current += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    if escaped or len(parts) != 13 or parts[:2] != ["cpe", "2.3"]:
        return None
    vendor, product = parts[3:5]
    if any(char in vendor + product for char in "*?"):
        return None
    return vendor.replace("_", " "), product.replace("_", " ")


def _add_nvd_products(record: dict, cve: dict) -> None:
    for config in cve.get("configurations", []):
        for node in config.get("nodes", []):
            if config.get("negate") is True or node.get("negate") is True:
                continue
            for match in node.get("cpeMatch", []):
                if match.get("vulnerable") is True:
                    pair = _cpe_parts(match["criteria"])
                    if pair:
                        _add_product(record, *pair)


def _cvss(cve: dict) -> dict:
    metrics = cve.get("metrics", {})
    for key, version in (("cvssMetricV40", "4.0"), ("cvssMetricV31", "3.1")):
        values = metrics.get(key, [])
        if values:
            value = next((x for x in values if x.get("type") == "Primary"), values[0])
            return {"base_score": value["cvssData"]["baseScore"], "version": version}
    return {"base_score": None, "version": None}


def _merge_nvd(records: dict, rows, released: str, stamp: str) -> int:
    seen = set()
    for row in rows:
        cve = row["cve"]
        cve_id = cve["id"]
        if cve_id in seen:
            raise FeedError("CVE trùng giữa các trang NVD")
        seen.add(cve_id)
        description = next((x["value"] for x in cve.get("descriptions", []) if x["lang"] == "en"), cve_id)
        record = records.setdefault(cve_id, _base(cve_id, description, released[:10]))
        record["published_at"] = _timestamp(cve["published"])
        record["cvss"] = _cvss(cve)
        record["provenance"]["sources"].append(_source("NVD", stamp))
        if cve.get("vulnStatus") != "Rejected":
            _add_nvd_products(record, cve)
    return len(seen)


def _dataset(raw: bytes) -> CveDataset:
    data = json.loads(raw)
    keys = {"kind", "kev_snapshot_complete", "source_as_of", "retrieved_at", "candidates"}
    if not isinstance(data, dict) or set(data) != keys or data["kind"] != "imported":
        raise CvesUnavailable("invalid imported snapshot")
    result = CveDataset(**data, dataset_id="sha256:" + hashlib.sha256(raw).hexdigest())
    _validate_dataset(result)
    return result


class ImportedCveReadPort:
    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self.path = Path(path)

    def list_candidates(self) -> CveDataset:
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise CvesUnavailable("imported snapshot too large")
            return _dataset(raw)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
            raise CvesUnavailable("imported snapshot unavailable") from exc


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def import_snapshot(path: Path, days: int, fetch: Callable, now: datetime) -> dict:
    if not 7 <= days <= 30:
        raise FeedError("Chọn khoảng NVD 7–30 ngày")
    stamp = _stamp(now)
    released, records = _kev_records(fetch(KEV_URL), stamp)
    kev_count = len(records)
    nvd_count = _merge_nvd(records, _nvd_pages(fetch, now, days), released, stamp)
    snapshot = {
        "kind": "imported",
        "kev_snapshot_complete": True,
        "source_as_of": released,
        "retrieved_at": stamp,
        "candidates": [records[key] for key in sorted(records)],
    }
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise FeedError("Snapshot vượt giới hạn")
    _dataset(raw)
    _atomic_write(path, raw)
    examples = sorted(
        (
            {"cve": r["cve_id"], "date_added": r["provenance"]["kev_date_added"]}
            for r in records.values()
            if r["kev"]["known_exploited"]
        ),
        key=lambda r: (r["date_added"], r["cve"]),
        reverse=True,
    )[:3]
    return {
        "kev": kev_count,
        "nvd": nvd_count,
        "unique": len(records),
        "retrieved_at": stamp,
        "examples": examples,
        "without_products": sum(not r["affected_products"] for r in records.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kev", action="store_true", required=True)
    parser.add_argument("--nvd-days", type=int, default=7, choices=range(7, 31))
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        with httpx.Client(timeout=httpx.Timeout(20.0), follow_redirects=False, trust_env=False) as client:
            result = import_snapshot(args.path, args.nvd_days, Fetcher(client), datetime.now(UTC))
    except (FeedError, CvesUnavailable, ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Import failed: {exc if isinstance(exc, FeedError) else type(exc).__name__}")
        return 1
    result["elapsed_seconds"] = round(time.monotonic() - started, 2)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
