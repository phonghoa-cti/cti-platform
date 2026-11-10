"""Ma trận HTTP selection v1 qua gateway với SQLite tổng hợp thuộc từng run."""

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
SCENARIO_RUNS = 0


def check(condition: bool, label: str) -> None:
    global CHECKS
    if not condition:
        raise AssertionError(label)
    CHECKS += 1


def row(db_path: Path, query: str, parameters: tuple[object, ...] = ()):
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute(query, parameters).fetchone()
    finally:
        connection.close()


def count(db_path: Path, table: str, draft_id: int) -> int:
    return int(row(db_path, f"SELECT COUNT(*) FROM {table} WHERE draft_id = ?", (draft_id,))[0])


def draft_state(db_path: Path, draft_id: int):
    return row(
        db_path,
        "SELECT payload_json, review_status, review_version, selection_version, "
        "decided_by_subject, decision_reason FROM drafts WHERE id = ?",
        (draft_id,),
    )


def expect_error(response: httpx.Response, status: int, code: str) -> None:
    check(response.status_code == status, f"expected {status}, got {response.status_code}: {response.text}")
    check(response.json()["error"]["code"] == code, f"expected {code}: {response.text}")
    check(response.headers.get("cache-control") == "no-store", "error must be no-store")


def post_headers(run: LocalRun) -> dict[str, str]:
    return {"Origin": run.url, "Content-Type": "application/json"}


def happy_selection_matrix() -> None:
    global SCENARIO_RUNS
    SCENARIO_RUNS += 1
    with LocalRun("selection-admin", duration_seconds=30, start_ui=False) as run:
        draft_id = run.selection_draft_id
        assert draft_id is not None
        with httpx.Client(base_url=run.url, timeout=3) as client:
            page = client.get("/api/v1/drafts?limit=1")
            check(page.status_code == 200, "v1 list status")
            check(len(page.json()["items"]) == 1, "v1 list query preserved")
            check(page.headers.get("cache-control") == "no-store", "v1 list no-store")
            check(page.headers.get("vary") == "Cf-Access-Jwt-Assertion", "v1 list Vary")

            detail = client.get(f"/api/v1/drafts/{draft_id}")
            check(detail.status_code == 200, "v1 detail status")
            body = detail.json()
            check(body["selection"]["selected_indices"] == [0, 1], "initial selection")
            check(body["selection"]["ai_eligible_count"] == 2, "two eligible IOC")
            payload_before = draft_state(run.db_path, draft_id)[0]
            keep_before = [item["keep"] for item in json.loads(payload_before)["items"]]

            core = b'{"expected_version":0,"selected_indices":[0,1]}'
            padded = core + b" " * (65536 - len(core))
            at_limit = client.post(
                f"/api/v1/drafts/{draft_id}/selection",
                headers=post_headers(run),
                content=padded,
            )
            check(at_limit.status_code == 200, "v1 body at 65536 reaches API")
            check(at_limit.json()["changed"] is False, "boundary body is no-op")
            expect_error(
                client.post(
                    f"/api/v1/drafts/{draft_id}/selection",
                    headers=post_headers(run),
                    content=padded + b" ",
                ),
                413,
                "request_too_large",
            )
            expect_error(
                client.post(
                    f"/api/drafts/{run.draft_ids[0]}/decision",
                    headers=post_headers(run),
                    content=b'{"decision":"approve","expected_version":0}' + b" " * 9000,
                ),
                413,
                "request_too_large",
            )

            saved = client.post(
                f"/api/v1/drafts/{draft_id}/selection",
                headers=post_headers(run),
                json={"expected_version": 0, "selected_indices": [1]},
            )
            check(saved.status_code == 200, "selection save status")
            saved_body = saved.json()
            check(saved_body["changed"] is True, "selection changed")
            check(saved_body["review_version"] == saved_body["selection_version"] == 1, "save version 1")
            check(saved_body["selected_indices"] == [1], "one IOC remains selected")
            selected_hash = saved_body["selected_sha256"]

            no_op = client.post(
                f"/api/v1/drafts/{draft_id}/selection",
                headers=post_headers(run),
                json={"expected_version": 1, "selected_indices": [1]},
            )
            check(no_op.status_code == 200 and no_op.json()["changed"] is False, "selection no-op")
            check(no_op.json()["review_version"] == 1, "no-op keeps version")
            check(
                count(run.db_path, "draft_selection_audit", draft_id) == 1, "no-op creates no selection event"
            )

            for invalid, status, code in (
                ({"expected_version": 1, "selected_indices": [0, 0]}, 422, "invalid_request"),
                ({"expected_version": 1, "selected_indices": [999]}, 403, "forbidden"),
                (
                    {"expected_version": 1, "selected_indices": [1], "subject": "spoof"},
                    422,
                    "invalid_request",
                ),
            ):
                expect_error(
                    client.post(
                        f"/api/v1/drafts/{draft_id}/selection",
                        headers=post_headers(run),
                        json=invalid,
                    ),
                    status,
                    code,
                )
            expect_error(
                client.post(
                    f"/api/v1/drafts/{draft_id}/selection",
                    headers={"Origin": run.url, "Content-Type": "text/plain"},
                    content="{}",
                ),
                415,
                "unsupported_media_type",
            )
            for origin_headers in (
                {"Content-Type": "application/json"},
                {"Origin": "http://127.0.0.1:1", "Content-Type": "application/json"},
            ):
                expect_error(
                    client.post(
                        f"/api/v1/drafts/{draft_id}/selection",
                        headers=origin_headers,
                        json={"expected_version": 1, "selected_indices": [1]},
                    ),
                    403,
                    "forbidden",
                )
            check(count(run.db_path, "draft_selection_audit", draft_id) == 1, "invalid saves do not write")
            check(count(run.db_path, "draft_audit", draft_id) == 0, "invalid saves do not decide")

            approved = client.post(
                f"/api/v1/drafts/{draft_id}/decision",
                headers=post_headers(run),
                json={"decision": "approve", "expected_version": 1},
            )
            check(approved.status_code == 200, "v1 approve status")
            approved_body = approved.json()
            check(approved_body["status"] == "approved" and approved_body["version"] == 2, "review version 2")
            check(approved_body["selection_version"] == 1, "final selection version 1")
            check(approved_body["selected_indices"] == [1], "final indices")
            check(approved_body["selected_sha256"] == selected_hash, "final selection hash")

            state = draft_state(run.db_path, draft_id)
            check(state[0] == payload_before, "payload_json immutable")
            check(
                [item["keep"] for item in json.loads(state[0])["items"]] == keep_before,
                "items.keep immutable",
            )
            check(state[1:] == ("approved", 2, 1, "admin-sub", None), "committed review state")
            final_audit = row(
                run.db_path,
                "SELECT action, expected_version, previous_version, new_version, selection_version, "
                "selected_indices_json, selected_sha256 FROM draft_audit WHERE draft_id = ?",
                (draft_id,),
            )
            check(final_audit[:5] == ("approve", 1, 1, 2, 1), "final audit versions")
            check(
                json.loads(final_audit[5]) == [1] and final_audit[6] == selected_hash, "final audit snapshot"
            )
            expect_error(
                client.post(
                    f"/api/v1/drafts/{draft_id}/decision",
                    headers=post_headers(run),
                    json={"decision": "approve", "expected_version": 1},
                ),
                409,
                "draft_conflict",
            )
            expect_error(
                client.post(
                    f"/api/v1/drafts/{draft_id}/selection",
                    headers=post_headers(run),
                    json={"expected_version": 1, "selected_indices": [0]},
                ),
                409,
                "draft_conflict",
            )
            check(
                count(run.db_path, "draft_selection_audit", draft_id) == 1,
                "terminal conflict no selection event",
            )
            check(count(run.db_path, "draft_audit", draft_id) == 1, "terminal conflict no decision event")
            expect_error(client.get("/api/v1/drafts/0"), 404, "not_found")
            expect_error(client.get("/api/v1/drafts/1/other"), 404, "not_found")


def empty_and_reject_matrix() -> None:
    global SCENARIO_RUNS
    for scenario, decision in (("selection-empty", "approve"), ("selection-reject", "reject")):
        SCENARIO_RUNS += 1
        with LocalRun(scenario, duration_seconds=30, start_ui=False) as run:
            draft_id = run.selection_draft_id
            assert draft_id is not None
            with httpx.Client(base_url=run.url, timeout=3) as client:
                saved = client.post(
                    f"/api/v1/drafts/{draft_id}/selection",
                    headers=post_headers(run),
                    json={
                        "expected_version": 0,
                        "selected_indices": [] if scenario == "selection-empty" else [1],
                    },
                )
                check(saved.status_code == 200, f"{scenario} save")
                if decision == "approve":
                    expect_error(
                        client.post(
                            f"/api/v1/drafts/{draft_id}/decision",
                            headers=post_headers(run),
                            json={"decision": "approve", "expected_version": 1},
                        ),
                        403,
                        "forbidden",
                    )
                    check(
                        draft_state(run.db_path, draft_id)[1:4] == ("pending", 1, 1), "empty remains pending"
                    )
                    check(count(run.db_path, "draft_audit", draft_id) == 0, "empty approve no decision")
                else:
                    rejected = client.post(
                        f"/api/v1/drafts/{draft_id}/decision",
                        headers=post_headers(run),
                        json={"decision": "reject", "expected_version": 1, "reason": "  Thiếu bằng chứng  "},
                    )
                    check(rejected.status_code == 200, "reject status")
                    check(rejected.json()["reason"] == "Thiếu bằng chứng", "reject reason trimmed")
                    check(rejected.json()["selected_indices"] == [1], "reject snapshot indices")
                    check(count(run.db_path, "draft_audit", draft_id) == 1, "reject audit once")
                    audit = row(
                        run.db_path,
                        "SELECT action, reason, selection_version, selected_indices_json, selected_sha256 "
                        "FROM draft_audit WHERE draft_id = ?",
                        (draft_id,),
                    )
                    check(audit[:3] == ("reject", "Thiếu bằng chứng", 1), "reject audit metadata")
                    check(
                        json.loads(audit[3]) == [1] and audit[4] == rejected.json()["selected_sha256"],
                        "reject audit snapshot",
                    )


def auth_and_self_review_matrix() -> None:
    global SCENARIO_RUNS
    for scenario, status, code in (
        ("insufficient-role", 403, "forbidden"),
        ("missing-token", 401, "authentication_required"),
        ("expired", 401, "authentication_required"),
        ("wrong-signature", 401, "authentication_required"),
    ):
        SCENARIO_RUNS += 1
        with LocalRun(scenario, duration_seconds=30, start_ui=False) as run:
            with httpx.Client(base_url=run.url, timeout=3) as client:
                expect_error(client.get("/api/v1/drafts"), status, code)
                check(count(run.db_path, "draft_audit", run.draft_ids[0]) == 0, f"{scenario} no decision")

    SCENARIO_RUNS += 1
    with LocalRun("analyst-self", duration_seconds=30, start_ui=False) as run:
        draft_id = run.draft_ids[2]
        with httpx.Client(base_url=run.url, timeout=3) as client:
            expect_error(
                client.post(
                    f"/api/v1/drafts/{draft_id}/decision",
                    headers=post_headers(run),
                    json={"decision": "approve", "expected_version": 0},
                ),
                403,
                "forbidden",
            )
            check(count(run.db_path, "draft_audit", draft_id) == 0, "self approve no decision")


def refresh_fault_matrix() -> None:
    global SCENARIO_RUNS
    SCENARIO_RUNS += 1
    with LocalRun("selection-save-refresh-503", duration_seconds=30, start_ui=False) as run:
        draft_id = run.selection_draft_id
        assert draft_id is not None
        with httpx.Client(base_url=run.url, timeout=3) as client:
            saved = client.post(
                f"/api/v1/drafts/{draft_id}/selection",
                headers=post_headers(run),
                json={"expected_version": 0, "selected_indices": [1]},
            )
            check(saved.status_code == 200, "save fault POST succeeds")
            expect_error(client.get(f"/api/v1/drafts/{draft_id}"), 503, "synthetic_refresh_failure")
            check(
                draft_state(run.db_path, draft_id)[1:4] == ("pending", 1, 1), "save fault snapshot committed"
            )
            check(
                count(run.db_path, "draft_selection_audit", draft_id) == 1, "save fault one selection event"
            )
            check(count(run.db_path, "draft_audit", draft_id) == 0, "save fault no decision")

    SCENARIO_RUNS += 1
    with LocalRun("selection-decision-refresh-503", duration_seconds=30, start_ui=False) as run:
        draft_id = run.selection_draft_id
        assert draft_id is not None
        with httpx.Client(base_url=run.url, timeout=3) as client:
            approved = client.post(
                f"/api/v1/drafts/{draft_id}/decision",
                headers=post_headers(run),
                json={"decision": "approve", "expected_version": 1},
            )
            check(approved.status_code == 200, "decision fault POST succeeds")
            expect_error(client.get(f"/api/v1/drafts/{draft_id}"), 503, "synthetic_refresh_failure")
            check(draft_state(run.db_path, draft_id)[1:4] == ("approved", 2, 1), "decision fault committed")
            check(
                count(run.db_path, "draft_selection_audit", draft_id) == 1,
                "decision fault one selection event",
            )
            check(count(run.db_path, "draft_audit", draft_id) == 1, "decision fault one decision event")


def main() -> int:
    happy_selection_matrix()
    empty_and_reject_matrix()
    auth_and_self_review_matrix()
    refresh_fault_matrix()
    print(json.dumps({"status": "PASS", "checks": CHECKS, "scenarios": SCENARIO_RUNS}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
