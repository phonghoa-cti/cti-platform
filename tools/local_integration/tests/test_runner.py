from __future__ import annotations

import socket

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
