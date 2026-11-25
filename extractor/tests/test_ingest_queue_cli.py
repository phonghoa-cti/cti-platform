from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from test_ingest_queue import make_envelope

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "extractor" / "ingest_queue" / "run.py"


def run_cli(*arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(value) for value in arguments)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )


def write_envelope(path: Path) -> None:
    path.write_text(json.dumps(make_envelope(), ensure_ascii=False, indent=2), encoding="utf-8")


def test_cli_import_then_duplicate_has_exact_safe_json_output(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = tmp_path / "envelope.json"
    write_envelope(envelope)

    imported = run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-1")
    duplicate = run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-1")

    assert imported.returncode == duplicate.returncode == 0
    assert imported.stderr == duplicate.stderr == ""
    assert json.loads(imported.stdout) == {"draft_id": 2, "result": "imported"}
    assert json.loads(duplicate.stdout) == {"draft_id": 2, "result": "duplicate"}
    assert imported.stdout.count("\n") == duplicate.stdout.count("\n") == 1


def test_cli_creator_is_validated_before_envelope_read(tmp_path: Path):
    result = run_cli(
        "import",
        "--envelope",
        tmp_path / "missing-secret-name.json",
        "--db",
        tmp_path / "missing.sqlite",
        "--created-by-subject",
        " ",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Lỗi: invalid_created_by_subject\n"
    assert str(tmp_path) not in result.stderr


@pytest.mark.parametrize("control", ["\x85", "\x9f"])
def test_cli_rejects_control_characters_without_database_mutation(tmp_path: Path, control: str):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope_value = make_envelope()
    invalid_name = f"bao{control}cao.txt"
    envelope_value["input"]["display_name"] = invalid_name
    envelope_value["draft"]["source"]["name"] = invalid_name
    envelope = tmp_path / "envelope.json"
    envelope.write_text(json.dumps(envelope_value, ensure_ascii=False), encoding="utf-8")
    before = db.read_bytes()

    result = run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-1")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Lỗi: invalid_input_metadata\n"
    assert db.read_bytes() == before


def test_cli_argument_errors_and_help_are_closed(tmp_path: Path):
    invalid = run_cli("import", "--timeout", "NaN")
    help_result = run_cli("--help")

    assert invalid.returncode == 2
    assert invalid.stdout == ""
    assert invalid.stderr == "Lỗi: invalid_arguments\n"
    assert help_result.returncode == 0
    assert "usage:" in help_result.stdout.lower()
    assert help_result.stderr == ""


def test_cli_other_creator_conflict_never_discloses_draft_id(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = tmp_path / "envelope.json"
    write_envelope(envelope)
    assert (
        run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-1").returncode
        == 0
    )

    conflict = run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-2")

    assert conflict.returncode == 1
    assert conflict.stdout == ""
    assert conflict.stderr == "Lỗi: duplicate_creator_conflict\n"
    assert "2" not in conflict.stderr


def test_cli_rejects_same_envelope_and_database_path(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))

    result = run_cli("import", "--envelope", db, "--db", db, "--created-by-subject", "creator-1")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Lỗi: envelope_read_failed\n"
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == 1


def test_two_cli_processes_race_to_one_import_and_one_duplicate(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = tmp_path / "envelope.json"
    write_envelope(envelope)
    barrier = threading.Barrier(2)

    def invoke():
        barrier.wait()
        return run_cli("import", "--envelope", envelope, "--db", db, "--created-by-subject", "creator-1")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _value: invoke(), range(2)))

    assert [result.returncode for result in results] == [0, 0]
    assert sorted(json.loads(result.stdout)["result"] for result in results) == [
        "duplicate",
        "imported",
    ]
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM draft_ingest_provenance").fetchone()[0] == 1
