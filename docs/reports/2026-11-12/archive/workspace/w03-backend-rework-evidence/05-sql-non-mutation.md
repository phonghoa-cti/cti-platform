# SQL non-mutation evidence

Tests compare SQL state, not only database bytes or WAL files. Snapshot fields are:

- ordered `sqlite_master` rows (schema and indexes);
- every row in technology assets, audit and migration marker tables that exists;
- `PRAGMA user_version`.

Verified paths:

- valid read returns 200 without state change;
- missing path returns 503 and does not create a database;
- missing asset after dependency read returns 404 without state change;
- stale cursor after dependency read returns 409 without state change;
- each partial/invalid schema returns 503 without changing its already-defective state.

The trace test additionally observes exactly one connection, `BEGIN` before schema inspection,
schema inspection before `SELECT ... LIMIT 1001`, and final `ROLLBACK`. The implementation never
calls initialize, migrate, seed or `BEGIN IMMEDIATE`.
