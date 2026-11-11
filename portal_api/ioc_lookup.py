"""Tra cứu IOC chỉ đọc với hậu kiểm quyền TLP tại service."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from pydantic import ValidationError

from phonghoa_core import Allowlist, Ioc, ScoreInput, normalize, score
from portal_api.schemas import (
    AssetMatchView,
    IocLookupResponse,
    IocSourceView,
    IocView,
    RelatedView,
    ScoreParts,
    ScoreView,
)

TLP_ORDER = {
    "TLP:CLEAR": 0,
    "TLP:GREEN": 1,
    "TLP:AMBER": 2,
    "TLP:AMBER+STRICT": 3,
    "TLP:RED": 4,
}
ALL_TLPS = frozenset(TLP_ORDER)
IT_TLPS = frozenset({"TLP:CLEAR", "TLP:GREEN"})
RELATED_KINDS = frozenset({"technique", "malware", "actor"})


class InvalidIoc(ValueError):
    """Giá trị query không thể chuẩn hóa thành IOC hợp lệ."""


class PrivateIoc(InvalidIoc):
    """IOC là IP không định tuyến công khai."""


class LookupUnavailable(RuntimeError):
    """Adapter hoặc dữ liệu tra cứu không đáng tin để trả ra."""


@dataclass(frozen=True)
class SourceFact:
    source_id: str
    name: str
    reliability: float
    first_seen: datetime
    last_seen: datetime
    tlp: str


@dataclass(frozen=True)
class RelatedFact:
    kind: str
    value: str
    tlp: str


@dataclass(frozen=True)
class AssetFact:
    name: str
    tlp: str


@dataclass(frozen=True)
class LookupRecord:
    ioc: Ioc
    record_tlp: str
    sources: tuple[SourceFact, ...]
    related: tuple[RelatedFact, ...]
    assets: tuple[AssetFact, ...]
    as_of: datetime


class IocLookupPort(Protocol):
    def lookup(self, ioc: Ioc, allowed_tlps: frozenset[str]) -> LookupRecord | None: ...


class LookupService:
    """Chuẩn hóa, kiểm tra TLP và tính score chỉ từ facts visible."""

    def __init__(
        self,
        lookup_port: IocLookupPort | None,
        *,
        allowlist: Allowlist | None = None,
    ) -> None:
        self._lookup_port = lookup_port
        self._allowlist = allowlist or Allowlist.default()

    def lookup(self, raw: str, roles: frozenset[str]) -> IocLookupResponse:
        ioc = self._normalize(raw)
        if self._allowlist.contains(ioc):
            return self._allowlisted(ioc)
        allowed_tlps = _allowed_tlps(roles)
        if self._lookup_port is None:
            raise LookupUnavailable("lookup port is not configured")
        try:
            record = self._lookup_port.lookup(ioc, allowed_tlps)
        except Exception as exc:
            raise LookupUnavailable("lookup adapter failed") from exc
        if record is None:
            return self._not_found(ioc)
        try:
            return self._from_record(ioc, record, allowed_tlps)
        except LookupUnavailable:
            raise
        except (TypeError, ValueError, ValidationError, OverflowError) as exc:
            raise LookupUnavailable("lookup record is invalid") from exc

    @staticmethod
    def _normalize(raw: str) -> Ioc:
        if not isinstance(raw, str) or not raw or len(raw) > 4096:
            raise InvalidIoc("invalid raw IOC")
        try:
            ioc = normalize(raw)
        except ValueError as exc:
            if "IP không định tuyến công khai" in str(exc):
                raise PrivateIoc("private IP") from exc
            raise InvalidIoc("invalid IOC") from exc
        display = ioc.display()
        if not 1 <= len(ioc.value) <= 2048 or not 1 <= len(display) <= 4096:
            raise InvalidIoc("normalized IOC exceeds bounds")
        return ioc

    @staticmethod
    def _allowlisted(ioc: Ioc) -> IocLookupResponse:
        result = score(
            ScoreInput(
                ioc_type=ioc.type,
                reliability=0,
                confirmations=0,
                days_since_last_seen=0,
                allowlisted=True,
            )
        )
        return _response(
            ioc=ioc,
            state="allowlisted",
            score_view=ScoreView(value=result.score, level="low", reason=result.reason, parts=None),
            tlp="TLP:CLEAR",
        )

    @staticmethod
    def _not_found(ioc: Ioc) -> IocLookupResponse:
        return _response(ioc=ioc, state="not_found")

    def _from_record(
        self,
        ioc: Ioc,
        record: LookupRecord,
        allowed_tlps: frozenset[str],
    ) -> IocLookupResponse:
        _validate_record_header(record, ioc)
        if record.record_tlp not in allowed_tlps:
            return self._not_found(ioc)
        _validate_nested_facts(record)

        visible_sources = _dedupe_sources(tuple(item for item in record.sources if item.tlp in allowed_tlps))
        visible_related = tuple(item for item in record.related if item.tlp in allowed_tlps)
        visible_assets = tuple(item for item in record.assets if item.tlp in allowed_tlps)
        if not visible_sources:
            return self._not_found(ioc)

        latest = max(item.last_seen for item in visible_sources)
        reliability = sum(float(item.reliability) for item in visible_sources) / len(visible_sources)
        result = score(
            ScoreInput(
                ioc_type=ioc.type,
                reliability=reliability,
                confirmations=len(visible_sources),
                days_since_last_seen=(record.as_of - latest).total_seconds() / 86_400,
                asset_match=bool(visible_assets),
            )
        )
        level = "low" if result.score <= 39 else "medium" if result.score <= 69 else "high"
        markings = [record.record_tlp]
        markings.extend(item.tlp for item in visible_sources)
        markings.extend(item.tlp for item in visible_related)
        markings.extend(item.tlp for item in visible_assets)
        output_tlp = max(markings, key=TLP_ORDER.__getitem__)
        grouped = {
            "technique": [item.value for item in visible_related if item.kind == "technique"],
            "malware": [item.value for item in visible_related if item.kind == "malware"],
            "actor": [item.value for item in visible_related if item.kind == "actor"],
        }
        return IocLookupResponse(
            ioc=IocView(type=ioc.type.value, value=ioc.value, display=ioc.display()),
            state="found",
            found=True,
            allowlisted=False,
            score=ScoreView(
                value=result.score,
                level=level,
                reason=result.reason,
                parts=ScoreParts(**result.parts),
            ),
            sources=[
                IocSourceView(
                    name=item.name,
                    first_seen=item.first_seen,
                    last_seen=item.last_seen,
                    tlp=item.tlp,
                )
                for item in visible_sources
            ],
            related=RelatedView(
                techniques=grouped["technique"],
                malware=grouped["malware"],
                actors=grouped["actor"],
            ),
            asset_match=AssetMatchView(
                matched=bool(visible_assets),
                assets=[item.name for item in visible_assets],
            ),
            tlp=output_tlp,
        )


def _allowed_tlps(roles: frozenset[str]) -> frozenset[str]:
    if roles.intersection({"analyst", "admin"}):
        return ALL_TLPS
    return IT_TLPS


def _response(
    *,
    ioc: Ioc,
    state: str,
    score_view: ScoreView | None = None,
    tlp: str | None = None,
) -> IocLookupResponse:
    return IocLookupResponse(
        ioc=IocView(type=ioc.type.value, value=ioc.value, display=ioc.display()),
        state=state,
        found=state == "found",
        allowlisted=state == "allowlisted",
        score=score_view,
        sources=[],
        related=RelatedView(techniques=[], malware=[], actors=[]),
        asset_match=AssetMatchView(matched=False, assets=[]),
        tlp=tlp,
    )


def _validate_record_header(record: LookupRecord, expected_ioc: Ioc) -> None:
    if not isinstance(record, LookupRecord) or record.ioc != expected_ioc:
        raise LookupUnavailable("lookup record IOC does not match")
    _validate_tlp(record.record_tlp)
    _validate_utc(record.as_of)
    if not isinstance(record.sources, tuple) or len(record.sources) > 100:
        raise LookupUnavailable("invalid source list")
    if not isinstance(record.related, tuple) or len(record.related) > 300:
        raise LookupUnavailable("invalid related list")
    if not isinstance(record.assets, tuple) or len(record.assets) > 100:
        raise LookupUnavailable("invalid asset list")


def _validate_nested_facts(record: LookupRecord) -> None:
    for source in record.sources:
        _validate_source(source, record.as_of)
    counts = {kind: 0 for kind in RELATED_KINDS}
    for item in record.related:
        _validate_related(item)
        counts[item.kind] += 1
        if counts[item.kind] > 100:
            raise LookupUnavailable("too many related facts")
    for item in record.assets:
        _validate_asset(item)


def _validate_source(source: SourceFact, as_of: datetime) -> None:
    if not isinstance(source, SourceFact):
        raise LookupUnavailable("invalid source fact")
    _bounded_text(source.source_id)
    _bounded_text(source.name)
    if (
        isinstance(source.reliability, bool)
        or not isinstance(source.reliability, (int, float))
        or not math.isfinite(source.reliability)
        or not 0 <= source.reliability <= 1
    ):
        raise LookupUnavailable("invalid source reliability")
    _validate_utc(source.first_seen)
    _validate_utc(source.last_seen)
    if source.first_seen > source.last_seen or source.last_seen > as_of:
        raise LookupUnavailable("invalid source chronology")
    _validate_tlp(source.tlp)


def _validate_related(item: RelatedFact) -> None:
    if not isinstance(item, RelatedFact) or item.kind not in RELATED_KINDS:
        raise LookupUnavailable("invalid related fact")
    _bounded_text(item.value)
    _validate_tlp(item.tlp)


def _validate_asset(item: AssetFact) -> None:
    if not isinstance(item, AssetFact):
        raise LookupUnavailable("invalid asset fact")
    _bounded_text(item.name)
    _validate_tlp(item.tlp)


def _bounded_text(value: object) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise LookupUnavailable("invalid bounded text")


def _validate_tlp(value: object) -> None:
    if not isinstance(value, str) or value not in TLP_ORDER:
        raise LookupUnavailable("unknown TLP")


def _validate_utc(value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise LookupUnavailable("timestamp must be UTC")
    if value.tzinfo is not UTC:
        value.astimezone(UTC)


def _dedupe_sources(sources: tuple[SourceFact, ...]) -> tuple[SourceFact, ...]:
    by_id: dict[str, SourceFact] = {}
    for source in sources:
        previous = by_id.get(source.source_id)
        if previous is not None and previous != source:
            raise LookupUnavailable("conflicting source duplicate")
        by_id.setdefault(source.source_id, source)
    return tuple(by_id.values())
