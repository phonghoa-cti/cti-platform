from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tools.local_integration.w04_browser_helper import request_stop, snapshot_assets_database


def test_snapshot_assets_database_copies_db_and_writes_sanitized_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "live.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            "CREATE TABLE assets(id INTEGER PRIMARY KEY, deleted_at TEXT);"
            "CREATE TABLE asset_audit(id INTEGER PRIMARY KEY);"
            "INSERT INTO assets(id,deleted_at) VALUES(1,NULL),(2,'2026-11-11T00:00:00Z');"
            "INSERT INTO asset_audit(id) VALUES(1),(2),(3);"
        )

    summary = snapshot_assets_database(db_path, tmp_path / "evidence")

    assert summary == {"active_assets": 1, "asset_rows": 2, "audit_rows": 3}
    assert (tmp_path / "evidence" / "assets-before-cleanup.sqlite").is_file()
    assert json.loads((tmp_path / "evidence" / "db-summary.json").read_text(encoding="utf-8")) == summary


def test_request_stop_only_writes_marker_for_running_owned_state(tmp_path: Path) -> None:
    state_path = tmp_path / "session.json"
    state_path.write_text(json.dumps({"run_id": "owned-run", "status": "running"}), encoding="utf-8")

    marker = request_stop(state_path)

    assert marker == Path(f"{state_path}.stop")
    assert json.loads(marker.read_text(encoding="utf-8")) == {"run_id": "owned-run"}
