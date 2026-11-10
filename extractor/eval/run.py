"""Chạy baseline C1 ngoại tuyến trên dataset theo GUIDELINE."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_core.extract import extract_iocs  # noqa: E402
from phonghoa_core.ioc import Ioc, normalize  # noqa: E402
from phonghoa_extractor.evaluate import Score, micro_average, score_iocs  # noqa: E402


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, choices=("C1", "C2", "C3", "C4"))
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    if args.config != "C1":
        print(f"Lỗi: cấu hình {args.config} chưa được hỗ trợ; chỉ có C1 ngoại tuyến", file=sys.stderr)
        return 2
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


if __name__ == "__main__":
    raise SystemExit(main())
