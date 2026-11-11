# ADR 0008: status và audit W03-S1 dùng cùng transaction SQLite W04

- Trạng thái: chấp nhận
- Ngày: 12/11/2026

## Quyết định

Tạo schema additive riêng cho status/audit trong cùng file SQLite với technology W04. PUT dùng một connection,
`BEGIN IMMEDIATE`, optimistic version và audit append-only. Dataset CVE được validate thành một snapshot trước
transaction; không giả định file ngoài atomic với SQLite.

## Lý do và hệ quả

Cùng connection loại bỏ ghép technology cũ với status mới và cho status + audit rollback cùng nhau. Migration
phải gọi explicit và fail-closed khi schema/marker/index thiếu hoặc sai. Một writer SQLite giới hạn thông lượng,
nhưng phù hợp lát cắt cục bộ; triển khai phân tán là quyết định sau.
