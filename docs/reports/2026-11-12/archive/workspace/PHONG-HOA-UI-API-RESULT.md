# Kết quả WEB-W05 API client

Trạng thái: **PASS cục bộ**, **UNVERIFIED browser/FastAPI thật end-to-end**.

## Git và phạm vi

- Tree: `cti-portal-web`
- Branch: `feat/portal-w05-api-client-20261111`
- Base: `9b10223d90e529432d976177e14fdf2b6ce46bb7`
- Commits: `bec6b2c39388ca59d07660252734bdbd5677764c` (implementation), `733d82c03f0bbe5ca5aab02ab36dce07829458d0` (selection race), `8e205952a95434c59570152ff7c74c11623f8648` (refresh-after-write) và `a791a3f2be19b4c1593f82706c47b5dca97ab51a` (R1/R2, HEAD).
- Commit mới nhất: `fix(portal): preserve review state at queue edges`
- Diff từ base: 13 file, 1032 dòng thêm, 130 dòng bỏ; chỉ `portal/web/**` và `docs/PROGRESS.md`.
- Không push, PR, merge, deploy; không sửa backend, AI, RUNS hoặc tree khác.

## Phần đã triển khai

- `portal/web/data/api-client.ts:122,147,159,193`: parser runtime tách page summary, detail có `review`, decision response phẳng; kiểm shape exact, array, enum, null, boolean và `Number.isSafeInteger` cho ID/cursor/version/span/counter.
- Client gọi URL tương đối `/api/drafts*`, `credentials: same-origin`, `cache: no-store`; POST chỉ có `decision`, `expected_version` và `reason` khi reject. Không thêm subject/role/email/token, header danh tính, proxy hoặc endpoint phát triển.
- `portal/web/components/draft-review-app.tsx:15,116,126`: queue `limit=20`/cursor, số đếm dòng đã tải, detail riêng có AbortController + guard, trạng thái loading/empty/error/retry riêng và ánh xạ lỗi VI/EN an toàn.
- `portal/web/components/draft-review.tsx:46,125,176`: keep chỉ đọc trong API mode; approve/reject chỉ khi `review.pending`; reject trim và bắt buộc lý do; khóa lúc gửi, chống double click, không auto retry; 409 khóa version cũ và yêu cầu tải lại.
- Sau decision 200 hợp lệ: refresh queue + detail, hiển thị trạng thái review thật và thông báo quyết định cục bộ/chưa nhập OpenCTI.
- Rework race: trong lúc decision đang gửi, queue rows và tải thêm bị khóa. Kết quả POST/refresh chỉ được gắn vào
  detail khi ID đang chọn vẫn trùng draft đã quyết định; response có `draft_id` khác cũng bị từ chối. Guard theo
  `draft_id:review.version` tiếp tục chặn double-submit nhanh nhưng được xóa khi POST lỗi để retry thủ công.
- Rework refresh-after-write: POST decision hợp lệ được ghi nhận là success trước pha refresh. Nếu refresh lỗi,
  UI vẫn giữ success và guard version cũ, hiển thị cảnh báo an toàn cùng nút tải lại queue/detail; thao tác tải lại
  không POST decision lần nữa. Chỉ lỗi trước response POST hợp lệ mới xóa guard để người dùng retry thủ công.
- `/duyet` dùng API; `/duyet/mau` dùng ba fixture tổng hợp có nhãn, nút duyệt vô hiệu và không POST. Không fallback sample khi API lỗi.
- Giữ render text-only, Unicode span, IOC defang, clipboard và VI/EN; CSS chỉ bổ sung trạng thái/control cần cho tích hợp.

## Kiểm chứng vừa chạy

| Kiểm tra | Kết quả | Exit | Bằng chứng |
|---|---:|---:|---|
| RED: module API chưa tồn tại | 2 suite fail đúng nguyên nhân | 1 | `ui-api-evidence/01-red.log` |
| RED: payload `status=pending`, `review.status=approved` | 1 test fail đúng nhãn trạng thái cũ | 1 | `ui-api-evidence/08-review-status-red.log` |
| Focused API/UI/clipboard | 42/42 test đạt | 0 | `ui-api-evidence/07-focused-green-final.log` |
| Full `npm test` | 5 file, 47/47 test đạt | 0 | `ui-api-evidence/13-final-test.log` |
| `npm run typecheck` | đạt | 0 | `ui-api-evidence/14-final-typecheck.log` |
| `npm run lint` | đạt, 0 warning | 0 | `ui-api-evidence/15-final-lint.log` |
| `npm run build` | đạt; sinh `/`, `/duyet`, `/duyet/mau` | 0 | `ui-api-evidence/16-final-build.log` |
| Tổng exit cuối | test/typecheck/lint/build đều 0 | 0 | `ui-api-evidence/17-final-exits.log` |
| `git diff HEAD^ --check` + tree sạch | đạt | 0 | `ui-api-evidence/18-diff-check.log` |
| RED race decision A/chọn B | 1 test fail đúng vì hàng B chưa bị khóa | 1 | `ui-api-evidence/19-decision-selection-race-red.log` |
| GREEN race focused | 1/1 đạt | 0 | `ui-api-evidence/20-decision-selection-race-green.log` |
| Rework focused gồm race/double-click/manual retry | 44/44 đạt | 0 | `ui-api-evidence/21-rework-focused.log` |
| Rework full `npm test` | 5 file, 48/48 đạt | 0 | `ui-api-evidence/22-rework-full-test.log` |
| Rework typecheck/lint/build | đều đạt | 0 | `ui-api-evidence/23-rework-typecheck.log`, `24-rework-lint.log`, `25-rework-build.log`, `26-rework-exits.log` |
| Rework diff-check | đạt | 0 | `ui-api-evidence/28-rework-diff-check.log` |
| RED POST thành công/refresh lỗi | 1 test fail đúng vì mất success và mở lại quyết định | 1 | `ui-api-evidence/29-decision-refresh-failure-red.log` |
| GREEN refresh-after-write | 1/1 đạt | 0 | `ui-api-evidence/30-decision-refresh-failure-green.log` |
| Focused refresh rework | 45/45 đạt | 0 | `ui-api-evidence/31-refresh-rework-focused.log` |
| Full refresh rework `npm test` | 5 file, 49/49 đạt | 0 | `ui-api-evidence/32-refresh-rework-full-test.log` |
| Refresh rework typecheck/lint/build | đều đạt | 0 | `ui-api-evidence/33-refresh-rework-typecheck.log`, `34-refresh-rework-lint.log`, `35-refresh-rework-build.log`, `36-refresh-rework-exits.log` |
| Refresh rework diff-check | đạt | 0 | `ui-api-evidence/37-refresh-rework-diff-check.log` |
| RED Leader R1/R2 tái hiện nguyên trạng | 2/2 fail đúng hành vi | 1 | `ui-api-evidence/40-leader-review-red-reproduced.log` |
| RED regression repo R1 + approve/reject bản cuối | 3 fail, 21 pass | 1 | `ui-api-evidence/41-r1-r2-repo-red.log` |
| GREEN regression repo | 24/24 đạt | 0 | `ui-api-evidence/42-r1-r2-repo-green.log` |
| GREEN probe độc lập của Leader | 2/2 đạt | 0 | `ui-api-evidence/43-leader-review-green.log` |
| Full `npm test` sau R1/R2 | 5 file, 52/52 đạt | 0 | `ui-api-evidence/44-r1-r2-full-test.log` |
| Typecheck/lint sau R1/R2 | đều đạt | 0 | `ui-api-evidence/45-r1-r2-typecheck.log`, `46-r1-r2-lint.log` |
| Build sau R1/R2 | đạt; sinh `/`, `/duyet`, `/duyet/mau` | 0 | `ui-api-evidence/47-r1-r2-build.log` |
| Diff-check/tree sau commit | đạt; tree sạch | 0 | `ui-api-evidence/48-r1-r2-final-diff-check.log` |

## Rework R1/R2

- R1: `selectDraft` bỏ qua thao tác chọn lại đúng `selectedId`, nên không xóa detail, success hoặc khóa version đã ghi. Regression cũng xác nhận sau đó vẫn chuyển được sang draft ID khác.
- R2: khi refresh sau approve/reject làm queue thành `[]`, workspace vẫn giữ detail và thông báo quyết định đã ghi. Regression bao phủ cả approve và reject bản cuối, đồng thời giữ các ca refresh lỗi, double-submit và race selection cũ.
- Commit R1/R2 thay đổi 2 file, thêm 66 dòng, bỏ 2 dòng; không đổi API contract, auth, routing hay thiết kế.

Test bao phủ response phẳng thực tế, unsafe integer, phân trang, detail loading/stale response, race chọn draft khi decision đang gửi, approve/reject payload/version, blank reason, double click, lỗi rồi retry thủ công, 401/403/404/409/415/422/503, network/non-JSON/malformed 200, `payload.status=pending` với `review=approved`, sample không POST và API lỗi không fallback sample. 13 test preview/clipboard cũ vẫn nằm trong full suite và đạt.

## Giới hạn và handoff Engineer

- Trình duyệt tích hợp 1280x720 đã kiểm `/duyet`: trang trả 200, request tương đối `/api/drafts?limit=20` trả
  404 do chưa có routing và UI hiện lỗi an toàn, không fallback dữ liệu mẫu. Ảnh:
  `ui-api-evidence/39-browser-api-unavailable-1280.png`.
- Trình duyệt tích hợp đã kiểm `/duyet/mau`: có nhãn `Dữ liệu mẫu`, nút duyệt disabled, không có resource request
  `/api/drafts` và không có link IOC. Ảnh: `ui-api-evidence/38-browser-sample-1280.png`.
- Viewport thật 360/1440 vẫn **UNVERIFIED** vì bề mặt browser không có resize hợp lệ; không dùng CSS/zoom/browser
  khác để giả bằng chứng.
- Fetch trong test là boundary giả có response đúng contract; chưa chứng minh browser nối FastAPI/auth thật, signed JWT, Origin hoặc policy quyền end-to-end.
- Engineer cần định tuyến **cùng origin** `/api/drafts*` tới FastAPI đã nghiệm thu, giữ nguyên path/body/status/cache và Origin do browser phát sinh. Không thêm cấu hình release/deploy trong handoff này. Sau đó kiểm cục bộ với signed JWT tổng hợp ở `/duyet`; `/duyet/mau` phải tiếp tục không chạm API.
