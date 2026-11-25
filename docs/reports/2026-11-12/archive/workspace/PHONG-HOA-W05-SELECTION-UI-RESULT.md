# Kết quả W05 Selection UI

Ngày: 11/11/2026 (Asia/Saigon)

## Trạng thái

**PASS cục bộ trong phạm vi UI, gồm rework R1–R6.** `/duyet` đã dùng API v1, tách lựa chọn server đã lưu với lựa chọn analyst đang sửa, có nút lưu riêng và không tự nối save → decision. `/duyet/mau` vẫn là dữ liệu tổng hợp có nhãn và không gọi API.

- Tree: `$WORKSPACE\cti-w05-selection-ui`
- Branch: `feat/w05-selection-ui-20261111`
- Base: `812dae1ffbdc8e8866342cc075d925fdc99ef12d`
- Head/commit: `43737c000561c4d676705dbb564223a7bfa3596e`
- Commit rework mới nhất: `fix(portal): release stale pagination requests`
- Commit exit: `0`
- Diff base → head: 12 file, `+1014/-480`
- Diff R6: 2 file, `+59/-9`
- Status sau commit: sạch (`git status --porcelain=v1` không có dòng nào)
- Không push, PR, merge hoặc deploy.

## RED → GREEN

- Baseline trước sửa: 5 file test, 52 test đạt, exit `0`.
- RED API v1: 1 file, 13 test fail đúng vì parser/method v1 chưa có, exit `1`.
- GREEN API v1 targeted: 1 file, 13/13 đạt, exit `0`.
- RED state UI: 1 file, 6 test fail đúng vì checkbox API còn read-only và chưa có saved/editing state, exit `1`.
- GREEN state UI targeted: 1 file, 6/6 đạt, exit `0`.
- Regression biên read 1.025 → save 1.024: targeted 7/7 đạt, exit `0`.
- RED rework repo R1–R5: 3 file, 14 fail / 39 pass, exit `1`.
- RED probe Leader nguyên trạng: 15/15 fail do assertion hành vi, 0 lỗi setup/import, exit `1`.
- GREEN rework targeted: 3 file, 53/53 đạt, exit `0`.
- GREEN probe Leader nguyên trạng: 15/15 đạt, exit `0`; SHA256 probe `10E2C8589B5935428F3E4D4DEC1AB018AD3C969BD6308E3D62EB97619150F93A`.
- RED repo R6: 3 ca mới fail đúng lifecycle phân trang, 12 ca cũ đạt, exit `1`.
- GREEN repo R6: selection UI 15/15 đạt, exit `0`.
- GREEN probe R6 Leader nguyên trạng: 2/2 đạt, exit `0`; SHA256 `9AE5EC4FFF3C6E7E1525ED3A0837C008745C41FC582CC58FFE8B462A205915F9`.
- Recheck probe R1–R5 nguyên trạng sau R6: 15/15 đạt, exit `0`.

Không dùng `sleep`; race/double-submit dùng deferred promise.

## Kiểm tra cuối fresh

| Kiểm tra | Kết quả | Exit |
|---|---:|---:|
| Full Vitest | 7 file, 86/86 test đạt | 0 |
| `npm run typecheck` | đạt | 0 |
| `npm run lint` | đạt, 0 error/warning | 0 |
| `npm run build` | đạt; static routes `/`, `/duyet`, `/duyet/mau` | 0 |
| `git diff --check` | đạt | 0 |
| `git commit` | đạt | 0 |

## Ma trận acceptance rework

| Finding | Kết quả | Bằng chứng |
|---|---|---|
| R1 retry queue khi dirty/POST và race cũ | PASS | Repo regression + probe Leader; nút/handler khóa, response cũ bị chặn theo generation/ID |
| R2 rollback sau save/decision thành công | PASS | Floor review/selection version, status và snapshot; stale GET giữ success và tiếp tục khóa mutation |
| R3 POST 404, draft biến mất | PASS | Phục hồi explicit chỉ GET queue, không phụ thuộc detail draft đã mất, không replay POST |
| R4 detail sai ID | PASS | Client thật và component injected đều từ chối payload không khớp requested/selected ID |
| R5 strict legacy parser | PASS | Bác date rỗng, enum/count sai, ID trùng, actor/time rỗng |
| R6 đổi draft khi đang tải thêm | PASS | Request phân trang có owner riêng; đổi draft kết thúc lifecycle cũ, B giữ nguyên và tải tiếp được; callback cũ không mở khóa request mới |

## Phạm vi đã làm

- Client v1 exact cho list/detail/save/decision; số public safe integer, không coercion/bool; kiểm ID/version/status/snapshot/hash shape; legacy parser giữ riêng.
- Giới hạn 1.024 chỉ áp input save. Detail có selection >1.024 vẫn đọc nguyên; analyst được bỏ chọn xuống ngưỡng.
- `items.keep` không bị sửa. Chỉ IOC `kind=ioc`, `keep=true`, `status=ok` được chỉnh.
- Dirty cho phép sửa/lưu/hủy nhưng khóa đổi draft, load-more, reload và decision.
- POST network/abort/5xx/malformed/mismatch là kết quả chưa rõ, khóa gửi lại cho tới thao tác tải lại rõ ràng; không tự retry POST.
- 4xx chỉ được coi là known khi status và error envelope/code đúng hợp đồng ở client thật.
- Save/decision success được giữ khi refresh hỏng hoặc stale; nút phục hồi chỉ GET, không replay POST.
- Empty selection lưu được; approve bị khóa; reject vẫn dùng được với lý do đã trim.
- Giữ VI/EN, text-only, defang, clipboard, Unicode evidence/focus, keyboard label, sample/no-fallback.

## Giải thích cho người mới

`savedSelection` là tập IOC server đã ghi. `editingSelection` là tập analyst đang tích hoặc bỏ tích trên màn hình. Hai tập chỉ giống nhau sau khi tải dữ liệu, hủy thay đổi hoặc lưu thành công. Nút **Lưu lựa chọn** là ranh giới có chủ ý để nút duyệt không dùng nhầm một snapshot chưa được server ghi.

## UNVERIFIED / handoff

- **UNVERIFIED:** browser integration thật và hành vi focus/layout trên trình duyệt.
- **UNVERIFIED:** gateway same-origin `/api/v1/drafts`.
- **UNVERIFIED:** Cloudflare Access/JWKS thật, lab, OpenCTI và production.
- Fake-fetch/Vitest ở đây chỉ là kiểm component/client cục bộ, không được coi là browser hoặc gateway integration.
- Bước kế theo Leader plan: CTI Engineer mở allowlist gateway v1 có giới hạn và chạy browser integration same-origin riêng.

Evidence mới nhất: `w05-selection-ui-evidence\rework-r6\verification.md`, raw logs, JSON/JUnit, exit files và `manifest.sha256` cùng thư mục. Bằng chứng cũ được giữ nguyên.
