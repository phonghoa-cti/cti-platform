# W02-LOOKUP-VIEW — kết quả triển khai

## Nghiên cứu và lựa chọn tái sử dụng

Tái dùng trực tiếp W00/W02, `api-portal.md`, `DESIGN.md` và pattern component/state của W05; giữ nguyên SOC
console và không làm lại thương hiệu. Chọn `LookupDataSource` + view model nội bộ và fixture injection để hoàn
thiện view song song với quá trình chốt API. Giới hạn: chưa kiểm HTTP/API thật, auth, OpenCTI hoặc dữ liệu thật.

## Kết quả

- Trạng thái: **PASS cục bộ cho view/fixture W02**, không phải W02/API/live hoàn tất.
- Worktree: `cti-w02-lookup-ui`
- Branch: `feat/w02-lookup-view-20261111`
- Base: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`
- Commit mới nhất: `a949081bf302801e11d69a8ee70c1232d68955cc` (`fix(portal): guard IOC lookup async state`)
- Commit tính năng trước rework: `d5a3aa4eda20491937da3ab4b4e29198f9563c7c`
- Diff: 9 files, 514 insertions; 4 file mới, 5 file sửa.

`/tra-cuu/mau` tra đúng một IOC mỗi lần, có nhãn dữ liệu tổng hợp, VI/EN, keyboard/focus/live region và bố cục
responsive 360 px trong CSS. Nguồn fixture không gọi mạng; mọi giá trị không khớp trả `not-found`, không trả an
toàn. Component nhận nguồn dữ liệu thay được và không tự chuẩn hóa/chấm điểm/suy allowlist.

Đã triển khai idle/loading/result/not-found/invalid/private-IP/unavailable/forbidden; kết quả có raw copy value,
display defang, found/allowlisted, score/level/reason, sources/related/enrichment/TLP. Response cũ không ghi đè
truy vấn mới; lỗi xóa kết quả cũ; clipboard chỉ báo thành công sau Promise resolve và báo lỗi khi thiếu/từ chối.

## Rework review R1/R2

- R1 closed: fixture lookup dùng own-key exact-match; `__proto__`, `constructor`, `toString`, `hasOwnProperty` và
  `valueOf` đều trả `not-found`, không tự normalize hoặc chấm điểm.
- R2 closed: mỗi submit và mỗi copy có generation riêng; callback copy cũ bị vô hiệu khi submit mới, unmount hoặc
  một lượt copy mới hơn, nên không thể gắn success/error của IOC A lên kết quả IOC B.
- Rework commit: `a949081bf302801e11d69a8ee70c1232d68955cc`; 4 file, `+87/-6`, đúng allowlist review.
- TDD targeted: RED hợp lệ 7 fail/23 test, exit 1; GREEN 23/23, exit 0.
- Probe Leader nguyên trạng: 7/7, exit 0. Probe SHA-256 trước/sau đều
  `ca72dacd31f465b5b03bbd3cdd5711902bc42dcbb3551f592d7a0012998052af`; config trước/sau đều
  `e371eb1f7f0ae636f9b1430a5071b286a369b34fe4c262694a5cdb2b17821fc7`.
- Toàn web: 112/112, exit 0; typecheck/lint/build exit 0; `/tra-cuu/mau` vẫn prerender static; diff-check exit 0.
- Raw evidence: `w02-lookup-ui-evidence/rework-r1-r2/`. Browser không chạy lại vì race Promise đã có regression
  deterministic; bằng chứng desktop trước rework vẫn được giữ, mobile vẫn UNVERIFIED.

## File mới chính xác

- `portal/web/app/tra-cuu/mau/page.tsx`
- `portal/web/components/ioc-lookup.tsx`
- `portal/web/data/ioc-lookup.ts`
- `portal/web/tests/ioc-lookup.test.tsx`

File sửa: `docs/PROGRESS.md`, `portal/web/README.md`, `portal/web/app/globals.css`,
`portal/web/messages/vi.json`, `portal/web/messages/en.json`.

## TDD và kiểm tra

| Kiểm tra | Exit | Kết quả | Evidence |
|---|---:|---|---|
| RED `npm test -- tests/ioc-lookup.test.tsx` | 1 | import component chưa tồn tại, đúng lý do feature thiếu | `w02-lookup-ui-evidence/tdd-red.txt` |
| GREEN targeted | 0 | 1 file, 14 test đạt | `w02-lookup-ui-evidence/tdd-green.txt` |
| `npm test` | 0 | 8 file, 103 test đạt | `w02-lookup-ui-evidence/npm-test.txt` |
| `npm run typecheck` | 0 | không lỗi TypeScript | `w02-lookup-ui-evidence/typecheck.txt` |
| `npm run lint` | 0 | không warning/error | `w02-lookup-ui-evidence/lint.txt` |
| `npm run build` | 0 | build thành công; `/tra-cuu/mau` static | `w02-lookup-ui-evidence/build.txt` |
| `git diff --check` + allowlist | 0 | đạt | `w02-lookup-ui-evidence/diff-check.txt`, `allowlist-actual.txt` |

Các file bảo vệ không đổi, SHA-256 trước/sau khớp:

- `portal/web/package.json`: `EE51EA...9981`
- `portal/web/package-lock.json`: `63B538...524A`
- `portal/web/app/page.tsx`: `A99789...BE91`
- `portal/web/components/draft-review-app.tsx`: `D07D16...C552`

Chi tiết đầy đủ: `w02-lookup-ui-evidence/protected-hashes-before.txt` và
`w02-lookup-ui-evidence/protected-hashes-after.txt`.

## Browser và trạng thái tree

- Browser desktop: **PASS** tại `http://127.0.0.1:3012/tra-cuu/mau` bằng trình duyệt tích hợp và listener
  loopback đã cleanup. Đã kiểm fixture có điểm/nguồn, defang, lỗi clipboard, not-found không bị gọi là an toàn,
  đổi VI/EN, Enter gửi form và allowlist. Evidence: `w02-lookup-ui-evidence/browser-desktop.txt`,
  `browser-desktop-result.png`, `browser-desktop-not-found-en.png`.
- Mobile viewport thật: **UNVERIFIED** — công cụ trình duyệt tích hợp không có resize/device emulation; không
  thay bằng zoom/CSS hoặc automation khác.
- Target sau commit: sạch (`git status --short` không có output).
- Source trước/sau: HEAD vẫn `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`, status sạch; evidence
  `source-head-before.txt`, `source-head-after.txt`, `source-status-before.txt`, `source-status-after.txt`.

## Giới hạn

Không có adapter HTTP, API contract cuối, auth/quyền/TLP runtime, OpenCTI, enrichment thật, batch, lịch sử,
analytics, link ngoài, đề xuất chặn, login, lab, deploy hay dữ liệu vận hành. Không push/PR/merge/deploy.
Metadata tiêu đề tab vẫn là tiêu đề W05 dùng chung từ layout hiện có; `layout.tsx` nằm ngoài allowlist của lát cắt
này nên không sửa. Nội dung trang và heading W02 vẫn đúng; metadata route cần xử lý ở bước tích hợp được phép.

## Học thêm

- View model là cấu trúc dữ liệu dành riêng cho màn hình, giúp thay nguồn fixture bằng HTTP mà không đổi UI.
- Request generation là số thứ tự truy vấn, dùng để bỏ response cũ đến muộn và tránh hiển thị sai IOC.
- Defang làm IOC không bấm nhầm được; clipboard vẫn sao chép đúng giá trị gốc từ kết quả.
