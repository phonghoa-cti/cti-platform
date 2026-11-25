# Rework WEB-W05-PREVIEW

Base review: `be364bd87cd87a86b37d83e8a74e1ff3583ea7ec`, tree `cti-portal-web`, branch `feat/portal-w05-preview-20261110`. Leader chạy 11/11 test xanh, đọc log build/check và ảnh 1280. Không thiết kế lại UI.

## R1 — thao tác sao chép thất bại không được xử lý

`portal/web/components/draft-review.tsx`: `copyIoc` await `navigator.clipboard.writeText` không catch; onClick bỏ Promise bằng `void`. Khi API thiếu hoặc quyền clipboard bị từ chối, người dùng không nhận được phản hồi lỗi và có Promise rejection không được xử lý. Đây là finding từ đọc mã, chưa được Leader tái hiện browser.

Yêu cầu: xử lý cả Clipboard API không có và writeText từ chối, hiện thông báo VI/EN dễ hiểu và truy cập được bằng trình đọc màn hình; chỉ báo đã sao chép sau khi thực sự thành công, cho phép thử lại. Không log raw IOC/error ra console, không fallback tự đọc clipboard hoặc tự điều hướng. Viết test tái hiện đỏ trước, kiểm failure/success/retry và không gọi clipboard trước click. Nếu không tái hiện được thì trả bằng chứng cụ thể thay vì sửa theo suy đoán.

## Kiểm chứng viewport còn thiếu

Giữ 360/1440 UNVERIFIED khi bề mặt browser được cấp không có resize. Chỉ dùng khả năng thật của bề mặt được cấp; không khởi chạy browser khác/đụng trình duyệt người dùng để lách. Không dùng CSS width/zoom để gọi là viewport thực. Nếu lần này có resize hợp lệ thì kiểm 360/1440 và lưu ảnh/overflow/focus. Nếu vẫn không có, ghi blocker chính xác, không thử vòng lặp và không để việc thiếu viewport chặn sửa R1.

## Phạm vi và bàn giao

CTI Frontend Sol medium, tự làm không giao bot khác. Giữ brief gốc; chỉ component/messages/test cần cho R1, cập nhật đoạn task docs/PROGRESS.md và ai-log, bằng chứng trong frontend-evidence và PHONG-HOA-FRONTEND-RESULT.md. Local commit được phép; không push/PR/merge/deploy, không nối API/auth trong rework này. Bảo toàn sửa đổi có trước; không sửa tree khác hoặc RUNS.

Chạy test nhóm mới rồi npm test/typecheck/lint/build sau thay đổi; báo test count, exit, SHA/diff và giới hạn browser. Source nghiên cứu nhỏ dùng tài liệu Clipboard API chính thức/MDN cho failure/secure context, không khảo sát lại stack.

## Nghiệm thu sau rework

Leader kiểm ngày 11/11, lượt 00:40: R1 PASS tại `9b10223d90e529432d976177e14fdf2b6ce46bb7`. Đọc diff và chạy `npm test -- --run tests/draft-review.test.tsx`: 5/5, exit 0. Log worker ghi full 13/13 và typecheck/lint/build đạt; Leader không chạy lại full suite. Viewport 360/1440 vẫn UNVERIFIED, được theo dõi riêng bằng task UI-RESPONSIVE-VERIFY; không mở lại R1 vì thiếu resize. UI wiring chờ API. Bằng chứng: PHONG-HOA-LEADER-REVIEW-20261111-0040.md.
