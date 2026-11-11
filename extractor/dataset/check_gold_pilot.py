from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from phonghoa_extractor.gold_pilot import GoldPilotError, validate_gold_pilot, write_readiness


def line(stream, value: dict[str, str]) -> None:
    stream.buffer.write(json.dumps(value, separators=(",", ":")).encode() + b"\n")


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(exit_on_error=False)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--attack-snapshot", required=True)
    parser.add_argument("--attack-pin", required=True)
    parser.add_argument("--report", required=True)
    try:
        return parser.parse_args(argv)
    except (argparse.ArgumentError, SystemExit) as error:
        if "--help" in argv:
            raise SystemExit(0) from error
        raise GoldPilotError("invalid_arguments") from error


def main(argv: list[str] | None = None) -> int:
    try:
        args = arguments(list(sys.argv[1:] if argv is None else argv))
        report = validate_gold_pilot(Path(args.dataset), Path(args.attack_snapshot), Path(args.attack_pin))
        result = write_readiness(report, Path(args.report))
        if result.cleanup_warning:
            line(sys.stderr, {"warning": "cleanup_incomplete"})
        line(sys.stdout, {"status": report.status})
        return 0 if report.status == "READY_FOR_ADJUDICATION" else 2
    except GoldPilotError as error:
        line(sys.stderr, {"error": error.code})
        return 1 if error.code == "io_failure" else 2


if __name__ == "__main__":
    raise SystemExit(main())
