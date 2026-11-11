"""Tạo envelope draft C1 pending từ TXT/PDF cục bộ."""

from __future__ import annotations

import argparse
import errno
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.drafts import build_regex_draft  # noqa: E402
from phonghoa_extractor.local_ingest import (  # noqa: E402
    IngestedDocument,
    LocalIngestError,
    ingest_local_file,
)

TLP_CHOICES = ("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED")


class _InvalidArguments(ValueError):
    pass


class _ClosedArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> NoReturn:
        raise _InvalidArguments


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _ClosedArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--language", required=True, choices=("vi", "en"))
    parser.add_argument("--tlp", default="TLP:AMBER", choices=TLP_CHOICES)
    return parser.parse_args(argv)


def _build_envelope(document: IngestedDocument, language: str, tlp: str) -> dict[str, object]:
    draft = build_regex_draft(
        document.canonical_text,
        source=document.display_name,
        language=language,
        tlp=tlp,
    )
    return {
        "schema_version": "x01-local-ingest/1.0",
        "input": {
            "format": document.format,
            "display_name": document.display_name,
            "raw_sha256": document.raw_sha256,
            "raw_bytes": document.raw_bytes,
            "canonical_text_sha256": document.canonical_text_sha256,
            "page_count": document.page_count,
            "page_text_ranges": document.page_text_ranges,
        },
        "draft": draft,
    }


def _validate_output(input_path: Path, output: Path) -> None:
    try:
        if output == input_path or output.resolve(strict=False) == input_path.resolve(strict=False):
            raise LocalIngestError("unsafe_output_path")
        if not output.parent.is_dir():
            raise LocalIngestError("output_parent_invalid")
        if output.exists():
            if os.path.samefile(input_path, output):
                raise LocalIngestError("unsafe_output_path")
            raise LocalIngestError("output_exists")
    except LocalIngestError:
        raise
    except OSError as exc:
        raise LocalIngestError("output_write_failed") from exc


def _serialize_envelope(envelope: dict[str, object]) -> bytes:
    try:
        text = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            indent=2,
        )
    except (TypeError, ValueError) as exc:
        raise LocalIngestError("output_write_failed") from exc
    return (text + "\n").encode("utf-8")


def _publish_envelope(input_path: Path, output: Path, envelope: dict[str, object]) -> None:
    _validate_output(input_path, output)
    encoded = _serialize_envelope(envelope)
    temp_path: Path | None = None
    pending_error: LocalIngestError | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output.parent, prefix=".x01-ingest-", suffix=".tmp", delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        pending_error = LocalIngestError("output_write_failed")
    if pending_error is None:
        try:
            _before_publish_hook()
            os.link(temp_path, output)
        except FileExistsError:
            pending_error = LocalIngestError("output_exists")
        except OSError as exc:
            code = (
                "output_publish_unsupported"
                if exc.errno in _UNSUPPORTED_LINK_ERRNOS
                else "output_write_failed"
            )
            pending_error = LocalIngestError(code)
    try:
        if temp_path is not None and temp_path.exists():
            os.unlink(temp_path)
    except OSError as exc:
        raise LocalIngestError("output_cleanup_failed") from exc
    if pending_error is not None:
        raise pending_error


_UNSUPPORTED_LINK_ERRNOS = {
    errno.EPERM,
    errno.EXDEV,
    getattr(errno, "ENOTSUP", errno.EPERM),
    getattr(errno, "EOPNOTSUPP", errno.EPERM),
}


def _before_publish_hook() -> None:
    """Điểm test nội bộ ngay trước publish no-clobber."""


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        args = _parse_args(argv)
    except _InvalidArguments:
        print("Lỗi: invalid_arguments", file=sys.stderr)
        return 2
    try:
        document = ingest_local_file(args.input)
        envelope = _build_envelope(document, args.language, args.tlp)
        _publish_envelope(args.input, args.output, envelope)
    except LocalIngestError as exc:
        print(f"Lỗi: {exc.code}", file=sys.stderr)
        return 1
    summary = {
        "schema_version": "x01-local-ingest/1.0",
        "format": document.format,
        "output_created": True,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
