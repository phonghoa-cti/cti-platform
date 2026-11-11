from __future__ import annotations

import json
import socket
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from tools.local_integration.runner import LocalRun

E2E_SOURCE_BYTES = "Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n".encode()
E2E_SOURCE_SHA256 = "e73038e5d68d0aee0757bf72cd8a404b3f55a94ef9d6c519f5e0c3fb1292a655"


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


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        ("w02-it", 200),
        ("w02-analyst", 200),
        ("w02-multi-role", 200),
        ("w02-missing-token", 401),
        ("w02-forbidden", 403),
        ("w02-lookup-503", 503),
    ],
)
def test_w02_scenarios_inject_deterministic_lookup_fixture(scenario: str, status: int) -> None:
    with LocalRun(scenario, duration_seconds=20, start_ui=False) as run:
        response = httpx.get(f"{run.url}/api/ioc", params={"value": "evil.example"}, timeout=2)
        assert response.status_code == status
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"] == "Cf-Access-Jwt-Assertion"
        if status == 200:
            assert response.json()["state"] == "found"


def test_non_w02_scenario_keeps_production_default_lookup_port_missing() -> None:
    with LocalRun("admin-other", duration_seconds=20, start_ui=False) as run:
        response = httpx.get(f"{run.url}/api/ioc", params={"value": "evil.example"}, timeout=2)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "lookup_unavailable"


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        ("w04-it", 200),
        ("w04-analyst", 200),
        ("w04-multi-role", 200),
        ("w04-missing-token", 401),
        ("w04-forbidden", 403),
        ("w04-unknown-outcome", 200),
    ],
)
def test_w04_scenarios_opt_in_assets_and_role_policy(scenario: str, status: int) -> None:
    with LocalRun(scenario, duration_seconds=20, start_ui=False) as run:
        response = httpx.get(f"{run.url}/api/assets", timeout=2)
        assert response.status_code == status
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"] == "Cf-Access-Jwt-Assertion"
        assert run.asset_store is not None
        assert run.asset_store.path == run.db_path


def test_w04_asset_store_is_shared_with_w02_lookup_and_cleaned() -> None:
    run = LocalRun("w04-it", duration_seconds=20, start_ui=False)
    with run:
        created = httpx.post(
            f"{run.url}/api/assets",
            headers={"Origin": run.url},
            json={"type": "domain", "value": "company.example", "note": "synthetic"},
            timeout=2,
        )
        assert created.status_code == 201
        lookup = httpx.get(f"{run.url}/api/ioc", params={"value": "mail.company.example"}, timeout=2)
        assert lookup.status_code == 200
        assert lookup.json()["asset_match"] == {"matched": True, "assets": ["company.example"]}
        assert run.db_path.exists()
        temp_root = run.temp_root
    assert not temp_root.exists()


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        ("w04-technology-it", 200),
        ("w04-technology-analyst", 200),
        ("w04-technology-multi-role", 200),
        ("w04-technology-missing-token", 401),
        ("w04-technology-forbidden", 403),
        ("w04-technology-refresh-503", 200),
        ("w04-technology-unknown-outcome", 200),
    ],
)
def test_w04_technology_scenarios_opt_in_both_stores_on_one_database(scenario: str, status: int) -> None:
    with LocalRun(scenario, duration_seconds=20, start_ui=False) as run:
        response = httpx.get(f"{run.url}/api/assets/technologies", timeout=2)
        assert response.status_code == status
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"] == "Cf-Access-Jwt-Assertion"
        assert run.asset_store is not None
        assert run.technology_store is not None
        assert run.asset_store.path == run.db_path
        assert run.technology_store.path == run.db_path


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
