"""Trích IOC từ văn bản bằng regex.

Đây là BASELINE: cách làm đơn giản nhất, dùng để so sánh với AI extractor ở chương 4.
Điểm yếu đã biết (sẽ thấy trong thí nghiệm):
- Nhầm tên file thành tên miền (đã chặn một số đuôi file phổ biến bên dưới).
- Không hiểu ngữ cảnh: IOC của nạn nhân hay của kẻ tấn công đều bị lấy hết.
- Không trích được TTP (kỹ thuật tấn công) — việc đó cần LLM.
"""

from __future__ import annotations

import re

from phonghoa_core.ioc import Ioc, IocType, normalize, refang

# Thứ tự quan trọng: lấy URL và email trước, rồi "xóa" chúng khỏi văn bản,
# để tên miền nằm bên trong URL không bị đếm thêm một lần nữa.
_URL = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s<>\"'\)\]]+", re.IGNORECASE)
_EMAIL = re.compile(r"\b[a-z0-9._%+-]+@(?:[a-z0-9-]+\.)+[a-z]{2,63}\b", re.IGNORECASE)
_HASH = re.compile(r"\b(?:[0-9a-f]{64}|[0-9a-f]{40}|[0-9a-f]{32})\b", re.IGNORECASE)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_DOMAIN = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})\b",
    re.IGNORECASE,
)

# Đuôi file hay bị nhầm thành tên miền (ví dụ "invoice.pdf", "loader.exe").
_FILE_EXTENSIONS = {
    "exe",
    "dll",
    "sys",
    "bat",
    "cmd",
    "ps1",
    "vbs",
    "js",
    "jar",
    "lnk",
    "iso",
    "img",
    "pdf",
    "doc",
    "docx",
    "docm",
    "xls",
    "xlsx",
    "xlsm",
    "ppt",
    "pptx",
    "rtf",
    "txt",
    "zip",
    "rar",
    "7z",
    "gz",
    "tar",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "html",
    "htm",
    "php",
    "py",
    "sh",
    "json",
    "xml",
    "log",
    "tmp",
    "dat",
    "bin",
    "msi",
    "hta",
    "one",
}


def extract_iocs(text: str) -> list[Ioc]:
    """Trả về danh sách IOC đã chuẩn hóa, không trùng, giữ thứ tự xuất hiện."""
    remaining = refang(text)
    found: list[Ioc] = []

    for pattern in (_URL, _EMAIL, _HASH, _IPV4, _DOMAIN):
        for match in pattern.finditer(remaining):
            candidate = match.group(0)
            if pattern is _DOMAIN and _looks_like_filename(candidate):
                continue
            try:
                found.append(normalize(candidate))
            except ValueError:
                continue  # IP nội bộ, chuỗi không hợp lệ...
        remaining = pattern.sub(lambda m: " " * len(m.group(0)), remaining)

    return list(dict.fromkeys(found))  # khử trùng lặp nhưng giữ thứ tự


def _looks_like_filename(candidate: str) -> bool:
    return candidate.rsplit(".", 1)[-1].lower() in _FILE_EXTENSIONS


def count_by_type(iocs: list[Ioc]) -> dict[IocType, int]:
    """Tiện cho thống kê và dashboard."""
    counts: dict[IocType, int] = {}
    for ioc in iocs:
        counts[ioc.type] = counts.get(ioc.type, 0) + 1
    return counts
