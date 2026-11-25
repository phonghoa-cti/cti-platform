from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from pathlib import Path

import pytest

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft

SUMMARY_KEYS = {
    "id",
    "created_at",
    "status",
    "source",
    "language",
    "tlp",
    "item_count",
    "injection_warning",
    "review_status",
    "review_version",
}


def make_draft(index: int, *, text: str | None = None) -> dict:
    content = text or f"Bản nháp {index} 😀 ghi nhận evil{index}.example"
    return build_regex_draft(content, source=f"synthetic-{index}.txt", language="vi")


def save_many(db: Path, count: int) -> list[dict]:
    drafts = [make_draft(index) for index in range(1, count + 1)]
    for draft in drafts:
        store.save_draft(db, draft)
    return drafts


def ids(page: dict) -> list[int]:
    return [item["id"] for item in page["items"]]


def test_list_pages_five_drafts_and_gets_an_id_from_a_real_page(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    drafts = save_many(db, 5)

    first = store.list_drafts(db, limit=2)
    second = store.list_drafts(db, limit=2, before_id=first["next_before_id"])
    third = store.list_drafts(db, limit=2, before_id=second["next_before_id"])

    assert ids(first) == [5, 4]
    assert ids(second) == [3, 2]
    assert ids(third) == [1]
    assert [first["next_before_id"], second["next_before_id"], third["next_before_id"]] == [4, 2, None]
    assert set(first["items"][0]) == SUMMARY_KEYS
    selected_id = second["items"][0]["id"]
    assert store.get_draft(db, selected_id)["text"] == drafts[selected_id - 1]["text"]


def test_cursor_does_not_repeat_or_lose_old_ids_when_a_new_draft_is_inserted(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    save_many(db, 5)
    first = store.list_drafts(db, limit=2)

    assert store.save_draft(db, make_draft(6)) == 6
    second = store.list_drafts(db, limit=2, before_id=first["next_before_id"])
    third = store.list_drafts(db, limit=2, before_id=second["next_before_id"])
    refreshed = store.list_drafts(db, limit=2)

    old_ids = ids(first) + ids(second) + ids(third)
    assert old_ids == [5, 4, 3, 2, 1]
    assert len(old_ids) == len(set(old_ids))
    assert ids(refreshed) == [6, 5]


def test_empty_exact_multiple_single_page_missing_cursor_and_non_pending_rows(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    save_many(db, 4)

    first = store.list_drafts(db, limit=2)
    second = store.list_drafts(db, limit=2, before_id=first["next_before_id"])
    beyond = store.list_drafts(db, limit=2, before_id=999)

    assert ids(first) == [4, 3] and first["next_before_id"] == 3
    assert ids(second) == [2, 1] and second["next_before_id"] is None
    assert ids(beyond) == [4, 3]

    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "UPDATE drafts SET review_status = 'approved', review_version = 1, "
            "decided_by_subject = 'reviewer', decided_at = '2026-11-10T12:00:00+00:00'"
        )
        connection.commit()
    finally:
        connection.close()

    assert store.list_drafts(db) == {"items": [], "next_before_id": None}

    one_db = tmp_path / "one.sqlite"
    store.save_draft(one_db, make_draft(1))
    assert store.list_drafts(one_db, limit=2)["next_before_id"] is None
    assert store.list_drafts(one_db, before_id=1) == {"items": [], "next_before_id": None}


def test_summary_preserves_unicode_metadata_without_report_content(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    marker = "NỘI DUNG NHẠY CẢM 😀 evil.example"
    draft = build_regex_draft(marker, source="báo-cáo-😀.txt", language="vi")
    store.save_draft(db, draft)

    page = store.list_drafts(db)
    summary = page["items"][0]
    serialized = json.dumps(page, ensure_ascii=False)

    assert summary["source"] == draft["source"]
    assert summary["item_count"] == len(draft["items"])
    assert summary["injection_warning"] is draft["injection_warning"]
    assert marker not in serialized
    assert all(key not in summary for key in ("text", "items", "evidence", "findings"))


@pytest.mark.parametrize("limit", [True, False, 0, 101, -1, 1.5, "2"])
def test_list_rejects_invalid_limit_without_creating_database(tmp_path: Path, limit):
    db = tmp_path / "missing.sqlite"

    with pytest.raises(store.DraftStoreError, match="limit"):
        store.list_drafts(db, limit=limit)

    assert not db.exists()


@pytest.mark.parametrize("before_id", [True, False, 0, -1, 2**63, 1.5, "2"])
def test_list_rejects_invalid_cursor_without_changing_existing_data(tmp_path: Path, before_id):
    db = tmp_path / "drafts.sqlite"
    draft = make_draft(1)
    draft_id = store.save_draft(db, draft)

    with pytest.raises(store.DraftStoreError, match="before_id"):
        store.list_drafts(db, before_id=before_id)

    assert store.get_draft(db, draft_id)["source"] == draft["source"]


@pytest.mark.parametrize("timeout", [True, -1, math.inf, math.nan, "1"])
def test_list_rejects_non_finite_or_invalid_timeout_before_opening_database(tmp_path: Path, timeout):
    db = tmp_path / "missing.sqlite"

    with pytest.raises(store.DraftStoreError, match="timeout"):
        store.list_drafts(db, timeout=timeout)

    assert not db.exists()


def test_list_missing_or_corrupt_database_never_creates_or_rewrites(tmp_path: Path):
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(store.DraftStoreError, match="không tồn tại"):
        store.list_drafts(missing)
    assert not missing.exists()

    corrupt = tmp_path / "corrupt.sqlite"
    corrupt.write_bytes(b"not a sqlite database")
    before = corrupt.read_bytes()
    with pytest.raises(store.DraftStoreError, match="SQLite"):
        store.list_drafts(corrupt)
    assert corrupt.read_bytes() == before


@pytest.mark.parametrize("payload", ["{not-json", '{"status":"pending"}'])
def test_list_rejects_corrupt_payload_without_leaking_or_skipping_it(tmp_path: Path, payload: str):
    db = tmp_path / "drafts.sqlite"
    store.save_draft(db, make_draft(1))
    connection = sqlite3.connect(db)
    try:
        connection.execute("UPDATE drafts SET payload_json = ? WHERE id = 1", (payload,))
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(store.DraftStoreError) as exc_info:
        store.list_drafts(db)

    assert payload not in str(exc_info.value)


def test_list_rejects_created_at_without_iso_timezone(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    store.save_draft(db, make_draft(1))
    connection = sqlite3.connect(db)
    try:
        connection.execute("UPDATE drafts SET created_at = 'not-a-time' WHERE id = 1")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(store.DraftStoreError, match="created_at"):
        store.list_drafts(db)


def test_list_lock_timeout_and_successful_reads_leave_database_bytes_unchanged(tmp_path: Path):
    db = tmp_path / "drafts.sqlite"
    store.save_draft(db, make_draft(1))
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    locker = sqlite3.connect(db, timeout=0.1)
    try:
        locker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(store.DraftStoreError, match="locked"):
            store.list_drafts(db, timeout=0.01)
    finally:
        locker.rollback()
        locker.close()

    assert ids(store.list_drafts(db)) == [1]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash
