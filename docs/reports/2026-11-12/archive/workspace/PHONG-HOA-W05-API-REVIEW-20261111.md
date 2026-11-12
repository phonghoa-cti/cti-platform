# Leader review W05 API — 11/11/2026

Reviewed SHA `feac804818713a314d7db6bdc065b3a676234f32`, tree `cti-w05-backend`, branch `feat/w05-api-local-20261111`. **NEEDS_FIX R1–R3**. Leader đọc toàn bộ package API, kiểm test liên quan và chạy lại 77 test API: exit 0. Tree sạch. Số 355 full-suite là bằng chứng worker, không chạy lại trong review này.

Probe độc lập: `w05-api-evidence/leader_review_probe.py`, kết quả `leader-review-probe.json`; dùng RSA sinh trong RAM, SQLite tổng hợp tạm, TestClient in-process và chặn socket.create_connection. Không mạng/listener/token thật; không in token hoặc key. Lệnh chạy từ workspace Leader: `cti-w05-backend/.venv/Scripts/python.exe -X utf8 -B w05-api-evidence/leader_review_probe.py`, exit 0. Lần đầu thiếu UTF-8 bị lỗi in stdout sau khi ghi kết quả; lần chạy trên đã sửa tùy chọn encoding và hoàn tất.

## R1 — chặn token đúng dạng Cloudflare (ưu tiên cao)

`portal_api/auth.py`, `AccessJwtVerifier.verify`: `strict_aud=True` bắt audience claim phải là chuỗi. Token ký RS256 hợp lệ, issuer/sub/exp đúng, `aud=[configured_audience]` trả **401**, trong khi token có chuỗi audience tương ứng trả 200. Đây là lỗi tương thích, không phải bằng chứng vượt quyền.

[Cloudflare application token](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/application-token/) mô tả claim aud dạng mảng trong token danh tính. Nguồn chính thức được Leader kiểm ngày 11/11/2026. Kiểm chữ ký và audience vẫn bắt buộc; không chữa bằng bỏ verify_aud.

Quyết định: cấu hình một audience tin cậy. Chấp nhận claim chuỗi bằng chính xác giá trị đó hoặc mảng không rỗng chỉ chứa chuỗi không rỗng và có đúng giá trị đó trong các phần tử. Không substring/prefix/wildcard hoặc lấy audience mong đợi từ token. Mảng nhiều audience có phần tử khớp là hợp lệ; cập nhật ca hiện đang coi `[AUDIENCE, extra]` là sai. Mảng rỗng, sai kiểu, mixed types, không có audience khớp đều 401. Giữ RS256/chữ ký/issuer/expiry/subject/role và auth trước store.

RED/GREEN cần token ký thật cho string match, singleton-array match, multi-array match, wrong string/list, empty/mixed/list nested. Main demo nên dùng dạng mảng để không lặp blind spot.

## R2 — response lỗi bất ngờ thiếu no-store (ưu tiên vừa)

`portal_api/app.py`, middleware `review_headers` và `unexpected_handler`: store ném RuntimeError được đổi thành envelope 503 nhưng **Cache-Control và Vary đều vắng**. Handler Exception nằm ngoài luồng trả bình thường của middleware. Probe oversized integer cũng tới nhánh này. Trái hợp đồng mọi success/error dưới `/api/drafts` đều no-store.

Yêu cầu bảo đảm error ngoài dự kiến cũng có `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`, envelope sạch. Test bằng store ném lỗi có marker nhạy cảm tổng hợp; marker không ra response/log. Không trả traceback/path/token, không thêm cache dữ liệu.

## R3 — ID/cursor dài trả lỗi dịch vụ thay vì validation (ưu tiên vừa)

`portal_api/app.py`, `_parse_positive_integer`: trước kiểm giới hạn SQLite, `int()` nhận chuỗi 5.000 chữ số và ném ValueError của Python. `GET /api/drafts?before_id=<5000 chữ số>` đang trả **503**, yêu cầu là **422 invalid_request**. ID/path, before_id và limit dùng chung parser.

Chặn độ dài/giới hạn trước chuyển int hoặc bắt đúng lỗi chuyển kiểu; không nới giới hạn Python toàn tiến trình. Test 3 input này trả 422/no-store, không gọi store; giá trị biên SQLite và limit hợp lệ giữ nguyên. Không viết lại parser hoặc mở rộng endpoint.

## Phạm vi rework

CTI Backend, Sol medium, tự làm không giao bot khác, cùng tree/SHA trên. Chỉ API/auth/app/test/docs liên quan; không đổi core/store/migration, dependency nếu không cần. Giữ các giới hạn brief + Leader addendum; không sửa RUNS, file review/probe của Leader, tree khác. Local commit được phép, không push/PR/merge/deploy/Cloudflare thật/listener.

Viết regression đỏ trước sửa, chạy ca mới + toàn nhóm API, Ruff/format/diff-check và demo signed-token in-process. Không cần lặp toàn 355 nếu chỉ sửa API, trừ khi thay code dùng chung/dependency. Cập nhật báo cáo `PHONG-HOA-W05-API-RESULT.md` và bằng chứng mới không ghi đè probe Leader; báo SHA/count/exit và phần chưa kiểm. UI wiring vẫn phụ thuộc API nghiệm thu.

## Đóng R1–R3 ngày 11/11/2026

Leader kiểm diff tại `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04` và chạy 30 regression liên quan, exit0, tree sạch. Chấp nhận API trong phạm vi cục bộ; chi tiết PHONG-HOA-LEADER-REVIEW-20261111-0115.md. Không nâng thành production hoặc browser end-to-end.
