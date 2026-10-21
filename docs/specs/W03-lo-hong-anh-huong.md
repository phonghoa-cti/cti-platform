# W03 — Trang Lỗ hổng ảnh hưởng (`/lo-hong`)

- Vai: Web & Red team (giao diện) + Hạ tầng & Dữ liệu (đối chiếu dữ liệu) · Mốc: P3 (15/12/2026)
- Phụ thuộc: connector CVE/CISA KEV (F01), W04 Tài sản, API `GET /api/cves`

## Mục tiêu
Trả lời: "Phần mềm công ty đang dùng có lỗ hổng nào **đang bị khai thác thật** không, phải vá trước cái nào?"

## Cách đối chiếu (backend)
1. Lấy danh sách công nghệ từ hồ sơ tài sản (W04): nhà cung cấp + sản phẩm + phiên bản (ví dụ Fortinet / FortiOS / 7.2).
2. Lấy CVE từ OpenCTI (Vulnerability) kèm cờ KEV và điểm EPSS nếu có.
3. Khớp theo nhà cung cấp + sản phẩm (không phân biệt hoa thường); phiên bản chỉ hiển thị để người xem tự kiểm tra (đối chiếu phiên bản tự động dễ sai, để ngoài phạm vi).
4. Xếp hạng ưu tiên: KEV trước → EPSS cao → CVSS cao → mới hơn.

## Bố cục
```text
Bộ lọc: [Chỉ KEV ☑] [Tài sản: Tất cả ▼] [Trạng thái: Chưa xử lý ▼]    Tìm: [CVE-...]
┌───────────────┬───────────────┬──────┬──────┬───────┬──────────────┬────────────┐
│ CVE           │ Ảnh hưởng      │ KEV  │ EPSS │ CVSS  │ Hạn vá (KEV) │ Trạng thái │
├───────────────┼───────────────┼──────┼──────┼───────┼──────────────┼────────────┤
│ CVE-xxxx-yyyy │ FortiGate VPN  │ CÓ   │ 94%  │ 9.8   │ 05/12/2026   │ Chưa xử lý │
└───────────────┴───────────────┴──────┴──────┴───────┴──────────────┴────────────┘
Bấm một dòng → ngăn bên phải: mô tả ngắn (tiếng Việt nếu có), sản phẩm/phiên bản bị ảnh hưởng,
link khuyến cáo của hãng, nút đổi trạng thái: Chưa xử lý → Đang vá → Đã vá / Không ảnh hưởng (kèm ghi chú).
```
Lãnh đạo thấy bản tóm tắt: "3 lỗ hổng cần vá, 1 quá hạn" + danh sách rút gọn, không có nút đổi trạng thái.

## Tiêu chí chấp nhận
- [ ] Thêm "Fortinet FortiOS" vào tài sản → các CVE KEV của FortiOS xuất hiện, KEV xếp đầu.
- [ ] Trạng thái xử lý lưu trong SQLite, có nhật ký ai đổi, khi nào.
- [ ] Giải thích EPSS, KEV, CVSS bằng tooltip tiếng Việt.
- [ ] Unit test cho hàm xếp hạng ưu tiên.
