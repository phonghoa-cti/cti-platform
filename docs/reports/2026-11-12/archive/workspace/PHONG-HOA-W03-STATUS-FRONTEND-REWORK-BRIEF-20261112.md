# W03-S1 Frontend — sửa F1–F4

ROOT = `$WORKSPACE`.

Tiếp tục cùng tree `ROOT/cti-w03-status-frontend`, thread `a7b74dcb-d309-4b2b-a34e-19b13d145482`, candidate `e31f0b40ac7ed8a8acb31968485c281fc2b3b7b0`. Một Sol medium trực tiếp, không worker/bot con. Giữ edits nếu có, không reset/tạo writer mới. Đọc REVIEW.md/probe trong `ROOT/leader-w03-status-review-20261112` và brief S1 gốc. Allowlist và contract giữ nguyên; không redesign.

## Sửa cụ thể

1. **F1:** pending/unknown phải chặn mutation theo provider+relation qua close/reopen/đổi lựa chọn, kể cả GET đối soát thất bại và response cũ còn tồn tại. Chỉ GET thành công đủ điều kiện mở thao tác mới; bỏ registry unknown đúng lúc, không biến GET thành chứng cứ PUT cũ thành công. Known committed notice sống qua GET503; không auto replay PUT. Handler submit cũng phải kiểm lock, không chỉ disabled button.
2. **F2:** mọi mutation success/error/finally và GET refresh của A chỉ có quyền cập nhật A nếu selection/provider/generation vẫn thuộc nó. Đổi sang B, hoặc đổi provider nhưng cùng IDs, callback A không được sửa response/note/loading/notice của B. Giữ trạng thái pending/unknown của A để quay lại đối soát; không chạy effect gây double PUT hoặc dùng closure A làm GET cho B. Áp dụng cả conflict và rejected refresh.
3. **F3:** history409 phải bỏ items/pages/cursor thuộc snapshot cũ; không để nút trang tiếp giữ cursor cũ. Cho tải lại từ đầu bằng GET và giữ trạng thái/notice ghi hiện tại. Mọi history completion phải tuân context ownership như trên.
4. **F4:** HTTP read/save/history bind response với cve_id/technology_id đã yêu cầu; response PUT không đúng contract coi unknown. Parser không cho saved record hoặc audit của relation khác lọt qua review_required. Kiểm cross-fields review_required theo version/dataset; event/version before/after; page limit1..100 và items.length<=limit, ID giảm/không trùng. Bound đúng W04: vendor128, product256, software_version128 Unicode codepoints (đã kiểm source); không hardcode200. Giữ actor1..512 và note1..1000/Cc/Cs theo brief, tránh tự siết thành trim actor/Cf nếu contract chưa yêu cầu. Không đổi CVE DTO/parser cũ.

Không đòi backend thêm field hay thay wire. Backend đang sửa trên tree khác, không chỉnh/đọc thay đổi chưa bàn giao để ghép tạm. Mẫu vẫn memory và summary không gọi status API.

## Kiểm và bàn giao

- Giữ nguyên 7 probe Leader `ROOT/leader-w03-status-review-20261112/frontend-probes.test.tsx` cùng setup/config/tsconfig (manifest), làm GREEN cả7. Leader đã chạy7FAIL assertion sau sửa harness; không tính lỗi setup trước đó là lỗi product. Chạy command trong REVIEW.md từ thư mục review, ghi log GREEN vào evidence riêng; không ghi đè log RED.
- Thêm regression source cho unknownPUT+GET503→200 qua reopen, committed+GET503→200, A/B + provider switch cho success/conflict/failure, history409 reload đầu, parser wrong relation/bounds; valid controls product201..256, boundary vendor/softwareversion, snapshot cũ review_required hợp lệ. Không sửa probe/relax assertion để đạt.
- Focused status + W03 app/http và phần liên quan; typecheck/lint/build/diff-check. Không lặp full suite theo thói quen. Không sửa dependency/config shared, Backend hoặc gateway.
- Commit sạch, báo candidate/finalSHA/diff allowlist, command/exit/count, hash probe không đổi. Cập nhật `ROOT/PHONG-HOA-W03-STATUS-FRONTEND-RESULT.md`; thêm `ROOT/PHONG-HOA-W03-STATUS-FRONTEND-REWORK-RESULT.md`, evidence mới `ROOT/w03-status-frontend-rework-evidence/` gồm raw GREEN/manifest. Giữ evidence cũ.
- Không sửa RUNS/brief/Leader evidence. Không push/PR/merge/deploy/browser/lab/live feed. Chỉ khi hai input được Leader nghiệm thu mới ghép và kiểm browser.
