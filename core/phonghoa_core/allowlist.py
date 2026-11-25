"""Allowlist: những IOC KHÔNG được chặn dù có nguồn báo xấu.

Ví dụ: một báo cáo nhắc "mã độc kiểm tra mạng bằng cách ping 8.8.8.8". Nếu đưa 8.8.8.8
(DNS của Google) vào blocklist, cả công ty mất mạng. Allowlist ngăn chuyện đó.

Lưu ý quan trọng với URL: kẻ tấn công hay giấu mã độc trên dịch vụ hợp pháp
(github.com, drive.google.com...). Vì vậy URL chỉ được coi là "an toàn" khi
trỏ đúng trang chủ của tên miền trong allowlist; một URL có đường dẫn cụ thể
trên github.com vẫn có thể là IOC thật.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

from phonghoa_core.ioc import Ioc, IocType

DEFAULT_DOMAINS = {
    "google.com",
    "googleapis.com",
    "gstatic.com",
    "youtube.com",
    "microsoft.com",
    "windows.net",
    "windowsupdate.com",
    "office.com",
    "live.com",
    "apple.com",
    "icloud.com",
    "amazonaws.com",
    "cloudflare.com",
    "akamai.net",
    "github.com",
    "githubusercontent.com",
    "facebook.com",
    "zalo.me",
}
DEFAULT_NETWORKS = {
    "8.8.8.8/32",
    "8.8.4.4/32",
    "1.1.1.1/32",
    "1.0.0.1/32",
    "9.9.9.9/32",
    "2001:4860:4860::8888/128",
    "2606:4700:4700::1111/128",
}


class Allowlist:
    def __init__(self, domains: Iterable[str] = (), networks: Iterable[str] = ()) -> None:
        self.domains = {d.strip().lower().rstrip(".") for d in domains if d.strip()}
        self.networks = [ipaddress.ip_network(n.strip()) for n in networks if n.strip()]

    @classmethod
    def default(cls) -> Allowlist:
        return cls(DEFAULT_DOMAINS, DEFAULT_NETWORKS)

    @classmethod
    def from_file(cls, path: str | Path) -> Allowlist:
        """Mỗi dòng một tên miền hoặc dải IP (CIDR). Dòng bắt đầu bằng # là chú thích."""
        domains, networks = [], []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                ipaddress.ip_network(line)
                networks.append(line)
            except ValueError:
                domains.append(line)
        return cls(domains, networks)

    def add_domain(self, domain: str) -> None:
        self.domains.add(domain.strip().lower().rstrip("."))

    def contains(self, ioc: Ioc) -> bool:
        if ioc.type in (IocType.IPV4, IocType.IPV6):
            ip = ipaddress.ip_address(ioc.value)
            return any(ip in net for net in self.networks)
        if ioc.type is IocType.DOMAIN:
            return self._domain_listed(ioc.value)
        if ioc.type is IocType.EMAIL:
            return self._domain_listed(ioc.value.rsplit("@", 1)[-1])
        if ioc.type is IocType.URL:
            parts = urlsplit(ioc.value)
            is_homepage = parts.path in ("", "/") and not parts.query
            return is_homepage and self._domain_listed(parts.hostname or "")
        return False  # hash không bao giờ nằm trong allowlist theo tên miền

    def _domain_listed(self, domain: str) -> bool:
        """'mail.google.com' khớp với 'google.com', nhưng 'evilgoogle.com' thì không."""
        return any(domain == d or domain.endswith("." + d) for d in self.domains)
