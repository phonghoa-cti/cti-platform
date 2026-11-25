# W05-SELECTION-API-NEXT — nghiên cứu hợp đồng API cho lựa chọn IOC

Owner: CTI Research. Chỉ nghiên cứu có nguồn và lập brief triển khai Backend; chưa sửa code hoặc giao bot khác. Mục tiêu: đưa lựa chọn đã lưu và version đúng lên HTTP, để UI sau đó cho phép chọn/bỏ chọn và duyệt đúng dữ liệu. Không mở rộng thành thiết kế lại portal.

Workspace: `$WORKSPACE`.

## Hiện trạng đã kiểm và phần tái sử dụng

- Tree nguồn chính `<workspace>\cti-w05-selection`, branch `feat/w05-selection-local-20261111`, HEAD **b9c35bb45cbf1000c1324ba46f1f162e0c02be44**. Leader nghiệm thu core tại ref này, 40/40 ca mới; đọc `PHONG-HOA-W05-EDIT-REVIEW-20261111.md` phần đầu. Kiểm HEAD/status trước đọc; nếu ref đổi dùng git show ref đã chốt, không reset.
- Core `extractor/phonghoa_extractor/store.py`: schema v2, get_effective_selection/save_selection, version review/selection, audit từng lần lưu và final snapshot. Payload/items.keep/evidence/source bất biến. Chỉ chọn lại IOC vốn eligible; không thêm IOC, không hồi sinh allowlist/bia. Creator được sửa/reject, không tự approve; giữ policy Analyst/Admin.
- API cùng tree: `portal_api/schemas.py`, `service.py`, `app.py`, `auth.py`, `settings.py`, `tests/test_w05_api.py`. Hiện summary review_version=Literal[0], detail Review.version<=1, decision response Literal[1]; không tương thích draft đã sửa. Tái sử dụng JWT đã xác minh và role lookup server-side, cùng-origin cho mutation, no-store/error envelope/giới hạn đang có.
- UI đọc cùng tree: `portal/web/data/api-client.ts`, `components/draft-review-app.tsx` và tests liên quan. Snapshot UI này xuất xứ `a791a3f2be19b4c1593f82706c47b5dca97ab51a`, tree `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`. Parser exact, JS safe integer; UI chống double-submit và đã xử lý POST thành công nhưng refresh lỗi. Chưa sửa UI trong slice Backend kế tiếp.
- Đọc AGENTS.md, docs/PROGRESS.md và `docs/specs/W05-duyet.md`, `W05-draft-offline-contract.md`, `api-portal.md`; reuse `PHONG-HOA-W05-API-RESEARCH.md`, `PHONG-HOA-W05-API-IMPLEMENTATION-BRIEF.md`, `PHONG-HOA-W05-EDIT-RESEARCH.md`, `PHONG-HOA-W05-EDIT-LEADER-PLAN.md`. Leader plan đã thay các đề xuất cũ về v0 và reject snapshot; không hồi sinh quyết định bị thay.

## Những quyết định cần chốt trong nghiên cứu

1. So tối đa 3 cách đọc/lưu selection qua API; chọn một cách nhỏ nhất. Chốt method/path/body/response/error cụ thể và tính lặp của request. `expected_version` cùng core đã chống ghi đè; không tự retry mutation. Không thêm idempotency service, session store, dependency hoặc auth mới nếu không có lý do bắt buộc.
2. DTO rõ ràng cho summary/detail/selection save/decision: review và selection version, selected_indices/hash, counts, saved_by/time, changed chỉ nơi phù hợp. Phân biệt items.keep gốc với lựa chọn người dùng; không ghi đè payload hoặc giả version0/1 cho qua parser. Chốt miền integer JSON phù hợp SQLite và JS safe integer, validation strict không bool/coercion, duplicate/unknown/negative/empty/oversized input, extra fields và read-side dữ liệu hỏng.
3. **Detail phải có snapshot nhất quán.** Ghép get_draft và get_effective_selection bằng hai lần mở DB độc lập có thể lấy status/version ở hai thời điểm. Đọc code, chọn cách bảo đảm payload/review/selection đồng thời; nêu một thay đổi core nhỏ nếu thật sự cần thay vì tự viết SQL/nhân đôi validator trong service. Yêu cầu test interleaving có kiểm soát, không sleep. Save response lấy kết quả transaction đã commit, không đọc lại rồi gán nhầm thành kết quả mutation cũ.
4. Chốt version invariant/canonical hash và liên hệ selection với quyết định cuối; read v0/v1, historical audit NULL, DB v2 hỏng, no-op/stale/terminal. Không tự migrate qua GET hoặc qua việc khởi động API; không tự tạo DB nếu mất. Core đã có migration explicit; API nhận trạng thái chưa migrate phải có lỗi ổn định và không mutation.
5. Giữ danh tính JWT/subject/roles server-side, không tin email/body/header tự khai. Chốt Origin cho save selection như quyết định hiện tại, cả thiếu/sai; giữ chính sách đọc và lỗi401/403/404/409/422/503/no-store. Nêu rõ schema mới không được tạo đường vượt self-approve hay empty-approve.
6. Chốt tương thích với UI parser exact và kế hoạch nối: Backend API hoàn thành chưa nghĩa UI hiện tại chạy được. Không cài frontend fallback khiến mất lựa chọn hoặc quyết định nhầm. Brief Backend có contract mẫu synthetic và handoff cho Frontend sau nghiệm thu; chọn rõ thay path/version API hay cập nhật contract phối hợp, không vô tình phá bản tích hợp đã nghiệm thu.
7. Ma trận kiểm tập trung: auth/Origin/role; save/get/list version>1; selection empty/noneligible; no-op và stale; save-save/save-decision race; detail đọc xen writer; terminal/final snapshot; malformed JSON/types/extra/overflow/body limit; lỗi core không lộ chi tiết; cache headers; legacy/corrupt DB không bị ghi; API baseline regression. In-process với JWT/JWKS/SQLite tổng hợp, không listener hoặc browser ở slice Backend.

Đối chiếu nguồn chính thức HTTP method/conditional update, FastAPI/Pydantic strict validation và SQLite snapshot khi cần. Tái dùng nguồn đã đọc còn phù hợp, ghi link/ngày đọc và code/ref thực tế. Không suy tài liệu thành bằng chứng test đã chạy; không cần nghiên cứu lại JWT/gateway/LLM toàn bộ.

## Hai đầu ra duy nhất được ghi

1. `<workspace>\PHONG-HOA-W05-SELECTION-API-RESEARCH.md`: hiện trạng có file/ref, so phương án/chọn, nguồn và phần tái sử dụng, điểm chưa biết.
2. `<workspace>\PHONG-HOA-W05-SELECTION-API-IMPLEMENTATION-BRIEF.md`: tự đủ để giao CTI Backend/Sol medium. Đề xuất tree mới `<workspace>\cti-w05-selection-api`, nhánh `feat/w05-selection-api-20261111`, base b9c35bb ở trên; **không tạo tree trong nghiên cứu**. File scope cụ thể (API/test/docs và helper read core nhỏ nếu chứng minh cần), schema/signature/JSON example/error mapping, compatibility, acceptance matrix, TDD/checks/demo. Cấm UI/harness/deps/nguồn khác/RUNS; không giao UI triển khai lúc này.

Tự kiểm tài liệu đủ giao việc, báo hash hai file và trạng thái tree nguồn. Không sửa repo, báo cáo cũ, RUNS, memory; không chạy test sản phẩm để giả implementation; không cài gì, tạo DB/listener, đọc secret, gọi model/OpenCTI/cloud/lab, push/PR/merge/deploy. Web công khai chỉ để nghiên cứu nguồn. Leader quyết định sau khi đọc tài liệu, rồi giao triển khai.
