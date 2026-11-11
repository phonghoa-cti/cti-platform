"""Dựng báo cáo Markdown bất biến từ artifact evaluator X01 tổng hợp."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

MAX_BYTES = 1_048_576
MAX_DEPTH = 64
MAX_OBJECT = 64
MAX_ARRAY = 512
MAX_STRING = 8_192
MAX_DOCUMENTS = 256
MAX_INT = 9_223_372_036_854_775_807
CONFIG_ORDER = {"C1": 0, "C2": 1, "C3": 2}
IOC_TYPES = frozenset(("ipv4", "ipv6", "domain", "url", "email", "md5", "sha1", "sha256"))
MODES = ("model_completed", "regex_fallback")
QUOTE_STATUSES = ("matched", "missing", "not_found", "ambiguous")
CATALOG_STATUSES = ("active", "inactive", "unknown", "not_checked")
HASH_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)
REF_RE = re.compile(r"[0-9a-f]{40}", re.ASCII)
PYTHON_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)
VERSION_RE = re.compile(r"[A-Za-z0-9._-]{1,64}", re.ASCII)
LIMITATIONS_10 = [
    "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
    "C3 adapter merges model candidates with regex extraction before grounding; scores are not model-only.",
    "Semantic TTP, malware, and actor items are not evaluated.",
]
LIMITATIONS_11 = LIMITATIONS_10 + [
    "TTP audit reports source, quote, and catalog consistency only; semantic TTP and C4 remain unverified."
]
SCORE_KEYS = frozenset(("tp", "fp", "fn", "precision", "recall", "f1"))
C1_ROOT_KEYS = frozenset(
    (
        "schema_version",
        "config",
        "purpose",
        "dataset_sha256",
        "document_count",
        "documents",
        "micro",
        "by_type",
        "ttp",
    )
)
C1_DOCUMENT_KEYS = frozenset(("id", "language", "prediction", "score", "source"))
C23_ROOT_10_KEYS = frozenset(
    (
        "schema_version",
        "config",
        "purpose",
        "dataset_sha256",
        "fixture_manifest_sha256",
        "provider_policy",
        "mock_only",
        "evaluator",
        "document_count",
        "documents",
        "micro_all",
        "micro_by_result_mode",
        "by_type",
        "limitations",
    )
)
C23_COMMON_DOCUMENT_KEYS = frozenset(
    (
        "id",
        "config",
        "language",
        "tlp",
        "source",
        "fixture",
        "adapter_schema_version",
        "provider",
        "attempts",
        "result_mode",
        "error_codes",
        "model_items_used",
        "operational_draft_eligible",
        "prediction_basis",
        "prediction",
        "score",
    )
)
AUDIT_ITEM_KEYS = frozenset(
    (
        "item_index",
        "kind",
        "value",
        "evidence",
        "evidence_span",
        "source_sha256",
        "config",
        "quote_status",
        "catalog_status",
        "reason_code",
        "pin_kind",
        "snapshot_version",
        "snapshot_sha256",
        "semantic_status",
        "operational_draft_eligible",
    )
)
CATALOG_KEYS = frozenset(("kind", "version", "sha256", "source_url", "release_tag", "commit", "provenance"))


class InvalidInput(ValueError):
    pass


class InputIoError(OSError):
    pass


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise InvalidInput from None


@dataclass(frozen=True)
class LoadedArtifact:
    value: dict[str, Any]
    digest: str
    path: Path


def _exact_keys(value: object, keys: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != keys:
        raise InvalidInput
    return value


def _string(value: object, *, nonempty: bool = False) -> str:
    if type(value) is not str or len(value) > MAX_STRING or (nonempty and not value):
        raise InvalidInput
    return value


def _integer(value: object, *, maximum: int = MAX_INT) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise InvalidInput
    return value


def _boolean(value: object) -> bool:
    if type(value) is not bool:
        raise InvalidInput
    return value


def _hash(value: object) -> str:
    text = _string(value, nonempty=True)
    if HASH_RE.fullmatch(text) is None:
        raise InvalidInput
    return text


def _walk_bounds(value: object, depth: int = 1) -> None:
    if depth > MAX_DEPTH:
        raise InvalidInput
    if value is None or type(value) in (bool, int, float):
        if type(value) is int:
            _integer(value)
        elif type(value) is float and (not math.isfinite(value) or not 0 <= value <= 1):
            raise InvalidInput
        return
    if type(value) is str:
        _string(value)
        return
    if type(value) is list:
        if len(value) > MAX_ARRAY:
            raise InvalidInput
        for item in value:
            _walk_bounds(item, depth + 1)
        return
    if type(value) is dict:
        if len(value) > MAX_OBJECT:
            raise InvalidInput
        for key, item in value.items():
            _string(key)
            _walk_bounds(item, depth + 1)
        return
    raise InvalidInput


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput
        result[key] = value
    return result


def _parse_int(text: str) -> int:
    digits = text.removeprefix("-")
    if len(digits) > 19:
        raise InvalidInput
    value = int(text)
    return _integer(value)


def _reject_constant(value: str) -> NoReturn:
    raise InvalidInput


def _read_artifact(path_operand: str) -> LoadedArtifact:
    try:
        path = Path(path_operand).resolve(strict=True)
        if not stat.S_ISREG(path.stat().st_mode):
            raise InvalidInput
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except InvalidInput:
        raise
    except (OSError, RuntimeError) as error:
        raise InputIoError from error
    if len(raw) > MAX_BYTES:
        raise InvalidInput
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InvalidInput
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_int=_parse_int,
            parse_constant=_reject_constant,
        )
    except InvalidInput:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise InvalidInput from error
    _walk_bounds(value)
    if type(value) is not dict:
        raise InvalidInput
    return LoadedArtifact(value=value, digest=hashlib.sha256(raw).hexdigest(), path=path)


def _score(value: object) -> dict[str, Any]:
    result = _exact_keys(value, SCORE_KEYS)
    tp, fp, fn = (_integer(result[key]) for key in ("tp", "fp", "fn"))
    metrics = []
    for key in ("precision", "recall", "f1"):
        metric = result[key]
        if type(metric) not in (int, float) or type(metric) is bool:
            raise InvalidInput
        metric = float(metric)
        if not math.isfinite(metric) or not 0 <= metric <= 1:
            raise InvalidInput
        metrics.append(metric)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    if any(
        not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
        for actual, expected in zip(metrics, (precision, recall, f1), strict=True)
    ):
        raise InvalidInput
    return result


def _metadata_file(value: object) -> None:
    item = _exact_keys(value, frozenset(("path", "sha256")))
    _string(item["path"], nonempty=True)
    _hash(item["sha256"])


def _prediction(value: object) -> None:
    if type(value) is not dict:
        raise InvalidInput


def _validate_by_type(value: object) -> None:
    if type(value) is not dict or not set(value).issubset(IOC_TYPES):
        raise InvalidInput
    for item in value.values():
        _score(item)


def _sum_scores(documents: list[dict[str, Any]]) -> tuple[int, int, int]:
    return tuple(sum(document["score"][key] for document in documents) for key in ("tp", "fp", "fn"))  # type: ignore[return-value]


def _score_counts(value: object) -> tuple[int, int, int]:
    item = _score(value)
    return item["tp"], item["fp"], item["fn"]


def _validate_c1(root: dict[str, Any]) -> None:
    _exact_keys(root, C1_ROOT_KEYS)
    if root["schema_version"] != "1.0" or root["config"] != "C1" or root["purpose"] != "synthetic-smoke":
        raise InvalidInput
    _hash(root["dataset_sha256"])
    count = _integer(root["document_count"], maximum=MAX_DOCUMENTS)
    documents = root["documents"]
    if type(documents) is not list or len(documents) != count:
        raise InvalidInput
    ids: set[str] = set()
    for document in documents:
        item = _exact_keys(document, C1_DOCUMENT_KEYS)
        identifier = _string(item["id"], nonempty=True)
        if identifier in ids:
            raise InvalidInput
        ids.add(identifier)
        _string(item["language"], nonempty=True)
        _prediction(item["prediction"])
        _score(item["score"])
        _metadata_file(item["source"])
    if _score_counts(root["micro"]) != _sum_scores(documents):
        raise InvalidInput
    _validate_by_type(root["by_type"])
    if root["ttp"] != {"status": "not_evaluated"}:
        raise InvalidInput


def _validate_audit_item(value: object, config: str) -> tuple[str, str]:
    item = _exact_keys(value, AUDIT_ITEM_KEYS)
    _integer(item["item_index"])
    for key in ("kind", "value", "evidence", "reason_code", "pin_kind", "snapshot_version"):
        _string(item[key])
    span = item["evidence_span"]
    if span is not None and (
        type(span) is not list or len(span) != 2 or any(type(part) is not int or part < 0 for part in span)
    ):
        raise InvalidInput
    _hash(item["source_sha256"])
    _hash(item["snapshot_sha256"])
    if (
        item["config"] != config
        or item["quote_status"] not in QUOTE_STATUSES
        or item["catalog_status"] not in CATALOG_STATUSES
    ):
        raise InvalidInput
    if item["semantic_status"] != "unverified" or item["operational_draft_eligible"] is not False:
        raise InvalidInput
    return item["quote_status"], item["catalog_status"]


def _validate_catalog(value: object) -> dict[str, Any]:
    catalog = _exact_keys(value, CATALOG_KEYS)
    if catalog["kind"] not in ("synthetic", "official"):
        raise InvalidInput
    version = _string(catalog["version"], nonempty=True)
    if VERSION_RE.fullmatch(version) is None:
        raise InvalidInput
    _hash(catalog["sha256"])
    for key in ("source_url", "release_tag", "commit", "provenance"):
        if catalog[key] is not None:
            _string(catalog[key])
    if catalog["commit"] is not None and REF_RE.fullmatch(catalog["commit"]) is None:
        raise InvalidInput
    return catalog


def _validate_provider_evaluator(root: dict[str, Any]) -> None:
    policy = _exact_keys(root["provider_policy"], frozenset(("destination", "egress")))
    if (
        policy["destination"] != "fake_offline"
        or _boolean(policy["egress"]) is not False
        or root["mock_only"] is not True
    ):
        raise InvalidInput
    evaluator = _exact_keys(root["evaluator"], frozenset(("git_ref", "python")))
    if (
        REF_RE.fullmatch(_string(evaluator["git_ref"], nonempty=True)) is None
        or PYTHON_RE.fullmatch(_string(evaluator["python"], nonempty=True)) is None
    ):
        raise InvalidInput


def _validate_document_provider(value: object) -> None:
    provider = _exact_keys(value, frozenset(("name", "model_id", "destination", "egress")))
    if provider["destination"] != "fake_offline" or _boolean(provider["egress"]) is not False:
        raise InvalidInput
    _string(provider["name"], nonempty=True)
    _string(provider["model_id"], nonempty=True)


def _validate_c23_document(
    document: object, config: str, schema: str, ids: set[str]
) -> tuple[str, list[tuple[str, str]]]:
    audit_key = "raw_audit" if config == "C2" else "grounding_audit"
    keys = C23_COMMON_DOCUMENT_KEYS | {audit_key} | ({"ttp_audit"} if schema == "1.1" else set())
    item = _exact_keys(document, frozenset(keys))
    identifier = _string(item["id"], nonempty=True)
    if identifier in ids or item["config"] != config:
        raise InvalidInput
    ids.add(identifier)
    for key in ("language", "tlp", "adapter_schema_version", "prediction_basis"):
        _string(item[key], nonempty=True)
    _validate_document_provider(item["provider"])
    _metadata_file(item["source"])
    _metadata_file(item["fixture"])
    _integer(item["attempts"])
    if item["result_mode"] not in MODES:
        raise InvalidInput
    if type(item["error_codes"]) is not list or any(type(code) is not str for code in item["error_codes"]):
        raise InvalidInput
    _boolean(item["model_items_used"])
    _boolean(item["operational_draft_eligible"])
    _prediction(item["prediction"])
    _score(item["score"])
    if type(item[audit_key]) is not list or any(type(audit) is not dict for audit in item[audit_key]):
        raise InvalidInput
    if schema != "1.1":
        return item["result_mode"], []
    if type(item["ttp_audit"]) is not list:
        raise InvalidInput
    return item["result_mode"], [_validate_audit_item(audit, config) for audit in item["ttp_audit"]]


def _validate_c23_documents(
    documents: list[dict[str, Any]], config: str, schema: str
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int], dict[str, int], int]:
    modes: dict[str, list[dict[str, Any]]] = {mode: [] for mode in MODES}
    quote_counts = {status: 0 for status in QUOTE_STATUSES}
    catalog_counts = {status: 0 for status in CATALOG_STATUSES}
    ids: set[str] = set()
    technique_items = 0
    for document in documents:
        mode, audits = _validate_c23_document(document, config, schema, ids)
        modes[mode].append(document)
        for quote, catalog in audits:
            quote_counts[quote] += 1
            catalog_counts[catalog] += 1
            technique_items += 1
    return modes, quote_counts, catalog_counts, technique_items


def _validate_modes(value: object, mode_documents: dict[str, list[dict[str, Any]]]) -> None:
    modes = _exact_keys(value, frozenset(MODES))
    for mode in MODES:
        group = mode_documents[mode]
        if not group and modes[mode] != {"status": "not_available"}:
            raise InvalidInput
        if group and _score_counts(modes[mode]) != _sum_scores(group):
            raise InvalidInput


def _validate_ttp_top(
    value: object, technique_items: int, quote_counts: dict[str, int], catalog_counts: dict[str, int]
) -> None:
    top = _exact_keys(value, frozenset(("enabled", "catalog", "metric_note", "counts")))
    if (
        top["enabled"] is not True
        or top["metric_note"] != "counts only; not TTP precision, recall, F1, or detection rate"
    ):
        raise InvalidInput
    _validate_catalog(top["catalog"])
    counts = _exact_keys(top["counts"], frozenset(("technique_items", "quote_status", "catalog_status")))
    if (
        counts["technique_items"] != technique_items
        or counts["quote_status"] != quote_counts
        or counts["catalog_status"] != catalog_counts
    ):
        raise InvalidInput


def _validate_c23(root: dict[str, Any]) -> None:
    schema = root.get("schema_version")
    expected_root = C23_ROOT_10_KEYS | ({"ttp_audit"} if schema == "1.1" else set())
    _exact_keys(root, frozenset(expected_root))
    config = root["config"]
    if schema not in ("1.0", "1.1") or config not in ("C2", "C3") or root["purpose"] != "synthetic-smoke":
        raise InvalidInput
    _hash(root["dataset_sha256"])
    _hash(root["fixture_manifest_sha256"])
    _validate_provider_evaluator(root)
    count = _integer(root["document_count"], maximum=MAX_DOCUMENTS)
    documents = root["documents"]
    if type(documents) is not list or len(documents) != count:
        raise InvalidInput
    modes, quote_counts, catalog_counts, technique_items = _validate_c23_documents(documents, config, schema)
    if _score_counts(root["micro_all"]) != _sum_scores(documents):
        raise InvalidInput
    _validate_modes(root["micro_by_result_mode"], modes)
    _validate_by_type(root["by_type"])
    if root["limitations"] != (LIMITATIONS_11 if schema == "1.1" else LIMITATIONS_10):
        raise InvalidInput
    if schema == "1.1":
        _validate_ttp_top(root["ttp_audit"], technique_items, quote_counts, catalog_counts)


def _validate_cohort(artifacts: list[LoadedArtifact]) -> list[LoadedArtifact]:
    if not 1 <= len(artifacts) <= 3:
        raise InvalidInput
    seen: set[str] = set()
    for artifact in artifacts:
        config = artifact.value.get("config")
        if config in seen:
            raise InvalidInput
        seen.add(config)
        if config == "C1":
            _validate_c1(artifact.value)
        else:
            _validate_c23(artifact.value)
    ordered = sorted(artifacts, key=lambda artifact: CONFIG_ORDER.get(artifact.value.get("config"), 99))
    if any(item.value.get("config") not in CONFIG_ORDER for item in ordered):
        raise InvalidInput
    schemas = {item.value["schema_version"] for item in ordered}
    if len(schemas) != 1 or ("C1" in seen and schemas != {"1.0"}):
        raise InvalidInput
    first = ordered[0].value
    for item in ordered[1:]:
        value = item.value
        for key in ("purpose", "dataset_sha256", "document_count"):
            if value[key] != first[key]:
                raise InvalidInput
    c23 = [item.value for item in ordered if item.value["config"] in ("C2", "C3")]
    if len(c23) == 2:
        for key in ("fixture_manifest_sha256", "provider_policy", "mock_only", "evaluator"):
            if c23[0][key] != c23[1][key]:
                raise InvalidInput
        if schemas == {"1.1"} and c23[0]["ttp_audit"]["catalog"] != c23[1]["ttp_audit"]["catalog"]:
            raise InvalidInput
    return ordered


def _metric_row(config: str, score: dict[str, Any], count: int) -> str:
    return (
        f"| {config} | {count} | {score['tp']} | {score['fp']} | {score['fn']} | "
        f"{float(score['precision']):.6f} | {float(score['recall']):.6f} | {float(score['f1']):.6f} |"
    )


def _render_provenance(artifacts: list[LoadedArtifact], c23: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Provenance",
        "",
        "| Config | Schema | Documents | Dataset SHA-256 | Input SHA-256 |",
        "|---|---:|---:|---|---|",
    ]
    for item in artifacts:
        value = item.value
        lines.append(
            f"| {value['config']} | {value['schema_version']} | {value['document_count']} | "
            f"`{value['dataset_sha256']}` | `{item.digest}` |"
        )
    lines.extend(("", "- C1: evaluator/provider/fixture không có trong schema C1."))
    if c23:
        value = c23[0]
        lines.append(
            f"- C2/C3 fixture manifest: `{value['fixture_manifest_sha256']}`; evaluator "
            f"`{value['evaluator']['git_ref']}` / Python `{value['evaluator']['python']}`; "
            "provider `fake_offline`, egress `false`."
        )
        if value["schema_version"] == "1.1":
            catalog = value["ttp_audit"]["catalog"]
            lines.append(
                f"- ATT&CK catalog: `{catalog['kind']}` / `{catalog['version']}` / `{catalog['sha256']}`."
            )
    return lines


def _render_aggregate(artifacts: list[LoadedArtifact]) -> list[str]:
    lines = [
        "## IOC aggregate",
        "",
        "| Config | Documents | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in artifacts:
        value = item.value
        lines.append(
            _metric_row(
                value["config"],
                value["micro"] if value["config"] == "C1" else value["micro_all"],
                value["document_count"],
            )
        )
    lines.extend(("", "C3: grounded model candidates + regex; not model-only."))
    return lines


def _render_modes(c23: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Result modes",
        "",
        "| Config | Mode | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for value in c23:
        for mode in MODES:
            mode_score = value["micro_by_result_mode"][mode]
            if mode_score == {"status": "not_available"}:
                lines.append(
                    f"| {value['config']} | {mode} | not_available | not_available | "
                    "not_available | not_available | not_available | not_available |"
                )
            else:
                lines.append(
                    f"| {value['config']} | {mode} | {mode_score['tp']} | {mode_score['fp']} | "
                    f"{mode_score['fn']} | {float(mode_score['precision']):.6f} | "
                    f"{float(mode_score['recall']):.6f} | {float(mode_score['f1']):.6f} |"
                )
    return lines


def _render_by_type(artifacts: list[LoadedArtifact]) -> list[str]:
    lines = [
        "## IOC by type",
        "",
        "| Config | Type | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in artifacts:
        value = item.value
        for ioc_type in sorted(value["by_type"]):
            item_score = value["by_type"][ioc_type]
            lines.append(
                f"| {value['config']} | {ioc_type} | {item_score['tp']} | {item_score['fp']} | "
                f"{item_score['fn']} | {float(item_score['precision']):.6f} | "
                f"{float(item_score['recall']):.6f} | {float(item_score['f1']):.6f} |"
            )
    return lines


def _render_ttp(c23: list[dict[str, Any]]) -> list[str]:
    if not c23 or c23[0]["schema_version"] != "1.1":
        return []
    lines = [
        "## TTP consistency counts",
        "",
        "> Counts chỉ kiểm tra source/quote/catalog consistency; "
        "không phải Precision/Recall/F1 hay semantic truth.",
        "",
        "| Config | Technique items | matched | missing | not_found | ambiguous | "
        "active | inactive | unknown | not_checked |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for value in c23:
        counts = value["ttp_audit"]["counts"]
        quote, catalog = counts["quote_status"], counts["catalog_status"]
        lines.append(
            f"| {value['config']} | {counts['technique_items']} | {quote['matched']} | "
            f"{quote['missing']} | {quote['not_found']} | {quote['ambiguous']} | "
            f"{catalog['active']} | {catalog['inactive']} | {catalog['unknown']} | "
            f"{catalog['not_checked']} |"
        )
    return lines


def _render(artifacts: list[LoadedArtifact]) -> bytes:
    c23 = [item.value for item in artifacts if item.value["config"] in ("C2", "C3")]
    lines = [
        "# Báo cáo đánh giá X01",
        "",
        "> **SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật.**",
        "",
    ]
    for section in (
        _render_provenance(artifacts, c23),
        _render_aggregate(artifacts),
        _render_modes(c23),
        _render_by_type(artifacts),
        _render_ttp(c23),
    ):
        if section:
            lines.extend(section + [""])
    lines.extend(
        [
            "## Giới hạn",
            "",
            "- Chỉ là smoke tổng hợp với provider giả lập; chưa đo model hoặc corpus thật.",
            "- C3 trộn candidate model với regex trước grounding, nên không phải metric model-only.",
            "- TTP chỉ có consistency counts; semantic TTP, C4/RAG, W05, OpenCTI, "
            "lab và production chưa được xác minh.",
            "",
            "---",
            "Định dạng: `phonghoa-x01-eval-report/1`.",
        ]
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _output_alias(output: Path, inputs: list[LoadedArtifact]) -> bool:
    lexical = os.path.normcase(os.path.abspath(output))
    for item in inputs:
        if lexical == os.path.normcase(os.path.abspath(item.path)):
            return True
    if output.exists():
        try:
            return any(os.path.samefile(output, item.path) for item in inputs)
        except OSError as error:
            raise InputIoError from error
    try:
        resolved = output.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise InputIoError from error
    return any(resolved == item.path for item in inputs)


def _publish(
    output_operand: str, content: bytes, artifacts: list[LoadedArtifact], *, overwrite: bool
) -> None:
    output = Path(output_operand)
    if output.exists() and output.is_dir():
        raise InvalidInput
    if _output_alias(output, artifacts):
        raise InvalidInput
    if output.exists() and not overwrite:
        raise InvalidInput
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
        temp = Path(temp_name)
    except OSError as error:
        raise InputIoError from error
    committed = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temp, output)
        else:
            os.link(temp, output)
        committed = True
    except FileExistsError as error:
        raise InvalidInput from error
    except OSError as error:
        raise InputIoError from error
    finally:
        try:
            if temp.exists():
                temp.unlink()
        except OSError as error:
            if committed:
                raise InputIoError from error


def _parser() -> SafeParser:
    parser = SafeParser(description="Dựng báo cáo Markdown X01 offline", allow_abbrev=False)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not 1 <= len(args.input) <= 3:
            raise InvalidInput
        loaded = [_read_artifact(path) for path in args.input]
        artifacts = _validate_cohort(loaded)
        content = _render(artifacts)
        _publish(args.output, content, artifacts, overwrite=args.overwrite)
    except InputIoError:
        print("Lỗi: eval_report_io_failed", file=sys.stderr)
        return 1
    except (InvalidInput, KeyError, TypeError, OverflowError):
        print("Lỗi: eval_report_invalid_input", file=sys.stderr)
        return 2
    result = {"configs": [item.value["config"] for item in artifacts], "output": args.output}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
