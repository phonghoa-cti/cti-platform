# W02 — Trang Tra cứu IOC (`/tra-cuu`)

- Vai: Web & Red team · Mốc: P1 (01/12/2026) · Phụ thuộc: W00, API `GET /api/ioc`, `phonghoa_core`

## Mục tiêu
Nhân viên IT dán bất kỳ thứ gì đáng ngờ (IP, tên miền, link, hash, email) và trong 1 giây biết: có độc không, chắc chắn đến đâu, vì sao, nên làm gì.

## Bố cục
```text
┌──────────────────────────────────────────────────────────────────────┐
│ [ Dán IP, tên miền, link, hash hoặc email...                ] [Tra] │
│ Mẹo: dán được cả dạng hxxp://evil[.]com — hệ thống tự hiểu.          │
├──────────────────────────────────────────────────────────────────────┤
│ hoadon-dientu[.]top   Tên miền            [Sao chép] [Mở trên OpenCTI]│
│ ┌───────────┐  ĐIỂM 78 / 100 — CAO                                    │
│ │    78     │  Thẻ giải thích:                                        │
│ └───────────┘  Nguồn tin cậy 0.80 × 3 nguồn xác nhận (0.88) ×          │
│                thấy 2 ngày trước (0.96) × liên quan tài sản (1.30)     │
├──────────────────────────────────────────────────────────────────────┤
│ Nên làm gì: Chặn tên miền này trên firewall/DNS.  [Đề xuất chặn]      │
├────────────────────────────────┬─────────────────────────────────────┤
│ Nguồn đã báo (dòng thời gian)   │ Liên quan                            │
│ • 20/10 AlienVault OTX          │ • Kỹ thuật: T1566.001                │
│ • 21/10 ThreatFox               │ • Mã độc: <tên họ>                   │
│ • 22/10 Báo cáo NCSC (AI trích) │ • Tài sản khớp: email @congty.vn     │
├────────────────────────────────┴─────────────────────────────────────┤
│ Làm giàu: quốc gia, ASN, ngày đăng ký tên miền, VirusTotal x/y        │
│ [Đánh dấu báo nhầm]  (chỉ Analyst)                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Hành vi
1. Chuẩn hóa đầu vào bằng `phonghoa_core.normalize` (ở backend). Không nhận diện được → "Không phải IOC hợp lệ. Ví dụ hợp lệ: 8.8.8.8, evil.com, https://..., hash 32/40/64 ký tự."
2. IP nội bộ (192.168.x.x...) → thông báo "Đây là IP nội bộ, không tra cứu trên Internet".
3. Có trong allowlist → hiện nhãn xanh "Hạ tầng hợp pháp (allowlist)", điểm 0, kèm lý do.
4. Không có trong kho → "Chưa có nguồn nào báo IOC này" + nút "Làm giàu ngay" (gọi enrichment, tính vào giới hạn API; chỉ IT/Analyst).
5. Dán nhiều dòng (tối đa 50) → bảng kết quả gọn: giá trị, loại, điểm, mức; bấm từng dòng để xem chi tiết.
6. URL cập nhật theo truy vấn (`/tra-cuu?q=...`) để gửi link cho đồng nghiệp.
7. "Đề xuất chặn" tạo một yêu cầu chờ Analyst duyệt (W05), không chặn ngay.

## Tiêu chí chấp nhận
- [ ] `hxxp://Evil[.]COM/a` và `http://evil.com/a` cho cùng kết quả.
- [ ] Thẻ giải thích hiển thị đúng chuỗi `reason` từ API (không tính lại ở frontend).
- [ ] Dữ liệu TLP:AMBER/RED không hiện với vai trò IT (test API).
- [ ] Tra 50 dòng một lúc < 3 giây.
- [ ] Playwright: dán IOC → thấy điểm → bấm "Đề xuất chặn" → thấy thông báo "Đã gửi, chờ duyệt".
- [ ] Mọi giá trị IOC hiển thị dạng defang; nút sao chép trả giá trị thật.
