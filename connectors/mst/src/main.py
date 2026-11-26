"""Một lần thu RSS và xuất bundle; chỉ gửi OpenCTI sau khi bật rõ ràng."""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from connectors.mst.src.fetch import Fetcher, FetchError
from connectors.mst.src.parse import MAX_BYTES, parse_feed
from connectors.mst.src.to_stix import build_bundle

LOG = logging.getLogger(__name__)


def opencti_client(url: str, token: str) -> Any:
    # pycti chỉ cần khi chạy thật; test ngoại tuyến không cài hay gọi OpenCTI.
    from pycti import OpenCTIApiClient

    return OpenCTIApiClient(url, token, ssl_verify=True)


def publish_bundle(bundle: dict[str, Any]) -> None:
    url = os.environ.get("OPENCTI_URL", "").strip()
    token = os.environ.get("OPENCTI_TOKEN", "").strip()
    parts = urlsplit(url)
    if not token or parts.scheme not in ("http", "https") or not parts.hostname or parts.username:
        raise ValueError("Cần OPENCTI_URL và OPENCTI_TOKEN hợp lệ")
    try:
        client = opencti_client(url, token)
        _, failed = client.stix2.import_bundle(bundle, update=False)
        if failed:
            raise RuntimeError("OpenCTI trả về object chưa nhập")
    except Exception:
        # Không ghi exception gốc vì client có thể chứa URL hoặc token.
        raise RuntimeError("Nhập OpenCTI không hoàn tất; kiểm tra trên lab") from None


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connector RSS MST - Phong Hỏa")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", type=Path)
    source.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-terms", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def _read_fixture(path: Path) -> bytes:
    with path.open("rb") as file:
        return file.read(MAX_BYTES + 1)


def run(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    if args.live and not args.confirm_terms:
        LOG.error("Cần xác minh điều khoản nguồn trước khi chạy live")
        return 2
    if args.publish and (not args.live or not args.confirm_terms):
        LOG.error("Không gửi fixture lên OpenCTI")
        return 2
    started = time.monotonic()
    try:
        raw = Fetcher().fetch() if args.live else _read_fixture(args.fixture)
        result = parse_feed(raw)
        bundle = build_bundle(result.articles, synthetic=not args.live)
        # Không ghi đè dữ liệu hoặc bundle đã có; xem trước trước khi nhập.
        with args.output.open("x", encoding="utf-8") as file:
            file.write(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
        if args.publish and result.articles:
            publish_bundle(bundle)
    except (FetchError, OSError, ValueError, RuntimeError) as exc:
        LOG.error("Connector dừng (%s); kiểm tra đầu vào/cấu hình", type(exc).__name__)
        return 2
    LOG.info(
        "RSS: %s bài, %s hợp lệ, %s bị loại (không liên quan/thiếu trường/trùng); %.2fs",
        result.total,
        len(result.articles),
        result.skipped,
        time.monotonic() - started,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(run())
