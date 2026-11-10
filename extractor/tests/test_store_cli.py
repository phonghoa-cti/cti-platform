from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from phonghoa_extractor.drafts import build_regex_draft
from phonghoa_extractor.store import get_draft, save_draft

REPO_ROOT = Path(__file__).parents[2]
DRAFT_SCRIPT = REPO_ROOT / "extractor" / "draft" / "run.py"
STORE_SCRIPT = REPO_ROOT / "extractor" / "draft" / "store.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_text_to_draft_save_and_get_across_processes(tmp_path: Path):
    text = tmp_path / "input.txt"
    draft_json = tmp_path / "draft.json"
    db = tmp_path / "drafts.sqlite"
    stored_json = tmp_path / "stored.json"
    text.write_text("😀 Báo cáo.\nContact evil[.]example and google.com.", encoding="utf-8")

    built = run(
        str(DRAFT_SCRIPT),
        "--input",
        str(text),
        "--output",
        str(draft_json),
        "--language",
        "vi",
    )
    saved = run(str(STORE_SCRIPT), "save", "--db", str(db), "--input", str(draft_json))
    save_result = json.loads(saved.stdout)
    loaded = run(
        str(STORE_SCRIPT),
        "get",
        "--db",
        str(db),
        "--id",
        str(save_result["id"]),
        "--output",
        str(stored_json),
    )

    assert built.returncode == saved.returncode == loaded.returncode == 0
    assert save_result == {"id": 1, "status": "pending"}
    original = json.loads(draft_json.read_text(encoding="utf-8"))
    stored = json.loads(stored_json.read_text(encoding="utf-8"))
    assert stored["id"] == 1
    assert stored["created_at"].endswith("+00:00")
    assert {key: value for key, value in stored.items() if key not in {"id", "created_at"}} == original
    assert "evil.example" not in saved.stdout + saved.stderr + loaded.stdout + loaded.stderr


def test_cli_input_errors_do_not_create_db_or_output(tmp_path: Path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"status": "approved"}), encoding="utf-8")
    db = tmp_path / "drafts.sqlite"
    output = tmp_path / "output.json"

    malformed_result = run(str(STORE_SCRIPT), "save", "--db", str(db), "--input", str(malformed))
    invalid_result = run(str(STORE_SCRIPT), "save", "--db", str(db), "--input", str(invalid))
    missing_get = run(str(STORE_SCRIPT), "get", "--db", str(db), "--id", "1", "--output", str(output))

    assert malformed_result.returncode != 0
    assert invalid_result.returncode != 0
    assert missing_get.returncode != 0
    assert not db.exists()
    assert not output.exists()


@pytest.mark.parametrize("field", ["language", "tlp"])
@pytest.mark.parametrize("bad_value", [[], {}, None, 42])
def test_cli_wrong_language_and_tlp_types_are_safe_and_do_not_write(tmp_path: Path, field: str, bad_value):
    marker = "Sensitive synthetic marker: evil.example"
    valid = build_regex_draft(marker, source="synthetic.txt", language="vi")
    invalid = copy.deepcopy(valid)
    invalid[field] = bad_value
    input_path = tmp_path / f"invalid-{field}.json"
    input_path.write_text(json.dumps(invalid), encoding="utf-8")
    fresh_db = tmp_path / f"fresh-{field}.sqlite"

    fresh_result = run(str(STORE_SCRIPT), "save", "--db", str(fresh_db), "--input", str(input_path))

    assert fresh_result.returncode == 1
    assert field in fresh_result.stderr
    assert "Traceback" not in fresh_result.stderr
    assert marker not in fresh_result.stdout + fresh_result.stderr
    assert not fresh_db.exists()

    existing_db = tmp_path / f"existing-{field}.sqlite"
    first_id = save_draft(existing_db, valid)
    existing_result = run(str(STORE_SCRIPT), "save", "--db", str(existing_db), "--input", str(input_path))

    assert existing_result.returncode == 1
    assert field in existing_result.stderr
    assert "Traceback" not in existing_result.stderr
    assert marker not in existing_result.stdout + existing_result.stderr
    assert get_draft(existing_db, first_id)["text"] == marker
    assert save_draft(existing_db, valid) == 2


def test_cli_get_rejects_corrupt_row_without_overwriting_existing_output(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = save_draft(db, build_regex_draft("evil.example", source="synthetic.txt", language="vi"))
    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "UPDATE drafts SET payload_json = ? WHERE id = ?",
            ('{"status":"approved","text":"tampered-local-copy"}', draft_id),
        )
        connection.commit()
    finally:
        connection.close()
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    output = tmp_path / "existing.json"
    output.write_text("KEEP THIS", encoding="utf-8")

    result = run(
        str(STORE_SCRIPT),
        "get",
        "--db",
        str(db),
        "--id",
        str(draft_id),
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "tampered-local-copy" not in result.stdout + result.stderr
    assert output.read_text(encoding="utf-8") == "KEEP THIS"
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash


@pytest.mark.parametrize("command", ["save", "get", "list"])
@pytest.mark.parametrize("timeout", ["nan", "inf", "-inf", "-1"])
def test_cli_rejects_invalid_timeout_before_database_or_output_io(tmp_path: Path, command: str, timeout: str):
    db = tmp_path / f"missing-{command}-{timeout}.sqlite"
    output = tmp_path / f"existing-{command}-{timeout}.json"
    output.write_text("KEEP THIS", encoding="utf-8")
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        json.dumps(build_regex_draft("evil.example", source="synthetic.txt", language="vi")),
        encoding="utf-8",
    )
    args = [str(STORE_SCRIPT), command, "--db", str(db), f"--timeout={timeout}"]
    if command == "save":
        args.extend(["--input", str(draft_path)])
    elif command == "get":
        args.extend(["--id", "1", "--output", str(output)])
    else:
        args.extend(["--output", str(output)])

    result = run(*args)

    assert result.returncode == 1
    assert "timeout" in result.stderr
    assert "Traceback" not in result.stderr
    assert not db.exists()
    assert output.read_text(encoding="utf-8") == "KEEP THIS"
