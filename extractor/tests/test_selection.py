from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft


def make_draft() -> dict:
    draft = build_regex_draft(
        "Phat hien a.example va b.example trong bao cao",
        source="synthetic.txt",
        language="vi",
    )
    draft["items"].append(
        {
            "kind": "ioc",
            "type": "domain",
            "value": "excluded.example",
            "span": None,
            "evidence": "",
            "keep": False,
            "warning": "allowlist",
            "status": "allowlist",
        }
    )
    return draft


def audit_snapshot(db: Path, table: str) -> list[tuple]:
    with sqlite3.connect(db) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def create_v1_database(db: Path) -> str:
    draft = make_draft()
    payload = json.dumps(draft, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with sqlite3.connect(db) as connection:
        connection.executescript(
            """
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL, schema_version TEXT NOT NULL, status TEXT NOT NULL,
                source_sha256 TEXT NOT NULL, created_by_subject TEXT,
                review_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (review_status IN ('pending', 'approved', 'rejected')),
                review_version INTEGER NOT NULL DEFAULT 0 CHECK (review_version >= 0),
                decided_by_subject TEXT, decided_at TEXT, decision_reason TEXT
            );
            CREATE TABLE draft_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id INTEGER NOT NULL UNIQUE REFERENCES drafts(id),
                action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
                at TEXT NOT NULL, actor_subject TEXT NOT NULL, expected_version INTEGER NOT NULL,
                previous_status TEXT NOT NULL, new_status TEXT NOT NULL,
                previous_version INTEGER NOT NULL, new_version INTEGER NOT NULL, reason TEXT
            );
            CREATE INDEX idx_drafts_review_queue ON drafts(review_status, id DESC);
            PRAGMA user_version = 1;
            """
        )
        connection.execute(
            "INSERT INTO drafts (created_at,payload_json,schema_version,status,source_sha256,"
            "created_by_subject) VALUES (?,?,?,?,?,?)",
            (
                "2026-11-11T00:00:00+00:00",
                payload,
                "1.0",
                "pending",
                draft["source"]["sha256"],
                "author",
            ),
        )
        connection.commit()
    return payload


def test_migrate_v1_to_v2_preserves_payload_and_is_idempotent(tmp_path: Path):
    db = tmp_path / "v1.sqlite"
    payload = create_v1_database(db)

    store.migrate_store(db)
    first = db.read_bytes()
    store.migrate_store(db)

    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        assert connection.execute("SELECT payload_json,selection_version FROM drafts").fetchone() == (
            payload,
            0,
        )
        assert connection.execute("SELECT * FROM draft_selection_audit").fetchall() == []
    assert db.read_bytes() == first


def test_baseline_save_noop_and_reselect_are_canonical_and_counted(tmp_path: Path):
    db = tmp_path / "selection.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")

    baseline = store.get_effective_selection(db, draft_id)
    assert baseline == store.DraftSelectionResult(
        draft_id=draft_id,
        review_version=0,
        selection_version=0,
        selected_indices=(0, 1),
        selected_sha256=hashlib.sha256(b"[0,1]").hexdigest(),
        saved_by_subject=None,
        saved_at=None,
        changed=False,
        ai_extracted_count=3,
        ai_eligible_count=2,
        human_deselected_count=0,
        selection_save_count=0,
    )
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    noop = store.save_selection(db, draft_id, actor=actor, selected_indices=[1, 0], expected_version=0)
    assert noop.changed is False
    assert audit_snapshot(db, "draft_selection_audit") == []

    saved = store.save_selection(db, draft_id, actor=actor, selected_indices=[1], expected_version=0)
    assert (saved.review_version, saved.selection_version, saved.selected_indices) == (1, 1, (1,))
    assert saved.changed is True
    assert saved.human_deselected_count == 1
    assert saved.selection_save_count == 1
    assert store.get_effective_selection(db, draft_id) == saved.__class__(
        **{**saved.__dict__, "changed": False}
    )


@pytest.mark.parametrize(
    ("indices", "error"),
    [
        ([0, 0], store.DraftInputError),
        ([True], store.DraftInputError),
        ([1.0], store.DraftInputError),
        ("0", store.DraftInputError),
        ([-1], store.DraftInputError),
        ([2], store.DraftPolicyError),
    ],
)
def test_invalid_selection_never_changes_database(tmp_path: Path, indices, error):
    db = tmp_path / "invalid.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    before = db.read_bytes()
    with pytest.raises(error):
        store.save_selection(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            selected_indices=indices,
            expected_version=0,
        )
    assert db.read_bytes() == before


def test_saved_snapshot_is_copied_to_approve_audit_and_payload_is_unchanged(tmp_path: Path):
    db = tmp_path / "approve.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    with sqlite3.connect(db) as connection:
        payload_before = connection.execute(
            "SELECT payload_json, source_sha256 FROM drafts WHERE id=?", (draft_id,)
        ).fetchone()

    saved = store.save_selection(db, draft_id, actor=actor, selected_indices=[1], expected_version=0)
    result = store.decide_draft(
        db, draft_id, actor=actor, decision="approve", expected_version=saved.review_version
    )
    assert result.version == 2
    with sqlite3.connect(db) as connection:
        payload_after = connection.execute(
            "SELECT payload_json, source_sha256 FROM drafts WHERE id=?", (draft_id,)
        ).fetchone()
        snapshot = connection.execute(
            "SELECT selection_version, selected_indices_json, selected_sha256 "
            "FROM draft_audit WHERE draft_id=?",
            (draft_id,),
        ).fetchone()
    assert payload_after == payload_before
    assert snapshot == (1, "[1]", hashlib.sha256(b"[1]").hexdigest())


def test_empty_save_blocks_approve_but_reject_records_empty_snapshot(tmp_path: Path):
    db = tmp_path / "empty.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    saved = store.save_selection(db, draft_id, actor=actor, selected_indices=[], expected_version=0)
    with pytest.raises(store.DraftPolicyError, match="rỗng"):
        store.decide_draft(
            db, draft_id, actor=actor, decision="approve", expected_version=saved.review_version
        )
    result = store.decide_draft(
        db,
        draft_id,
        actor=actor,
        decision="reject",
        expected_version=saved.review_version,
        reason="Không đủ bằng chứng",
    )
    assert result.version == 2
    with sqlite3.connect(db) as connection:
        assert connection.execute(
            "SELECT selection_version, selected_indices_json, selected_sha256 FROM draft_audit"
        ).fetchone() == (1, "[]", hashlib.sha256(b"[]").hexdigest())


def test_stale_noop_and_terminal_save_conflict_without_event(tmp_path: Path):
    db = tmp_path / "conflict.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    saved = store.save_selection(db, draft_id, actor=actor, selected_indices=[0], expected_version=0)
    with pytest.raises(store.DraftConflictError):
        store.save_selection(db, draft_id, actor=actor, selected_indices=[0], expected_version=0)
    store.decide_draft(db, draft_id, actor=actor, decision="reject", expected_version=1, reason="x")
    with pytest.raises(store.DraftConflictError):
        store.save_selection(db, draft_id, actor=actor, selected_indices=[1], expected_version=2)
    assert len(audit_snapshot(db, "draft_selection_audit")) == 1
    assert saved.selection_save_count == 1


def test_selection_event_insert_failure_rolls_back_pointer_and_version(tmp_path: Path):
    db = tmp_path / "rollback.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TRIGGER fail_selection BEFORE INSERT ON draft_selection_audit "
            "BEGIN SELECT RAISE(ABORT, 'forced selection failure'); END"
        )
        connection.commit()
    with pytest.raises(store.DraftSQLiteError, match="forced selection failure"):
        store.save_selection(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            selected_indices=[0],
            expected_version=0,
        )
    assert store.get_effective_selection(db, draft_id).review_version == 0
    assert audit_snapshot(db, "draft_selection_audit") == []


def test_two_concurrent_saves_with_same_version_have_one_winner(tmp_path: Path):
    db = tmp_path / "save-race.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    barrier = threading.Barrier(2)

    def save(indices: list[int]):
        barrier.wait()
        try:
            return store.save_selection(
                db, draft_id, actor=actor, selected_indices=indices, expected_version=0
            )
        except store.DraftConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(save, ([0], [1])))

    assert sum(isinstance(item, store.DraftSelectionResult) for item in outcomes) == 1
    assert sum(isinstance(item, store.DraftConflictError) for item in outcomes) == 1
    assert len(audit_snapshot(db, "draft_selection_audit")) == 1


def test_concurrent_save_and_approve_have_one_coherent_winner(tmp_path: Path):
    db = tmp_path / "save-decision-race.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    barrier = threading.Barrier(2)

    def save():
        barrier.wait()
        try:
            return store.save_selection(db, draft_id, actor=actor, selected_indices=[1], expected_version=0)
        except store.DraftConflictError as exc:
            return exc

    def approve():
        barrier.wait()
        try:
            return store.decide_draft(db, draft_id, actor=actor, decision="approve", expected_version=0)
        except store.DraftConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [executor.submit(save), executor.submit(approve)]
        results = [future.result() for future in outcomes]

    assert sum(isinstance(item, store.DraftConflictError) for item in results) == 1
    assert (
        sum(isinstance(item, (store.DraftSelectionResult, store.DraftReviewResult)) for item in results) == 1
    )
    selection_rows = audit_snapshot(db, "draft_selection_audit")
    final_rows = audit_snapshot(db, "draft_audit")
    assert (len(selection_rows), len(final_rows)) in {(1, 0), (0, 1)}
