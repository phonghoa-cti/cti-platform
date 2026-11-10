from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
RUN_SCRIPT = REPO_ROOT / "extractor" / "draft" / "run.py"


def run_cli(input_path: Path, output_path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUN_SCRIPT),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--language",
            "vi",
            *extra,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_writes_pending_json_from_utf8_text(tmp_path: Path):
    input_path = tmp_path / "bao-cao.txt"
    output_path = tmp_path / "nested" / "draft.json"
    input_path.write_text("Phát hiện evil[.]example.", encoding="utf-8")

    completed = run_cli(input_path, output_path)

    assert completed.returncode == 0, completed.stderr
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "pending"
    assert result["source"]["name"] == "bao-cao.txt"
    assert result["tlp"] == "TLP:AMBER"
    assert result["items"][0]["evidence"] == "Phát hiện evil[.]example."


def test_cli_accepts_empty_input_and_writes_empty_pending_draft(tmp_path: Path):
    input_path = tmp_path / "empty.txt"
    output_path = tmp_path / "draft.json"
    input_path.write_text("", encoding="utf-8")

    completed = run_cli(input_path, output_path)

    assert completed.returncode == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["items"] == []


def test_cli_rejects_missing_input_and_does_not_write_output(tmp_path: Path):
    output_path = tmp_path / "draft.json"

    completed = run_cli(tmp_path / "missing.txt", output_path)

    assert completed.returncode != 0
    assert "missing.txt" in completed.stderr
    assert not output_path.exists()


def test_cli_rejects_non_txt_input_and_unknown_tlp(tmp_path: Path):
    markdown = tmp_path / "report.md"
    markdown.write_text("evil.example", encoding="utf-8")
    md_output = tmp_path / "md.json"
    tlp_output = tmp_path / "tlp.json"

    wrong_suffix = run_cli(markdown, md_output)
    wrong_tlp = run_cli(markdown.with_suffix(".txt"), tlp_output, "--tlp", "TLP:BLUE")

    assert wrong_suffix.returncode != 0
    assert "txt" in wrong_suffix.stderr.lower()
    assert wrong_tlp.returncode != 0
    assert "TLP" in wrong_tlp.stderr
    assert not md_output.exists()
    assert not tlp_output.exists()
