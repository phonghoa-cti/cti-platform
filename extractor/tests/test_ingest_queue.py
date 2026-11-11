from __future__ import annotations

import copy
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft
from phonghoa_extractor.ingest_queue import (
    IngestEnvelopeError,
    get_ingest_provenance,
    load_ingest_envelope,
    save_ingested_envelope,
)


def make_envelope(*, text: str = "Nguồn 😀 ghi nhận evil.example", format: str = "text") -> dict:
    draft = build_regex_draft(text, source=f"synthetic.{format}", language="vi")
    canonical = draft["source"]["sha256"]
    if format == "text":
        raw_hash = canonical
        raw_bytes = len(text.encode("utf-8"))
        page_count = None
        ranges = None
    else:
        separator = "\n\f\n"
        assert separator in text
        split = text.index(separator)
        raw_hash = "a" * 64
        raw_bytes = 1234
        page_count = 2
        ranges = [[0, split], [split + len(separator), len(text)]]
    return {
        "schema_version": "x01-local-ingest/1.0",
        "input": {
            "format": format,
            "display_name": draft["source"]["name"],
            "raw_sha256": raw_hash,
            "raw_bytes": raw_bytes,
            "canonical_text_sha256": canonical,
            "page_count": page_count,
            "page_text_ranges": ranges,
        },
        "draft": draft,
    }


def create_v2_database(db: Path) -> None:
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    with sqlite3.connect(db) as connection:
        connection.execute("DROP TABLE IF EXISTS draft_ingest_provenance")
        connection.execute("PRAGMA user_version = 2")
        connection.commit()


def row_counts(db: Path) -> tuple[int, int]:
    with sqlite3.connect(db) as connection:
        return (
            connection.execute("SELECT COUNT(*) FROM drafts").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM draft_ingest_provenance").fetchone()[0],
        )


def test_text_import_migrates_v2_and_preserves_exact_payload_and_provenance(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    create_v2_database(db)
    envelope = make_envelope()
    original = copy.deepcopy(envelope)

    result = save_ingested_envelope(db, envelope, created_by_subject="creator-1")

    assert result.result == "imported"
    assert envelope == original
    stored = store.get_draft(db, result.draft_id)
    assert {key: stored[key] for key in envelope["draft"]} == envelope["draft"]
    assert stored["review"]["created_by_subject"] == "creator-1"
    provenance = get_ingest_provenance(db, result.draft_id)
    assert provenance.input_format == "text"
    assert provenance.page_text_ranges is None
    assert provenance.raw_sha256 == envelope["input"]["raw_sha256"]
    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' "
                "AND name='idx_draft_selection_audit_draft_version'"
            ).fetchone()[0]
            == 1
        )


def test_pdf_ranges_and_unicode_round_trip_as_immutable_tuples(tmp_path: Path):
    text = "Trang một evil.example\n\f\nTrang hai 203.0.113.9"
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))

    result = save_ingested_envelope(
        db, make_envelope(text=text, format="pdf"), created_by_subject="creator-1"
    )

    provenance = get_ingest_provenance(db, result.draft_id)
    assert provenance.page_count == 2
    separator = text.index("\n\f\n")
    assert provenance.page_text_ranges == ((0, separator), (separator + 3, len(text)))


def test_same_canonical_envelope_is_idempotent_only_for_same_creator(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = make_envelope()

    first = save_ingested_envelope(db, envelope, created_by_subject="creator-1")
    duplicate = save_ingested_envelope(db, copy.deepcopy(envelope), created_by_subject="creator-1")
    assert duplicate.result == "duplicate"
    assert duplicate.draft_id == first.draft_id
    before = row_counts(db)

    with pytest.raises(store.DraftConflictError, match="creator"):
        save_ingested_envelope(db, envelope, created_by_subject="creator-2")
    assert row_counts(db) == before


def test_distinct_envelope_fields_do_not_merge_on_raw_hash(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    first = make_envelope(text="Một evil.example\n\f\nHai", format="pdf")
    second = make_envelope(text="Khác evil.example\n\f\nHai", format="pdf")
    assert second["input"]["raw_sha256"] == first["input"]["raw_sha256"]

    one = save_ingested_envelope(db, first, created_by_subject="creator-1")
    two = save_ingested_envelope(db, second, created_by_subject="creator-1")

    assert one.draft_id != two.draft_id
    assert row_counts(db)[1] == 2


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.update({"extra": 1}), "invalid_envelope"),
        (lambda value: value["input"].update({"raw_bytes": True}), "invalid_input_metadata"),
        (lambda value: value["input"].update({"display_name": "bad/name"}), "invalid_input_metadata"),
        (lambda value: value["input"].update({"canonical_text_sha256": "0" * 64}), "invalid_provenance"),
        (lambda value: value["draft"].update({"status": "approved"}), "invalid_draft"),
    ],
)
def test_invalid_envelope_fails_before_database_mutation(tmp_path: Path, mutation, code: str):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = make_envelope()
    mutation(envelope)
    before = db.read_bytes()

    with pytest.raises(IngestEnvelopeError) as captured:
        save_ingested_envelope(db, envelope, created_by_subject="creator-1")

    assert captured.value.code == code
    assert db.read_bytes() == before


def test_pdf_separator_and_page_bounds_are_strict(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = make_envelope(text="Trang 1 evil.example\n\f\nTrang 2", format="pdf")
    envelope["input"]["page_text_ranges"][1][0] += 1

    with pytest.raises(IngestEnvelopeError) as captured:
        save_ingested_envelope(db, envelope, created_by_subject="creator-1")
    assert captured.value.code == "invalid_provenance"


def test_parse_rejects_duplicate_keys_nonfinite_surrogate_and_depth(tmp_path: Path):
    samples = {
        "duplicate_json_key": b'{"schema_version":"x","schema_version":"y"}',
        "invalid_json": b'{"value":NaN}',
        "invalid_utf8": b'{"value":"\\ud800"}',
        "json_too_deep": ("[" * 65 + "0" + "]" * 65).encode(),
    }
    for code, payload in samples.items():
        path = tmp_path / f"{code}.json"
        path.write_bytes(payload)
        with pytest.raises(IngestEnvelopeError) as captured:
            load_ingest_envelope(path)
        assert captured.value.code == code


def test_missing_or_oversized_envelope_has_closed_read_error(tmp_path: Path):
    with pytest.raises(IngestEnvelopeError) as missing:
        load_ingest_envelope(tmp_path / "missing.json")
    assert missing.value.code == "envelope_read_failed"
    large = tmp_path / "large.json"
    large.write_bytes(b" " * (16 * 1024 * 1024 + 1))
    with pytest.raises(IngestEnvelopeError) as oversized:
        load_ingest_envelope(large)
    assert oversized.value.code == "envelope_too_large"


def test_provenance_insert_and_commit_failure_leave_no_orphan(tmp_path: Path, monkeypatch):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TRIGGER fail_provenance BEFORE INSERT ON draft_ingest_provenance "
            "BEGIN SELECT RAISE(ABORT, 'forced provenance failure'); END"
        )
        connection.commit()
    with pytest.raises(store.DraftSQLiteError):
        save_ingested_envelope(db, make_envelope(), created_by_subject="creator-1")
    assert row_counts(db) == (1, 0)
    with sqlite3.connect(db) as connection:
        connection.execute("DROP TRIGGER fail_provenance")
        connection.commit()

    monkeypatch.setattr(
        store, "_commit", lambda _connection: (_ for _ in ()).throw(sqlite3.OperationalError("x"))
    )
    with pytest.raises(store.DraftSQLiteError):
        save_ingested_envelope(db, make_envelope(), created_by_subject="creator-1")
    assert row_counts(db) == (1, 0)


def test_two_writers_create_exactly_one_draft_and_one_provenance(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    envelope = make_envelope()

    def import_once():
        return save_ingested_envelope(db, copy.deepcopy(envelope), created_by_subject="creator-1")

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _value: import_once(), range(2)))

    assert sorted(result.result for result in outcomes) == ["duplicate", "imported"]
    assert row_counts(db) == (2, 1)


def test_two_migrators_recheck_v2_under_writer_lock(tmp_path: Path):
    db = tmp_path / "v2.sqlite"
    create_v2_database(db)
    barrier = threading.Barrier(2)

    def migrate_once():
        barrier.wait()
        store.migrate_store(db, timeout=5)

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _value: migrate_once(), range(2)))

    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM draft_ingest_provenance").fetchone()[0] == 0


def test_failed_v2_to_v3_commit_rolls_back_table_and_version(tmp_path: Path, monkeypatch):
    db = tmp_path / "v2.sqlite"
    create_v2_database(db)
    monkeypatch.setattr(
        store, "_commit", lambda _connection: (_ for _ in ()).throw(sqlite3.OperationalError("x"))
    )

    with pytest.raises(store.DraftSQLiteError):
        store.migrate_store(db)

    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='draft_ingest_provenance'"
            ).fetchone()[0]
            == 0
        )


def test_corrupt_provenance_fails_closed_for_existing_w05_reader(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))
    imported = save_ingested_envelope(db, make_envelope(), created_by_subject="creator-1")
    with sqlite3.connect(db) as connection:
        connection.execute(
            "UPDATE draft_ingest_provenance SET canonical_text_sha256=? WHERE draft_id=?",
            ("0" * 64, imported.draft_id),
        )
        connection.commit()
    before = db.read_bytes()

    with pytest.raises(store.DraftSQLiteError, match="Provenance"):
        store.get_draft(db, imported.draft_id)

    assert db.read_bytes() == before


def test_library_rejects_recursive_mapping_before_database_io(tmp_path: Path):
    envelope = make_envelope()
    envelope["loop"] = envelope

    with pytest.raises(IngestEnvelopeError) as captured:
        save_ingested_envelope(tmp_path / "missing.sqlite", envelope, created_by_subject="creator-1")

    assert captured.value.code == "invalid_envelope"
    assert not (tmp_path / "missing.sqlite").exists()


def test_v2_and_v3_readers_do_not_migrate_or_write(tmp_path: Path):
    v2 = tmp_path / "v2.sqlite"
    create_v2_database(v2)
    before = v2.read_bytes()
    assert store.get_draft(v2, 1)["id"] == 1
    assert store.list_drafts(v2)["items"]
    assert v2.read_bytes() == before

    store.migrate_store(v2)
    after = v2.read_bytes()
    assert store.get_draft(v2, 1)["id"] == 1
    assert store.get_effective_selection(v2, 1).draft_id == 1
    assert v2.read_bytes() == after


def test_draft_without_provenance_is_not_reported_as_ingested(tmp_path: Path):
    db = tmp_path / "queue.sqlite"
    draft_id = store.save_draft(db, build_regex_draft("seed.example", source="seed.txt", language="vi"))

    with pytest.raises(store.DraftNotFoundError):
        get_ingest_provenance(db, draft_id)
