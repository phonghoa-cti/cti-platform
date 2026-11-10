"""Lưu hoặc đọc bản nháp IOC pending trong SQLite cục bộ."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.store import DraftStoreError, get_draft, save_draft  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="lưu một draft JSON mới")
    save_parser.add_argument("--db", required=True, type=Path, help="file SQLite")
    save_parser.add_argument("--input", required=True, type=Path, help="draft JSON UTF-8")
    save_parser.add_argument("--timeout", type=float, default=5.0, help="timeout khóa DB (giây)")

    get_parser = subparsers.add_parser("get", help="đọc một draft theo ID")
    get_parser.add_argument("--db", required=True, type=Path, help="file SQLite")
    get_parser.add_argument("--id", required=True, type=int, help="ID draft")
    get_parser.add_argument("--output", required=True, type=Path, help="file JSON sẽ tạo")
    get_parser.add_argument("--timeout", type=float, default=5.0, help="timeout khóa DB (giây)")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    try:
        if args.command == "save":
            draft = json.loads(args.input.read_text(encoding="utf-8"))
            draft_id = save_draft(args.db, draft, timeout=args.timeout)
            print(json.dumps({"id": draft_id, "status": "pending"}))
            return 0

        stored = get_draft(args.db, args.id, timeout=args.timeout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"id": args.id, "status": "pending"}))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, DraftStoreError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
