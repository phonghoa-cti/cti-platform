"""Chấm điểm IOC từ 0 đến 100, kèm lời giải thích để hiện trên "thẻ giải thích".

Công thức (xem skill cti-thesis-conventions):
    score = 100 × R × (1 − e^(−0.7 × n)) × e^(−λ × d) × (1 + 0.3 × asset_match)

- R  : độ tin cậy của nguồn (0–1)
- n  : số nguồn độc lập cùng báo IOC này
- d  : số ngày kể từ lần cuối thấy IOC
- λ  : tốc độ "nguội" theo loại IOC (IP đổi chủ nhanh, hash thì không đổi)
- asset_match: IOC có liên quan tài sản của doanh nghiệp không
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from phonghoa_core.ioc import IocType

# Thang Admiralty: A = luôn đáng tin ... E = không đáng tin, F = chưa đánh giá được.
ADMIRALTY_RELIABILITY = {"A": 0.95, "B": 0.8, "C": 0.6, "D": 0.4, "E": 0.2, "F": 0.5}

DECAY_PER_DAY = {
    IocType.IPV4: 0.05,
    IocType.IPV6: 0.05,
    IocType.URL: 0.04,
    IocType.DOMAIN: 0.02,
    IocType.EMAIL: 0.02,
    IocType.MD5: 0.002,
    IocType.SHA1: 0.002,
    IocType.SHA256: 0.002,
}

CONFIRMATION_RATE = 0.7
ASSET_BONUS = 0.3
MIN_RELIABILITY = 0.1
FALSE_POSITIVE_PENALTY = 0.02


@dataclass(frozen=True)
class ScoreInput:
    ioc_type: IocType
    reliability: float
    confirmations: int
    days_since_last_seen: float
    asset_match: bool = False
    allowlisted: bool = False


@dataclass(frozen=True)
class ScoreResult:
    score: int
    parts: dict[str, float]
    reason: str


def reliability_from_admiralty(letter: str) -> float:
    try:
        return ADMIRALTY_RELIABILITY[letter.strip().upper()]
    except KeyError as exc:
        raise ValueError(f"Mức Admiralty phải là A–F, nhận được {letter!r}") from exc


def score(inp: ScoreInput) -> ScoreResult:
    _validate(inp)
    if inp.allowlisted:
        return ScoreResult(0, {}, "IOC nằm trong allowlist (hạ tầng hợp pháp) nên điểm = 0.")
    if inp.confirmations == 0:
        return ScoreResult(0, {}, "Chưa có nguồn nào xác nhận nên điểm = 0.")

    confirm = 1 - math.exp(-CONFIRMATION_RATE * inp.confirmations)
    fresh = math.exp(-DECAY_PER_DAY[inp.ioc_type] * inp.days_since_last_seen)
    asset = 1 + ASSET_BONUS if inp.asset_match else 1.0
    value = min(100.0, 100 * inp.reliability * confirm * fresh * asset)

    parts = {
        "reliability": round(inp.reliability, 2),
        "confirmation": round(confirm, 2),
        "freshness": round(fresh, 2),
        "asset": asset,
    }
    reason = (
        f"Nguồn tin cậy {parts['reliability']:.2f}"
        f" × {inp.confirmations} nguồn xác nhận ({parts['confirmation']:.2f})"
        f" × thấy lần cuối {inp.days_since_last_seen:g} ngày trước ({parts['freshness']:.2f})"
        + (" × liên quan tài sản (1.30)" if inp.asset_match else "")
        + f" = {round(value)} điểm"
    )
    return ScoreResult(round(value), parts, reason)


def penalize_false_positive(reliability: float) -> float:
    """Mỗi lần analyst đánh dấu báo nhầm, nguồn đó bị giảm độ tin cậy một chút."""
    return max(MIN_RELIABILITY, round(reliability - FALSE_POSITIVE_PENALTY, 4))


def _validate(inp: ScoreInput) -> None:
    if not 0 <= inp.reliability <= 1:
        raise ValueError("reliability phải nằm trong [0, 1]")
    if inp.confirmations < 0:
        raise ValueError("confirmations không được âm")
    if inp.days_since_last_seen < 0:
        raise ValueError("days_since_last_seen không được âm")
