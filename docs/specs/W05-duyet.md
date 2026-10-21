# W05 — Trang Duyệt (`/duyet`)

- Vai: AI & Agent (logic) + Web & Red team (giao diện) · Mốc: P4 (12/01/2027) · Chỉ Analyst và Admin

## Mục tiêu
Một nơi duy nhất để con người quyết định trước khi máy làm: (1) bản nháp STIX do AI trích từ báo cáo, (2) hành động do người dùng hoặc agent đề xuất (chặn, xuất).
Đây là phần "người duyệt" (human-in-the-loop) — điểm an toàn quan trọng khi bảo vệ.

## Tab 1 — Bản nháp AI
```text
┌─────────────────────────────────────┬────────────────────────────────────────┐
│ Văn bản gốc (chỉ đọc, dạng text)     │ AI trích được (tích để giữ)             │
│ ...tải mã độc từ hxxps://cdn-update │ ☑ URL  https://cdn-update[.]xyz/... 🔗 │
│ [.]xyz/payload/loader.exe và kết nối│ ☑ IPv4 45.137.21[.]9                    │
│ máy chủ C2 tại 45.137.21[.]9...     │ ☐ Domain google[.]com  ⚠ allowlist     │
│ (IOC được tô màu tại chỗ xuất hiện) │ ☑ TTP  T1566.001 Lừa đảo kèm tệp        │
│                                     │ ⚠ "IOC không có trong văn bản" (bị loại)│
├─────────────────────────────────────┴────────────────────────────────────────┤
│ Nguồn · Ngôn ngữ · TLP [GREEN ▼] · Model · Thời gian xử lý · Chi phí token       │
│ [Duyệt và lưu vào OpenCTI]  [Lưu nháp]  [Từ chối + lý do]                       │
└──────────────────────────────────────────────────────────────────────────────┘
```
- Mỗi mục AI trích có liên kết tới vị trí trong văn bản gốc; mục không tìm thấy trong văn bản bị **tự động loại** và gắn cảnh báo (chống "bịa").
- Văn bản gốc **chỉ hiển thị dạng text**; nếu phát hiện dấu hiệu chèn lệnh (prompt injection), hiện cảnh báo đỏ ở đầu.
- Duyệt → tạo Report + các object STIX trên OpenCTI với tác giả là người duyệt; lưu lại số mục bị sửa (số liệu cho chương 4).

## Tab 2 — Hành động chờ duyệt
| Cột | Ví dụ |
|---|---|
| Hành động | Chặn tên miền `hoadon-dientu[.]top` |
| Người/agent đề xuất | IT: an@congty.vn / Agent Hermes |
| Lý do | Điểm 78, liên quan email công ty |
| Ảnh hưởng | Thêm vào blocklist; firewall cập nhật trong 1 giờ |
| Nút | Duyệt · Từ chối (bắt buộc ghi lý do) |
Đề xuất quá 72 giờ không ai xử lý → tự hết hạn.

## Tiêu chí chấp nhận
- [ ] Không có cách nào (API hay giao diện) để agent tự duyệt đề xuất của chính nó.
- [ ] Mọi quyết định ghi nhật ký: ai, lúc nào, trước/sau.
- [ ] Đo và lưu: số mục AI trích, số mục bị bỏ tích, số mục người thêm → tính Precision/Recall thực tế.
- [ ] Playwright: mở bản nháp → bỏ tích 1 mục → duyệt → thấy Report trên OpenCTI.
