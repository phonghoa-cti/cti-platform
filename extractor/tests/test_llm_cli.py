from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "extractor" / "llm" / "run.py"
FIXTURES = REPO / "extractor" / "llm" / "fixtures"


def _run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(arg) for arg in args)],
        cwd=REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def _args(
    output: Path,
    *,
    config: str = "C3",
    response: Path | None = None,
    input_path: Path | None = None,
) -> list[object]:
    return [
        "--config",
        config,
        "--input",
        input_path or FIXTURES / "report.txt",
        "--response",
        response or FIXTURES / "c2c3-response.json",
        "--language",
        "vi",
        "--tlp",
        "TLP:AMBER",
        "--output",
        output,
    ]


@pytest.mark.parametrize("config", ["C2", "C3"])
def test_cli_runs_offline_demo_and_writes_parseable_artifact(tmp_path, config):
    output = tmp_path / f"{config.lower()}.json"

    completed = _run(*_args(output, config=config))
    artifact = json.loads(output.read_text(encoding="utf-8"))

    assert completed.returncode == 0, completed.stderr
    assert artifact["config"] == config
    assert artifact["provider"]["egress"] is False
    assert artifact["source"]["sha256"] == "71dc8cb5c1afd86d286017ab66fe01821a51c9a759d394d75dcb3767fa833475"
    assert json.loads(completed.stdout)["output"] == str(output)
    assert str(FIXTURES / "report.txt") not in completed.stdout


def test_cli_c3_marks_grounded_and_hallucinated_items(tmp_path):
    output = tmp_path / "c3.json"

    completed = _run(*_args(output))
    artifact = json.loads(output.read_text(encoding="utf-8"))
    by_value = {item["value"]: item for item in artifact["iocs"]}

    assert completed.returncode == 0
    assert by_value["evil.example"]["keep"] is True
    assert by_value["ghost.example"]["status"] == "bia"


@pytest.mark.parametrize("alias_kind", ["same", "hardlink"])
def test_cli_rejects_output_alias_without_changing_input(tmp_path, alias_kind):
    source = tmp_path / "source.txt"
    source.write_text("synthetic marker", encoding="utf-8")
    response = tmp_path / "response.json"
    response.write_text((FIXTURES / "c2c3-response.json").read_text(encoding="utf-8"), encoding="utf-8")
    output = source
    if alias_kind == "hardlink":
        output = tmp_path / "alias.json"
        try:
            os.link(source, output)
        except OSError:
            pytest.skip("filesystem không hỗ trợ hard link")

    completed = _run(*_args(output, response=response, input_path=source))

    assert completed.returncode == 1
    assert source.read_text(encoding="utf-8") == "synthetic marker"


def test_cli_error_keeps_existing_output_and_does_not_leak_raw_response(tmp_path):
    marker = "RAW_RESPONSE_SECRET_MARKER"
    response = tmp_path / "bad.json"
    response.write_text(marker, encoding="utf-8")
    output = tmp_path / "existing.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run(*_args(output, response=response))

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert marker not in completed.stdout
    assert marker not in completed.stderr
    assert "Traceback" not in completed.stderr


def test_cli_rejects_raw_response_file_over_one_mib_before_output(tmp_path):
    response = tmp_path / "oversized.json"
    response.write_text(
        (FIXTURES / "c2c3-response.json").read_text(encoding="utf-8") + " " * (1024 * 1024),
        encoding="utf-8",
    )
    output = tmp_path / "result.json"

    completed = _run(*_args(output, response=response))

    assert completed.returncode == 1
    assert not output.exists()


def test_cli_rejects_deep_json_without_traceback_or_output_change(tmp_path):
    response = tmp_path / "deep.json"
    response.write_text("[" * 1100 + "]" * 1100, encoding="utf-8")
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run(*_args(output, response=response))

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "Traceback" not in completed.stderr


def test_cli_fallback_is_deterministic_and_reports_mock_only(tmp_path):
    response = tmp_path / "invalid-sequence.json"
    response.write_text(
        json.dumps(
            {
                "provider": {"name": "scripted", "destination": "fake_offline", "egress": False},
                "responses": [
                    {"status": "completed", "model_id": "scripted-v1", "payload": {"iocs": []}},
                    {"status": "completed", "model_id": "scripted-v1", "payload": {"actors": []}},
                ],
            }
        ),
        encoding="utf-8",
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    one = _run(*_args(first, response=response))
    two = _run(*_args(second, response=response))

    assert one.returncode == two.returncode == 0
    assert first.read_bytes() == second.read_bytes()
    artifact = json.loads(first.read_text(encoding="utf-8"))
    assert artifact["result_mode"] == "regex_fallback"
    assert artifact["mock_only"] is True
