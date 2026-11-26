from email.message import Message
from urllib.error import HTTPError

import pytest

from connectors.mst.src.fetch import FEED_URL, Fetcher, FetchError


class Response:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return self.body[:limit]


def test_robots_rate_retry_and_cache():
    requests = []
    waits = []

    def open_url(request, timeout):
        requests.append((request.full_url, request.get_header("User-agent"), timeout))
        if request.full_url.endswith("/robots.txt"):
            return Response(b"User-agent: *\nAllow: /\n")
        if len(requests) == 2:
            headers = Message()
            headers["Retry-After"] = "7"
            raise HTTPError(request.full_url, 429, "retry", headers, None)
        return Response(b"<rss/>")

    fetcher = Fetcher(open_url=open_url, sleep=waits.append, clock=lambda: 0)
    assert fetcher.fetch() == b"<rss/>"
    assert fetcher.fetch() == b"<rss/>"
    assert [r[0] for r in requests] == ["https://mst.gov.vn/robots.txt", FEED_URL, FEED_URL]
    assert all(r[1] and r[2] > 0 for r in requests)
    assert max(waits) >= 7


def test_robots_denial():
    requests = []

    def open_url(request, timeout):
        requests.append(request.full_url)
        return Response(b"User-agent: *\nDisallow: /rss/\n")

    with pytest.raises(FetchError):
        Fetcher(open_url=open_url, sleep=lambda _: None).fetch()
    assert requests == ["https://mst.gov.vn/robots.txt"]


def test_robots_unavailable():
    def open_url(request, timeout):
        raise HTTPError(request.full_url, 403, "denied", None, None)

    with pytest.raises(FetchError):
        Fetcher(open_url=open_url, sleep=lambda _: None).fetch()
