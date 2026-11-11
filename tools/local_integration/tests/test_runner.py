from __future__ import annotations

import hashlib
import io
import json
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft
from tools.local_integration.runner import LocalRun, seed_ingest_fixture
from tools.local_integration.tests import run_ingest_browser_stix as harness_module
from tools.local_integration.tests.run_ingest_browser_stix import (
    verify_browser_outcome,
    wait_for_browser_signal,
)

E2E_SOURCE_BYTES = "Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n".encode()
E2E_SOURCE_SHA256 = "e73038e5d68d0aee0757bf72cd8a404b3f55a94ef9d6c519f5e0c3fb1292a655"


def make_fixture_producer(tmp_path: Path, source: Path) -> Path:
    producer_root = tmp_path / "producer"
    script = producer_root / "extractor" / "ingest" / "run.py"
    script.parent.mkdir(parents=True)
    text = source.read_text(encoding="utf-8")
    envelope = {
        "schema_version": "x01-local-ingest/1.0",
        "input": {
            "format": "text",
            "display_name": source.name,
            "raw_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "raw_bytes": len(source.read_bytes()),
            "canonical_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "page_count": None,
            "page_text_ranges": None,
        },
        "draft": build_regex_draft(text, source=source.name, language="vi", tlp="TLP:GREEN"),
    }
    fixture = script.with_name("fixture.json")
    fixture.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
    script.write_text(
        """import argparse, json, shutil
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--language', required=True)
parser.add_argument('--tlp', required=True)
args = parser.parse_args()
shutil.copyfile(Path(__file__).with_name('fixture.json'), args.output)
print(json.dumps({'format':'text','output_created':True,'schema_version':'x01-local-ingest/1.0'}))
""",
        encoding="utf-8",
    )
    return producer_root


def test_seed_ingest_fixture_uses_two_clis_and_one_database_without_mutating_input(
    tmp_path: Path,
) -> None:
    source = tmp_path / "synthetic.txt"
    source.write_bytes(E2E_SOURCE_BYTES)
    input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    producer_root = make_fixture_producer(tmp_path, source)
    envelope = tmp_path / "envelope.json"
    database = tmp_path / "drafts.sqlite"

    result = seed_ingest_fixture(
        input_path=source,
        envelope_path=envelope,
        db_path=database,
        producer_root=producer_root,
        producer_python=Path(sys.executable),
        importer_python=Path(sys.executable),
        created_by_subject="e2e-author-sub",
    )

    assert result.draft_id == 1
    assert result.import_result == "imported"
    assert result.duplicate_result == "duplicate"
    assert result.eligible_indices == (0, 1)
    assert result.ioc_values == ("evil-one.example", "evil-two.example")
    assert result.raw_sha256 == input_hash
    assert result.canonical_text_sha256 == E2E_SOURCE_SHA256
    assert hashlib.sha256(source.read_bytes()).hexdigest() == input_hash
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM drafts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM draft_ingest_provenance").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM draft_selection_audit").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM draft_audit").fetchone()[0] == 0


def test_ingest_browser_scenario_seeds_real_api_and_cleans_owned_resources(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.txt"
    source.write_bytes(E2E_SOURCE_BYTES)
    producer_root = make_fixture_producer(tmp_path, source)
    run = LocalRun(
        "ingest-browser-stix",
        duration_seconds=20,
        start_ui=False,
        producer_root=producer_root,
        producer_python=Path(sys.executable),
        ingest_input=source,
        created_by_subject="e2e-author-sub",
    )

    with run:
        response = httpx.get(f"{run.url}/api/v1/drafts/{run.selection_draft_id}", timeout=2)
        assert response.status_code == 200
        assert response.json()["source"] == {
            "name": "synthetic.txt",
            "sha256": E2E_SOURCE_SHA256,
        }
        assert run.ingest_seed is not None
        assert run.ingest_seed.eligible_indices == (0, 1)
        temp_root = run.temp_root

    assert not temp_root.exists()


def make_approved_postcheck_case(tmp_path: Path) -> SimpleNamespace:
    source = tmp_path / "synthetic.txt"
    source.write_bytes(E2E_SOURCE_BYTES)
    producer_root = make_fixture_producer(tmp_path, source)
    envelope = tmp_path / "envelope.json"
    database = tmp_path / "drafts.sqlite"
    config = tmp_path / "exporter-config.json"
    bundle = tmp_path / "approved-bundle.json"
    repository = Path(__file__).resolve().parents[3]
    config.write_bytes(
        (
            repository / "extractor" / "draft" / "examples" / "stix" / "exporter-config.example.json"
        ).read_bytes()
    )
    seed = seed_ingest_fixture(
        input_path=source,
        envelope_path=envelope,
        db_path=database,
        producer_root=producer_root,
        producer_python=Path(sys.executable),
        importer_python=Path(sys.executable),
        created_by_subject="e2e-author-sub",
    )
    actor = store.Actor("admin-sub", frozenset({"admin"}))
    selection = store.save_selection(
        database,
        seed.draft_id,
        actor=actor,
        selected_indices=[1],
        expected_version=0,
    )
    store.decide_draft_with_selection(
        database,
        seed.draft_id,
        actor=actor,
        decision="approve",
        expected_version=selection.review_version,
    )
    return SimpleNamespace(
        db_path=database,
        selection_draft_id=seed.draft_id,
        exporter_config_path=config,
        bundle_path=bundle,
        source_path=source,
        draft_json_path=envelope,
        created_by_subject="e2e-author-sub",
        private_markers={
            "source_name": "synthetic.txt",
            "raw_source": "Cảnh báo thử nghiệm 😀",
            "evidence": "ghi nhận",
            "creator_subject": "e2e-author-sub",
            "reviewer_subject": "admin-sub",
        },
        ingest_seed=seed,
    )


def test_offline_postcheck_verifies_selection_audit_and_stix_on_seed_database(tmp_path: Path) -> None:
    run = make_approved_postcheck_case(tmp_path)

    summary = verify_browser_outcome(
        run,
        expected_selected_indices=(1,),
        expected_actor_subject="admin-sub",
        expected_selection_events=((1,),),
    )

    assert summary["status"] == "PASS"
    assert summary["selected_indices"] == [1]
    assert summary["source_sha256"] == E2E_SOURCE_SHA256
    assert summary["object_count"] == 4
    assert summary["bundle_sha256"] == hashlib.sha256(run.bundle_path.read_bytes()).hexdigest()


def test_postcheck_rejects_valid_envelope_whose_canonical_digest_changed(tmp_path: Path) -> None:
    run = make_approved_postcheck_case(tmp_path)
    envelope = json.loads(run.draft_json_path.read_text(encoding="utf-8"))
    envelope["input"]["display_name"] = "renamed-synthetic.txt"
    envelope["draft"]["source"]["name"] = "renamed-synthetic.txt"
    run.draft_json_path.write_text(
        json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source/envelope/provenance"):
        verify_browser_outcome(
            run,
            expected_selected_indices=(1,),
            expected_actor_subject="admin-sub",
            expected_selection_events=((1,),),
        )


def mutate_all_postcheck_actors(run: SimpleNamespace) -> None:
    with closing(sqlite3.connect(run.db_path)) as connection:
        values = ("other-reviewer-sub", run.ingest_seed.draft_id)
        connection.execute("UPDATE drafts SET decided_by_subject=? WHERE id=?", values)
        connection.execute("UPDATE draft_audit SET actor_subject=? WHERE draft_id=?", values)
        connection.execute("UPDATE draft_selection_audit SET actor_subject=? WHERE draft_id=?", values)
        connection.commit()


def mutate_selection_postcheck_actor(run: SimpleNamespace) -> None:
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute(
            "UPDATE draft_selection_audit SET actor_subject=? WHERE draft_id=?",
            ("other-selection-sub", run.ingest_seed.draft_id),
        )
        connection.commit()


def mutate_selection_postcheck_snapshot(run: SimpleNamespace) -> None:
    serialized = "[0]"
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute(
            "UPDATE draft_selection_audit SET selected_indices_json=?,selected_sha256=? WHERE draft_id=?",
            (serialized, digest, run.ingest_seed.draft_id),
        )
        connection.commit()


def mutate_selection_postcheck_versions(run: SimpleNamespace) -> None:
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute(
            "UPDATE draft_selection_audit SET selection_version=9,review_version=9 WHERE draft_id=?",
            (run.ingest_seed.draft_id,),
        )
        connection.commit()


def mutate_selection_postcheck_action(run: SimpleNamespace) -> None:
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE draft_selection_audit SET action='tampered' WHERE draft_id=?",
            (run.ingest_seed.draft_id,),
        )
        connection.commit()


def mutate_final_postcheck_versions(run: SimpleNamespace) -> None:
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute(
            "UPDATE draft_audit SET expected_version=41,previous_version=41,new_version=42 WHERE draft_id=?",
            (run.ingest_seed.draft_id,),
        )
        connection.commit()


def mutate_final_postcheck_snapshot(run: SimpleNamespace) -> None:
    serialized = "[0]"
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    with closing(sqlite3.connect(run.db_path)) as connection:
        connection.execute(
            "UPDATE draft_audit SET selected_indices_json=?,selected_sha256=? WHERE draft_id=?",
            (serialized, digest, run.ingest_seed.draft_id),
        )
        connection.commit()


@pytest.mark.parametrize(
    "mutation",
    [
        mutate_all_postcheck_actors,
        mutate_selection_postcheck_actor,
        mutate_selection_postcheck_snapshot,
        mutate_selection_postcheck_versions,
        mutate_selection_postcheck_action,
        mutate_final_postcheck_versions,
        mutate_final_postcheck_snapshot,
    ],
)
def test_postcheck_rejects_actor_or_selection_audit_mutation_before_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation
) -> None:
    run = make_approved_postcheck_case(tmp_path)
    mutation(run)

    def export_must_not_run(*_args, **_kwargs):
        raise AssertionError("audit mutation reached exporter")

    monkeypatch.setattr(harness_module, "run_export", export_must_not_run)
    with pytest.raises(RuntimeError, match="audit"):
        verify_browser_outcome(
            run,
            expected_selected_indices=(1,),
            expected_actor_subject="admin-sub",
            expected_selection_events=((1,),),
        )


def inject_forbidden_bundle_value(bundle: dict, mutation: str, marker: str) -> None:
    report = bundle["objects"][-1]
    if mutation == "top_level_field":
        bundle["x_forbidden"] = marker
    elif mutation == "nested_field":
        report["external_references"][0]["x_forbidden"] = marker
    elif mutation == "selected_ioc_only_in_report":
        sco = next(item for item in bundle["objects"] if item.get("type") == "domain-name")
        sco["value"] = "replacement.example"
        report["name"] += f" {marker}"
    else:
        report["name"] += f" {marker}"


@pytest.mark.parametrize(
    ("mutation", "marker_key"),
    [
        ("top_level_field", "evidence"),
        ("nested_field", "evidence"),
        ("allowed_source_name", "source_name"),
        ("allowed_raw_source", "raw_source"),
        ("allowed_evidence", "evidence"),
        ("allowed_creator_subject", "creator_subject"),
        ("allowed_reviewer_subject", "reviewer_subject"),
        ("selected_ioc_only_in_report", "selected_ioc"),
    ],
)
def test_postcheck_rejects_forbidden_bundle_structure_or_private_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    marker_key: str,
) -> None:
    run = make_approved_postcheck_case(tmp_path)
    original_export = harness_module.run_export

    def leaking_export(run_arg, output):
        result = original_export(run_arg, output)
        bundle = json.loads(output.read_text(encoding="utf-8"))
        marker = (
            run.ingest_seed.ioc_values[1] if marker_key == "selected_ioc" else run.private_markers[marker_key]
        )
        inject_forbidden_bundle_value(bundle, mutation, marker)
        raw = (json.dumps(bundle, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
        output.write_bytes(raw)
        summary = json.loads(result.stdout)
        summary["bundle_sha256"] = hashlib.sha256(raw).hexdigest()
        return subprocess.CompletedProcess(
            result.args,
            0,
            json.dumps(summary, separators=(",", ":"), sort_keys=True),
            "",
        )

    monkeypatch.setattr(harness_module, "run_export", leaking_export)
    with pytest.raises(RuntimeError, match="bundle|marker|privacy"):
        verify_browser_outcome(
            run,
            expected_selected_indices=(1,),
            expected_actor_subject="admin-sub",
            expected_selection_events=((1,),),
        )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("escaped_evidence_in_description", "privacy marker"),
        ("deselected_ioc_in_description", "IOC đã bỏ"),
    ],
)
def test_postcheck_rejects_semantic_description_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_error: str,
) -> None:
    run = make_approved_postcheck_case(tmp_path)
    original_export = harness_module.run_export

    def leaking_export(run_arg, output):
        result = original_export(run_arg, output)
        bundle = json.loads(output.read_text(encoding="utf-8"))
        report = next(item for item in bundle["objects"] if item["type"] == "report")
        leaked = (
            run.private_markers["evidence"]
            if mutation == "escaped_evidence_in_description"
            else run.ingest_seed.ioc_values[0]
        )
        report["description"] += f" | {leaked}"
        raw = json.dumps(
            bundle,
            ensure_ascii=mutation == "escaped_evidence_in_description",
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        output.write_bytes(raw)
        summary = json.loads(result.stdout)
        summary["bundle_sha256"] = hashlib.sha256(raw).hexdigest()
        return subprocess.CompletedProcess(
            result.args,
            0,
            json.dumps(summary, separators=(",", ":"), sort_keys=True),
            "",
        )

    monkeypatch.setattr(harness_module, "run_export", leaking_export)
    with pytest.raises(RuntimeError, match=expected_error):
        verify_browser_outcome(
            run,
            expected_selected_indices=(1,),
            expected_actor_subject="admin-sub",
            expected_selection_events=((1,),),
        )


def test_browser_signal_distinguishes_continue_eof_and_timeout() -> None:
    assert wait_for_browser_signal(io.StringIO("done\n"), timeout=0.1) == "continue"
    assert wait_for_browser_signal(io.StringIO(""), timeout=0.1) == "eof"

    release = threading.Event()

    class BlockingInput:
        def readline(self) -> str:
            release.wait()
            return "done\n"

    try:
        assert wait_for_browser_signal(BlockingInput(), timeout=0.01) == "timeout"
    finally:
        release.set()


def recover_resources_created_by_failed_lifecycle_test(run: LocalRun) -> None:
    """Only protects RED runs; production must reject before this is needed."""
    if any((run._gateway_process, run._ui_process, run._api_thread, run._temporary)):
        run._closed = False
        run.close()


def test_runner_starts_signed_http_stack_and_cleans_owned_resources() -> None:
    run = LocalRun("admin-other", duration_seconds=20, start_ui=False)
    with run:
        response = httpx.get(f"{run.url}/api/drafts", timeout=2)
        assert response.status_code == 200
        assert run.db_path.exists()
        port = run.gateway_port
        temp_root = run.temp_root
    assert not temp_root.exists()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.2)


def test_runner_rejects_unknown_scenario_before_creating_resources() -> None:
    with pytest.raises(ValueError):
        LocalRun("caller-selected-admin")


def test_selection_scenario_adds_two_ioc_fixture_without_changing_legacy_fixtures() -> None:
    with LocalRun("selection-admin", duration_seconds=20, start_ui=False) as selection_run:
        response = httpx.get(
            f"{selection_run.url}/api/v1/drafts/{selection_run.selection_draft_id}", timeout=2
        )
        assert response.status_code == 200
        assert len(selection_run.draft_ids) == 5
        body = response.json()
        assert [(item["kind"], item["keep"], item["status"]) for item in body["items"]] == [
            ("ioc", True, "ok"),
            ("ioc", True, "ok"),
        ]
        assert body["selection"]["ai_eligible_count"] == 2
        assert body["selection"]["selected_indices"] == [0, 1]

    with LocalRun("admin-other", duration_seconds=20, start_ui=False) as legacy_run:
        assert len(legacy_run.draft_ids) == 4
        assert legacy_run.selection_draft_id is None


def test_stix_e2e_scenario_seeds_reviewable_draft_through_two_real_clis() -> None:
    run = LocalRun("stix-e2e", duration_seconds=120, start_ui=False)
    with run:
        response = httpx.get(f"{run.url}/api/v1/drafts/{run.selection_draft_id}", timeout=2)
        assert response.status_code == 200
        body = response.json()
        assert run.source_path.read_bytes() == E2E_SOURCE_BYTES
        assert json.loads(run.draft_json_path.read_text(encoding="utf-8"))["source"]["sha256"] == (
            E2E_SOURCE_SHA256
        )
        assert run.draft_ids == (1,)
        assert run.selection_draft_id == 1
        assert body["source"] == {"name": "stix-e2e-input.txt", "sha256": E2E_SOURCE_SHA256}
        assert body["text"] == E2E_SOURCE_BYTES.decode("utf-8")
        assert body["language"] == "vi"
        assert body["tlp"] == "TLP:GREEN"
        assert body["model"] == "regex-C1"
        assert body["review"]["created_by_subject"] == "e2e-author-sub"
        assert [item["value"] for item in body["items"]] == ["evil-one.example", "evil-two.example"]
        assert all(
            body["text"][item["span"][0] : item["span"][1]] == item["evidence"] for item in body["items"]
        )
        assert body["selection"]["selected_indices"] == [0, 1]
        assert run.exporter_config_path.read_bytes()
        assert not run.bundle_path.exists()
        temp_root = run.temp_root
        gateway = run._gateway_process
        api_thread = run._api_thread

    assert not temp_root.exists()
    assert gateway is not None and gateway.poll() is not None
    assert api_thread is not None and not api_thread.is_alive()


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (subprocess.CompletedProcess(["python"], 1, "", "sensitive child failure"), "seed CLI thất bại"),
        (subprocess.TimeoutExpired(["python"], 10), "seed CLI quá thời hạn"),
        (subprocess.CompletedProcess(["python"], 0, "not-json", ""), "store CLI trả kết quả không hợp lệ"),
    ],
)
def test_stix_e2e_seed_failure_cleans_owned_temp_without_leaking_child_output(
    monkeypatch: pytest.MonkeyPatch,
    failure: subprocess.CompletedProcess[str] | subprocess.TimeoutExpired,
    expected_message: str,
) -> None:
    calls = 0

    def fail_seed(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if isinstance(failure, subprocess.TimeoutExpired):
            raise failure
        if failure.returncode == 0 and calls == 1:
            return subprocess.CompletedProcess(["python"], 0, "", "")
        return failure

    monkeypatch.setattr(subprocess, "run", fail_seed)
    run = LocalRun("stix-e2e", duration_seconds=120, start_ui=False)

    with pytest.raises(RuntimeError, match=expected_message) as captured:
        run.start()

    assert "sensitive child failure" not in str(captured.value)
    assert run._closed
    assert run._temporary is None
    assert run._api_thread is None
    assert run._gateway_process is None
    assert not run.temp_root.exists()


def test_stix_e2e_exception_inside_run_cleans_owned_stack() -> None:
    run = LocalRun("stix-e2e", duration_seconds=120, start_ui=False)
    gateway = None
    api_thread = None

    with pytest.raises(RuntimeError, match="synthetic mid-run failure"):
        with run:
            temp_root = run.temp_root
            gateway = run._gateway_process
            api_thread = run._api_thread
            raise RuntimeError("synthetic mid-run failure")

    assert not temp_root.exists()
    assert gateway is not None and gateway.poll() is not None
    assert api_thread is not None and not api_thread.is_alive()
    assert run._closed


def test_decision_refresh_fault_starts_from_saved_selection_snapshot() -> None:
    with LocalRun("selection-decision-refresh-503", duration_seconds=20, start_ui=False) as run:
        response = httpx.get(f"{run.url}/api/v1/drafts/{run.selection_draft_id}", timeout=2)
        assert response.status_code == 200
        assert response.json()["review"]["version"] == 1
        assert response.json()["selection"]["selection_version"] == 1
        assert response.json()["selection"]["selected_indices"] == [1]


def test_runner_busy_gateway_port_does_not_stop_unowned_listener() -> None:
    sentinel = socket.socket()
    sentinel.bind(("127.0.0.1", 0))
    sentinel.listen()
    port = sentinel.getsockname()[1]
    try:
        run = LocalRun("admin-other", duration_seconds=20, start_ui=False, gateway_port=port)
        with pytest.raises(RuntimeError):
            run.start()
        assert sentinel.fileno() != -1
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            pass
        assert not run.temp_root.exists()
    finally:
        sentinel.close()


def test_cleanup_continues_after_child_error_and_reports_incomplete_cleanup() -> None:
    run = LocalRun("admin-other", start_ui=False)
    gateway = Mock()
    gateway.poll.return_value = None
    gateway.terminate.side_effect = PermissionError("synthetic terminate failure")
    ui = Mock()
    ui.poll.return_value = None
    api = SimpleNamespace(should_exit=False)
    thread = Mock()
    thread.is_alive.return_value = False
    temporary = Mock()
    run._gateway_process, run._ui_process = gateway, ui
    run._api_server, run._api_thread, run._temporary = api, thread, temporary

    with pytest.raises(ExceptionGroup):
        run.close()

    assert ui.terminate.called
    assert api.should_exit
    assert temporary.cleanup.called
    assert not run._closed


def test_cleanup_retries_transient_temp_failure() -> None:
    run = LocalRun("admin-other", start_ui=False)
    temporary = Mock()
    temporary.cleanup.side_effect = [PermissionError("synthetic Windows file lock"), None]
    run._temporary = temporary

    with pytest.raises(ExceptionGroup):
        run.close()
    run.close()

    assert temporary.cleanup.call_count == 2
    assert run._closed


def test_cleanup_keeps_temp_until_api_thread_has_stopped() -> None:
    run = LocalRun("admin-other", start_ui=False)
    api = SimpleNamespace(should_exit=False)
    thread = Mock()
    thread.is_alive.side_effect = [True, False]
    temporary = Mock()
    run._api_server, run._api_thread, run._temporary = api, thread, temporary

    with pytest.raises(ExceptionGroup):
        run.close()
    temporary.cleanup.assert_not_called()
    run.close()

    temporary.cleanup.assert_called_once()
    assert run._closed


def test_ttl_closes_owned_stack_and_temp_root() -> None:
    run = LocalRun("admin-other", duration_seconds=1, start_ui=False).start()
    temp_root = run.temp_root
    port = run.gateway_port
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline and temp_root.exists():
        time.sleep(0.05)

    assert not temp_root.exists()
    assert run._closed
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.2)


def test_partial_start_failure_stops_api_and_removes_temp(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_gateway_start(*_args, **_kwargs):
        raise OSError("synthetic child start failure")

    monkeypatch.setattr(subprocess, "Popen", fail_gateway_start)
    run = LocalRun("admin-other", duration_seconds=20, start_ui=False)

    with pytest.raises(OSError, match="synthetic child start failure"):
        run.start()

    assert not run.temp_root.exists()
    assert run._closed
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", run.api_port), timeout=0.2)


def test_completed_run_cannot_start_again() -> None:
    run = LocalRun("admin-other", duration_seconds=20, start_ui=False)
    run.start()
    run.close()
    first_temp_root = run.temp_root

    try:
        with pytest.raises(RuntimeError, match="chỉ được start một lần"):
            run.start()

        assert run._closed
        assert run.temp_root == first_temp_root
        assert not first_temp_root.exists()
        assert run._gateway_process is None
        assert run._api_thread is None
    finally:
        recover_resources_created_by_failed_lifecycle_test(run)


def test_close_before_start_permanently_blocks_start() -> None:
    run = LocalRun("admin-other", duration_seconds=20, start_ui=False)
    run.close()

    try:
        with pytest.raises(RuntimeError, match="chỉ được start một lần"):
            run.start()

        assert run._closed
        assert run._temporary is None
        assert run._gateway_process is None
        assert run._api_thread is None
    finally:
        recover_resources_created_by_failed_lifecycle_test(run)


def test_failed_start_cannot_allocate_resources_again(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def fail_gateway_start(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise OSError("synthetic child start failure")

    monkeypatch.setattr(subprocess, "Popen", fail_gateway_start)
    run = LocalRun("admin-other", duration_seconds=20, start_ui=False)

    try:
        with pytest.raises(OSError, match="synthetic child start failure"):
            run.start()
        with pytest.raises(RuntimeError, match="chỉ được start một lần"):
            run.start()

        assert attempts == 1
        assert run._closed
        assert not run.temp_root.exists()
    finally:
        recover_resources_created_by_failed_lifecycle_test(run)
