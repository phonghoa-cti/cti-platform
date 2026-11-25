# W03-STATUS-INTEGRATION-PREP — kết quả

Ngày 12/11/2026. Trạng thái: **PASS cục bộ cho prep HTTP**, không phải nghiệm thu UI/browser hay toàn W03-S1.

## Git và phạm vi

- Tree: `cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Base: `4f7100cf83e57b1cb30a12472ed71a0cd985a413`
- Final: `32b5c068c4d6da5a0abb00906c619f92f13b9177`
- Commit: `feat(integration): prepare W03 status HTTP harness`
- Diff: 8 file, `+641/-7`; chỉ `tools/local_integration/**`, `docs/PROGRESS.md`, `docs/specs/W03-status-local-contract.md`.
- Brief SHA-256 đã đối chiếu: `a28f77c85f88b303286a45d15dced53bdb1efac6f7973c959dcf0a3b3d0859ea`.
- Không cherry-pick Frontend `13b80252`; không sửa `portal_api`, core/auth/frontend/deps/RUNS; không push/PR/merge/deploy.

## Đã thực hiện

- Gateway allowlist chính xác GET/PUT status và GET status-history; giữ query, thay JWT phía server và chặn method/path gần đúng.
- PUT status có cap riêng 16 KiB; cap 8 KiB cũ và cap v1 64 KiB không đổi.
- Runner opt-in tạo `CveStatusStore` cùng SQLite W04/TechnologyStore, migration/seed explicit trước listener; scenario cũ không tự bật status.
- Fixture CVE được copy vào temp root sở hữu để kiểm dataset snapshot drift mà không sửa fixture repo.
- Fault hữu hạn: known commit PUT 200 rồi GET `503→503→200`; unknown outcome upstream commit một lần, PUT 503 rồi GET `503→200`. Trace chỉ có counter/method/path/status; không chứa JWT/body.
- Ma trận socket gateway/API thật kiểm IT/analyst/admin/mixed, leader 403, thiếu JWT 401, JWT client không nâng quyền; Origin/media/strict bool/fraction/duplicate key; no-store/Vary; route/method allowlist.
- Kiểm unset GET không tạo row; PUT v1/audit1, update v2/audit2; paging/cursor stale; stale status/context; first-write concurrency; W04 version/note drift, case-only display, dataset drift, delete/recreate và identity change; schema lỗi/unconfigured không tự migration.
- Payload JSON hợp lệ có Unicode escape dài hơn 8 KiB nhưng không quá 16 KiB đạt; trên 16 KiB trả 413 và SQL không đổi.

## Kiểm tra mới nhất

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `node --test tools/local_integration/tests/test_gateway.mjs` | 0 | 16/16 PASS |
| `python -m pytest tools/local_integration/tests/test_runner.py portal_api/tests/test_cves_status_api.py -q` | 0 | 98/98 PASS (49 runner + 49 Backend status) |
| `python -m tools.local_integration.tests.run_w03_status_matrix ...` | 0 | 144 assertion PASS |
| `python -m tools.local_integration.tests.run_w03_matrix ...` | 0 | 120 check, 8 scenario PASS |
| `python -m tools.local_integration.tests.run_w04_technology_matrix ...` | 0 | 51 assertion PASS |
| `python -m ruff check tools/local_integration` | 0 | All checks passed |
| `python -m ruff format --check tools/local_integration` | 0 | 19 file formatted |
| `git diff --cached --check` trước commit | 0 | sạch |

TDD: gateway probe RED `404 != 200`, runner probe RED vì scenario chưa được phép; sau implementation hai probe GREEN. Lần chạy Python đầu tiên dùng nhầm venv thiếu `httpx` là lỗi setup trước collection, sau đó dùng đúng `cti-w03-read-backend/.venv` và kiểm tra đạt; không tính lần setup đó là lỗi sản phẩm.

## Evidence và cleanup

- Evidence: `w03-status-integration-prep-evidence/`
- Ma trận chính: `http-matrix.json`; raw JUnit: `gateway-junit.xml`, `runner-junit.xml`, `backend-status-junit.xml`.
- Trace phục hồi: `http/w03-status-known-commit-trace.jsonl`, `http/w03-status-unknown-outcome-trace.jsonl`.
- SQL trước cleanup: ba file `*-before-cleanup.sqlite`; smoke W03-R/W04 có JSON, trace, wire và backup riêng.
- Manifest: `SHA256SUMS.txt`.
- Mỗi LocalRun xác nhận đóng port/xóa temp root do nó sở hữu; test cleanup runner đạt. Các thư mục `w05-local-*` còn thấy có timestamp 22:12 và 00:21, tồn tại trước lượt 04:xx này nên không bị xóa nhầm.
- Git tree sau commit sạch.

## Chưa xác minh

- Frontend F5/F6 và việc ghép candidate Frontend.
- UI, browser desktop/mobile, toàn W03-S1.
- Cloudflare/JWKS/HTTPS thật, feed/OpenCTI, lab, production và dữ liệu thật.

## Học thêm

- **Optimistic version** là số phiên bản giúp phát hiện người khác đã sửa bản ghi trước khi mình ghi.
- **Unknown outcome** là lúc server có thể đã commit nhưng client mất response, nên chỉ GET đối soát và không gửi lại PUT.
- **SQL non-mutation** là bằng chứng snapshot database không đổi sau GET hoặc lỗi bị từ chối.
