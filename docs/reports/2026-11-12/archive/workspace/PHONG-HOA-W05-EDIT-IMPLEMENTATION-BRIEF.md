# W05-EDIT — brief Backend: lõi/store selection snapshot

## Mục tiêu, base và giới hạn

**Owner giao:** CTI Backend (Sol medium). Tạo tree mới đề xuất `cti-w05-selection`, branch `feat/w05-selection-local-20261111`, base chính xác `d94afb1e24929f64f82a921cd29307be175fb04e`. Kiểm HEAD/status trước khi sửa, không reset/đụng tree nguồn.

Làm core SQLite offline để Analyst/Admin lưu tập IOC hợp lệ được giữ/bỏ, audit mọi save có hiệu lực, và approve đúng snapshot; giữ evidence/payload bất biến. **Không làm:** HTTP/API/UI/parser TypeScript, CLI, OpenCTI, model, secret, service/listener, lab, push/PR/merge/deploy, human-added IOC hay redesign workflow.

## File được phép sửa

* `extractor/phonghoa_extractor/store.py`
* `extractor/tests/test_review.py` (thêm/sửa test store)
* `extractor/tests/test_queue.py` và `extractor/tests/test_store_cli.py` chỉ khi assertion review version hiện có phải phản ánh semantic mới.

Không sửa `portal_api/**`, `portal/web/**`, `docs/**`, RUNS hay report nghiên cứu trong implementation task.

## Contract lõi

Thêm dataclass frozen:

```python
@dataclass(frozen=True)
class DraftSelectionResult:
    draft_id: int
    review_version: int
    selection_version: int
    selected_indices: tuple[int, ...]
    selected_sha256: str
    saved_by_subject: str | None   # None chỉ với baseline version 0
    saved_at: str | None
    changed: bool

def get_effective_selection(db_path, draft_id, *, timeout: float = 5.0) -> DraftSelectionResult: ...
def save_selection(db_path, draft_id, *, actor: Actor,
                   selected_indices: Sequence[int], expected_version: int,
                   timeout: float = 5.0) -> DraftSelectionResult: ...
```

`get_effective_selection` là read-only (`mode=ro`), không migrate/không tạo DB; legacy/v1 DB trả lỗi rõ rằng cần migrate v2, thay vì suy đoán. `save_selection` không nhận trust flag, item JSON hay text. Normalize only after strict type validation: sequence phải `list|tuple` (không string), mỗi index `int` không bool, unique; sort ascending; canonical JSON `json.dumps(indices, separators=(",", ":"))`; SHA-256 UTF-8. Dùng `DraftInputError`, `DraftPolicyError`, `DraftConflictError`, `DraftNotFoundError`, `DraftSQLiteError` hiện có, không tạo mã HTTP.

Eligibility (`_eligible_ioc_indices(payload)`) yêu cầu đã `_validate_draft(payload)`, rồi đúng `kind == 'ioc'`, `keep is True`, `status == 'ok'`; item index zero-based. `selected_indices` phải là subset exact của eligible. Empty save hợp lệ; `approve` empty raise `DraftPolicyError`. No-op trả `changed=False`, không update/insert/audit/version. `DraftReviewResult.version` vẫn là review version mới và có thể >1.

## Schema/migration v2

1. Đổi `STORE_SCHEMA_VERSION` 1→2. Mở rộng allowed/current columns và schema validators; `drafts.selection_version INTEGER NOT NULL DEFAULT 0 CHECK (selection_version >= 0)`.
2. Tạo `draft_selection_audit` exactly như nghiên cứu: FK `draft_id REFERENCES drafts(id)`, `UNIQUE(draft_id, selection_version)`, `UNIQUE(draft_id, review_version)`, action check `save_selection`, hash 64 lower hex, JSON canonical checked in Python, và index `(draft_id, selection_version DESC)`.
3. `draft_audit` **giữ `draft_id UNIQUE`** và action approve/reject. Add nullable `selection_version`, `selected_indices_json`, `selected_sha256`; v2 validator chấp nhận old final records chỉ khi cả 3 NULL, record approve mới chỉ khi cả 3 present/valid/canonical and selection version >=0. Reject mới để cả ba NULL.
4. Migration V1→V2 trong một `BEGIN IMMEDIATE`: `ALTER TABLE drafts ADD`, create table/index, add audit columns, validate V2, `PRAGMA user_version=2`, commit. Thất bại rollback. V2 rerun idempotent; V0/unknown/corrupt/mixed schema fail closed except an explicit retained V0→V1→V2 route implemented/tested atomically. Do not use `writable_schema`.
5. All write connections run `PRAGMA foreign_keys=ON` before `BEGIN`; all reads remain `mode=ro`; verify physical schema with `PRAGMA table_info`, `index_list/index_xinfo`, `foreign_key_list` plus SQL checks, as current code does.

## Thay đổi `decide_draft`

Inside current `BEGIN IMMEDIATE`, before terminal update: decode/validate current payload, require expected `review_version`, derive effective selection from newest selection event or immutable baseline. For `approve`, retain existing role/creator/unsupported-kind checks **and** require non-empty selection and each referenced index still eligible. Update terminal row `WHERE id=? AND review_status='pending' AND review_version=?`; insert `draft_audit` immediately after with exact `selection_version`, canonical JSON and hash for approve. Any event/audit/commit failure rolls all changes back.

For reject, preserve existing reason policy and emit current final audit with selection fields null. After either terminal decision, `save_selection` must conflict. Do not change `payload_json`, `source_sha256`, `status`, evidence/span/text or creator.

## Acceptance matrix (24 checks)

| # | Scenario | Expected |
|---:|---|---|
| 1 | migrate V1 current DB | v2 schema/index/FK/check/user_version=2, data preserved |
| 2 | migrate V2 again | no change/idempotent |
| 3 | corrupt/unknown/future/mixed schema | fail closed, no partial mutation |
| 4 | read legacy/v1 | no migration/write; explicit error where v2 required |
| 5 | baseline selection | exactly eligible `ioc,keep,ok`, version 0 |
| 6 | valid deselect/reselect | canonical sorted snapshot, version increments, event actor/time/hash |
| 7 | empty selection save | allowed/audited; subsequent approve denied |
| 8 | duplicate/unknown/negative/bool/string/float/out-of-range index | input/policy error, zero DB change |
| 9 | `allowlist`, `bia`, keep=false, non-IOC submitted | denied, cannot revive policy-excluded item |
| 10 | no-op same set | `changed=False`, no new row/version |
| 11 | caller wrong role/bad subject | denied, no change |
| 12 | creator modifies selection | allowed by current policy; creator approve still denied |
| 13 | approval with saved selection | `draft_audit` exact snapshot/hash/version, terminal result version correct |
| 14 | approval baseline selection | audit contains canonical baseline snapshot |
| 15 | self approve/legacy creator null/unsupported kept kind | existing denial remains |
| 16 | reject path | reason required; selection audit untouched; final audit selection fields null |
| 17 | stale save vs save | exactly one wins; loser conflict, one event |
| 18 | save vs approve race | exactly one wins; winner snapshot/version coherent |
| 19 | save/decision on terminal | conflict and no new audit/event |
| 20 | injected event INSERT failure | draft version and event rollback |
| 21 | injected final audit INSERT/commit failure | terminal update and audit rollback |
| 22 | FK enforcement | orphan selection event rejected on write connection |
| 23 | payload/source/evidence unchanged | byte-identical stored payload/source hash before/after edits/decision |
| 24 | existing W05 store/queue review regressions | update only expected version assumptions; no HTTP/UI suite required |

## TDD và kiểm chứng bàn giao

Viết test fail trước cho #5–#10, #13–#21, sau đó migration #1–#4/#22/#23, cuối cùng regression #24. Dùng DB tạm trong pytest và controlled commit/event failure seam giống `test_review.py`; không tạo DB/lab persistent. Chạy riêng `pytest extractor/tests/test_review.py extractor/tests/test_queue.py extractor/tests/test_store_cli.py` và các test store liên quan theo lệnh repo, ghi exit code/số test thực tế. Không gọi test này “đã chạy” trước khi worker có output.

Demo SQLite tổng hợp sau test: một draft có hai eligible IOC và một excluded; save `[1]`, đọc effective shows version/hash; approve với expected version mới; query `draft_selection_audit` và `draft_audit` cho thấy cùng snapshot/hash; query payload/source hash chứng minh bất biến. Demo là local/offline, không phải API/UI/OpenCTI.

## Bàn giao bắt buộc

Trả exact commit/SHA, `git status`, file diff, lệnh + exit code + count test, bảng PASS/FAIL/UNVERIFIED cho 24 tiêu chí, output demo đã che dữ liệu nhạy cảm, và phần không kiểm (HTTP/UI/auth production/OpenCTI/lab/performance). Không tự mở rộng contract parser: API/UI follow-up phải thay strict `Literal[0|1]` sang integer và thêm selection object có version riêng, sau khi Leader review.
