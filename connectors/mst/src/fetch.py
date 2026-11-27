"""Cấu hình tải RSS MST; phần HTTP dùng chung cho connector Việt Nam."""

from connectors.common.fetch import Fetcher as BaseFetcher
from connectors.common.fetch import FetchError as FetchError

FEED_URL = "https://mst.gov.vn/rss/tin-tuc-su-kien/khoa-hoc-va-cong-nghe.rss"
ROBOTS_URL = "https://mst.gov.vn/robots.txt"


class Fetcher(BaseFetcher):
    feed_url = FEED_URL
    robots_url = ROBOTS_URL
