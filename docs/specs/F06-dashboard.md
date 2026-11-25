# F06 — Dashboard

> **Đã chi tiết hóa:** trang cho lãnh đạo xem `W01-tong-quan.md`. Phần 1 (dashboard analyst trong OpenCTI) vẫn theo file này.

- Vai: Web & Red team · Mốc: v0.5 · Trạng thái: Nháp

## Mục tiêu
Hai màn hình cho hai đối tượng:
1. **Analyst:** dashboard tùy chỉnh ngay trong OpenCTI (không code) — IOC mới theo nguồn, top malware, ATT&CK.
2. **Lãnh đạo SME:** trang Tổng quan tiếng Việt trên portal — 4 con số chính, xu hướng 30 ngày, 5 cảnh báo cần chú ý.

## Tiêu chí chấp nhận
- [ ] Dashboard OpenCTI được xuất cấu hình và lưu trong `deploy/opencti-dashboards/`.
- [ ] Trang Tổng quan đọc dữ liệu thật, tải < 2 giây, hiển thị tốt trên điện thoại.
- [ ] Tiếng Việt mặc định, có nút chuyển tiếng Anh.

## Ghi chú học tập
Trước khi code, vẽ phác 3 màn hình trên giấy hoặc Excalidraw, chụp đưa vào devlog — làm bằng chứng thiết kế cho chương 3.
