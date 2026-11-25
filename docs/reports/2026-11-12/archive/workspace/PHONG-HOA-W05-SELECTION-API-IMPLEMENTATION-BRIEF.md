# W05 Selection API — brief triển khai Backend

## Mục tiêu và giới hạn

Triển khai HTTP v1 cho đọc/lưu lựa chọn IOC hiệu lực và quyết định đúng version trên core đã nghiệm thu. Đây là lát cắt Backend in-process; không UI, browser/harness, listener, dependency mới, auth mới, migration mới, OpenCTI, cloud/lab, push/PR/merge/deploy.

**Tree được phép tạo (chưa tạo trong brief):** `$WORKSPACE\cti-w05-selection-api`
**Branch:** `feat/w05-selection-api-20261111`
**Base bắt buộc:** `b9c35bb45cbf1000c1324ba46f1f162e0c02be44` (`cti-w05-selection`). Kiểm path/HEAD/status trước tạo; không reset/ghi đè tree khác.

Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-duyet.md`, `W05-draft-offline-contract.md`, `api-portal.md`, `PHONG-HOA-W05-SELECTION-API-RESEARCH.md`, và quyết định Leader `PHONG-HOA-W05-EDIT-LEADER-PLAN.md` trước sửa. Lát cắt này không làm lại JWT/gateway/LLM research.

## Quyết định triển khai

1. Giữ `/api/drafts` legacy không đổi. Thêm v1 dưới `/api/v1/drafts`; lý do: parser TypeScript cũ exact và khóa version 0/1.
2. Core thêm hai helper read nhỏ: `get_draft_with_selection(db_path, draft_id, *, timeout=5.0)` và `list_drafts_with_selection_version(db_path, *, limit, before_id, timeout=5.0)`. Helper detail mở DB `mode=ro`, yêu cầu schema v2, validate schema, `BEGIN`, đọc một draft rồi `_load_effective_selection` qua **cùng connection**, trả payload/review/selection. Helper list giữ query pending/cursor của list cũ nhưng trả summary với selection_version; không thêm selected/count để tránh N composite snapshots. Không SQL selection ở `portal_api/service.py`; không đổi shape legacy `get_draft`/`list_drafts`.
3. `GET v1 detail` chỉ dùng helper này. `POST selection` trả trực tiếp result đã `save_selection` commit; `POST decision` trả result `decide_draft` và snapshot quyết định được lõi xác thực/copy từ cùng transaction (thêm một core result field/helper nhỏ chỉ nếu cần; không reread sau commit).
4. Public JSON integer `<= 9007199254740991` (`JSON_SAFE_INTEGER`), dù SQLite lớn hơn. Strict int, no bool/coercion, `extra=forbid`.

## File scope

Được sửa/thêm:

- `extractor/phonghoa_extractor/store.py` — hai helper read v2, snapshot nhất quán detail và tối thiểu result cần thiết cho response decision.
- `extractor/tests/test_selection.py` (hoặc test selection mới gần nhất) — interleaving deterministic/helper/error contract lõi.
- `portal_api/schemas.py` — v1 strict DTO, safe-integer validator/constants.
- `portal_api/service.py` — adapter mỏng gọi core đúng một lần, translate error hiện có.
- `portal_api/app.py` — route v1, validate path/query/body/Origin/content-type, no-store/Vary.
- `portal_api/tests/test_w05_api.py` — test in-process JWT/JWKS/SQLite tổng hợp cho v1 và regression legacy.
- `docs/specs/api-portal.md`, `docs/specs/W05-draft-offline-contract.md`, `docs/PROGRESS.md` — ghi contract/compatibility/trạng thái thật.

Không sửa `portal/web/**`, auth/settings (trừ khi import/route typing bắt buộc và không thay security semantics), dependency/lock, test harness, CLI, core IOC/AI, RUNS, báo cáo Leader hay tree nguồn.

## Schema exact

Tạo `ExactModel` strict/forbid như đang có. Các integer public dùng `StrictInt`, `ge=0` (ID `ge=1`) và `le=JSON_SAFE_INTEGER`. `selected_indices` max length phải ràng buộc bởi limit hợp lý đã cấu hình, sau đó core kiểm subset eligible; reject duplicate bằng validator trước call store. `selected_sha256` pattern lowercase 64 hex.

```python
class SelectionSaveRequest(ExactModel):
    expected_version: SafeNonNegativeInt
    selected_indices: list[SafeNonNegativeInt]
    # validator: unique; no bool by StrictInt

class SelectionView(ExactModel):
    review_version: SafeNonNegativeInt
    selection_version: SafeNonNegativeInt
    selected_indices: list[SafeNonNegativeInt]
    selected_sha256: str
    saved_by_subject: str | None
    saved_at: str | None
    changed: bool
    ai_extracted_count: SafeNonNegativeInt
    ai_eligible_count: SafeNonNegativeInt
    human_deselected_count: SafeNonNegativeInt
    selection_save_count: SafeNonNegativeInt
```

`DraftDetailV1` is the stored 1.0 fields + strict `ReviewV1` + `selection: SelectionView`; `ReviewV1.version` no longer max 1. `DraftSummaryV1` is old summary plus `selection_version`; it must not pretend counts are snapshot-consistent. `DecisionResponseV1` has `draft_id,status,version,decided_by_subject,decided_at,reason,selection_version,selected_indices,selected_sha256` and accepts result version >1.

## Routes and exact behavior

| Method/path | Request | 200 response | Core call |
|---|---|---|---|
| `GET /api/v1/drafts` | `limit` 1–100, optional safe positive `before_id`; no unknown/repeated query keys | `{"items":[SummaryV1],"next_before_id":int|null}` | new v2-only list helper, then validate v1 summary; preserve pending-only behavior |
| `GET /api/v1/drafts/{id}` | safe positive path | `DraftDetailV1` | `get_draft_with_selection` once |
| `POST /api/v1/drafts/{id}/selection` | `{"expected_version":2,"selected_indices":[0]}` | `SelectionView` | `save_selection` once with trusted `Actor` |
| `POST /api/v1/drafts/{id}/decision` | current exact approve/reject body, safe expected version | `DecisionResponseV1` | `decide_draft` once; no post-commit race reread |

All v1 calls require current verified `Principal` role `analyst|admin`; never accept identity/role in body/query/header. Both POSTs require exact same-origin and existing strict JSON content type; GET does not. Maintain error envelope and mapping: 401 auth, 403 role/Origin/policy, 404 missing draft, 409 stale/terminal/race/ceiling, 415 content type, 422 malformed/types/extra/unsafe number, 503 unavailable/corrupt/unmigrated/output-contract failure. `Cache-Control: no-store` and `Vary: Cf-Access-Jwt-Assertion` on both success and errors under `/api/v1/drafts`.

## Version and safety invariants

- `items.keep`, text/evidence/source/payload never change. Effective selection is only indices from eligible `ioc + keep=true + status=ok`.
- Empty save allowed; empty approve denied by core. Reject requires nonblank reason and may use empty selection.
- Pending: `review_version == selection_version`; terminal: `review_version == selection_version + 1`.
- No-op happens only after actor/pending/expected-version/eligibility validation: 200 `changed:false`, no new event/version; stale no-op is still 409.
- Core canonicalizes sorted integer list and hashes compact UTF-8 JSON. Never trust/recompute an asserted client hash.
- v0/v1 reads legacy only; v1 API selection requires v2 and maps not-migrated/corrupt/future schema to 503; no GET/startup mutation.

## TDD and acceptance matrix

Write focused test first (RED), then implementation (GREEN). Use only existing in-process test facilities and synthetic DB/JWT/JWKS fixtures; do not start a server.

| Case | Expected |
|---|---|
| Detail read interleaving | Reader begins snapshot, writer commits save between reader's draft/select queries; reader returns matching old review+selection, fresh request sees new; deterministic Barrier/hook, no sleep. |
| Selection save changed/no-op | Changed increments both versions/event and returns committed shape; repeat with current version returns unchanged, no audit/version increase. |
| Stale/terminal/races | Two save or save-vs-decision same expected version: exactly one mutation wins; loser 409; no orphan event; save terminal 409. |
| Approval | Effective nonempty snapshot copied in final audit; empty approval 403; reject records final snapshot and reason. |
| Eligibility/input | empty valid; noneligible/unknown, duplicate, negative, bool, string/null/object, overflow, extra key/list too large → 422, no mutation. |
| Safe number boundary | accept `2**53-1`; client input above it 422; stored public result above it 503, never silently round. |
| Auth/Origin | missing/invalid JWT 401; wrong role 403; missing/wrong Origin POST 403; subject/body spoof cannot alter actor; existing self-approve denial remains. |
| HTTP parsing | missing/wrong content type 415; malformed JSON/query/path/repeated/unknown query/extra body 422; no trace/payload leak. |
| Cache/error | Every v1 response including errors has no-store and Vary; error envelope exact. |
| Compatibility | existing `/api/drafts` tests continue; v0/v1 DB selection v1 endpoints 503 without writes; corrupt/mixed DB 503 and no mutation. |
| API/UI boundary | v1 response has selection and versions >1; legacy parser is not invoked/changed. Document Frontend handoff rather than add fallback. |

Run targeted extractor selection tests, `portal_api/tests/test_w05_api.py`, then relevant full Python suite if project command is known from tree; report every command/exit code/count. Run formatting/lint only for changed Python files and inspect `git diff --check`. Do not call research a product test.

## Synthetic examples for Backend and later Frontend handoff

```
GET /api/v1/drafts/5 -> review.version=2, selection.version=2, selected_indices=[0]
POST /api/v1/drafts/5/selection {"expected_version":2,"selected_indices":[]} -> 200 changed=true, review=3, selection=3
POST /api/v1/drafts/5/decision {"decision":"approve","expected_version":3} -> 403 forbidden
POST /api/v1/drafts/5/decision {"decision":"reject","expected_version":3,"reason":"Không đủ bằng chứng"} -> 200 version=4, selection_version=3
```

Handoff Frontend after Backend acceptance: change API path to `/api/v1`, parse exact v1 shape atomically, render selection from `selection.selected_indices` (not `items.keep`), submit only `expected_version` + indices, and on 409 reload detail rather than retrying mutation. No frontend fallback may silently approve baseline/all items.

## Definition of done / evidence

Backend reports: resulting commit/ref; exact changed file list; `git status`; each test/lint/diff command with fresh exit/count; deterministic interleaving test evidence; short JSON response samples; and explicit UNVERIFIED items (browser, listener, proxy/JWKS cloud/lab/UI integration). Completion is API slice only, not portal integration or deployment.
