# PHONG HỎA W03 filter fix result — 2026-11-12

## Kết quả

- Base: `f650f04de8f08238e13e2630f974e9f30ef838b5`
- HEAD/commit: `7ff62711f4304aefda9a6fc640d05039fd0cd9af`
- Commit: `fix(portal): align unchecked KEV filter`
- Nhánh: `feat/w03-read-frontend-20261112`
- Working tree sau commit: sạch.
- Diff: 4 file, 39 dòng thêm, 1 dòng xóa.

Adapter `createCvesHttpProvider` nay chỉ thêm `kev=true` khi checkbox “Chỉ KEV” bật. Khi bỏ chọn, adapter bỏ hẳn tham số `kev`, giữ nguyên GET/no-store và các filter khác. Không đổi Backend, sample provider hoặc nhãn UI.

## TDD RED → GREEN

Focused command:

`portal/web/node_modules/.bin/vitest.cmd run tests/cves-http.test.ts tests/cve-app.test.tsx`

- RED exit 1: 1 file fail, 1 file pass; 1 fail, 52 pass, tổng 53.
- Sai khác đúng mục tiêu: expected `/api/cves?limit=10`, received `/api/cves?kev=false&limit=10`.
- GREEN exit 0: 2/2 files, 53/53 tests pass.
- Production fix tối thiểu: thay một dòng để chỉ `parameters.set("kev", "true")` khi `query.kev` là true.
- Regression component xác nhận `kev=false` được giữ qua đổi checkbox, trang sau và retry thủ công; regression true hiện có tiếp tục xác nhận URL gửi `kev=true`.

## Probe Leader nguyên bản

- Probe: `leader-w03-integration-review-20261112/kev-checkbox-probe.test.ts`
- SHA-256 trước/sau: `1756efa94d8e2fa77f8108f1c6f309e20a584aaa32cb9c130663b38fd085a797` (không đổi).
- Config gốc không được dùng vì alias sang integration tree.
- Config evidence `w03-filter-fix-evidence/vitest.frontend.config.ts` alias sang đúng frontend tree.
- Lần chạy config evidence đầu exit 1 trước khi chạy test: `vitest/config` không resolve vì config nằm ngoài cây có `node_modules`.
- Config được sửa thành object thuần; lần hai exit 0: 1 file, 3/3 tests pass.
- Warning Vite về ESM trong CommonJS được giữ nguyên trong evidence; không ảnh hưởng kết quả test.

## Kiểm chứng cuối

| Lệnh | Exit | Kết quả |
|---|---:|---|
| focused W03 Vitest | 0 | 2 files, 53/53 |
| Leader probe với config frontend evidence | 0 | 1 file, 3/3 |
| `npm run typecheck` | 0 | không lỗi |
| `npm run lint` | 0 | không warning/error |
| `git diff --check` | 0 | không lỗi whitespace |
| kiểm allowlist/name-only | 0 | đúng 4 file |
| `git status --short` sau commit | 0 | rỗng |

Không chạy full suite 356 hoặc build theo brief vì production chỉ đổi một nhánh query adapter, không đổi component runtime/framework. Không chạy browser/backend/gateway/deps/feed/OpenCTI/lab/production.

## File trong commit

- `docs/PROGRESS.md` (+4/-0)
- `portal/web/data/cves-http.ts` (+1/-1)
- `portal/web/tests/cve-app.test.tsx` (+23/-0)
- `portal/web/tests/cves-http.test.ts` (+11/-0)

`portal/web/data/cves-http.ts` khớp `.gitignore:20:data/` và được stage rõ bằng `git add -f`.

## SHA-256

- `docs/PROGRESS.md`: `5840c3d85ae8f335752f378cc30341df3c8df8140ccae56a3b70098c929ecafa`
- `portal/web/data/cves-http.ts`: `7519e8a51173c0b29083973bdc082fd64a2ed86f3f3db04bb15731f321c8dc18`
- `portal/web/tests/cve-app.test.tsx`: `676c8e35b248380f1d62f0f3bfb12722008c452f7ed12c1c6b257dd2f6ce37d7`
- `portal/web/tests/cves-http.test.ts`: `57a7c8bba12ed9701378b1167c5efaa83de0932be8b58cca99dae7497dfedd0d`
- evidence config: `8e4f40c62c6521602a433daf71096a8393e059d7d5612fa2078658065fc45d00`

## Giới hạn

Chỉ chứng minh hành vi adapter/component bằng test cục bộ. Không tuyên bố Backend/API/gateway/browser/feed/OpenCTI/lab/production đạt. Không push, PR, merge hoặc deploy.
