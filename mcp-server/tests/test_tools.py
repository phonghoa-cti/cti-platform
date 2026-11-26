import json

import anyio
import pytest
from phonghoa_mcp.server import build_server
from phonghoa_mcp.sources import FixtureSource, OpenCtiSource, SourceUnavailable
from phonghoa_mcp.tools import ReadTools

TOOLS = {
    "lookup_ioc",
    "kev_affecting",
    "pending_drafts",
    "search_reports",
    "overview",
    "weekly_brief",
    "events_since",
    "related_cves",
}


def unwrap(result):
    assert result.startswith("<tai_lieu>")
    assert result.endswith("</tai_lieu>")
    return json.loads(result.removeprefix("<tai_lieu>").removesuffix("</tai_lieu>"))


@pytest.fixture
def tools():
    return ReadTools(FixtureSource())


def test_ioc(tools):
    result = unwrap(tools.lookup_ioc("hxxp://sample[.]example"))
    assert result["data_mode"] == "fixture"
    assert result["data"]["ioc"]["display"] == "hxxp://sample[.]example/"
    assert result["data"]["score"]["value"] > 0
    assert "http://sample.example" not in str(result)
    assert unwrap(tools.lookup_ioc("missing.example"))["data"]["state"] == "not_found"
    assert unwrap(tools.lookup_ioc("10.0.0.1"))["status"] == "invalid_input"
    assert unwrap(tools.lookup_ioc("restricted.example"))["data"]["state"] == "not_found"


def test_cves(tools):
    result = unwrap(tools.related_cves("nginx"))["data"]
    assert [item["id"] for item in result["items"]] == ["CVE-2099-10001"]
    assert "phiên bản" in result["notice"]
    assert unwrap(tools.kev_affecting())["data"]["items"][0]["id"] == "CVE-2099-10001"
    assert unwrap(tools.related_cves("unknown"))["data"]["items"] == []


def test_drafts_and_reports(tools):
    draft = unwrap(tools.pending_drafts())["data"]
    assert draft["items"][0]["id"] == 1
    assert len(draft["items"]) == 1
    output = tools.search_reports("demo")
    assert output.count("</tai_lieu>") == 1
    assert "<script>" not in output
    data = unwrap(output)["data"]
    assert len(data["items"]) == 1
    assert "</tai_lieu>" in data["items"][0]["description"]
    assert "restricted" not in str(data)


def test_overview_week_events(tools):
    assert unwrap(tools.overview())["data"]["pending_drafts"] == 1
    assert unwrap(tools.weekly_brief())["status"] == "ok"
    assert len(unwrap(tools.events_since("2026-11-25T00:00:00Z"))["data"]["items"]) == 1
    assert unwrap(tools.events_since("yesterday"))["status"] == "invalid_input"


def test_limits_and_read_only(tools):
    assert unwrap(tools.search_reports(""))["status"] == "invalid_input"
    assert unwrap(tools.search_reports("demo", 0))["status"] == "invalid_input"

    async def check():
        server = build_server(FixtureSource())
        registered = await server.list_tools()
        assert {tool.name for tool in registered} == TOOLS
        for tool in registered:
            assert tool.annotations.readOnlyHint is True
            assert tool.annotations.destructiveHint is False
        result = await server.call_tool("lookup_ioc", {"value": "missing.example"})
        assert result

    anyio.run(check)


class ListOnly:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return self.rows


def test_opencti_read_and_tlp():
    class Client:
        report = ListOnly(
            [
                {
                    "id": "one",
                    "name": "demo",
                    "description": "outside",
                    "published": "2026-11-26",
                    "objectMarking": [{"definition": "TLP:GREEN"}],
                },
                {
                    "id": "two",
                    "name": "secret",
                    "description": "never",
                    "objectMarking": [{"definition": "TLP:AMBER"}],
                },
                {"id": "three", "name": "unmarked"},
                {
                    "id": "four",
                    "name": "mixed",
                    "objectMarking": [{"definition": "TLP:CLEAR"}, {"definition": "TLP:RED"}],
                },
            ]
        )

    tools = ReadTools(OpenCtiSource(Client()))
    result = unwrap(tools.search_reports("demo"))
    assert [item["id"] for item in result["data"]["items"]] == ["one"]
    assert Client.report.calls[0]["search"] == "demo"
    assert unwrap(tools.pending_drafts())["status"] == "unavailable"


def test_source_failure_does_not_leak():
    class Broken(FixtureSource):
        def reports(self, query, limit):
            raise SourceUnavailable("secret token")

    result = ReadTools(Broken()).search_reports("demo")
    assert unwrap(result)["status"] == "unavailable"
    assert "secret token" not in result
