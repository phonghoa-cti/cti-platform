"""Ma trận HTTP thật W03 status qua gateway loopback tổng hợp."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx

from tools.local_integration.runner import LocalRun
from tools.local_integration.w03_fixture import FIXTURE_PATH

RELATION = "/api/cves/CVE-2026-2001/technologies/1"
STATUS = RELATION + "/status"
HISTORY = RELATION + "/status-history"


class Matrix:
    def __init__(self) -> None:
        self.assertions = 0

    def check(self, condition: bool, label: str) -> None:
        self.assertions += 1
        if not condition:
            raise AssertionError(label)


def request(method: str, base: str, path: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(method, base + path, timeout=5, **kwargs)


def security_headers(matrix: Matrix, response: httpx.Response, label: str) -> None:
    matrix.check(response.headers.get("cache-control") == "no-store", f"{label} no-store")
    matrix.check(response.headers.get("vary") == "Cf-Access-Jwt-Assertion", f"{label} vary")


def sql_snapshot(path: Path) -> dict[str, Any]:
    with closing(sqlite3.connect(path)) as connection:
        schema = connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        ).fetchall()
        tables = {}
        existing = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in (
            "technology_assets",
            "technology_asset_audit",
            "cve_status_records",
            "cve_status_audit",
            "w03_status_migrations",
        ):
            tables[table] = (
                connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                if table in existing
                else []
            )
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":"), default=str)
    return {
        "schema_sha256": hashlib.sha256(schema_json.encode()).hexdigest(),
        "user_version": user_version,
        "rows": tables,
    }


def counts(snapshot: dict[str, Any]) -> dict[str, int]:
    return {name: len(rows) for name, rows in snapshot["rows"].items()}


def body(
    context: dict[str, Any], version: int, state: str = "open", note: str = "Đã kiểm tra"
) -> dict[str, Any]:
    return {
        "status": state,
        "note": note,
        "expected_status_version": version,
        "expected_technology_record_version": context["technology_record_version"],
        "expected_dataset_id": context["dataset_id"],
    }


def put(base: str, payload: dict[str, Any]) -> httpx.Response:
    return request("PUT", base, STATUS, headers={"Origin": base}, json=payload)


def backup(path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(destination)) as target:
        source.backup(target)


def primary(matrix: Matrix, evidence: Path) -> dict[str, Any]:
    trace = evidence / "primary-trace.jsonl"
    trace.unlink(missing_ok=True)
    with LocalRun("w03-status-it", duration_seconds=60, start_ui=False, trace_path=trace) as run:
        before_get = sql_snapshot(run.db_path)
        unset = request("GET", run.url, STATUS)
        security_headers(matrix, unset, "unset")
        matrix.check(unset.status_code == 200 and unset.json()["record"] is None, "unset GET")
        matrix.check(sql_snapshot(run.db_path) == before_get, "unset GET does not create row")
        context = unset.json()["context"]

        committed = put(run.url, body(context, 0, note='Kiểm tra "Unicode"  😀'))
        matrix.check(committed.status_code == 200, "first PUT 200")
        matrix.check(committed.json()["record"]["status_version"] == 1, "first status v1")
        first = sql_snapshot(run.db_path)
        matrix.check(counts(first)["cve_status_records"] == 1, "one status row")
        matrix.check(counts(first)["cve_status_audit"] == 1, "one audit row")

        updated = put(run.url, body(context, 1, "patching", "Đang vá"))
        matrix.check(updated.status_code == 200, "update PUT 200")
        matrix.check(updated.json()["record"]["status_version"] == 2, "update status v2")
        second = sql_snapshot(run.db_path)
        matrix.check(counts(second)["cve_status_records"] == 1, "update keeps one status")
        matrix.check(counts(second)["cve_status_audit"] == 2, "update adds second audit")

        page1 = request("GET", run.url, HISTORY + "?limit=1")
        cursor = page1.json()["page"]["next_cursor"]
        matrix.check(page1.status_code == 200 and len(page1.json()["items"]) == 1, "history page 1")
        page2 = request("GET", run.url, HISTORY + f"?limit=1&cursor={cursor}")
        matrix.check(page2.status_code == 200 and len(page2.json()["items"]) == 1, "history page 2")
        matrix.check(sql_snapshot(run.db_path) == second, "history GETs read-only")

        stale = put(run.url, body(context, 1, "patched", "stale"))
        matrix.check(
            (stale.status_code, stale.json()["error"]["code"]) == (409, "status_version_conflict"),
            "stale status 409",
        )
        matrix.check(sql_snapshot(run.db_path) == second, "stale status no write")

        third = put(run.url, body(context, 2, "patched", "Đã vá"))
        matrix.check(third.status_code == 200, "third PUT")
        before_stale_cursor = sql_snapshot(run.db_path)
        stale_cursor = request("GET", run.url, HISTORY + f"?limit=1&cursor={cursor}")
        matrix.check(
            (stale_cursor.status_code, stale_cursor.json()["error"]["code"])
            == (409, "status_snapshot_changed"),
            "old cursor 409",
        )
        matrix.check(sql_snapshot(run.db_path) == before_stale_cursor, "old cursor no write")
        restarted = request("GET", run.url, HISTORY + "?limit=1")
        matrix.check(restarted.status_code == 200, "history restart 200")

        large_note = "😀" * 700
        large_payload = json.dumps(body(context, 3, "open", large_note), ensure_ascii=True).encode()
        matrix.check(8192 < len(large_payload) <= 16384, "valid payload crosses 8 KiB only")
        large = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url, "Content-Type": "application/json"},
            content=large_payload,
        )
        matrix.check(
            large.status_code == 200 and large.json()["record"]["status_version"] == 4,
            "16 KiB status allowance",
        )
        before_oversize = sql_snapshot(run.db_path)
        oversize = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url, "Content-Type": "application/json"},
            content=b"{" + b" " * 16384,
        )
        matrix.check(oversize.status_code == 413, "over 16 KiB rejected")
        matrix.check(sql_snapshot(run.db_path) == before_oversize, "over 16 KiB no write")

        invalid_cases = [
            ({}, {}, 403),
            ({"Origin": run.url}, {}, 415),
        ]
        for headers, payload, expected in invalid_cases:
            response = request("PUT", run.url, STATUS, headers=headers, content=json.dumps(payload))
            matrix.check(response.status_code == expected, f"protocol {expected}")
            matrix.check(sql_snapshot(run.db_path) == before_oversize, f"protocol {expected} no write")
        for field, value in (("expected_status_version", True), ("expected_technology_record_version", 1.5)):
            invalid = body(context, 4)
            invalid[field] = value
            response = put(run.url, invalid)
            matrix.check(response.status_code == 422, f"strict {field}")
            matrix.check(sql_snapshot(run.db_path) == before_oversize, f"strict {field} no write")
        duplicate = json.dumps(body(context, 4))[:-1] + ',"expected_status_version":4}'
        duplicate_response = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url, "Content-Type": "application/json"},
            content=duplicate,
        )
        matrix.check(duplicate_response.status_code == 422, "duplicate JSON key rejected")
        matrix.check(sql_snapshot(run.db_path) == before_oversize, "duplicate key no write")

        backup(run.db_path, evidence / "primary-before-cleanup.sqlite")
        final_snapshot = sql_snapshot(run.db_path)
        temp_root, port = run.temp_root, run.gateway_port
    matrix.check(not temp_root.exists(), "primary temp cleanup")
    try:
        socket.create_connection(("127.0.0.1", port), timeout=0.2)
        matrix.check(False, "primary port closed")
    except OSError:
        matrix.check(True, "primary port closed")
    return {"counts": counts(final_snapshot), "trace": trace.name}


def roles_and_allowlist(matrix: Matrix) -> dict[str, int]:
    expected = {
        "w03-status-it": 200,
        "w03-status-analyst": 200,
        "w03-status-admin": 200,
        "w03-status-multi-role": 200,
        "w03-status-leader": 403,
        "w03-status-missing-token": 401,
    }
    observed = {}
    for scenario, status in expected.items():
        with LocalRun(scenario, duration_seconds=30, start_ui=False) as run:
            before = sql_snapshot(run.db_path)
            response = request("GET", run.url, STATUS)
            observed[scenario] = response.status_code
            matrix.check(response.status_code == status, scenario)
            security_headers(matrix, response, scenario)
            matrix.check(sql_snapshot(run.db_path) == before, f"{scenario} GET no write")
            if status == 200:
                mutation = put(run.url, body(response.json()["context"], 0))
                matrix.check(mutation.status_code == 200, f"{scenario} PUT allowed")
                history = request("GET", run.url, HISTORY)
                matrix.check(
                    history.status_code == 200 and len(history.json()["items"]) == 1,
                    f"{scenario} history allowed",
                )
            else:
                mutation = request(
                    "PUT",
                    run.url,
                    STATUS,
                    headers={"Origin": run.url, "Content-Type": "application/json"},
                    content="{}",
                )
                history = request("GET", run.url, HISTORY)
                matrix.check(mutation.status_code == status, f"{scenario} PUT denied")
                matrix.check(history.status_code == status, f"{scenario} history denied")
                matrix.check(sql_snapshot(run.db_path) == before, f"{scenario} denied no write")
            if scenario == "w03-status-missing-token":
                spoofed = request("GET", run.url, STATUS, headers={"Cf-Access-Jwt-Assertion": "caller"})
                matrix.check(spoofed.status_code == 401, "client JWT cannot elevate")
            for path, method in (
                (STATUS + "/", "GET"),
                (RELATION + "/status-extra", "GET"),
                ("/api/cves/CVE-2026-2001/technologies/01/status", "GET"),
                (STATUS, "POST"),
                (HISTORY, "PUT"),
            ):
                blocked = request(method, run.url, path)
                matrix.check(blocked.status_code == 404, f"allowlist blocks {method} {path}")
    return observed


def first_write_race(matrix: Matrix) -> dict[str, Any]:
    with LocalRun("w03-status-it", duration_seconds=30, start_ui=False) as run:
        context = request("GET", run.url, STATUS).json()["context"]
        payloads = [body(context, 0, note="one"), body(context, 0, note="two")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda value: put(run.url, value), payloads))
        statuses = sorted(response.status_code for response in responses)
        snapshot = sql_snapshot(run.db_path)
        matrix.check(statuses == [200, 409], "first write race one winner")
        matrix.check(counts(snapshot)["cve_status_records"] == 1, "race one status")
        matrix.check(counts(snapshot)["cve_status_audit"] == 1, "race one audit")
    return {"statuses": statuses, "counts": counts(snapshot)}


def context_changes(matrix: Matrix) -> dict[str, Any]:
    with LocalRun("w03-status-it", duration_seconds=45, start_ui=False) as run:
        context = request("GET", run.url, STATUS).json()["context"]
        matrix.check(put(run.url, body(context, 0)).status_code == 200, "context baseline write")
        before = sql_snapshot(run.db_path)
        changed = request(
            "PUT",
            run.url,
            "/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": "Fortinet",
                "product": "FortiOS",
                "software_version": "7.4.3",
                "note": "drift",
                "expected_version": 1,
            },
        )
        matrix.check(changed.status_code == 200, "W04 version change")
        after_w04 = sql_snapshot(run.db_path)
        matrix.check(after_w04 != before, "controlled W04 mutation recorded")
        stale = put(run.url, body(context, 1, "patched"))
        matrix.check(
            (stale.status_code, stale.json()["error"]["code"]) == (409, "status_context_changed"),
            "old context 409",
        )
        matrix.check(sql_snapshot(run.db_path) == after_w04, "old context no status write")
        reviewed = request("GET", run.url, STATUS)
        matrix.check(
            reviewed.status_code == 200 and reviewed.json()["review_required"] is True, "GET marks review"
        )
        current = reviewed.json()["context"]
        confirmed = put(run.url, body(current, 1, "patched", "human confirm"))
        matrix.check(confirmed.status_code == 200, "current context writes")

        case_changed = request(
            "PUT",
            run.url,
            "/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": "FORTINET",
                "product": "FORTIOS",
                "software_version": "7.4.3",
                "note": "case",
                "expected_version": 2,
            },
        )
        matrix.check(case_changed.status_code == 200, "case-only rename accepted")
        case_read = request("GET", run.url, STATUS)
        matrix.check(
            case_read.status_code == 200 and case_read.json()["record"] is not None, "case-only keeps status"
        )
        case_history = request("GET", run.url, HISTORY)
        matrix.check(
            case_history.status_code == 200 and len(case_history.json()["items"]) == 2,
            "case-only keeps history",
        )

        before_dataset = sql_snapshot(run.db_path)
        fixture = json.loads(run.cve_fixture_path.read_text(encoding="utf-8"))
        fixture["retrieved_at"] = "2026-11-12T03:00:00Z"
        run.cve_fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        dataset_read = request("GET", run.url, STATUS)
        matrix.check(
            dataset_read.status_code == 200 and dataset_read.json()["review_required"] is True,
            "dataset drift review",
        )
        stale_dataset = put(run.url, body(case_read.json()["context"], 2, "open"))
        matrix.check(
            (stale_dataset.status_code, stale_dataset.json()["error"]["code"])
            == (409, "status_context_changed"),
            "dataset old context 409",
        )
        matrix.check(sql_snapshot(run.db_path) == before_dataset, "dataset failure no SQL write")

        deleted = request(
            "DELETE", run.url, "/api/assets/technologies/1?expected_version=3", headers={"Origin": run.url}
        )
        matrix.check(deleted.status_code == 204, "technology delete controlled")
        recreated = request(
            "POST",
            run.url,
            "/api/assets/technologies",
            headers={"Origin": run.url},
            json={
                "vendor": "Fortinet",
                "product": "FortiOS",
                "software_version": "7.4.3",
                "note": "recreated",
            },
        )
        matrix.check(recreated.status_code == 201, "technology recreated")
        new_id = recreated.json()["id"]
        new_status = f"/api/cves/CVE-2026-2001/technologies/{new_id}/status"
        recreated_read = request("GET", run.url, new_status)
        matrix.check(
            recreated_read.status_code == 200 and recreated_read.json()["record"] is None,
            "delete/recreate does not inherit",
        )
        matrix.check(request("GET", run.url, STATUS).status_code == 404, "deleted relation unavailable")
        identity = request(
            "PUT",
            run.url,
            f"/api/assets/technologies/{new_id}",
            headers={"Origin": run.url},
            json={
                "vendor": "Other",
                "product": "Product",
                "software_version": "1",
                "note": "identity",
                "expected_version": 1,
            },
        )
        matrix.check(identity.status_code == 200, "identity change controlled")
        identity_read = request("GET", run.url, new_status)
        matrix.check(identity_read.status_code == 404, "identity change does not inherit")
        final_snapshot = sql_snapshot(run.db_path)
    return {"counts": counts(final_snapshot), "identity_status": identity_read.status_code}


def faults(matrix: Matrix, evidence: Path) -> dict[str, Any]:
    results = {}
    for scenario, put_status, gets in (
        ("w03-status-known-commit", 200, [503, 503, 200]),
        ("w03-status-unknown-outcome", 503, [503, 200]),
    ):
        trace = evidence / f"{scenario}-trace.jsonl"
        trace.unlink(missing_ok=True)
        with LocalRun(scenario, duration_seconds=30, start_ui=False, trace_path=trace) as run:
            context = request("GET", run.url, STATUS).json()["context"]
            committed = put(run.url, body(context, 0))
            matrix.check(committed.status_code == put_status, f"{scenario} PUT status")
            after_put = sql_snapshot(run.db_path)
            other_relation = request(
                "GET",
                run.url,
                "/api/cves/CVE-2026-2013/technologies/2/status",
            )
            history = request("GET", run.url, HISTORY)
            matrix.check(other_relation.status_code == 200, f"{scenario} other relation bypasses fault")
            matrix.check(history.status_code == 200, f"{scenario} history bypasses fault")
            matrix.check(
                sql_snapshot(run.db_path) == after_put,
                f"{scenario} interleaved GETs do not mutate SQL",
            )
            statuses = [request("GET", run.url, STATUS).status_code for _ in gets]
            matrix.check(statuses == gets, f"{scenario} GET recovery")
            snapshot = sql_snapshot(run.db_path)
            matrix.check(counts(snapshot)["cve_status_records"] == 1, f"{scenario} one status")
            matrix.check(counts(snapshot)["cve_status_audit"] == 1, f"{scenario} one audit")
            records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
            matrix.check(sum(row["method"] == "PUT" for row in records) == 1, f"{scenario} exactly one PUT")
            matrix.check(
                not any("token" in json.dumps(row).lower() for row in records), f"{scenario} trace sanitized"
            )
            backup(run.db_path, evidence / f"{scenario}-before-cleanup.sqlite")
        results[scenario] = {
            "put": put_status,
            "interleaved": {
                "other_relation": other_relation.status_code,
                "history": history.status_code,
            },
            "gets": gets,
            "counts": counts(snapshot),
        }
    return results


def schema_failure(matrix: Matrix) -> dict[str, Any]:
    with LocalRun("w03-status-it", duration_seconds=30, start_ui=False) as run:
        with closing(sqlite3.connect(run.db_path)) as connection:
            connection.execute("UPDATE w03_status_migrations SET version=2")
            connection.commit()
        before = sql_snapshot(run.db_path)
        failed = request("GET", run.url, STATUS)
        after = sql_snapshot(run.db_path)
        matrix.check(
            (failed.status_code, failed.json()["error"]["code"]) == (503, "status_unavailable"),
            "schema damage 503",
        )
        matrix.check(after == before, "request does not migrate damaged schema")
    with LocalRun("w04-technology-it", duration_seconds=30, start_ui=False) as run:
        before_unconfigured = sql_snapshot(run.db_path)
        unconfigured = request("GET", run.url, STATUS)
        matrix.check(unconfigured.status_code == 503, "status opt-in only")
        matrix.check(
            sql_snapshot(run.db_path) == before_unconfigured, "unconfigured request does not create schema"
        )
    return {"damaged": failed.status_code, "unconfigured": unconfigured.status_code}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    output, evidence = args.output.resolve(), args.evidence_dir.resolve()
    if not FIXTURE_PATH.is_file():
        raise RuntimeError("fixture W03 bắt buộc không tồn tại")
    fixture_sha256 = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
    evidence.mkdir(parents=True, exist_ok=True)
    matrix = Matrix()
    result = {
        "fixture": {"path": FIXTURE_PATH.as_posix(), "sha256": fixture_sha256},
        "primary": primary(matrix, evidence),
        "roles_and_allowlist": roles_and_allowlist(matrix),
        "first_write_race": first_write_race(matrix),
        "context_changes": context_changes(matrix),
        "faults": faults(matrix, evidence),
        "schema_failure": schema_failure(matrix),
    }
    result.update({"assertions": matrix.assertions, "status": "PASS"})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"assertions": matrix.assertions, "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
