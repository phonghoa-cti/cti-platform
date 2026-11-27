import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

from connectors.vsec.src import main
from connectors.vsec.src.fetch import FEED_URL, ROBOTS_URL, Fetcher, FetchError
from connectors.vsec.src.parse import parse_feed
from connectors.vsec.src.to_stix import build_bundle

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic.html"


def test_parse_cards():
    result = parse_feed(FIXTURE.read_bytes())
    assert (result.total, result.skipped) == (6, 4)
    first, second = result.articles
    assert first.published == "2026-11-25T17:00:00.000Z"
    assert second.published == "2026-10-14T17:00:00.000Z"
    assert first.cves == ("CVE-2099-12345",)
    assert {i.value for i in first.iocs} == {"demo.example", "https://sample.example/path"}


@pytest.mark.parametrize("raw", [b"<html>changed layout</html>", b"\xff", b"x" * (2 * 1024 * 1024 + 1)])
def test_reject_bad_page(raw):
    with pytest.raises(ValueError):
        parse_feed(raw)


def test_bundle(tmp_path):
    articles = parse_feed(FIXTURE.read_bytes()).articles
    bundle = build_bundle(articles, synthetic=True)
    assert bundle == build_bundle(articles, synthetic=True)
    objects = bundle["objects"]
    ids = {obj["id"] for obj in objects}
    reports = [obj for obj in objects if obj["type"] == "report"]
    assert len(ids) == len(objects)
    assert len(reports) == 2
    assert all(set(report["object_refs"]) <= ids for report in reports)
    assert all("synthetic" in report["labels"] and "unverified" in report["labels"] for report in reports)
    assert all(
        report["external_references"][0]["url"].startswith("https://vsec.com.vn/") for report in reports
    )
    assert all("TLP:GREEN" in report["labels"] for report in reports)
    assert len([obj for obj in objects if obj["type"] == "vulnerability"]) == 1
    assert not any(obj["type"] == "indicator" for obj in objects)
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    name = "stix2_validator.exe" if sys.platform == "win32" else "stix2_validator"
    checked = subprocess.run(
        [str(Path(sys.executable).with_name(name)), "--version", "2.1", "--enforce-refs", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


class Response:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return self.body[:limit]


def test_fetch_empty_robots_rate_cache():
    calls = []
    waits = []

    def open_url(request, timeout):
        calls.append(request.full_url)
        assert timeout > 0
        return Response(b"" if request.full_url == ROBOTS_URL else b"<html/>")

    fetcher = Fetcher(open_url=open_url, sleep=waits.append, clock=lambda: 0)
    assert fetcher.fetch() == fetcher.fetch() == b"<html/>"
    assert calls == [ROBOTS_URL, FEED_URL]
    assert max(waits) >= 5


@pytest.mark.parametrize("robots", [b"User-agent: *\nDisallow: /tin-tong-hop-vi/", b"<html>error</html>"])
def test_robots_deny(robots):
    calls = []

    def open_url(request, timeout):
        calls.append(request.full_url)
        return Response(robots)

    with pytest.raises(FetchError):
        Fetcher(open_url=open_url, sleep=lambda _: None).fetch()
    assert calls == [ROBOTS_URL]


def test_robots_unavailable():
    def open_url(request, timeout):
        raise HTTPError(request.full_url, 403, "denied", None, None)

    with pytest.raises(FetchError):
        Fetcher(open_url=open_url, sleep=lambda _: None).fetch()


def test_cli_offline_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "Fetcher", lambda: pytest.fail("không gọi mạng"))
    output = tmp_path / "bundle.json"
    args = ["--fixture", str(FIXTURE), "--output", str(output)]
    assert main.run(args) == 0
    assert main.run(args) == 2
    assert main.run(["--live", "--output", str(tmp_path / "live.json")]) == 2
    assert not (tmp_path / "live.json").exists()


def test_live_only_explicit_and_never_publish(tmp_path, monkeypatch):
    class FakeFetcher:
        def fetch(self):
            return FIXTURE.read_bytes()

    monkeypatch.setattr(main, "Fetcher", FakeFetcher)
    output = tmp_path / "live.json"
    assert main.run(["--live", "--confirm-terms", "--output", str(output)]) == 0
    reports = [o for o in json.loads(output.read_text(encoding="utf-8"))["objects"] if o["type"] == "report"]
    assert all("synthetic" not in o["labels"] for o in reports)
    with pytest.raises(SystemExit):
        main.run(["--live", "--confirm-terms", "--output", str(output), "--publish"])


def test_public_excerpt_reconstruction():
    result = parse_feed((FIXTURE.parent / "vsec_excerpt.html").read_bytes())
    assert result.total == 1 and result.skipped == 0
    assert result.articles[0].cves == ("CVE-2025-0411",)
    assert result.articles[0].published == "2025-01-22T17:00:00.000Z"
