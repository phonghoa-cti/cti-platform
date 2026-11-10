# ADR 0015 — Tách contract selection sang API v1

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh

Parser frontend legacy khóa review version 0/1 và exact key, trong khi selection core cho phép nhiều lần save.
Ghép hai getter core ở service cũng có thể trả review và selection ở hai snapshot SQLite khác nhau.

## Các phương án

1. Đổi `/api/drafts` tại chỗ: ít route hơn nhưng phá parser legacy.
2. Ghép getter hoặc SQL trong service: ít code core hơn nhưng có race hoặc nhân đôi invariant.
3. Thêm `/api/v1/drafts` và helper composite trong core.

## Quyết định

Chọn phương án 3. Detail dùng một connection/read transaction; mutation trả result đã commit. API v1 dùng số
an toàn JavaScript, body stream tối đa 65.536 byte và giữ auth/Origin/error/no-store hiện có.

## Hệ quả (tốt / xấu / cách giảm thiểu)

Contract legacy không đổi và response v1 nhất quán. Đổi lại frontend phải chuyển path/parser trong task riêng;
không thêm fallback tự chọn baseline vì có thể duyệt sai IOC.
