# X01-INGEST-QUEUE-NEXT — brief triển khai Sol medium

## Mục tiêu và phạm vi

Tạo một CLI local/offline nhập **một envelope đã có** từ X01 local ingest vào hàng chờ review W05, đồng thời lưu provenance envelope trong cùng SQLite transaction. Không làm lại TXT/PDF parser, không gọi model/mạng/OpenCTI, không tạo HTTP/listener/UI và không tự approve/export.

## Base bắt buộc

- Source W05 chỉ đọc: `$WORKSPACE\cti-x01-w05-stix-e2e` HEAD `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Target phải tạo: `$WORKSPACE\cti-x01-ingest-queue`; branch `feat/x01-ingest-queue-20261111`, base đúng SHA trên.
- Trước/sau: `git rev-parse HEAD`, `git status --short`; nếu base/status khác thì dừng và báo, không checkout/reset source khác.
- Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-draft-offline-contract.md`, `extractor/phonghoa_extractor/store.py`, `extractor/draft/store.py`, tests store/queue/CLI trước code.
- Producer chỉ đọc: `$WORKSPACE\cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`, nhất là `extractor/ingest/run.py` và `extractor/phonghoa_extractor/local_ingest.py`. Không import runtime hoặc cherry-pick toàn branch này.

## Quyết định phải giữ

1. Tạo `extractor/phonghoa_extractor/ingest_queue.py` cho parse/validate envelope và save atomic; tạo `extractor/ingest_queue/run.py` cho CLI `import`.
2. Nâng `STORE_SCHEMA_VERSION` từ 2 lên 3 trong `store.py`, bằng migration additive và bảng provenance 1:1. Không đổi schema payload draft `"1.0"`.
3. `save_ingested_envelope()` gọi validator W05 hiện có (`_validate_draft`) và không sửa `draft`, `items.keep`, evidence, text hay findings.
4. CLI/library bắt buộc creator: `--created-by-subject <opaque-subject>` / keyword-only `created_by_subject: str`. Tái dùng `_validate_subject`; không nhận identity từ envelope, không bịa subject và không nới policy self-approve.
5. Không ghi output/sidecar. stdout thành công đúng một JSON: `{"draft_id":N,"result":"imported"}` hoặc `{"draft_id":N,"result":"duplicate"}`. stderr lỗi chỉ code/nhãn an toàn, không raw CTI/path tuyệt đối.

## Hợp đồng CLI và envelope

```powershell
.\.venv\Scripts\python.exe extractor\ingest_queue\run.py import `
  --envelope <envelope.json> --db <drafts.sqlite> `
  --created-by-subject <opaque-subject> [--timeout 5]
```

- Argument lỗi/`--help`: exit 2/0. Thành công/duplicate: exit 0. Mọi mã lỗi đóng sau đây exit 1, stderr đúng `Lỗi: <code>`: `invalid_created_by_subject`, `envelope_read_failed`, `envelope_too_large`, `invalid_utf8`, `invalid_json`, `duplicate_json_key`, `json_too_deep`, `invalid_envelope`, `invalid_input_metadata`, `invalid_provenance`, `invalid_draft`, `database_invalid`, `database_locked`, `duplicate_creator_conflict`, `write_failed`.
- `timeout`: int/float hữu hạn, không bool, `>=0`; tái dùng semantics timeout W05.
- Envelope file phải local regular, không UNC, symlink hoặc Windows reparse point ở file/ancestor, tối đa 16 MiB; đọc bytes một lần. Chỉ dùng path CLI, không bao giờ dùng path lồng trong payload.
- Decode strict UTF-8 JSON: reject duplicate key ở mọi object, `NaN/Infinity/-Infinity`, non-object root, depth >64; root dict depth 1, mỗi dict/list tăng 1, scalar không tăng. Validate type/keys của parent trước khi đọc child. Chuỗi phải encode `utf-8`, `strict`; escaped surrogate trả `invalid_utf8`, không traceback. Dùng `json.loads(..., object_pairs_hook=..., parse_constant=...)`; serialize canonical `ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False`.
- Exact root keys: `schema_version`, `input`, `draft`; schema chính xác `x01-local-ingest/1.0`.
- Gọi `_validate_draft(envelope["draft"])`. Payload draft phải được lưu nguyên vẹn.

`input` exact keys và checks:

| Key | Contract |
|---|---|
| format | exact `text`/`pdf`. |
| display_name | non-empty str UTF-8; không control, slash/backslash; bằng `draft.source.name`. |
| raw_sha256 | lowercase SHA-256 syntax; chỉ provenance self-declared. |
| raw_bytes | true int, 0..`8*1024*1024`; TXT phải bằng `len(draft.text.encode("utf-8", "strict"))`. |
| canonical_text_sha256 | lowercase SHA-256; bằng `draft.source.sha256`. `_validate_draft` còn chứng minh nó khớp `draft.text` UTF-8. |
| page_count/page_text_ranges | `draft.text` là UTF-8 strict, ≤1.000.000 code point. Text: cả hai null, `raw_sha256 == canonical_text_sha256`, không normalize newline/BOM. PDF: true int 1..50, list đúng count `[start,end]`; true int bounded, mỗi page ≤100.000 code point, ít nhất một page `strip()` không rỗng; first start 0, last end `len(text)`, separator giữa range kề nhau đúng `\n\f\n`. |

Thứ tự lỗi: args/timeout → safe read/cap → JSON decode → root/schema → input shape/bounds → input↔draft invariants → W05 draft validation → DB/path/schema/lock → duplicate/write. Viết test theo thứ tự này để tránh leak hoặc nondeterminism.

## Store v3 và migration

Thêm bảng sau trong `store.py` (tên/semantics giữ đúng):

```sql
CREATE TABLE draft_ingest_provenance (
  draft_id INTEGER PRIMARY KEY REFERENCES drafts(id),
  envelope_schema_version TEXT NOT NULL,
  envelope_sha256 TEXT NOT NULL UNIQUE,
  input_format TEXT NOT NULL CHECK (input_format IN ('text','pdf')),
  display_name TEXT NOT NULL,
  raw_sha256 TEXT NOT NULL,
  raw_bytes INTEGER NOT NULL,
  canonical_text_sha256 TEXT NOT NULL,
  page_count INTEGER,
  page_text_ranges_json TEXT
)
```

- Add an explicit `_validate_v2_schema`/mode, then current v3 structural validator (column/type/nullability, exact PK/FK and full UNIQUE key `envelope_sha256`; each provenance row must join one valid draft and match canonical fields). Old v2 drafts have no provenance and remain valid.
- Existing migration 0/1→2 is one transaction; preserve it. Add 2→3 within its own migration transaction: `BEGIN IMMEDIATE`, validate v2, create table, validate v3, set `PRAGMA user_version=3`, commit. No nested `BEGIN`. v3 rerun validates only; future/hỏng schema reject.
- Import flow is two phases: validate envelope+creator before DB; run migration transaction; then a **separate** `BEGIN IMMEDIATE` for draft+provenance. Re-read version and validate v3 while this second writer lock is held. If migration commits but later insert/commit fails, v3 schema may remain but there must be no orphan draft/provenance.
- New binary readers never migrate/write: legacy get/list retain 0/1 behavior; v2 and v3 get/list/selection/review/export retain their respective v2 semantics; unsupported/future rejects. The old v2 binary can reject v3; no downgrade.
- Create an internal/publicly tested read helper only if required for provenance assertion. It must be `mode=ro`, no migrate/write, validate row and not expose raw text in CLI summary.

## Atomic write/idempotency

Implement frozen DTO `IngestProvenance(draft_id, envelope_schema_version, envelope_sha256, input_format, display_name, raw_sha256, raw_bytes, canonical_text_sha256, page_count, page_text_ranges)` and `IngestQueueResult(draft_id: int, result: Literal["imported", "duplicate"])`. Add exact read helper (mode=ro, no migration/write):

```python
get_ingest_provenance(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> IngestProvenance
```

Create `IngestEnvelopeError(DraftInputError)` carrying one closed envelope code. Retain `DraftInputError` for creator/timeout, `DraftConflictError` for other-creator duplicate, `DraftNotFoundError` and `DraftSQLiteError`; only CLI maps them to the finite stderr code set. Then implement:

```python
save_ingested_envelope(db_path: str | Path, envelope: Mapping[str, Any], *, created_by_subject: str, timeout: float = 5.0) -> IngestQueueResult
```

Compute `envelope_sha256` from **validated canonical envelope JSON**, not original formatting. It is the dedupe identity only; it is not an authenticity signature.

Flow:

1. Validate all data before DB open.
2. Require existing regular local DB path; reject missing DB, envelope/DB samefile/equivalent/reparse/UNC aliases. Use parameterized SQL.
3. Open writer and run separate migration transaction as above. Then begin a fresh `BEGIN IMMEDIATE`, re-read version/schema under the lock.
4. Look up provenance joined to draft by `envelope_sha256`; validate linkage/hash. Same creator returns duplicate with no mutation. Different creator returns `duplicate_creator_conflict`, with no draft disclosure or owner change.
5. Else INSERT pending `drafts` row exactly like `save_draft` with `created_by_subject`, then matching provenance row, then one commit. Rollback every exception in this write transaction.

Use a test hook equivalent to `_commit` only when necessary to prove failed provenance insert/commit rollback; do not leave test-only production behavior exposed through CLI. A lost response after successful commit is resolved by retry→duplicate. Do not claim exactly-once. Do not merge on raw hash alone and never alter a previous draft on duplicate.

## TDD tests and acceptance matrix

Write tests RED first, then implementation. At minimum:

| Test group | Cases |
|---|---|
| Valid contract | TXT Unicode/emoji and PDF multi-page envelope; creator subject; persisted payload byte/semantic equality, source/canonical/raw hashes, range JSON and `draft_id` link. |
| Invalid envelope | unknown/missing key, duplicate key, nonfinite, malformed UTF-8/surrogate, deep nesting, >16 MiB, bool-as-int, bad bounds/name/hash, producer text/PDF cap/range/separator mismatch, canonical/text mismatch. |
| Immutability | draft `items.keep`, span/evidence/findings unchanged after import; no payload rewrite. |
| Atomicity | injected provenance insert failure and commit failure rollback; no orphan draft or provenance. |
| Duplicate/concurrency | same semantic JSON + creator returns duplicate; same envelope different creator conflict; distinct draft/raw fields do not merge; two subprocesses race, at most one import/provenance, other duplicate or bounded lock failure. |
| Migration | v2→v3, repeated migration, 0/1 current chain, hỏng/future schema; rollback migration; failed insert/commit after successful migration; v2/v3 reader calls do not migrate/write. |
| Regression | `get/list`, selection/review v2, approval with reviewer different creator, STIX export and legacy draft/store CLI work after v3 migration. |
| CLI process demo | import fixture envelope to temp DB then list/get/provenance assertion; stdout exact and no network/listener/browser. |

Run only after writing tests, using `$WORKSPACE\cti-x01-ingest-queue\.venv\Scripts\python.exe` (Python 3.12.13). Record each command, fresh exit code and count in result. Suggested final gates (all named regression files exist in base):

```powershell
.\.venv\Scripts\python.exe -m pytest extractor/tests/test_ingest_queue.py extractor/tests/test_ingest_queue_cli.py -q
.\.venv\Scripts\python.exe -m pytest extractor/tests/test_store.py extractor/tests/test_store_cli.py extractor/tests/test_queue.py extractor/tests/test_queue_cli.py extractor/tests/test_draft_cli.py extractor/tests/test_review.py extractor/tests/test_selection.py -q
.\.venv\Scripts\python.exe -m pytest extractor/tests/test_stix_export.py extractor/tests/test_stix_export_cli.py -q
.\.venv\Scripts\python.exe -m ruff check extractor
.\.venv\Scripts\python.exe -m ruff format --check extractor
git diff --check
```

Do not represent an unrun full suite as run.

## Documentation and handoff

Allowlist thay đổi: `extractor/phonghoa_extractor/store.py`; mới `extractor/phonghoa_extractor/ingest_queue.py`, `extractor/ingest_queue/run.py`, `extractor/tests/test_ingest_queue.py`, `extractor/tests/test_ingest_queue_cli.py`; các regression đã nêu; `docs/specs/W05-draft-offline-contract.md`; ADR mới `docs/adr/00xx-x01-ingest-envelope-provenance.md`; `docs/PROGRESS.md`; `extractor/draft/README.md` nếu cần lệnh sử dụng. Không sửa file khác. Update contract với schema v3/importer/provenance/creator/duplicate semantics. State raw SHA PDF là provenance tự khai, không verified byte; integrity checks chỉ phát hiện bất nhất nội bộ, envelope sửa và tính lại hash nhất quán là input mới. Report chính xác `PHONG-HOA-X01-INGEST-QUEUE-RESULT.md`; evidence `x01-ingest-queue-evidence/` có manifest, commands/exit/count/demo, source before/after, exact commit/diff và ownership cleanup. Chỉ fixture/DB/envelope tổng hợp, không raw dữ liệu thật/secret. Commit local chỉ sau gates PASS; không push/PR/merge/deploy.

Done means: exact base and clean source recorded; migration and transaction behavior are covered by fresh tests; demo proves only local envelope→queue→read/provenance; report separately API/browser/OpenCTI/lab/production as UNVERIFIED.
