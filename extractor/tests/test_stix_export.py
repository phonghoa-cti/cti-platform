from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import sqlite3
import subprocess
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from phonghoa_core.ioc import normalize
from phonghoa_extractor import stix_export, store

IOC_VALUES = (
    "8.8.8.8",
    "2606:4700:4700::1111",
    "evil.example",
    "https://evil.example/path?q=1",
    "alert@evil.example",
    "d41d8cd98f00b204e9800998ecf8427e",
    "da39a3ee5e6b4b0d3255bfef95601890afd80709",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
)


def make_ioc_draft(values: tuple[str, ...] = IOC_VALUES, *, tlp: str = "TLP:GREEN") -> dict:
    text = " | ".join(values)
    items = []
    cursor = 0
    for raw in values:
        normalized = normalize(raw)
        start = text.index(raw, cursor)
        end = start + len(raw)
        cursor = end
        items.append(
            {
                "kind": "ioc",
                "type": normalized.type.value,
                "value": normalized.value,
                "span": [start, end],
                "evidence": raw,
                "keep": True,
                "warning": None,
                "status": "ok",
            }
        )
    return {
        "schema_version": "1.0",
        "status": "pending",
        "source": {
            "name": "synthetic.txt",
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        },
        "language": "vi",
        "tlp": tlp,
        "text": text,
        "items": items,
        "injection_warning": False,
        "findings": [],
        "model": "synthetic-test",
        "cost_tokens": 0,
    }


def approve_draft(
    db: Path,
    *,
    values: tuple[str, ...] = IOC_VALUES,
    selected: tuple[int, ...] | None = None,
    tlp: str = "TLP:GREEN",
) -> int:
    draft_id = store.save_draft(db, make_ioc_draft(values, tlp=tlp), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    version = 0
    if selected is not None:
        saved = store.save_selection(
            db,
            draft_id,
            actor=actor,
            selected_indices=list(selected),
            expected_version=0,
        )
        version = saved.review_version
    store.decide_draft(
        db,
        draft_id,
        actor=actor,
        decision="approve",
        expected_version=version,
    )
    return draft_id


def exporter_config(*, tlp: str = "TLP:GREEN", name: str = "Phong Hoa test exporter") -> dict:
    return {
        "schema_version": "1",
        "id_namespace_uuid": "3f33d4f4-e1ac-4b20-b94d-44e2563f15ed",
        "name": name,
        "identity_class": "organization",
        "created": "2026-01-01T00:00:00.000Z",
        "tlp": tlp,
    }


def test_snapshot_uses_final_approve_audit_and_hides_reviewer_from_repr(tmp_path: Path):
    db = tmp_path / "approved.sqlite"
    draft_id = approve_draft(db, selected=(1, 3))

    snapshot = store.get_approved_export_snapshot(db, draft_id)

    assert snapshot.draft_id == draft_id
    assert snapshot.selected_indices == (1, 3)
    assert snapshot.final_selection_version == 1
    assert snapshot.review_version == 2
    assert snapshot.decided_by_subject == "reviewer"
    assert "reviewer" not in repr(snapshot)
    assert snapshot.selected_sha256 == hashlib.sha256(b"[1,3]").hexdigest()
    snapshot.payload["source"]["name"] = "mutated"
    assert store.get_approved_export_snapshot(db, draft_id).payload["source"]["name"] == "synthetic.txt"


def test_snapshot_begins_transaction_before_schema_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    db = tmp_path / "begin-first.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    original = store._validate_current_schema
    observed: list[bool] = []

    def validate_after_begin(connection: sqlite3.Connection) -> None:
        observed.append(connection.in_transaction)
        original(connection)

    monkeypatch.setattr(store, "_validate_current_schema", validate_after_begin)
    store.get_approved_export_snapshot(db, draft_id)
    assert observed == [True]


def test_snapshot_wal_interleaving_never_mixes_schema_and_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    db = tmp_path / "wal-interleave.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    with sqlite3.connect(db) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    original = store._validate_current_schema
    entered = False

    def validate_then_write(connection: sqlite3.Connection) -> None:
        nonlocal entered
        original(connection)
        if not entered:
            entered = True
            with sqlite3.connect(db) as writer:
                payload = json.loads(writer.execute("SELECT payload_json FROM drafts").fetchone()[0])
                payload["model"] = "writer-committed-after-schema-read"
                writer.execute(
                    "UPDATE drafts SET payload_json=? WHERE id=?",
                    (
                        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                        draft_id,
                    ),
                )

    monkeypatch.setattr(store, "_validate_current_schema", validate_then_write)
    old = store.get_approved_export_snapshot(db, draft_id)
    current = store.get_approved_export_snapshot(db, draft_id)

    assert old.payload["model"] == "synthetic-test"
    assert current.payload["model"] == "writer-committed-after-schema-read"


def test_snapshot_validates_every_selection_event_not_only_latest(tmp_path: Path):
    db = tmp_path / "all-selection-events.sqlite"
    draft_id = store.save_draft(db, make_ioc_draft(), created_by_subject="author")
    actor = store.Actor("reviewer", frozenset({"analyst"}))
    first = store.save_selection(db, draft_id, actor=actor, selected_indices=[1, 2], expected_version=0)
    second = store.save_selection(
        db,
        draft_id,
        actor=actor,
        selected_indices=[2],
        expected_version=first.review_version,
    )
    store.decide_draft(
        db,
        draft_id,
        actor=actor,
        decision="approve",
        expected_version=second.review_version,
    )
    with sqlite3.connect(db) as connection:
        connection.execute("UPDATE draft_selection_audit SET actor_subject='' WHERE selection_version=1")

    with pytest.raises(store.DraftStoreError, match="selection actor"):
        store.get_approved_export_snapshot(db, draft_id)


@pytest.mark.parametrize("state", ["pending", "rejected", "legacy", "future"])
def test_snapshot_fails_closed_for_non_approved_or_wrong_schema(tmp_path: Path, state: str):
    db = tmp_path / f"{state}.sqlite"
    draft_id = store.save_draft(db, make_ioc_draft(), created_by_subject="author")
    if state == "rejected":
        store.decide_draft(
            db,
            draft_id,
            actor=store.Actor("reviewer", frozenset({"analyst"})),
            decision="reject",
            expected_version=0,
            reason="synthetic rejection",
        )
    elif state == "legacy":
        with sqlite3.connect(db) as connection:
            connection.execute("PRAGMA user_version = 1")
    elif state == "future":
        with sqlite3.connect(db) as connection:
            connection.execute("PRAGMA user_version = 3")

    with pytest.raises(store.DraftStoreError):
        store.get_approved_export_snapshot(db, draft_id)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_audit",
        "audit_actor",
        "audit_time",
        "audit_version",
        "audit_reason",
        "audit_id",
        "selection_hash",
        "selection_event",
        "creator_missing",
        "self_review",
    ],
)
def test_snapshot_detects_authority_and_integrity_tampering(tmp_path: Path, mutation: str):
    db = tmp_path / f"tamper-{mutation}.sqlite"
    draft_id = approve_draft(db, selected=(1, 3))
    with sqlite3.connect(db) as connection:
        if mutation == "duplicate_audit":
            original = connection.execute("SELECT * FROM draft_audit").fetchone()
            connection.execute("ALTER TABLE draft_audit RENAME TO old_draft_audit")
            connection.execute(
                """CREATE TABLE draft_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draft_id INTEGER NOT NULL REFERENCES drafts(id),
                    action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
                    at TEXT NOT NULL, actor_subject TEXT NOT NULL,
                    expected_version INTEGER NOT NULL, previous_status TEXT NOT NULL,
                    new_status TEXT NOT NULL, previous_version INTEGER NOT NULL,
                    new_version INTEGER NOT NULL, reason TEXT, selection_version INTEGER,
                    selected_indices_json TEXT, selected_sha256 TEXT
                )"""
            )
            placeholders = ",".join("?" for _ in original)
            connection.execute(f"INSERT INTO draft_audit VALUES ({placeholders})", original)
            duplicate = (None, *original[1:])
            connection.execute(f"INSERT INTO draft_audit VALUES ({placeholders})", duplicate)
        elif mutation == "audit_actor":
            connection.execute("UPDATE draft_audit SET actor_subject='attacker'")
        elif mutation == "audit_time":
            connection.execute("UPDATE draft_audit SET at='2026-01-01T00:00:00+00:00'")
        elif mutation == "audit_version":
            connection.execute("UPDATE draft_audit SET new_version=99")
        elif mutation == "audit_reason":
            connection.execute("UPDATE draft_audit SET reason='not-null'")
        elif mutation == "audit_id":
            connection.execute("UPDATE draft_audit SET id=-1")
        elif mutation == "selection_hash":
            connection.execute("UPDATE draft_audit SET selected_sha256=?", ("0" * 64,))
        elif mutation == "selection_event":
            connection.execute("DELETE FROM draft_selection_audit")
        elif mutation == "creator_missing":
            connection.execute("UPDATE drafts SET created_by_subject=NULL")
        elif mutation == "self_review":
            connection.execute("UPDATE drafts SET created_by_subject='reviewer'")

    with pytest.raises(store.DraftStoreError):
        store.get_approved_export_snapshot(db, draft_id)


def test_build_bundle_maps_all_eight_iocs_and_exact_provenance(tmp_path: Path):
    db = tmp_path / "all.sqlite"
    draft_id = approve_draft(db)
    snapshot = store.get_approved_export_snapshot(db, draft_id)
    config = stix_export.validate_exporter_config(exporter_config())

    artifact = stix_export.build_bundle(snapshot, config)
    bundle = json.loads(artifact.bytes)

    assert artifact.bytes.endswith(b"\n")
    assert bundle.keys() == {"type", "id", "objects"}
    assert bundle["type"] == "bundle"
    assert "created" not in bundle and "spec_version" not in bundle
    assert [obj["type"] for obj in bundle["objects"]] == [
        "marking-definition",
        "identity",
        "ipv4-addr",
        "ipv6-addr",
        "domain-name",
        "url",
        "email-addr",
        "file",
        "file",
        "file",
        "report",
    ]
    assert bundle["objects"][7]["hashes"] == {"MD5": IOC_VALUES[5]}
    assert bundle["objects"][8]["hashes"] == {"SHA-1": IOC_VALUES[6]}
    assert bundle["objects"][9]["hashes"] == {"SHA-256": IOC_VALUES[7]}
    marking = bundle["objects"][0]
    assert marking["id"] == "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da"
    assert "object_marking_refs" not in marking
    report = bundle["objects"][-1]
    assert report["created"] == report["modified"] == report["published"]
    assert report["created"] == artifact.provenance["decided_at"]
    assert report["created"].endswith("Z")
    assert report["created_by_ref"] == bundle["objects"][1]["id"]
    assert report["object_refs"] == [obj["id"] for obj in bundle["objects"][1:-1]]
    assert len(report["external_references"]) == 1
    reference = report["external_references"][0]
    provenance = json.loads(reference["description"])
    assert reference["source_name"] == "phong-hoa-approved-snapshot"
    assert reference["external_id"] == hashlib.sha256(reference["description"].encode()).hexdigest()
    assert provenance == artifact.provenance
    assert provenance["selected_indices"] == list(range(8))
    serialized = artifact.bytes.decode()
    assert "reviewer" not in serialized
    assert "synthetic.txt" not in serialized
    assert snapshot.payload["text"] not in serialized
    assert not {"indicator", "observed-data", "relationship", "attack-pattern"}.intersection(
        obj["type"] for obj in bundle["objects"]
    )


@pytest.mark.parametrize(
    ("source_tlp", "config_tlp", "marking_id", "stix_tlp"),
    [
        (
            "TLP:CLEAR",
            "TLP:CLEAR",
            "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9",
            "TLP:WHITE",
        ),
        (
            "TLP:AMBER",
            "TLP:AMBER",
            "marking-definition--f88d31f6-486f-44da-b317-01333bde0b82",
            "TLP:AMBER",
        ),
        (
            "TLP:RED",
            "TLP:RED",
            "marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed",
            "TLP:RED",
        ),
    ],
)
def test_tlp_mapping_is_literal_and_provenance_keeps_source_tlp(
    tmp_path: Path, source_tlp: str, config_tlp: str, marking_id: str, stix_tlp: str
):
    db = tmp_path / "tlp.sqlite"
    draft_id = approve_draft(db, values=("evil.example",), tlp=source_tlp)
    artifact = stix_export.build_bundle(
        store.get_approved_export_snapshot(db, draft_id),
        stix_export.validate_exporter_config(exporter_config(tlp=config_tlp)),
    )
    bundle = json.loads(artifact.bytes)
    assert bundle["objects"][0]["id"] == marking_id
    assert artifact.provenance["source_tlp"] == source_tlp
    assert artifact.provenance["stix_tlp"] == stix_tlp


def test_amber_strict_and_tlp_mismatch_fail_closed(tmp_path: Path):
    strict_db = tmp_path / "strict.sqlite"
    strict_id = approve_draft(strict_db, values=("evil.example",), tlp="TLP:AMBER+STRICT")
    strict_snapshot = store.get_approved_export_snapshot(strict_db, strict_id)
    with pytest.raises(stix_export.StixExportError, match=r"AMBER\+STRICT"):
        stix_export.build_bundle(
            strict_snapshot,
            stix_export.validate_exporter_config(exporter_config(tlp="TLP:AMBER+STRICT")),
        )

    green_db = tmp_path / "green.sqlite"
    green_id = approve_draft(green_db, values=("evil.example",))
    with pytest.raises(stix_export.StixExportError, match="TLP"):
        stix_export.build_bundle(
            store.get_approved_export_snapshot(green_db, green_id),
            stix_export.validate_exporter_config(exporter_config(tlp="TLP:RED")),
        )


def test_deterministic_ids_use_independent_known_sco_vector_and_child_namespaces(tmp_path: Path):
    db = tmp_path / "ids.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    snapshot = store.get_approved_export_snapshot(db, draft_id)
    config = stix_export.validate_exporter_config(exporter_config())

    first = stix_export.build_bundle(snapshot, config)
    second = stix_export.build_bundle(snapshot, config)
    bundle = json.loads(first.bytes)
    domain = bundle["objects"][2]
    expected_uuid = uuid.uuid5(uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7"), '{"value":"evil.example"}')

    assert first.bytes == second.bytes
    assert domain["id"] == f"domain-name--{expected_uuid}"
    assert uuid.UUID(domain["id"].split("--", 1)[1]).version == 5
    namespace = uuid.UUID(exporter_config()["id_namespace_uuid"])
    children = {
        uuid.uuid5(namespace, "phonghoa:w05:stix:1:identity"),
        uuid.uuid5(namespace, "phonghoa:w05:stix:1:report"),
        uuid.uuid5(namespace, "phonghoa:w05:stix:1:bundle"),
    }
    assert len(children) == 3
    assert stix_export.SCO_NAMESPACE not in children
    assert all(uuid.UUID(obj["id"].split("--", 1)[1]).version == 5 for obj in bundle["objects"][1:])


def test_report_and_bundle_ids_change_with_provenance_but_sco_id_does_not(tmp_path: Path):
    first_db = tmp_path / "first.sqlite"
    second_db = tmp_path / "second.sqlite"
    first_id = approve_draft(first_db, values=("evil.example",))
    second_id = approve_draft(second_db, values=("evil.example",))
    with sqlite3.connect(second_db) as connection:
        connection.execute(
            "UPDATE drafts SET payload_json=replace(payload_json, 'synthetic-test', 'other-model')"
        )
    config = stix_export.validate_exporter_config(exporter_config())

    first = json.loads(
        stix_export.build_bundle(store.get_approved_export_snapshot(first_db, first_id), config).bytes
    )
    second = json.loads(
        stix_export.build_bundle(store.get_approved_export_snapshot(second_db, second_id), config).bytes
    )

    assert first["objects"][2]["id"] == second["objects"][2]["id"]
    assert first["objects"][-1]["id"] != second["objects"][-1]["id"]
    assert first["id"] != second["id"]


@pytest.mark.parametrize(
    "change",
    [
        {"extra": "field"},
        {"schema_version": "2"},
        {"id_namespace_uuid": "00000000-0000-0000-0000-000000000000"},
        {"id_namespace_uuid": str(stix_export.SCO_NAMESPACE)},
        {"name": " "},
        {"identity_class": "individual"},
        {"created": "2026-01-01T00:00:00"},
        {"created": "0001-01-01T00:00:00+01:00"},
        {"created": "9999-12-31T23:59:59-01:00"},
        {"tlp": "TLP:BLUE"},
        {"tlp": []},
        {"tlp": {}},
    ],
)
def test_exporter_config_is_strict(change: dict[str, object]):
    config = exporter_config()
    config.update(change)
    with pytest.raises(stix_export.StixExportError):
        stix_export.validate_exporter_config(config)


def test_serializer_defensively_rejects_unsupported_selected_item(tmp_path: Path):
    db = tmp_path / "unsupported.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    snapshot = store.get_approved_export_snapshot(db, draft_id)
    bad_payload = json.loads(json.dumps(snapshot.payload))
    bad_payload["items"][0]["kind"] = "ttp"
    tampered = replace(snapshot, payload=bad_payload)

    with pytest.raises(stix_export.StixExportError, match="IOC"):
        stix_export.build_bundle(tampered, stix_export.validate_exporter_config(exporter_config()))


def test_publish_is_no_clobber_idempotent_and_protects_inputs(tmp_path: Path):
    output = tmp_path / "bundle.json"
    protected = tmp_path / "approved.sqlite"
    protected.write_bytes(b"database")

    stix_export.publish_bytes(output, b"first\n", protected_paths=(protected,))
    first_stat = output.stat()
    stix_export.publish_bytes(output, b"first\n", protected_paths=(protected,))
    assert output.read_bytes() == b"first\n"
    assert output.stat().st_mtime_ns == first_stat.st_mtime_ns
    with pytest.raises(stix_export.StixExportError, match="tồn tại"):
        stix_export.publish_bytes(output, b"second\n", protected_paths=(protected,))
    assert output.read_bytes() == b"first\n"
    with pytest.raises(stix_export.StixExportError, match="bảo vệ"):
        stix_export.publish_bytes(protected, b"bad", protected_paths=(protected,))
    with pytest.raises(stix_export.StixExportError):
        stix_export.publish_bytes(Path(str(protected) + "-wal"), b"bad", protected_paths=(protected,))
    assert protected.read_bytes() == b"database"


def test_publish_rejects_directory_symlink_and_hardlink_aliases(tmp_path: Path):
    protected = tmp_path / "config.json"
    protected.write_text("{}", encoding="utf-8")
    directory = tmp_path / "directory"
    directory.mkdir()
    hardlink = tmp_path / "hardlink.json"
    os.link(protected, hardlink)

    with pytest.raises(stix_export.StixExportError):
        stix_export.publish_bytes(directory, b"x", protected_paths=(protected,))
    with pytest.raises(stix_export.StixExportError, match="bảo vệ"):
        stix_export.publish_bytes(hardlink, b"x", protected_paths=(protected,))

    symlink = tmp_path / "symlink.json"
    try:
        symlink.symlink_to(protected)
    except OSError:
        pytest.fail("Windows test environment must support file symlinks for fail-closed coverage")
    with pytest.raises(stix_export.StixExportError, match="symbolic"):
        stix_export.publish_bytes(symlink, b"x", protected_paths=(protected,))


def test_publish_rejects_reparse_ancestor_not_only_immediate_parent(tmp_path: Path):
    real_parent = tmp_path / "real-parent"
    child = real_parent / "child"
    child.mkdir(parents=True)
    alias_parent = tmp_path / "alias-parent"
    try:
        alias_parent.symlink_to(real_parent, target_is_directory=True)
    except OSError:
        pytest.fail("Windows test environment must support directory symlinks")

    with pytest.raises(stix_export.StixExportError, match="reparse"):
        stix_export.publish_bytes(alias_parent / "child" / "bundle.json", b"complete\n")


@pytest.mark.parametrize("alias_kind", ["file_symlink", "directory_symlink"])
@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
@pytest.mark.parametrize("protected_kind", ["database", "config"])
def test_export_protects_resolved_input_sidecars(
    tmp_path: Path, alias_kind: str, suffix: str, protected_kind: str
):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    db = real_dir / "approved.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    config = real_dir / "exporter.json"
    config.write_text(json.dumps(exporter_config()), encoding="utf-8")
    protected = db if protected_kind == "database" else config
    if alias_kind == "file_symlink":
        alias = tmp_path / protected.name
        alias.symlink_to(protected)
    else:
        alias_dir = tmp_path / "alias-dir"
        alias_dir.symlink_to(real_dir, target_is_directory=True)
        alias = alias_dir / protected.name
    db_input = alias if protected_kind == "database" else db
    config_input = alias if protected_kind == "config" else config
    output = Path(str(protected) + suffix)
    before_db = hashlib.sha256(db.read_bytes()).hexdigest()
    before_config = hashlib.sha256(config.read_bytes()).hexdigest()

    with pytest.raises(stix_export.StixExportError, match="bảo vệ"):
        stix_export.export_approved(
            db_path=db_input,
            draft_id=draft_id,
            exporter_config_path=config_input,
            output_path=output,
        )

    assert not output.exists()
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_db
    assert hashlib.sha256(config.read_bytes()).hexdigest() == before_config
    assert not list(real_dir.glob(".*.tmp"))


@pytest.mark.parametrize("alias_kind", ["file_symlink", "directory_symlink"])
@pytest.mark.parametrize("protected_kind", ["database", "config"])
def test_export_supports_static_input_alias_to_regular_bundle(
    tmp_path: Path, alias_kind: str, protected_kind: str
):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    db = real_dir / "approved.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    config = real_dir / "exporter.json"
    config.write_text(json.dumps(exporter_config()), encoding="utf-8")
    protected = db if protected_kind == "database" else config
    if alias_kind == "file_symlink":
        alias = tmp_path / protected.name
        alias.symlink_to(protected)
    else:
        alias_dir = tmp_path / "alias-dir"
        alias_dir.symlink_to(real_dir, target_is_directory=True)
        alias = alias_dir / protected.name
    output = tmp_path / "bundle.json"

    result = stix_export.export_approved(
        db_path=alias if protected_kind == "database" else db,
        draft_id=draft_id,
        exporter_config_path=alias if protected_kind == "config" else config,
        output_path=output,
    )

    assert result.object_count == 4
    assert json.loads(output.read_bytes())["type"] == "bundle"


def test_publish_windows_race_same_bytes_both_succeed(tmp_path: Path):
    output = tmp_path / "same.json"
    barrier = threading.Barrier(2)

    def publish() -> None:
        stix_export.publish_bytes(output, b"complete\n", before_link=barrier.wait)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(publish) for _ in range(2)]
        for future in futures:
            future.result()
    assert output.read_bytes() == b"complete\n"


def test_publish_windows_race_different_bytes_has_one_winner(tmp_path: Path):
    output = tmp_path / "different.json"
    barrier = threading.Barrier(2)

    def publish(data: bytes) -> str:
        try:
            stix_export.publish_bytes(output, data, before_link=barrier.wait)
            return "success"
        except stix_export.StixExportError:
            return "conflict"

    values = (b"first-complete\n", b"second-complete\n")
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(publish, values))
    assert sorted(outcomes) == ["conflict", "success"]
    assert output.read_bytes() in values


def test_publish_race_rechecks_protected_alias_before_identical_compare(tmp_path: Path):
    protected = tmp_path / "approved.sqlite"
    protected.write_bytes(b"same-bytes")
    output = tmp_path / "bundle.json"

    def insert_protected_alias() -> None:
        os.link(protected, output)

    with pytest.raises(stix_export.StixExportError, match="bảo vệ"):
        stix_export.publish_bytes(
            output,
            b"same-bytes",
            protected_paths=(protected,),
            before_link=insert_protected_alias,
        )
    assert output.samefile(protected)


def test_publish_write_link_and_cleanup_failures_only_remove_owned_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "failure.json"
    foreign = tmp_path / ".failure.json.foreign.tmp"
    foreign.write_bytes(b"foreign")

    real_link = os.link

    def fail_link(_source, _target):
        raise OSError("forced link failure")

    monkeypatch.setattr(os, "link", fail_link)
    with pytest.raises(stix_export.StixExportError, match="publish"):
        stix_export.publish_bytes(output, b"complete\n")
    assert not output.exists()
    assert foreign.read_bytes() == b"foreign"
    assert list(tmp_path.glob(".failure.json.*.tmp")) == [foreign]

    monkeypatch.setattr(os, "link", real_link)
    real_unlink = os.unlink

    def fail_owned_unlink(path, *args, **kwargs):
        if str(path).endswith(".tmp"):
            raise OSError("forced cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", fail_owned_unlink)
    with pytest.raises(stix_export.PublicationCleanupError, match="đã publish"):
        stix_export.publish_bytes(output, b"complete\n")
    assert output.read_bytes() == b"complete\n"


def test_publish_fsync_failure_cleans_only_owned_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output = tmp_path / "fsync.json"
    foreign = tmp_path / ".fsync.json.foreign.tmp"
    foreign.write_bytes(b"foreign")

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("forced fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="forced fsync failure"):
        stix_export.publish_bytes(output, b"complete\n")
    assert not output.exists()
    assert list(tmp_path.glob(".fsync.json.*.tmp")) == [foreign]


@pytest.mark.parametrize(
    ("draft_id", "timeout", "message"),
    [(True, 5.0, "draft_id"), (1, float("nan"), "timeout"), (1, -1.0, "timeout")],
)
def test_export_validates_scalar_inputs_before_config_or_database_io(
    tmp_path: Path, draft_id, timeout: float, message: str
):
    with pytest.raises((stix_export.StixExportError, store.DraftStoreError), match=message):
        stix_export.export_approved(
            db_path=tmp_path / "missing.sqlite",
            draft_id=draft_id,
            exporter_config_path=tmp_path / "missing-config.json",
            output_path=tmp_path / "bundle.json",
            timeout=timeout,
        )


def _validator(path: Path, *options: str) -> subprocess.CompletedProcess[str]:
    executable = Path(sys.executable).with_name("stix2_validator.exe")
    return subprocess.run(
        [str(executable), "--version", "2.1", "--enforce-refs", *options, str(path)],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )


def test_validator_332_must_refs_and_strict_except_only_103(tmp_path: Path):
    assert importlib.metadata.version("stix2-validator") == "3.3.2"
    db = tmp_path / "validator.sqlite"
    draft_id = approve_draft(db)
    artifact = stix_export.build_bundle(
        store.get_approved_export_snapshot(db, draft_id),
        stix_export.validate_exporter_config(exporter_config()),
    )
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_bytes(artifact.bytes)

    must_and_refs = _validator(bundle_path)
    strict_except_103 = _validator(bundle_path, "--strict", "--disable", "103")
    plain_strict = _validator(bundle_path, "--strict")

    assert must_and_refs.returncode == 0, must_and_refs.stdout + must_and_refs.stderr
    assert strict_except_103.returncode == 0, strict_except_103.stdout + strict_except_103.stderr
    assert plain_strict.returncode == 2
    strict_output = plain_strict.stdout + plain_strict.stderr
    check_lines = [line for line in strict_output.splitlines() if "{" in line]
    assert len(check_lines) == 3, strict_output
    assert all("{103}" in line for line in check_lines)


@pytest.mark.parametrize("corruption", ["schema", "marking", "reference"])
def test_validator_negative_artifacts_fail(tmp_path: Path, corruption: str):
    db = tmp_path / "validator-negative.sqlite"
    draft_id = approve_draft(db, values=("evil.example",))
    artifact = stix_export.build_bundle(
        store.get_approved_export_snapshot(db, draft_id),
        stix_export.validate_exporter_config(exporter_config()),
    )
    bundle = json.loads(artifact.bytes)
    if corruption == "schema":
        del bundle["objects"][-1]["name"]
    elif corruption == "marking":
        bundle["objects"][0]["definition"]["tlp"] = "blue"
    else:
        bundle["objects"][-1]["created_by_ref"] = "identity--bad-reference"
    path = tmp_path / f"invalid-{corruption}.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")

    result = _validator(path, "--strict", "--disable", "103")
    assert result.returncode == 2, result.stdout + result.stderr
