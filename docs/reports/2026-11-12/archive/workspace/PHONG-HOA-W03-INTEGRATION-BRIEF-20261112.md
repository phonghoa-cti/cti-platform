# W03-READ-INTEGRATION — nối và kiểm tra lỗ hổng cục bộ

ROOT = $WORKSPACE

CTI Engineer, một Sol medium trực tiếp; không worker con/bot khác. Người dùng cần xem CVE liên quan danh sách Công nghệ và ưu tiên kiểm tra, bằng luồng UI → gateway → API → cùng SQLite. Đây là W03-R chỉ đọc, nguồn CVE synthetic được ghi nhãn; không kết luận phiên bản bị ảnh hưởng.

## Đầu vào và tree
- Backend accepted: ROOT\cti-w03-read-backend tại abcd14dacca361791b17719632d2ce38557d6baf. Đọc leader-w03-backend-acceptance-20261112/ACCEPTANCE.md.
- Frontend accepted: ROOT\cti-w03-read-frontend tại f650f04de8f08238e13e2630f974e9f30ef838b5. Đọc leader-w03-frontend-acceptance-20261112/ACCEPTANCE.md.
- Base chung273196e2d23b36172d57cc61b289522786d61b2a. Tạo ROOT\cti-w03-read-integration, branch feat/w03-read-integration-20261112 từ Backend accepted.
- Cherry-pick cục bộ 5c968c74cc53c5798bcf8adaf8695dacfd86ffd4 rồi f650f04de8f08238e13e2630f974e9f30ef838b5. PROGRESS giữ hai phần đúng. Không merge branch/main; không sửa hai tree nguồn. Nếu target đã có thì kiểm owner/ref/dirty, giữ edits, không reset.
- Trước wiring, chứng minh portal_api giống Backend và portal/web giống Frontend accepted; báo SHA các cherry-pick.
- Đọc AGENTS/PROGRESS/spec đúng branch; contract ROOT\PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md và docs/specs/W03-read-local-contract.md, nghiên cứu ROOT\PHONG-HOA-W03-RESEARCH-20261112.md còn phù hợp. Tái dùng harness W04 đã accepted, không nghiên cứu kiến trúc mới.
- Người dùng đã cho phép phát triển/tích hợp cục bộ liên tục. Không xin duyệt lại thay đổi nhiều file trong phạm vi.

## Phạm vi mới
1. tools/local_integration/: opt-in W03 scenarios, fixture tổng hợp12+ CVE với provenance/hash; inject CveReadPort và TechnologyStore cùng DB của W04, schema/seed chỉ trong setup. Scenario cũ không tự bật fixture.
2. gateway.mjs: allowlist chính xác GET /api/cves, query giữ nguyên; chặn mutation/route gần đúng, không mở proxy /api/* chung. Giữ quản lý JWT ở server, Origin/body/header/bounds hiện có. Không lộ token/key vào UI/log/URL/evidence.
3. Dùng CveHttpClient và /lo-hong đã có, không fallback fixture ở client; /lo-hong/mau giữ nhãn mẫu. Không redesign, không nhân bản matching/rank trong UI.
4. Thêm/mở rộng HTTP matrix, browser helper bounded, tests, README/PROGRESS và evidence. W03 GET đọc cùng DB và không làm thay schema/rows/audit/user_version.
5. Allowlist: tools/local_integration/**, portal/web/tests/*cve* và test fixtures cần đối chiếu wire, docs/PROGRESS.md, docs/specs/W03-read-local-contract.md chỉ ghi cách tích hợp, báo cáo/evidence. Không đổi portal_api/core/auth/deps/lock/schema, component/provider đã accepted hoặc RUNS. Nếu wiring có lỗi ngoài phạm vi, trả repro/minimal fix cụ thể, không tự nới.

## Hợp đồng và HTTP
Trước browser, đưa wire lấy từ API thật qua parser Frontend: detail/summary/empty/error/409, null và0, notice đúng literal, input dài hợp lệ và response sát cap1MiB. Dữ liệu lớn hợp lệ không bị adapter từ chối; vượt cap trả lỗi không truncate. Không dùng DTO fixture tự viết làm bằng chứng API.
Kiểm gateway/HTTP tập trung:
- IT/analyst/admin/mixed role detail, leader-only summary không lộ matches/asset metadata; missing token401, forbidden403, client giả JWT không tăng quyền.
- vendor/product exact casefold, version chỉ hiển thị; ranking KEV→EPSS→CVSS→ngày→CVE ID; null khác0; filters/paging đủ12+ candidate, không lặp/bỏ item.
- W04 create/update/delete qua API thật trên cùng DB làm thay matches phù hợp. Cursor đang dùng gặp snapshot đổi trả409; bắt đầu lại phản ánh dữ liệu mới. Ghi riêng các mutation setup/W04 để không lẫn với GET W03.
- Summary filter asset bị403, query malformed422; dependency unavailable503; response no-store/Vary. Reuse component tests đã accepted cho ma trận chuyên sâu, không lặp full345/356.
- SQL snapshot trước/sau W03 GET200/404/409/503 giữ nguyên schema,rows,audit,version; DB thiếu không tự tạo. Mutation W04 chỉ nằm ở ranh giới setup/controlled test rõ.
- GET503 → manual retry200 thực sự; trace không có W03 POST/PUT/PATCH/DELETE. Không gọi feed thật.

## Browser qua công cụ OpenMausBot
Áp dụng browser-integration-acceptance. Chỉ Engineer dùng browser lượt này. Không tự launch browser hoặc thay bằng automation khác. Sau navigation kiểm trang thật; nếu công cụ không làm được thì ghi đúng blocker, giữ HTTP PASS riêng.
Tối thiểu3 run gọn:
1. IT /lo-hong: thấy source synthetic, notice phiên bản, filter KEV/q/technology; paging, detail, score0/null; controlled change của data giữa trang gây409, tải từ đầu200 và dữ liệu mới không trộn cũ.
2. Leader summary: chỉ summary fields, không filter/detail tài sản; trace chứng minh **không gọi Technology API**.
3. Failure/recovery: GET503 hiển thị lỗi, retry thủ công200 và list khớp; không mutation hoặc retry vô hạn.
HTTP matrix chứng minh W04 changes thật; browser409 helper có thể dùng controlled setup change trong DB test giữa hai GET, ghi rõ state change/SQL delta, không giả response409 khi backend chưa đổi snapshot.
Mỗi run: ảnh trước/sau cần thiết + thao tác/lỗi/trạng thái, viewport thật, sanitized method/path/status trace, DB snapshot. Chỉ ảnh không đủ bằng chứng quyền/non-mutation. Trình duyệt desktop đạt khác mobile360px; không dùngCSSscale/ảnhresize giả viewport. Nếu tool không resize thực, đánh dấu mobile UNVERIFIED, không tự chuyển máy/lab.

## Kiểm và giao kết quả
- RED→GREEN cho gateway/runner/helper mới; test phần bị ảnh hưởng, Ruff/format/diff. Nếu thêm validator, test cả dữ liệu bị sửa để tránh false PASS.
- Chạy W03 focused và wire compatibility trên kết quả ghép một lượt; gateway/harness targeted; W04 smoke có rủi ro do sửa harness. Typecheck/lint khi frontend test/code đổi, build cần để chạy browser. Không lặp nguyên lịch sử hay toàn portal/core.
- Chọn interpreter có dependency harness sẵn, đọc README trước (môi trường API có thể thiếu uvicorn); PYTHONPATH/cwd phải trỏ target tree. Không sửa dependency môi trường khác.
- Helper foreground có giới hạn thời gian, không sleep/poll vòng lặp. Cleanup chỉ tài nguyên sở hữu: helper stopped, PID đóng, port đóng, temp root xóa; lưu evidence ngoài temp trước cleanup.
- Output ROOT\PHONG-HOA-W03-INTEGRATION-RESULT.md và ROOT\w03-integration-evidence\; manifest SHA256, command/exit/count, source/finalHEAD sạch, diff và limitation. Artifact phải đúng SHA chạy; giải thích docs/evidence-only commit nếu có.
- Không push/PR/merge/deploy, lab, live OpenCTI/CISA/feed/LLM, đọc secret, cài dịch vụ hoặc đổi quyền. Dataset tổng hợp không chứng minh CVE thật/accuracy/version-range.
Sau trả kết quả Leader kiểm bằng chứng mới và nối phần đủ điều kiện của dự án; không tự giao bot khác.
