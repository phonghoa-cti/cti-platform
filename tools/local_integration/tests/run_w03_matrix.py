"""Ma trận W03 qua gateway/API thật trên SQLite W04 tổng hợp."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import httpx

from tools.local_integration.runner import LocalRun

NOTICE = "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá."


class Matrix:
    def __init__(self) -> None:
        self.checks = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            raise AssertionError(message)


def sql_snapshot(path: Path) -> dict[str, Any]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        schema = connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        tables = [row[1] for row in schema if row[0] == "table"]
        rows: dict[str, list[list[Any]]] = {}
        for table in tables:
            quoted = table.replace('"', '""')
            rows[table] = [
                list(row) for row in connection.execute(f'SELECT * FROM "{quoted}" ORDER BY rowid')
            ]
    canonical_schema = json.dumps(schema, ensure_ascii=False, separators=(",", ":"), default=str).encode()
    canonical_rows = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), default=str).encode()
    return {
        "schema_sha256": hashlib.sha256(canonical_schema).hexdigest(),
        "rows_sha256": hashlib.sha256(canonical_rows).hexdigest(),
        "user_version": user_version,
        "table_counts": {name: len(value) for name, value in rows.items()},
    }


def assert_get_immutable(matrix: Matrix, run: LocalRun, path: str, status: int) -> httpx.Response:
    before = sql_snapshot(run.db_path)
    response = httpx.get(f"{run.url}{path}", timeout=3)
    after = sql_snapshot(run.db_path)
    matrix.check(response.status_code == status, f"{path} status {status}")
    matrix.check(before == after, f"{path} SQL immutable")
    return response


def assert_headers(matrix: Matrix, response: httpx.Response) -> None:
    matrix.check(response.headers.get("cache-control") == "no-store", "Cache-Control no-store")
    matrix.check(response.headers.get("vary") == "Cf-Access-Jwt-Assertion", "Vary JWT")


def collect_pages(matrix: Matrix, run: LocalRun) -> tuple[list[dict[str, Any]], str]:
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    first_cursor = ""
    priorities: list[int] = []
    while True:
        params = {"limit": "5"}
        if cursor is not None:
            params["cursor"] = cursor
        response = httpx.get(f"{run.url}/api/cves", params=params, timeout=3)
        matrix.check(response.status_code == 200, "paging GET 200")
        body = response.json()
        matrix.check(body["notice"] == NOTICE, "notice literal")
        if not first_cursor:
            first_cursor = body["page"]["next_cursor"]
        items.extend(body["items"])
        priorities.extend(item["priority"] for item in body["items"])
        cursor = body["page"]["next_cursor"]
        if cursor is None:
            break
    ids = [item["cve_id"] for item in items]
    matrix.check(len(ids) == 16, "16 matched candidates")
    matrix.check(len(set(ids)) == len(ids), "paging no duplicates")
    matrix.check(priorities == list(range(1, 17)), "paging no omissions and continuous rank")
    matrix.check(items[0]["kev"] is True, "KEV first")
    by_id = {item["cve_id"]: item for item in items}
    matrix.check(
        by_id["CVE-2026-2012"]["epss_score"] == 0 and by_id["CVE-2026-2012"]["cvss_base_score"] == 0,
        "zero preserved",
    )
    matrix.check(
        by_id["CVE-2026-2013"]["epss_score"] is None and by_id["CVE-2026-2013"]["cvss_base_score"] is None,
        "null preserved",
    )
    matrix.check(items[0]["matches"][0]["software_version"] == "7.4.2", "version display only")
    return items, first_cursor


def capture_large_real_api_wires(matrix: Matrix, wire_dir: Path) -> dict[str, Any]:
    """Tìm response lớn nhất còn 200 từ API thật; response kế tiếp phải fail closed."""

    from portal_api.tests import test_w02_ioc_api as w02_test_api
    from portal_api.tests.test_cves_api import StaticPort, _candidate, _client, _dataset, _get, _store

    private_key_and_jwk = w02_test_api.rsa_keys.__wrapped__()
    with tempfile.TemporaryDirectory(prefix="w03-large-wire-") as temporary:
        temp_root = Path(temporary)
        store = _store(temp_root)
        stamp = "2026-11-01T00:00:00Z"
        connection = sqlite3.connect(store.path)
        try:
            connection.executemany(
                "INSERT INTO technology_assets(vendor,vendor_key,product,product_key,software_version,note,"
                "record_version,created_by,created_at,updated_at,deleted_at) "
                "VALUES(?,?,?,?,?,?,1,?,?,?,NULL)",
                [
                    (
                        "Fortinet",
                        "fortinet",
                        "FortiOS",
                        "fortios",
                        str(index),
                        "",
                        "setup-large",
                        stamp,
                        stamp,
                    )
                    for index in range(1000)
                ],
            )
            connection.commit()
        finally:
            connection.close()
        largest: httpx.Response | Any | None = None
        over: httpx.Response | Any | None = None
        largest_count = 0
        for count in range(1, 26):
            candidates = [_candidate(f"CVE-2026-{30000 + index}") for index in range(count)]
            client, private_key = _client(
                temp_root, private_key_and_jwk, port=StaticPort(_dataset(candidates)), store=store
            )
            try:
                response = _get(client, private_key, "?limit=100")
            finally:
                client.close()
            if response.status_code == 200:
                largest = response
                largest_count = count
                continue
            over = response
            break
        matrix.check(largest is not None, "large valid API response exists")
        matrix.check(over is not None, "over-cap API response exists")
        matrix.check(
            over.status_code == 503 and over.json()["error"]["code"] == "cves_unavailable",
            "over cap fails 503",
        )
        body = largest.content
        matrix.check(len(body) > 700_000, "large valid response is near cap")
        matrix.check(len(body) <= 1024 * 1024, "large valid response stays within cap")
        (wire_dir / "near-cap.json").write_bytes(body)
        (wire_dir / "over-cap.json").write_bytes(over.content)
        return {
            "candidate_count": largest_count,
            "response_bytes": len(body),
            "over_status": over.status_code,
        }


def run_matrix(output: Path, evidence_dir: Path) -> dict[str, Any]:
    matrix = Matrix()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    wire_dir = evidence_dir / "wire"
    wire_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"scenarios": {}}

    trace = evidence_dir / "w03-it-trace.jsonl"
    run = LocalRun("w03-it", duration_seconds=60, start_ui=False, trace_path=trace)
    with run:
        setup_snapshot = sql_snapshot(run.db_path)
        items, stale_cursor = collect_pages(matrix, run)
        detail = assert_get_immutable(matrix, run, "/api/cves?limit=5", 200)
        assert_headers(matrix, detail)
        (wire_dir / "detail.json").write_bytes(detail.content)
        empty = assert_get_immutable(matrix, run, "/api/cves?q=ZZZZZZZZ&limit=5", 200)
        matrix.check(empty.json()["items"] == [], "empty wire")
        (wire_dir / "empty.json").write_bytes(empty.content)
        long_query = "A" * 128
        matrix.check(
            assert_get_immutable(matrix, run, f"/api/cves?q={long_query}&limit=5", 200).json()["items"] == [],
            "128-codepoint q accepted",
        )
        kev = assert_get_immutable(matrix, run, "/api/cves?kev=true&limit=100", 200).json()
        matrix.check(
            [item["cve_id"] for item in kev["items"]] == ["CVE-2026-2001", "CVE-2026-2002", "CVE-2026-2003"],
            "KEV filter/rank",
        )
        casefold = assert_get_immutable(matrix, run, "/api/cves?asset_id=1&q=fortios&limit=100", 200).json()
        matrix.check(casefold["summary"]["matched_cves"] == 15, "vendor/product exact casefold")
        missing_asset = assert_get_immutable(matrix, run, "/api/cves?asset_id=999999", 404)
        assert_headers(matrix, missing_asset)
        malformed = assert_get_immutable(matrix, run, "/api/cves?limit=1e2", 422)
        assert_headers(matrix, malformed)
        before_mutation = sql_snapshot(run.db_path)
        changed = httpx.put(
            f"{run.url}/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": "Fortinet",
                "product": "NoMatch",
                "software_version": "7.4.3",
                "note": "Controlled W04 mutation for W03 snapshot",
                "expected_version": 1,
            },
            timeout=3,
        )
        matrix.check(changed.status_code == 200, "controlled W04 update 200")
        after_mutation = sql_snapshot(run.db_path)
        matrix.check(before_mutation != after_mutation, "controlled W04 mutation changes SQL")
        stale = assert_get_immutable(matrix, run, f"/api/cves?limit=5&cursor={stale_cursor}", 409)
        assert_headers(matrix, stale)
        (wire_dir / "snapshot-changed.json").write_bytes(stale.content)
        restarted = assert_get_immutable(matrix, run, "/api/cves?limit=5", 200).json()
        matrix.check(restarted["summary"]["matched_cves"] == 1, "restart reflects new technology snapshot")
        matrix.check(restarted["items"][0]["cve_id"] == "CVE-2026-2013", "restart does not mix old page")
        result["scenarios"]["w03-it"] = {
            "controlled_mutation": {
                "before": before_mutation,
                "after": after_mutation,
                "status": changed.status_code,
            },
            "initial_items": len(items),
            "setup_snapshot": setup_snapshot,
        }
    matrix.check(not run.temp_root.exists(), "w03-it temp cleanup")
    try:
        socket.create_connection(("127.0.0.1", run.gateway_port), timeout=0.2)
        matrix.check(False, "w03-it port closed")
    except OSError:
        matrix.check(True, "w03-it port closed")

    for scenario, status, view in (
        ("w03-analyst", 200, "detail"),
        ("w03-admin", 200, "detail"),
        ("w03-multi-role", 200, "detail"),
        ("w03-leader", 200, "summary"),
        ("w03-missing-token", 401, None),
        ("w03-forbidden", 403, None),
    ):
        with LocalRun(scenario, duration_seconds=30, start_ui=False) as role_run:
            response = assert_get_immutable(matrix, role_run, "/api/cves?limit=5", status)
            assert_headers(matrix, response)
            if view is not None:
                body = response.json()
                matrix.check(body["view"] == view, f"{scenario} view")
                if view == "summary":
                    forbidden_keys = {"matches", "advisory_url", "technology_id", "software_version"}
                    matrix.check(
                        not any(forbidden_keys & set(item) for item in body["items"]),
                        "summary no asset metadata",
                    )
                    (wire_dir / "summary.json").write_bytes(response.content)
                    filtered = assert_get_immutable(matrix, role_run, "/api/cves?asset_id=1", 403)
                    assert_headers(matrix, filtered)
            else:
                (wire_dir / f"{scenario}.json").write_bytes(response.content)
            result["scenarios"][scenario] = {"status": status, "view": view}

    with LocalRun("w03-unavailable", duration_seconds=30, start_ui=False) as unavailable_run:
        unavailable = assert_get_immutable(matrix, unavailable_run, "/api/cves", 503)
        assert_headers(matrix, unavailable)
        matrix.check(unavailable.json()["error"]["code"] == "cves_unavailable", "dependency unavailable code")
        (wire_dir / "unavailable.json").write_bytes(unavailable.content)

    recovery_trace = evidence_dir / "w03-refresh-503-trace.jsonl"
    with LocalRun(
        "w03-refresh-503", duration_seconds=30, start_ui=False, trace_path=recovery_trace
    ) as recovery_run:
        first = assert_get_immutable(matrix, recovery_run, "/api/cves?limit=5", 503)
        second = assert_get_immutable(matrix, recovery_run, "/api/cves?limit=5", 200)
        matrix.check(second.json()["summary"]["matched_cves"] == 16, "manual retry 200 matches")
        result["scenarios"]["w03-refresh-503"] = {"statuses": [first.status_code, second.status_code]}

    for trace_path in (trace, recovery_trace):
        records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
        matrix.check(
            not any(record["path"] == "/api/cves" and record["method"] != "GET" for record in records),
            f"{trace_path.name} no W03 mutation",
        )

    missing_db = evidence_dir / "missing.sqlite"
    matrix.check(not missing_db.exists(), "missing DB absent before check")
    from portal_api.cves import ReadOnlyTechnologyStore
    from portal_api.technologies import TechnologyStore

    try:
        ReadOnlyTechnologyStore.from_store(TechnologyStore(missing_db)).list()
    except Exception:
        pass
    matrix.check(not missing_db.exists(), "read-only adapter does not create missing DB")

    result["large_wire"] = capture_large_real_api_wires(matrix, wire_dir)

    result.update({"checks": matrix.checks, "status": "PASS"})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"checks": matrix.checks, "scenarios": len(result["scenarios"]), "status": "PASS"}, sort_keys=True
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    run_matrix(args.output.resolve(), args.evidence_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
