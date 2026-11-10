from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
RUN_SCRIPT = REPO_ROOT / "extractor" / "eval" / "run.py"


def _write_document(
    dataset: Path,
    document_id: str,
    text: str,
    iocs: list[dict[str, str]],
    *,
    language: str = "vi",
) -> None:
    raw_dir = dataset / "raw"
    labels_dir = dataset / "labels"
    raw_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{document_id}.txt").write_text(text, encoding="utf-8")
    (raw_dir / f"{document_id}.meta.json").write_text(
        json.dumps(
            {
                "id": document_id,
                "synthetic": True,
                "author": "Phong Hoa system",
                "language": language,
                "purpose": "synthetic-smoke",
            }
        ),
        encoding="utf-8",
    )
    (labels_dir / f"{document_id}.json").write_text(
        json.dumps({"id": document_id, "iocs": iocs, "ttps": []}),
        encoding="utf-8",
    )


def _run_cli(dataset: Path, output: Path, config: str = "C1") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUN_SCRIPT),
            "--config",
            config,
            "--dataset",
            str(dataset),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_reports_hand_calculated_counts_and_does_not_score_ttps(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(
        dataset,
        "case-01",
        "Kẻ tấn công dùng EVIL[.]example và victim.example; IOC bị thiếu không có trong bài.",
        [
            {"type": "domain", "value": "evil.example", "role": "attacker"},
            {"type": "domain", "value": "missing.example", "role": "attacker"},
            {"type": "domain", "value": "victim.example", "role": "victim"},
        ],
    )
    output = tmp_path / "result.json"

    completed = _run_cli(dataset, output)

    assert completed.returncode == 0, completed.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["config"] == "C1"
    assert result["purpose"] == "synthetic-smoke"
    assert result["document_count"] == 1
    assert result["micro"] == {
        "tp": 1,
        "fp": 1,
        "fn": 1,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
    assert result["by_type"]["domain"] == result["micro"]
    assert result["documents"][0]["score"] == result["micro"]
    assert result["documents"][0]["source"]["path"] == "raw/case-01.txt"
    assert len(result["documents"][0]["source"]["sha256"]) == 64
    assert result["ttp"] == {"status": "not_evaluated"}


def test_cli_accepts_empty_text_and_produces_reproducible_content(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "empty", "", [])
    first_output = tmp_path / "first.json"
    second_output = tmp_path / "second.json"

    first = _run_cli(dataset, first_output)
    second = _run_cli(dataset, second_output)

    assert first.returncode == second.returncode == 0
    assert first_output.read_bytes() == second_output.read_bytes()
    result = json.loads(first_output.read_text(encoding="utf-8"))
    assert result["micro"]["tp"] == result["micro"]["fp"] == result["micro"]["fn"] == 0
    assert result["documents"][0]["prediction"]["iocs"] == []


def test_cli_rejects_missing_label_with_named_file_and_writes_no_result(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "missing-label", "evil.example", [])
    missing_label = dataset / "labels" / "missing-label.json"
    missing_label.unlink()
    output = tmp_path / "result.json"

    completed = _run_cli(dataset, output)

    assert completed.returncode != 0
    assert "missing-label.json" in completed.stderr
    assert not output.exists()


def test_cli_rejects_malformed_metadata_with_named_file(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "broken", "evil.example", [])
    metadata = dataset / "raw" / "broken.meta.json"
    metadata.write_text("{not-json", encoding="utf-8")

    completed = _run_cli(dataset, tmp_path / "result.json")

    assert completed.returncode != 0
    assert "broken.meta.json" in completed.stderr


def test_cli_rejects_label_without_source_with_named_file(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "orphan", "evil.example", [])
    (dataset / "raw" / "orphan.txt").unlink()

    completed = _run_cli(dataset, tmp_path / "result.json")

    assert completed.returncode != 0
    assert "orphan.json" in completed.stderr


def test_cli_rejects_metadata_without_source_with_named_file(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "orphan", "evil.example", [])
    (dataset / "raw" / "orphan.txt").unlink()
    (dataset / "labels" / "orphan.json").unlink()

    completed = _run_cli(dataset, tmp_path / "result.json")

    assert completed.returncode != 0
    assert "orphan.meta.json" in completed.stderr


def test_cli_rejects_empty_dataset_and_unsupported_config(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    (dataset / "raw").mkdir(parents=True)
    (dataset / "labels").mkdir()

    empty = _run_cli(dataset, tmp_path / "empty.json")
    unsupported = _run_cli(dataset, tmp_path / "c2.json", config="C2")

    assert empty.returncode != 0
    assert "không có báo cáo" in empty.stderr.lower()
    assert unsupported.returncode != 0
    assert "C2" in unsupported.stderr
    assert not (tmp_path / "empty.json").exists()
    assert not (tmp_path / "c2.json").exists()
