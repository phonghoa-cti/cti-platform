# Kết quả W04-ASSETS-FRONTEND

Ngày kiểm: 11/11/2026. Branch: `feat/w04-assets-frontend-20261111`.
Base: `aeff542a20ecc6fe436a0884801fdd69ab0435f6`.

## Kết quả

**PASS trong phạm vi frontend/component cục bộ.** `/tai-san/mau` dùng provider dữ liệu tổng hợp có nhãn, quản lý
tên miền và dải IP qua hai tab, thêm/sửa/xóa với xác nhận tên đối tượng, expected version, khóa double-submit và
giữ riêng các trạng thái loading/empty/invalid/401/403/503/409/kết quả mutation chưa rõ. UI không nhúng JWT,
role hay identity; không tự retry POST/PUT/DELETE; refresh GET lỗi sau mutation được thông báo là “đã lưu, chưa
tải lại”, khác với lưu thất bại.

Adapter `/api/assets` chỉ gọi same-origin, kiểm schema exact, JSON/content-type/body tối đa 1 MiB, timeout 10 giây
xuyên suốt fetch và đọc stream, hủy body khi lỗi, và không thêm header danh tính. Provider mẫu chỉ giữ thay đổi
trong phiên thử; không giả backend hoặc auth đã chạy.

Parser/view W02 giữ `asset_match` cho `found`, `allowlisted` và `not_found`, cho tên asset tối đa 253 code point
nhưng vẫn giữ source/related ở 128. View hiển thị “Thuộc tài sản của bạn” và, với `not_found`, “Chưa tìm thấy dữ
liệu đe dọa”; không gọi IOC an toàn hoặc đã chặn.

## Fixture Backend candidate

Bốn file trong `portal/web/data/fixtures/w04-fixture-*.json` khớp nguyên byte SHA-256 với file root và
`leader-w04-backend-intake-20261111.json`:

| Fixture | SHA-256 | Kết quả |
|---|---|---|
| allowlisted + asset | `60af0330ebb0af42c7de7d4e0511848a800bdba2ca4631e1987f8da2f0909b08` | MATCH |
| not_found URL + asset | `f8a1765363d125906662d161c75776fe9f0c17c1c7e792bfa50edfc3aa2dc217` | MATCH |
| found URL + asset | `607a52fc15be775c2fd7fa8b5b62a218170568a5a2fe7f245aed533e52b06d13` | MATCH |
| assets_unavailable | `47fb12a67ad5afe55f04b74328cca5b90acb068c6ff268d99a93a2e4996fddd4` | MATCH |

Không phát hiện lệch hợp đồng ở bốn fixture. Đây chỉ là regression schema/view từ candidate Backend
`bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`, chưa phải nghiệm thu Backend hoặc bằng chứng runtime.

## TDD và kiểm tra

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `npm test -- tests/assets-http.test.ts tests/assets-app.test.tsx tests/ioc-lookup-http.test.ts tests/ioc-lookup.test.tsx` (RED đầu) | 1 | 95 test chạy; 4 fail đúng hành vi W02 mới, 2 suite thiếu module W04 |
| `npm test -- tests/assets-http.test.ts` (RED body timeout/bound) | 1 | 24 test; 2 fail do body treo/vượt 1 MiB chưa bị hủy |
| cùng nhóm test tập trung sau GREEN | 0 | 132/132 test đạt |
| `npm test` | 0 | 222/222 test, 11/11 file đạt sau rework R1 |
| `npm run typecheck` | 0 | PASS |
| `npm run lint` | 0 | PASS, 0 warning |
| `npm run build` | 0 | PASS bằng Next.js 16.4.6/Turbopack; sinh route `/tai-san/mau` |
| `npm run build -- --webpack` | 0 | PASS độc lập; sinh 7 route tĩnh |
| `git diff --check` | 0 | PASS; chỉ có cảnh báo chuyển LF/CRLF của Git |

Lần chạy `npm run build` đầu tiên exit 1 vì `node_modules` là junction ra ngoài workspace và Turbopack từ chối.
Không lặp nguyên trạng: dùng bản sao cục bộ của dependency W02 hiện hữu trong `node_modules` ignored, không cài mới
và không sửa package/lock; sau đó đúng lệnh `npm run build` exit 0. Raw lỗi ban đầu được giữ để báo cáo trung thực.

## File chính

- `portal/web/app/tai-san/mau/page.tsx`
- `portal/web/components/assets-app.tsx`
- `portal/web/data/assets.ts`, `portal/web/data/assets-http.ts`
- `portal/web/data/fixtures/w04-fixture-*.json`
- mở rộng giới hạn trong `portal/web/data/ioc-lookup*.ts` và `portal/web/components/ioc-lookup.tsx`
- `portal/web/tests/assets*.test.*`, bổ sung regression W02
- `portal/web/app/globals.css`, `portal/web/messages/{vi,en}.json`
- `portal/web/README.md`, `docs/PROGRESS.md`

Raw evidence: `w04-assets-frontend-evidence/`.

## Rework R1 — mutation cũ sau khi đổi tab

Review phát hiện mutation domain đang chờ có thể hoàn tất sau khi người dùng đã chuyển sang tab dải IP, rồi gọi
refresh domain và ghi đè bảng/context mới. Test RED tái hiện đúng lỗi: tab vẫn là Dải IP nhưng bảng bị đổi thành
`congty.vn` và hiện thông báo thành công của context cũ.

Sửa tối thiểu bằng `contextRef`: mutation ghi nhận token lúc bắt đầu; chuyển tab hoặc cleanup/unmount tăng token.
Kết quả success/error/finally của mutation cũ chỉ được đổi state khi token vẫn thuộc context hiện tại. Chuyển tab
cũng giải phóng trạng thái saving của context cũ; mutation cũ không phát GET refresh không còn cần thiết. Request
ownership sẵn có vẫn bảo vệ response list đã bắt đầu trước đó.

| Kiểm R1 | Exit | Kết quả |
|---|---:|---|
| `npm test -- tests/assets-app.test.tsx` RED | 1 | 1 fail/12 test; bảng IP bị domain cũ ghi đè |
| cùng lệnh GREEN | 0 | 12/12 test đạt |
| `npm test` | 0 | 222/222 test, 11/11 file đạt |
| `npm run typecheck` | 0 | PASS |
| `npm run lint` | 0 | PASS |
| `npm run build` | 0 | PASS; `/tai-san/mau` được prerender |
| `git diff --check` | 0 | PASS |

Evidence R1 dùng tiền tố `w04-assets-frontend-evidence/rework-r1-`.

## Rework F1–F3 — đồng bộ contract và ownership sau refresh

Base rework: `be131133da7b63a3054da032ed1ab8a85af48bc6`. F1 đổi riêng bound `created_by` từ 253 lên
512 code point; các bound value/note/asset name khác không đổi. Parser kiểm 253/254/512 hợp lệ, 513 bị từ chối;
adapter GET list và POST create đều nhận response có actor dài 512.

F2 chỉ coi đúng cặp status/code đã xác nhận là kết quả mutation đã biết. `upstream_unavailable`, envelope lạ hoặc
cặp status/code lạ của POST/PUT/DELETE trở thành `unknown-mutation`, gọi đúng một lần và hướng người dùng GET đối
soát; GET vẫn là `unavailable`. `503/assets_unavailable` và các lỗi auth/forbidden/conflict/not-found/invalid đã
biết vẫn giữ mapping cũ.

F3 kiểm lại context token ngay sau `await load(type, true)` và trước khi ghi notice cho create/update/delete.
Refresh domain cũ reject sau khi tab IP đã tải xong không còn ghi thông báo “đã lưu nhưng chưa tải lại” vào context
mới; recovery 503→200 trong chính context hiện tại vẫn đạt.

| Kiểm F1–F3 | Exit | Kết quả |
|---|---:|---|
| F1 RED / GREEN `assets-http.test.ts` | 1 / 0 | 4 fail → 31/31 pass |
| F2 RED / GREEN `assets-http.test.ts` | 1 / 0 | 6 fail → 38/38 pass |
| F3 RED / GREEN `assets-app.test.tsx` | 1 / 0 | 3 fail → 15/15 pass |
| focused assets HTTP + UI | 0 | 53/53 test, 2/2 file đạt; không chạy lại full 222 theo brief |
| `npm run typecheck` / `npm run lint` / `npm run build` | 0 / 0 / 0 | PASS; 7 route tĩnh gồm `/tai-san/mau` |
| `git diff --check` | 0 | PASS; chỉ cảnh báo LF/CRLF của Git |
| probe Leader nguyên lệnh brief | 0 | 6/6 test đạt |

Raw evidence mới: `w04-assets-frontend-evidence/rework-f{1,2,3}-{red,green}.txt`,
`rework-focused-assets.txt`, `rework-{typecheck,lint,build,diff-check}.txt`, và
`w04-assets-frontend-evidence/rework-leader/leader-probe-green.txt`.

## PASS / FAIL / UNVERIFIED

- **PASS:** UI mẫu, provider/HTTP adapter, CRUD interaction, optimistic version, lỗi/quyền, mutation không replay,
  stale request/context ownership trước và sau refresh, strict W02 asset fixtures, focused assets 53/53,
  probe Leader 6/6, typecheck/lint/build/diff check.
- **FAIL:** không còn failure sản phẩm trong phạm vi. Lỗi build junction ban đầu đã được xử lý bằng dependency copy
  cục bộ và giữ log; không sửa package/lock.
- **UNVERIFIED:** browser thật/viewport 360 px/clipboard; API `/api/assets` thật, gateway, JWT/role, database và
  toàn luồng W04 + W02 cùng một DB; Backend đã được Leader nghiệm thu riêng nhưng chưa tích hợp runtime ở tree này;
  Cloudflare/JWKS/HTTPS, lab,
  OpenCTI và production. Không có công cụ browser được mount cho worker nên không tự mở browser khác.

## Giải thích cho người mới

`AssetsDataSource` là ranh giới cho phép cùng một màn hình dùng dữ liệu mẫu hoặc API mà không đổi UI. `version`
giúp API phát hiện người khác đã sửa bản ghi trước mình, thay vì âm thầm ghi đè. Mutation mất kết nối không được gửi
lại tự động vì lần đầu có thể đã ghi thành công. Schema strict từ chối dữ liệu thừa/sai kiểu để frontend không vô
tình hiển thị một hợp đồng khác với Backend.
