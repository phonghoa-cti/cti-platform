"""Nạp TXT/PDF cục bộ thành văn bản canonical có provenance hữu hạn."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal

_PDF_SEPARATOR = "\n\f\n"
_PDF_ERROR_CODES = {
    "pdf_malformed",
    "pdf_encrypted",
    "pdf_page_limit",
    "pdf_page_text_limit",
    "pdf_total_text_limit",
    "pdf_no_extractable_text",
}


@dataclass(frozen=True)
class IngestLimits:
    max_raw_bytes: int = 8 * 1024 * 1024
    max_pages: int = 50
    max_page_codepoints: int = 100_000
    max_total_codepoints: int = 1_000_000
    pdf_timeout_seconds: int = 15
    max_child_result_bytes: int = 16 * 1024 * 1024


@dataclass(frozen=True)
class IngestedDocument:
    format: Literal["text", "pdf"]
    display_name: str
    raw_sha256: str
    raw_bytes: int
    canonical_text: str
    canonical_text_sha256: str
    page_count: int | None
    page_text_ranges: tuple[tuple[int, int], ...] | None


class LocalIngestError(ValueError):
    """Lỗi ingest đóng, chỉ lộ mã ổn định."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _ChildLifecycleError(LocalIngestError):
    def __init__(self, code: str, *, reaped: bool) -> None:
        self.reaped = reaped
        super().__init__(code)


_HARD_LIMITS = IngestLimits()


def ingest_local_file(
    path: Path,
    *,
    limits: IngestLimits = IngestLimits(),  # noqa: B008 - API contract uses frozen value
) -> IngestedDocument:
    """Đọc một file regular local; không URL, network share hoặc symlink."""
    _validate_limits(limits)
    display_name = _validate_input(path)
    raw = _read_capped(path, limits.max_raw_bytes)
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    if path.suffix.lower() == ".txt":
        return _ingest_text(display_name, raw, raw_sha256, limits)
    pages = _extract_pdf_pages(raw, limits)
    return _build_pdf_document(display_name, raw, raw_sha256, pages, limits)


def _validate_limits(limits: IngestLimits) -> None:
    if type(limits) is not IngestLimits:
        raise LocalIngestError("invalid_limits")
    for field in fields(IngestLimits):
        value = getattr(limits, field.name)
        maximum = getattr(_HARD_LIMITS, field.name)
        if type(value) is not int or not 1 <= value <= maximum:
            raise LocalIngestError("invalid_limits")


def _validate_input(path: Path) -> str:
    if not isinstance(path, Path):
        raise LocalIngestError("invalid_input")
    name = path.name
    if not name or any(char in "/\\" or ord(char) < 32 or ord(char) == 127 for char in name):
        raise LocalIngestError("invalid_input_name")
    try:
        name.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise LocalIngestError("invalid_input_name") from exc
    _validate_regular_local(path)
    if path.suffix.lower() not in {".txt", ".pdf"}:
        raise LocalIngestError("unsupported_type")
    return name


def _validate_regular_local(path: Path) -> None:
    if str(path).startswith(("\\\\", "//")):
        raise LocalIngestError("input_not_regular")
    _validate_ancestor_chain(path)
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise LocalIngestError("input_missing") from exc
    except OSError as exc:
        raise LocalIngestError("input_read_failed") from exc
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(info, "st_file_attributes", 0)
    if stat.S_ISLNK(info.st_mode) or attributes & reparse or not stat.S_ISREG(info.st_mode):
        raise LocalIngestError("input_not_regular")


def _validate_ancestor_chain(path: Path) -> None:
    if path.drive and not path.is_absolute():
        raise LocalIngestError("input_not_regular")
    if path.is_absolute():
        current = Path(path.anchor)
        _validate_directory_node(current)
        parts = path.parts[1:-1]
    else:
        current = Path.cwd()
        for ancestor in (current, *current.parents):
            _validate_directory_node(ancestor)
        parts = path.parts[:-1]
    for part in parts:
        if part in {"", "."}:
            continue
        current = current.parent if part == ".." else current / part
        _validate_directory_node(current)


def _validate_directory_node(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise LocalIngestError("input_missing") from exc
    except OSError as exc:
        raise LocalIngestError("input_read_failed") from exc
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(info, "st_file_attributes", 0)
    if stat.S_ISLNK(info.st_mode) or attributes & reparse or not stat.S_ISDIR(info.st_mode):
        raise LocalIngestError("input_not_regular")


def _read_capped(path: Path, cap: int) -> bytes:
    try:
        with path.open("rb") as handle:
            raw = handle.read(cap + 1)
    except OSError as exc:
        raise LocalIngestError("input_read_failed") from exc
    if len(raw) > cap:
        raise LocalIngestError("input_too_large")
    return raw


def _ingest_text(name: str, raw: bytes, raw_hash: str, limits: IngestLimits) -> IngestedDocument:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise LocalIngestError("invalid_utf8") from exc
    if len(text) > limits.max_total_codepoints:
        raise LocalIngestError("text_total_limit")
    return IngestedDocument(
        format="text",
        display_name=name,
        raw_sha256=raw_hash,
        raw_bytes=len(raw),
        canonical_text=text,
        canonical_text_sha256=_text_hash(text),
        page_count=None,
        page_text_ranges=None,
    )


def _extract_pdf_pages(raw: bytes, limits: IngestLimits) -> list[str]:
    if importlib.util.find_spec("pypdf") is None:
        raise LocalIngestError("pdf_support_unavailable")
    if not raw.startswith(b"%PDF-"):
        raise LocalIngestError("not_pdf")
    try:
        root = Path(tempfile.mkdtemp(prefix="x01-pdf-"))
    except OSError as exc:
        raise LocalIngestError("input_read_failed") from exc
    cleanup_allowed = True
    try:
        snapshot = root / "input.pdf"
        result = root / "result.json"
        snapshot.write_bytes(raw)
        _snapshot_ready_hook(snapshot)
        pages = _run_pdf_child(snapshot, result, limits)
    except _ChildLifecycleError as exc:
        cleanup_allowed = exc.reaped
        raise LocalIngestError(exc.code) from exc
    except LocalIngestError:
        raise
    except (OSError, ValueError) as exc:
        raise LocalIngestError("input_read_failed") from exc
    finally:
        if cleanup_allowed:
            _cleanup_pdf_temp(root)
    return pages


def _cleanup_pdf_temp(root: Path) -> None:
    expected_parent = Path(tempfile.gettempdir()).resolve(strict=False)
    actual = root.resolve(strict=False)
    if actual.parent != expected_parent or not actual.name.startswith("x01-pdf-"):
        raise LocalIngestError("pdf_child_failed")
    try:
        shutil.rmtree(actual)
    except OSError as exc:
        raise LocalIngestError("pdf_child_failed") from exc


def _run_pdf_child(snapshot: Path, result: Path, limits: IngestLimits) -> list[str]:
    script = Path(__file__).resolve().parents[1] / "ingest" / "pdf_child.py"
    command = [
        sys.executable,
        str(script),
        str(snapshot),
        str(result),
        str(limits.max_pages),
        str(limits.max_page_codepoints),
        str(limits.max_total_codepoints),
        str(limits.max_child_result_bytes),
    ]
    try:
        process = _spawn_pdf_child(command)
    except OSError as exc:
        raise LocalIngestError("pdf_child_failed") from exc
    _wait_for_child(process, command, limits.pdf_timeout_seconds)
    if process.returncode != 0 or not result.is_file():
        raise LocalIngestError("pdf_child_failed")
    payload = _read_child_result(result, limits.max_child_result_bytes)
    return _decode_child_result(payload)


def _spawn_pdf_child(command: list[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        close_fds=True,
    )


def _wait_for_child(
    process: subprocess.Popen[bytes],
    command: list[str],
    timeout: int,
) -> None:
    deadline = time.monotonic() + timeout
    reaped, failed = _bounded_wait(process, max(0.0, deadline - time.monotonic()))
    if reaped and not failed:
        return
    had_oserror = failed
    if _process_exited(process):
        raise _ChildLifecycleError("pdf_child_failed", reaped=True)
    try:
        process.terminate()
    except OSError:
        had_oserror = True
    if _process_exited(process):
        code = "pdf_child_failed" if had_oserror else "pdf_child_timeout"
        raise _ChildLifecycleError(code, reaped=True)
    reaped, failed = _bounded_wait(process, 2)
    had_oserror = had_oserror or failed
    if reaped:
        code = "pdf_child_failed" if had_oserror else "pdf_child_timeout"
        raise _ChildLifecycleError(code, reaped=True)
    try:
        process.kill()
    except OSError:
        had_oserror = True
    if _process_exited(process):
        code = "pdf_child_failed" if had_oserror else "pdf_child_timeout"
        raise _ChildLifecycleError(code, reaped=True)
    reaped, failed = _bounded_wait(process, 2)
    if reaped:
        code = "pdf_child_failed" if had_oserror or failed else "pdf_child_timeout"
        raise _ChildLifecycleError(code, reaped=True)
    raise _ChildLifecycleError("pdf_child_failed", reaped=False)


def _bounded_wait(process: subprocess.Popen[bytes], timeout: float) -> tuple[bool, bool]:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, False
    except OSError:
        return _process_exited(process), True
    return True, False


def _process_exited(process: subprocess.Popen[bytes]) -> bool:
    poll = getattr(process, "poll", None)
    if poll is None:
        return process.returncode is not None
    try:
        return poll() is not None
    except OSError:
        return process.returncode is not None


def _read_child_result(path: Path, cap: int) -> bytes:
    try:
        with path.open("rb") as handle:
            payload = handle.read(cap + 1)
    except OSError as exc:
        raise LocalIngestError("pdf_child_failed") from exc
    if len(payload) > cap:
        raise LocalIngestError("pdf_child_result_too_large")
    return payload


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _decode_child_result(payload: bytes) -> list[str]:
    try:
        decoded = payload.decode("utf-8", "strict")
        data = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("nonfinite")),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise LocalIngestError("pdf_child_invalid_result") from exc
    if type(data) is not dict or type(data.get("ok")) is not bool:
        raise LocalIngestError("pdf_child_invalid_result")
    if data["ok"] is False:
        code = data.get("code")
        if set(data) != {"ok", "code"} or type(code) is not str or code not in _PDF_ERROR_CODES:
            raise LocalIngestError("pdf_child_invalid_result")
        raise LocalIngestError(code)
    if set(data) != {"ok", "pages"} or type(data.get("pages")) is not list:
        raise LocalIngestError("pdf_child_invalid_result")
    if any(type(page) is not str for page in data["pages"]):
        raise LocalIngestError("pdf_child_invalid_result")
    return data["pages"]


def _build_pdf_document(
    name: str,
    raw: bytes,
    raw_hash: str,
    pages: list[str],
    limits: IngestLimits,
) -> IngestedDocument:
    _validate_pdf_pages(pages, limits)
    text = _PDF_SEPARATOR.join(pages)
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for index, page in enumerate(pages):
        ranges.append((cursor, cursor + len(page)))
        cursor += len(page)
        if index + 1 < len(pages):
            cursor += len(_PDF_SEPARATOR)
    return IngestedDocument(
        format="pdf",
        display_name=name,
        raw_sha256=raw_hash,
        raw_bytes=len(raw),
        canonical_text=text,
        canonical_text_sha256=_text_hash(text),
        page_count=len(pages),
        page_text_ranges=tuple(ranges),
    )


def _validate_pdf_pages(pages: list[str], limits: IngestLimits) -> None:
    if not pages:
        raise LocalIngestError("pdf_malformed")
    if len(pages) > limits.max_pages:
        raise LocalIngestError("pdf_page_limit")
    total = len(_PDF_SEPARATOR) * (len(pages) - 1)
    for page in pages:
        try:
            page.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise LocalIngestError("pdf_malformed") from exc
        if len(page) > limits.max_page_codepoints:
            raise LocalIngestError("pdf_page_text_limit")
        total += len(page)
    if total > limits.max_total_codepoints:
        raise LocalIngestError("pdf_total_text_limit")
    if not any(page.strip() for page in pages):
        raise LocalIngestError("pdf_no_extractable_text")


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "strict")).hexdigest()


def _snapshot_ready_hook(_snapshot: Path) -> None:
    """Điểm test nội bộ sau khi snapshot đã được ghi."""
