# W05 Selection UI — nghiệm thu nghiên cứu và yêu cầu triển khai

Ngày 11/11/2026. **ACCEPTED RESEARCH WITH LEADER CORRECTIONS**. Chỉ nghiên cứu được nghiệm thu; UI selection chưa triển khai hoặc chạy kiểm thử. Các quyết định dưới đây thay phần mâu thuẫn của hai tài liệu Research, giữ nguyên tài liệu gốc để đối chiếu.

## Bằng chứng và lựa chọn

- Request Research: `0b60f0e5-0e78-469d-9440-f5fcf08adc1f`.
- `PHONG-HOA-W05-SELECTION-UI-RESEARCH.md`: SHA256 `0D79648C5977B05B544321DCE7E6674386E5AED77428D1F733F3868350F706C1`.
- `PHONG-HOA-W05-SELECTION-UI-IMPLEMENTATION-BRIEF.md`: SHA256 `47F1DAA8188F3698D2201000357A2B498BE3F2535901566BDE1ED3588BA0C308`.
- Leader đã đọc hai tài liệu và đối chiếu API v1 đã nghiệm thu, `portal_api/schemas.py`, client, adapter, hai component UI, package scripts và AGENTS.md trên tree nguồn. HEAD `812dae1ffbdc8e8866342cc075d925fdc99ef12d`, status sạch; path và branch đích chưa tồn tại lúc kiểm. Không chạy lại bộ test API đã nghiệm thu.
- Đã đọc lại [React: cấu trúc state](https://react.dev/learn/choosing-the-state-structure), [React: useEffect](https://react.dev/reference/react/useEffect), [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController). Tái sử dụng state suy ra từ dữ liệu và cơ chế bỏ qua phản hồi cũ. Đây là nguồn thiết kế, không phải bằng chứng UI chạy đúng.

Mục tiêu: người duyệt sửa tập IOC đủ điều kiện, lưu rõ ràng, rồi quyết định trên bản đã lưu. IOC là dấu hiệu như IP/domain/hash. Chọn nút **Lưu lựa chọn** riêng thay autosave hoặc tự lưu khi duyệt: ranh giới ghi rõ, dễ xử lý lỗi và giữ đúng snapshot (bản dữ liệu tại một thời điểm). Giữ thiết kế SOC và hai trang hiện có, không redesign.

## Quyết định bắt buộc

1. **Giới hạn 1.024 chỉ cho request lưu.** Response đọc hợp lệ có thể chứa hơn 1.024 indices; không từ chối, cắt bớt hoặc tự chọn lại. Hiển thị nguyên tập đã lưu. Nếu tập đang sửa >1.024, vẫn cho bỏ chọn, chặn thêm và chặn lưu tới khi giảm còn tối đa 1.024. Ở 1.024, chặn chọn thêm. Tập đã lưu >1.024 và không dirty vẫn được quyết định theo policy backend; giới hạn save không áp lên body decision. `[]` được lưu; chỉ **approve** yêu cầu tập đã lưu không rỗng. **Reject** được dùng với tập rỗng đã lưu và lý do không trắng.

2. **Không khóa chính thao tác sửa khi dirty.** Tách `items.keep` bất biến, selection đã lưu và tập đang sửa. Dirty được suy ra bằng so sánh tập. Khi dirty: cho checkbox eligible, lưu và hủy thay đổi; khóa đổi draft, tải thêm/khởi tạo lại hàng đợi, tải lại detail thông thường và cả hai quyết định. Khi gửi POST: khóa mọi mutation/navigation và chống nhấp hai lần bằng khóa đồng bộ trước await. Đọc bằng chứng, copy và đổi VI/EN vẫn dùng được. Khi lỗi cần hòa giải trạng thái, phải còn nút phục hồi cụ thể; không áp một cờ khóa chung làm nút tải lại cũng bị khóa.

3. **Một trạng thái hành động rõ ràng.** Dùng enum/union hoặc cách tương đương để không xuất hiện cùng lúc saving/deciding/unknown/refresh-failed. Saved selection thuộc đúng draft ID và generation; reset dữ liệu hiển thị liên quan khi đổi ID. Không khởi tạo selection từ `items.keep` trong API mode. Sample giữ hành vi xem/chọn thử hiện có, nhãn mẫu và tuyệt đối không gọi API; không sửa fixture mẫu để giả đã ghi.

4. **Phân loại kết quả POST.** Transport error, abort sau gửi, mọi 5xx (kể cả 503), 2xx không parse được hoặc sai association/version/snapshot đều là **chưa biết kết quả ghi**. Giữ lựa chọn hiển thị, khóa save/decision, không tự gửi lại. Không dùng câu “thử gửi lại” cho các lỗi này. HTTP 401/403/404/409/413/415/422 với envelope/code đúng hợp đồng mới được coi là lỗi từ chối có biết trạng thái; lỗi/envelope khác xử lý thận trọng như unknown. Không hiện raw message/exception. GET lỗi có thể retry GET bình thường.

5. **Phục hồi không làm mất dữ liệu âm thầm.** 409/422 hoặc unknown giữ tập sửa để người dùng thấy, hiện nút rõ nghĩa **Bỏ thay đổi cục bộ và tải lại trạng thái**; click đó là lựa chọn bỏ tập sửa, không cần modal mới. Chỉ thay mô hình sau GET detail hợp lệ, đúng ID/generation; GET thất bại giữ nội dung và khóa mutation. Không gửi GET phục hồi khi POST phía client còn đang chờ. GET thành công cho biết trạng thái hiện tại, không chứng minh POST trước của chính người dùng đã thành công: không tự hiện “đã lưu/đã duyệt” cho lần gửi chưa có response hợp lệ, kể cả indices trùng. Nếu version không tăng, nói chưa xác nhận lần ghi trước; mọi thao tác ghi tiếp là một click mới trên snapshot vừa tải, dùng expected_version mới đọc, không phát lại request đã giữ. Khóa version/transaction backend vẫn quyết định cạnh tranh nếu request cũ còn xử lý. Không thêm idempotency key/backend trong lát cắt này.

6. **Success và refresh là hai kết quả riêng.** Save có response hợp lệ: cập nhật ngay saved/editing và review version từ response, hiện đã lưu/no-op, không tự quyết định. Sau đó refresh detail + queue để đồng bộ hiển thị; nếu refresh lỗi, giữ bằng chứng save thành công và snapshot response, khóa mutation, hiện nút chỉ tải lại trạng thái. Kiểm dữ liệu refresh không lùi về version thấp hơn response đã ghi; dữ liệu stale không được mở khóa. Decision tương tự: success còn nguyên khi refresh lỗi hoặc hàng đợi cuối trở thành rỗng. Không POST lại từ các nút refresh.

7. **Strict v1 riêng và kiểm ngữ cảnh.** Giữ legacy parsers/API riêng nếu còn export/test; không nới parser cũ để lẫn contract. API mode dùng `/api/v1/drafts` cho list/detail/save/decision. DTO chính xác theo `portal_api/schemas.py` và `docs/specs/api-portal.md`, cùng invariant trong core; không dựa riêng ví dụ Research. Mọi số public phải safe integer, không bool/coercion; indices sorted/unique, trong bounds và eligible. `SelectionView` không có draft_id, nên gắn theo request ID/generation, không gắn tùy current draft sau await. GET detail: selection.review_version = review.version; pending review.version = selection_version, terminal review.version = selection_version + 1; GET changed=false. List pending review_version = selection_version. Kiểm metadata/counts theo core, không tự invent dữ liệu thiếu. SHA là lowercase 64 hex; decision hash phải bằng hash đã lưu, không cần thêm thư viện hash.

8. **Kiểm response so với request bị giữ cố định.** Save trả indices đúng tập vừa gửi; changed=true tăng cả review_version/selection_version một, changed=false giữ chúng; không overflow. Decision trả đúng draft_id, approve→approved/reject→rejected, version=expected_version+1 và snapshot indices/hash/selection_version đúng bản đã lưu trước gửi; reject reason đúng lý do đã trim, approve reason null. Mismatch không được tính success. Cả client parser và component dùng injected API tests phải bảo vệ association cần thiết. Số ở trần safe integer đọc được; không làm phép tăng rồi chấp nhận số không an toàn.

9. **Lỗi từ chối và khả năng dùng.** 401/403 giữ lựa chọn, báo cần đăng nhập/quyền; không suy role từ email/token client. 404 giữ thông báo draft không còn, có đường bỏ thay đổi rồi về hàng đợi. 409/422 yêu cầu tải lại. 413 cho giảm lựa chọn rồi thử thao tác mới; 415 báo lỗi yêu cầu an toàn, không workaround. Tất cả không retry POST tự động. Reload/race khi đổi draft, reload queue, load-more, unmount và locale phải được xét; phản hồi cũ không thay detail/selection/count của draft mới.

## Gói triển khai W05-SELECTION-UI-IMPLEMENT

Owner CTI Frontend, Sol medium, một implementer, không giao bot/agent con. User đã cho tiếp tục kỹ thuật cục bộ trên tree riêng, không cần hỏi lại cho phạm vi dưới đây.

Root: `$WORKSPACE`.

- Source read-only: `<root>\cti-w05-selection-api`.
- Tạo `<root>\cti-w05-selection-ui`, branch `feat/w05-selection-ui-20261111`, base **812dae1ffbdc8e8866342cc075d925fdc99ef12d**. Kiểm path/branch/status trước tạo, không reset/ghi đè nếu đã có. Không sửa tree nguồn hoặc tree Frontend cũ.
- Đọc AGENTS.md, docs/PROGRESS.md, spec W05/API/offline contract; hai tài liệu Research và plan này. Tận dụng phần đã nghiên cứu; không khảo sát lại auth/LLM/hạ tầng.
- Cho sửa `portal/web/data/api-client.ts`, thêm module v1/types/helper selection dưới data/lib nếu cần; hai component review/app; `messages/vi.json`, `messages/en.json`; tests/helper/fixture tổng hợp riêng dưới tests; `portal/web/README.md`, `docs/PROGRESS.md`. `app/globals.css` chỉ bổ sung trạng thái/controls cần thiết theo token hiện có; không thay bố cục/thương hiệu. Adapter chỉ đổi tối thiểu để tái sử dụng parser payload, không làm yếu validation. Không đổi sample fixture đã có.
- Không đổi package.json, lockfile, config build/test/lint, backend/core/API/settings/auth/gateway/harness hoặc docs spec API. Không thêm dependency. Có thể chuẩn bị dependency theo lock hiện có bằng npm ci trong tree mới nếu thiếu; giữ hash lock, không upgrade. Dữ liệu/asset tracked và ignored cần thiết phải được kiểm nguồn trước copy; không tạo fixture thay thế âm thầm.
- Output ngoài repo chỉ `<root>\PHONG-HOA-W05-SELECTION-UI-RESULT.md` và `<root>\w05-selection-ui-evidence\`. Không sửa RUNS, báo cáo/plan/probe Leader hoặc đầu ra đồng đội.
- TDD: viết regression có ý nghĩa, chạy RED trước implementation; GREEN từng nhóm. Chạy targeted rồi full Vitest một lần khi xanh, typecheck, lint, build, git diff --check. Lưu fresh exit code và số test từ reporter, không đếm dấu chấm. Có thể dùng fake-fetch/deferred promise để điều khiển race, không sleep. Không xóa/làm yếu regression cũ; khi chuyển contract component, giữ test legacy parser và chuyển fixture UI rõ nguồn.
- Không mở listener, browser, cloud/model thật, OpenCTI/lab hoặc dùng secret/dữ liệu thật. Build/test cục bộ không phải bằng chứng tích hợp browser. Không push/PR/merge/deploy/đổi quyền/trust.
- Commit cục bộ Conventional Commit sau checks; báo exact base/head/tree/branch, diff/stat/status, manifest SHA256, kết quả và giới hạn. Giải thích ngắn hai khái niệm saved/editing cho người mới.

## Acceptance phải có bằng chứng

| Nhóm | Tình huống quan trọng |
|---|---|
| Contract | Valid v1 bốn thao tác; extra/missing/unsafe/bool/unsorted/duplicate/index ngoài bounds/ineligible; legacy không nhận lẫn v1; sai status/version/draft/snapshot bị từ chối. |
| Chọn và lưu | Chỉ eligible sửa được; items.keep/payload byte-equivalent; dirty không POST; save body exact; saved version/hash đúng; discard khôi phục; no-op được client xử lý. |
| Biên | Empty save, empty approve disabled, empty reject enabled + reason; 1.024 input được lưu/1.025 bị chặn; read >1.024 hợp lệ, deselect xuống ngưỡng, clean decision không bị chặn vì ngưỡng save; safe ceiling. |
| Khóa | Dirty vẫn sửa/lưu/discard được; navigation/reload/decision bị chặn; saving chặn double-submit và decision; nút phục hồi không deadlock. |
| Kết quả mơ hồ | POST network/abort/503/2xx malformed/mismatch khóa gửi lại; GET phục hồi thất bại giữ edits; GET thành công không giả success cho POST; chỉ click mới mới ghi, không replay request cũ. |
| Success rồi lỗi | Save/decision response hợp lệ + refresh fail/stale giữ success và snapshot, chỉ retry GET; quyết định draft cuối vẫn thấy xác nhận khi queue rỗng. |
| Race | Deferred GET/POST của A không ghi đè B; chọn lại cùng ID không xóa detail; queue retry/load-more không bỏ dirty; unmount/generation; locale không refetch/mất state. |
| Giữ UI | Sample có nhãn, chọn thử không API; API không fallback mẫu; VI/EN, text-only IOC/defang, clipboard failure/success, evidence Unicode/focus, keyboard/labels giữ đúng. |
| Checks | Full Vitest, typecheck, lint, build, diff-check xanh; tree sạch sau commit. |

## Bước nối và mức xác minh

Leader nghiệm thu code và tập trung kiểm rủi ro mới khi Frontend trả kết quả. Sau UI accepted, giao CTI Engineer việc mở gateway v1 có giới hạn và kiểm luồng cùng origin trên trình duyệt. Đó là task tiếp theo, không nằm trong assignment Frontend này.

Dự án vẫn active. Lịch tiếp tục mỗi 30 phút đã kiểm enabled=true, lượt gần nhất 04:26 giờ Việt Nam trả NOTHING NEW khi Leader đang xử lý, lượt kế 04:56. Giữ lịch. Chưa xác minh UI mới, gateway/browser v1, Cloudflare/JWKS thật, lab/OpenCTI/production; guard/callback không chứng minh phục hồi việc bỏ dở.
