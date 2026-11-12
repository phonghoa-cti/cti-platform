# W05 Selection Integration — kết quả

Ngày 11/11/2026. **PASS cục bộ** cho gateway v1, ma trận selection/legacy, browser same-origin và cleanup.

## Git và phạm vi

- Tree: `cti-w05-selection-integration`
- Branch: `feat/w05-selection-integration-20261111`
- Base: `43737c000561c4d676705dbb564223a7bfa3596e`
- HEAD: `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`
- Commit: `test(integration): verify W05 selection workflow`
- Diff base→HEAD: 8 file, +550/-16; chỉ `tools/local_integration/**`, ADR/PROGRESS và `portal_api/README.md`.
- Trạng thái tree sau rework bằng chứng: sạch; không tạo commit rỗng vì repo source không đổi.
- UI subtree giữ nguyên: `dffcc2fa8f11a24ea34f5fe4c71e995bd68549f2`.
- `requirements-api.lock`: `D7C4951881C13C9904ABD6DC5D57C7B08D24BDB8675502824B6A014C5BCEF11F`.
- `portal/web/package-lock.json`: `63B538F51C26DB0DA8CF7050E4A4F18E78E227F8DC9B8A92BFE41A446BB1524A`.

Không sửa UI/API/core/settings/auth/dependency/lock/source tree hoặc RUNS. Không push/PR/merge/deploy/lab.

## Thay đổi

- Gateway allowlist đúng legacy và bốn path v1; giữ cap legacy 8.192 byte, v1 65.536 byte kể cả chunked; ngoài
  allowlist trả 404/no-store.
- Runner giữ 4 fixture legacy; chỉ scenario selection thêm fixture tổng hợp có 2 IOC eligible. Save-fault và
  decision-fault là hai run riêng; decision-fault bắt đầu từ snapshot đã lưu version 1.
- Thêm ma trận HTTP v1 hậu kiểm SQLite: selection/no-op/empty, approve/reject, auth/role/self-review,
  Origin/content-type/body/index/identity, stale/terminal conflict, payload bất biến và final audit snapshot/hash.
- Cập nhật ADR, tiến độ và hướng dẫn chạy harness.

TDD đã quan sát: hai test gateway mới đỏ 404 trước sửa rồi xanh 9/9; hai test runner mới đỏ vì scenario chưa có,
sau đó xanh 13/13.

## Kiểm chứng vừa chạy

| Nhóm | Kết quả | Exit/bằng chứng |
|---|---:|---|
| Gateway Node | 9/9 | 0 · `gateway-node.log` |
| Python harness/settings/API/core selection | 182/182, 0 fail/error | 0 · `python-targeted.junit.xml` |
| HTTP legacy | 56 checks / 7 scenario | 0 · `legacy-http-matrix.log` |
| HTTP selection v1 | 113 checks / 10 scenario | 0 · `selection-http-matrix.log` |
| UI Vitest | 89/89 | 0 · `ui-test.log`, `ui-test-verbose.log` |
| UI typecheck/lint/build | PASS; build có `/duyet`, `/duyet/mau` | 0/0/0 |
| Ruff check/format | PASS | 0/0 |
| `git diff --check` | PASS | 0 |
| Browser tích hợp | PASS happy/empty/reject/sample/save-fault/decision-fault và retry GET-only quan sát thật | `browser/STEPS.md`, `rework-evidence/` |
| Browser→SQLite cùng run | PASS; payload immutable, selection v1 `[1]`, review v2, hash audit khớp | `browser-happy-audit.json` |
| Cleanup | PASS trên 3 run rework: exact listener/PID/thread/temp sạch sau close | `rework-evidence/*-run.json` |

Mọi exit cuối nằm trong `fresh-exit-codes.json`; raw log/JUnit và ảnh nằm ở
`w05-selection-integration-evidence/`.

Rework R1/R2 không chạy lại suite/build vì source không đổi. Hai fault và `/duyet/mau` được chạy lại bằng
Trình duyệt tích hợp; trace sanitized chỉ ghi method/path/status, audit được đọc trong cùng run trước close.
`cleanup.log` cũ được giữ raw nhưng correction rõ: Windows `10035` là `WSAEWOULDBLOCK`, không phải connection
refused. Bằng chứng cleanup hợp lệ là OS listener ownership cùng exact PID/temp trong `rework-evidence/`.

## Tiêu chí

- **PASS routing/body/header:** bốn route v1 đi qua API thật; legacy 56 checks giữ nguyên; query/status/no-store/
  Origin được giữ; 65.536 byte tới API, 65.537 trả 413, legacy >8.192 vẫn 413.
- **PASS selection/decision:** save version 1, no-op không tăng version/event; approve review version 2; final
  audit giữ selection version/hash/indices; payload và `items.keep` không đổi.
- **PASS empty/reject/policy:** empty save hợp lệ và approve 403; reject có reason/audit; auth/role/self-review,
  invalid input, stale/repeated/terminal đều fail closed và không thêm write.
- **PASS refresh fault/no retry:** hai run riêng giữ confirmation; browser bấm retry đúng một lần ở mỗi fault;
  trace giữa marker chỉ có GET 503, tổng run không replay POST; audit cùng run có đúng số event/snapshot/hash.
- **PASS browser thật:** đã thao tác trên Trình duyệt tích hợp được cấp, không mở browser khác/giả viewport.
- **PASS sample isolation:** trace `/duyet/mau` riêng không có request drafts legacy/v1.
- **PASS cleanup:** ba browser run rework chứng minh listener owner trước close và 0 listener/exact PID/thread/temp
  owned còn lại sau close; không dùng glob stop/delete.

## Chưa kiểm và giới hạn

- **UNVERIFIED ngoài phạm vi:** Cloudflare Access/JWKS/HTTPS thật, lab, OpenCTI, feed/LLM và production.
- `npm ci` từ lock báo 9 advisory mức moderate; dependency/lock không đổi và không tự chạy `npm audit fix` trong
  task tích hợp này.
- Audit SQLite là trace cục bộ, không chống người có quyền sửa file DB.

Hoàn tác commit: `git revert d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`.

## Học thêm

- **Allowlist:** danh sách path được phép proxy; path khác bị chặn thay vì chuyển tiếp tùy ý.
- **Snapshot:** tập IOC đã lưu tại một version; decision tham chiếu đúng snapshot đó.
- **No-op:** save cùng tập lựa chọn không tăng version hoặc tạo event mới.
- **Owned cleanup:** mỗi run chỉ dừng/xóa process, port và thư mục do chính nó tạo.
