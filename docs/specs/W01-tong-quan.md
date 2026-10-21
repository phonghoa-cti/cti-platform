# W01 — Trang Tổng quan (`/tong-quan`)

- Vai: Web & Red team · Mốc: P2 (08/12/2026) · Phụ thuộc: W00, API `GET /api/overview`

## Mục tiêu
Lãnh đạo mở portal 30 giây mỗi sáng là biết: có gì đáng lo không, xu hướng ra sao, cần ai làm gì.

## Bố cục (máy tính; điện thoại xếp thành 1 cột theo thứ tự đánh số)
```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ① Mức đe dọa hôm nay: [TRUNG BÌNH]  "2 IOC liên quan tài sản, 1 CVE đang bị │
│    khai thác ảnh hưởng FortiGate"                     cập nhật 5 phút trước │
├──────────────┬──────────────┬──────────────┬───────────────────────────────┤
│ ② IOC mới 24h│ Liên quan    │ CVE KEV ảnh  │ Cảnh báo Wazuh 7 ngày          │
│   1.248 ▲12% │ tài sản: 2   │ hưởng: 1     │ 3                              │
├──────────────┴──────────────┴──────────────┴───────────────────────────────┤
│ ③ Việc cần chú ý (tối đa 5 dòng, xếp theo mức độ)                           │
│   ● Cao   CVE-xxxx-yyyy ảnh hưởng FortiGate 7.x — hạn vá theo KEV: 05/12    │
│   ● Cao   Domain hoadon-dientu[.]top giả mạo hóa đơn, liên quan email cty  │
├───────────────────────────────────────┬────────────────────────────────────┤
│ ④ IOC mới 30 ngày theo loại (đường)    │ ⑤ Kỹ thuật tấn công nổi bật tuần   │
│                                       │   (thanh ngang, top 5 ATT&CK)      │
├───────────────────────────────────────┴────────────────────────────────────┤
│ ⑥ Họ mã độc / nhóm tấn công được nhắc nhiều tuần này (thẻ nhỏ, top 5)       │
└────────────────────────────────────────────────────────────────────────────┘
```

## Chi tiết từng khối
| Khối | Nội dung | Quy tắc |
|---|---|---|
| ① Mức đe dọa | Thấp / Trung bình / Cao + 1 câu lý do sinh tự động | **Cao** nếu có IOC điểm ≥ 70 liên quan tài sản trong 24h, hoặc có CVE KEV ảnh hưởng chưa xử lý; **Trung bình** nếu có IOC điểm ≥ 40 liên quan tài sản trong 7 ngày; còn lại **Thấp** |
| ② 4 chỉ số | Số + so sánh với kỳ trước (▲▼ %) | Bấm vào chuyển tới trang tương ứng đã lọc sẵn |
| ③ Việc cần chú ý | Tối đa 5 mục: CVE KEV ảnh hưởng tài sản, IOC liên quan tài sản, cảnh báo Wazuh khớp IOC | Mỗi dòng: mức, mô tả 1 câu, liên kết chi tiết; Lãnh đạo chỉ xem, IT/Analyst có nút "Đã xử lý" |
| ④ Xu hướng | Biểu đồ đường 30 ngày, 1 đường cho mỗi loại IOC (IP, domain, URL, hash) | Có chú thích; rê chuột xem số theo ngày |
| ⑤ Kỹ thuật nổi bật | Top 5 kỹ thuật ATT&CK từ báo cáo trong 7 ngày | Hiển thị mã + tên tiếng Việt ngắn (ví dụ "T1566 Lừa đảo qua email") |
| ⑥ Mã độc / nhóm | Top 5 tên được nhắc nhiều nhất trong 7 ngày | Bấm vào mở trang tương ứng trên OpenCTI (chỉ Analyst) |

## Tiêu chí chấp nhận
- [ ] Đủ 6 khối với dữ liệu thật từ OpenCTI; tải < 2 giây khi đã có cache.
- [ ] Quy tắc mức đe dọa có unit test cho cả 3 mức (backend, không phải frontend).
- [ ] Mỗi khối có trạng thái trống và trạng thái lỗi riêng; lỗi một khối không làm hỏng cả trang.
- [ ] Hiển thị đúng ở 360 px; chữ không tràn khung.
- [ ] Lãnh đạo không thấy nút "Đã xử lý"; IT thấy và bấm được (có ghi nhật ký).
- [ ] Toàn bộ chữ có bản tiếng Anh.

## Câu hỏi mở
- Cảnh báo Wazuh lấy bằng cách nào: Wazuh gửi về portal (webhook) hay portal đọc từ Wazuh API? Đề xuất: Wazuh API, chỉ đọc. Chốt ở F07.
