# W03-S1 Frontend — kết quả rework2 F5/F6

## Kết quả

PASS cục bộ. Candidate `13b8025274a70ec88dc21dd9ca7f51c68961e881` được sửa thành commit sạch `2448b8600f9eff2c3e42b6742e220b46980f4ff4`; base/merge-base giữ `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.

- F5: frontend bind relation bằng `technology_id` + CVE ID; Backend giữ thẩm quyền identity casefold. Snapshot display cũ được nhận khi technology version hoặc dataset đổi; display drift với cùng version/dataset vẫn bị từ chối.
- F6: registry thông báo subscriber hiện hành khi pending cũ kết thúc conflict/known failure. Close/reopen và A→B→A thoát khóa đúng, conflict GET context mới, không replay PUT; provider khác không bị callback cũ sửa.

## Kiểm chứng

| Lệnh | Exit | Kết quả |
|---|---:|---|
| Leader recheck probe nguyên bản | 0 | 1 file, 3/3 pass |
| Leader probe cũ nguyên bản | 0 | 1 file, 7/7 pass |
| source RED | 1 | đúng 3 lỗi mục tiêu, 34 pass |
| source GREEN | 0 | 2 file, 37/37 pass |
| focused affected regression | 0 | 4 file, 97/97 pass |
| `npm run typecheck` riêng sau build | 0 | không lỗi |
| `npm run lint` | 0 | không lỗi/cảnh báo |
| `npm run build` | 0 | build thành công, 11/11 trang tĩnh |
| `git diff --check candidate..final` | 0 | không output |
| `git status --porcelain=v1` | 0 | không output, tree sạch |

Rework2 diff đúng 4 file allowlist, `+69/-13`; full frontend diff từ base 15 file, `+953/-6`. Hash 3 probe mới, 7 probe cũ, config/setup/wire không đổi; chi tiết tại `w03-status-frontend-rework2-evidence/manifest.md`.

## Giới hạn

Chỉ chứng minh parser/provider/component/build cục bộ bằng fixture tổng hợp và wire API in-process do Leader cung cấp. Chưa kiểm browser thật, chưa tích hợp gateway/Backend/UI chung, chưa kiểm lab/feed thật/production. Không push/PR/merge/deploy.
