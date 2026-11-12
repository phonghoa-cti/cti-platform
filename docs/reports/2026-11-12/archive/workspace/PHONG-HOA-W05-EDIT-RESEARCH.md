# W05-EDIT — lõi lưu lựa chọn IOC của người duyệt

**Ngày kiểm:** 11/11/2026 (UTC+07). **Phạm vi:** nghiên cứu/brief; không sửa mã, không tạo DB, không chạy test mới, không gọi HTTP, OpenCTI hay lab.

## Câu hỏi và hiện trạng kiểm trực tiếp

Chọn lát cắt SQLite nhỏ nhất để Analyst/Admin bỏ chọn rồi chọn lại **IOC đã đủ điều kiện**, lưu lịch sử lựa chọn, và `approve` đúng snapshot đó. Không có human-added IOC, API/UI hay OpenCTI trong lát cắt này.

Tree đọc: `cti-w05-local-integration`, branch `feat/w05-local-integration-20261111`, HEAD đúng `d94afb1e24929f64f82a921cd29307be175fb04e`; `git status --short` không có dòng nào khi kiểm.

Các điểm tái sử dụng tại ref này:

| Thành phần | Bằng chứng | Dùng lại / giới hạn |
|---|---|---|
| Payload và evidence bất biến | `extractor/phonghoa_extractor/store.py:99-185`, `_decode_payload_row`:430-451 | `_validate_draft`, hash nguồn, span/evidence và `payload_json` tiếp tục là nguồn sự thật; không ghi đè payload. |
| Quyết định hiện có | `store.py:697-842` | `Actor`, lỗi typed, policy Analyst/Admin, chống tự duyệt, `BEGIN IMMEDIATE`, optimistic `review_version`, update+audit cùng transaction. Version không còn chỉ 0/1. |
| Audit cuối | `store.py:259-280`, `:805-821` | `draft_audit.draft_id UNIQUE` giữ nguyên: đúng một **quyết định cuối**. Không nhét nhiều lần edit vào bảng này. |
| Migration/đọc chỉ đọc | `store.py:311-410`, `:602-694` | `PRAGMA user_version`, validate schema nghiêm, `mode=ro`; read không migrate/ghi. |
| Parser API/UI hiện hành | `portal_api/schemas.py:21-110`; `portal/web/data/draft-adapter.ts` | Core không chạm các hợp đồng này. Khi nối API sau, `review_version` không còn `Literal[0|1]`, còn shape GET cũ phải giữ tương thích có versioned extension. |

### Nguồn gốc đã đối chiếu

| Ai đã làm | Nguồn chính thức, đọc 11/11/2026 | Điều áp dụng / giới hạn |
|---|---|---|
| SQLite | [Transactions](https://sqlite.org/lang_transaction.html): chỉ một write transaction đồng thời; `BEGIN IMMEDIATE` có thể nhận `SQLITE_BUSY`. | Giữ transaction nguyên khối cho save/decision và timeout có kiểm soát; phải test xung đột. |
| SQLite | [Foreign keys](https://sqlite.org/foreignkeys.html): foreign key phải bật riêng từng connection. | Giữ `PRAGMA foreign_keys=ON` trước transaction và FK event→draft. |
| SQLite | [ALTER TABLE](https://sqlite.org/lang_altertable.html): `ADD COLUMN` có ràng buộc; [user_version](https://sqlite.org/pragma.html#pragma_user_version) là integer cho ứng dụng dùng. | Tăng schema 1→2 bằng migration explicit/idempotent; không đoán schema chỉ theo cột. |
| OpenCTI | [Draft workflow](https://docs.opencti.io/latest/usage/draft-workflow/) | Mượn nguyên tắc workflow instance/transition theo quyền; không tái dùng API/semantics validate hay Enterprise capability. |

## Ba phương án

| Phương án | Tái sử dụng | Hạn chế | Kết luận |
|---|---|---|---|
| A. Ghi `selected_indices_json` ngay trên `drafts` | Ít bảng | Mất lịch sử edit; không chứng minh snapshot nào được duyệt. | Loại. |
| B. Mở rộng `draft_audit`, bỏ `UNIQUE(draft_id)` để thêm action `save_selection` | Một bảng log | Phải rebuild bảng SQLite chỉ để đổi constraint; làm mờ invariant “một quyết định cuối”, ảnh hưởng mạnh test/audit hiện có. | Loại. |
| **C. Bảng event edit riêng + `draft_audit` giữ final decision** | Giữ toàn bộ review/migration/read-only hiện có; append-only selection history; migration `ADD COLUMN` tối thiểu. | Thêm 1 bảng và 3 cột reference nullable ở audit. | **Chọn.** |

## Quyết định C: snapshot selection event, không sửa IOC

### Policy và nhận diện

* `item_index` là vị trí zero-based của `items` trong payload canonical bất biến. Đây là ID ổn định **trong draft ID**; không dùng `value` (có thể trùng), và không nhận item object/`keep`/status do client đưa.
* `eligible_indices(payload)` chỉ gồm `item.kind == "ioc"`, `item.keep is True`, `item.status == "ok"`, span/evidence hợp lệ qua `_validate_draft`. `allowlist`, `bia`, `keep=false`, kind khác IOC và item lỗi không thể hồi sinh/chọn.
* Save nhận một danh sách index nguyên, không bool, không âm, không vượt `2**63-1`, không trùng; giới hạn tối đa `len(eligible_indices)` (tức <= số item draft). Tập rỗng **hợp lệ**: Analyst có thể bỏ chọn toàn bộ; `approve` tập rỗng bị policy từ chối để không sinh approval vô nghĩa. No-op (tập giống effective snapshot) trả kết quả hiện tại, không tăng version/không ghi event.
* Chỉ `Actor` trusted có `analyst|admin` save/approve/reject; subject phải không rỗng. Không tự approval nếu actor là creator. Chỉnh selection không phải quyết định và không áp quy tắc two-person mới; tuy vậy actor phải là Analyst/Admin và không được vượt eligibility. Actor không đến từ client/header trong core.
* Human-added IOC là **không hỗ trợ**. `AI extracted` = số eligible ban đầu; `human deselected` = `len(baseline) - len(effective)`; `selection_save_count` = event save thành công. Các số này không phải Precision/Recall hay đo chất lượng AI.

### Schema v2 đề xuất

`drafts` thêm `selection_version INTEGER NOT NULL DEFAULT 0 CHECK (selection_version >= 0)`. `review_version` là version đồng thời chung và tăng sau save hoặc decision; do đó bỏ mọi giả định max=1.

```sql
CREATE TABLE draft_selection_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  draft_id INTEGER NOT NULL REFERENCES drafts(id),
  selection_version INTEGER NOT NULL,
  review_version INTEGER NOT NULL,
  action TEXT NOT NULL CHECK(action = 'save_selection'),
  at TEXT NOT NULL,
  actor_subject TEXT NOT NULL,
  selected_indices_json TEXT NOT NULL,
  selected_sha256 TEXT NOT NULL,
  UNIQUE(draft_id, selection_version),
  UNIQUE(draft_id, review_version)
);
CREATE INDEX idx_draft_selection_audit_draft_version
  ON draft_selection_audit(draft_id, selection_version DESC);
```

`draft_audit` vẫn có một row final/draft, thêm nullable `selection_version INTEGER`, `selected_indices_json TEXT`, `selected_sha256 TEXT`. Audit legacy có ba giá trị `NULL` (không bịa snapshot); decision mới phải ghi đủ 3 giá trị. `selected_indices_json` là JSON canonical mảng index tăng dần, hash SHA-256 của UTF-8 canonical JSON. Event records immutable ở mức ứng dụng; SQLite file write access vẫn có thể sửa nên **không** gọi là tamper-proof.

Effective selection: event có `selection_version` lớn nhất; nếu chưa có event, lấy `eligible_indices(payload)` và coi `selection_version=0`. Quyết định copy exact canonical snapshot+hash và reference version vào `draft_audit` trong cùng transaction. Payload/source hash/text/evidence/author không sửa.

### Concurrency và transaction

1. Validate input/Actor trước write; mở `mode=rw`, bật FK, kiểm schema v2, `BEGIN IMMEDIATE`.
2. Read và `_decode_draft_row`, validate payload, pending state, `review_version == expected_version`; compute eligible/effective từ DB, không từ client.
3. Save: nếu no-op return current snapshot; nếu khác, update `drafts.review_version = +1, selection_version = +1` với `WHERE pending AND review_version=?`, rồi insert event. Commit một lần.
4. Approve: load effective snapshot trong **cùng transaction**, require non-empty and every index eligible, update terminal state with same `WHERE`, rồi insert one `draft_audit` carrying snapshot/hash/version. Reject giữ selection snapshot không đổi; audit final có nullable selection fields (không cần apply selection).
5. Bất cứ lỗi INSERT audit/event, update zero-row, constraint, `SQLITE_BUSY` hoặc commit fail đều rollback toàn bộ. Save-vs-save và save-vs-decision: đúng một bên thắng; bên kia `DraftConflictError`/mapped busy error, không event mồ côi. Terminal draft: save conflict, approve/reject conflict, không audit mới.

### Migration và compatibility

`STORE_SCHEMA_VERSION=2`. V2 migration chỉ nhận đúng V1 đã `_validate_current_schema`; legacy V0 vẫn phải đi qua V1 semantics hiện có hoặc được hỗ trợ explicit trong một transaction. `ALTER TABLE drafts ADD selection_version ... DEFAULT 0`, tạo event table/index, `ALTER TABLE draft_audit ADD` ba nullable columns, validate schema đầy đủ, rồi `PRAGMA user_version=2` và commit. Lần 2 không đổi DB. Unknown future version/corrupt/missing UNIQUE/FK/check hay v1 audit data mâu thuẫn: fail closed `DraftSQLiteError`; không tự repair. Đọc `get_draft`/`list_drafts` vẫn `mode=ro`, không migrate.

Core không đổi public GET/HTTP/UI trong task này. Compatibility cần giữ khi nối sau: GET detail giữ payload và `review` cũ; chỉ thêm `selection` object versioned (`eligible_indices`, `selected_indices`, `selection_version`, counts). Queue vẫn chỉ pending; `review_version` là strict int >=0 thay vì fixed literal. Không âm thầm approve “all” khi có saved selection.

## Chưa biết / ngoài phạm vi

Chưa test code này; chưa xác minh behaviour SQLite theo bản Python/lab, hiệu năng DB lớn, auth production, mapping role, UI/API compatibility thực tế, OpenCTI version/license/ingestion. Không có suy luận “không tìm thấy” thành không tồn tại. Cần giai đoạn evaluation xác định labeling ground truth trước khi dùng metrics chất lượng AI.
