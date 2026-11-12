from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

TASK_STATES = {
    "planned",
    "queued",
    "dispatched",
    "running",
    "reported",
    "accepted",
    "blocked",
    "failed",
    "stalled",
}
PROJECT_STATES = {"active", "complete"}
CRITERION_STATES = {"pending", "verified"}
RECEIPT_OUTCOMES = {"queued", "accepted"}
EXIT_CODES = {
    "INVALID": 2,
    "PAUSED": 0,
    "COMPLETE": 0,
    "REVIEW": 1,
    "REPLAN": 1,
    "DISPATCH": 1,
    "YIELD": 0,
    "BLOCKED": 0,
    "PLAN_NEXT": 1,
}


def result(decision: str, task_ids: list[str], reasons: list[str]) -> dict[str, Any]:
    return {"decision": decision, "task_ids": task_ids, "reasons": reasons}


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_allowed_enum(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_is_nonempty_string(item) for item in value)
    )


def _validate_receipt(task_id: str, status: str, receipt: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return [f"Task {task_id}: {status} requires a receipt object."]

    for field in ("request_id", "thread_id", "recorded_at"):
        if not _is_nonempty_string(receipt.get(field)):
            errors.append(f"Task {task_id}: receipt.{field} is required.")
    if not _is_allowed_enum(receipt.get("outcome"), RECEIPT_OUTCOMES):
        errors.append(f"Task {task_id}: receipt.outcome must be queued or accepted.")

    if status == "running":
        observation = receipt.get("observation")
        if not isinstance(observation, Mapping):
            errors.append(
                f"Task {task_id}: running requires an observation with a real status source."
            )
        else:
            for field in ("source", "observed_at"):
                if not _is_nonempty_string(observation.get(field)):
                    errors.append(
                        f"Task {task_id}: receipt.observation.{field} is required."
                    )
            if observation.get("status") != "running":
                errors.append(
                    f"Task {task_id}: receipt.observation.status must be running."
                )
    return errors


def _dependency_cycle(tasks_by_id: dict[str, Mapping[str, Any]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(task_id: str) -> list[str]:
        if task_id in visiting:
            start = stack.index(task_id)
            return stack[start:] + [task_id]
        if task_id in visited:
            return []
        visiting.add(task_id)
        stack.append(task_id)
        for dependency in tasks_by_id[task_id]["depends_on"]:
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(task_id)
        visited.add(task_id)
        return []

    for task_id in tasks_by_id:
        cycle = visit(task_id)
        if cycle:
            return cycle
    return []


def validate_ledger(ledger: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    error_task_ids: list[str] = []

    if not isinstance(ledger, Mapping):
        return ["Ledger root must be a JSON object."], []
    if ledger.get("schema_version") != 1 or isinstance(
        ledger.get("schema_version"), bool
    ):
        errors.append("schema_version must be 1.")

    project = ledger.get("project")
    if not isinstance(project, Mapping):
        errors.append("project must be an object.")
        return errors, error_task_ids
    if not _is_allowed_enum(project.get("status"), PROJECT_STATES):
        errors.append("project.status must be active or complete.")
    if not isinstance(project.get("user_paused"), bool):
        errors.append("project.user_paused must be a boolean.")
    if project.get("user_paused") and not _is_nonempty_string(
        project.get("pause_reason")
    ):
        errors.append("project.pause_reason is required when user_paused is true.")

    criteria = project.get("completion_criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append("project.completion_criteria must be a non-empty list.")
    else:
        criterion_ids: set[str] = set()
        for index, item in enumerate(criteria):
            if not isinstance(item, Mapping):
                errors.append(f"completion_criteria[{index}] must be an object.")
                continue
            criterion_id = item.get("id")
            if not _is_nonempty_string(criterion_id):
                errors.append(f"completion_criteria[{index}].id is required.")
            elif criterion_id in criterion_ids:
                errors.append(f"Duplicate completion criterion id: {criterion_id}.")
            else:
                criterion_ids.add(criterion_id)
            if not _is_allowed_enum(item.get("state"), CRITERION_STATES):
                errors.append(
                    f"Completion criterion {criterion_id or index}: invalid state."
                )
            if not _is_string_list(item.get("evidence")):
                errors.append(
                    f"Completion criterion {criterion_id or index}: evidence must be a list of strings."
                )

    tasks = ledger.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be a list.")
        return errors, error_task_ids

    tasks_by_id: dict[str, Mapping[str, Any]] = {}
    valid_task_objects: list[Mapping[str, Any]] = []
    for index, item in enumerate(tasks):
        if not isinstance(item, Mapping):
            errors.append(f"tasks[{index}] must be an object.")
            continue
        valid_task_objects.append(item)
        task_id = item.get("id")
        if not _is_nonempty_string(task_id):
            errors.append(f"tasks[{index}].id is required.")
            continue
        if task_id in tasks_by_id:
            errors.append(f"Duplicate task id: {task_id}.")
            if task_id not in error_task_ids:
                error_task_ids.append(task_id)
        else:
            tasks_by_id[task_id] = item

    for index, item in enumerate(valid_task_objects):
        task_id_value = item.get("id")
        task_id = task_id_value if _is_nonempty_string(task_id_value) else str(index)

        def task_error(
            message: str,
            current_task_id: str = task_id,
            current_task_id_value: Any = task_id_value,
        ) -> None:
            errors.append(f"Task {current_task_id}: {message}")
            if (
                _is_nonempty_string(current_task_id_value)
                and current_task_id not in error_task_ids
            ):
                error_task_ids.append(current_task_id)

        status = item.get("status")
        if not _is_allowed_enum(status, TASK_STATES):
            task_error("invalid status.")
        if not _is_nonempty_string(item.get("owner")):
            task_error("owner is required.")
        priority = item.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool):
            task_error("priority must be an integer.")
        depends_on = item.get("depends_on")
        if not _is_string_list(depends_on):
            task_error("depends_on must be a list of task IDs.")
        if not _is_string_list(item.get("evidence")):
            task_error("evidence must be a list of strings.")
        if status == "accepted" and not _is_string_list(
            item.get("evidence"), allow_empty=False
        ):
            task_error("accepted requires evidence.")
        if _is_allowed_enum(status, {"dispatched", "running"}):
            receipt_errors = _validate_receipt(task_id, status, item.get("receipt"))
            errors.extend(receipt_errors)
            if receipt_errors and task_id not in error_task_ids:
                error_task_ids.append(task_id)
        if status == "blocked":
            blocker = item.get("blocker")
            if not isinstance(blocker, Mapping):
                task_error("blocked requires a blocker object.")
            else:
                for field in ("reason", "owner", "unblock_condition"):
                    if not _is_nonempty_string(blocker.get(field)):
                        task_error(f"blocker.{field} is required.")

    if not errors:
        for task_id, item in tasks_by_id.items():
            for dependency in item["depends_on"]:
                if dependency not in tasks_by_id:
                    errors.append(
                        f"Task {task_id}: dependency {dependency} does not exist."
                    )
                    if task_id not in error_task_ids:
                        error_task_ids.append(task_id)
        if not errors:
            cycle = _dependency_cycle(tasks_by_id)
            if cycle:
                errors.append(f"Dependency cycle: {' -> '.join(cycle)}.")
                for task_id in cycle[:-1]:
                    if task_id not in error_task_ids:
                        error_task_ids.append(task_id)

    accepted_results = ledger.get("accepted_results")
    if not isinstance(accepted_results, list):
        errors.append("accepted_results must be a list.")
    else:
        request_ids: set[str] = set()
        for index, item in enumerate(accepted_results):
            if not isinstance(item, Mapping) or not _is_nonempty_string(
                item.get("request_id")
            ):
                errors.append(f"accepted_results[{index}].request_id is required.")
                continue
            request_id = item["request_id"]
            if request_id in request_ids:
                errors.append(f"Duplicate accepted result request_id: {request_id}.")
            request_ids.add(request_id)

    return errors, error_task_ids


def evaluate_ledger(ledger: Any) -> dict[str, Any]:
    errors, error_task_ids = validate_ledger(ledger)
    if errors:
        return result("INVALID", error_task_ids, errors)

    project = ledger["project"]
    tasks: list[Mapping[str, Any]] = ledger["tasks"]
    if project["user_paused"]:
        return result(
            "PAUSED",
            [],
            [f"User paused the project: {project['pause_reason']}"],
        )

    if project["status"] == "complete":
        incomplete_criteria = [
            item["id"]
            for item in project["completion_criteria"]
            if item["state"] != "verified" or not item["evidence"]
        ]
        open_task_ids = [item["id"] for item in tasks if item["status"] != "accepted"]
        if incomplete_criteria or open_task_ids:
            reasons: list[str] = []
            if incomplete_criteria:
                reasons.append(
                    "Project is complete but criteria are not verified with evidence: "
                    + ", ".join(incomplete_criteria)
                    + "."
                )
            if open_task_ids:
                reasons.append(
                    "Project is complete but tasks are not accepted: "
                    + ", ".join(open_task_ids)
                    + "."
                )
            return result("INVALID", open_task_ids, reasons)
        return result(
            "COMPLETE",
            [],
            [
                "All project criteria are verified with evidence and all tasks are accepted."
            ],
        )

    reported = [item["id"] for item in tasks if item["status"] == "reported"]
    if reported:
        return result(
            "REVIEW", reported, ["Reported tasks require review before acceptance."]
        )

    failed = [item["id"] for item in tasks if item["status"] in {"failed", "stalled"}]
    if failed:
        return result(
            "REPLAN",
            failed,
            ["Failed or stalled tasks require diagnosis and replanning."],
        )

    busy_owners = {
        item["owner"] for item in tasks if item["status"] in {"dispatched", "running"}
    }
    accepted_ids = {item["id"] for item in tasks if item["status"] == "accepted"}
    ready = [
        item
        for item in tasks
        if item["status"] == "queued"
        and all(dependency in accepted_ids for dependency in item["depends_on"])
        and item["owner"] not in busy_owners
    ]
    ready.sort(key=lambda item: (-item["priority"], item["id"]))
    selected: list[str] = []
    selected_owners: set[str] = set()
    for item in ready:
        if item["owner"] in selected_owners:
            continue
        selected.append(item["id"])
        selected_owners.add(item["owner"])
    if selected:
        return result(
            "DISPATCH",
            selected,
            ["Queued tasks have accepted dependencies and an available owner."],
        )

    in_flight = [
        item["id"] for item in tasks if item["status"] in {"dispatched", "running"}
    ]
    if in_flight:
        return result(
            "YIELD",
            in_flight,
            [
                "The ledger records dispatched or running work with a receipt/callback.",
                "This is ledger data, not a live check that a worker is currently running.",
            ],
        )

    remaining = [item for item in tasks if item["status"] != "accepted"]
    if remaining and all(item["status"] == "blocked" for item in remaining):
        return result(
            "BLOCKED",
            [item["id"] for item in remaining],
            [
                f"{item['id']}: {item['blocker']['reason']} "
                f"(owner: {item['blocker']['owner']}; "
                f"unblock: {item['blocker']['unblock_condition']})"
                for item in remaining
            ],
        )

    actionable_ids = [item["id"] for item in remaining if item["status"] != "blocked"]
    reasons = [
        "The project is active but there is no dispatchable or in-flight task; prepare the next work item."
    ]
    blocked_ids = {item["id"] for item in tasks if item["status"] == "blocked"}
    waiting_on_blocked = [
        f"{item['id']} waits on blocked dependency {dependency}."
        for item in remaining
        for dependency in item["depends_on"]
        if dependency in blocked_ids
    ]
    reasons.extend(waiting_on_blocked)
    return result("PLAN_NEXT", actionable_ids, reasons)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a Phong Hoa workflow ledger and recommend the next process action."
    )
    parser.add_argument("--ledger", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        text = args.ledger.read_text(encoding="utf-8")
        ledger = json.loads(text)
    except FileNotFoundError:
        output = result("INVALID", [], ["Ledger file does not exist."])
    except (OSError, UnicodeError):
        output = result("INVALID", [], ["Ledger file could not be read as UTF-8."])
    except json.JSONDecodeError:
        output = result("INVALID", [], ["Ledger file is not valid JSON."])
    else:
        output = evaluate_ledger(ledger)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return EXIT_CODES[output["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
