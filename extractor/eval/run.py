"""Chạy baseline C1 ngoại tuyến trên dataset theo GUIDELINE."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_core.extract import extract_iocs  # noqa: E402
from phonghoa_core.ioc import Ioc, normalize  # noqa: E402
from phonghoa_extractor.attack_catalog import (  # noqa: E402
    AttackCatalog,
    AttackCatalogError,
    SnapshotPin,
    load_catalog,
)
from phonghoa_extractor.attack_retrieval import AttackRetrievalError, _validate_query  # noqa: E402
from phonghoa_extractor.evaluate import Score, micro_average, score_iocs  # noqa: E402
from phonghoa_extractor.llm_adapter import AdapterError, run_c4_extraction, run_extraction  # noqa: E402
from phonghoa_extractor.llm_fixture import load_scripted_provider  # noqa: E402
from phonghoa_extractor.ttp_audit import (  # noqa: E402
    TechniqueAudit,
    TtpAuditError,
    audit_techniques,
)

PIN_MAX_BYTES = 16 * 1024
QUERY_MANIFEST_MAX_BYTES = 16 * 1024
REPORT_MAX_BYTES = 1024 * 1024
C4_LIMITATIONS = [
    "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
    "C4 adapter merges model candidates with regex extraction before grounding; scores are not model-only.",
    "Semantic TTP, malware, and actor items are not evaluated.",
    "Retrieval completion and context transmission do not prove model knowledge use or quality.",
    "TTP audit reports source, quote, and catalog consistency only; semantic TTP remains unverified.",
]
PIN_FIELDS = {
    "kind",
    "version",
    "sha256",
    "source_url",
    "release_tag",
    "commit",
    "provenance",
}


class DatasetError(ValueError):
    """Dataset không đúng cấu trúc smoke đã công bố."""


class _InvalidPinJson(ValueError):
    pass


@dataclass(frozen=True)
class C4QueryManifest:
    schema_version: Literal["1.0"]
    query_policy: Literal["explicit-per-document-v1"]
    raw_sha256: str
    queries: tuple[tuple[str, str], ...]


def _pin_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidPinJson
        result[key] = value
    return result


def _manifest_error() -> DatasetError:
    return DatasetError("query manifest không hợp lệ")


def _validate_query_entry(document_id: object, query: object) -> tuple[str, str]:
    if type(document_id) is not str or not 1 <= len(document_id) <= 128 or "\x00" in document_id:
        raise _manifest_error()
    try:
        document_id.encode("utf-8", errors="strict")
        validated_query, _ = _validate_query(query)
    except (UnicodeError, AttackRetrievalError) as exc:
        raise _manifest_error() from exc
    return document_id, validated_query


def load_c4_query_manifest(path: Path) -> C4QueryManifest:
    """Đọc manifest query bất biến, giữ digest của bytes đầu vào."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(QUERY_MANIFEST_MAX_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise _manifest_error() from exc
    if len(raw) > QUERY_MANIFEST_MAX_BYTES:
        raise _manifest_error()
    try:
        text = raw.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            raise _InvalidPinJson
        value = json.loads(
            text,
            object_pairs_hook=_pin_pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(_InvalidPinJson()),
        )
    except (UnicodeError, json.JSONDecodeError, _InvalidPinJson, RecursionError, ValueError) as exc:
        raise _manifest_error() from exc
    if type(value) is not dict or set(value) != {"schema_version", "query_policy", "queries"}:
        raise _manifest_error()
    if value["schema_version"] != "1.0" or value["query_policy"] != "explicit-per-document-v1":
        raise _manifest_error()
    queries = value["queries"]
    if type(queries) is not dict or not queries or len(queries) > 256:
        raise _manifest_error()
    entries = tuple(_validate_query_entry(key, query) for key, query in queries.items())
    return C4QueryManifest(
        schema_version="1.0",
        query_policy="explicit-per-document-v1",
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        queries=entries,
    )


def _load_snapshot_pin(path: Path) -> SnapshotPin:
    try:
        with path.open("rb") as stream:
            payload = stream.read(PIN_MAX_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise DatasetError("attack pin không hợp lệ") from exc
    if len(payload) > PIN_MAX_BYTES:
        raise DatasetError("attack pin không hợp lệ")
    try:
        text = payload.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            raise _InvalidPinJson
        value = json.loads(
            text,
            object_pairs_hook=_pin_pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(_InvalidPinJson()),
        )
    except (UnicodeError, json.JSONDecodeError, _InvalidPinJson, RecursionError, ValueError) as exc:
        raise DatasetError("attack pin không hợp lệ") from exc
    if type(value) is not dict or set(value) != PIN_FIELDS:
        raise DatasetError("attack pin không hợp lệ")
    if any(type(value[field]) is not str for field in ("kind", "version", "sha256", "provenance")):
        raise DatasetError("attack pin không hợp lệ")
    if any(
        field_value is not None and type(field_value) is not str
        for field_value in (value["source_url"], value["release_tag"], value["commit"])
    ):
        raise DatasetError("attack pin không hợp lệ")
    return SnapshotPin(**value)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DatasetError(f"Thiếu file {path.name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"Không đọc được {path.name}: {exc}") from exc


def _validate_metadata(metadata: Any, path: Path, document_id: str) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise DatasetError(f"{path.name}: metadata phải là object JSON")
    required = {"id", "synthetic", "author", "language", "purpose"}
    missing = sorted(required - metadata.keys())
    if missing:
        raise DatasetError(f"{path.name}: thiếu trường {', '.join(missing)}")
    if metadata["id"] != document_id:
        raise DatasetError(f"{path.name}: id không khớp {document_id}")
    if metadata["synthetic"] is not True or metadata["purpose"] != "synthetic-smoke":
        raise DatasetError(f"{path.name}: chỉ nhận dữ liệu synthetic-smoke")
    if not isinstance(metadata["language"], str) or metadata["language"] not in {"vi", "en"}:
        raise DatasetError(f"{path.name}: language không hợp lệ")
    return metadata


def _validate_labels(labels: Any, path: Path, document_id: str) -> list[dict[str, str]]:
    if not isinstance(labels, dict) or labels.get("id") != document_id:
        raise DatasetError(f"{path.name}: object nhãn hoặc id không hợp lệ")
    iocs = labels.get("iocs")
    if not isinstance(iocs, list):
        raise DatasetError(f"{path.name}: iocs phải là danh sách")
    for index, item in enumerate(iocs):
        _validate_label_item(item, path, index)
    return iocs


def _validate_label_item(item: Any, path: Path, index: int) -> None:
    if not isinstance(item, dict) or not all(key in item for key in ("type", "value", "role")):
        raise DatasetError(f"{path.name}: iocs[{index}] thiếu type/value/role")
    try:
        normalized = normalize(item["value"])
    except (TypeError, ValueError) as exc:
        raise DatasetError(f"{path.name}: iocs[{index}] có value không hợp lệ") from exc
    if item["type"] != normalized.type.value:
        raise DatasetError(f"{path.name}: iocs[{index}] có type không khớp value")
    role = item["role"]
    if not isinstance(role, str) or role not in {"attacker", "victim", "benign"}:
        raise DatasetError(f"{path.name}: iocs[{index}] có role không hợp lệ")


def _score_dict(score: Score) -> dict[str, int | float]:
    return {
        "tp": score.tp,
        "fp": score.fp,
        "fn": score.fn,
        "precision": score.precision,
        "recall": score.recall,
        "f1": score.f1,
    }


def _dataset_hash(dataset: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(dataset).as_posix()):
        relative = path.relative_to(dataset).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _score_by_type(predicted: list[Ioc], gold: list[dict[str, str]]) -> dict[str, Score]:
    relevant = {ioc.type.value for ioc in predicted}
    relevant.update(item["type"] for item in gold if item["role"] == "attacker")
    return {
        ioc_type: score_iocs(
            [ioc.value for ioc in predicted if ioc.type.value == ioc_type],
            [item for item in gold if item["type"] == ioc_type],
        )
        for ioc_type in sorted(relevant)
    }


def _evaluate_document(dataset: Path, text_path: Path) -> tuple[dict[str, Any], dict[str, Score], list[Path]]:
    document_id = text_path.stem
    metadata_path = text_path.with_suffix(".meta.json")
    label_path = dataset / "labels" / f"{document_id}.json"
    metadata = _validate_metadata(_load_json(metadata_path), metadata_path, document_id)
    gold = _validate_labels(_load_json(label_path), label_path, document_id)
    try:
        text = text_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DatasetError(f"Không đọc được {text_path.name}: {exc}") from exc
    predicted = extract_iocs(text)
    score = score_iocs([ioc.value for ioc in predicted], gold)
    result = {
        "id": document_id,
        "language": metadata["language"],
        "source": {
            "path": text_path.relative_to(dataset).as_posix(),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        },
        "prediction": {"iocs": [{"type": ioc.type.value, "value": ioc.value} for ioc in predicted]},
        "score": _score_dict(score),
    }
    return result, _score_by_type(predicted, gold), [text_path, metadata_path, label_path]


def evaluate_dataset(dataset: Path) -> dict[str, Any]:
    raw_dir = dataset / "raw"
    text_paths = sorted(raw_dir.glob("*.txt"))
    text_ids = {path.stem for path in text_paths}
    for label_path in sorted((dataset / "labels").glob("*.json")):
        if label_path.stem not in text_ids:
            raise DatasetError(f"{label_path.name}: thiếu file raw/{label_path.stem}.txt")
    for metadata_path in sorted(raw_dir.glob("*.meta.json")):
        document_id = metadata_path.name.removesuffix(".meta.json")
        if document_id not in text_ids:
            raise DatasetError(f"{metadata_path.name}: thiếu file raw/{document_id}.txt")
    if not text_paths:
        raise DatasetError(f"{raw_dir}: không có báo cáo .txt")
    documents: list[dict[str, Any]] = []
    per_type: dict[str, list[Score]] = {}
    input_paths: list[Path] = []
    for text_path in text_paths:
        document, type_scores, paths = _evaluate_document(dataset, text_path)
        documents.append(document)
        input_paths.extend(paths)
        for ioc_type, score in type_scores.items():
            per_type.setdefault(ioc_type, []).append(score)
    total = micro_average([_score_from_dict(document["score"]) for document in documents])
    return {
        "schema_version": "1.0",
        "config": "C1",
        "purpose": "synthetic-smoke",
        "dataset_sha256": _dataset_hash(dataset, input_paths),
        "document_count": len(documents),
        "documents": documents,
        "micro": _score_dict(total),
        "by_type": {
            ioc_type: _score_dict(micro_average(scores)) for ioc_type, scores in sorted(per_type.items())
        },
        "ttp": {"status": "not_evaluated"},
    }


def _score_from_dict(data: dict[str, Any]) -> Score:
    return Score(tp=data["tp"], fp=data["fp"], fn=data["fn"])


def _discover_text_paths(dataset: Path) -> list[Path]:
    raw_dir = dataset / "raw"
    text_paths = sorted(raw_dir.glob("*.txt"))
    text_ids = {path.stem for path in text_paths}
    for label_path in sorted((dataset / "labels").glob("*.json")):
        if label_path.stem not in text_ids:
            raise DatasetError(f"{label_path.name}: thiếu file raw/{label_path.stem}.txt")
    for metadata_path in sorted(raw_dir.glob("*.meta.json")):
        document_id = metadata_path.name.removesuffix(".meta.json")
        if document_id not in text_ids:
            raise DatasetError(f"{metadata_path.name}: thiếu file raw/{document_id}.txt")
    if not text_paths:
        raise DatasetError(f"{raw_dir}: không có báo cáo .txt")
    return text_paths


def _read_document_inputs(
    dataset: Path, text_path: Path
) -> tuple[str, dict[str, Any], list[dict], list[Path]]:
    document_id = text_path.stem
    metadata_path = text_path.with_suffix(".meta.json")
    label_path = dataset / "labels" / f"{document_id}.json"
    metadata = _validate_metadata(_load_json(metadata_path), metadata_path, document_id)
    gold = _validate_labels(_load_json(label_path), label_path, document_id)
    try:
        text = text_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DatasetError(f"Không đọc được {text_path.name}") from exc
    return text, metadata, gold, [text_path, metadata_path, label_path]


def _score_values_by_type(predicted: list[str], gold: list[dict[str, str]]) -> dict[str, Score]:
    predicted_by_type: dict[str, list[str]] = {}
    for value in predicted:
        try:
            ioc_type = normalize(value).type.value
        except (TypeError, ValueError):
            ioc_type = "invalid"
        predicted_by_type.setdefault(ioc_type, []).append(value)
    gold_types = {item["type"] for item in gold if item["role"] == "attacker"}
    return {
        ioc_type: score_iocs(
            predicted_by_type.get(ioc_type, []),
            [item for item in gold if item["role"] == "attacker" and item["type"] == ioc_type],
        )
        for ioc_type in sorted(set(predicted_by_type) | gold_types)
    }


def _git_ref() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise DatasetError("không xác định được evaluator ref")
    return completed.stdout.strip()


def _not_available_or_micro(scores: list[Score]) -> dict[str, Any]:
    return _score_dict(micro_average(scores)) if scores else {"status": "not_available"}


def _serialize_technique_audit(item: TechniqueAudit) -> dict[str, Any]:
    return {
        "item_index": item.item_index,
        "kind": item.kind,
        "value": item.value,
        "evidence": item.evidence,
        "evidence_span": list(item.evidence_span) if item.evidence_span is not None else None,
        "source_sha256": item.source_sha256,
        "config": item.config,
        "quote_status": item.quote_status,
        "catalog_status": item.catalog_status,
        "reason_code": item.reason_code,
        "pin_kind": item.pin_kind,
        "snapshot_version": item.snapshot_version,
        "snapshot_sha256": item.snapshot_sha256,
        "semantic_status": item.semantic_status,
        "operational_draft_eligible": item.operational_draft_eligible,
    }


def _empty_ttp_counts() -> dict[str, Any]:
    return {
        "technique_items": 0,
        "quote_status": {status: 0 for status in ("matched", "missing", "not_found", "ambiguous")},
        "catalog_status": {status: 0 for status in ("active", "inactive", "unknown", "not_checked")},
    }


def _add_ttp_counts(counts: dict[str, Any], items: tuple[TechniqueAudit, ...]) -> None:
    counts["technique_items"] += len(items)
    for item in items:
        counts["quote_status"][item.quote_status] += 1
        counts["catalog_status"][item.catalog_status] += 1


def _catalog_projection(catalog: AttackCatalog) -> dict[str, str | None]:
    pin = catalog.pin
    return {
        "kind": pin.kind,
        "version": pin.version,
        "sha256": pin.sha256,
        "source_url": pin.source_url,
        "release_tag": pin.release_tag,
        "commit": pin.commit,
        "provenance": pin.provenance,
    }


def evaluate_llm_dataset(
    dataset: Path,
    responses_dir: Path,
    *,
    config: str,
    tlp: str,
    attack_catalog: AttackCatalog | None = None,
) -> dict[str, Any]:
    if attack_catalog is not None and type(attack_catalog) is not AttackCatalog:
        raise DatasetError("attack catalog không hợp lệ")
    text_paths = _discover_text_paths(dataset)
    text_ids = {path.stem for path in text_paths}
    fixture_paths = sorted(responses_dir.glob("*.json"))
    fixture_ids = {path.stem for path in fixture_paths}
    if fixture_ids != text_ids:
        raise DatasetError("fixture IDs không khớp dataset")

    providers = {path.stem: load_scripted_provider(path) for path in fixture_paths}
    fixture_by_id = {path.stem: path for path in fixture_paths}
    documents: list[dict[str, Any]] = []
    dataset_paths: list[Path] = []
    scores_by_mode: dict[str, list[Score]] = {"model_completed": [], "regex_fallback": []}
    scores_by_type: dict[str, list[Score]] = {}
    ttp_counts = _empty_ttp_counts()

    for text_path in text_paths:
        document_id = text_path.stem
        text, metadata, gold, input_paths = _read_document_inputs(dataset, text_path)
        dataset_paths.extend(input_paths)
        adapter_result = run_extraction(
            text=text,
            language=metadata["language"],
            tlp=tlp,
            config=config,
            provider=providers[document_id],
        )
        if config == "C2":
            audit = adapter_result["raw_iocs"]
            predicted = [item["value"] for item in audit]
            prediction_basis = "adapter_raw_model" if adapter_result["model_items_used"] else "regex_fallback"
        else:
            audit = adapter_result["iocs"]
            predicted = [item["value"] for item in audit if item["keep"]]
            prediction_basis = (
                "adapter_grounded_model_plus_regex"
                if adapter_result["model_items_used"]
                else "regex_fallback"
            )
        score = score_iocs(predicted, gold)
        type_scores = _score_values_by_type(predicted, gold)
        scores_by_mode[adapter_result["result_mode"]].append(score)
        for ioc_type, type_score in type_scores.items():
            scores_by_type.setdefault(ioc_type, []).append(type_score)
        fixture_path = fixture_by_id[document_id]
        document = {
            "id": document_id,
            "config": config,
            "language": metadata["language"],
            "tlp": adapter_result["tlp"],
            "source": {
                "path": text_path.relative_to(dataset).as_posix(),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            },
            "fixture": {
                "path": fixture_path.relative_to(responses_dir).as_posix(),
                "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
            },
            "adapter_schema_version": adapter_result["schema_version"],
            "provider": adapter_result["provider"],
            "attempts": adapter_result["attempts"],
            "result_mode": adapter_result["result_mode"],
            "error_codes": adapter_result["error_codes"],
            "model_items_used": adapter_result["model_items_used"],
            "operational_draft_eligible": adapter_result["operational_draft_eligible"],
            "prediction_basis": prediction_basis,
            "prediction": {"values": predicted},
            "score": _score_dict(score),
        }
        if config == "C2":
            document["raw_audit"] = audit
        else:
            document["grounding_audit"] = audit
        if attack_catalog is not None:
            technique_audit = audit_techniques(
                adapter_result=adapter_result,
                source_text=text,
                catalog=attack_catalog,
            )
            document["ttp_audit"] = [_serialize_technique_audit(item) for item in technique_audit]
            _add_ttp_counts(ttp_counts, technique_audit)
        documents.append(document)

    all_scores = [_score_from_dict(document["score"]) for document in documents]
    limitations = [
        "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
        "C3 adapter merges model candidates with regex extraction before grounding; "
        "scores are not model-only.",
        "Semantic TTP, malware, and actor items are not evaluated.",
    ]
    result = {
        "schema_version": "1.1" if attack_catalog is not None else "1.0",
        "config": config,
        "purpose": "synthetic-smoke",
        "dataset_sha256": _dataset_hash(dataset, dataset_paths),
        "fixture_manifest_sha256": _dataset_hash(responses_dir, fixture_paths),
        "provider_policy": {"destination": "fake_offline", "egress": False},
        "mock_only": True,
        "evaluator": {"git_ref": _git_ref(), "python": platform.python_version()},
        "document_count": len(documents),
        "documents": documents,
        "micro_all": _score_dict(micro_average(all_scores)),
        "micro_by_result_mode": {
            mode: _not_available_or_micro(scores_by_mode[mode])
            for mode in ("model_completed", "regex_fallback")
        },
        "by_type": {
            ioc_type: _score_dict(micro_average(scores))
            for ioc_type, scores in sorted(scores_by_type.items())
        },
        "limitations": limitations,
    }
    if attack_catalog is not None:
        limitations.append(
            "TTP audit reports source, quote, and catalog consistency only; semantic TTP and C4 "
            "remain unverified."
        )
        result["ttp_audit"] = {
            "enabled": True,
            "catalog": _catalog_projection(attack_catalog),
            "metric_note": "counts only; not TTP precision, recall, F1, or detection rate",
            "counts": ttp_counts,
        }
    return result


def _validate_c4_manifest_dto(value: object) -> dict[str, str]:
    if type(value) is not C4QueryManifest:
        raise DatasetError("query manifest không hợp lệ")
    if value.schema_version != "1.0" or value.query_policy != "explicit-per-document-v1":
        raise DatasetError("query manifest không hợp lệ")
    if (
        type(value.raw_sha256) is not str
        or len(value.raw_sha256) != 64
        or any(character not in "0123456789abcdef" for character in value.raw_sha256)
        or type(value.queries) is not tuple
        or not value.queries
        or len(value.queries) > 256
    ):
        raise DatasetError("query manifest không hợp lệ")
    result: dict[str, str] = {}
    for pair in value.queries:
        if type(pair) is not tuple or len(pair) != 2:
            raise DatasetError("query manifest không hợp lệ")
        document_id, query = _validate_query_entry(pair[0], pair[1])
        if document_id in result:
            raise DatasetError("query manifest không hợp lệ")
        result[document_id] = query
    return result


def _preflight_c4_documents(
    dataset: Path, responses_dir: Path, queries: dict[str, str]
) -> tuple[list[tuple[Path, str, dict[str, Any], list[dict], list[Path], Any]], list[Path]]:
    text_paths = _discover_text_paths(dataset)
    if not 1 <= len(text_paths) <= 256 or {path.stem for path in text_paths} != set(queries):
        raise DatasetError("query manifest IDs không khớp dataset")
    fixture_paths = sorted(responses_dir.glob("*.json"))
    if {path.stem for path in fixture_paths} != set(queries):
        raise DatasetError("fixture IDs không khớp dataset")
    inputs = []
    for text_path in text_paths:
        text, metadata, gold, input_paths = _read_document_inputs(dataset, text_path)
        try:
            text_bytes = text.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise DatasetError("báo cáo không hợp lệ") from exc
        if len(text) > REPORT_MAX_BYTES or len(text_bytes) > REPORT_MAX_BYTES:
            raise DatasetError("báo cáo không hợp lệ")
        inputs.append((text_path, text, metadata, gold, input_paths))
    providers = {path.stem: load_scripted_provider(path) for path in fixture_paths}
    prepared = [(*values, providers[values[0].stem]) for values in inputs]
    return prepared, fixture_paths


def _c4_document(
    *,
    dataset: Path,
    responses_dir: Path,
    text_path: Path,
    text: str,
    metadata: dict[str, Any],
    gold: list[dict],
    provider: Any,
    query: str,
    tlp: str,
    attack_catalog: AttackCatalog,
) -> tuple[dict[str, Any], dict[str, Score], tuple[TechniqueAudit, ...]]:
    adapter_result = run_c4_extraction(
        text=text,
        language=metadata["language"],
        tlp=tlp,
        provider=provider,
        catalog=attack_catalog,
        attack_query=query,
        top_k=5,
        context_budget_bytes=4096,
    )
    audit = adapter_result["iocs"]
    predicted = [item["value"] for item in audit if item["keep"]]
    score = score_iocs(predicted, gold)
    technique_audit = audit_techniques(
        adapter_result=adapter_result,
        source_text=text,
        catalog=attack_catalog,
    )
    fixture_path = responses_dir / f"{text_path.stem}.json"
    document = {
        "id": text_path.stem,
        "config": "C4",
        "language": metadata["language"],
        "tlp": adapter_result["tlp"],
        "source": {
            "path": text_path.relative_to(dataset).as_posix(),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        "fixture": {
            "path": fixture_path.relative_to(responses_dir).as_posix(),
            "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        },
        "adapter_schema_version": adapter_result["schema_version"],
        "provider": adapter_result["provider"],
        "attempts": adapter_result["attempts"],
        "result_mode": adapter_result["result_mode"],
        "error_codes": adapter_result["error_codes"],
        "model_items_used": adapter_result["model_items_used"],
        "operational_draft_eligible": adapter_result["operational_draft_eligible"],
        "prediction_basis": (
            "adapter_grounded_model_plus_regex" if adapter_result["model_items_used"] else "regex_fallback"
        ),
        "prediction": {"values": predicted},
        "score": _score_dict(score),
        "grounding_audit": audit,
        "attack_context": adapter_result["attack_context"],
        "ttp_audit": [_serialize_technique_audit(item) for item in technique_audit],
    }
    return document, _score_values_by_type(predicted, gold), technique_audit


def evaluate_c4_dataset(
    dataset: Path,
    responses_dir: Path,
    *,
    tlp: str,
    attack_catalog: AttackCatalog,
    query_manifest: C4QueryManifest,
) -> dict[str, Any]:
    """Chạy C4 offline sau khi toàn bộ input đã qua preflight."""
    if type(attack_catalog) is not AttackCatalog:
        raise DatasetError("attack catalog không hợp lệ")
    if type(tlp) is not str or tlp not in {
        "TLP:CLEAR",
        "TLP:GREEN",
        "TLP:AMBER",
        "TLP:AMBER+STRICT",
        "TLP:RED",
    }:
        raise DatasetError("TLP không hợp lệ")
    queries = _validate_c4_manifest_dto(query_manifest)
    prepared, fixture_paths = _preflight_c4_documents(dataset, responses_dir, queries)
    documents: list[dict[str, Any]] = []
    dataset_paths: list[Path] = []
    scores_by_mode: dict[str, list[Score]] = {"model_completed": [], "regex_fallback": []}
    scores_by_type: dict[str, list[Score]] = {}
    ttp_counts = _empty_ttp_counts()
    for text_path, text, metadata, gold, input_paths, provider in prepared:
        document, type_scores, technique_audit = _c4_document(
            dataset=dataset,
            responses_dir=responses_dir,
            text_path=text_path,
            text=text,
            metadata=metadata,
            gold=gold,
            provider=provider,
            query=queries[text_path.stem],
            tlp=tlp,
            attack_catalog=attack_catalog,
        )
        dataset_paths.extend(input_paths)
        documents.append(document)
        scores_by_mode[document["result_mode"]].append(_score_from_dict(document["score"]))
        for ioc_type, type_score in type_scores.items():
            scores_by_type.setdefault(ioc_type, []).append(type_score)
        _add_ttp_counts(ttp_counts, technique_audit)
    all_scores = [_score_from_dict(document["score"]) for document in documents]
    return {
        "schema_version": "1.2",
        "config": "C4",
        "purpose": "synthetic-smoke",
        "dataset_sha256": _dataset_hash(dataset, dataset_paths),
        "fixture_manifest_sha256": _dataset_hash(responses_dir, fixture_paths),
        "query_manifest_sha256": query_manifest.raw_sha256,
        "provider_policy": {"destination": "fake_offline", "egress": False},
        "mock_only": True,
        "evaluator": {"git_ref": _git_ref(), "python": platform.python_version()},
        "document_count": len(documents),
        "documents": documents,
        "micro_all": _score_dict(micro_average(all_scores)),
        "micro_by_result_mode": {
            mode: _not_available_or_micro(scores_by_mode[mode])
            for mode in ("model_completed", "regex_fallback")
        },
        "by_type": {
            ioc_type: _score_dict(micro_average(scores))
            for ioc_type, scores in sorted(scores_by_type.items())
        },
        "ttp_audit": {
            "enabled": True,
            "catalog": _catalog_projection(attack_catalog),
            "metric_note": "counts only; not TTP precision, recall, F1, or detection rate",
            "counts": ttp_counts,
        },
        "limitations": list(C4_LIMITATIONS),
    }


def _check_c4_bounds(value: Any, depth: int = 1) -> None:
    if depth > 64:
        raise DatasetError("C4 artifact vượt giới hạn")
    if value is None or type(value) in (bool, int, float):
        return
    if type(value) is str:
        if len(value) > 8192:
            raise DatasetError("C4 artifact vượt giới hạn")
        return
    if type(value) is list:
        if len(value) > 512:
            raise DatasetError("C4 artifact vượt giới hạn")
        for item in value:
            _check_c4_bounds(item, depth + 1)
        return
    if type(value) is dict:
        if len(value) > 64 or any(type(key) is not str for key in value):
            raise DatasetError("C4 artifact vượt giới hạn")
        for item in value.values():
            _check_c4_bounds(item, depth + 1)
        return
    raise DatasetError("C4 artifact không hợp lệ")


def _c4_json_bytes(value: dict[str, Any]) -> bytes:
    _check_c4_bounds(value)
    from eval.report import InvalidInput as ReportInvalidInput
    from eval.report import _validate_c4

    try:
        _validate_c4(value)
    except ReportInvalidInput as exc:
        raise DatasetError("C4 artifact không hợp lệ") from exc
    try:
        raw = (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise DatasetError("C4 artifact không hợp lệ") from exc
    if len(raw) > 1_048_576:
        raise DatasetError("C4 artifact vượt giới hạn")
    return raw


def _write_c4_json_no_clobber(path: Path, value: dict[str, Any]) -> None:
    raw = _c4_json_bytes(value)
    if path.exists():
        raise DatasetError("output đã tồn tại")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise DatasetError("output đã tồn tại") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _ensure_output_safe(output: Path, dataset: Path, responses_dir: Path, inputs: list[Path]) -> None:
    output_resolved = output.resolve()
    for root in (dataset.resolve(), responses_dir.resolve()):
        if output_resolved == root or output_resolved.is_relative_to(root):
            raise DatasetError("output path không an toàn")
    if output.exists():
        for path in inputs:
            if path.exists() and output.samefile(path):
                raise DatasetError("output path không an toàn")


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp_name = handle.name
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--config", required=True, choices=("C1", "C2", "C3", "C4"))
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--responses-dir", type=Path)
    parser.add_argument(
        "--tlp",
        choices=("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"),
    )
    parser.add_argument("--ttp-audit", action="store_true")
    parser.add_argument("--attack-snapshot", type=Path)
    parser.add_argument("--attack-pin", type=Path)
    parser.add_argument("--query-manifest", type=Path)
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    audit_flags = (args.ttp_audit, args.attack_snapshot is not None, args.attack_pin is not None)
    audit_requested = any(audit_flags)
    audit_complete = all(audit_flags)
    if args.config != "C4" and audit_requested and not audit_complete:
        print("Lỗi: ttp-audit cần attack-snapshot và attack-pin", file=sys.stderr)
        return 2
    if args.config == "C1" and (
        args.responses_dir is not None
        or args.tlp is not None
        or audit_requested
        or args.query_manifest is not None
    ):
        print("Lỗi: C1 không nhận responses-dir/tlp/ttp-audit", file=sys.stderr)
        return 2
    if args.config in {"C2", "C3"} and (
        args.responses_dir is None or args.tlp is None or args.query_manifest is not None
    ):
        print("Lỗi: C2/C3 cần responses-dir và tlp", file=sys.stderr)
        return 2
    if args.config == "C4" and (
        args.responses_dir is None
        or args.tlp is None
        or args.attack_snapshot is None
        or args.attack_pin is None
        or args.query_manifest is None
        or args.ttp_audit
    ):
        print("Lỗi: C4 cần responses-dir/tlp/attack-snapshot/attack-pin/query-manifest", file=sys.stderr)
        return 2
    if args.config == "C1":
        try:
            result = evaluate_dataset(args.dataset.resolve())
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except (DatasetError, OSError) as exc:
            print(f"Lỗi: {exc}", file=sys.stderr)
            return 1
        print(f"Đã chấm {result['document_count']} báo cáo C1: {args.output}")
        return 0

    try:
        dataset = args.dataset.resolve()
        responses_dir = args.responses_dir.resolve()
        input_paths: list[Path] = [
            *dataset.rglob("*"),
            *responses_dir.rglob("*"),
        ]
        if args.config == "C4":
            input_paths.extend((args.attack_snapshot, args.attack_pin, args.query_manifest))
        elif audit_complete:
            input_paths.extend((args.attack_snapshot, args.attack_pin))
        _ensure_output_safe(
            args.output, dataset, responses_dir, [path for path in input_paths if path.is_file()]
        )
        if args.config == "C4" and args.output.exists():
            raise DatasetError("output đã tồn tại")
        attack_catalog = None
        query_manifest = None
        if args.config == "C4":
            query_manifest = load_c4_query_manifest(args.query_manifest)
            pin = _load_snapshot_pin(args.attack_pin)
            attack_catalog = load_catalog(args.attack_snapshot, pin)
        elif audit_complete:
            pin = _load_snapshot_pin(args.attack_pin)
            attack_catalog = load_catalog(args.attack_snapshot, pin)
        if args.config == "C4":
            result = evaluate_c4_dataset(
                dataset,
                responses_dir,
                tlp=args.tlp,
                attack_catalog=attack_catalog,
                query_manifest=query_manifest,
            )
            _write_c4_json_no_clobber(args.output, result)
        else:
            result = evaluate_llm_dataset(
                dataset,
                responses_dir,
                config=args.config,
                tlp=args.tlp,
                attack_catalog=attack_catalog,
            )
            _write_json_atomic(args.output, result)
    except (
        AdapterError,
        AttackCatalogError,
        AttackRetrievalError,
        DatasetError,
        OSError,
        TtpAuditError,
        UnicodeError,
    ):
        print("Lỗi: offline_eval_failed", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "config": args.config,
                "document_count": result["document_count"],
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
