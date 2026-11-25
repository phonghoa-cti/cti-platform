# ADR 0017 — W03-S2 dùng read model và cursor riêng

- Ngày: 12/11/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh

W03-R đã có wire/cursor strict; W03-S1 lưu status theo relation. Ghép N+1 ở browser không bảo đảm cùng snapshot,
còn sửa route W03-R làm tăng rủi ro regression và lộ metadata cho Leader.

## Các phương án

1. Mở rộng `GET /api/cves`; 2. route read model riêng; 3. browser ghép nhiều request status.

## Quyết định

Chọn `GET /api/cves/status-view`. Dataset validate một lần; Technology và status đọc trong cùng transaction
SQLite chỉ đọc. Cursor riêng bind query, dataset, Technology, status và ngày UTC; Leader dùng projection lược.

## Hệ quả (tốt / xấu / cách giảm thiểu)

Giữ nguyên hợp đồng đã nghiệm thu, lọc trước phân trang và phát hiện drift giữa trang. Đổi lại có thêm DTO/route
và cursor riêng; fixture strict cùng regression W03-R/S1 giảm nguy cơ lệch wire. Đây vẫn chỉ là read model cục bộ,
không chứng minh trạng thái vá thực tế hay runtime phân tán.
