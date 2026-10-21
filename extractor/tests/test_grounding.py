from phonghoa_extractor.grounding import ground_iocs, ground_techniques

SOURCE = (
    "Thư gửi từ ketoan[@]hoadon-dientu[.]top, tải mã độc từ hxxps://cdn-update[.]xyz/payload/loader.exe "
    "rồi kết nối 45.137.21[.]9. Mã độc kiểm tra mạng bằng google.com."
)


def by_value(items):
    return {i.value: i for i in items}


def test_real_iocs_are_kept_and_normalized():
    items = by_value(ground_iocs([{"value": "45.137.21[.]9"}, {"value": "ketoan@hoadon-dientu.top"}], SOURCE))
    assert items["45.137.21.9"].keep and items["45.137.21.9"].status == "ok"
    assert items["ketoan@hoadon-dientu.top"].keep


def test_hallucinated_ioc_is_dropped():
    items = by_value(ground_iocs([{"value": "185.220.101.4"}], SOURCE))
    assert items["185.220.101.4"].status == "bia" and not items["185.220.101.4"].keep


def test_allowlisted_domain_is_unchecked():
    items = by_value(ground_iocs([{"value": "google.com"}], SOURCE))
    assert items["google.com"].status == "allowlist" and not items["google.com"].keep


def test_invalid_and_duplicate_values():
    items = ground_iocs(
        [{"value": "không phải ioc"}, {"value": "45.137.21.9"}, {"value": "45.137.21[.]9"}], SOURCE
    )
    assert [i.status for i in items] == ["khong_hop_le", "ok"]


def test_techniques_must_exist_in_attack():
    known = {"T1566.002", "T1204.002"}
    items = by_value(ground_techniques([{"id": "t1566.002"}, {"id": "T9999"}, {"id": "phishing"}], known))
    assert items["T1566.002"].keep
    assert items["T9999"].status == "ma_sai" and items["PHISHING"].status == "ma_sai"
