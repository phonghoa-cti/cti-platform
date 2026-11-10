# ADR 0014 — Lưu lựa chọn IOC bằng snapshot audit riêng

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh

Người duyệt cần bỏ chọn rồi chọn lại IOC đủ điều kiện mà không sửa payload và evidence gốc. Quyết định cuối
phải chứng minh chính xác tập IOC đã được dùng, kể cả khi reject.

## Các phương án

1. Ghi danh sách chọn trực tiếp lên `drafts`: đơn giản nhưng mất lịch sử.
2. Dùng chung `draft_audit`: phải phá bất biến một quyết định cuối cho mỗi draft.
3. Tạo `draft_selection_audit`: giữ lịch sử save riêng và tham chiếu snapshot từ quyết định cuối.

## Quyết định

Chọn phương án 3. Schema v2 giữ payload bất biến, dùng item index trong draft, hash JSON canonical và hai
version đồng bộ. `BEGIN IMMEDIATE` gói update pointer cùng insert event/audit; v0 và v1 được migrate thẳng lên
v2 trong một transaction.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: no-op không tạo lịch sử; stale write xung đột; approve/reject có snapshot kiểm toán được.
- Xấu: API/UI hiện tại giới hạn review version 0/1 nên chưa được nối vào DB đã edit.
- Giảm thiểu: core cung cấp getter selection riêng; API/UI sẽ nâng contract version trong lát cắt tiếp theo.
