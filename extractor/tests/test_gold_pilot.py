from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from phonghoa_extractor.gold_pilot import (
    GoldPilotError,
    validate_gold_pilot,
    write_readiness,
)

ROOT = Path(__file__).parents[2]
CLI = ROOT / "extractor" / "dataset" / "check_gold_pilot.py"
CATALOG = ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def make_inputs(tmp_path: Path, *, annotations: int = 2, findings: bool = True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    snapshot = tmp_path / "catalog.json"
    snapshot.write_bytes(CATALOG.read_bytes())
    snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    pin = tmp_path / "pin.json"
    dump(
        pin,
        {
            "kind": "synthetic",
            "version": "synthetic-1",
            "sha256": snapshot_hash,
            "source_url": None,
            "release_tag": None,
            "commit": None,
            "provenance": "hand-authored-test-fixture",
        },
    )
    dataset = tmp_path / "dataset"
    for directory in ("records", "annotations", "raw"):
        (dataset / directory).mkdir(parents=True, exist_ok=True)
    dump(
        dataset / "manifest.json",
        {
            "schema_version": "gold-pilot-v1",
            "dataset_id": "synthetic-five",
            "purpose": "human-annotation-pilot",
            "provenance": "synthetic-fixture",
            "document_count": 5,
        },
    )
    for index in range(5):
        record_id = f"doc-{index}"
        token = f"evil{index}.example"
        text = f"IOC {token}\r\nHành vi thử nghiệm 😀."
        normalized = text.replace("\r\n", "\n")
        raw_bytes = text.encode()
        raw_hash = hashlib.sha256(normalized.encode()).hexdigest()
        (dataset / "raw" / f"{record_id}.txt").write_bytes(raw_bytes)
        dump(
            dataset / "records" / f"{record_id}.meta.json",
            {
                "schema_version": "gold-pilot-v1",
                "id": record_id,
                "source": {
                    "url": f"https://example.invalid/{record_id}",
                    "publisher": "Synthetic publisher",
                    "published_date": "2026-11-01",
                    "retrieved_at": "2026-11-02",
                    "source_license": "cc-by-4.0",
                    "storage_right": "repo-allowed",
                },
                "language": "vi",
                "tlp": "TLP:CLEAR",
                "raw": {"present": True, "sha256": raw_hash},
                "duplicate_group": record_id,
                "split": "pilot",
                "attack": {"version": "synthetic-1", "sha256": snapshot_hash},
            },
        )
        for annotator in range(annotations):
            iocs = []
            ttps = []
            if findings:
                start = normalized.index(token)
                evidence = {
                    "start": start,
                    "end": start + len(token),
                    "quote_sha256": hashlib.sha256(token.encode()).hexdigest(),
                }
                iocs = [
                    {
                        "type": "domain",
                        "value": token,
                        "role": "attacker",
                        "evidence": [evidence],
                    }
                ]
                phrase = "Hành vi thử nghiệm"
                start = normalized.index(phrase)
                ttps = [
                    {
                        "attack_id": "T1000",
                        "evidence": [
                            {
                                "start": start,
                                "end": start + len(phrase),
                                "quote_sha256": hashlib.sha256(phrase.encode()).hexdigest(),
                            }
                        ],
                    }
                ]
            dump(
                dataset / "annotations" / f"{record_id}.ann-{annotator}.json",
                {
                    "schema_version": "gold-pilot-v1",
                    "id": record_id,
                    "annotator_id": f"ann-{annotator}",
                    "annotated_at": "2026-11-03",
                    "attack_version": "synthetic-1",
                    "raw_sha256": raw_hash,
                    "iocs": iocs,
                    "ttps": ttps,
                    "no_findings": not findings,
                },
            )
    return dataset, snapshot, pin


def payload(report) -> dict[str, object]:
    return json.loads(report.payload)


def assert_code(code: str, action) -> None:
    with pytest.raises(GoldPilotError) as caught:
        action()
    assert caught.value.code == code
    assert str(caught.value) == code


def mutate_json(path: Path, keys: tuple[object, ...], supplied: object) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    node = value
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = supplied
    dump(path, value)


def test_ready_report_is_deterministic_bounded_and_non_sensitive(tmp_path: Path) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in dataset.rglob("*") if path.is_file()
    }

    first = validate_gold_pilot(dataset, snapshot, pin)
    second = validate_gold_pilot(dataset, snapshot, pin)
    value = payload(first)

    assert first.status == "READY_FOR_ADJUDICATION"
    assert first.payload == second.payload
    assert value["status"] == "READY_FOR_ADJUDICATION"
    assert value["reasons"] == []
    assert value["cohort"] == {
        "deduplication": "declared-only",
        "evaluated_record_count": 5,
        "ioc_agreement": {"intersection": 5, "ratio": 1.0, "status": "available", "union": 5},
        "ttp_agreement": {"intersection": 5, "ratio": 1.0, "status": "available", "union": 5},
    }
    assert value["limitations"][-1] == "no-model-quality-claim"
    assert all(item["semantic_status"] == "unverified" for item in value["records"])
    assert b"evil0" not in first.payload and b"Synthetic publisher" not in first.payload
    assert before == {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in dataset.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize(
    ("annotations", "findings", "record_reason", "dataset_reasons"),
    [
        (0, True, "NEEDS_SECOND_ANNOTATION", ["RECORDS_NOT_READY"]),
        (1, True, "NEEDS_SECOND_ANNOTATION", ["RECORDS_NOT_READY"]),
        (2, False, None, ["NO_FINDINGS_ONLY"]),
    ],
)
def test_not_ready_reasons_and_empty_agreement(
    tmp_path: Path,
    annotations: int,
    findings: bool,
    record_reason: str | None,
    dataset_reasons: list[str],
) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path, annotations=annotations, findings=findings)
    value = payload(validate_gold_pilot(dataset, snapshot, pin))
    assert value["status"] == "NOT_READY"
    assert value["reasons"] == dataset_reasons
    assert value["records"][0]["reasons"] == ([] if record_reason is None else [record_reason])
    if findings is False:
        assert value["records"][0]["ioc_agreement"] == {
            "intersection": 0,
            "ratio": None,
            "status": "both_empty",
            "union": 0,
        }


def test_rejects_unknown_keys_duplicate_json_bad_types_and_bom(tmp_path: Path) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    manifest = dataset / "manifest.json"
    manifest.write_text(manifest.read_text()[:-1] + ',"extra":1}', encoding="utf-8")
    assert_code("invalid_manifest", lambda: validate_gold_pilot(dataset, snapshot, pin))

    dataset, snapshot, pin = make_inputs(tmp_path / "duplicate")
    (dataset / "manifest.json").write_text(
        '{"schema_version":"gold-pilot-v1","schema_version":"gold-pilot-v1"}', encoding="utf-8"
    )
    assert_code("invalid_manifest", lambda: validate_gold_pilot(dataset, snapshot, pin))

    dataset, snapshot, pin = make_inputs(tmp_path / "bom")
    raw = dataset / "records" / "doc-0.meta.json"
    raw.write_bytes(b"\xef\xbb\xbf" + raw.read_bytes())
    assert_code("invalid_record", lambda: validate_gold_pilot(dataset, snapshot, pin))


def test_rejects_ioc_token_mismatch_unknown_or_inactive_technique(tmp_path: Path) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    annotation = dataset / "annotations" / "doc-0.ann-0.json"
    value = json.loads(annotation.read_text())
    value["iocs"][0]["evidence"][0]["end"] += 1
    dump(annotation, value)
    assert_code("invalid_annotation", lambda: validate_gold_pilot(dataset, snapshot, pin))

    for attack_id in ("T9999", "T2000"):
        dataset, snapshot, pin = make_inputs(tmp_path / attack_id)
        annotation = dataset / "annotations" / "doc-0.ann-0.json"
        value = json.loads(annotation.read_text())
        value["ttps"][0]["attack_id"] = attack_id
        dump(annotation, value)
        assert_code(
            "invalid_technique",
            lambda dataset=dataset, snapshot=snapshot, pin=pin: validate_gold_pilot(dataset, snapshot, pin),
        )


def test_rights_translation_inventory_and_fingerprint_mutation(tmp_path: Path) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    first = payload(validate_gold_pilot(dataset, snapshot, pin))["dataset_input_sha256"]
    annotation = dataset / "annotations" / "doc-0.ann-0.json"
    value = json.loads(annotation.read_text())
    value["annotated_at"] = "2026-11-04"
    dump(annotation, value)
    second = payload(validate_gold_pilot(dataset, snapshot, pin))["dataset_input_sha256"]
    assert first != second

    dataset, snapshot, pin = make_inputs(tmp_path / "rights")
    record = dataset / "records" / "doc-0.meta.json"
    value = json.loads(record.read_text())
    value["source"]["storage_right"] = "prohibited"
    dump(record, value)
    assert_code("invalid_record", lambda: validate_gold_pilot(dataset, snapshot, pin))

    dataset, snapshot, pin = make_inputs(tmp_path / "translation")
    record = dataset / "records" / "doc-0.meta.json"
    value = json.loads(record.read_text())
    value["translation_of"] = "missing"
    dump(record, value)
    assert_code("invalid_record", lambda: validate_gold_pilot(dataset, snapshot, pin))

    dataset, snapshot, pin = make_inputs(tmp_path / "orphan")
    (dataset / "raw" / "orphan.txt").write_text("x", encoding="utf-8")
    assert_code("invalid_inventory", lambda: validate_gold_pilot(dataset, snapshot, pin))


def test_writer_is_no_clobber_protects_inputs_and_reports_post_link_cleanup(
    tmp_path: Path, monkeypatch
) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    report = validate_gold_pilot(dataset, snapshot, pin)
    output = tmp_path / "report.json"
    result = write_readiness(report, output)
    assert result.published is True and result.cleanup_warning is False
    assert output.read_bytes() == report.payload
    assert_code("unsafe_output", lambda: write_readiness(report, output))
    assert_code("unsafe_output", lambda: write_readiness(report, dataset / "report.json"))
    assert_code("unsafe_output", lambda: write_readiness(report, snapshot))

    output2 = tmp_path / "report-2.json"
    real_unlink = os.unlink

    def fail_temp_unlink(path, *args, **kwargs):
        if str(path).endswith(".tmp"):
            raise OSError("injected")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", fail_temp_unlink)
    result = write_readiness(report, output2)
    assert result.published is True and result.cleanup_warning is True
    assert output2.read_bytes() == report.payload


def test_cli_ready_not_ready_invalid_and_api_parity(tmp_path: Path) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    report_path = tmp_path / "ready.json"
    command = [
        sys.executable,
        str(CLI),
        "--dataset",
        str(dataset),
        "--attack-snapshot",
        str(snapshot),
        "--attack-pin",
        str(pin),
        "--report",
        str(report_path),
    ]
    env = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "core"), str(ROOT / "extractor")))}
    completed = subprocess.run(command, capture_output=True, env=env, check=False)
    assert completed.returncode == 0
    assert completed.stdout == b'{"status":"READY_FOR_ADJUDICATION"}\n'
    assert completed.stderr == b""
    assert report_path.read_bytes() == validate_gold_pilot(dataset, snapshot, pin).payload

    dataset, snapshot, pin = make_inputs(tmp_path / "partial", annotations=1)
    completed = subprocess.run(
        command[:2]
        + [
            "--dataset",
            str(dataset),
            "--attack-snapshot",
            str(snapshot),
            "--attack-pin",
            str(pin),
            "--report",
            str(tmp_path / "partial.json"),
        ],
        capture_output=True,
        env=env,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stdout == b'{"status":"NOT_READY"}\n'

    completed = subprocess.run([sys.executable, str(CLI)], capture_output=True, env=env, check=False)
    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == b'{"error":"invalid_arguments"}\n'


@pytest.mark.parametrize("bad", [[], {}], ids=["list", "dict"])
@pytest.mark.parametrize(
    ("relative", "keys", "code"),
    [
        ("manifest.json", ("provenance",), "invalid_manifest"),
        ("records/doc-0.meta.json", ("source", "source_license"), "invalid_record"),
        ("records/doc-0.meta.json", ("source", "storage_right"), "invalid_record"),
        ("records/doc-0.meta.json", ("language",), "invalid_record"),
        ("records/doc-0.meta.json", ("tlp",), "invalid_record"),
        ("annotations/doc-0.ann-0.json", ("iocs", 0, "type"), "invalid_annotation"),
        ("annotations/doc-0.ann-0.json", ("iocs", 0, "role"), "invalid_annotation"),
        (
            "annotations/doc-0.ann-0.json",
            ("iocs", 0, "evidence", 0, "quote_sha256"),
            "invalid_annotation",
        ),
    ],
)
def test_wrong_json_types_return_closed_errors(
    tmp_path: Path,
    bad: object,
    relative: str,
    keys: tuple[object, ...],
    code: str,
) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    mutate_json(dataset / relative, keys, bad)
    assert_code(code, lambda: validate_gold_pilot(dataset, snapshot, pin))


@pytest.mark.parametrize(
    "url",
    [
        "https://[SYNTHETIC_PRIVATE_MARKER/",
        "https://@example.invalid/",
        "https://example.invalid/\x7f",
    ],
)
def test_malformed_userinfo_and_control_urls_are_safe_invalid_record(tmp_path: Path, url: str) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    mutate_json(dataset / "records/doc-0.meta.json", ("source", "url"), url)
    assert_code("invalid_record", lambda: validate_gold_pilot(dataset, snapshot, pin))


@pytest.mark.parametrize("kind", ["dataset", "pin", "snapshot", "output"])
def test_reparse_ancestor_is_rejected_before_use(tmp_path: Path, monkeypatch, kind: str) -> None:
    from phonghoa_extractor import gold_pilot as gp

    ancestor = tmp_path / "unsafe-ancestor"
    nested = ancestor / "nested"
    nested.mkdir(parents=True)
    if kind == "dataset":
        dataset, snapshot, pin = make_inputs(nested)
    else:
        dataset, snapshot, pin = make_inputs(tmp_path / "safe")
        if kind == "pin":
            pin = pin.rename(nested / pin.name)
        elif kind == "snapshot":
            snapshot = snapshot.rename(nested / snapshot.name)
    report = validate_gold_pilot(dataset, snapshot, pin) if kind == "output" else None
    original = Path.lstat

    class WithReparse:
        def __init__(self, info):
            self.info = info
            self.st_file_attributes = info.st_file_attributes | gp.REPARSE

        def __getattr__(self, name):
            return getattr(self.info, name)

    def marked(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        return WithReparse(info) if path == ancestor else info

    monkeypatch.setattr(Path, "lstat", marked)
    if kind == "output":
        assert_code("unsafe_output", lambda: write_readiness(report, nested / "report.json"))
    else:
        with pytest.raises(GoldPilotError):
            validate_gold_pilot(dataset, snapshot, pin)


def test_inventory_stops_at_global_file_cap(tmp_path: Path, monkeypatch) -> None:
    from phonghoa_extractor import gold_pilot as gp

    dataset, _, _ = make_inputs(tmp_path)
    raw = dataset / "raw"
    for index in range(100):
        (raw / f"extra-{index:03}.txt").write_bytes(b"x")
    original = Path.iterdir
    seen: list[str] = []

    def tracked(path):
        for entry in original(path):
            if path == raw:
                seen.append(entry.name)
            yield entry

    monkeypatch.setattr(Path, "iterdir", tracked)
    assert_code("invalid_inventory", lambda: gp.inventory(dataset))
    assert len(seen) <= 23


def test_fingerprint_permission_failure_is_closed_io_error(tmp_path: Path, monkeypatch) -> None:
    dataset, snapshot, pin = make_inputs(tmp_path)
    original = Path.read_bytes

    def denied(path):
        if path == dataset / "manifest.json":
            raise PermissionError("SYNTHETIC_PRIVATE_MARKER")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", denied)
    assert_code("io_failure", lambda: validate_gold_pilot(dataset, snapshot, pin))
