from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def _run_cli(
    dataset: Path,
    output: Path,
    config: str = "C1",
    *,
    responses_dir: Path | None = None,
    tlp: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(RUN_SCRIPT),
        "--config",
        config,
        "--dataset",
        str(dataset),
        "--output",
        str(output),
    ]
    if responses_dir is not None:
        command.extend(["--responses-dir", str(responses_dir)])
    if tlp is not None:
        command.extend(["--tlp", tlp])
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _payload(iocs: list[dict[str, str]]) -> dict:
    return {"iocs": iocs, "techniques": [], "malware": [], "actors": []}


def _ioc(value: str, evidence: str, *, ioc_type: str = "domain") -> dict[str, str]:
    return {"type": ioc_type, "value": value, "role": "attacker", "evidence": evidence}


def _write_fixture(
    responses_dir: Path,
    document_id: str,
    responses: list[dict],
    *,
    destination: object = "fake_offline",
    egress: object = False,
) -> Path:
    responses_dir.mkdir(parents=True, exist_ok=True)
    path = responses_dir / f"{document_id}.json"
    path.write_text(
        json.dumps(
            {
                "provider": {"name": "scripted", "destination": destination, "egress": egress},
                "responses": responses,
            }
        ),
        encoding="utf-8",
    )
    return path


def _completed(iocs: list[dict[str, str]]) -> dict:
    return {
        "status": "completed",
        "model_id": "scripted-v1",
        "payload": _payload(iocs),
        "retryable": False,
        "error_code": None,
    }


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
    unsupported = _run_cli(dataset, tmp_path / "c4.json", config="C4")

    assert empty.returncode != 0
    assert "không có báo cáo" in empty.stderr.lower()
    assert unsupported.returncode != 0
    assert "C4" in unsupported.stderr
    assert not (tmp_path / "empty.json").exists()
    assert not (tmp_path / "c4.json").exists()


def test_c2_scores_raw_duplicate_hallucinated_and_invalid_iocs(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    text = "Máy thử gọi EVIL[.]example."
    _write_document(
        dataset,
        "case-01",
        text,
        [{"type": "domain", "value": "evil.example", "role": "attacker"}],
    )
    responses = tmp_path / "responses"
    _write_fixture(
        responses,
        "case-01",
        [
            _completed(
                [
                    _ioc("EVIL[.]example", text),
                    _ioc("evil.example", text),
                    _ioc("ghost.example", "IOC bịa ghost.example"),
                    _ioc("not an ioc", "giá trị sai nhưng schema hợp lệ"),
                ]
            )
        ],
    )
    output = tmp_path / "c2.json"

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")
    result = json.loads(output.read_text(encoding="utf-8"))
    document = result["documents"][0]

    assert completed.returncode == 0, completed.stderr
    assert document["prediction"]["values"] == [
        "EVIL[.]example",
        "evil.example",
        "ghost.example",
        "not an ioc",
    ]
    assert document["score"]["tp"] == 1
    assert document["score"]["fp"] == 2
    assert result["by_type"]["domain"]["fp"] == 1
    assert result["by_type"]["invalid"]["fp"] == 1
    assert document["result_mode"] == "model_completed"
    assert document["model_items_used"] is True
    assert document["operational_draft_eligible"] is False


def test_c3_scores_only_kept_iocs_and_preserves_grounding_audit(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    text = "Máy thử gọi EVIL[.]example."
    _write_document(
        dataset,
        "case-01",
        text,
        [{"type": "domain", "value": "evil.example", "role": "attacker"}],
    )
    responses = tmp_path / "responses"
    _write_fixture(
        responses,
        "case-01",
        [_completed([_ioc("evil.example", text), _ioc("ghost.example", "IOC bịa ghost.example")])],
    )
    output = tmp_path / "c3.json"

    completed = _run_cli(dataset, output, "C3", responses_dir=responses, tlp="TLP:CLEAR")
    result = json.loads(output.read_text(encoding="utf-8"))
    document = result["documents"][0]
    audit = {item["value"]: item for item in document["grounding_audit"]}

    assert completed.returncode == 0, completed.stderr
    assert document["prediction"]["values"] == ["evil.example"]
    assert document["score"]["fp"] == 0
    assert audit["evil.example"]["keep"] is True
    assert audit["evil.example"]["span"] == [0, len(text)]
    assert audit["ghost.example"]["keep"] is False
    assert audit["ghost.example"]["status"] == "bia"
    assert audit["ghost.example"]["warning"]
    assert document["prediction_basis"] == "adapter_grounded_model_plus_regex"
    assert any("regex" in item.lower() for item in result["limitations"])


def test_retryable_failures_form_separate_regex_fallback_group(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(
        dataset,
        "case-01",
        "Kết nối evil.example.",
        [{"type": "domain", "value": "evil.example", "role": "attacker"}],
    )
    responses = tmp_path / "responses"
    _write_fixture(
        responses,
        "case-01",
        [
            {"status": "error", "retryable": True, "error_code": "temporary"},
            {"status": "completed", "model_id": "scripted-v1", "payload": {"iocs": []}},
        ],
    )
    output = tmp_path / "fallback.json"

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")
    result = json.loads(output.read_text(encoding="utf-8"))
    document = result["documents"][0]

    assert completed.returncode == 0, completed.stderr
    assert document["result_mode"] == "regex_fallback"
    assert document["model_items_used"] is False
    assert document["error_codes"] == ["provider_error", "invalid_response"]
    assert result["micro_by_result_mode"]["regex_fallback"]["tp"] == 1
    assert result["micro_by_result_mode"]["model_completed"] == {"status": "not_available"}


@pytest.mark.parametrize(
    "response",
    [
        {"status": "refusal", "error_code": "RAW_SECRET_MARKER"},
        {"status": "incomplete", "error_code": "RAW_SECRET_MARKER"},
        {"status": "error", "error_code": "RAW_SECRET_MARKER", "retryable": False},
    ],
)
def test_nonretryable_provider_result_stops_run_and_preserves_output(tmp_path: Path, response):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [response])
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "RAW_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr


def test_fixture_set_must_match_documents_before_output_changes(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "evil.example", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "extra", [_completed([])])
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("fixture_kind", ["malformed", "unsafe_provider"])
def test_malformed_or_unsafe_fixture_preserves_output_without_leak(tmp_path: Path, fixture_kind: str):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [])
    responses = tmp_path / "responses"
    if fixture_kind == "malformed":
        responses.mkdir()
        (responses / "case-01.json").write_text("RAW_FIXTURE_SECRET_MARKER", encoding="utf-8")
    else:
        _write_fixture(
            responses,
            "case-01",
            [_completed([])],
            destination="cloud",
            egress=False,
        )
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "RAW_FIXTURE_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("output_kind", ["inside_dataset", "hardlink"])
def test_output_cannot_target_dataset_or_alias_an_input(tmp_path: Path, output_kind: str):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "evil.example", [])
    responses = tmp_path / "responses"
    fixture = _write_fixture(responses, "case-01", [_completed([])])
    fixture_before = fixture.read_bytes()
    output = dataset / "result.json"
    if output_kind == "hardlink":
        output = tmp_path / "alias.json"
        try:
            os.link(fixture, output)
        except OSError:
            pytest.skip("filesystem không hỗ trợ hard link")

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert fixture.read_bytes() == fixture_before


def test_c2_output_is_deterministic_and_contains_provenance(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "evil.example", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    one = _run_cli(dataset, first, "C2", responses_dir=responses, tlp="TLP:CLEAR")
    two = _run_cli(dataset, second, "C2", responses_dir=responses, tlp="TLP:CLEAR")
    result = json.loads(first.read_text(encoding="utf-8"))
    document = result["documents"][0]

    assert one.returncode == two.returncode == 0
    assert first.read_bytes() == second.read_bytes()
    assert len(result["dataset_sha256"]) == len(result["fixture_manifest_sha256"]) == 64
    assert len(document["source"]["sha256"]) == len(document["fixture"]["sha256"]) == 64
    assert result["provider_policy"] == {"destination": "fake_offline", "egress": False}
    assert result["mock_only"] is True
    assert result["evaluator"]["git_ref"]
    assert result["evaluator"]["python"]
    assert document["score"] == {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


def test_c2_requires_flags_and_c1_rejects_them(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "", [])

    c2 = _run_cli(dataset, tmp_path / "c2.json", "C2")
    c1 = _run_cli(
        dataset,
        tmp_path / "c1.json",
        "C1",
        responses_dir=tmp_path / "responses",
        tlp="TLP:CLEAR",
    )

    assert c2.returncode != 0
    assert c1.returncode != 0
    assert not (tmp_path / "c2.json").exists()
    assert not (tmp_path / "c1.json").exists()


def test_invalid_metadata_language_is_stable_and_preserves_output(tmp_path: Path):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [], language="vi")
    metadata = dataset / "raw" / "case-01.meta.json"
    value = json.loads(metadata.read_text(encoding="utf-8"))
    value["language"] = []
    metadata.write_text(json.dumps(value), encoding="utf-8")
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run_cli(dataset, output, "C2", responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr
