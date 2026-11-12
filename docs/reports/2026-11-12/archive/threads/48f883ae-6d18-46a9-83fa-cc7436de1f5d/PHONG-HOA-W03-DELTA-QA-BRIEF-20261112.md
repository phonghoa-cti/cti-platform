# W03-STATUS-DELTA-QA — kiểm hai đầu vào trước bước tích hợp

## Mục tiêu và hiện trạng

Kiểm độc lập phần mới của hai kết quả W03-S1. Không nghiệm thu lại chặng A hoặc mở rộng tính năng. Leader đã xem các cuộc mở: không có Leader khác đang chạy; hai worker liên quan idle. Lượt trước dừng lúc 07:41 sau lời thông báo sẽ giao QA; chưa thấy receipt hay task QA tương ứng. Đây là giao việc QA thực tế cho phần mới, không giao lại hai việc triển khai đã trả kết quả.

Một CTI QA Security, Sol medium, trực tiếp làm, không giao tiếp. Mã sản phẩm chỉ đọc; báo cáo và probe riêng ghi trong thư mục output bên dưới. Tối đa hai lần thử lại cùng nguyên nhân; báo rõ blocker nếu không thể kiểm trong phạm vi.

## Đường dẫn và ref cố định

Project root: `$WORKSPACE`.

- Backend: `PROJECT_ROOT\cti-w03-product-boundary`, HEAD `1401402122a58baa7dba2b3f1a75abc080baabab`, branch `fix/w03-product-boundary-20261112`.
- Engineer: `PROJECT_ROOT\cti-w03-status-integration`, HEAD `170a38bb92fee09bd2e917faedc8de6342046b54`, branch `feat/w03-status-integration-20261112`.
- Cùng base `d09929311b4b6447aac8b2ec6adac5999beda25d`.
- Báo cáo đầu vào: `$THREADS\783188b9-409e-47a1-b799-eab58c16854a\PHONG-HOA-W03-PRODUCT-FIX-RESULT.md` và `PHONG-HOA-W03-STAGE-B-REWORK-RESULT.md` cùng thư mục.
- Evidence Backend thực nằm ở `PROJECT_ROOT\w03-product-fix-evidence` (hai tài liệu RED-GREEN.md và FINAL-VERIFICATION.md; chưa thấy raw log trong thư mục này).
- Evidence B: `$THREADS\783188b9-409e-47a1-b799-eab58c16854a\w03-status-stage-b-rework`.
- Output duy nhất: `$THREADS\48f883ae-6d18-46a9-83fa-cc7436de1f5d\w03-delta-qa-evidence` và `PHONG-HOA-W03-DELTA-QA-RESULT.md` ở thư mục cha của evidence.

Đọc AGENTS.md, docs/PROGRESS.md và contract W03 trên đúng ref. Nghiên cứu/quyết định dùng lại: `783188b9-409e-47a1-b799-eab58c16854a\PHONG-HOA-W03-NEXT-DECISION.md`, brief product cùng thư mục. Product W03 256 Unicode code point, vendor vẫn 128; không thay normalization/auth/audit.

## A. Backend và lỗi wire nền

1. Chụp HEAD/status trước/sau; đọc diff 5 file từ base. Kiểm delta chỉ nâng affected product và test/doc tương ứng, không mở rộng policy.
2. Chạy selector focused ghi trong FINAL-VERIFICATION.md (worker báo 12 PASS), giữ output thô/exit thực. Dùng Python của checkout `.venv` nếu có; nếu phải dùng interpreter chia sẻ sẵn `PROJECT_ROOT\cti-w03-read-backend\.venv\Scripts\python.exe`, xác nhận module portal_api import đúng tree candidate. Không cài dependency hay chỉnh môi trường chung.
3. Tái hiện riêng `test_checked_in_wire_fixtures_equal_real_api_responses`, không chạy lại cả suite. Kiểm bytes fixture checkout so với Git blob ở base và candidate, đối chiếu field-level chênh lệch. Báo có đúng chỉ dataset_id/hash vì CRLF/LF không; không mặc nhiên tin báo cáo worker.
4. Nếu cần chứng minh LF làm test đạt, chỉ tạo bản sao thử nghiệm ở output riêng, giữ source và fixture gốc bất biến. Không sửa product hash logic hay nới assertion chỉ để xanh. Đề xuất sửa nhỏ nhất để checkout sạch tái lập đúng bytes; chưa triển khai đề xuất.

## B. Bằng chứng khóa ghi sau remount

1. Review delta helper/scenario từ d099293 tới 170a38b (5 file, +50); chỉ test harness, không thay gateway/product semantics.
2. Đối chiếu manifest 27 file, hash/size, HEAD và run ID. Đọc trace gốc, ảnh, accessibility/DOM, SQLite ở chế độ chỉ đọc; không coi summary tự khai là bằng chứng đủ.
3. Chứng minh cùng run: GET200 ban đầu -> PUT503 sau commit -> GET503 tự động -> GET503 sau đóng/mở lại -> GET200 khi bấm đối soát. PUT đúng 1, tải /lo-hong đúng 1; trạng thái khóa được quan sát trước GET200, không có select/note/save trong vùng status; sau đó thấy patching/v1/note/actor đã lưu. SQLite từ 0/0 thành 1 record/1 audit, khớp trace.
4. Kiểm cleanup từ bằng chứng và kiểm nhanh PID/port/temp còn tồn tại hay không; không dừng tiến trình không xác định. Không khởi động browser, helper hoặc chạy lại chặng A khi evidence đủ. Nếu thiếu, nêu đúng khoảng trống và ca tối thiểu cần bổ sung.

## Kết quả phải trả

- PASS/FAIL/UNVERIFIED riêng cho delta Backend, nguyên nhân lỗi wire, và ca B. Không tuyên bố toàn W03-S1 hoàn tất, không ghép hai nhánh.
- SHA/base, phạm vi diff, lệnh/exit/count, raw logs, hash và đường dẫn evidence; HEAD/status không đổi sau kiểm.
- Findings có mức độ, cách tái hiện, sửa tối thiểu; ghi rõ việc nào cần Engineer làm khi tích hợp product256/257. Chặng A/accepted_results giữ nguyên.
- Không sửa RUNS, không commit vào tree nguồn, không push/PR/merge/deploy, không lab/cloud/LLM thật, không secret hay dữ liệu thật. Chỉ nguồn tổng hợp cục bộ được cấp.
