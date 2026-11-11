"""CLI local/offline nhập một envelope X01 vào SQLite W05."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor import store  # noqa: E402
from phonghoa_extractor.ingest_queue import (  # noqa: E402
    IngestEnvelopeError,
    IngestWriteError,
    load_ingest_envelope,
    paths_refer_to_same_file,
    save_ingested_envelope,
)


class _InvalidArguments(ValueError):
    pass


class _ClosedParser(argparse.ArgumentParser):
    def error(self, _message: str) -> NoReturn:
        raise _InvalidArguments


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = _ClosedParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    importer = subparsers.add_parser("import")
    importer.add_argument("--envelope", required=True, type=Path)
    importer.add_argument("--db", required=True, type=Path)
    importer.add_argument("--created-by-subject", required=True)
    importer.add_argument("--timeout", default="5")
    return parser.parse_args(argv)


def _parse_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise _InvalidArguments from exc
    if not math.isfinite(timeout) or timeout < 0:
        raise _InvalidArguments
    return timeout


def _is_locked(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        code = getattr(current, "sqlite_errorcode", None)
        if code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
            return True
        current = current.__cause__
    return False


def _map_error(exc: store.DraftStoreError) -> str:
    if isinstance(exc, IngestEnvelopeError):
        return exc.code
    if isinstance(exc, store.DraftConflictError):
        return "duplicate_creator_conflict"
    if isinstance(exc, IngestWriteError):
        return "database_locked" if _is_locked(exc) else "write_failed"
    if isinstance(exc, store.DraftInputError):
        return "invalid_created_by_subject"
    if isinstance(exc, store.DraftSQLiteError):
        return "database_locked" if _is_locked(exc) else "database_invalid"
    return "write_failed"


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        args = _parse_args(argv)
        timeout = _parse_timeout(args.timeout)
    except _InvalidArguments:
        print("Lỗi: invalid_arguments", file=sys.stderr)
        return 2
    try:
        store._validate_subject(args.created_by_subject, "created_by_subject")
        if paths_refer_to_same_file(args.envelope, args.db):
            raise IngestEnvelopeError("envelope_read_failed")
        envelope = load_ingest_envelope(args.envelope)
        result = save_ingested_envelope(
            args.db,
            envelope,
            created_by_subject=args.created_by_subject,
            timeout=timeout,
        )
    except store.DraftStoreError as exc:
        print(f"Lỗi: {_map_error(exc)}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"draft_id": result.draft_id, "result": result.result},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
