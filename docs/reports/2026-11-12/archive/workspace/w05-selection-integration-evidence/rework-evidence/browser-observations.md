# Browser observations

Surface: Trình duyệt tích hợp được cấp. Ngày 11/11/2026. Không resize viewport, không mở browser bằng shell.

## Save refresh fault

Sau bỏ chọn IOC đầu và bấm **Lưu lựa chọn**, browser quan sát `Lựa chọn đã được lưu.`, `1 IOC đã lưu`, nút
**Tải lại trạng thái**, cùng hai GET 503. Sau marker `before-retry`, bấm nút đúng một lần; browser báo không tải
được chi tiết, nhưng confirmation và snapshot đã lưu vẫn còn. Ảnh cuối: `save-refresh-after-retry.png`.

## Decision refresh fault

Sau bấm **Duyệt bản nháp**, browser quan sát `Đã duyệt`, confirmation `Bản nháp đã được duyệt cục bộ; chưa nhập
OpenCTI.`, nút **Tải lại trạng thái**, cùng hai GET 503. Sau marker `before-retry`, bấm nút đúng một lần. Browser
body sau retry vẫn chứa cả `Đã duyệt` và confirmation cuối; chỉ báo lỗi tải chi tiết. Ảnh cuối:
`decision-refresh-after-retry.png`.

## Sample route

Mở `/duyet/mau` trong run riêng. Browser body có `Dữ liệu mẫu`, `Nguồn: fixture ngoại tuyến đã kiểm hình dạng`
và `Bản xem thử không gửi yêu cầu ghi...`. Ảnh: `sample-no-api.png`; trace chỉ có marker sau load.

`save-refresh-after-retry-first-attempt.png` là ảnh giữ lại từ lượt instrumentation đầu bị lỗi khi *ghi* trạng
thái “không còn listener”; `LocalRun.close()` đã chạy nhưng lượt đó không có `*-run.json`, nên ảnh này không
được dùng để kết luận R1/R2. Lượt save hoàn chỉnh sau đó là bộ `save-refresh-retry-*` và ảnh không hậu tố
`first-attempt`.
