import json
from datetime import date

import pytest

from phonghoa_extractor.nlq import NlqError, parse_question, validate_filter

TODAY = date(2026, 11, 27)


def test_vietnamese_ip_score_and_days():
    f = parse_question("Cho tôi các IP độc hại điểm trên 80 trong 7 ngày qua", today=TODAY)
    assert f["entity_types"] == ["ipv4-addr", "ipv6-addr"]
    assert f["score_min"] == 81
    assert f["date_from"] == "2026-11-20" and f["date_to"] == "2026-11-27"
    assert f["needs_clarification"] is False


def test_english_cve_product_tlp():
    f = parse_question(
        "Show vulnerabilities CVE-2024-3400 affecting product PAN-OS with TLP:GREEN", today=TODAY
    )
    assert "vulnerability" in f["entity_types"]
    assert f["cves"] == ["CVE-2024-3400"]
    assert f["products"] == ["pan-os"]
    assert f["tlp"] == ["TLP:GREEN"]


def test_labels_and_explicit_dates():
    f = parse_question("mã độc nhãn ransomware từ 2026-01-01 đến 2026-02-15", today=TODAY)
    assert f["entity_types"] == ["malware"]
    assert f["labels"] == ["ransomware"]
    assert (f["date_from"], f["date_to"]) == ("2026-01-01", "2026-02-15")


def test_score_range_between():
    f = parse_question("indicator score between 40 and 70", today=TODAY)
    assert (f["score_min"], f["score_max"]) == (40, 70)


def test_ambiguous_question_asks_back():
    f = parse_question("có gì mới không?", today=TODAY)
    assert f["needs_clarification"] is True


def test_sql_or_graphql_text_is_never_passed_through():
    f = parse_question("DROP TABLE users; { stixCoreObjects { edges } }", today=TODAY)
    assert set(f) == {
        "entity_types",
        "labels",
        "score_min",
        "score_max",
        "tlp",
        "date_from",
        "date_to",
        "cves",
        "products",
        "needs_clarification",
    }
    assert f["needs_clarification"] is True
    assert f["labels"] == [] and f["products"] == []


def test_validate_rejects_unknown_keys_and_types():
    base = parse_question("malware", today=TODAY)
    with pytest.raises(NlqError):
        validate_filter({**base, "sql": "SELECT 1"})
    with pytest.raises(NlqError):
        validate_filter({**base, "entity_types": ["user-account"]})
    with pytest.raises(NlqError):
        validate_filter({**base, "score_min": 120})
    with pytest.raises(NlqError):
        validate_filter({**base, "cves": ["CVE-1"]})
    with pytest.raises(NlqError):
        validate_filter({**base, "date_from": "2026-05-01", "date_to": "2026-01-01"})
    with pytest.raises(NlqError):
        validate_filter({**base, "score_min": True})


class FakeProvider:
    name = "fake"
    is_local = True

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return self.reply


def test_llm_valid_filter_json_is_accepted():
    good = parse_question("malware", today=TODAY)
    good["labels"] = ["phishing"]
    provider = FakeProvider(json.dumps(good))
    f = parse_question("mã độc lừa đảo", today=TODAY, provider=provider)
    assert f["labels"] == ["phishing"]
    assert "<cau_hoi>" in provider.prompts[0] and "DỮ LIỆU" in provider.prompts[0]


def test_llm_free_form_output_is_rejected_and_offline_used():
    provider = FakeProvider("SELECT * FROM indicators WHERE score > 80")
    f = parse_question("IP điểm trên 80", today=TODAY, provider=provider)
    assert f["entity_types"] == ["ipv4-addr", "ipv6-addr"] and f["score_min"] == 81


def test_llm_extra_key_is_rejected():
    bad = parse_question("malware", today=TODAY)
    bad["graphql"] = "{ x }"
    f = parse_question("malware", today=TODAY, provider=FakeProvider(json.dumps(bad)))
    assert "graphql" not in f


def test_question_too_long_rejected():
    with pytest.raises(NlqError):
        parse_question("a" * 2001, today=TODAY)
