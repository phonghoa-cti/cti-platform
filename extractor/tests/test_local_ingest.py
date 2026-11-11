from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from ingest import pdf_child
from pypdf import PdfWriter

import phonghoa_extractor.local_ingest as local_ingest
from phonghoa_extractor.local_ingest import (
    IngestLimits,
    LocalIngestError,
    ingest_local_file,
)

FIXTURES = Path(__file__).parent / "fixtures" / "local_ingest"


def assert_error(code: str, function, *args, **kwargs) -> None:
    with pytest.raises(LocalIngestError) as caught:
        function(*args, **kwargs)
    assert caught.value.code == code
    assert str(caught.value) == code


def test_text_preserves_bytes_and_unicode_contract() -> None:
    path = FIXTURES / "text-crlf.txt"
    raw = path.read_bytes()

    document = ingest_local_file(path)

    assert document.format == "text"
    assert document.display_name == "text-crlf.txt"
    assert document.raw_bytes == len(raw)
    assert document.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert document.canonical_text == "line one\r\nline two\rline three\n\x00"
    assert document.canonical_text_sha256 == hashlib.sha256(raw).hexdigest()
    assert document.page_count is None
    assert document.page_text_ranges is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [("text-bom.txt", "\ufeffBOM stays"), ("text-vi-emoji.txt", "Bao cao Việt Nam 😀 IOC 192.0.2.1")],
)
def test_text_keeps_bom_vietnamese_and_emoji(name: str, expected: str) -> None:
    assert ingest_local_file(FIXTURES / name).canonical_text == expected


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, None, "1", [], {}])
def test_limits_require_exact_bounded_ints_before_io(value: object) -> None:
    limits = IngestLimits(max_raw_bytes=value)  # type: ignore[arg-type]
    assert_error("invalid_limits", ingest_local_file, Path("missing.txt"), limits=limits)


@pytest.mark.parametrize(
    "field",
    [
        "max_raw_bytes",
        "max_pages",
        "max_page_codepoints",
        "max_total_codepoints",
        "pdf_timeout_seconds",
        "max_child_result_bytes",
    ],
)
def test_each_limit_rejects_bool(field: str) -> None:
    assert_error(
        "invalid_limits",
        ingest_local_file,
        Path("missing.txt"),
        limits=IngestLimits(**{field: True}),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_raw_bytes", 8 * 1024 * 1024 + 1),
        ("max_pages", 51),
        ("max_page_codepoints", 100_001),
        ("max_total_codepoints", 1_000_001),
        ("pdf_timeout_seconds", 16),
        ("max_child_result_bytes", 16 * 1024 * 1024 + 1),
    ],
)
def test_limits_cannot_raise_hard_maximum(field: str, value: int) -> None:
    values = {field: value}
    assert_error("invalid_limits", ingest_local_file, Path("missing.txt"), limits=IngestLimits(**values))


def test_input_validation_and_error_order(tmp_path: Path) -> None:
    assert_error("invalid_input", ingest_local_file, "report.txt")  # type: ignore[arg-type]
    assert_error("invalid_input_name", ingest_local_file, tmp_path / "bad\nname.txt")
    assert_error("input_missing", ingest_local_file, tmp_path / "missing.txt")
    assert_error("input_not_regular", ingest_local_file, tmp_path)
    unsupported = tmp_path / "input.bin"
    unsupported.write_bytes(b"x")
    assert_error("unsupported_type", ingest_local_file, unsupported)


def test_symlink_input_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("safe", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    assert_error("input_not_regular", ingest_local_file, link)


def test_text_errors_are_finite(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff")
    assert_error("invalid_utf8", ingest_local_file, invalid)

    large = tmp_path / "large.txt"
    large.write_bytes(b"ab")
    assert_error("input_too_large", ingest_local_file, large, limits=IngestLimits(max_raw_bytes=1))

    text = tmp_path / "text.txt"
    text.write_text("ab", encoding="utf-8")
    assert_error("text_total_limit", ingest_local_file, text, limits=IngestLimits(max_total_codepoints=1))


def test_pdf_two_pages_uses_actual_child_and_exact_ranges() -> None:
    document = ingest_local_file(FIXTURES / "two-text-pages.pdf")
    first = "Page one IOC 192.0.2.1"
    second = "Page two domain example.test"
    separator = "\n\f\n"
    assert document.format == "pdf"
    assert document.canonical_text == first + separator + second
    assert document.page_count == 2
    assert document.page_text_ranges == ((0, len(first)), (len(first) + 3, len(first) + 3 + len(second)))
    assert (
        document.canonical_text_sha256 == hashlib.sha256(document.canonical_text.encode("utf-8")).hexdigest()
    )


def test_pdf_blank_middle_page_keeps_empty_range_and_separators() -> None:
    document = ingest_local_file(FIXTURES / "blank-middle-page.pdf")
    assert document.canonical_text == "First\n\f\n\n\f\nThird"
    assert document.page_text_ranges == ((0, 5), (8, 8), (11, 16))


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("all-whitespace-pages.pdf", "pdf_no_extractable_text"),
        ("encrypted.pdf", "pdf_encrypted"),
        ("malformed.pdf", "pdf_malformed"),
    ],
)
def test_pdf_child_returns_closed_parser_errors(name: str, code: str) -> None:
    assert_error(code, ingest_local_file, FIXTURES / name)


def test_pdf_magic_and_page_limits(tmp_path: Path) -> None:
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"not-pdf")
    assert_error("not_pdf", ingest_local_file, fake)
    assert_error(
        "pdf_page_limit",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(max_pages=1),
    )

    zero_page = tmp_path / "zero.pdf"
    with zero_page.open("wb") as handle:
        PdfWriter().write(handle)
    assert_error("pdf_malformed", ingest_local_file, zero_page)


def test_pdf_support_is_checked_without_parent_import(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local_ingest.importlib.util, "find_spec", lambda _name: None)
    assert_error("pdf_support_unavailable", ingest_local_file, FIXTURES / "two-text-pages.pdf")


def test_pdf_is_bound_to_parent_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "changing.pdf"
    original = (FIXTURES / "two-text-pages.pdf").read_bytes()
    replacement = (FIXTURES / "blank-middle-page.pdf").read_bytes()
    source.write_bytes(original)

    def mutate_original(_snapshot: Path) -> None:
        source.write_bytes(replacement)

    monkeypatch.setattr(local_ingest, "_snapshot_ready_hook", mutate_original)
    document = ingest_local_file(source)
    assert document.raw_sha256 == hashlib.sha256(original).hexdigest()
    assert document.page_count == 2
    assert document.canonical_text.startswith("Page one")
    assert source.read_bytes() == replacement


class FakeProcess:
    def __init__(self, command: list[str], mode: str) -> None:
        self.command = command
        self.mode = mode
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False
        self.wait_count = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_count += 1
        if self.mode == "timeout" and not self.terminated and not self.killed:
            raise subprocess.TimeoutExpired(self.command, timeout)
        if self.mode == "kill" and self.wait_count < 3:
            raise subprocess.TimeoutExpired(self.command, timeout)
        self.returncode = 1 if self.mode == "failed" else 0
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True


@pytest.mark.parametrize(
    ("mode", "payload", "cap", "code"),
    [
        ("missing", None, 32, "pdf_child_failed"),
        ("invalid", b'{"ok":true,"ok":false,"pages":[]}', 64, "pdf_child_invalid_result"),
        ("code-list", b'{"ok":false,"code":[]}', 64, "pdf_child_invalid_result"),
        ("code-dict", b'{"ok":false,"code":{}}', 64, "pdf_child_invalid_result"),
        ("nonfinite", b'{"ok":true,"pages":[NaN]}', 32, "pdf_child_invalid_result"),
        ("oversize", b"x" * 33, 32, "pdf_child_result_too_large"),
    ],
)
def test_child_result_is_strict_and_capped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
    payload: bytes | None,
    cap: int,
    code: str,
) -> None:
    created: list[FakeProcess] = []

    def spawn(command: list[str]) -> FakeProcess:
        if payload is not None:
            Path(command[3]).write_bytes(payload)
        process = FakeProcess(command, mode)
        created.append(process)
        return process

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    limits = IngestLimits(max_child_result_bytes=cap)
    assert_error(code, ingest_local_file, FIXTURES / "two-text-pages.pdf", limits=limits)
    assert created and created[0].returncode == 0


def test_timeout_terminates_reaps_and_cleans_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    created: list[FakeProcess] = []
    temp_roots: list[Path] = []

    def spawn(command: list[str]) -> FakeProcess:
        temp_roots.append(Path(command[3]).parent)
        process = FakeProcess(command, "timeout")
        created.append(process)
        return process

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_child_timeout",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(pdf_timeout_seconds=1),
    )
    assert created[0].terminated is True
    assert created[0].returncode == 0
    assert temp_roots and not temp_roots[0].exists()


def test_timeout_escalates_to_kill_and_reaps(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[FakeProcess] = []

    def spawn(command: list[str]) -> FakeProcess:
        process = FakeProcess(command, "kill")
        created.append(process)
        return process

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_child_timeout",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(pdf_timeout_seconds=1),
    )
    assert created[0].terminated is True
    assert created[0].killed is True
    assert created[0].returncode == 0


def test_lifecycle_failure_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[FakeProcess] = []
    roots: list[Path] = []

    class BrokenTerminate(FakeProcess):
        def wait(self, timeout: float | None = None) -> int:
            self.wait_count += 1
            if self.killed:
                self.returncode = 1
                return 1
            raise subprocess.TimeoutExpired(self.command, timeout)

        def terminate(self) -> None:
            raise OSError("terminate failed")

    def spawn(command: list[str]) -> BrokenTerminate:
        roots.append(Path(command[3]).parent)
        process = BrokenTerminate(command, "timeout")
        created.append(process)
        return process

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_child_failed",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(pdf_timeout_seconds=1),
    )
    assert created[0].killed is True
    assert created[0].returncode == 1
    assert roots and not roots[0].exists()


def test_unreaped_child_preserves_owned_temp(monkeypatch: pytest.MonkeyPatch) -> None:
    roots: list[Path] = []

    class UnrecoverableProcess(FakeProcess):
        def wait(self, timeout: float | None = None) -> int:
            raise OSError("wait failed")

        def terminate(self) -> None:
            raise OSError("terminate failed")

        def kill(self) -> None:
            raise OSError("kill failed")

        def poll(self) -> None:
            return None

    def spawn(command: list[str]) -> UnrecoverableProcess:
        roots.append(Path(command[3]).parent)
        return UnrecoverableProcess(command, "broken")

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error("pdf_child_failed", ingest_local_file, FIXTURES / "two-text-pages.pdf")
    assert roots and roots[0].is_dir()
    assert (roots[0] / "input.pdf").is_file()
    shutil.rmtree(roots[0])


def test_dead_child_after_terminate_error_allows_temp_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    roots: list[Path] = []

    class DiedDuringTerminate(FakeProcess):
        def wait(self, timeout: float | None = None) -> int:
            raise subprocess.TimeoutExpired(self.command, timeout)

        def terminate(self) -> None:
            self.returncode = 1
            raise OSError("already exited")

        def poll(self) -> int:
            return 1

    def spawn(command: list[str]) -> DiedDuringTerminate:
        roots.append(Path(command[3]).parent)
        return DiedDuringTerminate(command, "dead")

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_child_failed",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(pdf_timeout_seconds=1),
    )
    assert roots and not roots[0].exists()


def test_abnormal_child_exit_wins_over_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def spawn(command: list[str]) -> FakeProcess:
        Path(command[3]).write_text(json.dumps({"ok": True, "pages": ["safe"]}), encoding="utf-8")
        return FakeProcess(command, "failed")

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error("pdf_child_failed", ingest_local_file, FIXTURES / "two-text-pages.pdf")


def test_child_success_is_revalidated_by_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    def spawn(command: list[str]) -> FakeProcess:
        Path(command[3]).write_text(json.dumps({"ok": True, "pages": ["ab"]}), encoding="utf-8")
        return FakeProcess(command, "success")

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_page_text_limit",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(max_page_codepoints=1),
    )


def test_child_total_text_limit_includes_separators(monkeypatch: pytest.MonkeyPatch) -> None:
    def spawn(command: list[str]) -> FakeProcess:
        Path(command[3]).write_text(json.dumps({"ok": True, "pages": ["a", "b"]}), encoding="utf-8")
        return FakeProcess(command, "success")

    monkeypatch.setattr(local_ingest, "_spawn_pdf_child", spawn)
    assert_error(
        "pdf_total_text_limit",
        ingest_local_file,
        FIXTURES / "two-text-pages.pdf",
        limits=IngestLimits(max_total_codepoints=4),
    )


def test_child_oversize_result_signals_parent_cap(tmp_path: Path) -> None:
    result = tmp_path / "result.json"
    pdf_child._write_result(result, {"ok": True, "pages": ["x" * 100]}, 64)
    assert result.stat().st_size == 65
    assert_error("pdf_child_result_too_large", local_ingest._read_child_result, result, 64)


def test_snapshot_temp_creation_failure_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_temp(*_args, **_kwargs):
        raise OSError("temp unavailable")

    monkeypatch.setattr(local_ingest.tempfile, "mkdtemp", fail_temp)
    assert_error("input_read_failed", ingest_local_file, FIXTURES / "two-text-pages.pdf")


@pytest.mark.parametrize("ancestor_level", [1, 2])
def test_reparse_ancestor_is_rejected_before_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, ancestor_level: int
) -> None:
    parent = tmp_path / "one" / "two"
    parent.mkdir(parents=True)
    source = parent / "input.txt"
    source.write_text("192.0.2.1", encoding="utf-8")
    flagged = source.parents[ancestor_level - 1]
    real_lstat = Path.lstat
    reads: list[Path] = []

    def lstat(path: Path, *args, **kwargs):
        original = real_lstat(path, *args, **kwargs)
        if path == flagged:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            )
        return original

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(local_ingest, "_read_capped", lambda path, cap: reads.append(path))
    assert_error("input_not_regular", ingest_local_file, source)
    assert reads == []


def test_regular_ancestors_remain_supported(tmp_path: Path) -> None:
    parent = tmp_path / "one" / "two"
    parent.mkdir(parents=True)
    source = parent / "input.txt"
    source.write_text("192.0.2.1", encoding="utf-8")
    assert ingest_local_file(source).canonical_text == "192.0.2.1"


@pytest.mark.parametrize(
    "source",
    [Path("input.txt"), Path("one") / ".." / "input.txt", Path(r"\one\input.txt")],
)
def test_cwd_dependent_input_under_unc_is_rejected_before_stat_or_read(
    monkeypatch: pytest.MonkeyPatch, source: Path
) -> None:
    stat_calls: list[Path] = []
    read_calls: list[Path] = []

    def unexpected_lstat(path: Path, *_args, **_kwargs):
        stat_calls.append(path)
        raise AssertionError("lstat must not run for an input under a UNC cwd")

    monkeypatch.setattr(Path, "cwd", classmethod(lambda _cls: Path(r"\\server\share")))
    monkeypatch.setattr(Path, "lstat", unexpected_lstat)
    monkeypatch.setattr(
        local_ingest,
        "_read_capped",
        lambda path, _cap: read_calls.append(path),
    )

    assert_error("input_not_regular", ingest_local_file, source)
    assert stat_calls == []
    assert read_calls == []


def test_absolute_local_input_does_not_consult_unc_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "input.txt"
    source.write_text("192.0.2.1", encoding="utf-8")

    def unexpected_cwd(_cls):
        raise AssertionError("absolute local input must not consult cwd")

    monkeypatch.setattr(Path, "cwd", classmethod(unexpected_cwd))
    assert ingest_local_file(source).canonical_text == "192.0.2.1"


def test_explicit_unc_input_is_rejected_before_stat(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_lstat(_path: Path, *_args, **_kwargs):
        raise AssertionError("explicit UNC input must be rejected before lstat")

    monkeypatch.setattr(Path, "lstat", unexpected_lstat)
    assert_error(
        "input_not_regular",
        ingest_local_file,
        Path(r"\\server\share\input.txt"),
    )


def test_relative_local_input_remains_supported(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("192.0.2.1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert ingest_local_file(Path("input.txt")).canonical_text == "192.0.2.1"
