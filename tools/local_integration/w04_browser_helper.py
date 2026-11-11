"""Helper bounded start/status/stop cho browser acceptance W04."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tools.local_integration.runner import LocalRun

ALLOWED_SCENARIOS = (
    "w04-it",
    "w04-forbidden",
    "w04-refresh-503",
    "w04-unknown-outcome",
    "w04-technology-it",
    "w04-technology-forbidden",
    "w04-technology-refresh-503",
    "w04-technology-unknown-outcome",
)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def snapshot_assets_database(db_path: Path, evidence_dir: Path) -> dict[str, int]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:

        def count(table: str, where: str = "") -> int:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if exists is None:
                return 0
            return int(connection.execute(f"SELECT count(*) FROM {table} {where}").fetchone()[0])

        asset_rows = count("assets")
        active_assets = count("assets", "WHERE deleted_at IS NULL")
        audit_rows = count("asset_audit")
        technology_rows = count("technology_assets")
        active_technologies = count("technology_assets", "WHERE deleted_at IS NULL")
        technology_audit_rows = count("technology_asset_audit")
        draft_rows = count("drafts")
        destination = sqlite3.connect(evidence_dir / "assets-before-cleanup.sqlite")
        try:
            connection.backup(destination)
        finally:
            destination.close()
    summary = {
        "active_assets": active_assets,
        "active_technologies": active_technologies,
        "asset_rows": asset_rows,
        "audit_rows": audit_rows,
        "draft_rows": draft_rows,
        "technology_audit_rows": technology_audit_rows,
        "technology_rows": technology_rows,
    }
    _write_json(evidence_dir / "db-summary.json", summary)
    return summary


def request_stop(state_path: Path) -> Path:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    valid = (
        isinstance(state, dict) and state.get("status") == "running" and isinstance(state.get("run_id"), str)
    )
    if not valid:
        raise RuntimeError("session không ở trạng thái running")
    marker = Path(f"{state_path}.stop")
    _write_json(marker, {"run_id": state["run_id"]})
    return marker


def _stop_requested(state_path: Path, run_id: str) -> bool:
    marker = Path(f"{state_path}.stop")
    if not marker.is_file():
        return False
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return value == {"run_id": run_id}


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def start_session(scenario: str, duration: int, evidence_dir: Path, state_path: Path) -> dict[str, Any]:
    evidence_dir = evidence_dir.resolve()
    state_path = state_path.resolve()
    if state_path.is_file():
        current = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(current, dict) and current.get("status") == "running":
            raise RuntimeError("đã có session running tại state path")
    marker = Path(f"{state_path}.stop")
    marker.unlink(missing_ok=True)
    run_id = uuid.uuid4().hex
    started = datetime.now(UTC)
    trace_path = evidence_dir / "gateway-trace.jsonl"
    run = LocalRun(scenario, duration_seconds=duration, start_ui=True, trace_path=trace_path)
    final: dict[str, Any]
    try:
        with run:
            running = {
                "expires_at": (started + timedelta(seconds=duration)).isoformat(),
                "gateway_port": run.gateway_port,
                "pid": os.getpid(),
                "run_id": run_id,
                "scenario": scenario,
                "started_at": started.isoformat(),
                "status": "running",
                "url": run.url,
            }
            _write_json(state_path, running)
            print(json.dumps(running, ensure_ascii=False, sort_keys=True), flush=True)
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline and not _stop_requested(state_path, run_id):
                time.sleep(0.2)
            summary = snapshot_assets_database(run.db_path, evidence_dir)
            final = {**running, "db_summary": summary, "status": "stopping"}
            _write_json(state_path, final)
    finally:
        cleanup = {
            "gateway_port_closed": not _port_open(run.gateway_port),
            "temp_root_removed": not run.temp_root.exists(),
        }
        final = {
            "cleanup": cleanup,
            "finished_at": datetime.now(UTC).isoformat(),
            "run_id": run_id,
            "scenario": scenario,
            "status": "stopped",
        }
        _write_json(state_path, final)
        marker.unlink(missing_ok=True)
    return final


def read_status(state_path: Path) -> dict[str, Any]:
    value = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("state không hợp lệ")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("start")
    start.add_argument("--scenario", choices=ALLOWED_SCENARIOS, required=True)
    start.add_argument("--duration", type=int, choices=range(30, 301), default=300)
    start.add_argument("--evidence", type=Path, required=True)
    start.add_argument("--state", type=Path, required=True)
    for name in ("status", "stop"):
        command = subparsers.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "start":
        result = start_session(args.scenario, args.duration, args.evidence, args.state)
    elif args.command == "status":
        result = read_status(args.state)
    else:
        result = {"stop_marker": str(request_stop(args.state))}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
