# PHONG HỎA W05 — KẾT QUẢ TÍCH HỢP CỤC BỘ

Ngày kiểm: 2026-11-11 (Asia/Saigon)

## Kết luận

PASS cho phạm vi test-only cục bộ sau rework R1–R4. UI snapshot không đổi đã chạy qua gateway same-origin HTTP loopback tới FastAPI thật, dùng JWT RSA tổng hợp được xác minh chữ ký/issuer/audience/expiry/subject, role phía server và SQLite tạm. Gateway xử lý request target lỗi và stream lỗi sau headers mà không dừng dịch vụ; cleanup best-effort có thể thử lại tài nguyên chưa đóng; mỗi `LocalRun` chỉ được start một lần. Đây không phải tích hợp lab, HTTPS/JWKS thật, OpenCTI hoặc triển khai production.

## Provenance và Git

- Worktree: `$WORKSPACE\cti-w05-local-integration`
- Branch: `feat/w05-local-integration-20261111`
- Base backend: `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`
- UI source: `a791a3f2be19b4c1593f82706c47b5dca97ab51a`
- `portal/web` tree ở HEAD: `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`
- `git diff a791a3f2be19b4c1593f82706c47b5dca97ab51a -- portal/web`: 0 file; không đổi hành vi/source UI.
- Commit provenance: `8fc34e7` (`chore(integration): import portal web snapshot`)
- Commit settings/runtime: `5b8aed2` (`feat(integration): add fail-closed loopback settings`)
- Commit gateway/runner: `688ff99` (`feat(integration): add owned loopback gateway runner`)
- Commit matrix/browser docs: `12ad2767a5a0ed46cc89ba529ff7d7d878e88fb4` (`test(integration): prove local browser decision flow`)
- Commit rework R1–R3/HEAD cuối: `0a38e918c5967f6b98f95827ffffa1790de68598` (`fix(integration): harden gateway and cleanup failures`)
- Commit rework R4/HEAD cuối: `d94afb1e24929f64f82a921cd29307be175fb04e` (`fix(integration): make local runs single-use`)
- Trạng thái cuối: `git status --porcelain` = 0 dòng.

## Cấu hình và dependency

- Production không bị nới: `Settings.from_env()` và constructor thường vẫn chỉ nhận HTTPS.
- Factory nội bộ test-only chỉ nhận đúng `http://127.0.0.1:<port>` và DB mới nằm trong temp root của run.
- `requirements-api.lock` SHA-256: `c4cff04044acd2d95064f38d27e57307d6c6a10893e4152beebee3a9bc9b5374`.
- Uvicorn `0.54.0` được khóa bằng hai SHA-256: `505bdb0f318731d45f1f712071fc781a8981f6847a31c902c9f5e652d4f67faf` và `a2e33cbfaa0306f8e6b0c13e0cb89d7d7a2da3e62b90c66e18c33d9807b28620`.
- `npm ci` dùng lock hiện có; không sửa `portal/web`.

## Acceptance matrix

| Nhóm | Kết quả | Bằng chứng |
|---|---:|---|
| Settings production HTTPS fail-closed + factory loopback test-only | PASS | pytest toàn repo; test settings/runtime |
| Gateway giữ status/body/header/cookie, bỏ hop-by-hop/dynamic hop, thay JWT caller | PASS | Node 3/3 |
| Không tự tạo Origin; sai Host/body quá cỡ/timeout; không retry | PASS | Node 3/3 |
| JWT chữ ký/issuer/audience/expiry/subject và role phía server | PASS | ma trận HTTP 56 check / 7 scenario |
| Missing token, expired, wrong signature, insufficient role | PASS | HTTP thật qua gateway: 401/403 đúng hợp đồng |
| Approve/reject, self-review policy, optimistic conflict, audit đúng một lần | PASS | HTTP matrix + SQLite hậu kiểm |
| Origin/content-type/schema request | PASS | wrong/missing Origin 403; text/plain 415; role dư 422 |
| POST đã ghi nhưng refresh 503 | PASS | quyết định/audit còn nguyên, không retry; UI hiển thị nút tải lại |
| UI hàng đợi thật, approve, reject, sample mode | PASS | Trình duyệt tích hợp; ảnh trong evidence |
| Cleanup | PASS | 0 tiến trình owned, 0 temp dir `w05-local-*`, không còn listener của hai run browser |

## Rework R1–R3

- RED repo: Node hiện 4 ca mới fail rồi còn socket treo nên được ngắt thủ công sau 30 giây; Python runner có 3 ca cleanup fail, exit 1. Đây là lỗi mong đợi trước sửa, không được tính là lượt xác minh cuối.
- R1: request target `http://[` trả JSON `400 invalid_request_target`, `Cache-Control: no-store`; gateway không thoát và request hợp lệ kế tiếp đạt.
- R2: timeout sau khi upstream đã flush headers đóng downstream trong hạn; upstream abort và client abort đều được xử lý; gateway tiếp tục phục vụ và không retry POST.
- R3: lỗi dừng một child không bỏ qua UI/API/temp; lỗi temp tạm thời được retry ở `close()` sau; temp chỉ xóa sau khi API thread xác nhận đã dừng. Có regression cho success, fault, retry, TTL, partial start và sentinel không thuộc run.
- Probe Leader giữ nguyên: Node `2/2` và Python `2/2`, đều exit 0.
- Regression sau commit: gateway `7/7`; settings + runner `27/27`, 0 failure/error/skip; HTTP `56` check / `7` scenario; Ruff/check-format/diff-check đều exit 0.
- Cleanup đọc lại sau toàn bộ probe: 0 process, 0 listener và 0 temp dir thuộc harness.

## Rework R4

- RED repo: ba regression lifecycle đều fail trước sửa; `start→close→start`, `close→start` và `failed-start→start` đều có thể cấp tài nguyên lại. Regression RED tự thu hồi đúng handle do test tạo; hai gateway mồ côi của lượt RED đầu tiên đã được định danh theo PID/command line và dừng theo PID.
- Hợp đồng cuối: mỗi instance `LocalRun` chỉ được start một lần. Trạng thái lifecycle tách khỏi temp handle và chuyển khỏi `new` trước `_require_available_port` hay tạo temp/process/thread.
- Mọi start sau khi đang chạy, đã close, close-before-start hoặc start thất bại đều bị `RuntimeError` trước cấp tài nguyên. `close()` vẫn idempotent và retry cleanup ở trạng thái `cleanup-pending` như R3.
- Probe Leader R4 loopback thật: `1/1` pass, exit 0. Bốn probe R1–R3 vẫn đạt: Node `2/2`, Python `2/2`, exit 0.
- Runner sau commit: `11/11`, 0 failure/error/skip; gồm success, sentinel, fault cleanup, retry, API-before-temp, TTL, partial start và ba lifecycle regression.
- Ruff/check-format/diff-check exit 0. UI tree vẫn `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`, diff source 0 file.
- Cleanup cuối: 0 process, 0 listener, 0 temp dir thuộc harness; Git tree sạch.

## Kiểm tra đã chạy

- `python -m pytest --junitxml=<evidence>/pytest-full.xml` → exit 0, `385 passed in 20.87s`.
- `python tools/local_integration/tests/run_http_matrix.py` → exit 0, `56` checks, `7` scenarios, PASS.
- `node --test tools/local_integration/tests/test_gateway.mjs` → exit 0, `3/3` pass.
- `python -m ruff check portal_api tools/local_integration` → exit 0.
- `python -m ruff format --check portal_api tools/local_integration` → exit 0, 14 files formatted.
- `npm test` → exit 0, 5 files, `52/52` tests.
- `npm run typecheck` → exit 0.
- `npm run lint` → exit 0.
- `npm run build` → exit 0; `/`, `/duyet`, `/duyet/mau` prerender thành công.
- `git diff --cached --check` trước commit → exit 0.

Lần gọi pytest đầu tiên dùng sai cú pháp PowerShell cho `--junitxml`, exit 4 và không chạy test; đã ghi trong log, sửa thành một đối số `--junitxml=<path>`, chạy lại exit 0 với 385 test.

## Quan sát browser

- `admin-other`: tải 4 draft thật từ API; duyệt draft #4 làm hàng đợi còn 3; chọn draft #2, nhập lý do và từ chối làm hàng đợi còn 2. Trang hiển thị trạng thái đã từ chối.
- `/duyet/mau`: tải 3 mẫu tổng hợp và nút quyết định bị vô hiệu; không dùng API thật để thay đổi trạng thái.
- `post-ok-refresh-503`: sau approve, UI hiển thị cả thông báo quyết định đã ghi và cảnh báo không tải lại được trạng thái; browser quan sát hai GET refresh trả 503. Ma trận hậu kiểm xác nhận một review và một audit, không POST lại.

## Cleanup và giới hạn

- Hai gateway mồ côi từ các lần chạy lỗi trong lúc phát triển đã được định danh đúng command line/PID, dừng theo PID; temp DB tương ứng đã xóa. Kiểm cuối: 0 tiến trình gateway/Next/runner thuộc worktree và 0 thư mục temp `w05-local-*`.
- Mỗi run cuối chỉ bind `127.0.0.1`, có TTL và được đóng bằng handle do runner sở hữu.
- Không dùng secret thật, không ghi JWT/key ra file/log/browser, không thay trust store, không bỏ TLS validation, không giả Origin, không mở listener ngoài loopback.
- UNVERIFIED ngoài phạm vi: Cloudflare Access/JWKS thật, HTTPS local được tin cậy, lab, OpenCTI, dữ liệu thật, push/PR/merge/deploy.

## Evidence

Thư mục: `$WORKSPACE\local-integration-evidence`

- `python-regression.log`, `pytest-full.xml`
- `integration-matrix.log`
- `ui-regression.log`
- `provenance-cleanup.log`
- `browser-admin-approve-reject.png`
- `browser-refresh-503.png`
- `SHA256SUMS.txt`
- `rework-r1-r3/repo-gateway-red.log`, `repo-runner-red.log`: RED trước sửa.
- `rework-r1-r3/leader-gateway-green.log`, `leader-cleanup-green.log`: probe Leader GREEN.
- `rework-r1-r3/repo-regression-green.log`, `http-quality-green.log`: regression GREEN trước commit.
- `rework-r1-r3/final-verification.log`, `settings-runner.xml`: xác minh sau commit.
- `rework-r1-r3/SHA256SUMS.txt`: manifest riêng cho rework.
- `rework-r4/repo-runner-red.log`: RED trước sửa.
- `rework-r4/leader-restart-green.log`, `precommit-green.log`: R4 và probe cũ GREEN trước commit.
- `rework-r4/final-verification.log`, `runner.xml`: xác minh sau commit.
- `rework-r4/SHA256SUMS.txt`: manifest riêng cho R4.
