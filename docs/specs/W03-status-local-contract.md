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

Runner tích hợp chỉ bật status theo scenario opt-in, inject store vào cùng SQLite W04 và chạy migration/seed trước
request. Gateway giữ JWT phía server, chặn route/method gần đúng và dành cap 16 KiB riêng cho PUT status. Hai fault
hữu hạn chỉ mô phỏng mất response sau commit và lỗi GET đối soát; mutation không được tự replay.

Test Backend dùng JWT RSA, dataset và SQLite tổng hợp in-process. Ma trận tích hợp bổ sung socket gateway/API thật,
SQL snapshot và trace đã lược. Frontend đã ghép cục bộ; wire capture API thật được parser/provider production đọc
với Unicode, note 1000, actor 512, vendor/version 128 và history 100+cursor. Product trong context mới chứng minh
đến 128 vì loader dataset CVE giới hạn product 128 dù technology/context cho phép 256; product 256 hiện là giới hạn
bằng chứng, không phải PASS. Browser desktop 1280×720 đã chứng minh known-commit lỗi tạm thời rồi phục hồi trong
cùng trang với một PUT/audit; unknown-outcome reentry cùng trang còn PENDING. Chưa chứng minh mobile,
Cloudflare/JWKS/HTTPS thật, feed/OpenCTI, lab hay production.
