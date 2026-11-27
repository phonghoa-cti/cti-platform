import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from connectors.mst.src.parse import parse_feed
from connectors.mst.src.to_stix import build_bundle
from phonghoa_core import extract_cves

FIXTURES = Path(__file__).parent / "fixtures"


def test_core_cve_extraction():
    assert extract_cves("cve-2024-1234 CVE-2024-1234 CVE-2099-99999 CVE-2024-123") == [
        "CVE-2024-1234",
        "CVE-2099-99999",
    ]


def test_parse_synthetic():
    result = parse_feed((FIXTURES / "synthetic.rss").read_bytes())
    assert result.total == 5
    assert result.skipped == 3
    assert len(result.articles) == 2
    a = result.articles[0]
    assert a.published == "2026-11-26T02:00:00.000Z"
    assert a.cves == ("CVE-2099-12345",)
    assert {i.value for i in a.iocs} == {"demo.example", "https://sample.example/path"}


def test_parse_public_excerpt():
    result = parse_feed((FIXTURES / "mst_excerpt.rss").read_bytes())
    assert result.total == 1
    assert result.articles[0].cves == ("CVE-2024-30080", "CVE-2024-30103")


@pytest.mark.parametrize("raw", [b"<broken", b"<html/>", b"<!DOCTYPE rss><rss/>"])
def test_invalid_feed(raw):
    with pytest.raises(ValueError):
        parse_feed(raw)


def test_bundle_stable_and_valid(tmp_path):
    result = parse_feed((FIXTURES / "synthetic.rss").read_bytes())
    bundle = build_bundle(result.articles, synthetic=True)
    assert bundle == build_bundle(result.articles, synthetic=True)
    objs = bundle["objects"]
    ids = {o["id"] for o in objs}
    assert len(ids) == len(objs)
    reports = [o for o in objs if o["type"] == "report"]
    assert len(reports) == 2
    assert all("TLP:CLEAR" in o["labels"] and "synthetic" in o["labels"] for o in reports)
    assert all(o["external_references"][0]["url"].startswith("https://mst.gov.vn/") for o in reports)
    assert all(set(o["object_refs"]) <= ids for o in reports)
    assert len([o for o in objs if o["type"] == "domain-name"]) == 1
    assert len([o for o in objs if o["type"] == "vulnerability"]) == 1
    assert len([o for o in objs if o["type"] == "url"]) == 1
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    name = "stix2_validator.exe" if sys.platform == "win32" else "stix2_validator"
    result = subprocess.run(
        [str(Path(sys.executable).with_name(name)), "--version", "2.1", "--enforce-refs", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
