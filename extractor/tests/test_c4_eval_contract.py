from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from extractor.eval import run as eval_run
from phonghoa_extractor import llm_adapter as adapter_module

REPO_ROOT = Path(__file__).parents[2]
SNAPSHOT = REPO_ROOT / "extractor" / "attack" / "fixtures" / "synthetic-catalog.json"


def _write_document(dataset: Path, document_id: str, text: str = "Phishing uses evil.example.") -> None:
    (dataset / "raw").mkdir(parents=True, exist_ok=True)
    (dataset / "labels").mkdir(parents=True, exist_ok=True)
    (dataset / "raw" / f"{document_id}.txt").write_text(text, encoding="utf-8")
    (dataset / "raw" / f"{document_id}.meta.json").write_text(
        json.dumps(
            {
                "id": document_id,
                "synthetic": True,
                "author": "Phong Hoa system",
                "language": "en",
                "purpose": "synthetic-smoke",
            }
        ),
        encoding="utf-8",
    )
    (dataset / "labels" / f"{document_id}.json").write_text(
        json.dumps(
            {
                "id": document_id,
                "iocs": [{"type": "domain", "value": "evil.example", "role": "attacker"}],
                "ttps": [],
            }
        ),
        encoding="utf-8",
    )


def _write_response(responses: Path, document_id: str, responses_value: list[dict]) -> None:
    responses.mkdir(parents=True, exist_ok=True)
    (responses / f"{document_id}.json").write_text(
        json.dumps(
            {
                "provider": {"name": "scripted", "destination": "fake_offline", "egress": False},
                "responses": responses_value,
            }
        ),
        encoding="utf-8",
    )


def _completed() -> dict:
    return {
        "status": "completed",
        "model_id": "scripted-v1",
        "payload": {
            "iocs": [
                {
                    "type": "domain",
                    "value": "evil.example",
                    "role": "attacker",
                    "evidence": "evil.example",
                }
            ],
            "techniques": [{"id": "T1000", "evidence": "Phishing"}],
            "malware": [],
            "actors": [],
        },
        "retryable": False,
        "error_code": None,
    }


def _write_pin(tmp_path: Path) -> Path:
    pin = tmp_path / "pin.json"
    pin.write_text(
        json.dumps(
            {
                "kind": "synthetic",
                "version": "synthetic-1",
                "sha256": hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
                "source_url": None,
                "release_tag": None,
                "commit": None,
                "provenance": "hand-authored-test-fixture",
            }
        ),
        encoding="utf-8",
    )
    return pin


def _write_manifest(tmp_path: Path, queries: dict[str, str]) -> Path:
    path = tmp_path / "queries.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "query_policy": "explicit-per-document-v1",
                "queries": queries,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _catalog(tmp_path: Path):
    pin = eval_run._load_snapshot_pin(_write_pin(tmp_path))
    return eval_run.load_catalog(SNAPSHOT, pin)


def test_load_query_manifest_preserves_explicit_queries_and_raw_digest(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, {"doc-1": "phishing technique"})
    raw = path.read_bytes()

    manifest = eval_run.load_c4_query_manifest(path)

    assert manifest.schema_version == "1.0"
    assert manifest.query_policy == "explicit-per-document-v1"
    assert manifest.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert manifest.queries == (("doc-1", "phishing technique"),)


@pytest.mark.parametrize(
    "raw",
    [
        b"\xef\xbb\xbf{}",
        b'{"schema_version":"1.0","schema_version":"1.0"}',
        b'{"schema_version":"1.0","query_policy":"explicit-per-document-v1","queries":{"x":NaN}}',
        b'{"schema_version":"1.0","query_policy":"explicit-per-document-v1","queries":{"x":"!!!"}}',
        b'{"schema_version":"1.0","query_policy":"explicit-per-document-v1","queries":{"x":"a"}}',
        b'{"schema_version":"1.0","query_policy":"explicit-per-document-v1","queries":{"x":"   "}}',
    ],
)
def test_load_query_manifest_rejects_unsafe_or_unsearchable_input(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / "queries.json"
    path.write_bytes(raw)

    with pytest.raises(eval_run.DatasetError):
        eval_run.load_c4_query_manifest(path)


def test_public_evaluator_revalidates_manifest_dto_and_exact_id_map(tmp_path: Path) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    _write_document(dataset, "doc-1")
    _write_response(responses, "doc-1", [_completed()])
    manifest = eval_run.load_c4_query_manifest(
        _write_manifest(tmp_path, {"different-id": "phishing technique"})
    )

    with pytest.raises(eval_run.DatasetError):
        eval_run.evaluate_c4_dataset(
            dataset,
            responses,
            tlp="TLP:CLEAR",
            attack_catalog=_catalog(tmp_path),
            query_manifest=manifest,
        )


def test_c4_artifact_records_context_audit_and_never_raw_query_or_context(tmp_path: Path) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    _write_document(dataset, "doc-1")
    _write_response(responses, "doc-1", [_completed()])
    manifest_path = _write_manifest(tmp_path, {"doc-1": "QUERY_SECRET phishing technique"})
    manifest = eval_run.load_c4_query_manifest(manifest_path)

    result = eval_run.evaluate_c4_dataset(
        dataset,
        responses,
        tlp="TLP:AMBER+STRICT",
        attack_catalog=_catalog(tmp_path),
        query_manifest=manifest,
    )

    encoded = json.dumps(result, ensure_ascii=False)
    document = result["documents"][0]
    assert result["schema_version"] == "1.2"
    assert result["config"] == "C4"
    assert result["query_manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert result["document_count"] == 1
    assert result["ttp_audit"]["enabled"] is True
    assert document["adapter_schema_version"] == "1.0"
    assert document["tlp"] == "TLP:AMBER+STRICT"
    assert document["prediction_basis"] == "adapter_grounded_model_plus_regex"
    assert document["attack_context"]["top_k"] == 5
    assert document["attack_context"]["budget_bytes"] == 4096
    assert document["attack_context"]["c4_adapter_completed"] is True
    assert document["ttp_audit"][0]["semantic_status"] == "unverified"
    assert "QUERY_SECRET" not in encoded
    assert '"techniques"' not in encoded


def test_c4_preflights_all_documents_before_first_generate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    for document_id in ("a-good", "z-bad"):
        _write_document(dataset, document_id)
        _write_response(responses, document_id, [_completed()])
    (dataset / "raw" / "z-bad.meta.json").write_text("{bad-json", encoding="utf-8")
    manifest = eval_run.load_c4_query_manifest(
        _write_manifest(tmp_path, {"a-good": "phishing technique", "z-bad": "phishing technique"})
    )
    calls = 0
    provider_loads = 0
    real_loader = eval_run.load_scripted_provider

    def counted_loader(path: Path):
        nonlocal provider_loads
        provider_loads += 1
        return real_loader(path)

    def counted_adapter(**_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("generate must not run during failed preflight")

    monkeypatch.setattr(eval_run, "run_c4_extraction", counted_adapter, raising=False)
    monkeypatch.setattr(eval_run, "load_scripted_provider", counted_loader)

    with pytest.raises(eval_run.DatasetError):
        eval_run.evaluate_c4_dataset(
            dataset,
            responses,
            tlp="TLP:CLEAR",
            attack_catalog=_catalog(tmp_path),
            query_manifest=manifest,
        )
    assert calls == 0
    assert provider_loads == 0


def test_c4_requires_nonempty_bounded_dataset(tmp_path: Path) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    dataset.mkdir()
    responses.mkdir()
    manifest = eval_run.load_c4_query_manifest(_write_manifest(tmp_path, {"doc": "phishing technique"}))

    with pytest.raises(eval_run.DatasetError):
        eval_run.evaluate_c4_dataset(
            dataset,
            responses,
            tlp="TLP:CLEAR",
            attack_catalog=_catalog(tmp_path),
            query_manifest=manifest,
        )


def test_c4_writer_is_no_clobber_and_preserves_competing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    _write_document(dataset, "doc-1")
    _write_response(responses, "doc-1", [_completed()])
    manifest = eval_run.load_c4_query_manifest(_write_manifest(tmp_path, {"doc-1": "phishing technique"}))
    artifact = eval_run.evaluate_c4_dataset(
        dataset,
        responses,
        tlp="TLP:CLEAR",
        attack_catalog=_catalog(tmp_path),
        query_manifest=manifest,
    )
    output = tmp_path / "result.json"
    output.write_bytes(b"competitor")

    with pytest.raises(eval_run.DatasetError):
        eval_run._write_c4_json_no_clobber(output, artifact)
    assert output.read_bytes() == b"competitor"

    output.unlink()

    def competing_link(_source: Path, destination: Path) -> None:
        destination.write_bytes(b"race-winner")
        raise FileExistsError

    monkeypatch.setattr(eval_run.os, "link", competing_link)
    with pytest.raises(eval_run.DatasetError):
        eval_run._write_c4_json_no_clobber(output, artifact)
    assert output.read_bytes() == b"race-winner"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_c4_writer_validates_exact_schema_before_publish(tmp_path: Path) -> None:
    output = tmp_path / "result.json"

    with pytest.raises(eval_run.DatasetError):
        eval_run._write_c4_json_no_clobber(output, {"schema_version": "1.2"})

    assert not output.exists()


def test_c4_cleanup_failure_after_commit_keeps_published_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "result.json"
    real_unlink = Path.unlink

    monkeypatch.setattr(eval_run, "_c4_json_bytes", lambda _value: b"published\n")

    def failed_temp_unlink(path: Path, *args, **kwargs) -> None:
        if path.suffix == ".tmp":
            raise OSError("synthetic cleanup failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failed_temp_unlink)
    with pytest.raises(OSError):
        eval_run._write_c4_json_no_clobber(output, {})

    assert output.read_bytes() == b"published\n"
    for temp in tmp_path.glob(".*.tmp"):
        real_unlink(temp)


def test_c4_evaluator_records_one_retrieval_per_document_and_exact_provider_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset, responses = tmp_path / "dataset", tmp_path / "responses"
    for document_id in ("fallback", "normal", "retry"):
        _write_document(dataset, document_id)
    retryable = {"status": "error", "retryable": True, "error_code": "temporary"}
    _write_response(responses, "normal", [_completed()])
    _write_response(responses, "retry", [retryable, _completed()])
    _write_response(responses, "fallback", [retryable, retryable])
    manifest = eval_run.load_c4_query_manifest(
        _write_manifest(
            tmp_path,
            {document_id: "phishing technique" for document_id in ("fallback", "normal", "retry")},
        )
    )
    providers = {}
    real_loader = eval_run.load_scripted_provider
    real_retrieve = adapter_module.retrieve_techniques
    retrieval_calls = 0

    def recording_loader(path: Path):
        provider = real_loader(path)
        providers[path.stem] = provider
        return provider

    def counted_retrieve(*args, **kwargs):
        nonlocal retrieval_calls
        retrieval_calls += 1
        return real_retrieve(*args, **kwargs)

    monkeypatch.setattr(eval_run, "load_scripted_provider", recording_loader)
    monkeypatch.setattr(adapter_module, "retrieve_techniques", counted_retrieve)

    result = eval_run.evaluate_c4_dataset(
        dataset,
        responses,
        tlp="TLP:CLEAR",
        attack_catalog=_catalog(tmp_path),
        query_manifest=manifest,
    )

    assert retrieval_calls == 3
    assert {key: provider.calls for key, provider in providers.items()} == {
        "fallback": 2,
        "normal": 1,
        "retry": 2,
    }
    assert providers["fallback"].requests[0] is providers["fallback"].requests[1]
    assert providers["retry"].requests[0] is providers["retry"].requests[1]
    assert {document["id"]: document["attempts"] for document in result["documents"]} == {
        "fallback": 2,
        "normal": 1,
        "retry": 2,
    }
