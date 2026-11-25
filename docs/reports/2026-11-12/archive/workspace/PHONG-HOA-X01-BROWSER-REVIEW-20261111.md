# X01 browser — review và phần còn thiếu, 11/11/2026

Root: `$WORKSPACE`.

## Kết luận

**Chấp nhận bằng chứng các luồng đã chạy tại `5fd527fc5d9b113ac2725a855f3ac75c9b106762`; chưa đóng X01-INGEST-BROWSER-INTEGRATION vì thiếu phục hồi sau 503.** Không phát hiện lỗi dữ liệu qua các phép kiểm bổ sung dưới đây.

- Tree sạch; diff so importer `fc08897a` đúng sáu file allowlist, +1517/-10, diff-check exit 0. Importer/harness/producer/W05 đúng SHA và sạch.
- Manifest JSON `x01-ingest-browser-integration-evidence/manifest.json`: 14/14 size/hash khớp; SHA256 `dc6c41b18fdbd13b371fe9b03e2fd29509fe7ad91985d8ab71f7c26ca801dacd`.
- Leader đọc diff mới so harness `16e6f889`, xem năm ảnh và log tương ứng: TXT 56857, PDF 59480, tự duyệt 57352, save-refresh 63957, decision-refresh 50179. TXT/PDF có trạng thái duyệt và số event đúng; ảnh tự duyệt có thông báo không đủ quyền. Các ảnh fault cho thấy lỗi tải lại còn tồn tại. Đây là đối chiếu evidence browser của Engineer, không phải Leader chạy lại browser.
- Leader chạy targeted suite mới trên đúng target: `28 passed, 21 deselected`, exit 0 (postcheck, browser case plan, PDF orchestration, signal). Không chạy lặp 561 test.
- Probe Leader độc lập kiểm hai trạng thái self-approve/save-refresh: baseline đều PASS; sửa `payload_json.items[0].keep` trái phép đều bị từ chối bởi kiểm provenance. `false_passes=[]`, exit 0. Nghi ngờ verifier bỏ qua payload đã được bác bỏ bằng phép thử, không giao sửa điều này.
- 49 targeted và 561 full-repo là log Engineer cung cấp; manifest đã kiểm. Brief trước không yêu cầu chạy lại toàn repo; lần sửa tiếp không lặp suite này nếu không có lỗi/phạm vi mới. RED TDD và offline TXT/PDF được mô tả trong RESULT nhưng không có raw riêng trong manifest: không nâng thành chứng cứ độc lập đã lưu.
- Cleanup của năm browser run có log listener count 0/process count 0/junction false; LocalRun đã được kiểm vòng đời từ trước. Không lấy socket OSError chung làm bằng chứng.
- Báo cáo thực nằm ở `x01-ingest-browser-integration-evidence/RESULT.md`, chưa có tên root đã yêu cầu. Không thất lạc; cần tạo báo cáo root ở lần trả tiếp để người khác tìm đúng chỗ.

W02 docs `aeff542a20ecc6fe436a0884801fdd69ab0435f6` đã được lượt Leader lúc 20:00 nghiệm thu: 2 file docs, 19/19 hash, module/executable resolve. Đã đọc biên bản và đối chiếu trạng thái sổ; không chạy lại hoặc giao lại.

## R1 — thiếu bằng chứng phục hồi tải lại (mức trung bình, cổng nghiệm thu)

Kế hoạch `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-BRIEF.md`, ma trận 8 ca, yêu cầu lỗi sau save/approve và bấm Thử lại phục hồi. Hiện `gateway.mjs:88` trả 503 vĩnh viễn sau POST thành công khi bật `failRefreshAfterPost`. RESULT cũng xác nhận retry vẫn lỗi. Đã chứng minh không ghi lặp trong lỗi kéo dài, **chưa chứng minh GET trở lại 200, UI tải đúng lựa chọn/quyết định đã ghi trên cùng DB**. Đây là khoảng trống kiểm thử, không kết luận tính năng phục hồi đang lỗi.

## Rework Engineer — chỉ hoàn tất R1 và báo cáo

Một Sol medium trực tiếp, không giao bot khác. Cùng thread `ab20d277-269e-41c7-9a05-ab1381c0de68`, target `cti-x01-ingest-browser-integration`, branch `feat/x01-ingest-browser-integration-20261111`, base hiện tại `5fd527fc5d9b113ac2725a855f3ac75c9b106762`. Các source chỉ đọc giữ nguyên. Đọc AGENTS/PROGRESS/spec và tài liệu này; tái sử dụng gateway fault/LocalRun/UI hiện có, không thiết kế runner khác.

1. Thêm cách gây lỗi tạm thời có giới hạn cho gateway demo, giữ nguyên chế độ lỗi kéo dài cũ. Có thể dùng số GET lỗi hữu hạn sau POST thành công (ví dụ hai GET detail/list), cấu hình chỉ ở local runner. Không thêm API điều khiển lỗi công khai, không đổi API/UI/importer/store/exporter. RED trước GREEN; kiểm mode cũ vẫn giữ hành vi, mode mới fault rồi forward lại đúng upstream, không ảnh hưởng auth/allowlist.
2. Chạy đúng hai browser run mới trên trình duyệt tích hợp OpenMausBot, loopback TTL<=300 mỗi run. Cùng DB/port/draft suốt run; không seed lại/reset DB để tạo trạng thái phục hồi. Save: bỏ IOC đầu, lưu, quan sát 503; một lần tải lại thành công, UI vẫn chỉ chọn IOC thứ hai; sau đó duyệt và xuất STIX. Decision: dùng selection đã seed, duyệt, quan sát 503; tải lại thành công và UI hiển thị đã duyệt, không còn hàng pending tương ứng; xuất STIX.
3. Ghi chứng cứ request hữu hạn không chứa token/header/body: POST save/approve đúng số mong đợi, GET lỗi rồi GET 200, không POST do nút retry. Đối chiếu selection audit=1, decision audit=1 cuối mỗi run, payload/source/provenance/hash và DB export read-only. Kỳ vọng lấy từ cấu hình ca, không từ kết quả quan sát. Giữ các kiểm F1/F2/F3 trước đây.
4. Allowlist bổ sung cụ thể `tools/local_integration/gateway.mjs` và file test gateway hiện có; cộng allowlist cũ runner.py, tests/run_ingest_browser_stix.py, tests/run_stix_e2e.py, tests/test_runner.py, README.md, docs/PROGRESS.md. Giữ thay đổi nhỏ. Không sửa source tree hoặc các mảng sản phẩm khác.
5. Chỉ chạy test gateway/runner liên quan + probe hậu kiểm phù hợp và Ruff/format/diff. Không lặp full561/W02/webbuild nếu code/artefact UI không đổi. Giữ evidence cũ; log mới vào `x01-ingest-browser-integration-evidence/rework-recovery/`, manifest mới riêng. Dùng Python có thật, ghi executable/cwd/module/exit/count; browser ảnh/log phải khớp từng run.
6. Tạo `<root>\PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-RESULT.md` nêu cả phạm vi đã đạt và R1 mới, dẫn RESULT lịch sử. Trả local commit sạch, exact diff, raw RED/GREEN mới, browser recovery/request counts và cleanup listener/process/thread/temp thuộc run.

Chỉ Engineer dùng browser đợt này. Không thêm thành viên hay giao Frontend/Backend việc không phụ thuộc trực tiếp. Không cloud/LLM/OpenCTI/lab/push/PR/merge/deploy, không cài/sửa môi trường dùng chung.

## Bằng chứng Leader và giới hạn

`leader-x01-browser-review-20261111/`: verified-artifacts.json, targeted-tests.log, verify.py, review-probe-final.log. Hai lần probe đầu lỗi do import path và SQLite connection của chính probe; đã sửa và giữ log cũ, không gán thành lỗi sản phẩm. Lệnh dọn thư mục tạm `$USER_HOME\AppData\Local\Temp\leader-x01-db-gma1sgpe` bị kiểm duyệt tự động chặn với lý do chung `blocked by policy`; không xóa bằng cách khác. Thư mục thử nghiệm này được giữ lại; không liên quan cleanup năm browser run của Engineer.

Hai automation Phong Hỏa còn enabled, đã đọc trạng thái; dự án active. OpenCTI/Cloudflare/JWKS/HTTPS thật, dữ liệu thật/model/lab/production và clipboard vẫn UNVERIFIED. R1 được giao sửa, không tuyên bố hoàn thành toàn tích hợp.
