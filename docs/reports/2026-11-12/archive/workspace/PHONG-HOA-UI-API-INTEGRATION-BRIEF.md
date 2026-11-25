# Nối giao diện W05 với hợp đồng API đã kiểm

## Mục tiêu và quyết định

CTI Frontend triển khai client gọi API cho hàng đợi, chi tiết và duyệt/từ chối; giữ thiết kế Phong Hỏa, VI/EN, evidence Unicode, IOC không thành link và clipboard đã sửa. Tận dụng PHONG-HOA-W05-API-RESEARCH.md + LEADER-ADDENDUM và code API đã nghiệm thu; không nghiên cứu lại toàn portal.

Ba cách đã cân nhắc: client relative URL, proxy Next kèm client, hoặc gateway ngoài. Chọn **client relative URL ở lát cắt này**: không thêm tầng xác thực/proxy chưa kiểm. Hạ tầng định tuyến cùng origin và kiểm end-to-end với backend sẽ là bước riêng sau bàn giao. Không báo client test bằng fetch giả là browser đã nối FastAPI thật.

Workspace gốc: `$WORKSPACE`.

Owner CTI Frontend, Codex/Sol medium, tự làm không giao bot khác. Tree `cti-portal-web` sạch ở `9b10223d90e529432d976177e14fdf2b6ce46bb7`; tạo branch `feat/portal-w05-api-client-20261111` tại tree này. Chỉ sửa portal/web/** và docs/PROGRESS.md. Không merge/cherry-pick, không sửa backend/AI/tree gốc/RUNS. Local commit được phép, không push/PR/merge/deploy.

## Nguồn hợp đồng và tái sử dụng

Đọc AGENTS.md/spec/progress đúng tree, implementation đã có `portal/web/data/draft-adapter.ts`, components/draft-review*.tsx, lib/evidence.ts và tests/messages. Đọc tham khảo backend bằng `git show 02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04:portal_api/schemas.py` và app.py/service.py/tests/test_w05_api.py từ cti-w05-backend. Không dựa vào ví dụ POST cũ trong nghiên cứu: **response decision thực tế phẳng**, không có review lồng bên trong.

| Request | Response/điều kiện |
|---|---|
| GET /api/drafts?limit=20&before_id=N | `{items: DraftSummary[], next_before_id: number|null}`; summary gồm id/created_at/status/source/language/tlp/item_count/injection_warning/review_status/review_version, không text/items/evidence |
| GET /api/drafts/{id} | Payload 1.0 cũ + `review:{status,version,created_by_subject,decided_by_subject,decided_at,reason}`. Payload.status luôn pending; trạng thái duyệt hiển thị lấy review.status |
| POST /api/drafts/{id}/decision | JSON `{decision:'approve',expected_version:N}` hoặc `{decision:'reject',expected_version:N,reason:'...'}`. Response phẳng `{draft_id,status,version,decided_by_subject,decided_at,reason}` |

## Luồng người dùng và boundary

- `/duyet` dùng API thật qua fetch URL tương đối same-origin, credentials same-origin, cache no-store. `/duyet/mau` giữ preview dữ liệu tổng hợp, có nhãn rõ và nút duyệt vô hiệu. Không tự fallback sample khi API lỗi. Không tự tạo proxy, gateway, login, token, role hoặc me endpoint. Không đọc/store JWT trong browser; không gửi subject/role/email; browser tự gửi Origin khi POST, không giả header.
- Tách summary/detail DTO và parser runtime. Kiểm array/enum/null/boolean/safe integer trước dùng; ID/cursor không an toàn Number.MAX_SAFE_INTEGER phải lỗi rõ, không làm tròn. Dùng lại parser payload/evidence. Giao diện không hiển thị raw response/HTML/exception message hoặc log CTI/identity/token.
- Queue tải trang đầu, có tải thêm bằng next_before_id và ngừng khi null; số đếm chỉ số đang tải được. Chọn draft mới gọi detail riêng, không đoán detail từ summary. Loading/empty/error/retry riêng cho queue và detail. Abort hoặc sequence guard để response cũ không ghi đè lựa chọn mới.
- API mode giữ `keep` read-only: backend hiện chưa nhận sửa IOC. Không để người dùng chỉnh checkbox rồi tưởng approve lưu chỉnh sửa. Preview có thể giữ thao tác cũ với nhãn mẫu. Quyết định chỉ trên bản nháp đang hiển thị và review pending.
- Approve/reject là thao tác người dùng bấm; reject cần lý do không trắng. Gửi đúng expected_version từ detail hiện có. Khóa nút khi đang gửi, không gửi kép, không tự retry POST. Chỉ báo thành công sau response 200 hợp lệ; ghi rõ đã duyệt/từ chối cục bộ, chưa nhập OpenCTI. Refresh queue và detail/trạng thái sau thành công, giữ thông báo dễ thấy.
- Backend là nơi quyết định quyền/chống tự duyệt. Không có current-sub endpoint nên không giả nhận biết ai đang đăng nhập; xử lý403 theo phản hồi thật. Không thêm client role dropdown hoặc dev identity.
- Lỗi401: cần phiên đăng nhập hợp lệ;403: không có quyền quyết định;404: draft không còn khả dụng;409: dữ liệu đã đổi, tải lại trước khi người dùng quyết định lại;422: kiểm thông tin nhập;415/503/network/non-JSON: dịch vụ chưa sẵn sàng hoặc lỗi gửi, thông báo VI/EN an toàn. Không dùng nội dung message từ server làm HTML hoặc in raw error. Với409 không auto-submit lại; loại quyền thao tác dựa trên version cũ.
- Không thêm luồng chỉnh sửa, nhập OpenCTI hoặc xóa. Không đổi layout/thẩm mỹ ngoài trạng thái và controls cần cho các luồng trên. Giữ accessibility focus/labels/live status và Unicode span/defang/clipboard regressions.

## Kiểm và phạm vi bằng chứng

Viết tests RED rồi code: parser theo response thực, list pagination, detail loading/stale-response, approve và reject payload/version, blank reason, double click, failure rồi retry thủ công, 401/403/404/409/422/415/503, network/non-JSON/malformed-success, pending payload với review approved, preview không POST, sample không tự fallback. Fetch giả/injected transport chỉ trong test; không thêm endpoint bypass auth.

Chạy npm test/typecheck/lint/build và diff-check. Dùng dependency hiện có, không nâng thư viện tùy tiện. Browser tích hợp nếu khả dụng: preview và API-unavailable state, port3002 nếu cần; dừng listener đã tự mở. Không dùng màn hình riêng/ngõ khác để né giới hạn. 360/1440 đang UNVERIFIED do không resize; giữ đúng trạng thái, không CSS/zoom giả viewport. Browser luồng thành công với backend thật chưa có gateway/auth, ghi rõ UNVERIFIED thay vì giả.

Báo `PHONG-HOA-UI-API-RESULT.md` + `ui-api-evidence/` tại workspace gốc: SHA/diff/tree, commands/count/exit, mapping contract kiểm, screenshots nếu có và phạm vi mock vs browser. Handoff ngắn cho Engineer về routing `/api/drafts*` cùng origin tới FastAPI, không cấu hình phát hành. Bước sau: Leader review client rồi giao kiểm tích hợp cục bộ có signed JWT tổng hợp; chưa cloud/secret/lab.
