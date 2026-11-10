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
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_core.extract import extract_iocs  # noqa: E402
from phonghoa_core.ioc import Ioc, normalize  # noqa: E402
from phonghoa_extractor.evaluate import Score, micro_average, score_iocs  # noqa: E402
from phonghoa_extractor.llm_adapter import AdapterError, run_extraction  # noqa: E402
from phonghoa_extractor.llm_fixture import load_scripted_provider  # noqa: E402


class DatasetError(ValueError):
    """Dataset không đúng cấu trúc smoke đã công bố."""


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
    if item["role"] not in {"attacker", "victim", "benign"}:
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


def evaluate_llm_dataset(dataset: Path, responses_dir: Path, *, config: str, tlp: str) -> dict[str, Any]:
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
        documents.append(document)

    all_scores = [_score_from_dict(document["score"]) for document in documents]
    return {
        "schema_version": "1.0",
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
        "limitations": [
            "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
            "C3 adapter merges model candidates with regex extraction before grounding; "
            "scores are not model-only.",
            "Semantic TTP, malware, and actor items are not evaluated.",
        ],
    }


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, choices=("C1", "C2", "C3", "C4"))
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--responses-dir", type=Path)
    parser.add_argument(
        "--tlp",
        choices=("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"),
    )
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    if args.config == "C4":
        print("Lỗi: cấu hình C4 chưa được hỗ trợ", file=sys.stderr)
        return 2
    if args.config == "C1" and (args.responses_dir is not None or args.tlp is not None):
        print("Lỗi: C1 không nhận responses-dir/tlp", file=sys.stderr)
        return 2
    if args.config in {"C2", "C3"} and (args.responses_dir is None or args.tlp is None):
        print("Lỗi: C2/C3 cần responses-dir và tlp", file=sys.stderr)
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
        input_paths = [
            *dataset.rglob("*"),
            *responses_dir.rglob("*"),
        ]
        _ensure_output_safe(
            args.output, dataset, responses_dir, [path for path in input_paths if path.is_file()]
        )
        result = evaluate_llm_dataset(
            dataset,
            responses_dir,
            config=args.config,
            tlp=args.tlp,
        )
        _write_json_atomic(args.output, result)
    except (AdapterError, DatasetError, OSError, UnicodeError):
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
