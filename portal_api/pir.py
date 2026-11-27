"""F22: hồ sơ PIR (Priority Intelligence Requirements) cho một lần triển khai và hàm chấm CVE.

Hồ sơ chỉ là dữ liệu cấu hình do admin nhập; hàm ``score_cves`` là hàm thuần (không I/O),
chỉ sắp xếp lại danh sách đã có, không thêm/bớt CVE nào.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

LIST_FIELDS = ("vendors", "products", "sectors", "keywords")
MAX_ITEMS = 50
MAX_ITEM_LEN = 128
WEIGHTS = {"vendor": 40, "product": 40, "keyword": 15, "severity": 20}

SCHEMA = """
CREATE TABLE IF NOT EXISTS pir_profile(
  id INTEGER PRIMARY KEY CHECK (id = 1),
  body TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL
);
"""


class InvalidPirProfile(ValueError):
    """Hồ sơ PIR sai cấu trúc."""


def _clean_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise InvalidPirProfile(label)
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise InvalidPirProfile(label)
        text = item.strip()
        if not 1 <= len(text) <= MAX_ITEM_LEN or any(ord(c) < 32 or ord(c) == 127 for c in text):
            raise InvalidPirProfile(label)
        if text.casefold() not in {existing.casefold() for existing in cleaned}:
            cleaned.append(text)
    return cleaned


def validate_profile(body: object) -> dict:
    """Chỉ nhận đúng các khóa đã biết; ``min_cvss`` là số 0–10 hoặc null."""
    if not isinstance(body, dict) or set(body) - {*LIST_FIELDS, "min_cvss"}:
        raise InvalidPirProfile("keys")
    profile: dict[str, object] = {field: _clean_list(body.get(field, []), field) for field in LIST_FIELDS}
    min_cvss = body.get("min_cvss")
    if min_cvss is not None and (
        isinstance(min_cvss, bool) or not isinstance(min_cvss, (int, float)) or not 0 <= min_cvss <= 10
    ):
        raise InvalidPirProfile("min_cvss")
    profile["min_cvss"] = None if min_cvss is None else float(min_cvss)
    return profile


def _matched(needles: Iterable[str], haystack: Iterable[str]) -> list[str]:
    keys = {value.casefold() for value in haystack}
    return [needle for needle in needles if needle.casefold() in keys]


def score_cve(item: Mapping[str, object], profile: Mapping[str, object]) -> tuple[int, list[str]]:
    """Điểm PIR của một CVE (dạng item W03) và lý do khớp, để người dùng hiểu vì sao."""
    matches = item.get("matches") or []
    vendors = [str(match.get("vendor", "")) for match in matches if isinstance(match, Mapping)]
    products = [str(match.get("product", "")) for match in matches if isinstance(match, Mapping)]
    reasons: list[str] = []
    score = 0
    for label, needles, haystack in (
        ("vendor", profile["vendors"], vendors),
        ("product", profile["products"], products),
    ):
        hit = _matched(needles, haystack)
        if hit:
            score += WEIGHTS[label]
            reasons.append(f"{label}:{hit[0]}")
    text = f"{item.get('cve_id', '')} {item.get('title', '')}".casefold()
    keywords = [kw for kw in profile["keywords"] if kw.casefold() in text]
    if keywords:
        score += WEIGHTS["keyword"]
        reasons.append(f"keyword:{keywords[0]}")
    cvss = item.get("cvss_base_score")
    floor = profile.get("min_cvss")
    if floor is not None and isinstance(cvss, (int, float)) and cvss >= floor:
        score += WEIGHTS["severity"]
        reasons.append(f"cvss>={floor:g}")
    return score, reasons


def score_cves(items: list[Mapping[str, object]], profile: Mapping[str, object]) -> list[dict]:
    """Trả bản sao đã gắn ``pir_score``/``pir_reasons``, sắp điểm giảm dần.

    Sắp xếp ổn định: cùng điểm thì giữ thứ tự ưu tiên W03 ban đầu.
    """
    scored = []
    for item in items:
        score, reasons = score_cve(item, profile)
        scored.append({**item, "pir_score": score, "pir_reasons": reasons})
    return sorted(scored, key=lambda entry: -entry["pir_score"])


def _utc_now() -> datetime:
    return datetime.now(UTC)


class PirStore:
    """Một hồ sơ PIR duy nhất cho mỗi triển khai (single-tenant theo W00)."""

    def __init__(
        self, path: str | Path, *, timeout: float = 5.0, clock: Callable[[], datetime] = _utc_now
    ) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.clock = clock

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def get(self) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM pir_profile WHERE id=1").fetchone()
        if row is None:
            return None
        return {**json.loads(row["body"]), "updated_at": row["updated_at"], "updated_by": row["updated_by"]}

    def put(self, body: object, actor: str) -> dict:
        profile = validate_profile(body)
        stamp = self.clock().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO pir_profile(id,body,updated_at,updated_by) VALUES(1,?,?,?)"
                " ON CONFLICT(id) DO UPDATE SET body=excluded.body,"
                " updated_at=excluded.updated_at, updated_by=excluded.updated_by",
                (json.dumps(profile, sort_keys=True, ensure_ascii=False), stamp, actor),
            )
        return {**profile, "updated_at": stamp, "updated_by": actor}

    def delete(self) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM pir_profile WHERE id=1")
        return cursor.rowcount > 0
