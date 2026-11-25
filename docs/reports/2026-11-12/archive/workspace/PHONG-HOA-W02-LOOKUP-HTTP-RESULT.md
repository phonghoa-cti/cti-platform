# Kết quả W02-LOOKUP-HTTP-ADAPTER

Ngày kiểm: 11/11/2026. Kết luận: **PASS cục bộ trong phạm vi parser/adapter và component test với HTTP giả**.

## Ref và phạm vi

- Tree: `cti-w02-lookup-http`
- Branch: `feat/w02-lookup-http-20261111`
- Base bắt buộc: `a949081bf302801e11d69a8ee70c1232d68955cc`
- Commit/HEAD sau R1: `88e9a9b6e491c0d450640e848043f41c80feb4bd`
- Commit: `4b7b247840e2ba8523fe368918ad1d4aafaf3dcd` (`feat(portal): add strict W02 IOC HTTP adapter`)
  và `88e9a9b6e491c0d450640e848043f41c80feb4bd` (`fix(portal): require HTTP 200 for IOC lookup`).
- Diff base..HEAD: 8 file, `+684/-8`; không có file ngoài allowlist; `git status --short` có 0 dòng.
- Dispatch đã đối chiếu SHA256: `57ae0d0d77ba31504f1ed7a4b01ffb06170edcc85d272c09732525b263e3a690`.
- Contract đã đối chiếu SHA256: `93dab3d51d5e62e63711f6dc7fbd6b05a5c039c38f62e6e667b3ac2b34da84df`.

## Đã triển khai

- Export `parseIocLookupResponse` kiểm exact keys/schema, Unicode code-point bounds, integer/finite bounds,
  8 loại IOC, 5 TLP, timestamp UTC, `first_seen <= last_seen` và invariant found/allowlisted/not_found.
- Giữ đầy đủ `score.parts`, `sources.last_seen`, source TLP và `asset_match`; view chỉ map dữ liệu đang dùng,
  lấy `input` từ caller và để `enrichment={}`.
- `createIocHttpDataSource({ fetcher? })` gửi một GET same-origin tới `/api/ioc` với đúng một query `value`,
  `credentials=same-origin`, `cache=no-store`, `redirect=error`, chỉ có header `Accept: application/json`.
- AbortController 10 giây bao trùm fetch và đọc body; body UTF-8 tối đa 1 MiB, reader/body được hủy ở nhánh
  timeout/quá cỡ/từ chối sớm; không retry, không fallback fixture, không header danh tính hay lưu/log query.
- Map lỗi allowlist của contract vào state UI; lỗi/status mismatch, HTML, JSON sai và schema sai đều thành
  `unavailable`, không đưa message thô của server lên view.
- Chỉ HTTP status `200` được parse thành success; `201`, `202` và mọi status khác đi qua error parser exact,
  rồi chỉ status/code nằm trong allowlist mới được map, mismatch thành `unavailable`.
- Bổ sung state đăng nhập và nhãn VI/EN cho IPv6/MD5/SHA-1/SHA-256, giữ `hash` chỉ cho fixture cũ.

## TDD RED → GREEN

| Bước | Lệnh | Kết quả |
|---|---|---|
| RED ban đầu | `npm test -- tests/ioc-lookup-http.test.ts` | exit 1; 1 suite fail đúng vì module adapter chưa tồn tại |
| RED cleanup | test riêng `cancels an unread body rejected by its declared size` | exit 1; 1 fail/53 skip, bắt được body chưa hủy |
| GREEN W02 | `npm test -- tests/ioc-lookup-http.test.ts tests/ioc-lookup.test.tsx` | exit 0; 2 file, 87/87 test |
| R1 RED status | test riêng `non-contract success status 201` | exit 1; 1 fail/54 skip; thực tế trả `result` |
| R1 GREEN status | `npm test -- tests/ioc-lookup-http.test.ts` | exit 0; 1 file, 55/55 test |

## Kiểm chứng tươi

| Kiểm tra | Exit | Số lượng/kết quả |
|---|---:|---|
| `npm test` | 0 | 9 file, 177/177 test |
| `npm run typecheck` | 0 | 0 diagnostic |
| `npm run lint` | 0 | 0 finding/warning |
| `npm run build` | 0 | Next.js production build, 5 route hiển thị trong bảng đều static |
| `git diff --cached --check` trước commit | 0 | không lỗi whitespace |
| allowlist diff | 0 | 8 file đổi, 0 file ngoài allowlist |
| base/HEAD/status | 0 | base là ancestor; HEAD đúng; status 0 dòng |

Lượt build đầu exit 1 vì Turbopack không cho `node_modules` junction trỏ ra ngoài workspace. Junction trong target
được thay bằng bản sao dependency cache cục bộ (git ignore, không đổi package/lock, không tải dependency); build
tươi sau đó exit 0. Log thất bại và log thành công đều được giữ để không che lịch sử kiểm chứng.

## File diff

- `portal/web/data/ioc-lookup-http.ts` (mới)
- `portal/web/tests/ioc-lookup-http.test.ts` (mới)
- `portal/web/data/ioc-lookup.ts`
- `portal/web/tests/ioc-lookup.test.tsx`
- `portal/web/messages/vi.json`
- `portal/web/messages/en.json`
- `portal/web/README.md`
- `docs/PROGRESS.md`

## Evidence và manifest

- Thư mục: `w02-lookup-http-evidence/`
- Manifest: `w02-lookup-http-evidence/MANIFEST.sha256`
- SHA256 manifest: `1507c007de23be12c2cba3a01f1dad9459cf67e57e0f33f258367e73530a4aeb`
- Log chính: `01-red-ioc-lookup-http.log`, `02-red-declared-size-cleanup.log`,
  `03-green-w02-target.log`, `10-full-web-test.log`, `11-typecheck.log`, `12-lint.log`,
  `13-build.log`, `14-build-local-cache.log`, `15-diff-check.log`, `16-allowlist-diff.log`,
  `18-git-state-final.log`, `20-r1-red-status-201.log`, `21-r1-green-target.log`,
  `30-r1-full-web-test.log`, `31-r1-typecheck.log`, `32-r1-lint.log`, `33-r1-build.log`,
  `34-r1-diff-check.log`, `35-r1-allowlist-diff.log`, `37-r1-git-state-final.log`.

## Chưa kiểm chứng

- Chưa gắn adapter vào route vận hành và không đổi `/tra-cuu/mau` khỏi fixture.
- Chưa kết nối Backend thật, browser/listener, JWT/Cloudflare, OpenCTI, enrichment, lab hay production.
- Không push, PR, merge hoặc deploy.
