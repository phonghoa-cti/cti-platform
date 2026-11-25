# W03 — nghiệm thu delta product256 và nối việc

Leader kiểm ngày 12/11/2026. HEAD tích hợp `867bdcaeffded177ee119fe5e05015c4700979db`, tree sạch, 9 file đúng phạm vi. Chấp nhận delta product256/WIRE-01 tại SHA tích hợp này; source Backend 1401402 riêng không chứa sửa LF và không được coi là bản tích hợp đã đạt.

Leader đọc diff, xác nhận 4 file chức năng/contract khớp commit Backend, đối chiếu capture product256 Unicode/vender128 và hai error envelope. 51/51 artifact khớp SHA256. Leader tạo clone mới bằng Git với `core.autocrlf=true`: fixture1361 byte/0 CR, hash89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73; chạy lại đúng test WIRE-01 tại clone mới: 1 passed, exit0, Python3.13.14 từ môi trường cti-w03-read-backend. Committed diff-check exit0. Raw output và kết quả tại leader-product256-review/. Clone kiểm chứng giữ trong thư mục đó, không có dịch vụ chạy.

Tái dùng log worker đã đối chiếu hash: Backend12 passed; Frontend7 passed; capture12 response; Ruff/diff-check đạt. Không tự nhận Leader chạy các suite này. Chặng A/B đã accepted trước và không kiểm lại. Không thay runtime UI/auth/audit, nên delta này không làm mất bằng chứng A/B. Toàn W03-S1 còn đóng tài liệu/cleanup bên dưới; W03-S2, mobile/feed/OpenCTI/lab/production chưa được nghiệm thu.

## Engineer — đóng tài liệu và tài nguyên cũ

Giữ thread b05471df-3a0c-49c0-b02b-4019e1cf15d4, một Sol medium trực tiếp tại tree cti-w03-status-integration dưới ROOT. Không chạy lại test chức năng/browser.

1. Sửa chỉ docs/PROGRESS.md để bỏ mâu thuẫn dòng product256 chưa kiểm, ghi đúng SHA/evidence local hiện tại; phân biệt browser A/B dùng lại, HTTP/parser mới và lab chưa kiểm. Không sửa source/runtime/contract/fixture.
2. Leader đã xác minh PID31176 là node chạy tools/local_integration/gateway.mjs của đúng tree này, parent32440, tạo06:04:48, port52963. Điều tra metadata/parent/run_id trong evidence của chính task để xác định quyền sở hữu. Chỉ dừng gateway/helper cũ khi khớp đúng task này, không còn người dùng và danh tính process/port được kiểm lại ngay trước thao tác. Không dừng theo tên node hoặc theo port chung. Nếu không chứng minh được thì giữ nguyên và báo blocker cụ thể. Không xóa dữ liệu/clone/evidence của người khác.
3. Commit docs cục bộ, tree sạch, diff-check; báo HEAD/diff và chứng cứ cleanup port/process/temp thuộc task, không nhận cleanup tất cả máy. Output PHONG-HOA-W03-S1-CLOSEOUT-RESULT.md trong thư mục brief này. Không sửa RUNS/push/PR/merge/deploy/cloud/lab. Đây là closeout nhỏ, không mở lại triển khai.

## Research — phần S2 độc lập, chỉ nghiên cứu

ROOT=`$WORKSPACE`.

Đọc source bằng Git tại ref867bdca ở ROOT/cti-w03-status-integration để không phụ thuộc docs đang sửa. Tái dùng ROOT/PHONG-HOA-W03-STATUS-RESEARCH-20261112.md và ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md, docs/specs/W03-lo-hong-anh-huong.md, W03-read-local-contract.md, W03-status-local-contract.md và W01-tong-quan.md. Đối chiếu nguồn chính thức phù hợp và PR mở theo quyền đọc sẵn; không sửa hoặc tạo PR.

Chọn lát cắt S2 nhỏ nhất để lọc trạng thái toàn danh sách và số tổng hợp cho Leader theo spec, chưa triển khai. Cần quyết định ngữ nghĩa CVE có nhiều technology, unset/review_required/technology inactive, hạn vá và timezone/null, quyền summary không lộ note/actor/technology, snapshot/cursor khi status đổi, ranking/KEV/count/pagination. Nêu 2–3 phương án, phần tái dùng, giới hạn, phương án đề xuất và điều cần Leader chốt; không tự coi status đã vá là bằng chứng vá thật. Trả contract/brief đủ ngắn để Backend/Frontend làm riêng và test tích hợp. Không thiết kế lại UI, mở rộng quyền, live feed/LLM/lab hoặc sửa source/ledger. Không tự giao tiếp người khác.

Chỉ ghi PHONG-HOA-W03-S2-RESEARCH.md vào thư mục chứa brief này, kèm nguồn/ngày kiểm/phần chưa xác minh. Research không phụ thuộc việc Engineer sửa docs, nhưng mọi triển khai S2 phải đợi Leader nghiệm thu/chốt hợp đồng.
