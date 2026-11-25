"""Ma trận HTTP thật W04 Technology qua gateway loopback tổng hợp."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx

from tools.local_integration.runner import LocalRun

TECHNOLOGY_KEYS = {
    "id",
    "vendor",
    "product",
    "software_version",
    "note",
    "created_by",
    "created_at",
    "updated_at",
    "version",
}


class Matrix:
    def __init__(self) -> None:
        self.assertions = 0

    def check(self, condition: bool, label: str) -> None:
        self.assertions += 1
        if not condition:
            raise AssertionError(label)


def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(method, url, timeout=5, **kwargs)


def counts(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(path)) as connection:
        return {
            "assets": int(connection.execute("SELECT count(*) FROM assets").fetchone()[0]),
            "asset_audit": int(connection.execute("SELECT count(*) FROM asset_audit").fetchone()[0]),
            "technologies": int(connection.execute("SELECT count(*) FROM technology_assets").fetchone()[0]),
            "technology_audit": int(
                connection.execute("SELECT count(*) FROM technology_asset_audit").fetchone()[0]
            ),
        }


def backup(path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(destination)) as target:
        source.backup(target)


def create_technology(base: str, value: dict[str, str]) -> httpx.Response:
    return request("POST", f"{base}/api/assets/technologies", headers={"Origin": base}, json=value)


def primary(matrix: Matrix, evidence: Path | None) -> dict[str, Any]:
    with LocalRun("w04-technology-it", duration_seconds=40, start_ui=False) as run:
        before = counts(run.db_path)
        value = {
            "vendor": "Fortinet",
            "product": "FortiOS",
            "software_version": "7.2.1",
            "note": "VPN gateway tổng hợp",
        }
        created = create_technology(run.url, value)
        matrix.check(created.status_code == 201, "create technology")
        item = created.json()
        matrix.check(set(item) == TECHNOLOGY_KEYS and item["version"] == 1, "create exact DTO")

        duplicate = create_technology(
            run.url, {**value, "vendor": " FORTINET ", "product": "fortios", "note": "duplicate"}
        )
        matrix.check(duplicate.status_code == 409, "duplicate status")
        matrix.check(duplicate.json()["error"]["code"] == "technology_exists", "duplicate code")

        updated = request(
            "PUT",
            f"{run.url}/api/assets/technologies/{item['id']}",
            headers={"Origin": run.url},
            json={**value, "software_version": "7.2.2", "note": "đã cập nhật", "expected_version": 1},
        )
        matrix.check(updated.status_code == 200, "update technology")
        matrix.check(
            updated.json()["software_version"] == "7.2.2"
            and updated.json()["note"] == "đã cập nhật"
            and updated.json()["version"] == 2,
            "update fields and version",
        )
        stale = request(
            "PUT",
            f"{run.url}/api/assets/technologies/{item['id']}",
            headers={"Origin": run.url},
            json={**value, "expected_version": 1},
        )
        matrix.check(stale.status_code == 409, "stale status")
        matrix.check(stale.json()["error"]["code"] == "technology_conflict", "stale code")
        deleted = request(
            "DELETE",
            f"{run.url}/api/assets/technologies/{item['id']}",
            headers={"Origin": run.url},
            params={"expected_version": 2},
        )
        matrix.check(deleted.status_code == 204, "delete technology")
        recreated = create_technology(run.url, {**value, "software_version": "7.2.2"})
        matrix.check(recreated.status_code == 201, "recreate soft deleted identity")
        matrix.check(recreated.json()["id"] > item["id"], "recreate gets new id")

        after_technology = counts(run.db_path)
        matrix.check(before["assets"] == after_technology["assets"] == 0, "technology leaves assets")
        matrix.check(
            before["asset_audit"] == after_technology["asset_audit"] == 0,
            "technology leaves asset audit",
        )
        lookup = request("GET", f"{run.url}/api/ioc", params={"value": "fortinet.example"})
        matrix.check(lookup.status_code == 200, "W02 lookup remains available")
        matrix.check(lookup.json()["asset_match"] == {"matched": False, "assets": []}, "no W02 match")

        for payload in (
            {"type": "domain", "value": "company.example", "note": "domain smoke"},
            {"type": "ip_range", "value": "8.8.8.0/24", "note": "CIDR smoke"},
        ):
            response = request("POST", f"{run.url}/api/assets", headers={"Origin": run.url}, json=payload)
            matrix.check(response.status_code == 201, f"legacy {payload['type']} create")
        domain_lookup = request("GET", f"{run.url}/api/ioc", params={"value": "mail.company.example"})
        cidr_lookup = request("GET", f"{run.url}/api/ioc", params={"value": "8.8.8.7"})
        matrix.check(domain_lookup.json()["asset_match"]["matched"] is True, "domain lookup smoke")
        matrix.check(cidr_lookup.json()["asset_match"]["matched"] is True, "CIDR lookup smoke")
        final = counts(run.db_path)
        if evidence is not None:
            backup(run.db_path, evidence / "primary-before-cleanup.sqlite")
        with closing(sqlite3.connect(run.db_path)) as connection:
            actions = [
                row[0]
                for row in connection.execute(
                    "SELECT action FROM technology_asset_audit ORDER BY id"
                ).fetchall()
            ]
        matrix.check(
            actions
            == [
                "technology_created",
                "technology_updated",
                "technology_deleted",
                "technology_created",
            ],
            "technology audit order",
        )
    return {"before": before, "after_technology": after_technology, "final": final, "actions": actions}


def roles(matrix: Matrix) -> dict[str, int]:
    expected = {
        "w04-technology-it": 200,
        "w04-technology-analyst": 200,
        "w04-technology-multi-role": 200,
        "w04-technology-forbidden": 403,
        "w04-technology-missing-token": 401,
    }
    observed: dict[str, int] = {}
    for scenario, status in expected.items():
        with LocalRun(scenario, duration_seconds=20, start_ui=False) as run:
            response = request("GET", f"{run.url}/api/assets/technologies")
            observed[scenario] = response.status_code
            matrix.check(response.status_code == status, scenario)
            matrix.check(counts(run.db_path)["technology_audit"] == 0, f"{scenario} no audit")
    return observed


def corrupt_timestamp(matrix: Matrix) -> dict[str, Any]:
    with LocalRun("w04-technology-it", duration_seconds=20, start_ui=False) as run:
        assert run.technology_store is not None
        item = run.technology_store.create("Vendor", "Product", "1", "before", "it-sub")
        with closing(sqlite3.connect(run.db_path)) as connection:
            connection.execute(
                "UPDATE technology_assets SET updated_at='2026-11-12 00:00:00' WHERE id=?",
                (item.id,),
            )
            connection.commit()
        before = counts(run.db_path)
        listed = request("GET", f"{run.url}/api/assets/technologies")
        matrix.check(listed.status_code == 503, "corrupt timestamp GET 503")
        changed = request(
            "PUT",
            f"{run.url}/api/assets/technologies/{item.id}",
            headers={"Origin": run.url},
            json={
                "vendor": "Vendor",
                "product": "Product",
                "software_version": "2",
                "note": "must not write",
                "expected_version": 1,
            },
        )
        matrix.check(changed.status_code == 503, "corrupt timestamp PUT 503")
        with closing(sqlite3.connect(run.db_path)) as connection:
            row = connection.execute(
                "SELECT software_version,note,record_version FROM technology_assets WHERE id=?",
                (item.id,),
            ).fetchone()
        after = counts(run.db_path)
        matrix.check(row == ("1", "before", 1), "corrupt row not written")
        matrix.check(after == before, "corrupt row no extra audit")
    return {"statuses": [listed.status_code, changed.status_code], "counts": after}


def limits(matrix: Matrix, evidence: Path | None) -> dict[str, Any]:
    with LocalRun("w04-technology-it", duration_seconds=60, start_ui=False) as run:
        assert run.technology_store is not None
        for index in range(1000):
            run.technology_store.create("Vendor", f"Product-{index:04d}", "1", "", "it-sub")
        listed = request("GET", f"{run.url}/api/assets/technologies")
        matrix.check(listed.status_code == 200, "list 1000 status")
        items = listed.json()["items"]
        matrix.check(len(items) == 1000, "list 1000 complete")
        matrix.check(all(set(item) == TECHNOLOGY_KEYS for item in items), "list 1000 exact schema")
        matrix.check(items[0]["product"] == "Product-0000", "list first item")
        matrix.check(items[-1]["product"] == "Product-0999", "list last item")
        rejected = create_technology(
            run.url,
            {"vendor": "Vendor", "product": "Product-1000", "software_version": "1", "note": ""},
        )
        matrix.check(rejected.status_code == 503, "1001 rejected")
        matrix.check(rejected.json()["error"]["code"] == "assets_unavailable", "1001 code")
        final = counts(run.db_path)
        matrix.check(final["technologies"] == 1000, "1001 no row")
        matrix.check(final["technology_audit"] == 1000, "1001 no audit")
        if evidence is not None:
            backup(run.db_path, evidence / "limit-1000-before-cleanup.sqlite")
    return {"listed": len(items), "rejected_status": rejected.status_code, "counts": final}


def faults(matrix: Matrix, evidence: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for scenario, expected_gets in (
        ("w04-technology-refresh-503", [503, 503, 200]),
        ("w04-technology-unknown-outcome", [503, 200]),
    ):
        trace = None if evidence is None else evidence / f"{scenario}-trace.jsonl"
        with LocalRun(scenario, duration_seconds=30, start_ui=False, trace_path=trace) as run:
            mutation = create_technology(
                run.url,
                {"vendor": "Vendor", "product": scenario, "software_version": "1", "note": "fault"},
            )
            expected_mutation = 201 if scenario.endswith("refresh-503") else 503
            matrix.check(mutation.status_code == expected_mutation, f"{scenario} mutation")
            statuses = [
                request("GET", f"{run.url}/api/assets/technologies").status_code for _ in expected_gets
            ]
            matrix.check(statuses == expected_gets, f"{scenario} GET sequence")
            final = counts(run.db_path)
            matrix.check(final["technologies"] == 1, f"{scenario} one row")
            matrix.check(final["technology_audit"] == 1, f"{scenario} one audit")
            if evidence is not None:
                backup(run.db_path, evidence / f"{scenario}-before-cleanup.sqlite")
            result[scenario] = {
                "mutation_status": mutation.status_code,
                "get_statuses": statuses,
                "counts": final,
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    matrix = Matrix()
    result = {
        "status": "PASS",
        "primary": primary(matrix, args.evidence_dir),
        "roles": roles(matrix),
        "corrupt_timestamp": corrupt_timestamp(matrix),
        "limits": limits(matrix, args.evidence_dir),
        "faults": faults(matrix, args.evidence_dir),
    }
    result["assertions"] = matrix.assertions
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
