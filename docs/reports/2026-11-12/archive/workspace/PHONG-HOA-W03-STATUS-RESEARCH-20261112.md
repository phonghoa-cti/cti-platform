# W03-STATUS-NEXT — trạng thái xử lý theo technology/CVE

**Ngày kiểm:** 12/11/2026 (UTC+07) · **Loại:** nghiên cứu + contract đề xuất; không triển khai, không chạy test mới.
**Base chỉ đọc:** `cti-w03-read-integration` tại `7ff6eb3af21d8de65836bfbf707396ae5690de0b`; `git status --short` không có dòng nào khi đọc.
**Đích quyết định:** sau W03-R đã được nghiệm thu cục bộ, thêm lát cắt nhỏ để IT ghi nhận việc xử lý của *một quan hệ technology/CVE*, còn Leader chỉ xem tổng hợp/lịch sử đã lược dữ liệu.

## Kết luận để Leader chốt

**Khuyến nghị: điều chỉnh các thành phần cục bộ đã có, không lấy connector/feed live.** Tạo một store trạng thái độc lập nhưng dùng cùng SQLite path với TechnologyStore, qua port `CveStatusReadPort`/`CveStatusWritePort`. Định danh không thể tái dùng là `technology_id` cùng snapshot identity tại lúc ghi; bản ghi hiệu lực chỉ áp cho đúng:

```text
(technology_id, cve_id, vendor_key, product_key)
```

`software_version` là snapshot hiển thị/audit, **không nằm trong khóa**. Lý do: sửa version trên cùng asset không được làm mất lịch sử; nhưng status cũ phải hiện là “cần xem lại” chứ không được tự áp cho version mới. Đổi `vendor/product` (identity drift), soft-delete rồi tạo asset mới, hoặc CVE không còn match hiện hành đều không kế thừa trạng thái sang quan hệ mới.

Đây là status do người có quyền xác nhận, không phải kết luận kỹ thuật của hệ thống. `patched` và `not_affected` không được suy ra từ match tên, KEV, CVSS, EPSS, hay việc `software_version` vừa thay đổi. Không auto-remediation, không SLA SME từ KEV due date.

## Hiện trạng và phần dùng lại

| Đã có tại base | Đọc trực tiếp | Dùng lại | Không suy rộng |
|---|---|---|---|
| W03-R CVE read | `portal_api/cves.py`, `/api/cves` trong `app.py`, `docs/specs/W03-lo-hong-anh-huong.md` | dataset+technology snapshot, cursor có `snapshot/context`, limit 1 MiB, ranking/null/notice, lỗi 401/403/404/409/422/503 | Chưa có row status/audit hay kết luận affected version. |
| W04 Technology | `portal_api/technologies.py`, `TechnologyStore` | ID an toàn, vendor/product chuẩn hóa, `record_version`, soft delete, validate schema, SQLite `BEGIN IMMEDIATE`, audit before/after | Technology `record_version` không phải status version; CRUD không được tự sửa status. |
| Auth/API | `portal_api/app.py`, `auth.py` | JWT server-side, roles_by_subject, Origin+JSON cho mutation, `Cache-Control: no-store`, `Vary` | Client không được gửi actor/role/identity snapshot. |
| W03-S trước đó | `PHONG-HOA-W03-RESEARCH-20261112.md`, mục “Trạng thái/audit để sau” | granularity theo cặp, append-only audit, no auto-status, no mutation retry | Bản cũ chưa chốt version/identity drift, cursor/history, DTO và acceptance đầy đủ. |

## Nguồn đối chiếu đã đọc (12/11/2026)

| Nguồn gốc | Điều dùng cho quyết định | Giới hạn |
|---|---|---|
| [SQLite — Transactions](https://www.sqlite.org/lang_transaction.html) | SQLite chỉ có một write transaction tại một thời điểm; `BEGIN IMMEDIATE` có thể trả `SQLITE_BUSY`; lỗi trong transaction cần rollback rõ ràng. Dùng cho write status + audit nguyên tử và map unavailable. | Không thay thế kiểm thử thực tế trên filesystem/lab của dự án. |
| [SQLite — Isolation](https://www.sqlite.org/isolation.html) | Read transaction quan sát snapshot; WAL cho reader/writer đồng thời nhưng reader vẫn thấy snapshot cũ. Dùng để không trộn trang CVE/status qua nhiều thời điểm. | Không chứng minh journal mode/cấu hình runtime Phong Hỏa. |
| [IETF RFC 9110 §15.5.10](https://datatracker.ietf.org/doc/html/rfc9110#section-15.5.10) | `409 Conflict` phù hợp cho `expected_status_version` cũ, và response nên đủ để người dùng nhận ra xung đột. | Không bắt buộc một wire format cụ thể. |
| [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | Audit nên đủ “when, where, who, what”; chỉ lưu tóm tắt cần thiết, tránh ghi nội dung nhạy cảm không cần. | Đây là guidance, không chứng minh audit DB bất biến trước người có quyền ghi file. |

## Phạm vi

| Giai đoạn W03-S đầu | Để sau |
|---|---|
| Bốn status, note có kiểm bound, status version, snapshot identity/version, append-only audit, list status theo CVE query hiện hữu, row history theo relation, summary Leader lược dữ liệu, UI controls/recovery. | CPE/range assessment, workflow/phê duyệt hai người, chứng minh bản vá, ticket/change-management connector, due-date KPI/SLA, feed/OpenCTI/lab/production, sửa file SQLite, retention policy. |

## Contract nhỏ nhất

### 1. Mô hình và quy tắc identity

`CveStatus` (trạng thái hiện hành) chứa:

```text
technology_id: safe positive integer
cve_id: canonical CVE-YYYY-N+
vendor_key, product_key: exact normalized keys từ CVE match hiện hành
technology_vendor, technology_product, software_version: snapshot display tại lúc ghi
technology_record_version: record_version Technology khi ghi
status: open | patching | patched | not_affected
note: string (trimmed 1..1000 Unicode code points; control chars bị từ chối)
status_version: positive integer (first committed write = 1)
updated_at: UTC RFC3339
updated_by: server-side principal subject
dataset_id: dataset snapshot hiện hành của W03-R
```

`CveStatusAudit` là append-only, có `audit_id` tăng dần, `status_key`, `event=created|changed`, `before_status/null`, `after_status`, `note`, `actor_subject`, `occurred_at`, và đủ snapshot fields trên. Không cho client đặt actor/time/snapshot. Không có row = `status: null`, nhãn UI “chưa có trạng thái”; không tạo row giả khi GET.

**Drift rule:** write phải re-read trong transaction technology active cùng `technology_id`, canonical CVE candidate và exact vendor/product match trong **dataset snapshot hiện hành**. Nếu version thay nhưng identity vẫn exact, write thành công nhưng response đặt `review_required=true` khi client `technology_record_version` khác current; status cũ vẫn chỉ là history của version snapshot. Nếu vendor/product khác, deleted, ID không active, hoặc CVE no longer exact-match: `409 status_context_changed`, không ghi. Asset mới sau soft-delete có ID khác nên không thể thừa kế.

### 2. HTTP

Tái dùng `GET /api/cves` và bổ sung status theo DTO đó, không mở endpoint ghi chung toàn công ty.

```text
GET  /api/cves?...&status=open|patching|patched|not_affected|unset
GET  /api/cves/{cve_id}/technologies/{technology_id}/status-history?limit=1..100&cursor=<opaque>
PUT  /api/cves/{cve_id}/technologies/{technology_id}/status
```

* `GET /api/cves`: `status` optional; absent = cả row lẫn unset, `unset` = không có status row, các giá trị khác = status hiện hành. Nó là một phần của `context` hash/cursor. Trong mỗi `matches[]`, thêm `status` (`null` hoặc DTO status), `status_version` (`null` hoặc positive int), `review_required` và `status_updated_at`; không trả `updated_by`/note/history cho Leader.
* History only accepts `limit` (default 25) và opaque cursor, strict duplicate/unknown query rejection, max cursor 1024 bytes; cursor binds `technology_id,cve_id,vendor_key,product_key` **và status snapshot hash**. Status mutation giữa các trang → `409 status_snapshot_changed`, không skip/duplicate audit event.
* PUT body exact fields:

```json
{
  "status": "patching",
  "note": "Đã mở thay đổi nội bộ; chờ cửa sổ bảo trì.",
  "expected_status_version": 2,
  "expected_technology_record_version": 7,
  "expected_dataset_id": "sha256:..."
}
```

First write uses `expected_status_version: 0`; existing row requires exact current positive version. `note` is required for all writes, including reopen to `open`, so audit retains human reason. PUT is deliberately idempotence-by-version only: same request replay after committed success returns `409 status_version_conflict`, not a second audit. Response `200` is the committed DTO plus last audit id; no success response/connection aborted remains **unknown outcome** at UI.

### 3. Quyền và lỗi

| Caller (server role) | List CVE/status | History | PUT |
|---|---:|---:|---:|
| Leader only | summary/KPI only; no technology/version/note/actor | no | no |
| IT, analyst, admin (kể cả mixed-role) | full DTO trong phạm vi role hiện có | full relation history | allowed |
| Role khác | 403 | 403 | 403 |

`leader` mixed với `it|analyst|admin` nhận full DTO và được ghi: quyền hiệu lực cao nhất trong tập role đã xác thực. JWT/auth fail → `401 authentication_required`; auth verifier/store/database busy/corrupt/dataset unavailable → `503 cves_unavailable` hoặc `status_unavailable`, **không** nêu path/SQL. `404 technology_not_found` chỉ sau xác thực/quyền và khi công nghệ active không tồn tại; `409 status_version_conflict` trả current safe `{status,status_version,updated_at}` cho writer; `409 status_context_changed` trả reason enum (`technology_changed|technology_deleted|match_changed|dataset_changed`) không lộ dữ liệu ngoài relation; malformed fields, unsafe integer, over-bound body/note, duplicate/unknown query/invalid cursor/content type/origin → `422 invalid_status_request`. Tất cả response: `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`.

### 4. SQLite migration, transaction và non-mutation

Migration additive, version marker riêng `w03_status_migrations`; chỉ create `cve_technology_status`, `cve_technology_status_audit`, indexes/unique constraints, không alter W04 tables. `initialize()` được gọi ở wiring write store có chủ ý; GET W03 dùng read-only port `mode=ro`, **không** mkdir, migrate, create DB hay write audit/status.

Write sequence trên một connection, `foreign_keys=ON`, `BEGIN IMMEDIATE`:

1. validate body/Origin/auth trước DB; initialize/schema marker exact trước mutation;
2. re-read active technology and W03 dataset/match in same logical operation; reject drift;
3. insert first row with uniqueness `(technology_id,cve_id,vendor_key,product_key)` or conditional update `WHERE status_version=?`;
4. insert exactly one audit event from committed before/after snapshot;
5. commit only when both steps succeed; any exception rolls back, closes connection and maps expected DB issue to 503.

Race first write: unique conflict is reread; if committed equivalent row has a different/advanced version → 409, never silently overwrite and never duplicate audit. A constrained test seam must inject failure after status DML/before audit and prove no status/audit row remains. Schema partial/marker/index mismatch, missing/corrupt readonly DB, timeout/busy all fail closed 503. Append-only means application API has no UPDATE/DELETE audit path; OS-level tamper resistance is outside this local SQLite slice.

### 5. UI recovery, không redesign

Tái dùng W04 provider/layout/context token. Từng technology match hiện status pill, saved time; `null` rõ là “Chưa ghi nhận”, không “an toàn”. Form only opens for writer role; disable while pending; capture relation identity + status/technology/dataset versions; never send actor/role. A successful PUT retains committed notice even if subsequent refresh GET fails; refresh is **GET-only** and may be retried once by explicit UI action. A timeout/abort/lost response after PUT locks that relation as “chưa rõ kết quả”, shows no optimistic final status and offers *Tải lại để đối soát*; it must not replay PUT. `409` replaces editor with current server state and asks user to review/re-enter, not auto-merge. Context/provider/filter/route change invalidates stale callbacks; history cursor 409 returns to first page after explicit reload.

## Acceptance matrix đề xuất (chưa chạy)

| Nhóm | Tình huống | Đạt khi |
|---|---|---|
| First write race | Hai PUT `expected_status_version=0` cùng relation | đúng một status v1 + đúng một audit; còn lại 409; không overwrite. |
| Transition/reopen | `open→patching→patched→open`, note từng lần | status version tăng 1/lần, audit before/after/actor/time/snapshot đầy đủ; không suy affected. |
| Identity/version drift | đổi software_version; đổi vendor/product; delete rồi recreate; dataset no-match | version-only giữ history nhưng `review_required`; ba trường hợp sau 409/no inheritance/no audit mới. |
| Atomicity/schema | inject lỗi sau status DML; partial migration/index sai; DB missing/corrupt/busy | rollback zero row/audit mới hoặc 503; GET không tạo/migrate/write DB. |
| Auth/redaction | no/bad JWT; leader; IT/analyst/admin; mixed leader+IT; forged actor/role body | 401/403 trước DB; Leader only summary; writer actor server-derived; mixed effective writer. |
| Bounds/protocol | malformed JSON, Origin/type thiếu, note control/0/1001 chars, unsafe numbers, repeated query/body > cap | 422 trước mutation; status/audit byte-identical before/after. |
| Cursor/snapshot | history 2 pages rồi status mutation; context/filter/cursor sai | 409 snapshot changed hoặc 422 before read; không skip/duplicate; W03 1 MiB cap giữ nguyên. |
| UI recovery | double click; status 409; committed PUT then response loss; refresh 503; switch match mid-flight | one PUT; no replay; unknown locked/reload-only; committed notice survives; stale callback cannot alter new context. |

## Brief giao độc lập sau khi Leader chốt

### Backend (một tree riêng)

**Mục tiêu:** implement W03-S đúng contract trên trên base Leader chọn, không sửa W03-R ranking/match/cursor semantics ngoài thêm status context field.
**File dự kiến:** store/schema riêng status, `portal_api/cves.py`, `app.py`, schemas/settings/tests; không sửa ledger, feed, Technology CRUD behavior.
**Bắt buộc:** strict models/bounds; server principal only; read-only GET non-mutation; single immediate write transaction + audit; no implicit status; 409 expected versions/context; status/history cursor snapshot; tests acceptance matrix và regression W03-R/W04 Technology.
**Evidence trả:** HEAD/diff, exact focused commands/exits/counts, DB before/after or hash evidence for non-mutation/rollback. Không gọi local test là lab/browser/runtime proof.

### Frontend (một tree riêng)

**Mục tiêu:** add provider/parser/state for status controls per W03 technology match; không redesign và không assume API available.
**Bắt buộc:** strict DTO/error mapping; role/redaction UI; context ownership; pending/double submit; 409 reload/re-entry; unknown PUT outcome locks/reload-only/no replay; GET-only explicit recovery; history pagination cursor-change state; sample/offline mode never calls write API.
**Evidence trả:** unit/type/lint/build commands, focused recovery fixtures and HEAD/diff. Không claim gateway/browser/lab or backend integration.

### Integration gate (owner sau hai handoff)

1. Pin exact Backend + Frontend SHAs; compare DTO/OpenAPI/error codes and gateway route allowlist/body caps before wiring.
2. Local synthetic only: first-write race, all status transitions, version/identity drift, atomic rollback, authorization/redaction, cursor invalidation, unknown PUT + GET recovery. Prove mutation count separately from GET retry.
3. Acceptance local does not establish Cloudflare/JWKS/HTTPS thật, browser acceptance nếu chưa chạy, feed/OpenCTI, source freshness/license/TLP, lab hoặc production.

## Unknowns / không tuyên bố

* W03-R was accepted locally by Leader per task brief, but this report did not rerun its suite or repeat acceptance.
* The existing technology DB co-location, WAL mode, migration compatibility with every W04 deployment and real concurrent filesystem behavior require implementation tests.
* `patched`/`not_affected` have no evidence of a patch, CPE/version-range assessment, maintenance outcome or business impact.
* No source/feed, OpenCTI, secret, lab, cloud LLM, browser, push/PR/merge/deploy or ledger was accessed/changed in this task.

**Decision requested:** approve the W03-S contract as an independent local status/audit slice, with `software_version` snapshot + `review_required` rather than status inheritance or automatic patch determination.
