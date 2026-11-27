"""Nguồn SSE có thể thay bằng fixture. Chỉ GET luồng lọc HTTPS, không writer."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from connectors.playbook.rules import strict_json

MAX_EVENT_BYTES = 1024 * 1024
EVENT_ID = re.compile(r"(0|[1-9][0-9]{0,19})-(0|[1-9][0-9]{0,19})\Z")


class SourceError(RuntimeError):
    """Luồng chưa thể tiếp tục an toàn; không tự bỏ qua event."""


@dataclass(frozen=True)
class Frame:
    event_id: str
    kind: str
    data: dict


class Source(Protocol):
    def events(self, last_event_id: str | None) -> Iterator[Frame]: ...


def _frame(fields):
    kind = fields.get("event", ["message"])[0]
    if kind in ("heartbeat", "connected", "metrics"):
        return None
    if kind not in ("create", "update", "merge", "delete"):
        raise SourceError("unsupported event or stream gap")
    event_id = fields.get("id", [""])[0]
    if not EVENT_ID.fullmatch(event_id) or not fields.get("data"):
        raise SourceError("invalid event framing")
    try:
        data = strict_json("\n".join(fields["data"]))
    except ValueError:
        raise SourceError("invalid event JSON") from None
    if not isinstance(data, dict):
        raise SourceError("invalid envelope")
    return Frame(event_id, kind, data)


def parse_sse(lines: Iterable[str]) -> Iterator[Frame]:
    fields: dict[str, list[str]] = {}
    size = 0
    for line in lines:
        size += len(line.encode("utf-8")) + 1
        if size > MAX_EVENT_BYTES:
            raise SourceError("event too large")
        if not line:
            if fields:
                frame = _frame(fields)
                if frame is not None:
                    yield frame
            fields, size = {}, 0
        elif not line.startswith(":"):
            name, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if name in ("id", "event", "data"):
                if name != "data" and name in fields:
                    raise SourceError("duplicate SSE field")
                fields.setdefault(name, []).append(value)
    if fields:
        raise SourceError("incomplete SSE event")


def _lines(chunks: Iterable[bytes]) -> Iterator[str]:
    pending = bytearray()
    try:
        for chunk in chunks:
            for part in chunk.splitlines(keepends=True):
                pending.extend(part)
                if len(pending) > MAX_EVENT_BYTES:
                    raise SourceError("line too large")
                # splitlines có thể tách CR trong CRLF giữa hai chunk; chỉ LF kết thúc.
                if pending.endswith(b"\n"):
                    yield bytes(pending).removesuffix(b"\n").removesuffix(b"\r").decode("utf-8")
                    pending.clear()
        if pending:
            raise SourceError("incomplete SSE line")
    except UnicodeError:
        raise SourceError("invalid SSE encoding") from None


class FixtureSource:
    def __init__(self, path: Path):
        self.path = Path(path)

    def events(self, last_event_id: str | None = None) -> Iterator[Frame]:
        # Replay toàn fixture để kiểm receipt; engine tự chống trùng.
        with self.path.open("rb") as stream:
            yield from parse_sse(_lines(iter(lambda: stream.read(8192), b"")))


class LiveSource:
    """Adapter runtime chưa nghiệm thu trên CE; một kết nối, caller điều phối retry."""

    def __init__(self, url: str, *, token_env: str = "OPENCTI_STREAM_TOKEN", timeout: float = 30):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"/stream/[A-Za-z0-9_-]+", parsed.path)
        ):
            raise ValueError("filtered HTTPS stream required")
        if not 1 <= timeout <= 60:
            raise ValueError("invalid timeout")
        self.url, self.token_env, self.timeout = url, token_env, timeout

    def events(self, last_event_id: str | None = None) -> Iterator[Frame]:
        token = os.environ.get(self.token_env)
        if not token or "\r" in token or "\n" in token:
            raise SourceError("missing or invalid read credential")
        headers = {"Accept": "text/event-stream", "Authorization": "Bearer " + token}
        if last_event_id is not None:
            if not EVENT_ID.fullmatch(last_event_id):
                raise SourceError("invalid resume cursor")
            headers["Last-Event-ID"] = last_event_id
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", self.url, headers=headers) as response:
                    if response.status_code != 200 or not response.headers.get(
                        "content-type", ""
                    ).lower().startswith("text/event-stream"):
                        raise SourceError("stream unavailable or resume rejected")
                    yield from parse_sse(_lines(response.iter_bytes(chunk_size=8192)))
            raise SourceError("live stream closed; reconnect requires reconciliation")
        except (httpx.HTTPError, UnicodeError):
            raise SourceError("stream transport failed") from None
