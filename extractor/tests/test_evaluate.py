import pytest

from phonghoa_extractor.evaluate import Score, micro_average, score_iocs, score_techniques


def test_ioc_scoring_normalizes_and_ignores_victim_iocs():
    gold = [
        {"type": "domain", "value": "hoadon-dientu.top", "role": "attacker"},
        {"type": "ipv4", "value": "45.137.21.9", "role": "attacker"},
        {"type": "domain", "value": "abclogistics.vn", "role": "victim"},
    ]
    s = score_iocs(["HOADON-DIENTU[.]top", "8.8.8.8"], gold)
    assert (s.tp, s.fp, s.fn) == (1, 1, 1)
    assert s.precision == pytest.approx(0.5) and s.recall == pytest.approx(0.5) and s.f1 == pytest.approx(0.5)


def test_technique_scoring_case_insensitive():
    s = score_techniques(["t1566.002", "T1204.002"], ["T1566.002"])
    assert (s.tp, s.fp, s.fn) == (1, 1, 0)


def test_empty_cases_do_not_divide_by_zero():
    s = Score(0, 0, 0)
    assert s.precision == s.recall == s.f1 == 0.0


def test_micro_average_sums_counts():
    total = micro_average([Score(2, 1, 0), Score(1, 0, 2)])
    assert (total.tp, total.fp, total.fn) == (3, 1, 2)
    assert total.f1 == pytest.approx(2 * 0.75 * 0.6 / (0.75 + 0.6))
