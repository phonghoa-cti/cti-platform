"""Nhận diện, refang/defang và chuẩn hóa IOC.

Vì sao cần chuẩn hóa? Cùng một IOC có thể được viết nhiều kiểu:
"EVIL.com.", "evil[.]com", "hxxp://Evil.com" ... Nếu không đưa về một dạng chuẩn,
hệ thống sẽ coi chúng là ba IOC khác nhau và việc khử trùng lặp thất bại.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit


class IocType(StrEnum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"


@dataclass(frozen=True)
class Ioc:
    """Một IOC đã chuẩn hóa. frozen=True để dùng được trong set (khử trùng lặp)."""

    type: IocType
    value: str

    def display(self) -> str:
        """Dạng an toàn để hiển thị (không bấm nhầm được)."""
        return defang(self.value, self.type)


# Refang: đưa IOC đã bị "vô hiệu hóa" (defang) trong báo cáo về dạng thật.
_REFANG_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"hxxp", re.IGNORECASE), "http"),
    (re.compile(r"\[\.\]|\(\.\)|\{\.\}|\[dot\]|\(dot\)", re.IGNORECASE), "."),
    (re.compile(r"\[@\]|\(@\)|\[at\]|\(at\)", re.IGNORECASE), "@"),
    (re.compile(r"\[:\]"), ":"),
    (re.compile(r"\[/\]"), "/"),
]

_HASH_TYPES = {32: IocType.MD5, 40: IocType.SHA1, 64: IocType.SHA256}
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$",
    re.IGNORECASE,
)
_STRIP_CHARS = " \t\r\n\"'<>()[]{},;"


def refang(text: str) -> str:
    """Ví dụ: 'hxxps://evil[.]com' -> 'https://evil.com'."""
    for pattern, replacement in _REFANG_RULES:
        text = pattern.sub(replacement, text)
    return text


def defang(value: str, ioc_type: IocType) -> str:
    """Ngược với refang: làm IOC không bấm được khi hiển thị trên web/Telegram."""
    if ioc_type is IocType.URL:
        value = re.sub(r"^http", "hxxp", value, flags=re.IGNORECASE)
        parts = urlsplit(value)
        return urlunsplit(parts._replace(netloc=parts.netloc.replace(".", "[.]")))
    if ioc_type is IocType.EMAIL:
        local, _, domain = value.partition("@")
        return f"{local}[@]{domain.replace('.', '[.]')}"
    if ioc_type in (IocType.DOMAIN, IocType.IPV4):
        return value.replace(".", "[.]")
    return value  # hash, IPv6: để nguyên


def classify(value: str) -> IocType | None:
    """Đoán loại IOC của một chuỗi (đã refang). Trả về None nếu không phải IOC."""
    if _HEX_RE.match(value) and len(value) in _HASH_TYPES:
        return _HASH_TYPES[len(value)]
    try:
        ip = ipaddress.ip_address(value)
        return IocType.IPV4 if ip.version == 4 else IocType.IPV6
    except ValueError:
        pass
    if _URL_RE.match(value):
        return IocType.URL
    if _EMAIL_RE.match(value):
        return IocType.EMAIL
    if _DOMAIN_RE.match(value.rstrip(".")):
        return IocType.DOMAIN
    try:  # tên miền có dấu (IDN), ví dụ "ngânhàng.vn"
        if _DOMAIN_RE.match(_to_ascii_domain(value.rstrip("."))):
            return IocType.DOMAIN
    except ValueError:
        pass
    return None


def normalize(raw: str) -> Ioc:
    """Đưa một IOC thô về dạng chuẩn. Ném ValueError nếu không hợp lệ hoặc là IP nội bộ."""
    value = refang(raw).strip(_STRIP_CHARS)
    ioc_type = classify(value)
    if ioc_type is None:
        raise ValueError(f"Không nhận diện được IOC: {raw!r}")

    if ioc_type in (IocType.MD5, IocType.SHA1, IocType.SHA256):
        return Ioc(ioc_type, value.lower())
    if ioc_type in (IocType.IPV4, IocType.IPV6):
        return Ioc(ioc_type, _normalize_ip(value))
    if ioc_type is IocType.DOMAIN:
        return Ioc(ioc_type, _to_ascii_domain(value.rstrip(".")))
    if ioc_type is IocType.EMAIL:
        local, _, domain = value.partition("@")
        return Ioc(ioc_type, f"{local}@{_to_ascii_domain(domain.rstrip('.'))}")
    return Ioc(ioc_type, _normalize_url(value))


def _normalize_ip(value: str) -> str:
    ip = ipaddress.ip_address(value)
    # IP nội bộ/đặc biệt không bao giờ là IOC hữu ích ngoài Internet.
    if not ip.is_global:
        raise ValueError(f"IP không định tuyến công khai, bỏ qua: {value}")
    return str(ip)


def _to_ascii_domain(domain: str) -> str:
    """Chữ thường + chuyển tên miền có dấu sang punycode (xn--...)."""
    try:
        return domain.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(f"Tên miền không hợp lệ: {domain!r}") from exc


def _normalize_url(value: str) -> str:
    """Chữ thường phần scheme và host; giữ nguyên path/query vì chúng phân biệt hoa thường."""
    value = value.rstrip(".,;:!?")
    parts = urlsplit(value)
    host = parts.hostname or ""
    try:
        host = str(ipaddress.ip_address(host)) if host else host
    except ValueError:
        host = _to_ascii_domain(host)
    netloc = host
    if parts.port:
        netloc = f"{host}:{parts.port}"
    if parts.username:  # hiếm, nhưng giữ lại vì có thể là dấu hiệu lừa đảo
        netloc = f"{parts.username}@{netloc}"
    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, ""))
