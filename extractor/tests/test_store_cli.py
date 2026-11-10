from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
