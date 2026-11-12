from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(__file__).resolve().parent
SCRIPT = WORKFLOW_DIR / "check_continuation.py"
PYTHON = WORKFLOW_DIR.parent / "cti-platform-start" / ".venv" / "Scripts" / "python.exe"


def criterion(
    criterion_id: str = "GOAL",
    *,
    state: str = "pending",
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "description": f"Criterion {criterion_id}",
        "state": state,
        "evidence": [] if evidence is None else evidence,
    }


def task(
    task_id: str,
    status: str,
    *,
    owner: str = "Engineer",
    priority: int = 50,
    depends_on: list[str] | None = None,
    receipt: dict[str, Any] | None = None,
    blocker: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "status": status,
        "owner": owner,
        "priority": priority,
        "depends_on": [] if depends_on is None else depends_on,
        "receipt": receipt,
        "blocker": blocker,
        "evidence": [] if evidence is None else evidence,
    }


def valid_receipt(*, running: bool = False) -> dict[str, Any]:
    value: dict[str, Any] = {
        "request_id": "request-123",
        "thread_id": "thread-456",
        "outcome": "accepted",
        "recorded_at": "2026-11-10T23:00:00+07:00",
    }
    if running:
        value["observation"] = {
            "source": "worker callback",
            "status": "running",
            "observed_at": "2026-11-10T23:01:00+07:00",
        }
    return value


def valid_blocker(reason: str = "Lab unavailable") -> dict[str, str]:
    return {
        "reason": reason,
        "owner": "Lab owner",
        "unblock_condition": "Lab access is granted",
    }


def ledger(
    *,
    project_status: str = "active",
    user_paused: bool = False,
    pause_reason: str | None = None,
    criteria: list[dict[str, Any]] | None = None,
    tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project": {
            "id": "PHONG-HOA",
            "status": project_status,
            "user_paused": user_paused,
            "pause_reason": pause_reason,
            "completion_criteria": [criterion()] if criteria is None else criteria,
        },
        "tasks": [] if tasks is None else tasks,
        "accepted_results": [],
    }


class ContinuationCliTests(unittest.TestCase):
    maxDiff = None

    def run_cli_text(
        self, text: str, *, filename: str = "ledger.json"
    ) -> tuple[int, dict[str, Any]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / filename
            ledger_path.write_text(text, encoding="utf-8")
            completed = subprocess.run(
                [str(PYTHON), str(SCRIPT), "--ledger", str(ledger_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        self.assertEqual(completed.stderr, "")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            self.fail(
                f"CLI stdout is not JSON; exit={completed.returncode}; "
                f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
            )
        self.assertEqual(set(payload), {"decision", "task_ids", "reasons"})
        return completed.returncode, payload

    def run_cli(self, value: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self.run_cli_text(json.dumps(value, ensure_ascii=False))

    def assert_decision(
        self,
        value: dict[str, Any],
        expected_decision: str,
        expected_exit: int,
        expected_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        exit_code, payload = self.run_cli(value)
        self.assertEqual(exit_code, expected_exit)
        self.assertEqual(payload["decision"], expected_decision)
        if expected_ids is not None:
            self.assertEqual(payload["task_ids"], expected_ids)
        self.assertIsInstance(payload["reasons"], list)
        self.assertTrue(payload["reasons"])
        return payload

    def test_active_project_with_all_children_accepted_plans_next(self) -> None:
        value = ledger(
            tasks=[task("DONE", "accepted", evidence=["verified-result.md"])]
        )
        self.assert_decision(value, "PLAN_NEXT", 1, [])

    def test_active_project_with_empty_task_list_plans_next(self) -> None:
        self.assert_decision(ledger(tasks=[]), "PLAN_NEXT", 1, [])

    def test_independent_ready_task_dispatches_despite_blocked_lab_task(self) -> None:
        value = ledger(
            tasks=[
                task("LAB", "blocked", priority=100, blocker=valid_blocker()),
                task("OFFLINE", "queued", priority=80),
            ]
        )
        self.assert_decision(value, "DISPATCH", 1, ["OFFLINE"])

    def test_dispatch_selects_highest_priority_at_most_once_per_owner(self) -> None:
        value = ledger(
            tasks=[
                task("E-LOW", "queued", owner="Engineer", priority=20),
                task("R", "queued", owner="Research", priority=80),
                task("E-HIGH", "queued", owner="Engineer", priority=90),
            ]
        )
        self.assert_decision(value, "DISPATCH", 1, ["E-HIGH", "R"])

    def test_queued_task_waiting_for_busy_owner_yields(self) -> None:
        value = ledger(
            tasks=[
                task("BUSY", "dispatched", receipt=valid_receipt()),
                task("NEXT", "queued", priority=100),
            ]
        )
        payload = self.assert_decision(value, "YIELD", 0, ["BUSY"])
        self.assertTrue(
            any("ledger" in reason.lower() for reason in payload["reasons"])
        )
        self.assertTrue(any("live" in reason.lower() for reason in payload["reasons"]))

    def test_dispatched_task_without_receipt_is_invalid(self) -> None:
        value = ledger(tasks=[task("BAD", "dispatched")])
        self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_dispatched_task_with_fake_receipt_outcome_is_invalid(self) -> None:
        receipt = valid_receipt()
        receipt["outcome"] = "success"
        value = ledger(tasks=[task("BAD", "dispatched", receipt=receipt)])
        self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_project_status_list_or_dict_is_invalid_without_traceback(self) -> None:
        for bad_status in ([], {}, None, True, 1, 1.5):
            with self.subTest(bad_status=bad_status):
                value = ledger(tasks=[])
                value["project"]["status"] = bad_status
                self.assert_decision(value, "INVALID", 2, [])

    def test_criterion_state_list_or_dict_is_invalid_without_traceback(self) -> None:
        for bad_state in ([], {}, None, True, 1, 1.5):
            with self.subTest(bad_state=bad_state):
                value = ledger(tasks=[])
                value["project"]["completion_criteria"][0]["state"] = bad_state
                self.assert_decision(value, "INVALID", 2, [])

    def test_task_status_list_or_dict_is_invalid_without_traceback(self) -> None:
        for bad_status in ([], {}, None, True, 1, 1.5):
            with self.subTest(bad_status=bad_status):
                value = ledger(tasks=[task("BAD", "planned")])
                value["tasks"][0]["status"] = bad_status
                self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_receipt_outcome_list_or_dict_is_invalid_without_traceback(self) -> None:
        for bad_outcome in ([], {}, None, True, 1, 1.5):
            with self.subTest(bad_outcome=bad_outcome):
                receipt = valid_receipt()
                receipt["outcome"] = bad_outcome
                value = ledger(tasks=[task("BAD", "dispatched", receipt=receipt)])
                self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_running_task_needs_observation_with_real_status_source(self) -> None:
        value = ledger(tasks=[task("BAD", "running", receipt=valid_receipt())])
        self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_running_rejects_non_running_observation_statuses(self) -> None:
        for bad_status in ("idle", "completed", "failed", "queued", "unknown", []):
            with self.subTest(bad_status=bad_status):
                receipt = valid_receipt(running=True)
                receipt["observation"]["status"] = bad_status
                value = ledger(tasks=[task("BAD", "running", receipt=receipt)])
                self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_valid_running_task_yields(self) -> None:
        value = ledger(
            tasks=[task("RUN", "running", receipt=valid_receipt(running=True))]
        )
        self.assert_decision(value, "YIELD", 0, ["RUN"])

    def test_reported_task_requires_review(self) -> None:
        value = ledger(tasks=[task("REPORT", "reported")])
        self.assert_decision(value, "REVIEW", 1, ["REPORT"])

    def test_failed_and_stalled_tasks_require_replan(self) -> None:
        value = ledger(tasks=[task("FAILED", "failed"), task("STALE", "stalled")])
        self.assert_decision(value, "REPLAN", 1, ["FAILED", "STALE"])

    def test_complete_project_with_pending_criterion_is_invalid(self) -> None:
        value = ledger(project_status="complete", tasks=[])
        self.assert_decision(value, "INVALID", 2, [])

    def test_complete_project_with_unaccepted_task_is_invalid(self) -> None:
        value = ledger(
            project_status="complete",
            criteria=[criterion(state="verified", evidence=["proof.md"])],
            tasks=[task("OPEN", "planned")],
        )
        self.assert_decision(value, "INVALID", 2, ["OPEN"])

    def test_fully_verified_complete_project_completes(self) -> None:
        value = ledger(
            project_status="complete",
            criteria=[criterion(state="verified", evidence=["proof.md"])],
            tasks=[task("DONE", "accepted", evidence=["task-proof.md"])],
        )
        self.assert_decision(value, "COMPLETE", 0, [])

    def test_paused_project_with_reason_pauses_before_work_decisions(self) -> None:
        value = ledger(
            user_paused=True,
            pause_reason="User explicitly paused",
            tasks=[task("READY", "queued")],
        )
        self.assert_decision(value, "PAUSED", 0, [])

    def test_paused_project_without_reason_is_invalid(self) -> None:
        value = ledger(user_paused=True, pause_reason="", tasks=[])
        self.assert_decision(value, "INVALID", 2, [])

    def test_all_remaining_tasks_blocked_reports_blockers(self) -> None:
        value = ledger(
            tasks=[
                task("UI", "blocked", blocker=valid_blocker("No UI owner")),
                task("LAB", "blocked", blocker=valid_blocker("No lab access")),
                task("DONE", "accepted", evidence=["done.md"]),
            ]
        )
        payload = self.assert_decision(value, "BLOCKED", 0, ["UI", "LAB"])
        joined = " ".join(payload["reasons"])
        self.assertIn("No UI owner", joined)
        self.assertIn("No lab access", joined)

    def test_planned_task_waiting_on_blocked_dependency_plans_next(self) -> None:
        value = ledger(
            tasks=[
                task("LAB", "blocked", blocker=valid_blocker()),
                task("AFTER-LAB", "planned", depends_on=["LAB"]),
            ]
        )
        payload = self.assert_decision(value, "PLAN_NEXT", 1, ["AFTER-LAB"])
        self.assertTrue(any("LAB" in reason for reason in payload["reasons"]))

    def test_accepted_task_without_evidence_is_invalid(self) -> None:
        value = ledger(tasks=[task("BAD", "accepted")])
        self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_duplicate_task_id_is_invalid(self) -> None:
        value = ledger(tasks=[task("DUP", "planned"), task("DUP", "queued")])
        self.assert_decision(value, "INVALID", 2, ["DUP"])

    def test_missing_dependency_is_invalid(self) -> None:
        value = ledger(tasks=[task("A", "planned", depends_on=["MISSING"])])
        self.assert_decision(value, "INVALID", 2, ["A"])

    def test_dependency_cycle_is_invalid(self) -> None:
        value = ledger(
            tasks=[
                task("A", "planned", depends_on=["B"]),
                task("B", "planned", depends_on=["A"]),
            ]
        )
        payload = self.assert_decision(value, "INVALID", 2)
        self.assertTrue(any("cycle" in reason.lower() for reason in payload["reasons"]))

    def test_unknown_task_status_is_invalid(self) -> None:
        value = ledger(tasks=[task("BAD", "done")])
        self.assert_decision(value, "INVALID", 2, ["BAD"])

    def test_invalid_json_is_invalid_without_echoing_input(self) -> None:
        secret_marker = "DO-NOT-ECHO-THIS-MARKER"
        exit_code, payload = self.run_cli_text(f'{{"bad": "{secret_marker}"')
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["decision"], "INVALID")
        self.assertNotIn(secret_marker, json.dumps(payload))

    def test_missing_file_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.json"
            completed = subprocess.run(
                [str(PYTHON), str(SCRIPT), "--ledger", str(missing)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["decision"], "INVALID")

    def test_accepted_result_does_not_turn_planned_task_into_accepted(self) -> None:
        value = ledger(tasks=[task("NEXT", "planned")])
        value["accepted_results"] = [
            {"request_id": "old-request", "sha": "abc123", "artifact": "old.md"}
        ]
        self.assert_decision(value, "PLAN_NEXT", 1, ["NEXT"])

    def test_input_object_is_not_mutated_by_evaluation(self) -> None:
        # This test imports only after the CLI contract exists, and protects the
        # pure/read-only evaluation boundary required by the workflow gate.
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_continuation", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        value = ledger(tasks=[task("NEXT", "planned")])
        before = copy.deepcopy(value)
        result = module.evaluate_ledger(value)
        self.assertEqual(result["decision"], "PLAN_NEXT")
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
