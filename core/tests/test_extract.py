from phonghoa_core.extract import count_by_type, extract_iocs
from phonghoa_core.ioc import IocType

REPORT_VI = """
Chiến dịch lừa đảo giả mạo ngân hàng phát tán file Hoa_don_thang10.docx
qua email ketoan[@]hoadon-dientu[.]top. Khi mở, tài liệu tải mã độc từ
hxxps://cdn-update[.]xyz/payload/loader.exe và kết nối máy chủ C2 tại 45.137.21[.]9
(cổng 443). Mã độc ghi file svchost32.dll vào máy. SHA256 của loader:
E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855.
Máy nạn nhân có IP nội bộ 192.168.10.25. Tên miền dự phòng: backup-c2.duckdns.org.
"""


def test_extract_from_vietnamese_report():
    iocs = extract_iocs(REPORT_VI)
    values = {ioc.value for ioc in iocs}

    assert "ketoan@hoadon-dientu.top" in values
    assert "https://cdn-update.xyz/payload/loader.exe" in values
    assert "45.137.21.9" in values
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in values
    assert "backup-c2.duckdns.org" in values


def test_extract_skips_filenames_private_ip_and_inner_domains():
    values = {ioc.value for ioc in extract_iocs(REPORT_VI)}

    assert "hoa_don_thang10.docx" not in values  # tên file, không phải tên miền
    assert "svchost32.dll" not in values
    assert "192.168.10.25" not in values  # IP nội bộ
    assert "cdn-update.xyz" not in values  # đã nằm trong URL, không đếm hai lần
    assert "hoadon-dientu.top" not in values  # đã nằm trong email


def test_extract_deduplicates_and_keeps_order():
    iocs = extract_iocs("evil.com rồi EVIL.COM rồi evil[.]com, sau đó 8.8.4.4")
    assert [i.value for i in iocs] == ["8.8.4.4", "evil.com"] or [i.value for i in iocs] == [
        "evil.com",
        "8.8.4.4",
    ]
    assert len(iocs) == 2


def test_count_by_type():
    counts = count_by_type(extract_iocs(REPORT_VI))
    assert counts[IocType.URL] == 1
    assert counts[IocType.EMAIL] == 1
