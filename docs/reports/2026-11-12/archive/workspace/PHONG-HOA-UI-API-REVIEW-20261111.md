# UI-API-INTEGRATION — ACCEPTED cục bộ sau R1/R2

## Kết quả recheck lúc02:03 ngày11/11

Đóng R1/R2 tại `a791a3f2be19b4c1593f82706c47b5dca97ab51a`. Leader đọc diff2file (+66/-2): bỏ qua chọn lại cùng ID; giữ workspace/detail thành công khi hàng đợi rỗng. Chạy nguyên probe Leader **2/2 pass** và nhóm state **24/24 pass**, cả hai exit0. Log mới: `ui-api-evidence/leader-review-green.log`, `leader-rework-state-tests.log`. Tree sạch, diff-check exit0. Worker có full52/typecheck/lint/build; Leader không lặp những kiểm tra đó. Phạm vi chấp nhận là client contract và trạng thái UI; browser nối backend/auth thật vẫn UNVERIFIED. Các finding/RED dưới đây được giữ làm lịch sử.

Leader kiểm độc lập commit `8e205952a95434c59570152ff7c74c11623f8648`, tree `cti-portal-web`, nhánh `feat/portal-w05-api-client-20261111`. Tree sạch lúc kiểm. Brief gốc và API contract tại `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04` giữ nguyên; tái sử dụng nghiên cứu đã nghiệm thu.

## R1 — bấm lại bản đang chọn làm mất detail và tải mãi (medium)

`portal/web/components/draft-review-app.tsx:122–128`: `selectDraft()` xóa detail rồi đặt lại cùng selectedId. Vì ID không thay đổi, effect tải detail không chạy lại. Hàng đang chọn vẫn bấm được ở dòng224.

Tái hiện: tải list/detail thành công, bấm lại hàng đang chọn. Detail biến mất, `Đang tải chi tiết…` còn mãi. Leader có test thất bại độc lập trong `ui-api-evidence/leader-review.test.tsx`.

Sửa tối thiểu: chọn lại cùng ID phải giữ detail/trạng thái, hoặc có cơ chế reload hoàn chỉnh nếu cố ý reload. Không làm mất quyết định đã ghi/khóa chống gửi lại khi chỉ bấm lại hàng. Thêm regression vào test thuộc repo, kiểm chọn sang ID khác vẫn hoạt động.

## R2 — duyệt bản cuối hàng đợi làm mất xác nhận đã ghi (medium)

`portal/web/components/draft-review-app.tsx:220–233`: toàn workspace, gồm `DraftReview` và `decisionSuccess`, chỉ render khi queue không rỗng. Sau POST thành công, refresh trả queue rỗng thì thông báo thành công cũng biến mất.

Tái hiện: queue có một bản pending, approve thành công, refresh list trả `items:[]`, detail trả approved. Người dùng chỉ thấy hàng đợi rỗng, không còn xác nhận quyết định đã được ghi. Test Leader thứ hai thất bại vì không còn success status.

Sửa: xác nhận quyết định đã ghi phải còn nhìn thấy khi queue trở thành rỗng; giữ nguyên chống gửi lại version cũ và không tự retry POST. Thêm ca approve và reject bản cuối, giữ regression refresh lỗi và chuyển bản đang có. Không thiết kế lại UI hoặc đổi contract.

## Bằng chứng và yêu cầu bàn giao

- Leader chạy nhóm API client + state component hiện có: **40/40 pass**, exit0.
- Hai test mới của Leader: **2/2 fail**, exit1, đã tái hiện hai lỗi trên; xem `ui-api-evidence/leader-review-red.log`. Đây là lỗi hành vi sau khi harness đã chạy được, không phải lỗi cấu hình.
- Có thể chạy lại probe từ `cti-portal-web/portal/web`: `node node_modules/vitest/vitest.mjs run --config ../../../ui-api-evidence/leader-review.config.mjs --reporter=verbose`. Không sửa probe/config/log RED của Leader; lưu GREEN riêng.
- Phạm vi sửa: component/test liên quan trong portal/web, docs/PROGRESS nếu cần, báo cáo `PHONG-HOA-UI-API-RESULT.md`, evidence mới. Không sửa ledger/review/Backend/AI hoặc file Leader.
- TDD RED/GREEN cho R1/R2; targeted suite, typecheck, lint, build, diff-check. Commit cục bộ rồi báo SHA, diff, exit/count, clean tree. Không push/PR/merge/deploy, không agent phụ.
- Browser nối FastAPI/JWT/Origin thật và viewport360/1440 vẫn UNVERIFIED. API404 trong demo trước phù hợp phạm vi client; không coi là đã tích hợp thật.
