# PHONG HỎA — W03-STATUS-INTEGRATION RESULT

Ngày kiểm: 12/11/2026 (Asia/Saigon). Kết luận: **PASS local integration**, gồm wire thật, component, browser desktop, trace/SQLite và cleanup. Không phải bằng chứng lab/production.

## Git và phạm vi

- Worktree: `$WORKSPACE/cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Prep base: `65e31980ac01910b825951676bae428ca3bf1742`
- Final HEAD: `a2c4ffa245297a8714b0023bf4e4bb248869dc36`
- Frontend mapping: `e31f0b40 -> 57c1dc1`, `13b80252 -> 0241b29`, `2448b860 -> 5ee40dc`.
- Integration helper commits: `7be19ca` (scenario + SQL counts), `a2c4ffa` (real-wire capture + production parser gate).
- Delta base..HEAD: 19 files, `+1177/-7`; product UI khác base chỉ do ba cherry-pick đã nghiệm thu. Phần thêm của integration nằm trong `tools/local_integration/**` và `portal/web/tests/**`.
- `git status --porcelain=v1`: rỗng. `git diff --check 65e3198..HEAD`: exit 0.

## Kiểm mới đã chạy

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `python -m pytest tools/local_integration/tests/test_w04_browser_helper.py -q` | 0 | 6 passed |
| `python -m tools.local_integration.tests.run_w03_status_matrix ...` | 0 | 150 assertions PASS |
| `python -m tools.local_integration.tests.capture_w03_status_wire ...` | 0 | 6 fixture thật: unset, committed, history, review-required, conflict 409, unavailable 503 |
| `W03_STATUS_WIRE_REQUIRED=1` nhưng thiếu thư mục fixture + Vitest | 1 mong đợi | RED đúng: thiếu fixture không bị skip |
| Vitest `cve-status-wire-capture.test.ts` với fixture vừa chụp | 0 | 4 passed; parser/provider production đọc toàn bộ wire |
| Vitest `cve-status.test.ts cve-status-panel.test.tsx cve-app.test.tsx` | 0 | 58 passed / 3 files |
| `npm run typecheck` | 0 | PASS |
| `npm run lint` | 0 | PASS |
| `npm run build` | 0 | PASS; `/lo-hong` và `/lo-hong/mau` được build |
| Ruff check + format-check helper/capture | 0 | PASS |

Python dùng môi trường local đã có tại checkout `cti-w03-read-backend/.venv`; không đổi dependency hoặc lockfile.

## Browser desktop, trace và SQLite cùng lượt

Tất cả phiên dùng Browser tab OpenMausBot, gateway loopback, helper có TTL và run_id riêng.

1. **Regular** `baae38c2...`: lưu v1 rồi v2, lịch sử hiển thị mới nhất trước (`#2`, `#1`). Trace có đúng 2 PUT status; SQLite cuối có 1 record / 2 audit. Ảnh `browser-regular/regular-two-saves-history.jpg`.
2. **Known commit** `d0b72652...`: PUT 200 rồi GET status `503 -> 503 -> 200`; notice đã lưu tồn tại trong lúc đối soát, không replay PUT. Trace đúng 1 PUT; SQLite 1/1. Ảnh `browser-known/known-recovered.png`.
3. **Unknown outcome** `f871e8f5...`: PUT trả 503 sau upstream commit; UI khóa ghi và chỉ GET đối soát. Chuỗi `GET 503 -> 200` (lần 200 sau browser remount), trace đúng 1 PUT; SQLite 1/1. Ảnh `browser-unknown/unknown-reconciled.jpg`.
4. **Context conflict** `2c8d4502...`: lưu baseline v1, setup công nghệ v2 cùng DB, PUT status bối cảnh cũ trả 409, UI hiện cảnh báo nhập/xác nhận lại và `review_required`; SQLite vẫn 1 record / 1 audit, chứng minh PUT 409 không ghi thêm. Ảnh `browser-conflict/context-conflict.jpg`.
5. **Smoke** `8ce36793...`: bộ lọc `3 KEV -> 16 tất cả -> 3`; `/lo-hong/mau` chỉ tải tài sản tĩnh, trace không có status/history/mutation; SQLite status/audit 0/0.

Mọi state cuối đều `status=stopped`, `gateway_port_closed=true`, `temp_root_removed=true`; stderr helper rỗng.

## HTTP/SQL bổ sung

- Ma trận 150 assertion chứng minh history cursor cũ trả 409 rồi restart 200, context/version conflict không mutation, 16 KiB boundary, auth/allowlist, role, race, schema opt-in, relation khác/history không tiêu thụ fault, và known/unknown mỗi lượt đúng 1 PUT + 1 audit.
- Trace browser không chứa token/body/secret; chỉ method/path/status/counter.
- UI history cursor 409 không thể phát sinh trực tiếp với fixture browser chỉ có hai audit và page limit 25; nhánh này được kiểm ở HTTP thật và component test, không tuyên bố đã bấm trên browser.

## Bằng chứng và giới hạn

- Evidence: `$THREADS/484d57b0-1cb9-4264-b24a-54cecff6e454/w03-status-integration-evidence/recovery-20261112`
- Manifest: `MANIFEST.sha256`, 69 artifact, SHA256 `f6a4543e041c4fdabde40e7827aaf41bf3f99a13580016a1c39b5d4696715066`.
- UNVERIFIED: mobile viewport, Cloudflare/JWKS/HTTPS, OpenCTI, lab, production, dữ liệu/feed thật và LLM thật.
- Không push, PR, merge, deploy, sửa RUNS, secret, dependency/lockfile hay source tree khác.

Hoàn tác cục bộ: revert `a2c4ffa`, `7be19ca`, rồi ba commit `5ee40dc`, `0241b29`, `57c1dc1` theo thứ tự ngược; không dùng reset trên tree có thay đổi người dùng.
