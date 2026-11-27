"""Kiểu dữ liệu chung của connector tin tiếng Việt."""

from dataclasses import dataclass

from phonghoa_core import Ioc

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 100


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    published: str
    iocs: tuple[Ioc, ...]
    cves: tuple[str, ...]


@dataclass(frozen=True)
class ParseResult:
    articles: tuple[Article, ...]
    total: int
    skipped: int
