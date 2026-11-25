from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from phonghoa_extractor.drafts import build_regex_draft
from phonghoa_extractor.store import get_draft

REPO_ROOT = Path(__file__).parents[2]
STORE_SCRIPT = REPO_ROOT / "extractor" / "draft" / "store.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STORE_SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def draft_file(tmp_path: Path, index: int, marker: str | None = None) -> Path:
    text = marker or f"CLI draft {index} 😀 evil{index}.example"
    draft = build_regex_draft(text, source=f"cli-{index}.txt", language="vi")
    path = tmp_path / f"draft-{index}.json"
    path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_save_many_list_pages_and_get_selected_id_without_leaking_text(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    marker = "FULL REPORT MUST NOT APPEAR 😀 evil5.example"
    for index in range(1, 6):
        saved = run(
            "save",
            "--db",
            str(db),
            "--input",
            str(draft_file(tmp_path, index, marker if index == 5 else None)),
        )
        assert saved.returncode == 0

    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    first_output = tmp_path / "first.json"
    first = run("list", "--db", str(db), "--limit", "2", "--output", str(first_output))
    first_page = json.loads(first_output.read_text(encoding="utf-8"))
    second_output = tmp_path / "second.json"
    second = run(
        "list",
        "--db",
        str(db),
        "--limit",
        "2",
        "--before-id",
        str(first_page["next_before_id"]),
        "--output",
        str(second_output),
    )
    second_page = json.loads(second_output.read_text(encoding="utf-8"))
    selected_id = second_page["items"][0]["id"]
    selected_output = tmp_path / "selected.json"
    loaded = run("get", "--db", str(db), "--id", str(selected_id), "--output", str(selected_output))

    assert first.returncode == second.returncode == loaded.returncode == 0
    assert [item["id"] for item in first_page["items"]] == [5, 4]
    assert [item["id"] for item in second_page["items"]] == [3, 2]
    assert first_page["next_before_id"] == 4
    assert second_page["next_before_id"] == 2
    assert json.loads(selected_output.read_text(encoding="utf-8"))["id"] == selected_id
    assert marker not in first_output.read_text(encoding="utf-8")
    assert marker not in first.stdout + first.stderr + second.stdout + second.stderr
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash


@pytest.mark.parametrize("command", ["list", "get"])
def test_cli_refuses_output_equivalent_or_samefile_with_database(tmp_path: Path, command: str):
    db = tmp_path / "drafts.sqlite"
    saved = run("save", "--db", str(db), "--input", str(draft_file(tmp_path, 1)))
    assert saved.returncode == 0
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    equivalent = tmp_path / "unused" / ".." / db.name
    args = [command, "--db", str(db)]
    if command == "list":
        args.extend(["--output", str(equivalent)])
    else:
        args.extend(["--id", "1", "--output", str(equivalent)])

    equivalent_result = run(*args)
    alias = tmp_path / f"{command}-alias.sqlite"
    os.link(db, alias)
    samefile_args = [command, "--db", str(db)]
    if command == "list":
        samefile_args.extend(["--output", str(alias)])
    else:
        samefile_args.extend(["--id", "1", "--output", str(alias)])
    samefile_result = run(*samefile_args)

    assert equivalent_result.returncode == samefile_result.returncode == 1
    assert "output" in equivalent_result.stderr.lower()
    assert "output" in samefile_result.stderr.lower()
    assert "Traceback" not in equivalent_result.stderr + samefile_result.stderr
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash
    assert get_draft(db, 1)["id"] == 1


@pytest.mark.parametrize("failure", ["invalid_limit", "missing_db", "corrupt_db", "locked_db"])
def test_cli_list_errors_do_not_overwrite_existing_output(tmp_path: Path, failure: str):
    output = tmp_path / "existing.json"
    output.write_text("KEEP THIS", encoding="utf-8")
    db = tmp_path / "drafts.sqlite"
    locker: sqlite3.Connection | None = None

    if failure in {"invalid_limit", "locked_db"}:
        assert run("save", "--db", str(db), "--input", str(draft_file(tmp_path, 1))).returncode == 0
    elif failure == "corrupt_db":
        db.write_bytes(b"not sqlite")

    args = ["list", "--db", str(db), "--output", str(output)]
    if failure == "invalid_limit":
        args.extend(["--limit", "0"])
    elif failure == "locked_db":
        locker = sqlite3.connect(db, timeout=0.1)
        locker.execute("BEGIN EXCLUSIVE")
        args.extend(["--timeout", "0.01"])

    try:
        result = run(*args)
    finally:
        if locker is not None:
            locker.rollback()
            locker.close()

    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert output.read_text(encoding="utf-8") == "KEEP THIS"
