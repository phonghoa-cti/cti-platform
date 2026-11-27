"""Chỉ tải một trang danh mục VSEC, không theo link bài viết."""

from connectors.common.fetch import Fetcher as BaseFetcher
from connectors.common.fetch import FetchError as FetchError

FEED_URL = "https://vsec.com.vn/tin-tong-hop-vi/"
ROBOTS_URL = "https://vsec.com.vn/robots.txt"


class Fetcher(BaseFetcher):
    feed_url = FEED_URL
    robots_url = ROBOTS_URL
    # Đã quan sát HTTP 200 với body rỗng; không có quy tắc robots.
    # Các lỗi HTTP và body không hợp lệ vẫn bị từ chối.
    allow_empty_robots = True
