"""Ma trận HTTP thật W04 qua gateway loopback, không khởi động UI."""

from __future__ import annotations

import argparse
import json
import socket
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx

from tools.local_integration.runner import LocalRun


class Matrix:
    def __init__(self) -> None:
        self.assertions = 0

    def check(self, condition: bool, label: str) -> None:
        self.assertions += 1
        if not condition:
            raise AssertionError(label)


def _json_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(method, url, timeout=2, **kwargs)


def _db_counts(path: Path) -> tuple[int, int]:
    with closing(sqlite3.connect(path)) as connection:
        assets = connection.execute("SELECT count(*) FROM assets").fetchone()[0]
        audits = connection.execute("SELECT count(*) FROM asset_audit").fetchone()[0]
    return int(assets), int(audits)


def _assert_security_headers(matrix: Matrix, response: httpx.Response, label: str) -> None:
    matrix.check(response.headers.get("cache-control") == "no-store", f"{label}: no-store")
    matrix.check(response.headers.get("vary") == "Cf-Access-Jwt-Assertion", f"{label}: vary")


def _assert_match(matrix: Matrix, base: str, value: str, expected: list[str], state: str) -> None:
    response = _json_request("GET", f"{base}/api/ioc", params={"value": value})
    matrix.check(response.status_code == 200, f"lookup {value}: status")
    body = response.json()
    matrix.check(body["state"] == state, f"lookup {value}: state")
    matrix.check(
        body["asset_match"] == {"matched": bool(expected), "assets": expected},
        f"lookup {value}: asset match",
    )


def _run_primary(matrix: Matrix) -> dict[str, Any]:
    run = LocalRun("w04-it", duration_seconds=30, start_ui=False)
    with run:
        origin = run.url
        spoofed = _json_request(
            "GET",
            f"{run.url}/api/assets",
            headers={"Cf-Access-Jwt-Assertion": "caller-controlled-invalid-token"},
        )
        matrix.check(spoofed.status_code == 200, "gateway replaces caller JWT")
        matrix.check(spoofed.json() == {"items": []}, "initial assets empty")
        _assert_security_headers(matrix, spoofed, "initial list")

        wrong_origin = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": "http://127.0.0.1:1"},
            json={"type": "domain", "value": "company.example", "note": "synthetic"},
        )
        matrix.check(wrong_origin.status_code == 403, "wrong Origin rejected")
        matrix.check(_db_counts(run.db_path) == (0, 0), "wrong Origin precedes mutation")

        oversized = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": origin, "Content-Type": "application/json"},
            content=b"{" + (b"x" * 8192) + b"}",
        )
        matrix.check(oversized.status_code == 413, "gateway 8 KiB limit")
        matrix.check(_db_counts(run.db_path) == (0, 0), "body limit precedes mutation")

        domain = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": origin},
            json={"type": "domain", "value": "company.example", "note": "synthetic domain"},
        )
        matrix.check(domain.status_code == 201, "create domain")
        domain_body = domain.json()
        matrix.check(domain_body["version"] == 1, "create version 1")

        duplicate = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": origin},
            json={"type": "domain", "value": "company.example", "note": "duplicate"},
        )
        matrix.check(duplicate.status_code == 409, "duplicate canonical conflict")
        matrix.check(duplicate.json()["error"]["code"] == "asset_exists", "duplicate code")

        cidr = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": origin},
            json={"type": "ip_range", "value": "8.8.8.0/24", "note": "synthetic public range"},
        )
        matrix.check(cidr.status_code == 201, "create CIDR")

        updated = _json_request(
            "PUT",
            f"{run.url}/api/assets/{domain_body['id']}",
            headers={"Origin": origin},
            json={
                "type": "domain",
                "value": "company.example",
                "note": "updated synthetic domain",
                "expected_version": 1,
            },
        )
        matrix.check(updated.status_code == 200, "update domain")
        matrix.check(updated.json()["version"] == 2, "update increments version")

        stale = _json_request(
            "PUT",
            f"{run.url}/api/assets/{domain_body['id']}",
            headers={"Origin": origin},
            json={
                "type": "domain",
                "value": "company.example",
                "note": "stale",
                "expected_version": 1,
            },
        )
        matrix.check(stale.status_code == 409, "stale version conflict")
        matrix.check(stale.json()["error"]["code"] == "asset_conflict", "stale code")

        listed = _json_request("GET", f"{run.url}/api/assets")
        matrix.check(listed.status_code == 200, "list assets")
        matrix.check(len(listed.json()["items"]) == 2, "list returns same DB assets")
        _assert_match(matrix, run.url, "company.example", ["company.example"], "allowlisted")
        _assert_match(matrix, run.url, "mail.company.example", ["company.example"], "allowlisted")
        _assert_match(matrix, run.url, "8.8.8.7", ["8.8.8.0/24"], "allowlisted")
        _assert_match(
            matrix,
            run.url,
            "https://mail.company.example/path?q=synthetic",
            ["company.example"],
            "not_found",
        )

        deleted = _json_request(
            "DELETE",
            f"{run.url}/api/assets/{domain_body['id']}",
            headers={"Origin": origin},
            params={"expected_version": 2},
        )
        matrix.check(deleted.status_code == 204, "delete domain")
        _assert_match(matrix, run.url, "mail.company.example", [], "not_found")

        with closing(sqlite3.connect(run.db_path)) as connection:
            audit = connection.execute(
                "SELECT actor_subject,action,asset_id,before_json,after_json FROM asset_audit ORDER BY id"
            ).fetchall()
            active = connection.execute(
                "SELECT type,canonical_value,version FROM assets WHERE deleted_at IS NULL ORDER BY id"
            ).fetchall()
        matrix.check(
            [row[1] for row in audit]
            == [
                "asset_created",
                "asset_created",
                "asset_updated",
                "asset_deleted",
            ],
            "audit action order",
        )
        matrix.check(all(row[0] == "it-sub" for row in audit), "audit actor from verified principal")
        matrix.check(audit[2][3] is not None and audit[2][4] is not None, "update before/after audit")
        matrix.check(audit[3][3] is not None and audit[3][4] is None, "delete before audit")
        matrix.check(active == [("ip_range", "8.8.8.0/24", 1)], "delete changes same DB snapshot")
        temp_root = run.temp_root
        gateway_port = run.gateway_port
        gateway_pid = run._gateway_process.pid if run._gateway_process is not None else None
        api_thread_name = run._api_thread.name if run._api_thread is not None else None

    matrix.check(not temp_root.exists(), "primary temp root removed")
    try:
        socket.create_connection(("127.0.0.1", gateway_port), timeout=0.2)
    except OSError:
        matrix.check(True, "primary gateway port closed")
    else:
        matrix.check(False, "primary gateway port closed")
    return {
        "asset_rows_total": 2,
        "active_asset_rows": 1,
        "audit_rows": 4,
        "gateway_pid": gateway_pid,
        "gateway_port": gateway_port,
        "api_thread": api_thread_name,
        "cleanup": {"temp_root_removed": True, "gateway_port_closed": True},
    }


def _run_roles(matrix: Matrix) -> dict[str, int]:
    expected = {
        "w04-it": 200,
        "w04-analyst": 200,
        "w04-multi-role": 200,
        "w04-forbidden": 403,
        "w04-missing-token": 401,
    }
    observed: dict[str, int] = {}
    for scenario, status in expected.items():
        with LocalRun(scenario, duration_seconds=20, start_ui=False) as run:
            response = _json_request("GET", f"{run.url}/api/assets")
            observed[scenario] = response.status_code
            matrix.check(response.status_code == status, f"role scenario {scenario}")
            _assert_security_headers(matrix, response, scenario)
    return observed


def _run_refresh_fault(matrix: Matrix) -> dict[str, Any]:
    with LocalRun("w04-refresh-503", duration_seconds=20, start_ui=False) as run:
        created = _json_request(
            "POST",
            f"{run.url}/api/assets",
            headers={"Origin": run.url},
            json={"type": "domain", "value": "refresh.example", "note": "synthetic refresh fault"},
        )
        matrix.check(created.status_code == 201, "refresh mutation committed")
        first_get = _json_request("GET", f"{run.url}/api/assets")
        second_get = _json_request("GET", f"{run.url}/api/assets")
        matrix.check(first_get.status_code == 503, "first refresh fault")
        matrix.check(second_get.status_code == 200, "second refresh recovers")
        matrix.check(len(second_get.json()["items"]) == 1, "committed asset retained")
        counts = _db_counts(run.db_path)
        matrix.check(counts == (1, 1), "no mutation replay and one audit")
        temp_root = run.temp_root
        port = run.gateway_port
    matrix.check(not temp_root.exists(), "fault temp root removed")
    try:
        socket.create_connection(("127.0.0.1", port), timeout=0.2)
    except OSError:
        matrix.check(True, "fault gateway port closed")
    else:
        matrix.check(False, "fault gateway port closed")
    return {
        "mutation_requests": 1,
        "refresh_get_requests": 2,
        "refresh_statuses": [503, 200],
        "asset_rows": counts[0],
        "audit_rows": counts[1],
        "cleanup": {"temp_root_removed": True, "gateway_port_closed": True},
    }


def _run_unknown_outcome(matrix: Matrix) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="w04-trace-") as trace_root:
        trace_path = Path(trace_root) / "gateway-trace.jsonl"
        with LocalRun(
            "w04-unknown-outcome",
            duration_seconds=20,
            start_ui=False,
            trace_path=trace_path,
        ) as run:
            created = _json_request(
                "POST",
                f"{run.url}/api/assets",
                headers={"Origin": run.url},
                json={"type": "domain", "value": "unknown.example", "note": "synthetic unknown outcome"},
            )
            matrix.check(created.status_code == 503, "unknown outcome hides committed success")
            matrix.check(
                created.json()["error"]["code"] == "synthetic_unknown_outcome",
                "unknown outcome code",
            )
            reconciled = _json_request("GET", f"{run.url}/api/assets")
            matrix.check(reconciled.status_code == 200, "unknown outcome reconcile GET")
            matrix.check(len(reconciled.json()["items"]) == 1, "unknown outcome commit visible")
            counts = _db_counts(run.db_path)
            matrix.check(counts == (1, 1), "unknown outcome does not replay mutation")
            trace = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
            matrix.check(
                trace
                == [
                    {"counter": 1, "method": "POST", "path": "/api/assets", "status": 503},
                    {"counter": 2, "method": "GET", "path": "/api/assets", "status": 200},
                ],
                "unknown outcome sanitized trace",
            )
        matrix.check("jwt" not in trace_path.read_text(encoding="utf-8").lower(), "trace excludes JWT")
    return {
        "mutation_requests": 1,
        "reconcile_get_requests": 1,
        "statuses": [503, 200],
        "asset_rows": counts[0],
        "audit_rows": counts[1],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    matrix = Matrix()
    result = {
        "status": "PASS",
        "primary": _run_primary(matrix),
        "roles": _run_roles(matrix),
        "refresh_recovery": _run_refresh_fault(matrix),
        "unknown_outcome": _run_unknown_outcome(matrix),
    }
    result["assertions"] = matrix.assertions
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
