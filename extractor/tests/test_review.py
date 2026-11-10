from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft


def make_draft(text: str = "Báo cáo ghi nhận evil.example") -> dict:
    return build_regex_draft(text, source="synthetic.txt", language="vi")


def create_legacy_database(db: Path, draft: dict | None = None) -> str:
    payload = draft or make_draft()
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    connection = sqlite3.connect(db)
    try:
        connection.execute(
            """
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                source_sha256 TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO drafts (created_at, payload_json, schema_version, status, source_sha256)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "2026-11-10T12:00:00+00:00",
                payload_json,
                "1.0",
                "pending",
                payload["source"]["sha256"],
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return payload_json


def create_counterfeit_current_database(db: Path, broken: str) -> None:
    drafts_checks = (
        ""
        if broken == "draft_checks"
        else ("CHECK (review_status IN ('pending', 'approved', 'rejected')),CHECK (review_version >= 0),")
    )
    audit_unique = "" if broken == "audit_unique" else "UNIQUE"
    audit_fk = "" if broken == "audit_fk" else "REFERENCES drafts(id)"
    audit_action_check = "" if broken == "audit_action_check" else "CHECK (action IN ('approve', 'reject'))"
    connection = sqlite3.connect(db)
    try:
        connection.executescript(
            f"""
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                created_by_subject TEXT,
                review_status TEXT NOT NULL DEFAULT 'pending',
                review_version INTEGER NOT NULL DEFAULT 0,
                decided_by_subject TEXT,
                decided_at TEXT,
                decision_reason TEXT,
                {drafts_checks}
                CHECK (id > 0)
            );
            CREATE TABLE draft_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id INTEGER NOT NULL {audit_unique} {audit_fk},
                action TEXT NOT NULL {audit_action_check},
                at TEXT NOT NULL,
                actor_subject TEXT NOT NULL,
                expected_version INTEGER NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                previous_version INTEGER NOT NULL,
                new_version INTEGER NOT NULL,
                reason TEXT
            );
            PRAGMA user_version = 1;
            """
        )
        if broken != "queue_index":
            connection.execute("CREATE INDEX idx_drafts_review_queue ON drafts(review_status, id DESC)")
        connection.commit()
    finally:
        connection.close()


def review_row(db: Path, draft_id: int = 1) -> tuple:
    connection = sqlite3.connect(db)
    try:
        return connection.execute(
            """
            SELECT review_status, review_version, created_by_subject,
                   decided_by_subject, decided_at, decision_reason
            FROM drafts WHERE id = ?
            """,
            (draft_id,),
        ).fetchone()
    finally:
        connection.close()


def audit_rows(db: Path, draft_id: int = 1) -> list[tuple]:
    connection = sqlite3.connect(db)
    try:
        return connection.execute(
            """
            SELECT draft_id, action, actor_subject, expected_version,
                   previous_status, new_status, previous_version, new_version, reason
            FROM draft_audit WHERE draft_id = ? ORDER BY id
            """,
            (draft_id,),
        ).fetchall()
    finally:
        connection.close()


def test_legacy_read_is_read_only_and_migration_preserves_payload_then_is_idempotent(tmp_path: Path):
    db = tmp_path / "legacy.sqlite"
    payload_json = create_legacy_database(db)
    before_read = hashlib.sha256(db.read_bytes()).hexdigest()

    stored = store.get_draft(db, 1)
    page = store.list_drafts(db)

    assert stored["review"] == {
        "status": "pending",
        "version": 0,
        "created_by_subject": None,
        "decided_by_subject": None,
        "decided_at": None,
        "reason": None,
    }
    assert page["items"][0]["review_status"] == "pending"
    assert page["items"][0]["review_version"] == 0
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_read

    store.migrate_store(db)
    connection = sqlite3.connect(db)
    try:
        first_state = connection.execute(
            "SELECT payload_json, review_status, review_version, created_by_subject FROM drafts"
        ).fetchall()
        first_audit = connection.execute("SELECT * FROM draft_audit").fetchall()
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
    finally:
        connection.close()
    first_hash = hashlib.sha256(db.read_bytes()).hexdigest()

    store.migrate_store(db)

    connection = sqlite3.connect(db)
    try:
        assert (
            connection.execute(
                "SELECT payload_json, review_status, review_version, created_by_subject FROM drafts"
            ).fetchall()
            == first_state
        )
        assert connection.execute("SELECT * FROM draft_audit").fetchall() == first_audit
    finally:
        connection.close()
    assert first_state == [(payload_json, "pending", 0, None)]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == first_hash


def test_failed_migration_rolls_back_columns_and_user_version(tmp_path: Path):
    db = tmp_path / "legacy.sqlite"
    create_legacy_database(db)
    connection = sqlite3.connect(db)
    try:
        connection.execute("CREATE TABLE draft_audit (wrong_column TEXT)")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(store.DraftSQLiteError):
        store.migrate_store(db)

    connection = sqlite3.connect(db)
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(drafts)")}
        assert "review_status" not in columns
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
    finally:
        connection.close()


def test_new_draft_records_authorship_and_can_be_approved_by_another_analyst(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft = make_draft("Nguồn 😀 ghi nhận evil.example")
    draft_id = store.save_draft(db, draft, created_by_subject="author-1")

    result = store.decide_draft(
        db,
        draft_id,
        actor=store.Actor("reviewer-2", frozenset({"analyst"})),
        decision="approve",
        expected_version=0,
    )

    assert result.status == "approved"
    assert result.version == 1
    assert result.draft_id == draft_id
    assert store.get_draft(db, draft_id)["review"] == {
        "status": "approved",
        "version": 1,
        "created_by_subject": "author-1",
        "decided_by_subject": "reviewer-2",
        "decided_at": result.decided_at,
        "reason": None,
    }
    assert audit_rows(db) == [(draft_id, "approve", "reviewer-2", 0, "pending", "approved", 0, 1, None)]
    connection = sqlite3.connect(db)
    try:
        payload_json = connection.execute(
            "SELECT payload_json FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()[0]
    finally:
        connection.close()
    assert json.loads(payload_json) == draft
    assert json.loads(payload_json)["status"] == "pending"


def test_reject_requires_reason_but_creator_may_reject_own_draft(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author-1")
    actor = store.Actor("author-1", frozenset({"admin"}))

    for reason in (None, "", "  "):
        with pytest.raises(store.DraftInputError, match="reason"):
            store.decide_draft(
                db,
                draft_id,
                actor=actor,
                decision="reject",
                expected_version=0,
                reason=reason,
            )

    result = store.decide_draft(
        db,
        draft_id,
        actor=actor,
        decision="reject",
        expected_version=0,
        reason="  Không đủ bằng chứng  ",
    )

    assert result.status == "rejected"
    assert result.reason == "Không đủ bằng chứng"
    assert audit_rows(db)[0][-1] == "Không đủ bằng chứng"


@pytest.mark.parametrize(
    ("subject", "roles"),
    [
        ("", frozenset({"analyst"})),
        ("   ", frozenset({"admin"})),
        ("reviewer", frozenset()),
        ("reviewer", frozenset({"it"})),
    ],
)
def test_invalid_or_unauthorized_actor_is_rejected_before_database_io(
    tmp_path: Path, subject: str, roles: frozenset[str]
):
    missing = tmp_path / "missing.sqlite"
    actor = store.Actor(subject, roles)

    with pytest.raises((store.DraftInputError, store.DraftPolicyError)):
        store.decide_draft(
            missing,
            1,
            actor=actor,
            decision="approve",
            expected_version=0,
        )

    assert not missing.exists()


@pytest.mark.parametrize("role", ["analyst", "admin"])
def test_self_approval_is_blocked_for_every_allowed_role(tmp_path: Path, role: str):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="same-subject")

    with pytest.raises(store.DraftPolicyError, match="tự duyệt"):
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("same-subject", frozenset({role})),
            decision="approve",
            expected_version=0,
        )

    assert review_row(db) == ("pending", 0, "same-subject", None, None, None)
    assert audit_rows(db) == []


def test_legacy_unknown_creator_cannot_be_approved_but_can_be_rejected(tmp_path: Path):
    db = tmp_path / "legacy.sqlite"
    create_legacy_database(db)
    store.migrate_store(db)
    actor = store.Actor("reviewer", frozenset({"analyst"}))

    with pytest.raises(store.DraftPolicyError, match="tác giả"):
        store.decide_draft(db, 1, actor=actor, decision="approve", expected_version=0)

    result = store.decide_draft(
        db,
        1,
        actor=actor,
        decision="reject",
        expected_version=0,
        reason="Không rõ nguồn tạo",
    )
    assert result.status == "rejected"


def test_stale_and_repeated_decisions_conflict_without_extra_audit(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    store.decide_draft(db, draft_id, actor=actor, decision="approve", expected_version=0)

    for decision, expected_version, reason in (
        ("approve", 0, None),
        ("reject", 0, "lặp"),
        ("reject", 1, "state đã kết thúc"),
    ):
        with pytest.raises(store.DraftConflictError):
            store.decide_draft(
                db,
                draft_id,
                actor=actor,
                decision=decision,
                expected_version=expected_version,
                reason=reason,
            )

    assert review_row(db)[:2] == ("approved", 1)
    assert len(audit_rows(db)) == 1


def test_audit_insert_failure_rolls_back_review_state(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "CREATE TRIGGER fail_audit BEFORE INSERT ON draft_audit "
            "BEGIN SELECT RAISE(ABORT, 'forced audit failure'); END"
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(store.DraftSQLiteError, match="forced audit failure"):
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="approve",
            expected_version=0,
        )

    assert review_row(db) == ("pending", 0, "author", None, None, None)
    assert audit_rows(db) == []


def test_commit_failure_rolls_back_review_and_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")

    def fail_commit(connection: sqlite3.Connection) -> None:
        raise sqlite3.OperationalError("forced commit failure")

    monkeypatch.setattr(store, "_commit", fail_commit)
    with pytest.raises(store.DraftSQLiteError, match="forced commit failure"):
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="approve",
            expected_version=0,
        )

    assert review_row(db) == ("pending", 0, "author", None, None, None)
    assert audit_rows(db) == []


def test_two_concurrent_callers_yield_one_decision_and_one_audit(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")

    def decide(subject: str):
        try:
            return store.decide_draft(
                db,
                draft_id,
                actor=store.Actor(subject, frozenset({"analyst"})),
                decision="approve",
                expected_version=0,
                timeout=1.0,
            )
        except store.DraftConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(decide, ("reviewer-a", "reviewer-b")))

    assert sum(isinstance(outcome, store.DraftReviewResult) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, store.DraftConflictError) for outcome in outcomes) == 1
    assert len(audit_rows(db)) == 1


def test_locked_database_times_out_without_retry_and_recovers(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    locker = sqlite3.connect(db, timeout=0.1)
    try:
        locker.execute("BEGIN IMMEDIATE")
        with pytest.raises(store.DraftSQLiteError, match="locked"):
            store.decide_draft(
                db,
                draft_id,
                actor=actor,
                decision="approve",
                expected_version=0,
                timeout=0.01,
            )
    finally:
        locker.rollback()
        locker.close()

    assert (
        store.decide_draft(
            db,
            draft_id,
            actor=actor,
            decision="approve",
            expected_version=0,
        ).status
        == "approved"
    )


@pytest.mark.parametrize(
    ("draft_id", "expected_version"),
    [(True, 0), (0, 0), (2**63, 0), (1, True), (1, -1), (1, 2**63)],
)
def test_invalid_ids_and_versions_are_rejected_before_database_io(tmp_path: Path, draft_id, expected_version):
    db = tmp_path / "missing.sqlite"
    with pytest.raises(store.DraftInputError):
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="approve",
            expected_version=expected_version,
        )
    assert not db.exists()


def test_approve_rejects_reason_and_unsupported_kept_item(tmp_path: Path):
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(store.DraftInputError, match="reason"):
        store.decide_draft(
            missing,
            1,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="approve",
            expected_version=0,
            reason="not allowed",
        )
    assert not missing.exists()

    db = tmp_path / "drafts.sqlite"
    draft = make_draft()
    draft["items"].append(
        {
            "kind": "ttp",
            "type": "attack-pattern",
            "value": "T1566.001",
            "span": [0, 7],
            "evidence": draft["text"][:7],
            "keep": True,
            "warning": None,
            "status": "ok",
        }
    )
    draft_id = store.save_draft(db, draft, created_by_subject="author")

    with pytest.raises(store.DraftPolicyError, match="kind"):
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="approve",
            expected_version=0,
        )


def test_decision_requires_migrated_existing_database_and_rejects_future_schema(tmp_path: Path):
    legacy = tmp_path / "legacy.sqlite"
    create_legacy_database(legacy)
    before = hashlib.sha256(legacy.read_bytes()).hexdigest()
    actor = store.Actor("reviewer", frozenset({"analyst"}))

    with pytest.raises(store.DraftSQLiteError, match="migrate"):
        store.decide_draft(
            legacy,
            1,
            actor=actor,
            decision="reject",
            expected_version=0,
            reason="legacy",
        )
    assert hashlib.sha256(legacy.read_bytes()).hexdigest() == before

    missing = tmp_path / "missing.sqlite"
    with pytest.raises(store.DraftNotFoundError):
        store.decide_draft(
            missing,
            1,
            actor=actor,
            decision="approve",
            expected_version=0,
        )
    assert not missing.exists()

    current = tmp_path / "future.sqlite"
    store.save_draft(current, make_draft(), created_by_subject="author")
    connection = sqlite3.connect(current)
    try:
        connection.execute("PRAGMA user_version = 2")
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(store.DraftSQLiteError, match="Phiên bản"):
        store.decide_draft(
            current,
            1,
            actor=actor,
            decision="approve",
            expected_version=0,
        )


def test_audit_contains_metadata_only_not_report_content(tmp_path: Path):
    marker = "SECRET REPORT TEXT evil.example"
    db = tmp_path / "drafts.sqlite"
    draft_id = store.save_draft(db, make_draft(marker), created_by_subject="author")
    store.decide_draft(
        db,
        draft_id,
        actor=store.Actor("reviewer", frozenset({"analyst"})),
        decision="reject",
        expected_version=0,
        reason="Thiếu ngữ cảnh",
    )

    connection = sqlite3.connect(db)
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(draft_audit)")}
        serialized = json.dumps(connection.execute("SELECT * FROM draft_audit").fetchall())
    finally:
        connection.close()
    assert not columns.intersection({"payload_json", "text", "items", "evidence", "findings"})
    assert marker not in serialized


@pytest.mark.parametrize(
    ("actor", "decision"),
    [
        (store.Actor("reviewer", ["analyst"]), "approve"),
        (store.Actor("reviewer", frozenset({1})), "approve"),
        (store.Actor("reviewer", frozenset({"analyst"})), []),
    ],
)
def test_malformed_actor_and_decision_types_raise_stable_input_error_before_io(
    tmp_path: Path, actor, decision
):
    db = tmp_path / "missing.sqlite"

    with pytest.raises(store.DraftInputError):
        store.decide_draft(
            db,
            1,
            actor=actor,
            decision=decision,
            expected_version=0,
        )

    assert not db.exists()


def test_get_and_list_reject_corrupt_review_metadata_without_writing(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    store.save_draft(db, make_draft(), created_by_subject="author")
    connection = sqlite3.connect(db)
    try:
        connection.execute("UPDATE drafts SET review_version = 1 WHERE id = 1")
        connection.commit()
    finally:
        connection.close()
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    with pytest.raises(store.DraftStoreError, match="review"):
        store.get_draft(db, 1)
    with pytest.raises(store.DraftStoreError, match="review"):
        store.list_drafts(db)

    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_queue_excludes_decided_drafts_but_get_keeps_them_readable(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    approved_id = store.save_draft(db, make_draft("Approved evil.example"), created_by_subject="author-a")
    rejected_id = store.save_draft(db, make_draft("Rejected evil.example"), created_by_subject="author-b")
    pending_id = store.save_draft(db, make_draft("Pending evil.example"), created_by_subject="author-c")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    store.decide_draft(db, approved_id, actor=actor, decision="approve", expected_version=0)
    store.decide_draft(
        db,
        rejected_id,
        actor=actor,
        decision="reject",
        expected_version=0,
        reason="Thiếu ngữ cảnh",
    )

    page = store.list_drafts(db)

    assert [item["id"] for item in page["items"]] == [pending_id]
    assert page["items"][0]["review_status"] == "pending"
    assert store.get_draft(db, approved_id)["review"]["status"] == "approved"
    assert store.get_draft(db, rejected_id)["review"]["status"] == "rejected"


@pytest.mark.parametrize(
    "broken",
    ["draft_checks", "audit_unique", "audit_fk", "audit_action_check", "queue_index"],
)
def test_current_schema_with_matching_columns_but_broken_constraints_is_rejected_before_write(
    tmp_path: Path, broken: str
):
    db = tmp_path / f"broken-{broken}.sqlite"
    create_counterfeit_current_database(db, broken)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    actor = store.Actor("reviewer", frozenset({"analyst"}))

    operations = (
        lambda: store.get_draft(db, 1),
        lambda: store.list_drafts(db),
        lambda: store.migrate_store(db),
        lambda: store.decide_draft(
            db,
            1,
            actor=actor,
            decision="approve",
            expected_version=0,
        ),
        lambda: store.save_draft(db, make_draft(), created_by_subject="author"),
    )
    for operation in operations:
        with pytest.raises(store.DraftSQLiteError, match="Schema"):
            operation()
        assert hashlib.sha256(db.read_bytes()).hexdigest() == before
