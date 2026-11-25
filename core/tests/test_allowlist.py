from phonghoa_core.allowlist import Allowlist
from phonghoa_core.ioc import normalize


def test_public_dns_ip_is_allowlisted():
    assert Allowlist.default().contains(normalize("8.8.8.8"))


def test_subdomain_matches_but_lookalike_does_not():
    allow = Allowlist.default()
    assert allow.contains(normalize("mail.google.com"))
    assert not allow.contains(normalize("evilgoogle.com"))
    assert not allow.contains(normalize("google.com.evil.xyz"))


def test_url_on_trusted_host_with_path_is_not_allowlisted():
    allow = Allowlist.default()
    assert allow.contains(normalize("https://github.com/"))
    # Mã độc có thể được host trên GitHub: URL cụ thể vẫn phải được xem xét.
    assert not allow.contains(normalize("https://github.com/attacker/repo/raw/payload.exe"))


def test_hash_never_allowlisted_by_domain():
    allow = Allowlist.default()
    assert not allow.contains(normalize("d41d8cd98f00b204e9800998ecf8427e"))


def test_from_file_reads_domains_networks_and_comments(tmp_path):
    path = tmp_path / "allow.txt"
    path.write_text(
        "# tài sản công ty\nphonghoa.vn\n113.160.0.0/16  # dải IP văn phòng\n\n", encoding="utf-8"
    )
    allow = Allowlist.from_file(path)
    assert allow.contains(normalize("portal.phonghoa.vn"))
    assert allow.contains(normalize("113.160.5.7"))
    assert not allow.contains(normalize("14.160.0.1"))
