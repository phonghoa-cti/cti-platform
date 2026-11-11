# W03-S1 — trạng thái CVE theo công nghệ

## Phạm vi

Ba route opt-in lưu trạng thái cục bộ, không đổi `GET /api/cves`: GET status, PUT status và GET
status-history. Chỉ role `it|analyst|admin`; danh tính lấy từ JWT đã xác minh phía server. Giá trị này là ghi nhận
của người dùng, không phải bằng chứng kỹ thuật đã vá.

## Tính nhất quán

Store dùng cùng file SQLite W04. `initialize()` là migration explicit; constructor, app factory và request không
tạo/migrate DB. GET mở `mode=ro` và transaction đọc. PUT mở `mode=rw`, `BEGIN IMMEDIATE`, kiểm schema W04/S1,
technology active, dataset/context và optimistic version trước khi ghi status + audit trong một transaction.
Mọi lỗi trước commit rollback; expected context cũ trả 409 và không ghi.

Dataset CVE được lấy/validate đúng một lần mỗi request. Dataset nằm ngoài SQLite nên snapshot này là immutable
trong request nhưng không được tuyên bố atomic với thay file ngoài. Technology/context dùng connection của thao
tác status làm thẩm quyền cuối.

## Cursor history canonical

Cursor là base64url không padding của JSON UTF-8 canonical (sort key, compact) gồm đúng `v=1`, `snapshot`,
`binding`, `after`. `binding` băm relation + role view + limit; `snapshot` băm context + max audit ID + số audit.
Sai binding/canonical/position trả 422; status, technology hoặc dataset đổi làm cursor cũ trả 409.

## Giới hạn bằng chứng

Test dùng JWT RSA, dataset và SQLite tổng hợp in-process. Chưa chứng minh browser/gateway, Cloudflare/JWKS/HTTPS
thật, feed/OpenCTI, lab hay production.
