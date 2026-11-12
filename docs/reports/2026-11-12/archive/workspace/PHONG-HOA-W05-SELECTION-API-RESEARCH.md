# W05 Selection API — nghiên cứu hợp đồng HTTP và tương thích

**Ngày kiểm:** 11/11/2026 (UTC+07)
**Phạm vi:** chỉ nghiên cứu và brief; không sửa mã, không tạo DB/listener, không chạy test sản phẩm.
**Tree đã đọc:** `cti-w05-selection`, branch `feat/w05-selection-local-20261111`, HEAD `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`, sạch khi kiểm (`git status --short` trống). Đây là core selection đã được Leader nghiệm thu 40/40; API/UI selection chưa được triển khai.

## Câu hỏi và kết luận

Cần đưa **lựa chọn hiệu lực** (effective selection) của IOC ra HTTP mà không lẫn nó với `items[].keep` là lựa chọn gốc do extractor tạo, đồng thời chống ghi đè khi hai Analyst cùng sửa.

**Khuyến nghị:** thêm một endpoint lưu selection riêng, nới DTO HTTP sang strict version nguyên an toàn JavaScript, và thêm một getter core nhỏ `get_draft_with_selection()` đọc draft + selection trong **một read transaction/cùng connection**. Không ghép `get_draft()` và `get_effective_selection()` tại service: hai getter hiện tự mở kết nối khác nhau, nên có thể trả payload/review trước save và selection sau save.

Không thêm dependency, session, idempotency key, auth mới, UI, listener, migration ngầm hay OpenCTI.

## Hiện trạng và phần tái sử dụng

| Phần | Bằng chứng ở ref đã đọc | Dùng lại / khoảng trống |
|---|---|---|
| Core selection | `extractor/phonghoa_extractor/store.py:920-1186` | `_eligible_ioc_indices`, canonical JSON/hash, `get_effective_selection`, `save_selection` đã kiểm policy, no-op, optimistic version, audit và `BEGIN IMMEDIATE`. |
| Quyết định cuối | `store.py:1233-1345` | `decide_draft` lấy selection trong write transaction, chặn self-approve và empty approval; response API hiện mới chỉ biểu diễn version cũ. |
| Read draft | `store.py:810-848` | `get_draft` chỉ đọc nhưng không mở explicit read transaction và không mang selection. Ghép nó với getter selection ở service là race snapshot. |
| HTTP | `portal_api/app.py:125-189`, `service.py:32-91`, `schemas.py:13-112` | JWT/role server-side, same-origin mutation, error envelope, `no-store`, giới hạn ID/query và dịch lỗi lõi có thể giữ nguyên. DTO cần thay. |
| UI parser hiện tại | `portal/web/data/api-client.ts:102-173` | Parser exact yêu cầu summary `review_version===0`, detail `review.version<=1`, decision `version===1` và các key cố định. Backend mới không thể giả 0/1 để vượt qua parser. |

`items[].keep` là dữ liệu bất biến trong `payload_json`; selection là snapshot do người duyệt chọn từ tập eligible (`kind=ioc`, `keep=true`, `status=ok`). Chỉ selection được đổi; API không nhận item/object/`keep` từ client.

## So sánh ba cách

| Cách | Ưu / nhược | Quyết định |
|---|---|---|
| A. Service gọi tuần tự `get_draft()` rồi `get_effective_selection()` | Ít code; nhưng writer có thể commit ở giữa hai connection: `review_version` và selection không cùng snapshot. | Loại. |
| B. Service tự SQL JOIN/đọc hai bảng | Có thể nhất quán nhưng nhân đôi schema/invariant/canonical validator của core vào adapter HTTP. | Loại. |
| **C. Core getter kết hợp, one connection + `BEGIN`** | Giữ core là nguồn sự thật; một điểm validate; API mỏng. SQLite cho read transaction giữ snapshot không đổi qua các SELECT. | **Chọn.** |

### Thay đổi core nhỏ bắt buộc

Thêm public helper, tên gợi ý:

```python
def get_draft_with_selection(db_path, draft_id, *, timeout=5.0) -> dict[str, Any]:
    # mode=ro; yêu cầu user_version==2; _validate_current_schema;
    # BEGIN; SELECT drafts; _decode_draft_row; _load_effective_selection(connection,...)
    # return {**payload, "id": ..., "created_at": ..., "review": review,
    #         "selection": asdict(selection)}
```

Thêm riêng `list_drafts_with_selection_version(...)` (cùng pagination pending hiện có, v2 only) để v1 list nhận đúng `selection_version` mà không đổi output `list_drafts()` legacy. Helper list không tính selected/count nên không phải ghép nhiều snapshot. Cả hai helper mới không thay `get_draft()`/`list_drafts()` legacy nên read v0/v1 cũ vẫn hoạt động không ghi. V2 hỏng/chưa migrate, missing DB, payload/event/hash/version hỏng phải fail closed thành `DraftSQLiteError`/`DraftNotFoundError`; không tự migrate/tạo DB. `selection.changed` từ getter luôn `false`.

Test interleaving phải dùng hook/Barrier được inject vào helper test hoặc wrapper connection: reader `BEGIN` và đọc draft, writer `save_selection` commit, reader mới đọc selection. Response reader phải chứa cả hai trường theo snapshot trước writer; request mới sau đó thấy snapshot mới. Không dùng `sleep`. Save response phải lấy trực tiếp `DraftSelectionResult` do transaction vừa commit trả về; không GET lại để tránh trả snapshot của writer kế tiếp.

## Contract HTTP được chốt: `/api/v1/drafts`

Chọn **prefix `/api/v1` cho contract selection**; ba route `/api/drafts` cũ không đổi để không làm parser legacy nhận detail/key/version khác. UI hiện tại sẽ chưa gọi v1; Frontend chỉ nối sau khi đổi parser trong task riêng. API v1 không là tuyên bố tương thích ngược với UI cũ.

Tất cả endpoint v1: JWT đã verify, subject/roles chỉ từ `Principal` server-side; role `analyst|admin`; JSON response; `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`. GET không cần Origin. Hai POST yêu cầu exact `Origin == settings.portal_origin` và `Content-Type: application/json` (tối đa charset UTF-8 như route cũ). Không tin subject/email/role trong body/query/header khác JWT.

### DTO và miền số

`JSON_SAFE_INTEGER = 9007199254740991` (= `2**53-1`) là giới hạn public cho **mọi integer JSON**: draft ID, cursor, review/selection version, indices, counts. SQLite nhận đến `2**63-1`, nhưng UI TypeScript kiểm `Number.isSafeInteger`; API v1 phải từ chối request ID/version/index vượt safe range bằng 422, và fail closed 503 nếu DB trả ID/version/count vượt safe range. `bool` không là integer. Pydantic dùng `strict=True`, `StrictInt`, `extra="forbid"`; list index giới hạn tối đa `ai_eligible_count` (cũng có body limit hiện hành/setting, không thêm dependency).

#### `GET /api/v1/drafts?limit=20&before_id=<safe-positive-int>`

Giữ queue pending, cursor ID giảm dần. Summary exact:

```json
{"items":[{"id":5,"created_at":"2026-11-11T...+00:00","status":"pending",
"source":{"name":"synthetic.txt","sha256":"<64 lowercase hex>"},"language":"vi","tlp":"TLP:GREEN",
"item_count":3,"injection_warning":false,"review_status":"pending","review_version":2,
"selection_version":2,"selected_count":1,"ai_eligible_count":2}],"next_before_id":null}
```

`selected_count` and counts come from an internally consistent source per row; if doing so would require N selection transactions, first preserve core semantics rather than fabricate values. V1 list keeps only `review_version` and `selection_version`; omit selection counts from list and show them in detail. It calls `list_drafts_with_selection_version`, not legacy `list_drafts`. Thus final v1 list exact keys are legacy summary plus `selection_version`; `review_version` strict `0..JSON_SAFE_INTEGER`, not literal 0.

#### `GET /api/v1/drafts/{draft_id}`

Calls only `get_draft_with_selection()`. Detail equals 1.0 stored payload plus `id`, `created_at`, `review`, and exact selection object:

```json
"selection":{"review_version":2,"selection_version":2,"selected_indices":[0],
"selected_sha256":"<64 lowercase hex>","saved_by_subject":"opaque-subject",
"saved_at":"2026-11-11T...+00:00","changed":false,
"ai_extracted_count":3,"ai_eligible_count":2,"human_deselected_count":1,"selection_save_count":2}
```

`review.version` must equal `selection.review_version`. Pending invariant is `review_version == selection_version`; terminal is `review_version == selection_version + 1`. Detail after decision is readable and includes final effective selection; no audit rows, no client-supplied flags, no hidden recovery to baseline.

#### `POST /api/v1/drafts/{draft_id}/selection`

Exact request, idempotent only in core's stated **no-op** sense (not a general retry guarantee):

```json
{"expected_version":2,"selected_indices":[0]}
```

`expected_version` is current `review.version`; no client retry after 409. Entries must be unique, non-negative safe ints, ascending or unordered accepted then canonicalized by core, subset of eligible; empty list allowed. Unknown/noneligible, duplicate, negative, bool, object/null/string, extra keys, oversized body/list and overflow are 422 before mutation. Service constructs `Actor(Principal.subject, Principal.roles)` then calls `save_selection` exactly once.

200 response exact selection object above except `changed` may be true. No-op returns current state with `changed:false`, same `saved_by_subject`/`saved_at`, no event/version change. Changed save returns committed core result with `changed:true`; no additional read. Pending stale/terminal and races are 409.

#### `POST /api/v1/drafts/{draft_id}/decision`

Same strict decision body as current route, but `expected_version` accepts safe int 0..`JSON_SAFE_INTEGER`; calls existing `decide_draft` once. Response:

```json
{"draft_id":5,"status":"approved","version":3,"decided_by_subject":"opaque-subject",
"decided_at":"2026-11-11T...+00:00","reason":null,"selection_version":2,
"selected_indices":[0],"selected_sha256":"<64 lowercase hex>"}
```

The core final audit remains authority for snapshot. Reject may have empty selected list but needs nonblank `reason`; approval rejects empty selection, unsupported kept kind, creator self-approval and creator null. No self-approval bypass is introduced.

### Stable errors

| Status | code | Cases |
|---:|---|---|
| 401 | `authentication_required` | missing/invalid JWT |
| 403 | `forbidden` | role, Origin, self-approve/other core policy |
| 404 | `draft_not_found` | authenticated request for missing DB draft |
| 409 | `draft_conflict` | stale version, terminal draft, concurrent winning mutation, SQLite INTEGER version ceiling |
| 415 | `unsupported_media_type` | mutation not exact JSON content type |
| 422 | `invalid_request` | malformed/extra/wrong type/unsafe number/body/query/path |
| 503 | `review_unavailable` | absent/unmigrated/corrupt/future DB, busy, output contract breach, unexpected core/store failure |

Envelope remains `{"error":{"code":"...","message":"..."}}`; no DB paths, SQL, stack trace, raw CTI text/evidence, actor/audit internals or token material. No error path may omit `no-store` for `/api/v1/drafts`.

## Compatibility and historical state

- DB v0/v1: legacy `GET /api/drafts*` remains read-only; v1 selection GET/save/decision return 503 `review_unavailable` until explicit `migrate_store`, never migrate on GET/startup.
- v2: strict schema validation; historical `draft_audit` selection columns NULL are valid only migrated audit history, not synthetic current selection.
- terminal: selection save is 409; detail is coherent and final snapshot remains visible. Save-vs-save and save-vs-decision have one committed winner because core uses `BEGIN IMMEDIATE` plus expected version.
- Canonical hash is SHA-256 of compact UTF-8 JSON sorted indices, e.g. `[0,2]`; API exposes it but never recomputes from client as authority.
- Current `/api/drafts` and `api-client.ts` deliberately remain legacy. Frontend handoff: adopt v1 path and replace exact parser/interface atomically (new selection object, `review_version>1`, decision `version>1`), then add UI selection controls. Backend completion alone does **not** mean the current UI works against edited drafts.

## Nguồn kiểm chứng (đọc 11/11/2026)

| Tổ chức | Nguồn | Áp dụng |
|---|---|---|
| SQLite | [Isolation](https://www.sqlite.org/isolation.html) | Read transaction có snapshot ổn định qua các SELECT; hai connection độc lập không tạo atomic composite read. |
| SQLite | [Transactions](https://www.sqlite.org/lang_transaction.html) | Một writer; `BEGIN IMMEDIATE` có thể `SQLITE_BUSY`; giữ lỗi unavailable khác conflict. |
| Pydantic | [Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) | Default có coercion; strict validation cần thiết cho version/index/body untrusted. |
| IETF | [RFC 9110, POST](https://www.rfc-editor.org/rfc/rfc9110#section-9.3.3) | POST không mặc định idempotent; không tự retry mutation, no-op chỉ là semantics ứng dụng. |

## Chưa kiểm

Không có implementation/test API mới trong nghiên cứu này. Chưa xác minh dependency/runtime FastAPI-Pydantic hiện hành, body limit hiện có, JWT/JWKS/cloud, reverse proxy, browser/UI, hiệu năng DB lớn hay lab. Nguồn SQLite/Pydantic hỗ trợ quyết định thiết kế, không là bằng chứng mã sẽ pass.
