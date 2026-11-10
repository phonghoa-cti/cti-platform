"""Xuất final approved draft thành một bundle STIX 2.1 ngoại tuyến."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.stix_export import (  # noqa: E402
    PublicationCleanupError,
    StixExportError,
    export_approved,
)
from phonghoa_extractor.store import DraftStoreError  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export-approved", help="xuất final approved snapshot")
    export.add_argument("--db", required=True, type=Path, help="file SQLite schema v2")
    export.add_argument("--id", required=True, type=int, help="ID draft approved")
    export.add_argument("--exporter-config", required=True, type=Path, help="config exporter JSON")
    export.add_argument("--output", required=True, type=Path, help="bundle STIX JSON sẽ tạo")
    export.add_argument("--timeout", type=float, default=5.0, help="timeout SQLite (giây)")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    try:
        result = export_approved(
            db_path=args.db,
            draft_id=args.id,
            exporter_config_path=args.exporter_config,
            output_path=args.output,
            timeout=args.timeout,
        )
    except PublicationCleanupError:
        print('{"error":"published_cleanup_incomplete"}', file=sys.stderr)
        return 1
    except (StixExportError, DraftStoreError, OSError, UnicodeError):
        print('{"error":"export_failed"}', file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "draft_id": result.draft_id,
                "bundle_sha256": result.bundle_sha256,
                "object_count": result.object_count,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
