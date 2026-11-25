# F07 — Xuất dữ liệu cho firewall/SIEM

- Vai: Hạ tầng & Dữ liệu · Mốc: v0.5 · Trạng thái: Nháp

## Mục tiêu
Firewall và Wazuh tự động lấy danh sách IOC đáng chặn từ Phong Hỏa.

## Cách làm
1. **TAXII 2.1:** dùng tính năng TAXII collection có sẵn của OpenCTI, lọc Indicator có điểm ≥ 60.
2. **Blocklist dạng text:** endpoint `GET /api/blocklist.txt?type=ipv4&min_score=60` (trong portal API),
   mỗi dòng một giá trị — loại mà firewall phổ biến đọc được.
3. **Wazuh:** xuất danh sách CDB (key:value) để rule Wazuh so khớp IP/domain trong log.

## Tiêu chí chấp nhận
- [ ] Không có IOC nằm trong allowlist trong mọi đầu ra (có test).
- [ ] Wazuh trong lab sinh cảnh báo khi máy nạn nhân truy cập domain có trong blocklist.
- [ ] Blocklist được tạo lại mỗi giờ.
