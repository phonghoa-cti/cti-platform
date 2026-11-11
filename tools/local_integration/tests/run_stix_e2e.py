"""Ma trận CLI → HTTP review → STIX trên cùng draft và SQLite tổng hợp."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- executable matrix bootstraps the repository root before imports

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.local_integration.runner import E2E_SOURCE_BYTES, LocalRun

SOURCE_SHA256 = "e73038e5d68d0aee0757bf72cd8a404b3f55a94ef9d6c519f5e0c3fb1292a655"
CHECKS = 0


def check(condition: bool, label: str) -> None:
    global CHECKS
    if not condition:
        raise AssertionError(label)
    CHECKS += 1


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_inventory(db_path: Path) -> dict[str, tuple[int, str]]:
    result = {}
    for suffix in ("", "-wal", "-shm", "-journal"):
        path = Path(f"{db_path}{suffix}")
        if path.exists():
            data = path.read_bytes()
            result[suffix or "db"] = (len(data), sha256_bytes(data))
    return result


def database_state(db_path: Path, draft_id: int) -> dict[str, Any]:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("BEGIN")
        draft = connection.execute(
            "SELECT payload_json, review_status, review_version, selection_version FROM drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()
        selection_count = connection.execute(
            "SELECT COUNT(*) FROM draft_selection_audit WHERE draft_id = ?",
            (draft_id,),
        ).fetchone()[0]
        decision = connection.execute(
            "SELECT id, action, selection_version, selected_indices_json, selected_sha256 "
            "FROM draft_audit WHERE draft_id = ?",
            (draft_id,),
        ).fetchone()
        draft_actor = connection.execute(
            "SELECT decided_by_subject FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        selection_events = connection.execute(
            "SELECT selection_version,review_version,action,actor_subject,"
            "selected_indices_json,selected_sha256 FROM draft_selection_audit "
            "WHERE draft_id=? ORDER BY selection_version",
            (draft_id,),
        ).fetchall()
        decision_event = connection.execute(
            "SELECT id,action,actor_subject,expected_version,previous_status,new_status,"
            "previous_version,new_version,selection_version,selected_indices_json,selected_sha256 "
            "FROM draft_audit WHERE draft_id=?",
            (draft_id,),
        ).fetchone()
    finally:
        connection.close()
    return {
        "draft": draft,
        "selection_count": selection_count,
        "decision": decision,
        "draft_actor": None if draft_actor is None else draft_actor[0],
        "selection_events": selection_events,
        "decision_event": decision_event,
    }


def run_export(run: LocalRun, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "-B",
            str(ROOT / "extractor" / "draft" / "stix_export.py"),
            "export-approved",
            "--db",
            str(run.db_path),
            "--id",
            str(run.selection_draft_id),
            "--exporter-config",
            str(run.exporter_config_path),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=10,
        shell=False,
    )


def post_headers(run: LocalRun) -> dict[str, str]:
    return {"Origin": run.url, "Content-Type": "application/json"}


def assert_port_released(port: int) -> None:
    probe = socket.socket()
    try:
        if os.name == "nt":
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("127.0.0.1", port))
    finally:
        probe.close()


def main() -> int:
    run = LocalRun("stix-e2e", duration_seconds=120, start_ui=False)
    gateway_process = None
    api_thread = None
    bundle_sha256 = ""
    object_count = 0

    with run:
        draft_id = run.selection_draft_id
        check(draft_id == 1, "draft ID từ store CLI")
        check(run.source_path.read_bytes() == E2E_SOURCE_BYTES, "fixture UTF-8 LF exact")
        source_file_sha = sha256_bytes(run.source_path.read_bytes())
        draft_file_sha = sha256_bytes(run.draft_json_path.read_bytes())
        check(source_file_sha == SOURCE_SHA256, "source SHA-256 literal")

        with httpx.Client(base_url=run.url, timeout=3) as client:
            detail = client.get(f"/api/v1/drafts/{draft_id}")
            check(detail.status_code == 200, "HTTP detail status")
            body = detail.json()
            check(body["source"]["sha256"] == SOURCE_SHA256, "HTTP source hash")
            check(body["text"] == E2E_SOURCE_BYTES.decode(), "HTTP Unicode text")
            check(body["language"] == "vi" and body["tlp"] == "TLP:GREEN", "language và TLP")
            check(body["model"] == "regex-C1" and body["cost_tokens"] == 0, "C1 metadata")
            check(
                [item["value"] for item in body["items"]] == ["evil-one.example", "evil-two.example"],
                "hai IOC",
            )
            check(
                all(
                    body["text"][item["span"][0] : item["span"][1]] == item["evidence"]
                    for item in body["items"]
                ),
                "Unicode spans",
            )
            check(body["selection"]["selected_indices"] == [0, 1], "initial selection")
            payload_before = database_state(run.db_path, draft_id)["draft"][0]
            keep_before = [item["keep"] for item in json.loads(payload_before)["items"]]

            pending_db_before = file_inventory(run.db_path)
            pending = run_export(run, run.bundle_path)
            pending_db_after = file_inventory(run.db_path)
            check(pending.returncode == 1, "pending export exit")
            check(
                pending.stdout == "" and pending.stderr == '{"error":"export_failed"}\n', "pending safe error"
            )
            check(not run.bundle_path.exists(), "pending creates no bundle")
            check(pending_db_before == pending_db_after, "pending export read-only window")

            selected = client.post(
                f"/api/v1/drafts/{draft_id}/selection",
                headers=post_headers(run),
                json={"expected_version": 0, "selected_indices": [1]},
            )
            check(selected.status_code == 200, "selection POST status")
            selected_body = selected.json()
            check(
                selected_body["review_version"] == selected_body["selection_version"] == 1,
                "selection versions",
            )
            check(selected_body["selected_indices"] == [1], "selection subset")
            selection_sha256 = selected_body["selected_sha256"]

            approved = client.post(
                f"/api/v1/drafts/{draft_id}/decision",
                headers=post_headers(run),
                json={"decision": "approve", "expected_version": 1},
            )
            check(approved.status_code == 200, "approve POST status")
            approved_body = approved.json()
            check(approved_body["status"] == "approved" and approved_body["version"] == 2, "approved version")
            check(
                approved_body["selection_version"] == 1
                and approved_body["selected_indices"] == [1]
                and approved_body["selected_sha256"] == selection_sha256,
                "approved final selection",
            )

        state_after_approve = database_state(run.db_path, draft_id)
        check(state_after_approve["selection_count"] == 1, "one selection audit")
        decision = state_after_approve["decision"]
        check(decision is not None and decision[1] == "approve", "one approve audit")
        check(json.loads(decision[3]) == [1] and decision[4] == selection_sha256, "audit snapshot")
        check(state_after_approve["draft"][0] == payload_before, "payload_json immutable through review")
        check(
            [item["keep"] for item in json.loads(payload_before)["items"]] == keep_before,
            "items.keep immutable",
        )
        check(sha256_bytes(run.source_path.read_bytes()) == source_file_sha, "source file immutable")
        check(sha256_bytes(run.draft_json_path.read_bytes()) == draft_file_sha, "draft file immutable")

        approved_db_before = file_inventory(run.db_path)
        exported = run_export(run, run.bundle_path)
        approved_db_after = file_inventory(run.db_path)
        check(exported.returncode == 0 and exported.stderr == "", "approved export exit")
        export_summary = json.loads(exported.stdout)
        bundle_bytes = run.bundle_path.read_bytes()
        bundle_sha256 = sha256_bytes(bundle_bytes)
        check(set(export_summary) == {"draft_id", "bundle_sha256", "object_count"}, "safe export stdout")
        check(
            export_summary["draft_id"] == draft_id and export_summary["bundle_sha256"] == bundle_sha256,
            "export stdout hashes",
        )
        object_count = export_summary["object_count"]
        check(object_count == 4, "one selected SCO plus required objects")
        check(approved_db_before == approved_db_after, "approved export read-only window")

        bundle = json.loads(bundle_bytes)
        check(
            [item["type"] for item in bundle["objects"]]
            == ["marking-definition", "identity", "domain-name", "report"],
            "bundle object order",
        )
        check(bundle["objects"][2]["value"] == "evil-two.example", "selected IOC only")
        decoded_bundle = bundle_bytes.decode()
        check("evil-one.example" not in decoded_bundle, "deselected IOC absent")
        check(
            E2E_SOURCE_BYTES.decode().strip() not in decoded_bundle and "😀" not in decoded_bundle,
            "raw source absent",
        )
        check("e2e-author-sub" not in decoded_bundle and "admin-sub" not in decoded_bundle, "subjects absent")
        check(body["items"][0]["evidence"] not in decoded_bundle, "evidence absent")
        check(body["source"]["name"] not in decoded_bundle, "source name absent")
        check(bundle["objects"][0]["name"] == "TLP:GREEN", "STIX marking GREEN")
        provenance = json.loads(bundle["objects"][-1]["external_references"][0]["description"])
        check(provenance["source_sha256"] == SOURCE_SHA256, "provenance source hash")
        check(
            provenance["draft_id"] == draft_id
            and provenance["approved_audit_id"] == decision[0]
            and provenance["review_version"] == 2,
            "provenance review audit",
        )
        check(
            provenance["selection_version"] == 1
            and provenance["selected_indices"] == [1]
            and provenance["selected_sha256"] == selection_sha256,
            "provenance selection",
        )
        check(provenance["source_tlp"] == provenance["stix_tlp"] == "TLP:GREEN", "provenance TLP")

        first_mtime = run.bundle_path.stat().st_mtime_ns
        identical = run_export(run, run.bundle_path)
        check(identical.returncode == 0 and identical.stderr == "", "identical re-export")
        check(run.bundle_path.read_bytes() == bundle_bytes, "identical bytes")
        check(run.bundle_path.stat().st_mtime_ns == first_mtime, "identical output not rewritten")

        different_path = run.temp_root / "different-existing.json"
        different_path.write_bytes(b"different synthetic bytes\n")
        different_before = (different_path.read_bytes(), different_path.stat().st_mtime_ns)
        different = run_export(run, different_path)
        check(different.returncode == 1, "different output exit")
        check(
            different.stdout == "" and different.stderr == '{"error":"export_failed"}\n',
            "different safe error",
        )
        check(
            (different_path.read_bytes(), different_path.stat().st_mtime_ns) == different_before,
            "different output untouched",
        )
        check(not list(run.temp_root.glob(".*.tmp")), "no orphan publisher temp")
        check(file_inventory(run.db_path) == approved_db_after, "re-exports keep DB read-only")

        temp_root = run.temp_root
        gateway_port = run.gateway_port
        gateway_process = run._gateway_process
        api_thread = run._api_thread
        check(gateway_process is not None and gateway_process.poll() is None, "gateway owned before close")
        check(api_thread is not None and api_thread.is_alive(), "API thread owned before close")

    check(not temp_root.exists(), "owned temp removed")
    check(gateway_process is not None and gateway_process.poll() is not None, "gateway stopped")
    check(api_thread is not None and not api_thread.is_alive(), "API thread stopped")
    assert_port_released(gateway_port)
    check(True, "gateway port released")
    print(
        json.dumps(
            {
                "status": "PASS",
                "checks": CHECKS,
                "draft_id": 1,
                "source_sha256": SOURCE_SHA256,
                "bundle_sha256": bundle_sha256,
                "object_count": object_count,
                "pending_export_db_inventory": {
                    "before": pending_db_before,
                    "after": pending_db_after,
                },
                "approved_export_db_inventory": {
                    "before": approved_db_before,
                    "after": approved_db_after,
                },
                "cleanup": {
                    "gateway_stopped": True,
                    "api_thread_stopped": True,
                    "gateway_port_released": True,
                    "temp_removed": True,
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
