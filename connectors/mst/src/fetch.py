"""Tải RSS có giới hạn, không theo redirect, kiểm robots.txt trước khi tải."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from connectors.mst.src.parse import MAX_BYTES

FEED_URL = "https://mst.gov.vn/rss/tin-tuc-su-kien/khoa-hoc-va-cong-nghe.rss"
ROBOTS_URL = "https://mst.gov.vn/robots.txt"
USER_AGENT = "PhongHoaCTI/0.1 (academic threat intelligence connector)"
MIN_INTERVAL = 5
CACHE_TTL = 3600
MAX_ATTEMPTS = 5
TIMEOUT = 15
LOG = logging.getLogger(__name__)


class FetchError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Không theo URL do máy chủ trả về (không mở rộng phạm vi nguồn).
        return None


def _retry_delay(exc: HTTPError, attempt: int) -> float:
    delay = float(2**attempt)
    retry_after = exc.headers.get("Retry-After") if exc.headers else None
    if retry_after:
        try:
            seconds = int(retry_after)
        except ValueError:
            try:
                seconds = (parsedate_to_datetime(retry_after) - datetime.now(UTC)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                seconds = 0
        delay = max(delay, seconds)
    # Không tiếp tục gửi nếu máy chủ yêu cầu chờ lâu hơn giới hạn lần chạy.
    if delay > 300:
        raise FetchError("Máy chủ yêu cầu chờ; dừng lần chạy")
    return delay


class Fetcher:
    def __init__(
        self,
        open_url: Callable | None = None,
        sleep: Callable = time.sleep,
        clock: Callable = time.monotonic,
    ) -> None:
        self.open_url = open_url or build_opener(NoRedirect()).open
        self.sleep = sleep
        self.clock = clock
        self.interval = MIN_INTERVAL
        self.last_request: float | None = None
        self.cache: tuple[float, bytes] | None = None

    def _pace(self) -> None:
        if self.last_request is not None:
            self.sleep(max(0, self.interval - (self.clock() - self.last_request)))
        self.last_request = self.clock()

    def _get(self, url: str) -> bytes:
        for attempt in range(MAX_ATTEMPTS):
            self._pace()
            try:
                request = Request(url, headers={"User-Agent": USER_AGENT})
                with self.open_url(request, timeout=TIMEOUT) as response:
                    data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise FetchError("Response vượt giới hạn")
                return data
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == MAX_ATTEMPTS - 1:
                    raise FetchError(f"HTTP {exc.code}; dừng tải") from None
                delay = _retry_delay(exc, attempt)
            except (URLError, TimeoutError, OSError):
                if attempt == MAX_ATTEMPTS - 1:
                    raise FetchError("Không kết nối được nguồn") from None
                delay = 2**attempt
            LOG.warning("Nguồn tạm lỗi; retry sau %s giây", delay)
            self.sleep(delay)
        raise FetchError("Hết lượt tải")

    def fetch(self) -> bytes:
        if self.cache and self.clock() - self.cache[0] < CACHE_TTL:
            return self.cache[1]
        raw = self._get(ROBOTS_URL)
        try:
            robots_text = raw.decode("utf-8-sig")
        except UnicodeError as exc:
            raise FetchError("robots.txt không đọc được") from exc
        if not any(line.strip().lower().startswith("user-agent:") for line in robots_text.splitlines()):
            raise FetchError("robots.txt chưa xác minh được")
        robots = RobotFileParser()
        robots.parse(robots_text.splitlines())
        if not robots.can_fetch(USER_AGENT, FEED_URL):
            raise FetchError("robots.txt không cho phép tải RSS")
        crawl_delay = robots.crawl_delay(USER_AGENT)
        request_rate = robots.request_rate(USER_AGENT)
        if crawl_delay:
            self.interval = max(self.interval, crawl_delay)
        if request_rate:
            self.interval = max(self.interval, request_rate.seconds / request_rate.requests)
        if self.interval > 300:
            raise FetchError("robots.txt yêu cầu thời gian chờ quá dài; dừng lần chạy")
        body = self._get(FEED_URL)
        self.cache = (self.clock(), body)
        return body
