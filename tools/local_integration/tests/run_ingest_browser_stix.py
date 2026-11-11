"""Điều khiển seed X01 → browser W05 → hậu kiểm STIX trên cùng SQLite."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- executable harness bootstraps repository packages

import argparse
import hashlib
import json
import queue
import shutil
import sys
import tempfile
import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, TextIO

ROOT = Path(__file__).resolve().parents[3]
for package_root in (ROOT, ROOT / "core", ROOT / "extractor"):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

from phonghoa_extractor.ingest_queue import (
    _validate_envelope,
    get_ingest_provenance,
    load_ingest_envelope,
)
from phonghoa_extractor import store
from tools.local_integration.runner import E2E_SOURCE_BYTES, LocalRun, seed_ingest_fixture
from tools.local_integration.tests.run_stix_e2e import database_state, file_inventory, run_export

BUNDLE_KEYS = {"type", "id", "objects"}
COMMON_SCO_KEYS = {"type", "spec_version", "id", "object_marking_refs"}
VALUE_SCO_TYPES = {"ipv4-addr", "ipv6-addr", "domain-name", "url", "email-addr"}
OBJECT_KEYS = {
    "marking-definition": {
        "type",
        "spec_version",
        "id",
        "created",
        "name",
        "definition_type",
        "definition",
    },
    "identity": {
        "type",
        "spec_version",
        "id",
        "created",
        "modified",
        "name",
        "identity_class",
        "object_marking_refs",
    },
    "file": COMMON_SCO_KEYS | {"hashes"},
    "report": {
        "type",
        "spec_version",
        "id",
        "created_by_ref",
        "created",
        "modified",
        "name",
        "description",
        "published",
        "report_types",
        "object_refs",
        "object_marking_refs",
        "external_references",
    },
}
PROVENANCE_KEYS = {
    "format_version",
    "source_sha256",
    "payload_sha256",
    "draft_id",
    "approved_audit_id",
    "review_version",
    "selection_version",
    "selected_indices",
    "selected_sha256",
    "decided_at",
    "exporter_config_sha256",
    "source_tlp",
    "stix_tlp",
}
PRIVATE_MARKER_KEYS = {
    "source_name",
    "raw_source",
    "evidence",
    "creator_subject",
    "reviewer_subject",
}


@dataclass(frozen=True)
class BrowserCasePlan:
    scenario: str
    expected_eligible_indices: tuple[int, ...]
    expected_selected_indices: tuple[int, ...]
    expected_selection_events: tuple[tuple[int, ...], ...]
    outcome: str


def browser_case_plan(input_kind: str, case: str) -> BrowserCasePlan:
    """Trả kỳ vọng literal của fixture, không suy ra từ kết quả importer."""

    plans = {
        ("txt", "happy"): BrowserCasePlan("ingest-browser-stix", (0, 1), (1,), ((1,),), "approved"),
        ("pdf", "happy"): BrowserCasePlan("ingest-browser-stix", (0,), (0,), ((), (0,)), "approved"),
        ("txt", "self-approve"): BrowserCasePlan("ingest-browser-self-approve", (0, 1), (0, 1), (), "denied"),
        ("txt", "save-refresh-503"): BrowserCasePlan(
            "ingest-browser-save-refresh-503", (0, 1), (1,), ((1,),), "pending"
        ),
        ("txt", "decision-refresh-503"): BrowserCasePlan(
            "ingest-browser-decision-refresh-503", (0, 1), (1,), ((1,),), "approved"
        ),
    }
    try:
        return plans[(input_kind, case)]
    except KeyError:
        raise RuntimeError("case browser không hỗ trợ input này") from None


def _iter_json_strings(value: Any) -> Iterator[str]:
    """Duyệt chuỗi semantic sau JSON parse, độc lập escape và whitespace."""

    if type(value) is str:
        yield value
    elif type(value) is list:
        for item in value:
            yield from _iter_json_strings(item)
    elif type(value) is dict:
        for key, item in value.items():
            yield key
            yield from _iter_json_strings(item)


def _validate_bundle_allowlist(bundle: Any) -> None:
    if type(bundle) is not dict or set(bundle) != BUNDLE_KEYS or type(bundle.get("objects")) is not list:
        raise RuntimeError("bundle structure ngoài allowlist")
    for item in bundle["objects"]:
        if type(item) is not dict or type(item.get("type")) is not str:
            raise RuntimeError("bundle object ngoài allowlist")
        object_type = item["type"]
        expected_keys = (
            COMMON_SCO_KEYS | {"value"} if object_type in VALUE_SCO_TYPES else OBJECT_KEYS.get(object_type)
        )
        if expected_keys is None or set(item) != expected_keys:
            raise RuntimeError("bundle object ngoài allowlist")
        if object_type == "marking-definition" and (
            type(item["definition"]) is not dict or set(item["definition"]) != {"tlp"}
        ):
            raise RuntimeError("bundle marking ngoài allowlist")
        if object_type == "file" and (
            type(item["hashes"]) is not dict
            or len(item["hashes"]) != 1
            or not set(item["hashes"]).issubset({"MD5", "SHA-1", "SHA-256"})
        ):
            raise RuntimeError("bundle file ngoài allowlist")
        if object_type == "report":
            references = item["external_references"]
            if (
                type(references) is not list
                or len(references) != 1
                or type(references[0]) is not dict
                or set(references[0]) != {"source_name", "external_id", "description"}
            ):
                raise RuntimeError("bundle reference ngoài allowlist")


def _privacy_markers(input_kind: str, source: Path, reviewer_subject: str) -> dict[str, str]:
    content_markers = (
        ("Cảnh báo thử nghiệm 😀", "ghi nhận") if input_kind == "txt" else ("Page one IOC", "Page two domain")
    )
    return {
        "source_name": source.name,
        "raw_source": content_markers[0],
        "evidence": content_markers[1],
        "creator_subject": "e2e-author-sub",
        "reviewer_subject": reviewer_subject,
    }


def _validate_source_provenance(run: Any, seed: Any) -> str:
    envelope, envelope_sha256 = _validate_envelope(load_ingest_envelope(run.draft_json_path))
    provenance = get_ingest_provenance(run.db_path, seed.draft_id)
    if (
        envelope_sha256 != seed.envelope_sha256
        or envelope_sha256 != provenance.envelope_sha256
        or provenance.raw_sha256 != seed.raw_sha256
        or provenance.canonical_text_sha256 != seed.canonical_text_sha256
        or envelope["draft"]["source"]["sha256"] != seed.canonical_text_sha256
        or hashlib.sha256(run.source_path.read_bytes()).hexdigest() != seed.raw_sha256
    ):
        raise RuntimeError("source/envelope/provenance đã thay đổi")
    return envelope_sha256


def _expected_selection_rows(
    events: tuple[tuple[int, ...], ...], actor_subject: str
) -> list[tuple[Any, ...]]:
    rows = []
    for version, snapshot in enumerate(events, start=1):
        serialized = json.dumps(list(snapshot), separators=(",", ":"))
        rows.append(
            (
                version,
                version,
                "save_selection",
                actor_subject,
                serialized,
                hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            )
        )
    return rows


def verify_nonterminal_browser_outcome(run: Any, plan: BrowserCasePlan) -> dict[str, Any]:
    """Hậu kiểm ca bị chặn hoặc save-refresh 503 mà không chạy exporter."""

    seed = run.ingest_seed
    if seed is None or plan.outcome not in {"denied", "pending"}:
        raise RuntimeError("plan nonterminal không hợp lệ")
    if seed.eligible_indices != plan.expected_eligible_indices:
        raise RuntimeError("eligible indices không khớp fixture contract")
    state = database_state(run.db_path, seed.draft_id)
    draft = state["draft"]
    expected_rows = _expected_selection_rows(plan.expected_selection_events, run.actor_subject)
    if (
        draft is None
        or draft[1:] != ("pending", len(expected_rows), len(expected_rows))
        or state["selection_count"] != len(expected_rows)
        or state["selection_events"] != expected_rows
        or state["decision"] is not None
        or state["decision_event"] is not None
        or state["draft_actor"] is not None
        or run.bundle_path.exists()
    ):
        raise RuntimeError("nonterminal audit/count không hợp lệ")
    current = plan.expected_eligible_indices if not expected_rows else plan.expected_selection_events[-1]
    if current != plan.expected_selected_indices:
        raise RuntimeError("nonterminal selection không khớp")
    envelope_sha256 = _validate_source_provenance(run, seed)
    return {
        "status": "PASS",
        "outcome": plan.outcome,
        "draft_id": seed.draft_id,
        "source_sha256": seed.canonical_text_sha256,
        "envelope_sha256": envelope_sha256,
        "duplicate_verified": seed.duplicate_result == "duplicate",
        "selected_indices": list(current),
        "selection_audit_count": len(expected_rows),
        "decision_audit_count": 0,
    }


def verify_browser_outcome(
    run: Any,
    *,
    expected_selected_indices: tuple[int, ...],
    expected_actor_subject: str,
    expected_selection_events: tuple[tuple[int, ...], ...],
) -> dict[str, Any]:
    """Hậu kiểm final audit và STIX; không ghi DB ngoài artifact bundle."""

    seed = run.ingest_seed
    if (
        seed is None
        or not expected_actor_subject
        or not expected_selection_events
        or expected_selection_events[-1] != expected_selected_indices
        or any(
            index not in seed.eligible_indices for snapshot in expected_selection_events for index in snapshot
        )
    ):
        raise RuntimeError("seed hoặc selection hậu kiểm không hợp lệ")
    state = database_state(run.db_path, seed.draft_id)
    draft = state["draft"]
    decision = state["decision"]
    if (
        draft is None
        or draft[1] != "approved"
        or type(draft[2]) is not int
        or draft[2] != len(expected_selection_events) + 1
        or type(draft[3]) is not int
        or draft[3] != len(expected_selection_events)
    ):
        observed = None if draft is None else draft[1:]
        raise RuntimeError(f"draft chưa ở final state mong đợi: {observed!r}")
    expected_selection_rows = _expected_selection_rows(expected_selection_events, expected_actor_subject)
    final_serialized = json.dumps(list(expected_selected_indices), separators=(",", ":"))
    final_sha256 = hashlib.sha256(final_serialized.encode("utf-8")).hexdigest()
    expected_final = (
        decision[0] if decision is not None else None,
        "approve",
        expected_actor_subject,
        len(expected_selection_events),
        "pending",
        "approved",
        len(expected_selection_events),
        len(expected_selection_events) + 1,
        len(expected_selection_events),
        final_serialized,
        final_sha256,
    )
    if (
        state["selection_count"] != len(expected_selection_events)
        or state["selection_events"] != expected_selection_rows
        or state["draft_actor"] != expected_actor_subject
        or decision is None
        or state["decision_event"] != expected_final
        or decision[1] != "approve"
        or decision[2] != draft[3]
    ):
        raise RuntimeError("audit count hoặc action không hợp lệ")
    selected = tuple(json.loads(decision[3]))
    if selected != expected_selected_indices:
        raise RuntimeError("final selection không khớp thao tác mong đợi")

    _validate_source_provenance(run, seed)

    db_before = file_inventory(run.db_path)
    exported = run_export(run, run.bundle_path)
    db_after = file_inventory(run.db_path)
    if exported.returncode != 0 or exported.stderr or db_before != db_after:
        raise RuntimeError("STIX CLI thất bại hoặc đã ghi DB")
    try:
        export_summary = json.loads(exported.stdout)
        bundle_bytes = run.bundle_path.read_bytes()
        bundle = json.loads(bundle_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RuntimeError("artifact STIX không hợp lệ") from None
    _validate_bundle_allowlist(bundle)
    private_markers = getattr(run, "private_markers", None)
    if (
        not isinstance(private_markers, Mapping)
        or set(private_markers) != PRIVATE_MARKER_KEYS
        or any(type(value) is not str or not value for value in private_markers.values())
    ):
        raise RuntimeError("privacy marker config không hợp lệ")
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()
    if (
        export_summary.get("draft_id") != seed.draft_id
        or export_summary.get("bundle_sha256") != bundle_sha256
        or export_summary.get("object_count") != len(bundle.get("objects", []))
    ):
        raise RuntimeError("summary STIX không khớp artifact")

    selected_values = {
        value
        for index, value in zip(seed.eligible_indices, seed.ioc_values, strict=True)
        if index in selected
    }
    deselected_values = {
        value
        for index, value in zip(seed.eligible_indices, seed.ioc_values, strict=True)
        if index not in selected and value not in selected_values
    }
    sco_values = set()
    for item in bundle["objects"]:
        if item["type"] in VALUE_SCO_TYPES:
            sco_values.add(item["value"])
        elif item["type"] == "file":
            sco_values.update(item["hashes"].values())
    if sco_values != selected_values:
        raise RuntimeError("bundle SCO không khớp IOC đã chọn")
    semantic_strings = tuple(_iter_json_strings(bundle))
    if any(marker in field for marker in private_markers.values() for field in semantic_strings):
        raise RuntimeError("STIX lộ privacy marker")
    if any(value in field for value in deselected_values for field in semantic_strings):
        raise RuntimeError("STIX chứa IOC đã bỏ ngoài SCO")

    report = next((item for item in bundle["objects"] if item.get("type") == "report"), None)
    if report is None:
        raise RuntimeError("STIX thiếu Report")
    try:
        stix_provenance = json.loads(report["external_references"][0]["description"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise RuntimeError("STIX provenance không hợp lệ") from None
    if (
        type(stix_provenance) is not dict
        or set(stix_provenance) != PROVENANCE_KEYS
        or stix_provenance.get("source_sha256") != seed.canonical_text_sha256
        or stix_provenance.get("draft_id") != seed.draft_id
        or stix_provenance.get("approved_audit_id") != decision[0]
        or stix_provenance.get("review_version") != draft[2]
        or stix_provenance.get("selection_version") != draft[3]
        or tuple(stix_provenance.get("selected_indices", [])) != selected
        or stix_provenance.get("selected_sha256") != decision[4]
    ):
        raise RuntimeError("STIX provenance không khớp final audit")
    return {
        "status": "PASS",
        "draft_id": seed.draft_id,
        "source_sha256": seed.canonical_text_sha256,
        "selected_indices": list(selected),
        "bundle_sha256": bundle_sha256,
        "object_count": len(bundle["objects"]),
        "selection_audit_count": state["selection_count"],
        "decision_audit_id": decision[0],
        "database_read_only_during_export": db_before == db_after,
    }


def wait_for_browser_signal(stream: TextIO, *, timeout: float) -> str:
    """Đợi đúng một dòng có deadline; thread đọc stdin là daemon để timeout không giữ process."""

    result: queue.Queue[str] = queue.Queue(maxsize=1)

    def read_line() -> None:
        try:
            result.put(stream.readline())
        except (OSError, UnicodeError):
            result.put("")

    reader = threading.Thread(target=read_line, name="w05-browser-signal", daemon=True)
    reader.start()
    reader.join(timeout=timeout)
    if reader.is_alive():
        return "timeout"
    line = result.get_nowait()
    return "eof" if line == "" else "continue"


def _stage_input(root: Path, input_kind: str, producer_root: Path) -> Path:
    if input_kind == "txt":
        path = root / "ingest-browser-synthetic.txt"
        path.write_bytes(E2E_SOURCE_BYTES)
        return path
    source = producer_root / "extractor" / "tests" / "fixtures" / "local_ingest" / "two-text-pages.pdf"
    if not source.is_file():
        raise RuntimeError("fixture PDF producer không tồn tại")
    path = root / source.name
    shutil.copyfile(source, path)
    return path


def _offline_check(
    *, input_kind: str, producer_root: Path, producer_python: Path, importer_python: Path
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="x01-ingest-browser-offline-") as temp:
        root = Path(temp)
        source = _stage_input(root, input_kind, producer_root)
        envelope = root / "envelope.json"
        database = root / "drafts.sqlite"
        config = root / "exporter-config.json"
        bundle = root / "approved-bundle.json"
        config.write_bytes(
            (ROOT / "extractor" / "draft" / "examples" / "stix" / "exporter-config.example.json").read_bytes()
        )
        seed = seed_ingest_fixture(
            input_path=source,
            envelope_path=envelope,
            db_path=database,
            producer_root=producer_root,
            producer_python=producer_python,
            importer_python=importer_python,
            created_by_subject="e2e-author-sub",
        )
        summary: dict[str, Any] = {
            "status": "PASS",
            "mode": "offline",
            "input_format": seed.input_format,
            "draft_id": seed.draft_id,
            "eligible_indices": list(seed.eligible_indices),
            "source_sha256": seed.canonical_text_sha256,
            "envelope_sha256": seed.envelope_sha256,
            "duplicate_verified": seed.duplicate_result == "duplicate",
            "browser": "UNVERIFIED",
        }
        if not seed.eligible_indices:
            summary["postcheck"] = "SEED_ONLY_NO_ELIGIBLE_IOC"
            return summary

        expected = seed.eligible_indices[1:] if len(seed.eligible_indices) > 1 else ()
        actor = store.Actor("admin-sub", frozenset({"admin"}))
        selection = store.save_selection(
            database,
            seed.draft_id,
            actor=actor,
            selected_indices=expected,
            expected_version=0,
        )
        selection_events = (expected,)
        if not expected:
            expected = seed.eligible_indices
            selection = store.save_selection(
                database,
                seed.draft_id,
                actor=actor,
                selected_indices=expected,
                expected_version=selection.review_version,
            )
            selection_events = ((), expected)
        store.decide_draft_with_selection(
            database,
            seed.draft_id,
            actor=actor,
            decision="approve",
            expected_version=selection.review_version,
        )
        run = SimpleNamespace(
            db_path=database,
            selection_draft_id=seed.draft_id,
            exporter_config_path=config,
            bundle_path=bundle,
            source_path=source,
            draft_json_path=envelope,
            created_by_subject="e2e-author-sub",
            private_markers=_privacy_markers(input_kind, source, actor.subject),
            ingest_seed=seed,
        )
        summary.update(
            verify_browser_outcome(
                run,
                expected_selected_indices=expected,
                expected_actor_subject=actor.subject,
                expected_selection_events=selection_events,
            )
        )
        summary.update({"mode": "offline", "input_format": seed.input_format, "browser": "UNVERIFIED"})
        return summary


def _browser_session(
    *, input_kind: str, case: str, producer_root: Path, producer_python: Path, duration_seconds: int
) -> dict[str, Any]:
    plan = browser_case_plan(input_kind, case)
    actions = {
        ("txt", "happy"): "bỏ IOC 0, lưu, duyệt",
        ("pdf", "happy"): "bỏ IOC 0, lưu rỗng, chọn lại IOC 0, lưu, duyệt",
        ("txt", "self-approve"): "giữ lựa chọn, duyệt và quan sát 403",
        ("txt", "save-refresh-503"): "bỏ IOC 0, lưu, bấm Thử lại một lần",
        ("txt", "decision-refresh-503"): "duyệt lựa chọn đã lưu, bấm Thử lại một lần",
    }
    with tempfile.TemporaryDirectory(prefix="x01-ingest-browser-input-") as temp:
        source = _stage_input(Path(temp), input_kind, producer_root)
        with LocalRun(
            plan.scenario,
            duration_seconds=duration_seconds,
            start_ui=True,
            producer_root=producer_root,
            producer_python=producer_python,
            ingest_input=source,
            created_by_subject="e2e-author-sub",
        ) as run:
            seed = run.ingest_seed
            if seed is None or seed.eligible_indices != plan.expected_eligible_indices:
                raise RuntimeError("eligible indices không khớp fixture contract")
            print(
                json.dumps(
                    {
                        "status": "READY",
                        "url": run.url,
                        "draft_id": seed.draft_id,
                        "case": case,
                        "actions": actions[(input_kind, case)],
                        "eligible_indices": list(seed.eligible_indices),
                        "expected_selected_indices": list(plan.expected_selected_indices),
                        "deadline_seconds": duration_seconds,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                flush=True,
            )
            signal = wait_for_browser_signal(sys.stdin, timeout=duration_seconds)
            if signal != "continue":
                raise RuntimeError(f"browser session kết thúc do {signal}")
            run.private_markers = _privacy_markers(input_kind, run.source_path, run.actor_subject)
            if plan.outcome in {"denied", "pending"}:
                return verify_nonterminal_browser_outcome(run, plan)
            return verify_browser_outcome(
                run,
                expected_selected_indices=plan.expected_selected_indices,
                expected_actor_subject=run.actor_subject,
                expected_selection_events=plan.expected_selection_events,
            )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("offline-check", "browser-session"):
        command = subparsers.add_parser(name)
        command.add_argument("--input-kind", choices=("txt", "pdf"), required=True)
        command.add_argument("--producer-root", required=True, type=Path)
        command.add_argument("--producer-python", type=Path)
        if name == "browser-session":
            command.add_argument(
                "--case",
                choices=("happy", "self-approve", "save-refresh-503", "decision-refresh-503"),
                default="happy",
            )
            command.add_argument("--duration-seconds", type=int, default=300)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    producer_python = args.producer_python or args.producer_root / ".venv" / "Scripts" / "python.exe"
    try:
        if args.command == "offline-check":
            summary = _offline_check(
                input_kind=args.input_kind,
                producer_root=args.producer_root,
                producer_python=producer_python,
                importer_python=Path(sys.executable),
            )
        else:
            if isinstance(args.duration_seconds, bool) or not 1 <= args.duration_seconds <= 300:
                raise RuntimeError("duration_seconds phải từ 1 đến 300")
            summary = _browser_session(
                input_kind=args.input_kind,
                case=args.case,
                producer_root=args.producer_root,
                producer_python=producer_python,
                duration_seconds=args.duration_seconds,
            )
    except (OSError, RuntimeError, store.DraftStoreError):
        print('{"error":"harness_failed","status":"FAIL"}', file=sys.stderr)
        return 1
    print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
