# W05 tiếp theo sau hàng đợi SQLite: quyết định cục bộ và nhật ký kiểm tra

**Ngày kiểm:** 10/11/2026. **Phạm vi:** nghiên cứu và brief trước lab; không chạy test, không sửa repo, không gọi OpenCTI/cloud/LLM.
**Ref đã đọc:** `cti-platform-start`, nhánh `feat/x01-draft-queue-20261110`, HEAD `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`; `git status --short --branch` sạch lúc bắt đầu.

## Câu hỏi quyết định

Sau khi đã tạo → lưu → liệt kê/đọc bản nháp `pending` trong SQLite, lát cắt nào nhỏ nhất nhưng làm luồng W05 tiến gần việc con người thực sự chịu trách nhiệm: siết dữ liệu vào, ghi quyết định duyệt/từ chối có audit, hay mở API đọc có quyền?

## Hiện trạng đã kiểm trong đúng ref

- `store.py` chỉ chấp nhận payload schema `1.0`, `status="pending"`; `save_draft()` chỉ thêm bản ghi, còn `get_draft()`/`list_drafts()` mở SQLite read-only. Bảng `drafts` hiện có `id`, `created_at`, `payload_json`, `schema_version`, `status`, `source_sha256`; không có chủ thể tạo/duyệt, version, migration hay audit.
- Hợp đồng `W05-draft-offline-contract.md` xác nhận chưa có cập nhật/chuyển trạng thái/ghi đè; `kind` và `item.status` chưa bị allowlist hoàn chỉnh. `api-portal.md` cũng nói endpoint W05, HTTP, auth, approve/reject chưa hoạt động.
- Các test `extractor/tests/test_store.py` và `test_queue.py` đã bao phủ hash/span, đọc lỗi, timeout, cursor và không tạo DB khi đọc. Chúng chưa chứng minh quyết định, danh tính, transaction audit, HTTP, Cloudflare Access, UI hay OpenCTI.

## Đối chiếu nguồn và phần tái sử dụng

| Nguồn đã kiểm ngày 10/11/2026 | Ai đã làm / điều kiểm chứng được | Dùng lại được | Giới hạn đối với Phong Hỏa |
|---|---|---|---|
| [OpenCTI Draft workspaces](https://docs.opencti.io/latest/usage/draftWorkspaces/) | OpenCTI tách draft khỏi knowledge base, có review diff; approve chuyển draft sang validated và đưa thay đổi vào ingestion. | Dùng **mô hình vòng đời**: sửa/so sánh trước, rồi mới quyết định; ghi rõ pending/validated. | Không có lab/version/license để xác minh API hay quyền. `approve` của OpenCTI có nghĩa nhập knowledge, nên không được gọi từ lát cắt SQLite hoặc gán cùng ý nghĩa cho local state.
| [OpenCTI Draft workflow](https://docs.opencti.io/7.260914.0/usage/draft-workflow/) và [Users/RBAC](https://docs.opencti.io/latest/administration/users/) | Workflow có thứ tự trạng thái, hạn chế người được chuyển trạng thái; một số capability workflow/draft phụ thuộc Enterprise Edition. | Dùng nguyên tắc “policy transition” tách khỏi UI. | Không lấy đây làm bằng chứng OpenCTI Community/lab sẽ ép two-person approval; policy cục bộ vẫn cần test riêng.
| [SQLite transactions](https://sqlite.org/lang_transaction.html), [foreign keys](https://www.sqlite.org/foreignkeys.html) | SQLite có `BEGIN`/`COMMIT`/`ROLLBACK`; foreign key phải bật cho từng connection, không nên dựa vào mặc định. | Một transaction cho update state + audit; `PRAGMA foreign_keys=ON` trước transaction; FK/index trong schema mới. | SQLite không xác thực danh tính và không làm audit bất biến trước người có quyền ghi file DB.
| [Cloudflare Access application token](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/application-token/) | Header đơn lẻ không đủ: origin phải xác thực JWT/signature; JWT có `sub` và email từ IdP. | Thiết kế interface nhận subject opaque đã xác thực để sau này adapter HTTP map từ JWT `sub`. | Chưa có Cloudflare Access, team domain, AUD hay portal HTTP. Một hàm nhận `actor` ở offline chỉ là policy-test, **không** là production auth.
| [JSON Schema validation](https://python-jsonschema.readthedocs.io/en/latest/validate/) | `Draft202012Validator` kiểm schema; format không tự được enforce nếu không gắn format checker. | Có thể dùng sau cho biên HTTP/schema công khai. | Chưa cần thêm dependency để quyết định cục bộ: validator bespoke hiện có mới là nguồn thực thi payload 1.0; không được tự nhận JSON Schema đã bảo vệ API.

## Ba lát cắt có thể làm tiếp

| Phương án | Lợi ích / phần tái sử dụng | Khoảng trống và rủi ro | Đánh giá |
|---|---|---|---|
| A. Siết schema đầu vào | Bổ sung allowlist `kind`/`item.status`, có thể công bố JSON Schema. Tận dụng `_validate_draft`. | Chưa tạo quyết định của người, audit hay đường đi ra OpenCTI; thêm dependency/contract mới có thể rộng hơn dữ liệu C1 hiện chỉ IOC. | Nên làm **trong biên quyết định** ở mức từ chối item không hỗ trợ khi có chỉnh sửa, nhưng không phải lát cắt kế.
| B. Lõi quyết định cục bộ approve/reject + audit (**khuyến nghị**) | Nối trực tiếp hàng đợi hiện có với human-in-the-loop; tái dùng SQLite, validation/read-only, test rollback/lock; tạo điểm kiểm chứng được trước HTTP/UI/OpenCTI. | Phải có migration an toàn, optimistic concurrency và mô hình danh tính rõ; chưa phải authentication hoặc ingestion. | Nhỏ nhất có giá trị: con người có thể tạo một quyết định có trace thay vì chỉ xem `pending`.
| C. API đọc có quyền | Có thể làm UI W05/Antigravity lấy queue thật và buộc role Analyst/Admin. | Chưa có portal HTTP/auth thật; dễ biến header/email client thành giả danh tính; vẫn không có transition/audit. | Để **sau B**. B cung cấp transaction/state/audit để API chỉ là adapter mỏng, giảm rủi ro lặp logic.

## Quyết định đề xuất: B — lõi quyết định cục bộ, không nhập OpenCTI

Tạo một API Python nội bộ (không HTTP) để một `pending` draft được **duyệt cục bộ** hoặc từ chối, đồng thời ghi audit trong **cùng transaction**. “Đã duyệt cục bộ” chỉ nghĩa là người duyệt đã ra quyết định trên dữ liệu offline; không gọi OpenCTI, không tạo Report/STIX và không được UI ghi “đã nhập”. Lát cắt kế sau mới quyết định mapping/nhập OpenCTI theo version/lab thực tế.

### Dữ liệu, danh tính và policy

- Giữ nguyên payload `schema_version="1.0"` và `payload.status="pending"` như evidence bất biến. Không đổi status trong `payload_json`; thêm state review ở metadata SQLite để không làm hỏng `_validate_draft()`/hash/span hiện có.
- Bảng/metadata mới tối thiểu: `review_status` (`pending|approved|rejected`), `review_version` (từ 0), `created_by_subject` nullable, `decided_by_subject`, `decided_at`, `decision_reason`; bảng `draft_audit` có `draft_id`, timestamp UTC, actor subject, action, expected/actual version và snapshot metadata trước/sau (không sao chép `text`, `evidence`, `findings` vào audit).
- Subject là định danh opaque ổn định (về sau là JWT `sub`), không lấy email/header do client tự gửi. Offline core nhận `Actor(subject, roles)` do caller cung cấp chỉ để test policy. Chỉ `analyst`/`admin` được quyết định; không tự duyệt khi `created_by_subject` đã biết và trùng subject. Đây là hàm policy đã test, không phải kiểm chứng xác thực sản xuất.
- Draft cũ 1.0 không có creator: migration đặt `created_by_subject=NULL`, `review_status=pending`, `review_version=0`. Để không biến dữ liệu thiếu provenance thành quyết định đáng tin, chúng **không được approve**; có thể reject có lý do, hoặc chờ lát cắt ownership-attestation có audit riêng. Đây là mặc định bảo thủ và đảo ngược được bằng một thao tác có audit, không tự gán email.
- `reject` bắt buộc lý do không rỗng sau trim; `approve` không nhận lý do tự do. Một draft chỉ quyết định từ `pending` một lần; lần lặp/stale `expected_version` trả conflict và không thêm audit.

### Transaction, migration và tương thích

1. Trước transaction, validate kiểu/roles/subject/reason/expected version. Với connection ghi, bật `PRAGMA foreign_keys=ON`; bắt đầu `BEGIN IMMEDIATE`.
2. Migration có version rõ bằng `PRAGMA user_version`: tạo/`ALTER` schema và index trong transaction, backfill metadata legacy, sau đó mới tăng version. Kiểm tra migration idempotent; nếu lỗi rollback thì DB không ở trạng thái nửa cũ/nửa mới. Không đổi hay diễn dịch lại `payload_json` 1.0.
3. Đọc row hiện tại, xác minh payload vẫn hợp lệ bằng `_decode_draft_row`, kiểm `review_status=pending` và `review_version=expected_version`; policy self-approval; sau đó `UPDATE ... WHERE review_status='pending' AND review_version=?` và `INSERT draft_audit` cùng transaction. Không có hai transaction riêng cho state/audit.
4. `list_drafts()` vẫn chỉ hiện review pending sau migration; summary bổ sung `review_status`/`review_version` theo hợp đồng cập nhật. `get_draft()` trả payload nguyên vẹn cộng metadata review tách tên, không làm payload trông như STIX/OpenCTI đã duyệt.

## Rủi ro còn lại và thứ tự sau nghiệm thu

| Rủi ro / chưa rõ | Cách giữ phạm vi | Việc sau B |
|---|---|---|
| Danh tính production chưa tồn tại | Chỉ `Actor` injected trong test; không tin email client/header. | Adapter HTTP xác thực JWT Access (issuer, signature, audience) hoặc key hash; map role server-side; kiểm 401/403/self-approval.
| OpenCTI draft có semantics/license/version chưa kiểm lab | Không gọi API/OpenCTI trong B; không giả lập Report. | Lab xác minh version/capability/role rồi design outbox/retry idempotent, tách transaction SQLite khỏi remote ingestion.
| Audit SQLite có thể bị admin file DB sửa | App audit là trace vận hành, không gọi là tamper-proof. | Threat model/backup/quyền file, export audit hoặc append-only storage nếu scope yêu cầu.
| Item schemas tương lai TTP/malware/actor | Không mở rộng payload C1 vô căn cứ. | A: versioned boundary allowlist/schema khi có dataset và contract item mới.
| Không có UI | Không thiết kế UI ở lát cắt này. | Handoff cho Antigravity chỉ sau B: state/role/error/evidence contract đã rõ.

## Trạng thái bằng chứng

- **Đã kiểm trực tiếp:** ref/status nêu trên; spec, source `store.py`/`drafts.py`, và test hiện có; nội dung tài liệu nguồn ở các liên kết.
- **Suy luận/đề xuất:** schema metadata, trạng thái, default legacy, interface `Actor`, transaction/migration và thứ tự làm.
- **Chưa kiểm:** test của lát cắt mới, FastAPI/HTTP, JWT, UI, OpenCTI/lab, license/version OpenCTI thực tế, hiệu năng/đa tiến trình ngoài test SQLite.
