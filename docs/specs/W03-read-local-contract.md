# W03-R — hợp đồng đọc lỗ hổng cục bộ

## Phạm vi

Lát cắt này thêm đúng một endpoint `GET /api/cves`. Nguồn CVE là fixture tổng hợp được inject rõ ràng;
`create_app(..., cve_port=None)` không tự bật fixture. Endpoint chỉ đối chiếu `vendor + product` bằng
`casefold`, không kết luận phiên bản bị ảnh hưởng và không lưu trạng thái xử lý.

Snapshot công nghệ dùng `TechnologyStore` hiện có nhưng adapter W03 mở SQLite bằng URI `mode=ro`. Request
không gọi `initialize`, không migrate/seed và không tạo database khi path thiếu. Một request đọc đúng một
dataset và một lần `SELECT ... fetchall()` toàn bộ technology active đã được validation W04.

## Quyền, query và lỗi

Auth chạy trước query. `it`, `analyst`, `admin` hoặc role hỗn hợp có một trong ba role này nhận `view=detail`;
leader-only nhận `view=summary`; role khác bị 403. Query chỉ gồm `kev=true|false`, `asset_id`, `q`, `limit`
(1..100, mặc định 25) và `cursor`. Query lạ/lặp, control, số không phải decimal canonical hoặc cursor sai trả
422 `invalid_cve_query` trước port/store. Leader-only dùng `asset_id` bị 403 trước port/store.

Mã lỗi ổn định: 401 `authentication_required`, 403 `forbidden`, 404 `technology_not_found`, 409
`cve_snapshot_changed`, 422 `invalid_cve_query`, 503 `cves_unavailable`. Mọi response có
`Cache-Control: no-store` và `Vary: Cf-Access-Jwt-Assertion`; message tĩnh, không echo dữ liệu không tin cậy.

## Dataset, wire và giới hạn

Fixture tối đa 4 MiB, 0..1.000 candidate, mỗi candidate 1..20 product. Adapter tính `dataset_id` là
`sha256:<64 hex>` từ chính bytes fixture. Service kiểm exact key/type, CVE ID uppercase, ngày/timestamp UTC,
HTTPS URL, bool không nhận số, số hữu hạn, quan hệ null và duplicate trước khi trả bất kỳ kết quả nào. KEV
overlay phải đánh dấu đầy đủ; `false` chỉ có nghĩa không nằm trong snapshot mẫu.

Detail item có CVE/source scores, `matches` tăng theo `technology_id` và `priority`. Summary item chỉ có
`cve_id,title,kev,epss_score,cvss_base_score,priority,match_count`; không có metadata technology. Tổng kết được
tính sau filter và trước paging. Rank là KEV trước, EPSS giảm, CVSS giảm, `published_at` giảm theo thời gian
thực, CVE ID tăng; null đứng sau cả giá trị 0. JSON UTF-8 vượt 1 MiB trả 503, không truncate.

## Cursor canonical v1

Cursor là base64url không padding của JSON UTF-8 canonical (sort key, separator compact):
`{"after":"CVE-...","context":"<sha256>","snapshot":"<sha256>","v":1}`. Tối đa 1.024 ASCII.
`context` hash từ `view,kev,asset_id,q đã trim,limit`; `snapshot` hash từ dataset đã validation và toàn bộ
technology snapshot theo ID. Cursor không chứa asset thô. Context sai trả 422 trước dependency; snapshot đổi
sau khi đọc dependency trả 409. `after` phải tồn tại trong tập filter và rank được tính lại từ dữ liệu.

## Mức kiểm chứng

Pytest cục bộ dùng JWT/SQLite/fixture tổng hợp kiểm quyền, strict schema, matching/rank, paging/cursor, byte cap
và SQL bất biến. Wire fixtures `w03-wire-*.json` là response lấy từ API test thật. Chưa kiểm gateway, frontend,
browser, feed/CISA/OpenCTI, Cloudflare/JWKS/HTTPS thật, lab hoặc production.
