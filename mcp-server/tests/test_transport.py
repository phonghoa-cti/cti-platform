"""Kiểm hợp đồng stdio thật và khởi tạo SDK live bằng mock, không gọi mạng."""

import json
import sys
from pathlib import Path
from types import ModuleType

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from phonghoa_mcp.sources import source_from_env


def test_live_factory(monkeypatch):
    calls = []
    module = ModuleType("pycti")

    def client(url, token, *, ssl_verify, requests_timeout, log_level):
        calls.append((url, token, ssl_verify, requests_timeout, log_level))
        return object()

    module.OpenCTIApiClient = client
    monkeypatch.setitem(sys.modules, "pycti", module)
    monkeypatch.setenv("PHONGHOA_MCP_SOURCE", "opencti")
    monkeypatch.setenv("OPENCTI_URL", "https://opencti.example/")
    monkeypatch.setenv("OPENCTI_TOKEN", "synthetic")
    monkeypatch.delenv("PHONGHOA_PORTAL_URL", raising=False)
    monkeypatch.delenv("PHONGHOA_PORTAL_TOKEN", raising=False)
    assert source_from_env().mode == "opencti"
    assert calls == [("https://opencti.example", "synthetic", True, 5, "error")]


def test_stdio_roundtrip():
    repo = Path(__file__).resolve().parents[2]
    import os

    paths = os.pathsep.join(str(repo / part) for part in ("mcp-server", "core", "extractor", "."))
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "phonghoa_mcp.server"],
        env={"PYTHONPATH": paths, "PYTHONIOENCODING": "utf-8", "PHONGHOA_MCP_SOURCE": "fixture"},
        cwd=str(repo),
    )

    async def read():
        with anyio.fail_after(25):
            async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert len(listed.tools) == 8
                result = await session.call_tool("lookup_ioc", {"value": "sample.example"})
                assert not result.isError
                payload = result.content[0].text
                assert payload.startswith("<tai_lieu>") and payload.endswith("</tai_lieu>")
                data = json.loads(payload.removeprefix("<tai_lieu>").removesuffix("</tai_lieu>"))
                assert data["data_mode"] == "fixture"
                blocked = await session.call_tool("propose_block", {"value": "sample.example"})
                assert blocked.isError

    anyio.run(read)
