# W05 Selection UI — kiểm lại R1–R5, phát hiện R6

Ngày 11/11/2026, khoảng 05:16 giờ Việt Nam. **NEEDS_FIX R6**; không nghiệm thu UI trước khi sửa lỗi phân trang mới.

## Phạm vi và bằng chứng

- Task `W05-SELECTION-UI-IMPLEMENT`, kết quả rework request `b6fa6556-7755-4282-8499-5398269d138e`.
- Tree `$WORKSPACE\cti-w05-selection-ui`.
- HEAD `def7622676d43b8b13578edefb0bae063ad357df`, branch `feat/w05-selection-ui-20261111`, sạch; rework từ `2276f49399ae2cd5ae40963622a3d9b70bcf1d3c`: 5 file, +183/-25.
- Leader đọc diff rework và chạy lại probe R1–R5 nguyên trạng: **15/15 PASS, exit 0**. Log/JUnit mới: `w05-selection-ui-evidence/leader-recheck.log`, `leader-recheck.xml`. Probe hash không đổi: `10E2C8589B5935428F3E4D4DEC1AB018AD3C969BD6308E3D62EB97619150F93A`.
- Leader kiểm manifest rework: **36 mục, 0 mismatch**. Đã đọc raw JUnit full Vitest của worker: **86 tests, 0 failures, 0 errors**; raw log typecheck/lint/build và các exit-file đều 0. Đây là bằng chứng worker đã chạy; Leader không chạy lại full/build.
- Leader thêm probe R6 ngoài repo, dùng deferred Promise, không sleep: **2 tests, 2 failures, 0 setup/import errors, exit 1**. Cả success và error đều để lại nút `Đang tải thêm…` disabled sau khi request đã kết thúc.
- Probe R6: `w05-selection-ui-evidence/leader-pagination.test.tsx`; SHA256 `9AE5EC4FFF3C6E7E1525ED3A0837C008745C41FC582CC58FFE8B462A205915F9`. Config `leader-pagination.config.mjs`; bằng chứng `leader-pagination-red.log`, `leader-pagination-red.xml`, `leader-pagination-red.exit.txt`.
- Leader không sửa mã sản phẩm. Những lỗi R1–R5 đã tái hiện trước đó nay đạt; lỗi R6 mới xuất hiện trong đường cleanup của thay đổi phân trang.

## R6 — Vừa: đổi draft khi tải thêm khiến phân trang bị khóa mãi

`portal/web/components/draft-review-app.tsx:150`–`:162`, đặc biệt `finally` tại `:161`.

Luồng tái hiện: có hai draft 3 và 2 → bấm Tải thêm (request đang chờ) → chọn draft 2 (được UI cho phép) → request tải thêm trả thành công hoặc thất bại. `selectDraft` tăng generation, nên cả nhánh kết quả lẫn `finally` của request cũ bỏ qua cập nhật. `loadingMore` đã được đặt true nhưng không có đường reset nào khác. Người dùng vẫn thấy draft 2, song không thể tải các draft tiếp theo trong cùng màn hình.

Đây là lỗi được thêm bởi điều kiện generation/selected ID ở `finally`; chặn dữ liệu cũ là cần thiết nhưng vòng đời trạng thái đang tải vẫn phải kết thúc. Gắn quyền sở hữu request phân trang và trạng thái queue rõ ràng; không dùng generation của detail theo cách làm mất cleanup. Nếu bỏ request cũ khi chuyển ngữ cảnh, phải giải phóng trạng thái của nó, đồng thời bảo đảm callback cũ không giải phóng nhầm một request mới. Giữ khả năng chọn draft khác khi phân trang đang chờ, không mở lại lỗ hổng retry bỏ dirty/POST.

## Brief sửa R6 — Sol medium, cùng Frontend và cùng tree

- Tái sử dụng plan/nghiên cứu hiện có và bằng chứng RED ở trên. Không mở thêm nghiên cứu hoặc thiết kế lại UI.
- Chỉ sửa vòng đời phân trang trong `draft-review-app.tsx`, thêm regression cần thiết trong `portal/web/tests/selection-review-app.test.tsx` (hoặc file test nhỏ cùng phạm vi), cập nhật báo cáo kết quả. Không client/parser/backend/gateway/dependency/lock/config trừ khi phát hiện blocker cụ thể và giải thích trước.
- Thêm test repo trước sửa: success/error sau chọn B; sau settle tải tiếp được và B giữ nguyên; request/callback cũ không mở khóa request mới hay ghi đè detail/queue đã thay thế. Không dùng sleep; không tự retry POST.
- Không sửa probe, config, RED log/XML, plan hoặc review của Leader. Chạy cả probe R1–R5 15 ca và probe R6 2 ca nguyên trạng; lưu output mới riêng.
- Kiểm cần chạy: regression selection UI liên quan, 17 ca Leader, typecheck, lint, `git diff --check`. Không bắt buộc lặp full86/build vì phạm vi chỉ lifecycle phân trang; chỉ mở rộng nếu thay đổi/lỗi mới đòi hỏi.
- Output: cập nhật `PHONG-HOA-W05-SELECTION-UI-RESULT.md`, thêm `w05-selection-ui-evidence/rework-r6/` với log/JUnit, fresh exit, verification và manifest; giữ bằng chứng cũ. Commit cục bộ, tree sạch; báo HEAD/diff và hai hash probe không đổi.
- Từ workspace Leader, lệnh probe: `node .\cti-w05-selection-ui\portal\web\node_modules\vitest\vitest.mjs run --config w05-selection-ui-evidence/leader-review.config.mjs` và tương tự `leader-pagination.config.mjs`. Dùng reporter JUnit/log tại thư mục rework-r6 để không ghi đè bằng chứng Leader.
- Không browser/listener/cloud/JWKS/lab/OpenCTI/push/PR/merge/deploy. Chưa có bằng chứng browser integration v1.

## Điều phối

Đã xem các cuộc đang mở một lần trong lượt này: chỉ Leader hiện tại đang xử lý, Frontend idle. Đã đọc automation: enabled=true, mỗi 30 phút; lần gần nhất 04:56 trả NOTHING NEW, lần kế 05:26 giờ Việt Nam. Giữ automation vì dự án active. Sau khi giao R6 thành công, lưu receipt rồi nhường lượt; gateway/browser chỉ bắt đầu sau khi UI đạt.
