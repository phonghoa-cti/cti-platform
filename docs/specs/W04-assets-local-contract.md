# W04 — hợp đồng tài sản domain/CIDR cục bộ

## Phạm vi

Lát cắt này cho IT, analyst và admin quản lý hai loại tài sản `domain` và `ip_range` qua API
in-process. Dữ liệu nằm trong SQLite demo riêng và chỉ hoạt động khi `AssetStore` được inject vào
`create_app`. Mặc định W02 không mở DB, không tạo schema và không bật route tài sản.

Chưa có UI, CSV, công nghệ/thương hiệu, dò phơi nhiễm, OpenCTI, listener, lab hay production.

## API

- `GET /api/assets?type=domain|ip_range`: tối đa 1.000 asset active, thứ tự ID tăng dần.
- `POST /api/assets`: body exact `{type,value,note}`, tối đa 8 KiB, trả `201`.
- `PUT /api/assets/{id}`: body exact `{type,value,note,expected_version}`.
- `DELETE /api/assets/{id}?expected_version=N`: soft delete, trả `204`.

ID và version là integer strict trong khoảng `1..2^53-1`. Mutation bắt buộc `Origin` đúng cấu hình.
Mọi route xác minh JWT và role phía server trước query, body hoặc DB. Response có
`Cache-Control: no-store` và `Vary: Cf-Access-Jwt-Assertion`.

Lỗi ổn định gồm `authentication_required` (401), `forbidden` (403), `asset_not_found` (404),
`request_too_large` (413), `invalid_asset` (422), `asset_exists`/`asset_conflict` (409) và
`assets_unavailable` (503). Lỗi không trả raw input, SQL, path hay token.

## Canonical và transaction

Domain chỉ nhận hostname, hỗ trợ dấu chấm cuối và IDN theo codec IDNA hiện có của Python/core;
không nhận URL, email, wildcard hoặc chuỗi đã defang. CIDR dùng `ipaddress.ip_network` với
`strict=True`, nên địa chỉ có host bits bị từ chối. Domain canonical tối đa 253 ký tự.

Create/update/delete và audit before/after canonical nằm trong cùng `BEGIN IMMEDIATE`. Unique index
partial chỉ cấm trùng `(type, canonical_value)` khi asset chưa bị xóa. Schema được khởi tạo tường minh,
idempotent cho DB demo; request không tự migrate DB dùng chung.

## Nối W02

Mỗi lookup đọc một snapshot active assets. Domain khớp equality hoặc ranh giới nhãn; IP chỉ khớp
network cùng family; URL/email dùng hostname/domain; hash không khớp. URL có path/query vẫn có
`asset_match` nhưng giữ luật allowlist cũ: chỉ homepage được allowlist.

Asset local được gắn vào `asset_match` cho `allowlisted`, `not_found` và `found`. Nó không biến
unknown thành found. Khi found, tên local được gộp với asset fact đã qua TLP filter rồi score được tính
lại từ tập visible. Default allowlist độc lập và vẫn còn hiệu lực sau khi asset trùng giá trị bị xóa.
Lỗi snapshot map về `lookup_unavailable` trên `/api/ioc`.

Giới hạn: tối đa 100 tên match và 1.000 asset active; vượt giới hạn trả unavailable thay vì dữ liệu
partial.
