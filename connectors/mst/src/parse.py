"""Đọc RSS 2.0 công khai của MST; văn bản nguồn luôn là dữ liệu không tin cậy."""

from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit
from xml.etree import ElementTree

from phonghoa_core import Ioc, IocType, extract_cves, extract_iocs

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 100
SOURCE_HOST = "mst.gov.vn"
TOPICS = ("cảnh báo", "lỗ hổng", "mã độc", "an toàn thông tin", "an ninh mạng")


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


class VisibleText(HTMLParser):
    """Không lấy link ẩn, script, style hay template làm IOC."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "template"):
            self.hidden.append(tag)
        elif not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()
        elif not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def visible_text(text: str) -> str:
    parser = VisibleText()
    parser.feed(text)
    parser.close()
    return " ".join("".join(parser.parts).split())


def article_url(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.netloc != SOURCE_HOST
        or not parts.path.endswith(".htm")
        or parts.query
        or parts.fragment
        or any(ch.isspace() or ord(ch) < 32 for ch in value)
    ):
        raise ValueError("Link bài không thuộc nguồn MST")
    return value


def _safe_observable(ioc: Ioc) -> bool:
    # Không thu email hoặc URL có thông tin xác thực/query; tránh dữ liệu cá nhân/secret.
    if ioc.type == IocType.EMAIL:
        return False
    if ioc.type == IocType.URL:
        parts = urlsplit(ioc.value)
        return (
            parts.scheme in ("http", "https")
            and bool(parts.hostname)
            and not parts.username
            and not parts.query
            and parts.hostname != SOURCE_HOST
        )
    return ioc.value != SOURCE_HOST


def _parse_item(item: ElementTree.Element) -> Article | None:
    title = visible_text(item.findtext("title", ""))
    if not title or not any(topic in title.casefold() for topic in TOPICS):
        return None
    url = article_url(item.findtext("link", "").strip())
    date = parsedate_to_datetime(item.findtext("pubDate", ""))
    if date.tzinfo is None:
        raise ValueError("Ngày RSS thiếu múi giờ")
    published = date.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    description = visible_text(item.findtext("description", ""))
    if not description:
        raise ValueError("Thiếu mô tả")
    text = f"{title} {description}"
    iocs = tuple(ioc for ioc in extract_iocs(text) if _safe_observable(ioc))
    cves = tuple(extract_cves(text))
    if not (iocs or cves):
        return None
    return Article(title, url, published, iocs, cves)


def parse_feed(raw: bytes) -> ParseResult:
    if len(raw) > MAX_BYTES:
        raise ValueError("RSS vượt giới hạn kích thước")
    text = raw.decode("utf-8-sig")
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("RSS không cho phép DTD/entity")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise ValueError("RSS XML không hợp lệ") from exc
    if root.tag != "rss" or root.find("channel") is None:
        raise ValueError("Không phải RSS 2.0")
    items = root.findall("./channel/item")
    if len(items) > MAX_ITEMS:
        raise ValueError("RSS vượt số bài cho phép")
    articles: dict[str, Article] = {}
    for item in items:
        try:
            article = _parse_item(item)
        except (ValueError, TypeError, OverflowError):
            continue
        if article is not None:
            articles.setdefault(article.url, article)
    return ParseResult(tuple(articles.values()), len(items), len(items) - len(articles))
