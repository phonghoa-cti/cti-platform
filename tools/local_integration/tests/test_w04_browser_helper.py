from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tools.local_integration.w04_browser_helper import (
    ALLOWED_SCENARIOS,
    request_stop,
    snapshot_assets_database,
)


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

    assert summary == {
        "active_assets": 1,
        "active_technologies": 0,
        "asset_rows": 2,
        "audit_rows": 3,
        "cve_status_audit": 0,
        "cve_status_records": 0,
        "draft_rows": 0,
        "technology_audit_rows": 0,
        "technology_rows": 0,
    }
    assert (tmp_path / "evidence" / "assets-before-cleanup.sqlite").is_file()
    assert json.loads((tmp_path / "evidence" / "db-summary.json").read_text(encoding="utf-8")) == summary


def test_snapshot_assets_database_includes_technology_and_legacy_non_impact_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "shared.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            "CREATE TABLE assets(id INTEGER PRIMARY KEY, deleted_at TEXT);"
            "CREATE TABLE asset_audit(id INTEGER PRIMARY KEY);"
            "CREATE TABLE technology_assets(id INTEGER PRIMARY KEY, deleted_at TEXT);"
            "CREATE TABLE technology_asset_audit(id INTEGER PRIMARY KEY);"
            "CREATE TABLE drafts(id INTEGER PRIMARY KEY);"
            "INSERT INTO technology_assets(id,deleted_at) VALUES(1,NULL),(2,'2026-11-12T00:00:00Z');"
            "INSERT INTO technology_asset_audit(id) VALUES(1),(2),(3);"
            "INSERT INTO drafts(id) VALUES(1),(2),(3),(4);"
        )

    summary = snapshot_assets_database(db_path, tmp_path / "evidence")

    assert summary == {
        "active_assets": 0,
        "active_technologies": 1,
        "asset_rows": 0,
        "audit_rows": 0,
        "cve_status_audit": 0,
        "cve_status_records": 0,
        "draft_rows": 4,
        "technology_audit_rows": 3,
        "technology_rows": 2,
    }


def test_request_stop_only_writes_marker_for_running_owned_state(tmp_path: Path) -> None:
    state_path = tmp_path / "session.json"
    state_path.write_text(json.dumps({"run_id": "owned-run", "status": "running"}), encoding="utf-8")

    marker = request_stop(state_path)

    assert marker == Path(f"{state_path}.stop")
    assert json.loads(marker.read_text(encoding="utf-8")) == {"run_id": "owned-run"}


def test_browser_helper_accepts_only_bounded_w03_browser_scenarios() -> None:
    assert {
        "w03-it",
        "w03-leader",
        "w03-snapshot-change",
        "w03-refresh-503",
        "w03-status-it",
        "w03-status-known-commit",
        "w03-status-unknown-outcome",
    }.issubset(ALLOWED_SCENARIOS)


def test_snapshot_assets_database_includes_w03_status_write_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "shared.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            "CREATE TABLE cve_status_records(id INTEGER PRIMARY KEY);"
            "CREATE TABLE cve_status_audit(id INTEGER PRIMARY KEY);"
            "INSERT INTO cve_status_records(id) VALUES(1);"
            "INSERT INTO cve_status_audit(id) VALUES(1),(2);"
        )

    summary = snapshot_assets_database(db_path, tmp_path / "evidence")

    assert summary["cve_status_records"] == 1
    assert summary["cve_status_audit"] == 2


def test_snapshot_assets_database_supports_distinct_initial_and_final_artifacts(tmp_path: Path) -> None:
    db_path = tmp_path / "shared.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE drafts(id INTEGER PRIMARY KEY)")

    snapshot_assets_database(db_path, tmp_path / "evidence", label="initial")
    snapshot_assets_database(db_path, tmp_path / "evidence")

    assert (tmp_path / "evidence" / "assets-initial.sqlite").is_file()
    assert (tmp_path / "evidence" / "db-summary-initial.json").is_file()
    assert (tmp_path / "evidence" / "assets-before-cleanup.sqlite").is_file()
