# F01 — Thu thập feed tự động

- Vai: Hạ tầng & Dữ liệu · Mốc: v0.1 (24/11/2026) · Trạng thái: Nháp

## Mục tiêu
OpenCTI tự động nhận dữ liệu từ ít nhất 5 nguồn miễn phí theo lịch, không cần ai bấm tay.

## Cách làm (ưu tiên bật sẵn, chỉ viết khi thiếu)
1. Mở danh sách connector chính thức (repo `OpenCTI-Platform/connectors`, thư mục `external-import`).
2. Với mỗi nguồn trong bảng dưới: có connector chính thức → chỉ thêm khối cấu hình vào docker-compose;
   chưa có → viết connector riêng theo skill `stix-connector`.

| Nguồn | Dự kiến | Ghi chú |
|---|---|---|
| MITRE ATT&CK | Bật sẵn | Từ điển TTP, bắt buộc có trước |
| AlienVault OTX | Bật sẵn | Cần API key miễn phí |
| abuse.ch URLhaus, ThreatFox | Bật sẵn nếu có | Cần Auth-Key miễn phí của abuse.ch |
| CISA KEV + CVE/NVD | Bật sẵn nếu có | Phục vụ F11 (lỗ hổng ảnh hưởng tài sản) |
| abuse.ch Feodo Tracker | Tự viết nếu chưa có | Connector đầu tiên của nhóm — để học quy trình |

## Tiêu chí chấp nhận
- [ ] ≥ 5 nguồn chạy theo lịch, thấy object mới trên OpenCTI mỗi ngày.
- [ ] Mỗi object có nguồn (`created_by`), nhãn TLP, link tham chiếu.
- [ ] Mỗi connector giới hạn RAM ≤ 256 MB; tổng RAM máy chủ còn ≥ 2 GB trống.
- [ ] Bảng nguồn trên Wiki ghi: tên, giấy phép, giới hạn request, chu kỳ.

## Không làm
Không thu thập dark web; không cào trang cấm robots.

## Task
1. Liệt kê connector chính thức khớp bảng trên (ghi vào Wiki).
2. Bật MITRE + OTX, kiểm tra RAM.
3. Bật các nguồn còn lại có sẵn.
4. Viết connector Feodo Tracker (nếu cần) theo skill `stix-connector`, dùng `phonghoa_core.normalize`.
