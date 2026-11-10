from __future__ import annotations

import socket
import subprocess
import time
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from tools.local_integration.runner import LocalRun


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
