# W03-S1 Frontend — kết quả rework F1–F4

## Kết quả

PASS cục bộ. Candidate `e31f0b40ac7ed8a8acb31968485c281fc2b3b7b0` được sửa thành commit sạch `13b8025274a70ec88dc21dd9ca7f51c68961e881` trên branch `feat/w03-status-frontend-20261112`; base/merge-base giữ `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.

- F1: pending/unknown khóa mutation theo provider+relation qua đóng/mở; GET lỗi giữ khóa, GET thành công mới bỏ unknown; không replay PUT.
- F2: completion save/read/history chỉ cập nhật owner provider+relation hiện tại; callback cũ không ghi đè selection/provider mới.
- F3: history 409 bỏ toàn bộ page/items/cursor cũ và chỉ tải lại từ cursor null theo thao tác người dùng.
- F4: parser/provider bind đúng relation yêu cầu, kiểm review/audit/version/page cross-field, W04 bounds vendor 128/product 256/software_version 128; note cho phép Cf, actor không bị trim quá contract.

## Kiểm chứng

| Lệnh | Exit | Kết quả |
|---|---:|---|
| Leader probe nguyên bản | 0 | 1 file, 7/7 pass |
| focused status + W03 app/http/technology | 0 | 6 file, 151/151 pass |
| `npm run typecheck` | 0 | không lỗi |
| `npm run lint` | 0 | không lỗi/cảnh báo |
| `npm run build` | 0 | build thành công, 11/11 trang tĩnh |
| `git diff --check candidate..final` | 0 | không output |
| `git status --porcelain=v1` | 0 | không output, tree sạch |

Probe hash không đổi: `a5169c29a4b2ecef2da289482008f29a511119c2133908e38380ebbac8d60368`. Rework diff đúng 4 file allowlist, `+168/-54`; full frontend diff từ base 15 file, `+897/-6`.

Evidence: `w03-status-frontend-rework-evidence/leader-probes-green.log`, `checks.log`, `manifest.md`.

## Giới hạn

Chỉ chứng minh unit/component/parser/provider/build cục bộ bằng fixture tổng hợp. Chưa kiểm browser thật, chưa nối Backend/API chung, chưa kiểm lab/feed thật/production. Không push/PR/merge/deploy.
