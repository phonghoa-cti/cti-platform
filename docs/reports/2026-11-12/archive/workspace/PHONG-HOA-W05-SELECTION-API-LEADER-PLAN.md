# W05 Selection API — nghiệm thu nghiên cứu và quyết định triển khai

Ngày 11/11/2026. **ACCEPTED RESEARCH WITH LEADER CORRECTIONS**; chưa có implementation hoặc test API v1. Tài liệu này chốt các điểm không thống nhất trong Research/brief, là đầu vào triển khai cùng hai tài liệu đó. Không sửa lại bằng chứng nghiên cứu gốc.

## Bằng chứng Leader đã kiểm

- Research request `ffd7ea79-21bf-4d71-8ebd-6c0035d5e8c6`.
- `PHONG-HOA-W05-SELECTION-API-RESEARCH.md`: SHA256 `3315288FB710DB80CCFB8D4D3012197027EDC6FA1E24D0D09613BDB58A30D70A`.
- `PHONG-HOA-W05-SELECTION-API-IMPLEMENTATION-BRIEF.md`: SHA256 `6F33D500BEA580D67CA2DCB268F61931A19571F6326319A13AB8A3495FD747AA`.
- Đã đọc hai tài liệu, đối chiếu `portal_api/app.py`, `schemas.py`, `service.py`, `settings.py`, các getter/mutation/result/error trong `extractor/phonghoa_extractor/store.py`, `AGENTS.md`, `pytest.ini`.
- Tree nguồn `cti-w05-selection` sạch tại `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`. Tree đích `cti-w05-selection-api` và branch đích chưa tồn tại lúc kiểm; worker phải kiểm lại trước tạo.
- Nguồn chính thức đã đọc lại: [SQLite isolation](https://www.sqlite.org/isolation.html), [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/), [RFC 9110 §9.2.2/9.3.3](https://www.rfc-editor.org/rfc/rfc9110). SQLite giải thích snapshot trong read transaction; Pydantic hỗ trợ kiểm kiểu nghiêm ngặt; POST không được tự retry khi chưa biết tác động. Đây là căn cứ thiết kế, không phải bằng chứng test sản phẩm.

## Mục tiêu và lựa chọn

Cho phép API đọc, lưu lựa chọn IOC và duyệt đúng lựa chọn đã lưu. IOC là dấu hiệu như địa chỉ IP/domain/hash. So với đổi API cũ đồng thời UI hoặc dựng lớp API khác, chọn thêm `/api/v1/drafts` trong app hiện có: tái sử dụng xác thực/quyền, tách contract mới khỏi parser UI cũ. Bản tích hợp cũ không bị nối sang DB mới trong lát cắt này.

Giữ bốn thao tác của brief: list, detail, POST selection, POST decision. Không làm UI, gateway, migration mới hoặc auth mới. Sau nghiệm thu API mới chuẩn bị bàn giao UI.

## Các quyết định thay phần mơ hồ/mâu thuẫn của brief

1. **Shape JSON chính xác.** List là summary legacy cộng `selection_version`, với `review_version` có thể >0; bỏ `selected_count` và `ai_eligible_count` trong ví dụ Research. Detail giữ payload bất biến, thêm review/selection đúng cùng snapshot. `SelectionView` đúng các trường trong brief, **không có `draft_id`**. Service ánh xạ tường minh, đổi tuple indices của core thành list JSON; không dùng `asdict()` nguyên trạng rồi mong strict DTO tự bỏ key/chuyển kiểu. GET trả `changed:false`; POST lấy `changed` từ kết quả core. Dùng đúng tên `selection.review_version` và `selection.selection_version`, không có `selection.version`.

2. **Đọc và quyết định phải cùng snapshot.** Hai helper read mới như brief; detail đọc payload/review/selection qua một connection, một read transaction. List không thêm counts/event query theo từng draft. Đối với decision, thêm `decide_draft_with_selection()` và result riêng chứa sáu trường decision cũ cộng `selection_version,selected_indices,selected_sha256`. Dùng chung một routine transaction với `decide_draft()`; wrapper cũ vẫn trả nguyên `DraftReviewResult` sáu trường để CLI/API cũ không đổi. Tạo result từ dữ liệu dùng để ghi final audit trong transaction, trả sau commit; không gọi getter sau commit, không nhân đôi policy/SQL mutation.

3. **Giới hạn số trước khi ghi.** V1 dùng `JSON_SAFE_INTEGER=9007199254740991` cho mọi trường số nguyên public, kể cả indices, counts, span, findings.paragraph, cost_tokens. Không bool/coercion; không sửa miền kiểu legacy. Số request vượt giới hạn → 422; read response vượt giới hạn → 503. Cho phép core mutation nhận keyword `max_version`, mặc định miền SQLite để giữ caller cũ; v1 truyền JSON_SAFE_INTEGER. Validate giá trị cap, kiểm cap trong write transaction trước UPDATE/INSERT. Changed save/decision làm version vượt cap → `DraftConflictError`/409, không ghi; no-op tại cap vẫn 200 sau kiểm actor/pending/version/eligibility. Không được commit rồi mới phát hiện overflow ở response DTO. Kiểm logic với cap nhỏ (ví dụ 2) trên DB thật tổng hợp, không tạo hàng triệu event hoặc giả version làm hỏng invariant. Adapter test phải chứng minh v1 truyền đúng cap.

4. **Mã lỗi.** Duplicate, âm, sai kiểu, extra key, unsafe integer hoặc quá số indices → 422 `invalid_request`, trước gọi core. Index không tồn tại hoặc IOC không eligible → 403 `forbidden` theo `DraftPolicyError` hiện có; sửa expectation 422 mâu thuẫn trong ma trận Research. Empty save hợp lệ; empty approve/self-approve vẫn 403. Missing draft row → 404. Missing DB → 503, tuyệt đối không tạo DB: thêm lỗi core cụ thể `DraftDatabaseNotFoundError(DraftNotFoundError)` tại những nhánh cần phân biệt; v1 dịch lỗi cụ thể này trước lỗi base. Legacy vẫn bắt base như cũ. Không suy lỗi bằng cách đọc chuỗi exception hoặc thêm filesystem check riêng ở service. Lỗi mở DB sau precheck tiếp tục qua `DraftSQLiteError` → 503. v0/v1/future/corrupt DB → 503, không migrate khi đọc/khởi động.

5. **Giới hạn request có giá trị cụ thể.** Hiện app/settings chưa có body limit, không tuyên bố tái sử dụng một setting chưa tồn tại. Chốt local v1 constants: tối đa **65,536 byte** raw body cho cả hai POST; `selected_indices` tối đa **1,024 phần tử**, sau đó core kiểm subset eligible. Đây là giới hạn vận hành ban đầu, không khẳng định giới hạn của dữ liệu CTI thực tế. Đọc body theo stream có đếm byte, dừng trước parse/core khi vượt; không chỉ tin Content-Length. Body quá lớn → 413 `request_too_large` cùng envelope/headers; list quá dài trong body hợp lệ → 422. Không đổi body handling legacy, không thêm dependency/settings mới. Test chunked/no Content-Length và boundary. Giới hạn 1,024 áp dụng input, không ép read response hợp lệ cũ phải có ít hơn 1,024 IOC.

6. **Xác thực, lỗi và compatibility.** Dùng Principal đã xác minh và role mapping hiện có; Actor không lấy từ body. Hai POST kiểm Origin chính xác và content type JSON hiện có. No-store/Vary/error handler bao phủ cả v1 success, validation, policy và unexpected errors, không lộ raw exception. Giữ tests/shape legacy; không đổi version giả về 0/1 và không tuyên bố legacy UI đã dùng được selection. Legacy UI chỉ dùng baseline tương thích cho đến khi được nối v1 riêng.

## Gói giao CTI Backend — W05-SELECTION-API-IMPLEMENT

Một implementer Sol medium, không giao tiếp bot/agent khác. User đã cho tiếp tục kỹ thuật cục bộ/nhánh riêng, không cần xin lại cho các quyết định đảo ngược trong phạm vi này.

Root: `$WORKSPACE`.

- Tạo worktree mới `<root>\cti-w05-selection-api`, branch `feat/w05-selection-api-20261111`, base chính xác `b9c35bb45cbf1000c1324ba46f1f162e0c02be44` từ repo nguồn `cti-w05-selection`. Không reset/ghi đè nếu path/branch đã xuất hiện; không sửa tree nguồn.
- Đọc AGENTS.md, docs/PROGRESS.md, spec W05, offline contract/API portal, Research + implementation brief và quyết định này. Tái sử dụng nghiên cứu, không lặp khảo sát JWT/LLM/gateway.
- Scope như brief: store.py; extractor selection/read/review tests liên quan; portal_api schemas/service/app/tests; docs/specs/api-portal.md, W05-draft-offline-contract.md và docs/PROGRESS.md. Có thể thêm một file tests v1 và một ADR ngắn dưới docs/adr cho version API. Phạm vi store bổ sung chính xác result/helper quyết định, lỗi DB cụ thể và version cap ở trên. Không chỉnh auth/settings/CLI/UI/dependency/harness hoặc xóa/làm yếu test cũ.
- Output ngoài repo chỉ `<root>\PHONG-HOA-W05-SELECTION-API-RESULT.md` và `<root>\w05-selection-api-evidence\`. Không sửa sổ RUNS, báo cáo/plan/probe của Leader, memory hoặc đầu ra đồng đội.
- TDD: chạy test mới RED rồi triển khai GREEN. Kiểm ma trận brief với sửa lỗi ở trên, đặc biệt snapshot reader/writer deterministic không sleep; save-save/save-decision race; canonical/no-op/stale/empty/eligibility; committed final snapshot không reread; version cap không mutation; body limit; DB thiếu/corrupt; quyền/self-approve/Origin và legacy regression.
- Test in-process, JWT RSA/JWKS/SQLite tổng hợp, không network/listener/browser/real secret. Dùng Python/dependency đã có; không cài mới. Chạy targeted core selection + API (cả v1 và legacy), sau đó toàn Python theo pytest.ini một lần khi targeted xanh; Ruff check/format cho changed Python và git diff --check. Không chạy UI/full browser. Mỗi lệnh có giải thích ngắn trong log/report, ghi fresh exit code và số test chính xác bằng JUnit, không đếm dấu chấm.
- Demo in-process: list/detail version>1 → changed save → no-op → approve/reject cùng snapshot final audit; tình huống stale và empty approve bị từ chối. Lưu JSON tổng hợp và kiểm payload/items.keep bất biến.
- Commit cục bộ Conventional Commit sau checks, báo base/head/branch/diff/status, manifest hashes, các lỗi đã sửa và phần chưa xác minh. Không push/PR/merge/deploy, không OpenCTI/lab/cloud/model thật, không đổi trust/quyền.

## Mức hoàn thành và bước nối

Hiện tại chỉ **nghiên cứu đã nghiệm thu có hiệu chỉnh**. Leader chưa chạy test cho code API v1 vì code chưa được triển khai. Handoff được tính đã giao chỉ sau receipt thành công và ghi sổ.

Khi Backend trả kết quả: Leader review diff/bằng chứng và kiểm tập trung phần mới; nếu đạt thì chuẩn bị UI selection trên contract v1 đã chốt. Browser, gateway v1, Cloudflare/JWKS thật, lab và OpenCTI vẫn chưa được xác minh. Dự án tiếp tục active; lịch tiếp tục mỗi 30 phút vẫn được giữ, không coi callback/guard là bằng chứng worker sống hoặc phục hồi bỏ dở đã được kiểm.
