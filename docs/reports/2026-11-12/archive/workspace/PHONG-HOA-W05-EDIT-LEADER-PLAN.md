# W05-EDIT — nghiệm thu nghiên cứu và quyết định triển khai của Leader

Ngày 11/11/2026, khoảng 03:16 giờ Việt Nam. Kết luận: **ACCEPTED RESEARCH với các chốt bên dưới**; chưa có implementation hoặc test selection mới. Khi khác với brief Research, áp dụng quyết định trong tài liệu này. Giữ nguyên hai tài liệu nghiên cứu để lưu nguồn gốc.

## Bằng chứng review

- Request `e45b4f57-6081-46f6-b8d8-5fb470fae853`, hai file tồn tại và đọc đủ. Research SHA256 `f8dab592a594bab8a1a72e99ecbc5d0728937ae39ef756fc4fc1473ebca6b4ba`; implementation brief SHA256 `3249f7d25f904f1013b1c18465ca1a0a8cd3d0425493965161a3bbdbc2f83fdc`; khớp báo cáo.
- Nguồn chính `cti-w05-local-integration` sạch, HEAD `d94afb1e24929f64f82a921cd29307be175fb04e`. Leader đối chiếu store validation/migration/read/decision, API schemas/service và TypeScript parser. Không chạy lại test sản phẩm cho hai tài liệu nghiên cứu.
- Đã mở nguồn chính thức [SQLite transaction](https://sqlite.org/lang_transaction.html), [foreign keys](https://sqlite.org/foreignkeys.html), [ADD COLUMN](https://sqlite.org/lang_altertable.html#alter_table_add_column), [OpenCTI draft workflow](https://docs.opencti.io/latest/usage/draft-workflow/) ngày 11/11. SQLite chỉ có một write transaction; BEGIN IMMEDIATE có thể busy, FK bật theo connection. Các điểm này hỗ trợ lựa chọn transaction/FK, không tự chứng minh mã sắp viết đúng. OpenCTI chỉ dùng làm tham khảo mô hình, không suy khả năng lab/license.

## Lựa chọn và các chốt bắt buộc

Chọn phương án C: giữ `draft_audit` một final decision/draft, thêm `draft_selection_audit` cho các lần save có thay đổi. Giữ payload nguồn bất biến và item index ổn định trong draft. Không tạo hệ thống event sourcing tổng quát, không thêm dependency.

1. **Migration là tương thích bắt buộc.** Không chọn nhánh tùy ý từ chối tất cả v0 như brief gợi ý. Giữ `save_draft` tạo DB mới schema v2; `migrate_store` hỗ trợ schema v0 hợp lệ và v1 hợp lệ sang v2 nguyên tử, v2 idempotent. Không commit trạng thái v1 trung gian. `get_draft`/`list_drafts` vẫn đọc v0/v1 không sửa DB như trước; chức năng selection mới yêu cầu v2. Mọi lỗi schema/DDL/commit phải rollback; schema giả/mixed/future không tự sửa. Test cả v0, v1 pending/terminal, DB mới, v2 lặp và injected failure sau ALTER.

2. **Version và snapshot có invariant rõ.** Với draft v2 pending: `review_version == selection_version`; terminal: `review_version == selection_version + 1`. Các save có hiệu lực tạo selection version liên tiếp từ 1, mỗi event có review version tương ứng. Version 0 chỉ dùng baseline khi thật sự không có event. Pointer/version lệch, thiếu event, JSON/hash không hợp lệ hoặc indices không eligible phải lỗi, không fallback về giữ toàn bộ. Kiểm chính xác integer, không bool, và không tăng vượt miền INTEGER SQLite. No-op chỉ sau kiểm quyền/pending/expected_version, `changed=False`, không event/version mới. Getter trả `changed=False`, cùng author/time của save gần nhất (baseline None).

3. **Đọc selection cũng cần snapshot nhất quán.** `get_effective_selection` dùng connection read-only và read transaction khi đọc drafts + event qua nhiều query, để một save xen giữa không tạo cặp version/lựa chọn khác thời điểm. Test interleaving có kiểm soát, không test may rủi bằng sleep. Save và decision dùng BEGIN IMMEDIATE, kiểm expected_version rồi update/audit/commit cùng transaction; giữ nghĩa lỗi lock và stale khác nhau.

4. **Snapshot của cả hai quyết định mới.** Mọi approve/reject mới ở v2 ghi đủ selection_version/canonical indices/hash vào final audit; reject vẫn yêu cầu reason và được phép với selection rỗng. Điều này thay phần “reject mới để NULL” của Research. Audit lịch sử migrate v1 giữ ba cột NULL, không bịa lịch sử. Có thể suy trước/sau một save từ baseline hoặc event trước và event hiện tại; không nhân bản text/evidence vào audit. App không sửa event đã ghi; không tuyên bố bảo vệ trước người có quyền sửa trực tiếp DB.

5. **Count không được đặt tên sai.** Research gọi số eligible là “AI extracted”; đổi thành hai số riêng: `ai_extracted_count = số items kind=ioc trong payload`, `ai_eligible_count = số eligible IOC ban đầu`. `human_deselected_count = eligible - selected`; `selection_save_count = số save có thay đổi`. Bổ sung bốn trường này vào DraftSelectionResult của brief; không thêm vào shape get/list hiện tại. Thêm IOC người dùng chưa hỗ trợ, không công bố metric chất lượng hay Precision/Recall. Test có cả IOC đủ điều kiện và bị loại để hai count không bị nhập một.

6. **Eligibility/policy giữ chặt.** Chỉ kind=ioc, keep=true, status=ok và payload vượt validator hiện có. Không hồi sinh allowlist/bia/keep=false, không nhận trusted flags client. Giữ unsupported-kept-kind và self-approve policy hiện tại; chỉnh lựa chọn không đổi creator và không tự thêm yêu cầu hai reviewer. Empty save được, empty approve không được. Malformed input phải trả typed error trước mọi mutation, kể cả list/dict/null/bool ở giá trị scalar; không TypeError/traceback ngoài dự kiến.

7. **Tách đúng trạng thái core và API.** Giữ shape `get_draft`/`list_drafts` hiện tại; `items.keep` ở đây vẫn là extraction ban đầu, getter selection riêng trả lựa chọn hiệu lực. `_decode_review` phải hỗ trợ version tăng trong v2, không nới invariant v1 cũ một cách mù quáng. API hiện khóa summary version=0, detail<=1, decision=1; TypeScript cũng kiểm các giới hạn đó. Vì vậy branch core này **chưa tương thích HTTP/UI cho draft đã edit**; không được báo “API giữ nguyên nên đã tương thích”. Chỉ demo bằng core và DB tổng hợp riêng, không cho portal hiện tại dùng DB selection. Tree tích hợp đã nghiệm thu d94 giữ nguyên. API/UI tiếp theo sẽ thay contract/version và hiển thị effective selection trước khi nối, không đổi version giả về 0/1 để qua parser.

## Giao CTI Backend — W05-EDIT-IMPLEMENT

Root output: `$WORKSPACE`.

- Một implementer Sol medium, không giao thêm bot/agent. Tạo **worktree mới** `<root>\cti-w05-selection`, branch `feat/w05-selection-local-20261111`, base `d94afb1e24929f64f82a921cd29307be175fb04e`. Leader đã thấy path/tree chưa tồn tại khi review; kiểm lại trước tạo, không ghi đè/reset nếu xuất hiện. Không sửa các tree nguồn.
- Đọc AGENTS.md, docs/PROGRESS.md, spec W05, Research và brief triển khai rồi tài liệu này. User đã cho tiếp tục kỹ thuật cục bộ/nhánh riêng; không cần hỏi lại cho lựa chọn đảo ngược trong phạm vi.
- Được sửa: `extractor/phonghoa_extractor/store.py`; thêm `extractor/tests/test_selection.py`, `test_selection_migration.py` nếu giúp tách test; sửa tests store/review/queue/CLI liên quan trong `extractor/tests/` khi schema/version thật sự thay đổi. Không xóa test cũ hoặc làm yếu assertion quyền/atomicity chỉ để xanh.
- Cho phép cập nhật `docs/PROGRESS.md`, thêm `docs/adr/0014-w05-selection-snapshots.md` (nếu số trùng chọn số kế, không ghi đè), và bổ sung phần contract selection lõi trong `docs/specs/W05-draft-offline-contract.md`. Đây là ngoại lệ rõ cho mục cấm docs của brief Research, nhằm giữ quy ước repo.
- Giữ nguyên `portal_api/**`, `portal/web/**`, harness, dependency/lock, core IOC, model/evaluator và các tài liệu/RUNS/probe của Leader. Không sửa CLI sản phẩm hay thêm HTTP handler trong lượt này.
- Có thể dùng interpreter hiện có `<root>\cti-w05-local-integration\.venv\Scripts\python.exe` **chỉ chạy**, cwd/PYTHONPATH phải trỏ tree mới và xác minh module store được import từ tree mới. Không cài/sửa môi trường chung. Dùng `-B`, pytest `-p no:cacheprovider` khi phù hợp.

## TDD, kiểm thử và bàn giao

Viết test mới trước sửa, giữ RED chứng minh failure đúng mục tiêu rồi GREEN. Áp dụng 24 ca Research, sửa #16 theo snapshot reject và mở rộng migration/consistency/read-race/count ở trên. Test concurrency dùng hai connection với đồng bộ có kiểm soát; đúng một write thắng cho cùng expected_version, không event lạc. Có rollback khi event INSERT/final audit INSERT/commit lỗi, DB lock timeout, schema giả thiếu UNIQUE/FK/check, event JSON/hash/version lỗi, no-op stale/terminal, payload byte-identical và read-only không tự migrate.

Chạy nhóm selection/migration/review/store/queue/CLI; sau đó **full Python suite một lần** vì đổi store dùng chung, gồm API baseline chưa edit để bắt regression cũ. Không tuyên bố suite API baseline chứng minh API hỗ trợ selection. Nếu test cũ fail, phân biệt thay đổi policy đã chốt với bug, không sửa file ngoài scope cho xanh. Ruff/check-format các file đổi và diff-check. Không chạy UI/build/browser/HTTP listener trong slice core này.

Demo SQLite tổng hợp: 2 eligible và 1 excluded; save một IOC, đọc getter, approve đúng expected_version; query event/final audit khớp hash/version và payload nguyên vẹn. Có reject sau save và empty-approve denied. Mọi DB demo trong thư mục tạm do mình tạo và dọn đúng ownership; không dùng DB thật.

Commit cục bộ Conventional Commit, tree sạch. Chỉ ghi output ngoài tree vào `<root>\PHONG-HOA-W05-EDIT-RESULT.md` và `<root>\w05-selection-evidence\` (RED/GREEN, demo, checks, manifest SHA256). Báo base/HEAD/branch, diff, exit/count thật, matrix PASS/FAIL/UNVERIFIED, giới hạn core-only/API mismatch và dữ liệu tổng hợp. Không push/PR/merge/deploy, secret/model/cloud/lab hoặc đổi quyền. Nếu có blocker cụ thể ngoài scope, báo bằng chứng cho Leader, không tự mở rộng.

Leader sẽ nghiệm thu đúng commit rồi chọn bước API/contract tiếp. Lịch dự phòng đã đọc trong lượt, còn bật; không có Leader khác đang làm. Dự án tổng vẫn active.
