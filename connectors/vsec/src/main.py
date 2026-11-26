"""CLI ngoại tuyến mặc định; chỉ xuất tệp để analyst xem xét."""

import argparse
import json
import logging
import time
from pathlib import Path

from connectors.common.articles import MAX_BYTES
from connectors.vsec.src.fetch import Fetcher, FetchError
from connectors.vsec.src.parse import parse_feed
from connectors.vsec.src.to_stix import build_bundle

LOG = logging.getLogger(__name__)


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connector tin VSEC - Phong Hỏa")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", type=Path)
    source.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-terms", action="store_true")
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
    started = time.monotonic()
    try:
        raw = Fetcher().fetch() if args.live else _read_fixture(args.fixture)
        result = parse_feed(raw)
        bundle = build_bundle(result.articles, synthetic=not args.live)
        with args.output.open("x", encoding="utf-8") as file:
            file.write(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
    except (FetchError, OSError, ValueError, RuntimeError) as exc:
        LOG.error("Connector dừng (%s); kiểm tra đầu vào/cấu hình", type(exc).__name__)
        return 2
    LOG.info(
        "HTML: %s bài, %s hợp lệ, %s bị loại; %.2fs",
        result.total,
        len(result.articles),
        result.skipped,
        time.monotonic() - started,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(run())
