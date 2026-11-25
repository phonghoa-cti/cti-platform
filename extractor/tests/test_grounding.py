import pytest

from phonghoa_extractor.grounding import ground_iocs, ground_techniques

SOURCE = (
    "Thư gửi từ ketoan[@]hoadon-dientu[.]top, tải mã độc từ hxxps://cdn-update[.]xyz/payload/loader.exe "
    "rồi kết nối 45.137.21[.]9. Mã độc kiểm tra mạng bằng google.com."
)


def by_value(items):
    return {i.value: i for i in items}


def test_real_iocs_are_kept_and_normalized():
    items = by_value(
        ground_iocs(
            [
                {"value": "45.137.21[.]9", "evidence": SOURCE},
                {"value": "ketoan@hoadon-dientu.top", "evidence": SOURCE},
            ],
            SOURCE,
        )
    )
    assert items["45.137.21.9"].keep and items["45.137.21.9"].status == "ok"
    assert items["ketoan@hoadon-dientu.top"].keep
    assert items["45.137.21.9"].extra["span"] == (0, len(SOURCE))


def test_hallucinated_ioc_is_dropped():
    items = by_value(ground_iocs([{"value": "185.220.101.4", "evidence": SOURCE}], SOURCE))
    assert items["185.220.101.4"].status == "bia" and not items["185.220.101.4"].keep


def test_allowlisted_domain_is_unchecked():
    items = by_value(ground_iocs([{"value": "google.com", "evidence": SOURCE}], SOURCE))
    assert items["google.com"].status == "allowlist" and not items["google.com"].keep


def test_invalid_and_duplicate_values():
    items = ground_iocs(
        [
            {"value": "không phải ioc", "evidence": SOURCE},
            {"value": "45.137.21.9", "evidence": SOURCE},
            {"value": "45.137.21[.]9", "evidence": SOURCE},
        ],
        SOURCE,
    )
    assert [i.status for i in items] == ["khong_hop_le", "ok"]


def test_missing_evidence_is_rejected_even_when_value_exists_in_source():
    [item] = ground_iocs([{"type": "domain", "value": "evil.example"}], "Contact evil.example.")

    assert not item.keep
    assert item.status == "bia"
    assert item.extra.get("span") is None


def test_invented_evidence_is_rejected_even_when_value_exists_elsewhere():
    [item] = ground_iocs(
        [{"type": "domain", "value": "evil.example", "evidence": "Invented evil.example quote."}],
        "Contact evil.example.",
    )

    assert not item.keep
    assert item.status == "bia"


def test_evidence_must_contain_the_same_bounded_ioc():
    [item] = ground_iocs(
        [{"type": "domain", "value": "evil.example", "evidence": "Contact not-evil.example."}],
        "Contact not-evil.example.",
    )

    assert not item.keep
    assert item.status == "bia"


def test_substrings_are_not_accepted_for_domains_ips_or_hashes():
    cases = [
        ("evil.example", "not-evil.example"),
        ("45.137.21.9", "145.137.21.90"),
        ("a" * 32, "b" + "a" * 32 + "c"),
        ("a" * 32, "z" + "a" * 32 + "z"),
    ]

    for value, evidence in cases:
        [item] = ground_iocs([{"value": value, "evidence": evidence}], evidence)
        assert not item.keep, (value, evidence)


def test_url_path_and_email_local_part_remain_case_sensitive():
    source = "Download hxxps://evil[.]example/Path?Q=One then mail Admin[@]evil[.]example."
    raw_items = [
        {"value": "https://evil.example/path?Q=One", "evidence": source},
        {"value": "admin@evil.example", "evidence": source},
    ]

    items = ground_iocs(raw_items, source)

    assert all(not item.keep and item.status == "bia" for item in items)


def test_non_string_evidence_and_mismatched_declared_type_are_rejected():
    source = "Contact evil.example."
    items = ground_iocs(
        [
            {"value": "evil.example", "evidence": {"quote": source}},
            {"type": "ipv4", "value": "evil.example", "evidence": source},
        ],
        source,
    )

    assert all(not item.keep for item in items)
    assert {item.status for item in items} == {"khong_hop_le"}


def test_valid_duplicate_replaces_an_invalid_first_item():
    source = "Contact evil.example."
    items = ground_iocs(
        [
            {"value": "evil.example", "evidence": "invented"},
            {"value": "evil.example", "evidence": source},
        ],
        source,
    )

    assert len(items) == 1
    assert items[0].keep
    assert items[0].evidence == source


def test_grounded_allowlist_duplicate_replaces_invalid_first_item():
    source = "Checks google.com."

    items = ground_iocs(
        [
            {"value": "google.com", "evidence": "invented"},
            {"value": "google.com", "evidence": source},
        ],
        source,
    )

    assert len(items) == 1
    assert items[0].status == "allowlist"
    assert items[0].evidence == source
    assert items[0].extra["span"] == (0, len(source))


def test_exact_evidence_occurrence_sets_unicode_character_span():
    source = "😀 Mở đầu tiếng Việt.\nLiên hệ evil[.]example ngay."
    evidence = "Liên hệ evil[.]example ngay."

    [item] = ground_iocs([{"value": "evil.example", "evidence": evidence}], source)

    assert item.keep
    assert item.extra["span"] == (source.index(evidence), source.index(evidence) + len(evidence))
    start, end = item.extra["span"]
    assert source[start:end] == evidence


def test_repeated_evidence_uses_first_occurrence_that_contains_ioc():
    evidence = "Contact evil.example."
    source = f"{evidence}\nOther text.\n{evidence}"

    [item] = ground_iocs([{"value": "evil.example", "evidence": evidence}], source)

    assert item.keep
    assert item.extra["span"] == (0, len(evidence))


@pytest.mark.parametrize(
    ("value", "source"),
    [
        ("evil.example", "Contact not-evil.example."),
        ("45.137.21.9", "Contact 145.137.21.90."),
        ("a" * 32, "b" + "a" * 32 + "c"),
    ],
)
def test_cut_quote_is_rejected_when_source_token_boundary_is_invalid(value, source):
    [item] = ground_iocs([{"value": value, "evidence": value}], source)

    assert not item.keep
    assert item.status == "bia"
    assert item.extra["span"] is None


def test_cut_quote_skips_invalid_occurrence_and_selects_later_bounded_one():
    source = "not-evil.example then evil.example"

    [item] = ground_iocs([{"value": "evil.example", "evidence": "evil.example"}], source)

    assert item.keep
    assert item.extra["span"] == (22, 34)
    start, end = item.extra["span"]
    assert source[start:end] == item.evidence


def test_ipv6_evidence_is_grounded_on_original_source():
    source = "Host 2606:4700:4700::1111"

    [item] = ground_iocs([{"value": "2606:4700:4700::1111", "evidence": source}], source)

    assert not item.keep
    assert item.status == "allowlist"
    assert item.note == "hạ tầng hợp pháp, mặc định bỏ chọn"
    assert item.extra["span"] == (0, len(source))


def test_techniques_must_exist_in_attack():
    known = {"T1566.002", "T1204.002"}
    items = by_value(ground_techniques([{"id": "t1566.002"}, {"id": "T9999"}, {"id": "phishing"}], known))
    assert items["T1566.002"].keep
    assert items["T9999"].status == "ma_sai" and items["PHISHING"].status == "ma_sai"
