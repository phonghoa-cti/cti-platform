"""Ma trận HTTP thật qua gateway; mỗi scenario sở hữu DB/listener riêng."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- executable matrix bootstraps the repository root before imports

import json
import sqlite3
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.local_integration.runner import LocalRun

CHECKS = 0


def check(condition: bool, label: str) -> None:
    global CHECKS
    if not condition:
        raise AssertionError(label)
    CHECKS += 1


def audit_count(db_path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM draft_audit").fetchone()[0])
    finally:
        connection.close()


def draft_row(db_path, draft_id: int):
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute(
            "SELECT payload_json, review_status, review_version, decided_by_subject, decision_reason "
            "FROM drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()
    finally:
        connection.close()


def expect_error(response: httpx.Response, status: int, code: str) -> None:
    check(response.status_code == status, f"expected {status}, got {response.status_code}")
    check(response.json()["error"]["code"] == code, f"expected {code}")
    check(response.headers.get("cache-control") == "no-store", "error must be no-store")


def admin_matrix() -> None:
    with LocalRun("admin-other", duration_seconds=30, start_ui=False) as run:
        with httpx.Client(base_url=run.url, timeout=2) as client:
            listed = client.get("/api/drafts?limit=20")
            check(listed.status_code == 200, "list status")
            check(len(listed.json()["items"]) == 4, "list count")
            check(listed.headers["cache-control"] == "no-store", "list no-store")
            first, second, _, fourth = run.draft_ids
            detail = client.get(f"/api/drafts/{first}")
            check(
                detail.status_code == 200 and detail.json()["review"]["status"] == "pending", "detail pending"
            )
            payload_before = draft_row(run.db_path, first)[0]
            headers = {"Origin": run.url, "Content-Type": "application/json"}
            approved = client.post(
                f"/api/drafts/{first}/decision",
                headers=headers,
                json={"decision": "approve", "expected_version": 0},
            )
            check(approved.status_code == 200 and approved.json()["status"] == "approved", "approve")
            row = draft_row(run.db_path, first)
            check(row[0] == payload_before and json.loads(row[0])["status"] == "pending", "payload preserved")
            check(row[1:4] == ("approved", 1, "admin-sub"), "approved review row")
            check(audit_count(run.db_path) == 1, "approve audit once")
            repeated = client.post(
                f"/api/drafts/{first}/decision",
                headers=headers,
                json={"decision": "approve", "expected_version": 0},
            )
            expect_error(repeated, 409, "draft_conflict")
            check(audit_count(run.db_path) == 1, "conflict no extra audit")
            rejected = client.post(
                f"/api/drafts/{second}/decision",
                headers=headers,
                json={"decision": "reject", "expected_version": 0, "reason": "  Thiếu bằng chứng  "},
            )
            check(
                rejected.status_code == 200 and rejected.json()["reason"] == "Thiếu bằng chứng", "reject trim"
            )
            check(
                draft_row(run.db_path, second)[1:] == ("rejected", 1, "admin-sub", "Thiếu bằng chứng"),
                "reject row",
            )
            check(audit_count(run.db_path) == 2, "two successful audits")
            before = audit_count(run.db_path)
            expect_error(
                client.post(
                    f"/api/drafts/{fourth}/decision",
                    headers={**headers, "Origin": "http://127.0.0.1:1"},
                    json={"decision": "approve", "expected_version": 0},
                ),
                403,
                "forbidden",
            )
            expect_error(
                client.post(
                    f"/api/drafts/{fourth}/decision",
                    headers={"Content-Type": "application/json"},
                    json={"decision": "approve", "expected_version": 0},
                ),
                403,
                "forbidden",
            )
            expect_error(
                client.post(
                    f"/api/drafts/{fourth}/decision",
                    headers={"Origin": run.url, "Content-Type": "text/plain"},
                    content="{}",
                ),
                415,
                "unsupported_media_type",
            )
            expect_error(
                client.post(
                    f"/api/drafts/{fourth}/decision",
                    headers=headers,
                    json={"decision": "approve", "expected_version": 0, "role": "admin"},
                ),
                422,
                "invalid_request",
            )
            check(audit_count(run.db_path) == before, "invalid requests do not audit")


def self_review_matrix() -> None:
    with LocalRun("analyst-self", duration_seconds=30, start_ui=False) as run:
        draft_id = run.draft_ids[2]
        headers = {"Origin": run.url, "Content-Type": "application/json"}
        with httpx.Client(base_url=run.url, timeout=2) as client:
            expect_error(
                client.post(
                    f"/api/drafts/{draft_id}/decision",
                    headers=headers,
                    json={"decision": "approve", "expected_version": 0},
                ),
                403,
                "forbidden",
            )
            check(audit_count(run.db_path) == 0, "self approve no audit")
            rejected = client.post(
                f"/api/drafts/{draft_id}/decision",
                headers=headers,
                json={"decision": "reject", "expected_version": 0, "reason": "Không đủ ngữ cảnh"},
            )
            check(rejected.status_code == 200, "self reject allowed")
            check(audit_count(run.db_path) == 1, "self reject audit")


def auth_matrix() -> None:
    for scenario, status, code in (
        ("insufficient-role", 403, "forbidden"),
        ("missing-token", 401, "authentication_required"),
        ("expired", 401, "authentication_required"),
        ("wrong-signature", 401, "authentication_required"),
    ):
        with LocalRun(scenario, duration_seconds=30, start_ui=False) as run:
            with httpx.Client(base_url=run.url, timeout=2) as client:
                expect_error(
                    client.get("/api/drafts", headers={"Cf-Access-Jwt-Assertion": "caller-token"}),
                    status,
                    code,
                )
                check(audit_count(run.db_path) == 0, f"{scenario} no audit")


def refresh_fault_matrix() -> None:
    with LocalRun("post-ok-refresh-503", duration_seconds=30, start_ui=False) as run:
        draft_id = run.draft_ids[0]
        with httpx.Client(base_url=run.url, timeout=2) as client:
            response = client.post(
                f"/api/drafts/{draft_id}/decision",
                headers={"Origin": run.url, "Content-Type": "application/json"},
                json={"decision": "approve", "expected_version": 0},
            )
            check(response.status_code == 200, "fault scenario POST recorded")
            expect_error(client.get("/api/drafts"), 503, "synthetic_refresh_failure")
            check(
                draft_row(run.db_path, draft_id)[1:4] == ("approved", 1, "admin-sub"),
                "refresh fault keeps review",
            )
            check(audit_count(run.db_path) == 1, "refresh fault keeps one audit")


def main() -> int:
    admin_matrix()
    self_review_matrix()
    auth_matrix()
    refresh_fault_matrix()
    print(json.dumps({"status": "PASS", "checks": CHECKS, "scenarios": 7}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
