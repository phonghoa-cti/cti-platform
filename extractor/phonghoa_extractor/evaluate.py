"""Task 7 của X01: chấm Precision / Recall / F1 so với nhãn thủ công (chương 4).

- Precision: trong những gì máy trích ra, bao nhiêu phần đúng.
- Recall: trong những gì đúng (nhãn), máy tìm được bao nhiêu phần.
- F1: trung bình điều hòa của hai số trên.
"""

from __future__ import annotations

from dataclasses import dataclass

from phonghoa_core.ioc import normalize


@dataclass(frozen=True)
class Score:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def _norm_ioc(value: str) -> str:
    try:
        return normalize(value).value
    except ValueError:
        return value.strip().lower()


def score_sets(predicted: set[str], gold: set[str]) -> Score:
    return Score(tp=len(predicted & gold), fp=len(predicted - gold), fn=len(gold - predicted))


def score_iocs(predicted: list[str], gold: list[dict], attacker_only: bool = True) -> Score:
    """gold: danh sách nhãn theo GUIDELINE ({"type", "value", "role"}).

    Mặc định chỉ chấm IOC của kẻ tấn công.
    """
    gold_vals = {
        _norm_ioc(g["value"]) for g in gold if not attacker_only or g.get("role", "attacker") == "attacker"
    }
    return score_sets({_norm_ioc(p) for p in predicted}, gold_vals)


def score_techniques(predicted: list[str], gold: list[str]) -> Score:
    return score_sets({p.upper() for p in predicted}, {g.upper() for g in gold})


def micro_average(scores: list[Score]) -> Score:
    """Cộng dồn TP/FP/FN trên mọi báo cáo rồi mới tính — cách báo cáo chuẩn cho bảng tổng."""
    return Score(sum(s.tp for s in scores), sum(s.fp for s in scores), sum(s.fn for s in scores))
