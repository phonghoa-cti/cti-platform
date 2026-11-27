"""Client MCP stdio chỉ gọi danh sách đọc cố định, không có LLM."""

import json
import os
import sys
from pathlib import Path
from typing import Protocol

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

READ_TOOLS = frozenset(
    {"lookup_ioc", "related_cves", "kev_affecting", "pending_drafts", "overview", "weekly_brief"}
)


class Reader(Protocol):
    async def call(self, name: str, params: dict) -> str: ...


class McpReader:
    async def call(self, name: str, params: dict) -> str:
        if name not in READ_TOOLS:
            raise ValueError("Công cụ không được phép")
        repo = Path(__file__).resolve().parents[2]
        paths = os.pathsep.join(str(repo / part) for part in ("mcp-server", "core", "extractor", "."))
        # Bot không giữ token OpenCTI/portal; B10 chạy fixture trong tiến trình riêng.
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "phonghoa_mcp.server"],
            cwd=str(repo),
            env={"PYTHONPATH": paths, "PYTHONIOENCODING": "utf-8", "PHONGHOA_MCP_SOURCE": "fixture"},
        )
        with anyio.fail_after(25):
            async with stdio_client(server) as (reader, writer), ClientSession(reader, writer) as session:
                await session.initialize()
                result = await session.call_tool(name, params)
                if (
                    result.isError
                    or len(result.content) != 1
                    or not isinstance(result.content[0], TextContent)
                ):
                    raise ValueError("MCP không trả dữ liệu hợp lệ")
                return result.content[0].text


def _restricted(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() == "tlp" and item not in ("TLP:CLEAR", "TLP:GREEN", None):
                return True
            if _restricted(item):
                return True
    elif isinstance(value, list):
        return any(_restricted(item) for item in value)
    return False


def parse_response(raw: str) -> dict:
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > 132 * 1024:
        raise ValueError("Phản hồi quá lớn")
    if not raw.startswith("<tai_lieu>") or not raw.endswith("</tai_lieu>"):
        raise ValueError("Thiếu bao dữ liệu")
    body = raw.removeprefix("<tai_lieu>").removesuffix("</tai_lieu>")
    if "<" in body or ">" in body or "&" in body:
        raise ValueError("Bao dữ liệu bị phá vỡ")
    payload = json.loads(body)
    if not isinstance(payload, dict) or payload.get("data_mode") not in ("fixture", "opencti"):
        raise ValueError("Nguồn không hợp lệ")
    if payload.get("status") not in ("ok", "invalid_input", "unavailable"):
        raise ValueError("Trạng thái không hợp lệ")
    if not isinstance(payload.get("data"), dict) or _restricted(payload["data"]):
        raise ValueError("Dữ liệu hạn chế hoặc không hợp lệ")
    return payload
