"""Lưu hoặc đọc bản nháp IOC pending trong SQLite cục bộ."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.store import DraftStoreError, get_draft, list_drafts, save_draft  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="lưu một draft JSON mới")
    save_parser.add_argument("--db", required=True, type=Path, help="file SQLite")
    save_parser.add_argument("--input", required=True, type=Path, help="draft JSON UTF-8")
    save_parser.add_argument("--created-by-subject", help="subject opaque của tác giả draft")
    save_parser.add_argument("--timeout", type=float, default=5.0, help="timeout khóa DB (giây)")

    get_parser = subparsers.add_parser("get", help="đọc một draft theo ID")
    get_parser.add_argument("--db", required=True, type=Path, help="file SQLite")
    get_parser.add_argument("--id", required=True, type=int, help="ID draft")
    get_parser.add_argument("--output", required=True, type=Path, help="file JSON sẽ tạo")
    get_parser.add_argument("--timeout", type=float, default=5.0, help="timeout khóa DB (giây)")

    list_parser = subparsers.add_parser("list", help="liệt kê draft pending theo từng trang")
    list_parser.add_argument("--db", required=True, type=Path, help="file SQLite")
    list_parser.add_argument("--limit", type=int, default=20, help="số draft mỗi trang (1-100)")
    list_parser.add_argument("--before-id", type=int, help="chỉ lấy draft có ID nhỏ hơn cursor")
    list_parser.add_argument("--output", required=True, type=Path, help="file JSON summary sẽ tạo")
    list_parser.add_argument("--timeout", type=float, default=5.0, help="timeout khóa DB (giây)")
    return parser.parse_args()


def _ensure_output_is_not_database(db_path: Path, output_path: Path) -> None:
    db_resolved = os.path.normcase(str(db_path.resolve()))
    output_resolved = os.path.normcase(str(output_path.resolve()))
    if db_resolved == output_resolved:
        raise DraftStoreError("output không được trùng database")
    if db_path.exists() and output_path.exists() and db_path.samefile(output_path):
        raise DraftStoreError("output không được trỏ tới cùng file database")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    try:
        if args.command == "save":
            draft = json.loads(args.input.read_text(encoding="utf-8"))
            draft_id = save_draft(
                args.db,
                draft,
                created_by_subject=args.created_by_subject,
                timeout=args.timeout,
            )
            print(json.dumps({"id": draft_id, "status": "pending"}))
            return 0

        _ensure_output_is_not_database(args.db, args.output)
        if args.command == "get":
            stored = get_draft(args.db, args.id, timeout=args.timeout)
            _write_json(args.output, stored)
            print(
                json.dumps(
                    {
                        "id": args.id,
                        "payload_status": stored["status"],
                        "review_status": stored["review"]["status"],
                        "review_version": stored["review"]["version"],
                    }
                )
            )
            return 0

        page = list_drafts(
            args.db,
            limit=args.limit,
            before_id=args.before_id,
            timeout=args.timeout,
        )
        _write_json(args.output, page)
        print(json.dumps({"count": len(page["items"]), "next_before_id": page["next_before_id"]}))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, DraftStoreError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
