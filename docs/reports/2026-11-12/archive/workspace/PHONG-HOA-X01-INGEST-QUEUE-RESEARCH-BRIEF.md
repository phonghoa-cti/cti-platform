# X01-INGEST-QUEUE-NEXT — nghiên cứu cầu nối vào hàng chờ

Ngày 11/11/2026. CTI Research đọc nguồn và viết đúng hai tài liệu; chưa triển khai, không giao tiếp bot khác. Mục tiêu mẹ: TXT/PDF tạo bản nháp có bằng chứng rồi vào hàng chờ người duyệt, không tự ghi OpenCTI.

Root tuyệt đối: `$WORKSPACE`.

## Nguồn chỉ đọc và quyết định đã có

1. `<root>\cti-x01-ingest-local`, `feat/x01-ingest-local-20261111`, HEAD `8a16758601647fb3dbf935abecc2435f3b7a3fb6`. Leader vừa nghiệm thu 81 test tại HEAD. Đọc AGENTS, `docs/specs/X01-ai-extractor.md`, `extractor/ingest/run.py`, `extractor/phonghoa_extractor/local_ingest.py`, drafts/store và tests liên quan. Envelope `x01-local-ingest/1.0` gồm input metadata và draft schema 1.0; raw hash khác canonical text hash; span luôn trên canonical text. Loader đã được nghiệm thu, không thiết kế lại PDF parser.
2. `<root>\cti-x01-w05-stix-e2e`, `feat/x01-w05-stix-e2e-20261111`, HEAD `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`. Leader vừa xác nhận sạch. Đọc AGENTS, store/review/selection, CLI draft, contract W05 và demo E2E liên quan. Store schema 2, khác store legacy ở nhánh AI; không giả định hai branch đã gộp. Existing save/list/get, selection/final audit và STIX phải giữ đúng hành vi đã nghiệm thu.
3. Root: `PHONG-HOA-X01-LOCAL-INGEST-IMPLEMENTATION-ACCEPTANCE-20261111.md`, `PHONG-HOA-X01-LOCAL-INGEST-LEADER-PLAN.md`, `PHONG-HOA-X01-QUEUE-BRIEF.md`, `PHONG-HOA-X01-W05-STIX-E2E-RESULT.md`. Kế thừa nghiên cứu còn phù hợp; báo cáo nghiên cứu/test cũ không thành bằng chứng triển khai cầu nối mới.

Kiểm HEAD/status trước và sau; nếu khác ref, báo chênh lệch, không checkout/reset/sửa source. Chỉ đọc phần cần cho cầu nối, tránh nghiên cứu lại toàn dự án.

## Câu hỏi cần chốt

So tối đa ba cách nhỏ: import envelope có sẵn vào queue; tích hợp save trực tiếp trong ingest CLI; hoặc một thành phần riêng thực sự cần thiết. Ưu tiên tái dùng validators/store/transaction đã có, không lặp parser và không kéo toàn nhánh AI vào W05. Chọn một cách, giải thích phần tái sử dụng và giới hạn, có nguồn chính thức SQLite/Python và code ref cụ thể. Leader quyết định cuối sau review tài liệu.

Brief triển khai phải tự đủ cho một Sol medium làm trên tree mới:

- Chọn exact base/target/branch, các file đọc/sửa, phần mã cần mang sang nếu có và cách kiểm provenance của chúng. Không tạo tree hoặc cherry-pick/merge trong nhiệm vụ nghiên cứu này.
- Chốt CLI/library DTO, strict JSON/exact types/keys/bounds và thứ tự lỗi. Đối chiếu input metadata với draft name/text/hash/ranges, language/TLP, giữ payload và `items.keep` bất biến. Envelope là dữ liệu không tin cậy. Raw SHA tự khai không chứng minh bytes PDF gốc khi cầu nối không đọc raw; phải nói rõ và không nâng mức tin cậy.
- Bảo toàn raw hash, canonical hash, format/ranges và liên kết với draft ID khi lưu; chọn schema/phụ lục nhỏ nhất. Nếu migration cần thiết, định nghĩa version, compatibility, idempotence, malformed schema, rollback; đọc không tự ghi/migrate. Không làm hỏng store v2/selection/audit/STIX hiện hữu.
- Lưu draft cùng provenance nguyên tử trong một transaction. Chốt nhập trùng/retry/concurrency, khóa định danh dùng dữ liệu nào, lỗi giữa commit và phản hồi; không tuyên bố exactly-once nếu thiết kế không chứng minh. Không tự sửa hoặc duyệt draft cũ khi gặp trùng.
- Không dựa vào đường dẫn file nguồn có thể thay đổi để lấy nội dung sau validation; đọc giới hạn, alias DB/input/output/sidecars, local path policy và timeout hữu hạn; tái dùng boundary đã có khi phù hợp. Không thêm file đầu ra nếu chỉ summary stdout là đủ. Không log raw CTI, full path hay secret.
- Đề xuất test matrix: hợp lệ TXT/PDF envelope có Unicode, dữ liệu sửa/hash lệch/types sai/deep JSON/duplicate keys; provenance không mất; failed write rollback; duplicate/race; schema cũ/mới; list/get chỉ pending; giữ review/selection/legacy CLI. Phân biệt test giả lập lỗi, test process thật và chưa kiểm.
- Chốt lệnh TDD/regression/lint cần thiết, môi trường Python riêng hoặc đã có, demo tổng hợp cùng envelope→queue→get đối chiếu provenance (không mạng/listener/browser), nơi report/evidence/manifest và acceptance matrix. ADR/PROGRESS theo đúng AGENTS. Chỉ đề nghị local commit sau checks; không push/PR/merge/deploy.

## Hai đầu ra được phép

- `<root>\PHONG-HOA-X01-INGEST-QUEUE-RESEARCH.md`.
- `<root>\PHONG-HOA-X01-INGEST-QUEUE-IMPLEMENTATION-BRIEF.md`.

Không sửa RUNS, review/acceptance, source code, cấu hình, dependency hay corpus. Không cài package, tải PDF/corpus, mở DB thật, chạy implementation/test sản phẩm, tạo listener, dùng model/cloud/lab/secret. Không tạo task tiếp hoặc giao bot khác. Nguồn web chính thức dùng để nghiên cứu là được phép.

Bàn giao hai đường dẫn tuyệt đối + SHA-256, refs/status trước–sau, phương án chọn và phần UNVERIFIED. Tự rà contract đủ rõ để Sol không phải đoán dữ liệu, migration hoặc test. Nghiên cứu không được ghi là đã chạy luồng sản phẩm.
