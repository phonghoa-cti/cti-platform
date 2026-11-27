"""Đọc thẻ tin của chuyên mục VSEC, không chạy JS hay tải liên kết."""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit

from connectors.common.articles import MAX_BYTES, MAX_ITEMS, Article, ParseResult
from phonghoa_core import Ioc, IocType, extract_cves, extract_iocs

SOURCE_HOST = "vsec.com.vn"
TOPICS = ("cảnh báo", "lỗ hổng", "mã độc", "an toàn thông tin", "an ninh mạng", "bảo mật", "ransomware")
MONTHS = (
    "một",
    "hai",
    "ba",
    "tư",
    "năm",
    "sáu",
    "bảy",
    "tám",
    "chín",
    "mười",
    "mười một",
    "mười hai",
)
HIDDEN = {"script", "style", "template", "noscript"}


@dataclass
class Card:
    date: list[str] = field(default_factory=list)
    title: list[str] = field(default_factory=list)
    excerpt: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)


class CardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.card_depth = 0
        self.card: Card | None = None
        self.cards: list[Card] = []
        self.capture: tuple[str, str, int] | None = None
        self.hidden: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in HIDDEN:
            self.hidden.append(tag)
        if self.hidden:
            return
        attr = dict(attrs)
        classes = (attr.get("class") or "").split()
        if tag == "div":
            self.depth += 1
            if "content-item" in classes:
                if self.card is not None:
                    raise ValueError("Thẻ tin lồng nhau")
                self.card = Card()
                self.card_depth = self.depth
        if self.card is None:
            return
        if self.capture is None:
            if tag == "div" and "date__content" in classes:
                self.capture = ("date", tag, self.depth)
            elif tag == "h3" and "title" in classes:
                self.capture = ("title", tag, self.depth)
            elif tag == "div" and "excerpt-wrapper" in classes:
                self.capture = ("excerpt", tag, self.depth)
        if tag == "a" and self.capture and self.capture[0] == "title":
            self.card.urls.append(attr.get("href") or "")
        if tag in {"p", "br", "li", "div"} and self.capture:
            self.handle_data(" ")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if self.capture and tag == self.capture[1] and self.depth == self.capture[2]:
            self.capture = None
        elif self.capture and tag in {"p", "li", "div"}:
            self.handle_data(" ")
        if tag == "div":
            if self.card is not None and self.depth == self.card_depth:
                self.cards.append(self.card)
                if len(self.cards) > MAX_ITEMS:
                    raise ValueError("Vượt số thẻ tin cho phép")
                self.card = None
                self.capture = None
            self.depth = max(0, self.depth - 1)

    def handle_data(self, data: str) -> None:
        if not self.hidden and self.card is not None and self.capture:
            getattr(self.card, self.capture[0]).append(data)


def _text(parts: list[str]) -> str:
    return " ".join("".join(parts).split())


def _published(value: str) -> str:
    match = re.fullmatch(r"tháng (.+) (\d{1,2}), (\d{4})", value.casefold())
    if match is None:
        raise ValueError("Ngày VSEC không hợp lệ")
    month, day, year = match.groups()
    # Trang chỉ có ngày, không có giờ; dùng đầu ngày theo UTC+7, không suy đoán giờ thật.
    date = datetime(int(year), MONTHS.index(month) + 1, int(day), tzinfo=timezone(timedelta(hours=7)))
    return date.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _article_url(value: str) -> str:
    if any(ch.isspace() or ord(ch) < 32 for ch in value):
        raise ValueError("Link bài không hợp lệ")
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.netloc != SOURCE_HOST
        or not re.fullmatch(r"/tin-tuc-bao-chi/[a-z0-9-]+/", parts.path)
        or parts.query
        or parts.fragment
    ):
        raise ValueError("Link bài không thuộc chuyên mục VSEC")
    return value


def _source_host(host: str) -> bool:
    return host == SOURCE_HOST or host.endswith("." + SOURCE_HOST)


def _safe_observable(ioc: Ioc) -> bool:
    if ioc.type == IocType.EMAIL:
        return False
    if ioc.type == IocType.URL:
        parts = urlsplit(ioc.value)
        return (
            parts.scheme in ("http", "https")
            and bool(parts.hostname)
            and not parts.username
            and not parts.password
            and not parts.query
            and not parts.fragment
            and not _source_host(parts.hostname or "")
        )
    return not _source_host(ioc.value)


def _parse_card(card: Card) -> Article | None:
    title = _text(card.title)
    excerpt = _text(card.excerpt)
    if not title or not excerpt or not any(topic in title.casefold() for topic in TOPICS):
        return None
    if len(card.urls) != 1:
        raise ValueError("Thiếu link duy nhất trong tiêu đề")
    url = _article_url(card.urls[0])
    published = _published(_text(card.date))
    text = f"{title} {excerpt}"
    iocs = tuple(ioc for ioc in extract_iocs(text) if _safe_observable(ioc))
    cves = tuple(extract_cves(text))
    if not (iocs or cves):
        return None
    return Article(title, url, published, iocs, cves)


def parse_feed(raw: bytes) -> ParseResult:
    if len(raw) > MAX_BYTES:
        raise ValueError("HTML vượt giới hạn kích thước")
    parser = CardParser()
    parser.feed(raw.decode("utf-8-sig"))
    parser.close()
    if not parser.cards or parser.card is not None:
        raise ValueError("Không nhận diện được đầy đủ cấu trúc VSEC")
    articles: dict[str, Article] = {}
    for card in parser.cards:
        try:
            article = _parse_card(card)
        except (ValueError, TypeError, OverflowError):
            continue
        if article is not None:
            articles.setdefault(article.url, article)
    return ParseResult(tuple(articles.values()), len(parser.cards), len(parser.cards) - len(articles))
