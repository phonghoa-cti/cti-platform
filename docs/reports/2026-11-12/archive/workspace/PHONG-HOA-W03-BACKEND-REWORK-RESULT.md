# W03 backend rework B1/B2 — DONE

## Git boundary

- Candidate: `a49486caf39942019259e41514457bdb85498347`
- HEAD: `abcd14dacca361791b17719632d2ce38557d6baf`
- Commit: `fix: harden W03 read-only boundaries`
- Branch: `feat/w03-read-backend-20261112`
- Tree after commit: clean (`git status --porcelain` returned no output)
- Delta: 4 allowed files, 219 insertions, 9 deletions

Files changed:

- `portal_api/cves.py`
- `portal_api/tests/test_cves_api.py`
- `docs/specs/W03-read-local-contract.md`
- `docs/PROGRESS.md`

## B1 result

`ReadOnlyTechnologyStore.list()` now opens SQLite only with URI `mode=ro`, starts one deferred read
transaction, validates the W04 schema/index/migration marker, and performs a bounded active-row SELECT on
that same connection and snapshot. It validates every returned row, rejects more than 1,000 active rows,
and rolls the read transaction back. It does not initialize, migrate, seed or use `BEGIN IMMEDIATE`.

Test-first RED covered missing audit table, missing marker, missing index, wrong marker version and wrong
marker schema independently. GREEN also covers valid 200, missing database 503/no-create, and a trace proving
one connection with `BEGIN -> schema checks -> bounded SELECT -> ROLLBACK`.

SQL snapshots compare ordered `sqlite_master`, all rows from existing asset/audit/marker tables, and
`PRAGMA user_version`. They remain equal before/after success 200, dependency failures 404 and stale-cursor
409, and every partial-schema 503 failure.

## B2 result

Advisory URL validation catches `ValueError` from parsing hostname/port and rejects absent hostname,
credentials, authority whitespace, backslash, percent escapes, nonnumeric/out-of-range ports and malformed
bracketed IPv6. Valid HTTPS hostname, explicit port and bracketed IPv6 remain accepted. Validation is syntax-only:
no DNS resolution, live request or SSRF probe occurs.

## RED to GREEN and verification

| Check | Exit | Result |
|---|---:|---|
| Focused W03 RED | 1 | 12 failed, 47 passed |
| Original external probe RED | 1 | 3 failed |
| Focused W03 GREEN/final | 0 | 59 passed in 2.43s |
| Original external probe GREEN | 0 | 3 passed in 0.76s |
| SQL/no-create focused proof | 0 | 8 passed in 0.94s |
| Ruff check | 0 | all checks passed |
| Ruff format check | 0 | 2 files already formatted |
| `git diff --check` | 0 | no diff errors |

The external probe SHA-256 was unchanged before/after:
`D17F27A8E50CE9AF17D343BE3B7A4FD229E925B34FB3BBCA7D74E5E6476DDD20`.

The entire 345-test portal suite was intentionally not run because the B1/B2 brief explicitly said not to
run it when shared code was unchanged. No app/auth/technology implementation or external probe was edited.

## Evidence

Raw command summaries, RED/GREEN, final checks, probe hash and SQL non-mutation details:

`$WORKSPACE\w03-backend-rework-evidence\`

## Evidence limits

Verified only at local component/API-test level with synthetic fixtures. Gateway, frontend/browser, real feed,
OpenCTI, Cloudflare/JWKS/HTTPS, lab and production remain **UNVERIFIED**. No push, PR, merge or deploy occurred.
