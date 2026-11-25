# W04 — tiếp tục sau lượt bị dừng

Ngày 11/11/2026, Leader nhận callback failed/stalled của request `a8d902c0-9c10-4c57-be79-7d61d1a83fbf`, thread Engineer `5262b550-6793-407c-b9fc-bc10820a712f`. Hệ thống báo dừng sau 20 phút không có hoạt động. Đây là lần phục hồi thứ nhất của sự cố này.

## Quan sát của Leader

- Đã xem các cuộc đang mở một lần: thread đích idle, không có Leader khác đang làm Phong Hỏa.
- Tree `cti-w04-local-integration` sạch khi kiểm; HEAD `59d679e0949fea5ece953645cd6b80303546b43a`, commit lúc 22:46:27 giờ Việt Nam.
- Lịch sử giữ base `652545688fb5dd7bb4fe974c597fed370e9ad0f0` và ba cherry-pick Frontend `3299b35`, `f317876`, `1aeedc4`.
- Commit tích hợp có 12 file, +388/-4. Có artifact focused frontend, harness, HTTP matrix và helper smoke. Log frontend-checks mới chỉ thấy đầu transcript khi đọc; chưa chứng minh typecheck/lint/build hoàn tất.
- Không có báo cáo `PHONG-HOA-W04-LOCAL-INTEGRATION-RESULT.md` trong danh sách file root khi kiểm. Không có bằng chứng nghiệm thu browser trong callback này.
- Kiểm tiến trình theo đúng tên thư mục chỉ thấy lệnh kiểm của Leader; không thấy tiến trình mang đường dẫn target. Đây không phải khẳng định mọi worker nền đã dừng.

## Phần Engineer phải hoàn tất trên đúng thread/tree

1. Đọc brief gốc `PHONG-HOA-W04-LOCAL-INTEGRATION-BRIEF-20261111.md`, giữ phạm vi/quyền và mã đã lưu. Không dựng lại tree, không lặp cherry-pick, không reset/xóa sửa đổi.
2. Kiểm trạng thái worker/lệnh đã khởi chạy từ lượt của mình. Nếu còn tác vụ sống, thu kết quả đúng tác vụ đó, không tạo writer thứ hai. Engineer/Sol làm trực tiếp phần còn thiếu, không giao tiếp worker/bot mới. Không chờ vô hạn hoặc coi launch exit 0 là kết quả.
3. Thu exit/count và hash bằng chứng đã có; chỉ chạy lại lệnh thiếu kết quả kết thúc hoặc phạm vi mới/rủi ro. Các lệnh dài phải có timeout phù hợp, giữ foreground, chia bước để có tiến độ quan sát được. Không lặp suite Backend đã nghiệm thu.
4. Hoàn tất kiểm browser bằng bề mặt OpenMausBot được cấp theo brief. Nếu không có, trả ngay báo cáo CODE/HTTP có bằng chứng và helper start/status/stop hữu hạn, lệnh chính xác để Leader kiểm browser. Không chờ một browser không được cấp và không tự dùng đường khác.
5. Báo cáo root `PHONG-HOA-W04-LOCAL-INTEGRATION-RESULT.md`, evidence `w04-local-integration-evidence/`, SHA/tree/delta chính xác, kiểm đã chạy/exit/count/cleanup và phần UNVERIFIED. Không tự gắn PASS toàn luồng nếu browser chưa kiểm.

Sự cố không làm mất nghiệm thu Backend/Frontend/prep. W04 vẫn chưa được nghiệm thu tích hợp; không push/PR/merge/deploy hoặc đổi quyền.
