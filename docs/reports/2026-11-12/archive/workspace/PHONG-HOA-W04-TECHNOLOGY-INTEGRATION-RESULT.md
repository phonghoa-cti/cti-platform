# W04 Technology Integration — kết quả 12/11/2026

## Kết luận

**PASS mã/HTTP/build và browser desktop cục bộ; mobile 360 px UNVERIFIED.**

Commit cục bộ sạch: `273196e2d23b36172d57cc61b289522786d61b2a` trên
`feat/w04-technology-integration-20261112`. Không push/PR/merge/deploy/lab, không sửa source Backend/Frontend,
không sửa API/core/schema/auth/settings/dependency lock/RUNS.

## Ref và ghép nguồn

- Common base: `8a767314b654d39c1ddc2995b7919c44a5b7027a`.
- Backend source/base integration: `f4c19d44a33fe588046e0e974af9c18cbf8a1a12`, source tree sạch.
- Frontend source: `cfb612f05f6ae57952362580e35ad59d2aff0a3f`, source tree sạch.
- Cherry-pick theo thứ tự: `2419b29656092edcf2bb20b0d7c62a12fa0774c0` thành local
  `0e1e898de29faaedb6deb2a25119545b7912cc64`, rồi `cfb612f05f6ae57952362580e35ad59d2aff0a3f`
  thành local `d5bb1b46e8893cdfbce0dd9f500620ca34fc42b9`.
- Conflict duy nhất khi chuẩn bị: `docs/PROGRESS.md`, giữ cả bằng chứng Backend và Frontend.
- Delta nguồn gốc: Backend so common base 8 file, +1483; Frontend so common base 13 file, +1538/-5.
- Commit code/integration: `f016d6cae6c81424ae6b46618624e1f8a418ccf5`; commit evidence browser:
  `273196e2d23b36172d57cc61b289522786d61b2a`.
- Delta integration cuối so `d5bb1b4`: 71 file, +2116/-24; gồm code/harness, raw log, SQLite snapshot HTTP/helper/browser,
  sanitized trace và sáu screenshot desktop.

## Thay đổi integration

- `/tai-san` inject `createTechnologiesHttpProvider` ổn định theo lifetime wrapper; `/tai-san/mau` giữ fixture.
- Gateway allowlist mới chỉ gồm `/api/assets/technologies` và
  `/api/assets/technologies/{positive-id}`. Route gần đúng, zero/leading-zero/negative, extra segment và traversal
  bị 404; response hợp lệ hơn 1 MiB được stream nguyên vẹn.
- Runner chỉ bật Technology theo scenario opt-in, tạo `AssetStore` và `TechnologyStore` trên cùng `db_path`, gọi
  `initialize()` trong setup trước listener/request; các scenario cũ không tự bật Technology.
- Fixture/helper snapshot đồng thời `technology_assets`, `technology_asset_audit`, `assets`, `asset_audit` và
  draft count; helper vẫn hữu hạn, không tự mở browser.
- Fault committed: một mutation 201, sau đó GET `503,503,200`; DB/audit đúng 1/1. Fault unknown: upstream commit
  một lần nhưng gateway trả 503, GET đối soát `503,200`; DB/audit đúng 1/1. Không có endpoint điều khiển công khai.

## RED → GREEN và kiểm đã chạy

Interpreter Python:
`cti-x01-ingest-browser-prep\.venv\Scripts\python.exe` (Python 3.12 checkout-local đã có).
CWD chính: `cti-w04-technology-integration`; frontend CWD: `portal\web`.

- RED gateway: 13 pass/1 fail, exit 1; đúng nguyên nhân route Technology trả 404.
- RED runner/helper: 8 fail, exit 1; đúng nguyên nhân scenario/store/snapshot Technology chưa tồn tại.
- RED wrapper: 1 fail, exit 1; đúng nguyên nhân không có tab Công nghệ.
- GREEN ma trận HTTP thật: 51 assertion, exit 0. Kiểm CRUD vendor/product/software_version/version,
  duplicate409, stale409, soft-delete/recreate; IT/analyst/multi-role 200, leader403, missing401; same DB;
  Technology không đổi assets/audit hoặc tạo W02 match; domain/CIDR+lookup smoke; timestamp hỏng GET/PUT503 và
  không ghi; list1000 đủ exact schema/first/last, 1001 trả503 và không truncate/ghi/audit.
- Node gateway: 14/14 pass, exit 0.
- Python runner/helper: 42/42 pass, exit 0; regression cleanup Windows đã được test bắt và sửa trước lượt cuối.
- Frontend focused technology+assets+wrapper: 120/120 pass, 6 file, exit 0.
- TypeScript typecheck: exit 0. ESLint: exit 0.
- Next production build: exit 0, compile/typecheck/static generation 9/9. Lần đầu build bằng junction bị
  Turbopack từ chối dependency ngoài root; bản cuối dùng bản sao vật lý dependency đã nghiệm thu, không cài/nâng
  cấp và không đổi lock.
- Ruff check: exit 0. Ruff format check: exit 0. `git diff --check` trên code/docs trước stage: exit 0.
- Helper bounded smoke 30 giây: `status=stopped`, gateway port đóng, temp root xóa.
- Browser desktop bằng Browser tab OpenMausBot: CRUD v1→v2, duplicate/stale409 và confirm delete; leader403;
  committed `POST201 → GET503 → GET503 → GET200`; unknown `POST503 → GET503 → GET200` qua đổi tab. Bốn helper
  đều dừng sạch; DB chứng minh leader0/0 và mỗi fault đúng1row/1audit.

## Evidence và cleanup

Evidence commit tại `w04-technology-integration-evidence/`: raw RED/GREEN, HTTP assertions, sanitized traces,
SQLite snapshot primary/1000/two fault/helper/bốn browser run, sáu screenshot, cleanup, rerun commands và
manifest 58 entry.
SHA-256 của `SHA256SUMS.txt`:
`802c7f7726a2890152044246ac17806b0290d0c7a1643af73e068c60dd814beb`.

Quét evidence không thấy mẫu secret/JWT/key; trace chỉ có counter/method/path/status. Tất cả process/port/temp root
do matrix/helper sở hữu đã đóng/xóa. Junction dependency tạm đã xóa; target còn bản sao `node_modules` ignored để
build, không commit. Target `git status --short --branch` chỉ còn dòng branch, không có thay đổi tracked/untracked.

## Chưa xác minh

- Mobile 360 px bằng resize viewport thật: **UNVERIFIED** vì Browser tab không có điều khiển resize; không giả
  bằng CSS. Desktop đã PASS bằng Browser tab OpenMausBot; công cụ không trả `Recorded as step` nên không có step ID.
- Cloudflare/JWKS/HTTPS thật, lab, production, OpenCTI/W03 matching, feed/NVD/LLM/cloud: ngoài phạm vi và
  **UNVERIFIED**.

## Giải thích cho người mới

Provider là lớp giao diện dùng để gọi API; wrapper giữ provider ổn định để thao tác đang chờ không bị mất khi
React render lại. Allowlist là danh sách đường dẫn gateway cho phép, giúp route gần giống không vô tình đi qua.
Hai store dùng chung một file SQLite nhưng sở hữu bảng/audit riêng, nên Technology không làm thay đổi tài sản
domain/CIDR. Fault tổng hợp mô phỏng mất phản hồi sau khi server đã ghi để chứng minh UI chỉ đối soát bằng GET,
không gửi lại mutation và tạo bản ghi trùng.

## Hoàn tác

Trước khi nhánh được tích hợp, hoàn tác bằng cách bỏ hai commit local `273196e` và `f016d6c` theo quy trình Git
của Leader; không
cần migration production vì chỉ có DB tạm tổng hợp. Không tự merge hoặc deploy commit này.
