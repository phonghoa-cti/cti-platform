# PHONG HỎA W03 frontend rework result — 2026-11-12

## Kết quả

- Candidate/base rework: `5c968c74cc53c5798bcf8adaf8695dacfd86ffd4`
- HEAD/commit mới: `f650f04de8f08238e13e2630f974e9f30ef838b5`
- Commit: `fix(portal): harden CVE response ownership`
- Nhánh: `feat/w03-read-frontend-20261112`
- Working tree sau commit: sạch.
- Diff candidate..HEAD: 5 file, 170 dòng thêm, 11 dòng xóa.

## Thay đổi

- F1: parser chỉ nhận đúng literal notice r1 cho cả detail và summary:
  `Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.`
- F2: parser từ chối `cveId` trùng ở detail/summary; từng detail item chỉ nhận `technologyId` tăng nghiêm ngặt, do đó đồng thời từ chối trùng và giảm. Không sort/dedupe payload.
- F3: response và options công nghệ có ownership theo provider/context hiện hành. Bắt đầu load mới xóa response/notice/options/detail cũ và vô hiệu callback công nghệ; chỉ response detail do provider hiện hành hoàn tất mới được gọi Technology provider.
- Regression bao phủ detail→pending summary, summary→detail, detail→detail, đổi provider riêng, đổi Technology provider riêng, đổi cả hai, stale resolve/reject, loading/notice/options, filter và 409 hiện có.

## TDD RED → GREEN

Lệnh focused:
`portal/web/node_modules/.bin/vitest.cmd run tests/cves-http.test.ts tests/cve-app.test.tsx`

- RED exit 1: 2 test files fail; 7 fail, 42 pass, tổng 49.
  - F1: 2 fail (detail notice, summary notice/metadata).
  - F2: 4 fail (CVE trùng detail, CVE trùng summary, match trùng, match ID giảm).
  - F3: 1 fail (detail cũ gọi Technology provider mới khi summary đang pending).
- GREEN cuối exit 0: 2/2 files, 51/51 tests pass.
- Một test stale-rejection mới ban đầu tạo unhandled rejection do reject trước khi effect gắn handler; fixture test được sửa để chờ old list bắt đầu. Không cần đổi production code cho lỗi test harness này.

## Kiểm chứng

| Lệnh | Exit | Kết quả |
|---|---:|---|
| focused W03 Vitest | 0 | 2 files, 51/51 |
| probe gốc từ `OUT\w03-frontend-qa-evidence`: `node_modules\.bin\vitest.cmd run --config .\vitest.qa.config.ts` | 0 | 1 file, 3/3 |
| `npm test` | 0 | 17 files, 356/356 |
| `npm run typecheck` (lần cuối, độc lập) | 0 | không lỗi |
| `npm run lint` | 0 | không warning/error |
| `npm run build` | 0 | 10 route static, gồm `/lo-hong` và `/lo-hong/mau` |
| `git diff --check` | 0 | không lỗi whitespace |
| kiểm allowlist/name-only | 0 | chỉ 5 file được phép |
| `git status --short` sau commit | 0 | rỗng |

Ghi chú minh bạch: một lần `npm run typecheck` chạy song song với `npm run build` exit 1 vì build đang tái tạo `.next/types/routes.js`. Sau khi build kết thúc, typecheck được chạy độc lập hai lần và đều exit 0; build cuối exit 0.

Probe gốc không bị sửa, SHA-256:
`4de999e36cfed42b36f0e8744222d0a049c53cad7e7abfa4f8c2d396c738de9f`.

## File trong commit

- `docs/PROGRESS.md` (+5/-0)
- `portal/web/components/cve-app.tsx` (+10/-2)
- `portal/web/data/cves-http.ts` (+16/-4)
- `portal/web/tests/cve-app.test.tsx` (+100/-5)
- `portal/web/tests/cves-http.test.ts` (+39/-0)

`portal/web/data/cves-http.ts` khớp rule ignore chung `.gitignore:20:data/`; file đã được stage rõ bằng `git add -f`. Không sửa `portal/web/data/cves.ts`.

## SHA-256

- `docs/PROGRESS.md`: `1ed427e4d22ae304f5dd5712ce84bbebfcd27d7c17f8a6b5f5ffbaf315eebed7`
- `portal/web/components/cve-app.tsx`: `1ba1b701f2432c04e5749c56ee1d45bf7fe6c6b03a16efcaadd6272d3149a12f`
- `portal/web/data/cves-http.ts`: `da12fcf5eb501ad2e31dce8ab4bcb2803121480de9a186d9a01a6b33a9ba8c46`
- `portal/web/tests/cve-app.test.tsx`: `455b34c54f0f8d0b24f9bb1c93961a61410c9f748f68e95d50054480318fbd9e`
- `portal/web/tests/cves-http.test.ts`: `bf7b8b84e06c8dbfa383d57a6d2390917eb34150b459a1ad1c136fa875d31762`
- fixture `w03-detail.json` (không đổi): `adcc16640ae425fd91955048ff17ddc60a3fb9476421d36531a2f596f40dd309`
- fixture `w03-summary.json` (không đổi): `fbccb17fca29d4dc00db16a4ce80156acc29a52ed437c36d48e246adaab96994`

## Giới hạn / chưa kiểm

Không chạy browser/live/lab và không nối API/backend/gateway/feed/OpenCTI/Cloudflare/JWKS/HTTPS/production. Không push, PR, merge hoặc deploy. Kết quả này chỉ chứng minh parser/provider/component và build portal cục bộ; không tuyên bố Backend/API/browser/feed đạt.
