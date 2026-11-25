# Nghiệm thu HTTP W02 và xử lý lỗi hậu kiểm X01

Ngày 11/11/2026. Root tuyệt đối: `$WORKSPACE`.

## Quyết định

- Giữ nghiệm thu cũ importer `fc08897a240d9e55198b1a8166b21e8e7caf7213` và UI `a949081bf302801e11d69a8ee70c1232d68955cc`; không tạo việc hoặc chạy lại suite vì báo cáo lặp.
- Chấp nhận W02 HTTP adapter `88e9a9b6e491c0d450640e848043f41c80feb4bd` ở mức parser/transport và component với HTTP giả. Chưa gắn route hay kết nối Backend thật.
- Chấp nhận báo cáo QA với kết luận **FAIL hậu kiểm harness** tại `970a130452eb69bae3cd3793eab5a527b3d382d5`. Chưa chấp nhận implementation harness; Engineer sửa F1–F3 trong cùng tree/thread.
- Backend tiếp tục W02 ở cùng tree/thread sau một lần provider capacity error. Không reset ba file dở, không tạo người thay thế hoặc đổi model ngầm. Đây là lần thử lại đầu tiên cho lỗi này.
- Hai việc Backend và Engineer độc lập; chưa cần thêm thành viên. Frontend đã hoàn tất phạm vi adapter; chờ API được nghiệm thu để nối. QA kiểm lại sau commit sửa ổn định.

## Bằng chứng Leader

- Đã xem một lần danh sách threads/bots: các thread worker liên quan idle, chỉ thread Leader hiện hành đang chạy; không có writer khác trên ba tree.
- PR mở kiểm bằng `gh pr list --repo phonghoa-cti/cti-platform --state open --json number,title,headRefName,headRefOid --limit 20`, exit 0: #1 `8d9d7df54e90a1811b58a713cfe7ec56072ed0a7`, #46 `36259c118f519d3ac9cfc1f7b79e7180c2448a88`. Không dùng main thay các ref được giao.
- HTTP: exact HEAD sạch, diff 8 file +684/-8 đúng allowlist; đọc parser, transport, các thay đổi types/messages/tests. Manifest 22/22 khớp. Chạy tươi `npm.cmd test -- tests/ioc-lookup-http.test.ts tests/ioc-lookup.test.tsx`: **88/88**, 2 file, exit 0. Đối chiếu raw evidence regression 177/177, typecheck/lint/build exit 0; không chạy lại các kiểm này.
- QA: manifest 5/5 khớp; đọc probe và implementation. Chạy `cti-x01-ingest-browser-prep/.venv/Scripts/python.exe -X utf8 -B leader-w02-harness-review-20261111/verify.py`, exit 0. Baseline hợp lệ PASS; bốn ca sai vẫn bị verifier nhận PASS: đổi tên trong envelope, đổi đồng bộ ba actor, chỉ đổi selection actor, thêm trường bundle cấm. Đây là bằng chứng tái hiện lỗi, không phải PASS sản phẩm.
- F3 có giới hạn: probe thêm tên nguồn và giá trị IOC trong field tên `x_leaked_selected_evidence`; chưa chứng minh exporter hiện tại làm lộ câu evidence. Đủ chứng minh verifier bỏ qua field cấm; rework phải bổ sung marker evidence riêng để kiểm đúng câu evidence.
- Các tree HTTP/harness/producer sạch sau kiểm; Backend còn `portal_api/schemas.py` modified và hai file mới `ioc_lookup.py`, `tests/test_w02_ioc_api.py`, HEAD `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`. Leader không sửa code sản phẩm.
- Raw output: `leader-w02-harness-review-20261111/qa-reproduction.log`, `frontend-targeted.log`, `verified-state.json`; script kiểm được giữ cùng thư mục.

## Gói sửa Engineer — X01-INGEST-BROWSER-HARNESS F1–F3

Một CTI Engineer Sol medium trực tiếp; không giao bot/worker khác. Dùng lại nghiên cứu/brief hiện hành `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-BRIEF.md`, `PHONG-HOA-PARALLEL-EXECUTION-20261111.md`, báo cáo QA và source exact SHA; đây là sửa hợp đồng hậu kiểm đã chốt, không chọn kiến trúc mới.

- Working tree duy nhất được sửa: `<root>\cti-x01-ingest-browser-prep`, branch `feat/x01-ingest-browser-prep-20261111`, bắt đầu `970a130452eb69bae3cd3793eab5a527b3d382d5`.
- Đọc AGENTS/docs/PROGRESS/spec tại tree. Allowlist: `tools/local_integration/tests/run_ingest_browser_stix.py`, `tools/local_integration/tests/run_stix_e2e.py` nếu cần helper tương thích cũ, `tools/local_integration/tests/test_runner.py`, có thể thêm `tools/local_integration/tests/test_ingest_postcheck.py`, `tools/local_integration/runner.py` chỉ khi cần truyền expected actor/fixture marker, `tools/local_integration/README.md`, `docs/PROGRESS.md`. Không sửa importer/exporter/store/API/UI/lock/RUNS hay QA evidence.
- F1 HIGH: tính lại digest canonical của toàn envelope hiện tại, cùng quy tắc importer, so với seed và provenance; thay trường hợp lệ ngoài source hash phải bị từ chối. Reuse helper hiện có nếu phù hợp, không sửa importer chỉ để tiện test.
- F2 HIGH: expected actor phải xuất phát từ cấu hình phiên của harness, không lấy DB làm nguồn kỳ vọng. Xác minh actor ở draft/final audit và từng selection event; kiểm action/version/selection hash và chuỗi phiên bản theo thao tác dự kiến. Bắt cả đổi đồng bộ ba actor lẫn chỉ đổi selection actor. Giữ tương thích W05 helper cũ; không chỉ so số row.
- F3 MEDIUM: kiểm cấu trúc bundle theo các trường được phép của exporter/spec và kiểm marker riêng cho tên nguồn/raw text/evidence/creator/reviewer. IOC được chọn vẫn phải xuất hiện trong SCO hợp lệ; không coi chính IOC là marker evidence. Kiểm field thêm ở top-level và nested; nguồn synthetic dùng marker an toàn, không dữ liệu thật. Không tuyên bố exporter hiện đang leak.
- TDD RED trước sửa, GREEN sau sửa; baseline TXT/PDF offline và export vẫn đạt; ca lỗi không được viết DB. Chạy bộ test `tools/local_integration/tests` có liên quan (gồm lifecycle/EOF/timeout/cleanup), Ruff check/format cho file đổi, diff-check và scope. Không chạy full repo/web hoặc browser/listener demo. Loopback test sẵn có chỉ nếu cần, cleanup resource sở hữu.
- Giữ nguyên probe QA. Có thể gọi qua wrapper riêng để cấp thêm expected actor nếu chữ ký thay đổi, ghi rõ thay đổi; không biến TypeError do sai chữ ký thành bằng chứng chặn dữ liệu sai. Kiểm cả positive và mỗi mutation đi tới verifier mới.
- Report cập nhật `PHONG-HOA-X01-INGEST-BROWSER-HARNESS-RESULT.md`; evidence mới `x01-ingest-browser-harness-evidence/rework-f1-f3/`, không ghi đè log cũ. Trả exact base/HEAD, diff, commands/exit/count, raw RED/GREEN, manifest và tree sạch; commit local Conventional Commits.
- Chưa ghép importer F1, chưa mở browser hoặc claim tích hợp. Không push/PR/merge/cherry-pick/deploy, secret/cloud/model/OpenCTI/lab. Bước ghép trên tree tích hợp riêng chỉ sau nghiệm thu bản sửa này.

## Gói nối lại Backend — W02-LOOKUP-API-IMPLEMENT

Giữ nguyên `PHONG-HOA-W02-API-ADAPTER-DISPATCH-20261111.md` SHA256 `57ae0d0d77ba31504f1ed7a4b01ffb06170edcc85d272c09732525b263e3a690` và contract `PHONG-HOA-W02-API-CONTRACT-BRIEF.md`. Một Sol medium trực tiếp, cùng tree `cti-w02-lookup-api`, branch `feat/w02-lookup-api-20261111`, base `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.

Đọc lại ba file dở và log RED trước khi tiếp tục; không reset/recreate. Hoàn tất implementation/test/evidence đúng allowlist; chưa có kết quả API đạt. HTTP adapter đã nghiệm thu cục bộ tại SHA trên nhưng không đọc/sửa tree Frontend để chỉnh hợp đồng cho khớp. Giữ kiểm TLP, dữ liệu ẩn, auth server-side và W05 regression. Trả báo cáo/evidence như brief cũ. Nếu provider lại lỗi, báo đúng nguyên nhân và phần còn dở; không tự thay model hoặc tạo worker khác.

## Cổng nối và tự động hóa

W02 chỉ nối runtime khi API và HTTP adapter đều được nghiệm thu. X01 chỉ nối browser sau sửa hậu kiểm và ghép importer đã đạt trên tree riêng. Browser TXT/PDF/self-approve/fault scenarios, Cloudflare, OpenCTI, lab và production vẫn chưa xác minh.

Đã đọc lại hai lịch liên quan: lịch tiếp tục 30 phút còn bật, lần kế 18:56 giờ Việt Nam; lịch khi hạn mức khôi phục còn bật, lần kế 18/11 lúc 17:35 giờ Việt Nam. Lịch 30 phút trả nội dung bị cắt ở cuối; không tự sửa lịch. Mục tiêu dự án còn mở nên giữ cả hai, chưa có căn cứ coi tác vụ phục hồi khi hạn mức khôi phục đã hoàn thành.

Học thêm: digest canonical là dấu kiểm của JSON theo một cách biểu diễn cố định; actor audit là danh tính gắn với từng lần lưu/duyệt. Cả hai phải đối chiếu với dữ liệu kỳ vọng độc lập để tránh xác nhận nhầm.
