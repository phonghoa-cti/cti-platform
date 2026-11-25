from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from extractor.eval import run as eval_run

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
    ttp_audit: bool = False,
    attack_snapshot: Path | None = None,
    attack_pin: Path | None = None,
    query_manifest: Path | None = None,
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
    if ttp_audit:
        command.append("--ttp-audit")
    if attack_snapshot is not None:
        command.extend(["--attack-snapshot", str(attack_snapshot)])
    if attack_pin is not None:
        command.extend(["--attack-pin", str(attack_pin)])
    if query_manifest is not None:
        command.extend(["--query-manifest", str(query_manifest)])
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _write_query_manifest(path: Path, queries: dict[str, str]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "query_policy": "explicit-per-document-v1",
                "queries": queries,
            }
        ),
        encoding="utf-8",
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


def _completed_payload(payload: dict) -> dict:
    return {
        "status": "completed",
        "model_id": "scripted-v1",
        "payload": payload,
        "retryable": False,
        "error_code": None,
    }


def _write_synthetic_pin(snapshot: Path, pin: Path, *, raw: bytes | None = None) -> dict:
    value = {
        "kind": "synthetic",
        "version": "synthetic-1",
        "sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "source_url": None,
        "release_tag": None,
        "commit": None,
        "provenance": "hand-authored-test-fixture",
    }
    pin.write_bytes(raw if raw is not None else json.dumps(value).encode("utf-8"))
    return value


def _audit_cli(
    dataset: Path,
    output: Path,
    responses: Path,
    snapshot: Path,
    pin: Path,
    *,
    config: str = "C2",
) -> subprocess.CompletedProcess[str]:
    return _run_cli(
        dataset,
        output,
        config,
        responses_dir=responses,
        tlp="TLP:CLEAR",
        ttp_audit=True,
        attack_snapshot=snapshot,
        attack_pin=pin,
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


@pytest.mark.parametrize("config", ["C2", "C3"])
@pytest.mark.parametrize(
    "role",
    [[], {}, None, False, 1, "unknown"],
    ids=["list", "dict", "null", "bool", "number", "unknown-enum"],
)
def test_invalid_label_role_is_stable_and_preserves_output(tmp_path: Path, config: str, role: object):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(
        dataset,
        "case-01",
        "SOURCE_SECRET_MARKER",
        [{"type": "domain", "value": "evil.example", "role": role}],
    )
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    output = tmp_path / "result.json"
    output.write_text("keep-me", encoding="utf-8")

    completed = _run_cli(dataset, output, config, responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "keep-me"
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("config", ["C2", "C3"])
@pytest.mark.parametrize("role", ["attacker", "victim", "benign"])
def test_valid_label_roles_remain_supported(tmp_path: Path, config: str, role: str):
    dataset = tmp_path / "synthetic-smoke"
    _write_document(
        dataset,
        "case-01",
        "Synthetic document without an IOC.",
        [{"type": "domain", "value": "evil.example", "role": role}],
    )
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    output = tmp_path / "result.json"

    completed = _run_cli(dataset, output, config, responses_dir=responses, tlp="TLP:CLEAR")

    assert completed.returncode == 0, completed.stderr
    assert output.exists()


@pytest.mark.parametrize("config", ["C2", "C3"])
def test_ttp_audit_opt_in_serializes_full_provenance_without_changing_ioc_score(
    tmp_path: Path, config: str
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    source_bytes = "😀 Đoạn mô tả\r\nCafe\u0301\rEVIL[.]example".encode()
    normalized_text = "😀 Đoạn mô tả\nCafe\u0301\nEVIL[.]example"
    _write_document(
        dataset,
        "case-01",
        "placeholder",
        [{"type": "domain", "value": "evil.example", "role": "attacker"}],
    )
    source_path = dataset / "raw" / "case-01.txt"
    source_path.write_bytes(source_bytes)
    responses = tmp_path / "responses"
    payload = {
        "iocs": [_ioc("EVIL[.]example", "EVIL[.]example")],
        "techniques": [
            {"id": "T1000", "evidence": "Đoạn mô tả"},
            {"id": "T1000.001", "evidence": "Cafe\u0301"},
            {"id": "T1000", "evidence": "Đoạn mô tả"},
        ],
        "malware": [{"name": "Demo", "evidence": "Đoạn mô tả"}],
        "actors": [{"name": "Nhóm demo", "evidence": "Đoạn mô tả"}],
    }
    _write_fixture(responses, "case-01", [_completed_payload(payload)])
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    expected_pin = _write_synthetic_pin(snapshot, pin)
    baseline = tmp_path / "baseline.json"
    audited = tmp_path / "audited.json"

    without_audit = _run_cli(dataset, baseline, config, responses_dir=responses, tlp="TLP:CLEAR")
    with_audit = _audit_cli(dataset, audited, responses, snapshot, pin, config=config)

    assert without_audit.returncode == with_audit.returncode == 0, with_audit.stderr
    old_result = json.loads(baseline.read_text(encoding="utf-8"))
    result = json.loads(audited.read_text(encoding="utf-8"))
    old_document = old_result["documents"][0]
    document = result["documents"][0]
    assert old_result["schema_version"] == "1.0"
    assert "ttp_audit" not in old_result and "ttp_audit" not in old_document
    assert result["schema_version"] == "1.1"
    assert result["ttp_audit"]["catalog"] == expected_pin
    assert result["ttp_audit"]["counts"] == {
        "technique_items": 3,
        "quote_status": {"matched": 3, "missing": 0, "not_found": 0, "ambiguous": 0},
        "catalog_status": {"active": 3, "inactive": 0, "unknown": 0, "not_checked": 0},
    }
    assert [item["item_index"] for item in document["ttp_audit"]] == [0, 1, 2]
    assert document["ttp_audit"][0]["evidence_span"] == [2, 12]
    assert document["ttp_audit"][1]["evidence_span"] == [13, 18]
    assert all(item["semantic_status"] == "unverified" for item in document["ttp_audit"])
    assert all(item["operational_draft_eligible"] is False for item in document["ttp_audit"])
    assert document["score"] == old_document["score"]
    assert document["prediction"] == old_document["prediction"]
    assert document["attempts"] == old_document["attempts"] == 1
    assert document["operational_draft_eligible"] == old_document["operational_draft_eligible"]
    assert document["source"]["sha256"] == hashlib.sha256(normalized_text.encode()).hexdigest()
    assert document["source"]["sha256"] != hashlib.sha256(source_bytes).hexdigest()
    assert set(result["ttp_audit"]) == {"enabled", "catalog", "metric_note", "counts"}
    assert not ({"precision", "recall", "f1", "rate"} & set(result["ttp_audit"]))


def test_ttp_audit_loads_catalog_once_and_preserves_attempt_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    responses = tmp_path / "responses"
    for document_id in ("normal", "retry", "fallback"):
        _write_document(dataset, document_id, f"Document {document_id}.", [])
    _write_fixture(responses, "normal", [_completed([])])
    _write_fixture(
        responses,
        "retry",
        [
            {"status": "error", "retryable": True, "error_code": "temporary"},
            _completed([]),
        ],
    )
    _write_fixture(
        responses,
        "fallback",
        [
            {"status": "error", "retryable": True, "error_code": "temporary"},
            {"status": "error", "retryable": True, "error_code": "temporary"},
        ],
    )
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    output = tmp_path / "result.json"
    real_load = eval_run.load_catalog
    calls = 0

    def counted_load(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_load(*args, **kwargs)

    monkeypatch.setattr(eval_run, "load_catalog", counted_load)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUN_SCRIPT),
            "--config",
            "C2",
            "--dataset",
            str(dataset),
            "--output",
            str(output),
            "--responses-dir",
            str(responses),
            "--tlp",
            "TLP:CLEAR",
            "--ttp-audit",
            "--attack-snapshot",
            str(snapshot),
            "--attack-pin",
            str(pin),
        ],
    )

    exit_code = eval_run.main()
    result = json.loads(output.read_text(encoding="utf-8"))
    attempts = {document["id"]: document["attempts"] for document in result["documents"]}

    assert exit_code == 0
    assert calls == 1
    assert attempts == {"fallback": 2, "normal": 1, "retry": 2}
    assert next(item for item in result["documents"] if item["id"] == "fallback")["ttp_audit"] == []
    assert result["ttp_audit"]["counts"] == {
        "technique_items": 0,
        "quote_status": {"matched": 0, "missing": 0, "not_found": 0, "ambiguous": 0},
        "catalog_status": {"active": 0, "inactive": 0, "unknown": 0, "not_checked": 0},
    }


def test_ttp_audit_runtime_failure_preserves_old_output_without_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    output = tmp_path / "result.json"
    output.write_bytes(b"keep-me")

    def fail_audit(**_kwargs):
        raise eval_run.TtpAuditError("AUDIT_SECRET_MARKER")

    monkeypatch.setattr(eval_run, "audit_techniques", fail_audit)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUN_SCRIPT),
            "--config",
            "C2",
            "--dataset",
            str(dataset),
            "--output",
            str(output),
            "--responses-dir",
            str(responses),
            "--tlp",
            "TLP:CLEAR",
            "--ttp-audit",
            "--attack-snapshot",
            str(snapshot),
            "--attack-pin",
            str(pin),
        ],
    )

    exit_code = eval_run.main()
    captured = capfd.readouterr()

    assert exit_code == 1
    assert output.read_bytes() == b"keep-me"
    assert captured.err.strip() == "Lỗi: offline_eval_failed"
    assert "SOURCE_SECRET_MARKER" not in captured.err
    assert "AUDIT_SECRET_MARKER" not in captured.err


def test_attack_snapshot_hash_mismatch_preserves_output_and_inputs(tmp_path: Path) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    committed_snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    snapshot = tmp_path / "SNAPSHOT_SECRET_MARKER.json"
    snapshot.write_bytes(committed_snapshot.read_bytes())
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    snapshot.write_bytes(snapshot.read_bytes() + b" ")
    snapshot_before = snapshot.read_bytes()
    pin_before = pin.read_bytes()
    output = tmp_path / "result.json"
    output.write_bytes(b"keep-me")

    completed = _audit_cli(dataset, output, responses, snapshot, pin)

    assert completed.returncode == 1
    assert output.read_bytes() == b"keep-me"
    assert snapshot.read_bytes() == snapshot_before
    assert pin.read_bytes() == pin_before
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "SNAPSHOT_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize(
    ("audit", "snapshot", "pin"),
    [
        (True, False, False),
        (True, True, False),
        (True, False, True),
        (False, True, True),
        (False, True, False),
        (False, False, True),
    ],
)
def test_ttp_audit_requires_all_three_flags_and_c1_rejects_them(
    tmp_path: Path, audit: bool, snapshot: bool, pin: bool
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "Document.", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    snapshot_path = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin_path = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot_path, pin_path)

    c2 = _run_cli(
        dataset,
        tmp_path / "c2.json",
        "C2",
        responses_dir=responses,
        tlp="TLP:CLEAR",
        ttp_audit=audit,
        attack_snapshot=snapshot_path if snapshot else None,
        attack_pin=pin_path if pin else None,
    )
    c1 = _run_cli(
        dataset,
        tmp_path / "c1.json",
        "C1",
        ttp_audit=True,
        attack_snapshot=snapshot_path,
        attack_pin=pin_path,
    )

    assert c2.returncode == 2
    assert c1.returncode == 2
    assert not (tmp_path / "c2.json").exists()
    assert not (tmp_path / "c1.json").exists()


def test_ttp_audit_accepts_pin_at_16_kib_and_rejects_16_kib_plus_one(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "Document.", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    value = _write_synthetic_pin(snapshot, pin)
    compact = json.dumps(value, separators=(",", ":")).encode()
    pin.write_bytes(compact + b" " * (16 * 1024 - len(compact)))
    accepted = tmp_path / "accepted.json"

    valid = _audit_cli(dataset, accepted, responses, snapshot, pin)
    pin.write_bytes(compact + b" " * (16 * 1024 + 1 - len(compact)))
    rejected = tmp_path / "rejected.json"
    rejected.write_bytes(b"keep-me")
    invalid = _audit_cli(dataset, rejected, responses, snapshot, pin)

    assert valid.returncode == 0, valid.stderr
    assert invalid.returncode == 1
    assert rejected.read_bytes() == b"keep-me"
    assert "Traceback" not in invalid.stderr


@pytest.mark.parametrize(
    "case",
    ["malformed", "bom", "duplicate", "nonfinite", "deep", "extra", "missing", "wrong_type"],
)
def test_invalid_attack_pin_is_safe_and_preserves_output(tmp_path: Path, case: str) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "SOURCE_SECRET_MARKER", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "PIN_SECRET_MARKER.json"
    value = _write_synthetic_pin(snapshot, pin)
    if case == "malformed":
        raw = b"{PIN_CONTENT_SECRET_MARKER"
    elif case == "bom":
        raw = b"\xef\xbb\xbf" + json.dumps(value).encode()
    elif case == "duplicate":
        raw = json.dumps(value).replace('{"kind":', '{"kind":"synthetic","kind":').encode()
    elif case == "nonfinite":
        raw = json.dumps(value).replace('"version": "synthetic-1"', '"version": NaN').encode()
    elif case == "deep":
        raw = ("[" * 300 + "0" + "]" * 300).encode()
    else:
        changed = dict(value)
        if case == "extra":
            changed["extra"] = "no"
        elif case == "missing":
            changed.pop("commit")
        else:
            changed["version"] = False
        raw = json.dumps(changed).encode()
    pin.write_bytes(raw)
    output = tmp_path / "result.json"
    output.write_bytes(b"keep-me")

    completed = _audit_cli(dataset, output, responses, snapshot, pin)

    assert completed.returncode == 1
    assert output.read_bytes() == b"keep-me"
    assert "SOURCE_SECRET_MARKER" not in completed.stderr
    assert "PIN_CONTENT_SECRET_MARKER" not in completed.stderr
    assert "PIN_SECRET_MARKER" not in completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("protected", ["snapshot", "pin"])
@pytest.mark.parametrize("alias_kind", ["hardlink", "symlink"])
def test_ttp_audit_output_cannot_alias_snapshot_or_pin(
    tmp_path: Path, protected: str, alias_kind: str
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "Document.", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    committed_snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_bytes(committed_snapshot.read_bytes())
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    protected_path = snapshot if protected == "snapshot" else pin
    before = protected_path.read_bytes()
    output = tmp_path / "alias.json"
    try:
        if alias_kind == "hardlink":
            os.link(protected_path, output)
        else:
            output.symlink_to(protected_path)
    except OSError:
        pytest.skip(f"filesystem không hỗ trợ {alias_kind}")

    completed = _audit_cli(dataset, output, responses, snapshot, pin)

    assert completed.returncode == 1
    assert protected_path.read_bytes() == before


def test_evaluator_rejects_wrong_catalog_type_before_loading_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = tmp_path / "synthetic-smoke"
    _write_document(dataset, "case-01", "Document.", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    provider_loaded = False

    def unexpected_provider(_path: Path):
        nonlocal provider_loaded
        provider_loaded = True
        raise AssertionError("provider must not load")

    monkeypatch.setattr(eval_run, "load_scripted_provider", unexpected_provider)

    with pytest.raises(eval_run.DatasetError, match="attack catalog"):
        eval_run.evaluate_llm_dataset(
            dataset,
            responses,
            config="C2",
            tlp="TLP:CLEAR",
            attack_catalog=object(),
        )

    assert provider_loaded is False


def test_c4_cli_requires_complete_flags_and_publishes_no_clobber_artifact(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_document(dataset, "case-01", "Phishing uses evil.example.", [])
    responses = tmp_path / "responses"
    _write_fixture(
        responses,
        "case-01",
        [
            _completed_payload(
                {
                    "iocs": [_ioc("evil.example", "evil.example")],
                    "techniques": [{"id": "T1000", "evidence": "Phishing"}],
                    "malware": [],
                    "actors": [],
                }
            )
        ],
    )
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    manifest = tmp_path / "queries.json"
    _write_query_manifest(manifest, {"case-01": "phishing technique"})
    output = tmp_path / "result.json"

    completed = _run_cli(
        dataset,
        output,
        "C4",
        responses_dir=responses,
        tlp="TLP:RED",
        attack_snapshot=snapshot,
        attack_pin=pin,
        query_manifest=manifest,
    )
    assert completed.returncode == 0, completed.stderr
    original = output.read_bytes()
    repeated = _run_cli(
        dataset,
        output,
        "C4",
        responses_dir=responses,
        tlp="TLP:RED",
        attack_snapshot=snapshot,
        attack_pin=pin,
        query_manifest=manifest,
    )

    assert json.loads(original)["schema_version"] == "1.2"
    assert repeated.returncode == 1
    assert repeated.stderr == "Lỗi: offline_eval_failed\n"
    assert output.read_bytes() == original


def test_c4_flag_combinations_are_usage_errors_and_old_configs_reject_manifest(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_document(dataset, "case-01", "Phishing uses evil.example.", [])
    manifest = tmp_path / "queries.json"
    _write_query_manifest(manifest, {"case-01": "phishing technique"})

    incomplete = _run_cli(dataset, tmp_path / "c4.json", "C4", query_manifest=manifest)
    old_config = _run_cli(dataset, tmp_path / "c1.json", "C1", query_manifest=manifest)

    assert incomplete.returncode == 2
    assert old_config.returncode == 2
    assert not (tmp_path / "c4.json").exists()
    assert not (tmp_path / "c1.json").exists()


def test_c4_rejects_ttp_audit_flag_and_output_alias_to_manifest(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_document(dataset, "case-01", "Phishing uses evil.example.", [])
    responses = tmp_path / "responses"
    _write_fixture(responses, "case-01", [_completed([])])
    snapshot = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"
    pin = tmp_path / "pin.json"
    _write_synthetic_pin(snapshot, pin)
    manifest = tmp_path / "queries.json"
    _write_query_manifest(manifest, {"case-01": "phishing technique"})
    original = manifest.read_bytes()

    rejected_flag = _run_cli(
        dataset,
        tmp_path / "flag.json",
        "C4",
        responses_dir=responses,
        tlp="TLP:CLEAR",
        ttp_audit=True,
        attack_snapshot=snapshot,
        attack_pin=pin,
        query_manifest=manifest,
    )
    rejected_alias = _run_cli(
        dataset,
        manifest,
        "C4",
        responses_dir=responses,
        tlp="TLP:CLEAR",
        attack_snapshot=snapshot,
        attack_pin=pin,
        query_manifest=manifest,
    )

    assert rejected_flag.returncode == 2
    assert rejected_alias.returncode == 1
    assert rejected_alias.stderr == "Lỗi: offline_eval_failed\n"
    assert manifest.read_bytes() == original
