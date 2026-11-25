# W03-S2 — read model trạng thái danh sách CVE cục bộ

## Phạm vi và quyền

`GET /api/cves/status-view` là route opt-in riêng, không đổi `GET /api/cves` hay ba route W03-S1.
`it|analyst|admin` (kể cả mixed role) nhận `view=detail`; leader-only nhận `view=summary`; role khác bị 403.
Auth và role chạy trước query/dependency. Leader có key `asset_id` hoặc `status` luôn bị 403 trước parse và trước
dataset/SQLite.

Query base `kev,asset_id,q,limit,cursor` giữ bounds W03-R và thêm
`status=unset|open|patching|patched|not_affected|review_required`. Query lạ/lặp/malformed hoặc cursor route khác
trả 422 `invalid_cve_status_query`; asset detail không tồn tại trả 404 `technology_not_found`; snapshot đổi trả
409 `status_snapshot_changed`; dependency/schema/row/cap lỗi trả 503 `cves_unavailable`.

## Ghép relation và projection

Status thuộc relation `(technology_id,cve_id,vendor_key,product_key)`. `unset` là không có row và được trả bằng
`status/status_version/status_updated_at=null, review_required=false`. Row hiện có được validator S1 kiểm đầy đủ;
dataset ID hoặc `technology_record_version` lệch đặt `review_required=true` nhưng không đổi status. Technology
inactive/deleted/không match và status key cũ không tạo relation hiển thị.

Status filter chọn CVE khi ít nhất một relation đạt, nhưng detail trả mọi relation của CVE trong base scope. Base
filter và ghép status diễn ra trước phân trang; rank vẫn KEV → EPSS → CVSS → published → CVE. Summary Leader giữ
đúng item W03-R và đúng năm field `matched_cves,kev_cves,actionable_cves,overdue_kev_cves,as_of_date`, không có
metadata/status relation. Detail thêm bốn field status trên match; summary thêm năm bucket relation và số relation
`review_required`.

`actionable_cves` đếm CVE duy nhất có relation unset/open/patching/review_required. `overdue_kev_cves` đếm CVE
actionable thuộc KEV, có due date hợp lệ nhỏ hơn ngày UTC lấy đúng một lần/request; bằng hôm nay và null không quá
hạn. Status tự khai không phải bằng chứng kỹ thuật đã vá.

## Snapshot, cursor và an toàn đọc

Dataset được đọc/validate đúng một lần. Technology active và toàn bộ status row được đọc trong một transaction
trên một connection SQLite `mode=ro`, có kiểm schema W04/S1; GET không initialize/migrate/DDL/audit/write. Nếu
TechnologyStore và CveStatusStore không trỏ cùng DB thì route fail closed 503.

Cursor canonical base64url JSON gồm đúng `{v:1,kind:"w03-status-view",snapshot,context,after}`. Context chứa
view/base query/status/limit/domain marker và không chứa ngày. Snapshot chứa fingerprint/dataset ID, hash toàn bộ
Technology/status đã validate và `as_of_date`; dataset/technology/status/ngày đổi trả 409. Context khác,
non-canonical, malformed, cross-route hoặc `after` không còn trong tập filter trả 422. Response UTF-8 vượt 1 MiB
trả 503, không truncate. Mọi response giữ `Cache-Control: no-store` và `Vary: Cf-Access-Jwt-Assertion`.

## Mức kiểm chứng

Fixture `w03-status-view-detail|leader|error.json` được đối chiếu với API in-process từ JWT RSA, dataset và SQLite
tổng hợp. Test dùng DB tạm WAL và writer thật để commit giữa hai phép đọc, chứng minh reader vẫn thấy một snapshot;
không sleep/poll. Đây không phải bằng chứng feed/CISA/OpenCTI, gateway/browser, Cloudflare/JWKS/HTTPS, lab hay
production.
