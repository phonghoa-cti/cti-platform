# W03-S1 — ghi trạng thái và lịch sử cho một công nghệ/CVE

## Quyết định của Leader

Nghiên cứu `PHONG-HOA-W03-STATUS-RESEARCH-20261112.md` (SHA-256 `c63ad100d48450ed3276cbff2e076387f9ea37894ac0930080e4f6c77a3cce24`) được chấp nhận **với sửa đổi dưới đây**, chỉ ở mức nghiên cứu. Base đã nghiệm thu W03-R: `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.

Chọn status/history trong chi tiết của từng quan hệ; giữ nguyên wire/query/ranking/cursor của GET `/api/cves`. Thêm ba route riêng. Cách này cho Backend và Frontend làm độc lập, không sửa hợp đồng chỉ đọc vừa nghiệm thu. Bộ lọc trạng thái toàn danh sách và KPI trạng thái/overdue cho Leader thuộc W03-S2, chưa làm lượt này. Phương án mở rộng toàn bộ list ngay tăng phạm vi cursor/redaction; phương án feed thật vẫn phụ thuộc môi trường ngoài. W03-S1 là một bước có ích, không phải toàn W03 đã xong.

Các sửa quan trọng so với research:

- **Mọi expected context cũ phải 409, không ghi rồi mới đánh dấu cần xem lại.** Đọc status cũ sau technology/dataset đổi thì `review_required=true`; chỉ lần xác nhận mới với context hiện hành mới ghi được.
- Giữ Origin 403, media type 415, body quá cỡ 413; không gộp thành 422. GET tài sản đã mất là 404; PUT context đã mất/đổi là 409, sau auth/quyền.
- Không initialize/migrate trong constructor, create_app hoặc bất kỳ request nào. Migration chỉ gọi rõ ở bootstrap/test có chủ ý.
- Dataset ngoài SQLite không nằm trong transaction SQLite: lấy đúng một snapshot immutable đã validate cho mỗi request. Kiểm expected_dataset_id với snapshot đó; không tuyên bố atomic với thay file ngoài giữa lúc chạy. W04 technology và status/audit phải đọc/ghi trong cùng connection/transaction.
- Chưa cho Leader đọc history/note/actor. Leader tiếp tục summary W03-R như cũ, không gọi status API.

Nguồn Leader mở trực tiếp 12/11/2026: [SQLite transactions](https://www.sqlite.org/lang_transaction.html) (một writer, BEGIN IMMEDIATE, busy/rollback); [SQLite isolation](https://www.sqlite.org/isolation.html) (snapshot giữa connection); [RFC 9110 §15.5.10](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.10) (409 cho xung đột trạng thái); [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#event-attributes) (ai/lúc nào/thao tác gì). Những nguồn này hỗ trợ cơ chế; contract cụ thể bên dưới là quyết định của Leader, chưa phải kiểm thử runtime.

## Nền và phân công

ROOT = `$WORKSPACE`.
Source chỉ đọc: `ROOT/cti-w03-read-integration`, base đầy đủ ở trên. Đọc AGENTS.md, docs/PROGRESS.md, spec W03, hợp đồng W03-R và W04 Technology đúng base. Brief này chốt phần mới; không sửa brief/ledger/source tree chung.

- Backend: `ROOT/cti-w03-status-backend`, branch `feat/w03-status-backend-20261112`.
- Frontend: `ROOT/cti-w03-status-frontend`, branch `feat/w03-status-frontend-20261112`.
- Mỗi người một Sol medium trực tiếp, không worker/bot con. Tạo worktree từ đúng base; nếu tree có sẵn giữ edits, kiểm owner/ref, không reset. Quyền làm cục bộ đã có; không mở vòng xin phép đa file vì mẫu cũ trong AGENTS.
- Không push/PR/merge/deploy, thay quyền/dependency, live feed/OpenCTI/LLM/lab/secret. Test dùng fixture tổng hợp hiện có; không claim nguồn thật hoặc đã vá thật. Không redesign UI.

## Contract chung s1 (không tự thay)

### Ngữ nghĩa và wire

Khóa lưu `(technology_id,cve_id,vendor_key,product_key)`; key chuẩn hóa lấy từ W04/CVE service, không từ client. Không có row nghĩa chưa ghi nhận, không tự tạo `open`. Bốn trạng thái `open|patching|patched|not_affected`; cho đổi bất kỳ trạng thái nào, kể cả reopen hoặc xác nhận lại cùng trạng thái, nhưng mỗi lần cần note mới và expected versions đúng.

`Context` có đúng các key:
```json
{"technology_id":1,"cve_id":"CVE-2026-2001","vendor":"Fortinet","product":"FortiOS","software_version":"7.2","technology_record_version":1,"dataset_id":"sha256:<64 lowercase hex>"}
```
`StatusRecord` có đúng `status,status_version,note,updated_at,updated_by,context`; `context` là snapshot Context khi lần ghi đó xảy ra. Status/version/actor/time không nullable. Context ở ngoài envelope là hiện hành, không phải snapshot lưu trong record.

Các response thành công đều có `notice` chính xác: **"Trạng thái do người dùng ghi nhận; không phải bằng chứng kỹ thuật đã vá hoặc không bị ảnh hưởng."**. Notice tên sản phẩm W03-R vẫn nguyên ở trang tra cứu.

1. `GET /api/cves/{cve_id}/technologies/{technology_id}/status`, không query. 200 đúng `{context,record,review_required,notice}`. `record=null` nếu chưa có row cho key hiện hành; khi null, review_required=false. Có record thì review_required=true nếu saved technology_record_version hoặc dataset_id khác context hiện tại. Đây là quy tắc bảo thủ: sửa note/display ở W04 cũng cần xác nhận lại, tránh tự áp trạng thái cũ khi identity/version đổi rồi đổi lại.
2. `PUT` cùng path, không query. Body đúng `{status,note,expected_status_version,expected_technology_record_version,expected_dataset_id}`. expected_status_version=0 chỉ cho row chưa có; row đã có dùng positive version đúng. 200 cùng envelope GET nhưng record bắt buộc khác null, review_required=false; thêm đúng `audit_id` positive integer. Không 201/204/202. Mọi lần thành công tăng status_version đúng 1 và thêm đúng một audit. Replay request cũ =>409, không tự idempotent-retry.
3. `GET /api/cves/{cve_id}/technologies/{technology_id}/status-history?limit=25&cursor=...`. Query chỉ limit (default25, 1..100) và cursor. 200 đúng `{context,items,page,notice}`, page đúng `{limit,next_cursor}`. Item audit đúng `{audit_id,event,before,after}`; event=`created|changed`, before=null cho created, còn lại StatusRecord trước; after luôn StatusRecord. Mới nhất trước, audit_id giảm, không trùng; audit before/after giữ nguyên snapshot/note/actor/time. Lượt này chỉ history của key identity đang active; history của identity cũ/technology đã xóa vẫn lưu DB, giao diện tra lịch sử đã lưu trữ để sau.

Technology ID, version, audit_id: strict JS-safe integer, positive trừ expected_status_version cho phép0; không bool/fraction. Chặn overflow khi increment. CVE ID canonical regex W03-R, tối đa64. vendor/product/software_version theo bound W04; actor server subject 1..512. Note trim 1..1000 Unicode code points, từ chối Unicode Cc/control và surrogate không hợp lệ; hiển thị text escaped. Timestamp UTC thực dạng `YYYY-MM-DDTHH:mm:ss[.1..6digits]Z`, không parse lỏng. Dataset_id luôn lấy qua validation/fingerprint W03-R, không tin trường tùy ý client. Mọi JSON object wire reject extra/missing keys, cross-field sai =>unavailable ở reader, không tự sửa dữ liệu.

Body PUT tối đa16 KiB UTF-8 (đọc streaming bound dù Content-Length thiếu/sai), JSON malformed/duplicate key/extra field =>422. Response tối đa1 MiB UTF-8; không cắt mảng để giả thành công. Query raw max4096 bytes, cursor max1024 ASCII canonical base64url; reject query lặp/lạ và path ID sai trước store/port nhưng sau auth/quyền.

### Quyền và lỗi

Ba route mới chỉ cho `it|analyst|admin`, kể cả mixed-role với leader. Leader-only và role khác403 **trước query/body/DB/CVE port**; không có GET status/history cho Leader. JWT thiếu/sai401 trước mọi dependency dữ liệu; verifier unavailable503. Dùng verifier/role mapping có sẵn, không thêm identity header, không nhận actor/role trong body. GET `/api/cves` và summary cũ không thay đổi.

PUT order: auth+role → Origin → JSON media → path/query/body validation → configured dependencies → dataset validation → DB transaction/schema/context/version → ghi. Origin phải chính xác portal_origin (403 forbidden); media chỉ application/json, optional charset=utf-8 (415 unsupported_media_type). Mọi response no-store và Vary JWT như W03-R, kể cả lỗi mới.

Error envelope giữ dạng `_error` ở app.py, đúng error.code + message chung, **không thêm current status/context vào lỗi**. UI GET lại sau conflict; không lộ SQL/path/note/actor từ exception.

| HTTP/code | Trường hợp |
|---|---|
| 401 authentication_required | token thiếu/sai |
| 403 forbidden | role hoặc Origin sai |
| 413 request_too_large / 415 unsupported_media_type | body/media |
| 422 invalid_status_request | path/query/body/cursor structure/context không hợp lệ |
| 404 status_relation_not_found | GET status/history: active technology hoặc CVE exact match không tồn tại |
| 409 status_context_changed | PUT: technology mất/đổi version, dataset expected sai hoặc không còn exact match |
| 409 status_version_conflict | PUT: status expected sai; cả hai first-write race chỉ một được ghi |
| 409 status_snapshot_changed | GET history: cursor thuộc snapshot cũ |
| 503 status_unavailable | cấu hình/nguồn/DB/schema/validation/size/verifier không dùng được |

Nếu context và status version cùng cũ, context error ưu tiên. Mọi lỗi trước commit không làm đổi status/audit/W04. Không coi mất response sau commit là chứng cứ rollback.

### Lưu trữ và tính nhất quán

Store độc lập cùng SQLite path W04, không sửa bảng W04; migration additive riêng tạo status/audit/marker/index. `initialize()` chỉ chạy explicit ngoài request, yêu cầu W04 schema hợp lệ và DB đã có; schema thiếu một phần hoặc không đúng marker/index phải fail-closed, không tự vá trong request. Constructor/create_app không I/O/seed. Cấu hình status store mặc địnhNone; route trả503 sau quyền/validation, không ảnh hưởng `/api/cves` khi chưa bật status.

GET dùng mode=ro và read transaction: validate schema + đọc active technology + status/history cùng connection; không gọi TechnologyStore.list() trên connection khác rồi ghép snapshot. Bảo toàn B1 kiểm schema W04 đầy đủ. Dataset immutable lấy một lần/request; không I/O mạng. PUT dùng mode=rw (không tạo DB) và BEGIN IMMEDIATE; validate W04/status schema, lấy technology active và status hiện hành trên cùng connection. Kiểm context hiện hành trước DML; expected tech version phải bằng record_version hiện tại, dataset phải bằng snapshot đã validate, candidate phải exact-match vendor/product. Không dùng technology object đọc từ connection cũ làm thẩm quyền ghi.

Ghi status và audit trong cùng transaction, validate existing record trước mutation. Audit có before/after đầy đủ, actor/time/dataset nguồn; chỉ INSERT, không có API update/delete audit. Chuẩn bị/validate response trong transaction trước commit để lỗi serialize không biến thành ghi thành công ngoài ý muốn. Exception rollback/close; DB busy/corrupt/malformed rows503. Migration lỗi rollback toàn bộ phần mới. Không thêm process-wide secret/lock hoặc thay journal mode toàn cục.

History cursor là vị trí, không quyền: binds relation identity + role view + limit + dataset/technology context + status/audit snapshot. Wrong binding422, snapshot changed409; after audit_id phải tồn tại trong tập. Backend định nghĩa canonicalencoding trong docs/test, UI coiopaque. Mọi status mutation của relation hoặc thay technology/dataset làm cursor cũ409; không ghép trang khác snapshot. W03-R list cursor không bị status mutation làm đổi vì wire/list chưa chứa status.

Version/danh tính thay đổi: record cũ giữ nguyên. Cùng key mới version -> GET review_required, không tự ghi. Đổi key -> GET record=null, không lấy record từ key khác. Quay lại key cũ vẫn review_required vì record_version đã tăng. Xóa-tạo lại ID mới không kế thừa. Dataset đổi -> cần xem lại nếu vẫn match; không match ->404 GET/409 PUT. Ghi với context mới là quyết định con người mới, không tự đánh giá phiên bản.

## Frontend — độc lập theo s1

Tái dùng DetailPanel W03, thêm nút chọn một technology match để mở `CveStatusPanel`; chỉ một panel, không tự GET mọi quan hệ. Provider status riêng: read/save/history. HTTP client status cùng origin, không tự chèn JWT/actor/role/Origin; browser gửi Origin cho PUT, Content-Type JSON. Không đổi CveProvider/CVE DTO/list/ranking/filter hiện có. Summary không render panel và không gọi status/Technology API. Mẫu `/lo-hong/mau` dùng provider lưu memory có nhãn tổng hợp, tuyệt đối không HTTP mutation; route thật không fallback fixture.

Panel tải context mới trước mở form; stale selection/provider/filter response không có quyền sửa màn hình mới. Cho chọn status + note bắt buộc; hiển thị version hiện tại và snapshot đã ghi nếu cần xem lại. Không gọi patched/not_affected là kết luận tự động. History theo explicit nút, có phân trang và reload khi409.

Double-submit chặn; giữ pending/unknown theo provider + cve/technology qua đóng/mở panel, đổi tab/selection. Không để callback/refresh contextA ghi notice/loading củaB. Khi quay lạiA, chỉ GET đối soát, không PUT lại. PUT200 parsed đúng =>committed notice sống qua refresh503; GET reload không gửi mutation. Network/abort/5xx/response không hợp đồng/không parse được sau PUT =>unknown, không optimistic final status. GET thành công hiển thị trạng thái hiện tại rồi mới cho người dùng quyết định thao tác mới; **không khẳng định lần PUT chưa rõ là thành công chỉ từ GET**. 409 hiển thị cần xem lại, GET context mới và người dùng nhập/xác nhận lại; không auto-merge/replay. History read errors không làm mất trạng thái ghi đã xác nhận.

## Phạm vi file và kiểm chứng

Backend allowed: `portal_api/cves_status*.py`, `portal_api/app.py` chỉ injection/routes/headers/errors mới, `portal_api/tests/test_cves_status*.py`, `portal_api/tests/fixtures/w03-status-*`, `docs/specs/W03-status-local-contract.md`, `docs/adr/*w03-status*`, một mục `docs/PROGRESS.md`. Được import/tái dùng private helpers W03/W04, không sửa auth.py/technologies.py/cves.py/shared/deps/frontend/gateway. Nếu cần ngoài allowlist báo nhu cầu cụ thể, không tự refactor. API configuration explicit cho tests/local integration sau này.

Frontend allowed: `portal/web/data/cve-status*.ts`, `portal/web/components/cve-status*.tsx`, `portal/web/components/cve-app.tsx` và hai cve http/sample client để inject panel/provider, `portal/web/tests/*cve-status*`, `portal/web/tests/cve-app.test.tsx` hồi quy cần thiết, `portal/web/tests/fixtures/w03-status-*`, `portal/web/app/globals.css` chỉ style panel dùng token cũ, một mục `docs/PROGRESS.md`. Không backend/tools/deps/route redesign hoặc thay semantics W03-R/W04. Nếu cần helpers dùng adapter cục bộ, không refactor parser cũ.

Viết RED→GREEN focused tests trước code. Backend: first-write concurrency hai connection (một200/v1/audit1, còn lại409 khi serialization thành công), stale update/replay, mọi trạng thái/reopen/same-state với note, actor forgery/auth trước dependencies, Origin/media/body/bounds, missing/partial/schema mismatch/busy/corrupt, failure giữa DML và audit rollback, non-mutation SQL schema+row/version/audit trước/sau GET/failures, version/identity drift gồm đổi đi-đổi lại/deletion/recreate, dataset drift, history paging/invalidcursor. Test giới hạn response trước commit và source snapshot1lần. Focused status + W03-R + W04 technology và auth/API regression liên quan app.py; Ruff/format/diff. Không full suite lặp nếu không thay shared rộng.

Frontend: strict nullable/wire/extra fields/timestamp/bounds, GET caps kể cả thiếuContent-Length, mutation200only/unknown statuses, readonly summary/sample noHTTP, double-submit, known commit+GET503→200, unknownPUT+GET503→200 qua đóng/mở panel/provider/selection, 409 reload/reentry, history paging/snapshot, note escaping. Focused status + W03app/http + technology recovery khi tái dùng pattern; typecheck/lint/build/diff. Không tuyên bố browser/API tích hợp đã đạt.

Backend xuất wire từ API test thật: unset, committed, review_required, history2pages, conflict, unavailable; SHA256/manifest cùng README provenance. Frontend tự fixture theo đúng s1, không đọc tree Backend đang sửa. Mỗi bên báo base/HEAD/status/diff, command/exit/count, RED/GREEN và giới hạn; không sửa ROOT brief hoặc RUNS.

Output Backend `ROOT/PHONG-HOA-W03-STATUS-BACKEND-RESULT.md`, `ROOT/w03-status-backend-evidence/`; Frontend `ROOT/PHONG-HOA-W03-STATUS-FRONTEND-RESULT.md`, `ROOT/w03-status-frontend-evidence/`. Chỉ sau hai input được Leader review mới giao Engineer ghép trên tree thứ ba, gateway/body caps và kiểm browser cùng DB/trace. W03-S2 chưa được giao ở đây; project vẫn active. Mobile/live/lab/production không thuộc bằng chứng lượt này.
