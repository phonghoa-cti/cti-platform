"""Cổng phát hiện chuỗi giấy phép EE, không phải chứng nhận pháp lý."""

import os
from pathlib import Path

EE_MARKER = b"OpenCTI Enterprise Edition License"
EXCLUDED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "data",
    "node_modules",
    "venv",
}
EXCLUDED_FILES = {
    Path("core/tests/test_no_opencti_ee_code.py"),
    Path("docs/specs/F18-thay-the-tinh-nang-tra-phi.md"),
    Path("docs/specs/F19-playbook-tu-dong.md"),
    Path("docs/adr/0018-khong-dung-ma-enterprise-opencti.md"),
}


def contains_marker(path: Path) -> bool:
    """Đọc theo khối, giữ phần giao nhau để không bỏ sót header."""
    tail = b""
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            window = tail + chunk
            if EE_MARKER in window:
                return True
            tail = window[-(len(EE_MARKER) - 1) :]
    return False


def raise_walk_error(error: OSError) -> None:
    raise error


def find_ee_files(root: Path) -> list[str]:
    """Chỉ trả đường dẫn vi phạm; không in nội dung file."""
    findings = []
    for directory, subdirs, files in os.walk(root, onerror=raise_walk_error):
        folder = Path(directory)
        subdirs[:] = [
            name for name in subdirs if name not in EXCLUDED_DIRS and not (folder / name).is_symlink()
        ]
        for name in files:
            path = folder / name
            relative = path.relative_to(root)
            if relative in EXCLUDED_FILES or path.is_symlink():
                continue
            if contains_marker(path):
                findings.append(relative.as_posix())
    return sorted(findings)


def test_no_opencti_ee_code() -> None:
    root = Path(__file__).resolve().parents[2]
    findings = find_ee_files(root)
    assert not findings, f"Phát hiện dấu hiệu giấy phép EE (cần rà soát): {findings}"


def test_scanner_detects_marker_across_chunks(tmp_path: Path) -> None:
    (tmp_path / "candidate.py").write_bytes(b"x" * 65530 + EE_MARKER)
    (tmp_path / "community.py").write_bytes(b"# Apache License, Version 2.0")
    assert find_ee_files(tmp_path) == ["candidate.py"]


def test_scanner_excludes_only_named_docs_and_cache(tmp_path: Path) -> None:
    for relative in EXCLUDED_FILES | {Path(name) / "sample.txt" for name in EXCLUDED_DIRS}:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(EE_MARKER)
    unexpected = tmp_path / "docs" / "unexpected.py"
    unexpected.write_bytes(EE_MARKER)
    assert find_ee_files(tmp_path) == ["docs/unexpected.py"]
