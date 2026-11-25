"""Ma trận HTTP W02 trên gateway/API/UI cùng local run tổng hợp."""

from __future__ import annotations

import json
import socket

import httpx

from tools.local_integration.runner import LocalRun


def _request(run: LocalRun, value: str | None, *, spoof: bool = False) -> httpx.Response:
    params = {} if value is None else {"value": value}
    headers = {"Cf-Access-Jwt-Assertion": "caller-spoof-must-not-win"} if spoof else {}
    return httpx.get(f"{run.url}/api/ioc", params=params, headers=headers, timeout=3)


def _assert_security_headers(response: httpx.Response) -> None:
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Cf-Access-Jwt-Assertion"


def _assert_cleanup(run: LocalRun, temp_root) -> None:
    assert not temp_root.exists()
    assert run._closed
    try:
        socket.create_connection(("127.0.0.1", run.gateway_port), timeout=0.2)
    except OSError:
        return
    raise AssertionError("gateway port vẫn còn listener sau cleanup")


def _normal_scenario(scenario: str, *, start_ui: bool = False) -> dict:
    run = LocalRun(scenario, duration_seconds=60, start_ui=start_ui)
    with run:
        temp_root = run.temp_root
        if start_ui:
            page = httpx.get(f"{run.url}/tra-cuu", timeout=3)
            assert page.status_code == 200
            assert "Bản thử kết nối API" in page.text
            sample_page = httpx.get(f"{run.url}/tra-cuu/mau", timeout=3)
            assert sample_page.status_code == 200
            assert "Không gọi mạng" in sample_page.text
        found = _request(run, "evil.example", spoof=True)
        allowlisted = _request(run, "8.8.8.8")
        unknown = _request(run, "unknown.example")
        invalid = _request(run, None)
        private = _request(run, "192.168.1.1")
        for response in (found, allowlisted, unknown, invalid, private):
            _assert_security_headers(response)
        assert [found.status_code, allowlisted.status_code, unknown.status_code] == [200, 200, 200]
        assert [invalid.status_code, private.status_code] == [422, 422]
        assert found.json()["state"] == "found"
        assert allowlisted.json()["state"] == "allowlisted"
        assert unknown.json()["state"] == "not_found"
        assert invalid.json()["error"]["code"] == "invalid_ioc"
        assert private.json()["error"]["code"] == "private_ip"
        body = found.json()
    _assert_cleanup(run, temp_root)
    return body


def _error_scenario(scenario: str, status: int, code: str) -> None:
    run = LocalRun(scenario, duration_seconds=60, start_ui=False)
    with run:
        temp_root = run.temp_root
        response = _request(run, "evil.example", spoof=True)
        assert response.status_code == status
        _assert_security_headers(response)
        assert response.json()["error"]["code"] == code
    _assert_cleanup(run, temp_root)


def main() -> int:
    it = _normal_scenario("w02-it", start_ui=True)
    it_hidden_mutated = _normal_scenario("w02-it-hidden-mutated")
    analyst = _normal_scenario("w02-analyst")
    multi = _normal_scenario("w02-multi-role")

    assert it == it_hidden_mutated
    assert len(it["sources"]) == 1
    assert it["score"]["value"] == 40
    assert it["tlp"] == "TLP:GREEN"
    assert len(analyst["sources"]) == 2
    assert analyst["tlp"] == "TLP:AMBER"
    assert analyst == multi
    assert analyst != it

    _error_scenario("w02-missing-token", 401, "authentication_required")
    _error_scenario("w02-forbidden", 403, "forbidden")
    _error_scenario("w02-lookup-503", 503, "lookup_unavailable")

    print(
        json.dumps(
            {
                "status": "PASS",
                "checks": 37,
                "route_api_same_run": True,
                "states": ["found", "allowlisted", "not_found"],
                "roles": ["it", "analyst", "it+analyst"],
                "errors": [401, 403, 422, 503],
                "hidden_data_invariant": True,
                "spoof_resistance": True,
                "cleanup": True,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
