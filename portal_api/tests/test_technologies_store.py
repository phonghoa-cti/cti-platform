from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from portal_api import technologies


def _store(tmp_path):
    store = technologies.TechnologyStore(tmp_path / "technologies.sqlite", timeout=0.01)
    store.initialize()
    return store


def _counts(store):
    with sqlite3.connect(store.path) as connection:
        return (
            connection.execute("SELECT count(*) FROM technology_assets").fetchone()[0],
            connection.execute("SELECT count(*) FROM technology_asset_audit").fetchone()[0],
        )


def test_initialize_is_additive_idempotent_and_preserves_legacy_w04_rows(tmp_path):
    path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE assets(id INTEGER PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE asset_audit(id INTEGER PRIMARY KEY, action TEXT NOT NULL);
            INSERT INTO assets(value) VALUES('congty.vn');
            INSERT INTO asset_audit(action) VALUES('asset_created');
            """
        )
    store = technologies.TechnologyStore(path)

    store.initialize()
    store.initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM assets").fetchall() == [(1, "congty.vn")]
        assert connection.execute("SELECT * FROM asset_audit").fetchall() == [(1, "asset_created")]
        assert connection.execute("SELECT version FROM w04_technology_migrations").fetchall() == [(1,)]


def test_initialize_rejects_partial_wrong_schema_index_or_marker_without_repair(tmp_path):
    cases = {
        "partial": "CREATE TABLE technology_assets(id INTEGER PRIMARY KEY)",
        "wrong_schema": """
            CREATE TABLE technology_assets(id INTEGER PRIMARY KEY);
            CREATE TABLE technology_asset_audit(id INTEGER PRIMARY KEY);
            CREATE TABLE w04_technology_migrations(version INTEGER NOT NULL);
            INSERT INTO w04_technology_migrations VALUES(1);
            CREATE UNIQUE INDEX technology_assets_active_identity
              ON technology_assets(id) WHERE id > 0;
        """,
        "wrong_marker": """
            CREATE TABLE technology_assets(id INTEGER PRIMARY KEY);
            CREATE TABLE technology_asset_audit(id INTEGER PRIMARY KEY);
            CREATE TABLE w04_technology_migrations(version INTEGER NOT NULL);
            INSERT INTO w04_technology_migrations VALUES(2);
            CREATE UNIQUE INDEX technology_assets_active_identity
              ON technology_assets(id) WHERE id > 0;
        """,
    }
    for name, ddl in cases.items():
        path = tmp_path / f"{name}.sqlite"
        with sqlite3.connect(path) as connection:
            connection.executescript(ddl)
        before = path.read_bytes()

        with pytest.raises(technologies.TechnologiesUnavailable):
            technologies.TechnologyStore(path).initialize()

        assert path.read_bytes() == before


def test_initialize_rolls_back_all_technology_ddl_on_mid_migration_fault(tmp_path, monkeypatch):
    path = tmp_path / "fault.sqlite"
    store = technologies.TechnologyStore(path)

    def fail_midway(connection):
        connection.execute("CREATE TABLE technology_assets(id INTEGER PRIMARY KEY)")
        raise sqlite3.OperationalError("synthetic migration fault")

    monkeypatch.setattr(store, "_create_schema", fail_midway)

    with pytest.raises(technologies.TechnologiesUnavailable):
        store.initialize()

    with sqlite3.connect(path) as connection:
        names = connection.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'technology_%' "
            "OR name='w04_technology_migrations'"
        ).fetchall()
    assert names == []


@pytest.mark.parametrize("damage", ["index", "marker"])
def test_initialize_rejects_damaged_index_or_marker_without_repair(tmp_path, damage):
    store = _store(tmp_path)
    with sqlite3.connect(store.path) as connection:
        if damage == "index":
            connection.execute("DROP INDEX technology_assets_active_identity")
            connection.execute(
                "CREATE UNIQUE INDEX technology_assets_active_identity "
                "ON technology_assets(vendor_key,product_key,software_version)"
            )
        else:
            connection.execute("UPDATE w04_technology_migrations SET version=2")
    before = store.path.read_bytes()

    with pytest.raises(technologies.TechnologiesUnavailable):
        store.initialize()

    assert store.path.read_bytes() == before


def test_crud_normalizes_only_trim_and_vendor_product_casefold_and_audits(tmp_path):
    store = _store(tmp_path)

    created = store.create(" Fortinet ", " FortiOS ", " 7.2.1 ", "VPN gateway", "it-sub")
    assert created.vendor == "Fortinet"
    assert created.product == "FortiOS"
    assert created.software_version == "7.2.1"
    assert created.version == 1

    with pytest.raises(technologies.TechnologyExists):
        store.create("FORTINET", "fortios", "7.2.1", "duplicate", "it-sub")

    distinct_version = store.create("FORTINET", "fortios", "7.2.2", "other", "it-sub")
    distinct_unicode = store.create("Ｆortinet", "FortiOS", "7.2.1", "no NFKC", "it-sub")
    assert [item.id for item in store.list()] == [created.id, distinct_version.id, distinct_unicode.id]

    updated = store.update(created.id, " Fortinet ", " FortiOS ", " 7.2.1 ", "new", 1, "analyst-sub")
    assert updated.version == 2
    assert updated.note == "new"
    store.delete(created.id, 2, "admin-sub")
    recreated = store.create("fortinet", "fortios", "7.2.1", "recreated", "it-sub")
    assert recreated.id > created.id

    with sqlite3.connect(store.path) as connection:
        audits = connection.execute(
            "SELECT action,actor_subject,before_json,after_json FROM technology_asset_audit ORDER BY id"
        ).fetchall()
    assert [row[0] for row in audits] == [
        "technology_created",
        "technology_created",
        "technology_created",
        "technology_updated",
        "technology_deleted",
        "technology_created",
    ]
    assert audits[3][1] == "analyst-sub"
    assert json.loads(audits[3][2])["version"] == 1
    assert json.loads(audits[3][3])["version"] == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vendor", ""),
        ("vendor", " " * 3),
        ("vendor", "v" * 129),
        ("product", "p" * 257),
        ("software_version", "1" * 129),
        ("vendor", "bad\nname"),
        ("product", "bad\u200bname"),
        ("software_version", "bad\ud800version"),
    ],
)
def test_create_rejects_bounds_control_format_and_surrogate_without_writes(tmp_path, field, value):
    store = _store(tmp_path)
    data = {"vendor": "Fortinet", "product": "FortiOS", "software_version": "7.2.1"}
    data[field] = value

    with pytest.raises(technologies.InvalidTechnology):
        store.create(**data, note="", actor="it-sub")

    assert _counts(store) == (0, 0)


@pytest.mark.parametrize("actor", ["", "   ", "x" * 513])
def test_actor_bound_is_checked_before_row_or_audit(actor, tmp_path):
    store = _store(tmp_path)

    with pytest.raises(technologies.InvalidTechnology):
        store.create("Fortinet", "FortiOS", "7.2.1", "", actor)

    assert _counts(store) == (0, 0)


@pytest.mark.parametrize("value", [0, True, 1.0, "1", 2**53])
def test_ids_and_versions_are_strict_safe_positive_integers(value, tmp_path):
    store = _store(tmp_path)
    created = store.create("Fortinet", "FortiOS", "7.2.1", "", "it-sub")

    with pytest.raises(technologies.InvalidTechnology):
        store.update(value, "Fortinet", "FortiOS", "7.2.1", "", 1, "it-sub")
    with pytest.raises(technologies.InvalidTechnology):
        store.update(created.id, "Fortinet", "FortiOS", "7.2.1", "", value, "it-sub")

    assert _counts(store) == (1, 1)


def test_stale_duplicate_overflow_and_audit_fault_roll_back(tmp_path):
    store = _store(tmp_path)
    one = store.create("Fortinet", "FortiOS", "7.2.1", "one", "it-sub")
    store.create("Microsoft", "Exchange", "2019", "two", "it-sub")

    with pytest.raises(technologies.TechnologyConflict):
        store.update(one.id, "Fortinet", "FortiOS", "7.2.1", "stale", 2, "it-sub")
    with pytest.raises(technologies.TechnologyExists):
        store.update(one.id, "microsoft", "exchange", "2019", "dup", 1, "it-sub")

    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE technology_assets SET record_version=? WHERE id=?", (2**53 - 1, one.id))
    with pytest.raises(technologies.TechnologiesUnavailable):
        store.update(one.id, "Fortinet", "FortiOS", "7.2.1", "overflow", 2**53 - 1, "it-sub")

    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "CREATE TRIGGER technology_audit_fault BEFORE INSERT ON technology_asset_audit "
            "BEGIN SELECT RAISE(ABORT, 'audit fault'); END"
        )
    with pytest.raises(technologies.TechnologiesUnavailable):
        store.create("Cisco", "IOS XE", "17", "", "it-sub")

    assert [item.note for item in store.list()] == ["one", "two"]
    assert _counts(store) == (2, 2)


def test_read_rejects_corrupt_row_or_key_and_over_limit_instead_of_partial_data(tmp_path):
    store = _store(tmp_path)
    item = store.create("Fortinet", "FortiOS", "7.2.1", "", "it-sub")
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE technology_assets SET vendor_key='wrong' WHERE id=?", (item.id,))
    with pytest.raises(technologies.TechnologiesUnavailable):
        store.list()

    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE technology_assets SET vendor_key='fortinet' WHERE id=?", (item.id,))
        row = connection.execute(
            "SELECT vendor,vendor_key,product,product_key,software_version,note,"
            "record_version,created_by,created_at,updated_at "
            "FROM technology_assets WHERE id=?",
            (item.id,),
        ).fetchone()
        rows = []
        for index in range(1000):
            values = list(row)
            values[4] = f"version-{index}"
            rows.append(tuple(values))
        connection.executemany(
            "INSERT INTO technology_assets(vendor,vendor_key,product,product_key,"
            "software_version,note,record_version,created_by,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
    with pytest.raises(technologies.TechnologiesUnavailable):
        store.list()


def test_true_identity_duplicate_is_distinct_from_other_unique_constraint(tmp_path):
    store = _store(tmp_path)
    store.create("Fortinet", "FortiOS", "7.2.1", "", "it-sub")
    with pytest.raises(technologies.TechnologyExists):
        store.create("FORTINET", "fortios", "7.2.1", "", "it-sub")

    with sqlite3.connect(store.path) as connection:
        connection.execute("CREATE UNIQUE INDEX technology_note_unique ON technology_assets(note)")
    with pytest.raises(technologies.TechnologiesUnavailable):
        store.create("Microsoft", "Exchange", "2019", "", "it-sub")

    assert _counts(store) == (1, 1)


def test_failure_paths_close_connection_and_release_write_lock(tmp_path):
    store = _store(tmp_path)
    item = store.create("Fortinet", "FortiOS", "7.2.1", "", "it-sub")
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE technology_assets SET record_version=0 WHERE id=?", (item.id,))

    with pytest.raises(technologies.TechnologiesUnavailable):
        store.list()

    with sqlite3.connect(store.path, timeout=0) as connection:
        connection.execute("BEGIN EXCLUSIVE")
        connection.rollback()


def test_active_limit_rejects_1001st_create_without_row_or_audit(tmp_path):
    store = _store(tmp_path)
    now = "2026-11-11T16:00:00Z"
    with sqlite3.connect(store.path) as connection:
        connection.executemany(
            "INSERT INTO technology_assets(vendor,vendor_key,product,product_key,"
            "software_version,note,record_version,created_by,created_at,updated_at) "
            "VALUES('Vendor','vendor','Product','product',?,'',1,'it-sub',?,?)",
            [(str(index), now, now) for index in range(1000)],
        )

    with pytest.raises(technologies.TechnologiesUnavailable):
        store.create("Other", "Product", "1", "", "it-sub")

    assert _counts(store) == (1000, 0)


def test_two_writers_with_same_version_cannot_lose_an_update(tmp_path):
    store = technologies.TechnologyStore(tmp_path / "race.sqlite", timeout=1)
    store.initialize()
    item = store.create("Fortinet", "FortiOS", "7.2.1", "", "it-sub")

    def update(note):
        try:
            return store.update(
                item.id,
                "Fortinet",
                "FortiOS",
                "7.2.1",
                note,
                1,
                "it-sub",
            )
        except technologies.TechnologyConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(update, ("writer-a", "writer-b")))

    assert sum(isinstance(result, technologies.Technology) for result in results) == 1
    assert sum(isinstance(result, technologies.TechnologyConflict) for result in results) == 1
    assert store.list()[0].version == 2
    assert _counts(store) == (1, 2)
