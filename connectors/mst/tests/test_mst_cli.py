import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from connectors.mst.src import main

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic.rss"


def test_fixture_cli_is_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCTI_URL", "https://opencti.example")
    monkeypatch.setenv("OPENCTI_TOKEN", "placeholder")
    monkeypatch.setattr(main, "publish_bundle", lambda _: pytest.fail("không được gửi fixture"))
    output = tmp_path / "bundle.json"
    assert main.run(["--fixture", str(FIXTURE), "--output", str(output)]) == 0
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert bundle["type"] == "bundle"
    assert main.run(["--fixture", str(FIXTURE), "--output", str(output), "--publish"]) == 2


def test_live_requires_terms_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "Fetcher", lambda: pytest.fail("không được gọi mạng"))
    assert main.run(["--live", "--output", str(tmp_path / "out.json")]) == 2


def test_publish_client_mock(monkeypatch):
    calls = []
    monkeypatch.setenv("OPENCTI_URL", "https://opencti.example")
    monkeypatch.setenv("OPENCTI_TOKEN", "placeholder")
    stix2 = SimpleNamespace(import_bundle=lambda bundle, **kw: (calls.append(bundle), []))
    client = SimpleNamespace(stix2=stix2)
    monkeypatch.setattr(main, "opencti_client", lambda url, token: client)
    main.publish_bundle({"type": "bundle"})
    assert calls == [{"type": "bundle"}]


def test_missing_secret(monkeypatch):
    monkeypatch.delenv("OPENCTI_TOKEN", raising=False)
    monkeypatch.delenv("OPENCTI_URL", raising=False)
    with pytest.raises(ValueError):
        main.publish_bundle({"type": "bundle"})
