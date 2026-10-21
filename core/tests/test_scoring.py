import pytest

from phonghoa_core.ioc import IocType
from phonghoa_core.scoring import (
    ScoreInput,
    penalize_false_positive,
    reliability_from_admiralty,
    score,
)


def make(**overrides):
    base = dict(ioc_type=IocType.DOMAIN, reliability=0.8, confirmations=2, days_since_last_seen=0)
    base.update(overrides)
    return ScoreInput(**base)


def test_more_confirmations_give_higher_score():
    assert score(make(confirmations=3)).score > score(make(confirmations=1)).score


def test_old_ip_decays_faster_than_old_hash():
    ip = score(make(ioc_type=IocType.IPV4, days_since_last_seen=30)).score
    sha = score(make(ioc_type=IocType.SHA256, days_since_last_seen=30)).score
    assert ip < sha


def test_asset_match_increases_score_and_is_explained():
    plain = score(make())
    related = score(make(asset_match=True))
    assert related.score > plain.score
    assert "tài sản" in related.reason


def test_score_is_capped_at_100():
    result = score(make(reliability=1.0, confirmations=50, asset_match=True))
    assert result.score == 100


def test_allowlisted_or_unconfirmed_ioc_scores_zero():
    assert score(make(allowlisted=True)).score == 0
    assert score(make(confirmations=0)).score == 0


def test_reason_mentions_final_score():
    result = score(make())
    assert result.reason.endswith(f"= {result.score} điểm")


@pytest.mark.parametrize(
    "bad", [dict(reliability=1.5), dict(confirmations=-1), dict(days_since_last_seen=-2)]
)
def test_invalid_input_raises(bad):
    with pytest.raises(ValueError):
        score(make(**bad))


def test_admiralty_mapping():
    assert reliability_from_admiralty("a") == 0.95
    with pytest.raises(ValueError):
        reliability_from_admiralty("Z")


def test_false_positive_penalty_has_floor():
    assert penalize_false_positive(0.5) == 0.48
    assert penalize_false_positive(0.1) == 0.1
