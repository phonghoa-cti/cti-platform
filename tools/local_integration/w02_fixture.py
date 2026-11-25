"""Fixture tra cứu W02 tổng hợp, deterministic và chỉ dùng cho local integration."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from phonghoa_core import Ioc
from portal_api.ioc_lookup import AssetFact, IocLookupPort, LookupRecord, RelatedFact, SourceFact

AS_OF = datetime(2026, 11, 11, tzinfo=UTC)


class SyntheticLookupFailure(RuntimeError):
    """Lỗi adapter có chủ ý để kiểm trạng thái 503."""


class W02FixtureLookupPort(IocLookupPort):
    def __init__(self, *, fail: bool = False, mutate_hidden: bool = False) -> None:
        self._fail = fail
        self._mutate_hidden = mutate_hidden

    def lookup(self, ioc: Ioc, allowed_tlps: frozenset[str]) -> LookupRecord | None:
        if self._fail:
            raise SyntheticLookupFailure("synthetic lookup failure")
        if ioc.value != "evil.example":
            return None
        record = _evil_record(ioc, mutate_hidden=self._mutate_hidden)
        return replace(
            record,
            sources=tuple(item for item in record.sources if item.tlp in allowed_tlps),
            related=tuple(item for item in record.related if item.tlp in allowed_tlps),
            assets=tuple(item for item in record.assets if item.tlp in allowed_tlps),
        )


def build_w02_fixture(*, fail: bool = False, mutate_hidden: bool = False) -> W02FixtureLookupPort:
    return W02FixtureLookupPort(fail=fail, mutate_hidden=mutate_hidden)


def _evil_record(ioc: Ioc, *, mutate_hidden: bool) -> LookupRecord:
    amber_reliability = 0.01 if mutate_hidden else 0.6
    amber_last_seen = AS_OF - timedelta(days=90 if mutate_hidden else 1)
    return LookupRecord(
        ioc=ioc,
        record_tlp="TLP:GREEN",
        sources=(
            SourceFact("alpha", "Synthetic Alpha", 0.8, AS_OF, AS_OF, "TLP:GREEN"),
            SourceFact(
                "amber", "Synthetic Amber", amber_reliability, amber_last_seen, amber_last_seen, "TLP:AMBER"
            ),
        ),
        related=(
            RelatedFact("technique", "T1566.001", "TLP:GREEN"),
            RelatedFact(
                "actor",
                "Synthetic Hidden Actor Mutated" if mutate_hidden else "Synthetic Hidden Actor",
                "TLP:AMBER",
            ),
        ),
        assets=(
            AssetFact(
                "hidden-critical-asset-mutated" if mutate_hidden else "hidden-critical-asset", "TLP:AMBER"
            ),
        ),
        as_of=AS_OF,
    )
