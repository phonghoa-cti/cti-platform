import pytest

from phonghoa_core.ioc import Ioc, IocType, classify, defang, normalize, refang


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hxxps://evil[.]com/a", "https://evil.com/a"),
        ("evil(.)com", "evil.com"),
        ("admin[@]evil[dot]com", "admin@evil.com"),
        ("192[.]0[.]2[.]1", "192.0.2.1"),
    ],
)
def test_refang(raw, expected):
    assert refang(raw) == expected


@pytest.mark.parametrize(
    ("value", "ioc_type"),
    [
        ("d41d8cd98f00b204e9800998ecf8427e", IocType.MD5),
        ("da39a3ee5e6b4b0d3255bfef95601890afd80709", IocType.SHA1),
        ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", IocType.SHA256),
        ("8.8.8.8", IocType.IPV4),
        ("2001:4860:4860::8888", IocType.IPV6),
        ("http://evil.com/x", IocType.URL),
        ("a@evil.com", IocType.EMAIL),
        ("sub.evil.com", IocType.DOMAIN),
        ("ngânhàng.vn", IocType.DOMAIN),
        ("hello world", None),
        ("1.2.3", None),
    ],
)
def test_classify(value, ioc_type):
    assert classify(value) == ioc_type


def test_normalize_domain_lowercase_and_trailing_dot():
    assert normalize("EVIL.Com.") == Ioc(IocType.DOMAIN, "evil.com")


def test_normalize_idn_domain_to_punycode():
    ioc = normalize("ngânhàng.vn")
    assert ioc.type is IocType.DOMAIN
    assert ioc.value.startswith("xn--")


def test_normalize_url_keeps_path_case():
    assert normalize("hxxp://Evil[.]COM/Payload.EXE").value == "http://evil.com/Payload.EXE"


def test_normalize_url_adds_root_path_and_strips_trailing_punctuation():
    assert normalize("http://evil.com.").value == "http://evil.com/"


def test_normalize_hash_lowercase():
    assert normalize("D41D8CD98F00B204E9800998ECF8427E").value == "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("private_ip", ["10.0.0.1", "192.168.1.5", "127.0.0.1", "172.16.0.9"])
def test_normalize_rejects_private_ip(private_ip):
    with pytest.raises(ValueError):
        normalize(private_ip)


def test_normalize_rejects_garbage():
    with pytest.raises(ValueError):
        normalize("không phải ioc")


def test_normalize_strips_surrounding_quotes():
    assert normalize('"evil.com",').value == "evil.com"


def test_defang_examples():
    assert defang("evil.com", IocType.DOMAIN) == "evil[.]com"
    assert defang("http://evil.com/a.php", IocType.URL) == "hxxp://evil[.]com/a.php"
    assert defang("a@evil.com", IocType.EMAIL) == "a[@]evil[.]com"
    assert Ioc(IocType.IPV4, "203.0.113.9").display() == "203[.]0[.]113[.]9"
