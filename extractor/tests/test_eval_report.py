from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from extractor.eval import report as report_module

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "extractor" / "eval" / "report.py"
LOWER_HASH = "a" * 64
GIT_REF = "b" * 40
LIMITATIONS_10 = [
    "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
    "C3 adapter merges model candidates with regex extraction before grounding; scores are not model-only.",
    "Semantic TTP, malware, and actor items are not evaluated.",
]
LIMITATIONS_11 = LIMITATIONS_10 + [
    "TTP audit reports source, quote, and catalog consistency only; semantic TTP and C4 remain unverified."
]
LIMITATIONS_12 = [
    "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
    "C4 adapter merges model candidates with regex extraction before grounding; scores are not model-only.",
    "Semantic TTP, malware, and actor items are not evaluated.",
    "Retrieval completion and context transmission do not prove model knowledge use or quality.",
    "TTP audit reports source, quote, and catalog consistency only; semantic TTP remains unverified.",
]
TTP_COUNT_PATHS = [
    ("technique_items",),
    *(("quote_status", status) for status in ("matched", "missing", "not_found", "ambiguous")),
    *(("catalog_status", status) for status in ("active", "inactive", "unknown", "not_checked")),
]


def score(tp: int = 1, fp: int = 0, fn: int = 0) -> dict[str, int | float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def c1_artifact() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "config": "C1",
        "purpose": "synthetic-smoke",
        "dataset_sha256": LOWER_HASH,
        "document_count": 1,
        "documents": [
            {
                "id": "doc-1",
                "language": "vi",
                "prediction": {"values": ["198.51.100.2"]},
                "score": score(),
                "source": {"path": "doc-1.txt", "sha256": LOWER_HASH},
            }
        ],
        "micro": score(),
        "by_type": {"ipv4": score()},
        "ttp": {"status": "not_evaluated"},
    }


def audit_item(config: str) -> dict[str, object]:
    return {
        "item_index": 0,
        "kind": "technique",
        "value": "T1566.002",
        "evidence": "quoted evidence",
        "evidence_span": [0, 15],
        "source_sha256": LOWER_HASH,
        "config": config,
        "quote_status": "matched",
        "catalog_status": "active",
        "reason_code": "ok",
        "pin_kind": "synthetic",
        "snapshot_version": "synthetic-1",
        "snapshot_sha256": LOWER_HASH,
        "semantic_status": "unverified",
        "operational_draft_eligible": False,
    }


def c23_artifact(config: str, *, schema: str = "1.0", fallback: bool = False) -> dict[str, object]:
    mode = "regex_fallback" if fallback else "model_completed"
    document: dict[str, object] = {
        "id": "doc-1",
        "config": config,
        "language": "vi",
        "tlp": "TLP:CLEAR",
        "source": {"path": "doc-1.txt", "sha256": LOWER_HASH},
        "fixture": {"path": "doc-1.json", "sha256": LOWER_HASH},
        "adapter_schema_version": "1.0",
        "provider": {
            "name": "scripted",
            "model_id": "unavailable" if fallback else "scripted-v1",
            "destination": "fake_offline",
            "egress": False,
        },
        "attempts": 1,
        "result_mode": mode,
        "error_codes": [],
        "model_items_used": not fallback,
        "operational_draft_eligible": False,
        "prediction_basis": "regex_fallback"
        if fallback
        else ("adapter_raw_model" if config == "C2" else "adapter_grounded_model_plus_regex"),
        "prediction": {"values": ["198.51.100.2"]},
        "score": score(),
        "raw_audit" if config == "C2" else "grounding_audit": [],
    }
    result: dict[str, object] = {
        "schema_version": schema,
        "config": config,
        "purpose": "synthetic-smoke",
        "dataset_sha256": LOWER_HASH,
        "fixture_manifest_sha256": LOWER_HASH,
        "provider_policy": {"destination": "fake_offline", "egress": False},
        "mock_only": True,
        "evaluator": {"git_ref": GIT_REF, "python": "3.12.13"},
        "document_count": 1,
        "documents": [document],
        "micro_all": score(),
        "micro_by_result_mode": {
            "model_completed": {"status": "not_available"} if fallback else score(),
            "regex_fallback": score() if fallback else {"status": "not_available"},
        },
        "by_type": {"ipv4": score()},
        "limitations": list(LIMITATIONS_10),
    }
    if schema == "1.1":
        document["ttp_audit"] = [audit_item(config)]
        result["limitations"] = list(LIMITATIONS_11)
        result["ttp_audit"] = {
            "enabled": True,
            "catalog": {
                "kind": "synthetic",
                "version": "synthetic-1",
                "sha256": LOWER_HASH,
                "source_url": None,
                "release_tag": None,
                "commit": None,
                "provenance": "hand-authored-test-fixture",
            },
            "metric_note": "counts only; not TTP precision, recall, F1, or detection rate",
            "counts": {
                "technique_items": 1,
                "quote_status": {"matched": 1, "missing": 0, "not_found": 0, "ambiguous": 0},
                "catalog_status": {"active": 1, "inactive": 0, "unknown": 0, "not_checked": 0},
            },
        }
    return result


def c4_artifact(*, fallback: bool = False) -> dict[str, object]:
    result = c23_artifact("C3", schema="1.1", fallback=fallback)
    result["schema_version"] = "1.2"
    result["config"] = "C4"
    result["query_manifest_sha256"] = "c" * 64
    result["limitations"] = list(LIMITATIONS_12)
    document = result["documents"][0]  # type: ignore[index]
    document["config"] = "C4"
    document["operational_draft_eligible"] = True
    document["prediction_basis"] = "regex_fallback" if fallback else "adapter_grounded_model_plus_regex"
    document["attack_context"] = {
        "requested": True,
        "retrieval_completed": True,
        "provider_context_sent": True,
        "c4_adapter_completed": not fallback,
        "schema_version": "1.0",
        "sha256": "d" * 64,
        "byte_length": 512,
        "top_k": 5,
        "budget_bytes": 4096,
        "snapshot": {
            "version": "synthetic-1",
            "sha256": LOWER_HASH,
            "kind": "synthetic",
            "source_url": None,
            "release_tag": None,
            "commit": None,
        },
    }
    for item in document["ttp_audit"]:
        item["config"] = "C4"
    return result


def write_json(path: Path, value: object) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)
    return raw


def run_report(
    tmp_path: Path, artifacts: list[dict[str, object]], *extra: str
) -> tuple[subprocess.CompletedProcess[str], Path, list[Path]]:
    paths = []
    for index, artifact in enumerate(artifacts):
        path = tmp_path / f"input-{index}.json"
        write_json(path, artifact)
        paths.append(path)
    output = tmp_path / "nested" / "report.md"
    command = [sys.executable, str(SCRIPT)]
    for path in paths:
        command.extend(("--input", str(path)))
    command.extend(("--output", str(output), *extra))
    return subprocess.run(command, text=True, encoding="utf-8", capture_output=True), output, paths


def test_renders_c1_without_document_config_and_hashes_exact_input_bytes(tmp_path: Path):
    result, output, paths = run_report(tmp_path, [c1_artifact()])

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert json.loads(result.stdout) == {"configs": ["C1"], "output": str(output)}
    report = output.read_text(encoding="utf-8")
    assert report.startswith("# Báo cáo đánh giá X01\n\n> **SYNTHETIC SMOKE")
    assert hashlib.sha256(paths[0].read_bytes()).hexdigest() in report
    assert "| C1 | 1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |" in report
    assert "không có trong schema C1" in report


def test_renders_c1_c2_c3_schema_10_in_config_order_independent_of_input_order(tmp_path: Path):
    artifacts = [c23_artifact("C3"), c1_artifact(), c23_artifact("C2", fallback=True)]
    result, output, _ = run_report(tmp_path, artifacts)

    assert result.returncode == 0, result.stderr
    report = output.read_text(encoding="utf-8")
    assert report.index("| C1 |") < report.index("| C2 |") < report.index("| C3 |")
    assert "grounded model candidates + regex; not model-only" in report
    assert "| C2 | regex_fallback | 1 | 0 | 0 |" in report


def test_renders_schema_11_ttp_counts_and_official_catalog_metadata(tmp_path: Path):
    c2, c3 = c23_artifact("C2", schema="1.1"), c23_artifact("C3", schema="1.1")
    for artifact in (c2, c3):
        catalog = artifact["ttp_audit"]["catalog"]  # type: ignore[index]
        catalog.update(
            {"kind": "official", "version": "v20.1", "release_tag": "ATTACK-v20.1", "commit": GIT_REF}
        )
    result, output, _ = run_report(tmp_path, [c3, c2])

    assert result.returncode == 0, result.stderr
    report = output.read_text(encoding="utf-8")
    assert "TTP consistency counts" in report
    assert "`official` / `v20.1`" in report
    assert "không phải Precision/Recall/F1 hay semantic truth" in report


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a.update(document_count=2),
        lambda a: a["micro"].update(tp=2),
        lambda a: a["micro"].update(precision=0.5),
        lambda a: a["documents"][0].update(config="C1"),
        lambda a: a["by_type"].update(hostname=score()),
        lambda a: a.update(dataset_sha256="A" * 64),
    ],
)
def test_rejects_c1_projection_and_metric_invariant_breaks(tmp_path: Path, mutate):
    artifact = c1_artifact()
    mutate(artifact)
    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert result.stdout == ""
    assert not output.exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a["documents"][0].update(config="C3"),
        lambda a: a["micro_by_result_mode"].update(model_completed={"status": "not_available"}),
        lambda a: a["micro_by_result_mode"].update(regex_fallback=score()),
        lambda a: a["provider_policy"].update(egress=0),
        lambda a: a.update(mock_only=1),
        lambda a: a["documents"][0].update(attempts=True),
    ],
)
def test_rejects_c23_projection_mode_and_bool_int_confusion(tmp_path: Path, mutate):
    artifact = c23_artifact("C2")
    mutate(artifact)
    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert not output.exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a["ttp_audit"]["counts"].update(technique_items=2),
        lambda a: a["ttp_audit"]["counts"]["quote_status"].update(matched=0),
        lambda a: a["documents"][0]["ttp_audit"][0].update(semantic_status="verified"),
        lambda a: a["documents"][0]["ttp_audit"][0].update(operational_draft_eligible=True),
        lambda a: a["ttp_audit"]["catalog"].update(version="[x](https://bad.invalid)"),
    ],
)
def test_rejects_ttp_count_projection_and_markdown_grammar_breaks(tmp_path: Path, mutate):
    artifact = c23_artifact("C2", schema="1.1")
    mutate(artifact)
    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert not output.exists()


@pytest.mark.parametrize("count_path", TTP_COUNT_PATHS, ids=lambda path: ".".join(path))
@pytest.mark.parametrize("wrong_type", (bool, float), ids=("bool", "float"))
def test_rejects_equivalent_noninteger_ttp_counts_before_any_publish(
    tmp_path: Path, count_path: tuple[str, ...], wrong_type: type
):
    artifact = c23_artifact("C2", schema="1.1")
    counts = artifact["ttp_audit"]["counts"]  # type: ignore[index]
    target = counts
    for key in count_path[:-1]:
        target = target[key]
    target[count_path[-1]] = wrong_type(target[count_path[-1]])
    input_path = tmp_path / "invalid.json"
    original_input = write_json(input_path, artifact)

    new_output = tmp_path / "new-parent" / "report.md"
    new_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(new_output)],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    old_output = tmp_path / "old.md"
    old_output.write_bytes(b"sentinel")
    overwrite_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(input_path),
            "--output",
            str(old_output),
            "--overwrite",
        ],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert (new_result.returncode, new_result.stdout, new_result.stderr) == (
        2,
        "",
        "Lỗi: eval_report_invalid_input\n",
    )
    assert not new_output.parent.exists()
    assert (overwrite_result.returncode, overwrite_result.stdout, overwrite_result.stderr) == (
        2,
        "",
        "Lỗi: eval_report_invalid_input\n",
    )
    assert old_output.read_bytes() == b"sentinel"
    assert input_path.read_bytes() == original_input


def test_rejects_mixed_schema_duplicate_config_and_cohort_mismatch(tmp_path: Path):
    cases = [
        [c23_artifact("C2"), c23_artifact("C3", schema="1.1")],
        [c23_artifact("C2"), c23_artifact("C2")],
        [c23_artifact("C2"), {**c23_artifact("C3"), "dataset_sha256": "c" * 64}],
        [c1_artifact(), c23_artifact("C2", schema="1.1")],
    ]
    for index, artifacts in enumerate(cases):
        case = tmp_path / str(index)
        case.mkdir()
        result, output, _ = run_report(case, artifacts)
        assert result.returncode == 2
        assert result.stderr == "Lỗi: eval_report_invalid_input\n"
        assert not output.exists()


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":"1.0","schema_version":"1.0"}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":92233720368547758070}',
        b"\xef\xbb\xbf{}",
        b"{" + b'"x":' * 65 + b"0" + b"}" * 65,
    ],
)
def test_rejects_unsafe_json_before_creating_output_parent(tmp_path: Path, raw: bytes):
    input_path = tmp_path / "bad.json"
    input_path.write_bytes(raw)
    output = tmp_path / "never" / "report.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output)],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert not output.parent.exists()


def test_missing_input_and_argparse_errors_are_generic_and_do_not_echo_operand(tmp_path: Path):
    secret_operand = tmp_path / "secret-name.json"
    missing = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(secret_operand), "--output", str(tmp_path / "out.md")],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    bad_flag = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", "do-not-echo", "--out", "also-secret"],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert (missing.returncode, missing.stderr) == (1, "Lỗi: eval_report_io_failed\n")
    assert "secret" not in missing.stderr
    assert (bad_flag.returncode, bad_flag.stderr) == (2, "Lỗi: eval_report_invalid_input\n")
    assert "do-not-echo" not in bad_flag.stderr


def test_no_overwrite_preserves_old_output_and_overwrite_replaces_it(tmp_path: Path):
    result, output, _ = run_report(tmp_path, [c1_artifact()])
    assert result.returncode == 0
    first = output.read_bytes()

    again, _, _ = run_report(tmp_path, [c1_artifact()])
    assert again.returncode == 2
    assert output.read_bytes() == first
    overwrite, _, _ = run_report(tmp_path, [c1_artifact()], "--overwrite")
    assert overwrite.returncode == 0
    assert output.read_bytes() == first


def test_rejects_output_alias_but_allows_different_sibling(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    original = write_json(artifact, c1_artifact())
    alias = tmp_path / "alias.md"
    try:
        os.link(artifact, alias)
    except OSError as error:
        pytest.skip(f"hardlink unavailable: {error}")
    rejected = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(artifact), "--output", str(alias), "--overwrite"],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    sibling = tmp_path / "sibling.md"
    accepted = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(artifact), "--output", str(sibling)],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert rejected.returncode == 2
    assert artifact.read_bytes() == original
    assert accepted.returncode == 0, accepted.stderr


def test_input_order_and_rerun_with_overwrite_are_byte_identical_and_inputs_unchanged(tmp_path: Path):
    artifacts = [c1_artifact(), c23_artifact("C2"), c23_artifact("C3")]
    result, output, paths = run_report(tmp_path, artifacts)
    assert result.returncode == 0, result.stderr
    before_report = output.read_bytes()
    before_inputs = [path.read_bytes() for path in paths]

    reversed_dir = tmp_path / "reversed"
    reversed_dir.mkdir()
    reversed_result, reversed_output, reversed_paths = run_report(reversed_dir, list(reversed(artifacts)))

    assert reversed_result.returncode == 0, reversed_result.stderr
    assert reversed_output.read_bytes() == before_report
    assert [path.read_bytes() for path in paths] == before_inputs
    assert [json.loads(path.read_bytes()) for path in reversed_paths] == list(reversed(artifacts))


def test_help_is_successful():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], text=True, encoding="utf-8", capture_output=True
    )
    assert result.returncode == 0
    assert "--input" in result.stdout


def test_accepts_zero_denominator_metrics(tmp_path: Path):
    artifact = c1_artifact()
    artifact["documents"][0]["score"] = score(0, 0, 0)  # type: ignore[index]
    artifact["micro"] = score(0, 0, 0)
    artifact["by_type"] = {}

    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 0, result.stderr
    assert "| C1 | 1 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |" in output.read_text(encoding="utf-8")


def test_non_rendered_payload_markdown_is_not_emitted(tmp_path: Path):
    artifact = c23_artifact("C2")
    attack = "![x](https://bad.invalid)<img src=x>&entity;`code`|pipe\nnext"
    artifact["documents"][0]["raw_audit"] = [{"value": attack}]  # type: ignore[index]

    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 0, result.stderr
    assert attack not in output.read_text(encoding="utf-8")


def test_rejects_file_larger_than_one_mib_without_output_parent(tmp_path: Path):
    input_path = tmp_path / "large.json"
    input_path.write_bytes(b" " * (1_048_576 + 1))
    output = tmp_path / "never" / "report.md"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output)],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert (result.returncode, result.stderr) == (2, "Lỗi: eval_report_invalid_input\n")
    assert not output.parent.exists()


def test_no_clobber_race_preserves_competing_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "input.json"
    write_json(input_path, c1_artifact())
    loaded = report_module._validate_cohort([report_module._read_artifact(str(input_path))])
    output = tmp_path / "report.md"

    def competing_link(source: Path, destination: Path) -> None:
        destination.write_bytes(b"competitor")
        raise FileExistsError

    monkeypatch.setattr(report_module.os, "link", competing_link)
    with pytest.raises(report_module.InvalidInput):
        report_module._publish(str(output), b"ours", loaded, overwrite=False)

    assert output.read_bytes() == b"competitor"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_publish_io_failure_before_commit_leaves_no_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "input.json"
    write_json(input_path, c1_artifact())
    loaded = report_module._validate_cohort([report_module._read_artifact(str(input_path))])
    output = tmp_path / "report.md"

    def failed_link(source: Path, destination: Path) -> None:
        raise OSError("synthetic publish failure")

    monkeypatch.setattr(report_module.os, "link", failed_link)
    with pytest.raises(report_module.InputIoError):
        report_module._publish(str(output), b"ours", loaded, overwrite=False)

    assert not output.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def test_cleanup_failure_after_commit_keeps_published_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "input.json"
    write_json(input_path, c1_artifact())
    loaded = report_module._validate_cohort([report_module._read_artifact(str(input_path))])
    output = tmp_path / "report.md"
    real_unlink = Path.unlink

    def failed_temp_unlink(path: Path, *args, **kwargs) -> None:
        if path.suffix == ".tmp":
            raise OSError("synthetic cleanup failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failed_temp_unlink)
    with pytest.raises(report_module.InputIoError):
        report_module._publish(str(output), b"committed", loaded, overwrite=False)

    assert output.read_bytes() == b"committed"
    for temp in tmp_path.glob(".*.tmp"):
        real_unlink(temp)


def test_renders_c4_only_with_query_catalog_and_non_quality_disclaimers(tmp_path: Path) -> None:
    result, output, _ = run_report(tmp_path, [c4_artifact()])

    assert result.returncode == 0, result.stderr
    report = output.read_text(encoding="utf-8")
    assert "`" + "c" * 64 + "`" in report
    assert "`synthetic` / `synthetic-1`" in report
    assert "không phải chất lượng model" in report
    assert "không chứng minh model sử dụng tri thức" in report
    assert "QUERY_SECRET" not in report


def test_renders_c3_audit_and_c4_cohort_with_matching_per_document_provenance(tmp_path: Path) -> None:
    result, output, _ = run_report(tmp_path, [c4_artifact(), c23_artifact("C3", schema="1.1")])

    assert result.returncode == 0, result.stderr
    report = output.read_text(encoding="utf-8")
    assert report.index("| C3 |") < report.index("| C4 |")
    assert "TTP consistency counts" in report


@pytest.mark.parametrize(
    "artifacts",
    [
        [c1_artifact(), c4_artifact()],
        [c23_artifact("C2", schema="1.1"), c4_artifact()],
        [c23_artifact("C3"), c4_artifact()],
    ],
)
def test_rejects_forbidden_c4_schema_mixes(tmp_path: Path, artifacts: list[dict[str, object]]) -> None:
    result, output, _ = run_report(tmp_path, artifacts)

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert not output.exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: a["documents"][0]["attack_context"].update(top_k=True),
        lambda a: a["documents"][0]["attack_context"].update(byte_length=0),
        lambda a: a["documents"][0].update(adapter_schema_version="1.1"),
        lambda a: a.update(query_manifest_sha256="A" * 64),
        lambda a: a.update(document_count=0),
    ],
)
def test_rejects_invalid_c4_context_types_and_projection(tmp_path: Path, mutate) -> None:
    artifact = c4_artifact()
    mutate(artifact)
    result, output, _ = run_report(tmp_path, [artifact])

    assert result.returncode == 2
    assert result.stderr == "Lỗi: eval_report_invalid_input\n"
    assert not output.exists()


def test_rejects_c3_c4_catalog_or_per_id_metadata_mismatch(tmp_path: Path) -> None:
    for mutate in (
        lambda a: a["ttp_audit"]["catalog"].update(version="synthetic-2"),
        lambda a: a["documents"][0]["source"].update(sha256="e" * 64),
        lambda a: a["documents"][0].update(tlp="TLP:GREEN"),
    ):
        c3, c4 = c23_artifact("C3", schema="1.1"), c4_artifact()
        mutate(c4)
        case = tmp_path / str(len(list(tmp_path.iterdir())))
        case.mkdir()
        result, output, _ = run_report(case, [c3, c4])
        assert result.returncode == 2
        assert not output.exists()
