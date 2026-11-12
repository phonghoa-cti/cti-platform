# Phong Hỏa — nghiệm thu hậu kiểm và nối tích hợp, 11/11/2026

## Kết luận và bằng chứng Leader

Root: `$WORKSPACE`.

- **PASS hậu kiểm ngoại tuyến** tại `cti-x01-ingest-browser-prep@16e6f889b4e8cd2e3bd1fa7147c81106cf6a328c`. Tree sạch; manifest mới khớp 21/21. Leader chạy probe giữ nguyên QA gốc: baseline nhận, bốn mutation cũ bị từ chối; hai mutation F3 semantic mới đều bị từ chối bằng RuntimeError đúng lý do, `false_passes=[]`, exit 0. Đóng F1/F2/F3; chưa chứng minh browser tích hợp importer.
- **PASS chức năng W02 cục bộ, còn sửa tài liệu tái chạy** tại `cti-w02-local-integration@50277102bbcfd0c011c1e162569b2c4fe4560189`. Tree sạch; manifest khớp 15/15. Bốn Git blob API trùng source `78b026003c86985c7f062986088bfd1f7210a1b1`. Leader đọc diff, xem ảnh found với điểm/nguồn/nhãn synthetic, chạy lại HTTP matrix: **37 checks, exit 0**; ba trạng thái, ba nhóm quyền, 401/403/422/503, chống giả quyền và bất biến dữ liệu ẩn đạt.
- Browser found có ảnh được Leader xem; các trạng thái browser khác có ghi chép của Frontend. Không gọi đó là Leader chạy lại toàn browser. Clipboard browser vẫn UNVERIFIED. Các số regression 178 API/25 runner/10 gateway/178 web cùng build/lint là log Frontend đã đối chiếu manifest; không chạy lặp toàn bộ.
- Lệnh report/README dùng `.venv` không có ở target và direct script thiếu module path. Lần thử bằng môi trường Backend thất bại do thiếu uvicorn; đây là lỗi tái chạy, không giấu trong PASS. Lệnh Leader chạy thành công từ target: `..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w02_matrix`.
- Cleanup HTTP matrix trả true; đã đối chiếu `LocalRun.close` quản lý process/thread/temp và phát lỗi khi dọn không xong. Không lấy mọi socket OSError trên Windows làm bằng chứng cổng đã đóng.

Bằng chứng mới, ngoài source: `leader-integration-review-20261111/verified-artifacts.json`, `postcheck-probe.log`, `w02-http-matrix-run.log`. Giữ log thử thất bại `w02-http-matrix.log`. Các kết quả đã nghiệm thu ở lượt trước giữ nguyên, không giao lại vì callback cũ được gửi lại.

## Chia việc

Một Sol medium trực tiếp mỗi đầu việc, không giao bot con. Hai tree riêng; **chỉ Engineer dùng browser lượt này**. Frontend sửa tài liệu, không chạy listener/browser. Không cần thành viên mới.

### Frontend — sửa hướng dẫn tái chạy W02

Tiếp tục cùng tree/branch/HEAD `cti-w02-local-integration@50277102bbcfd0c011c1e162569b2c4fe4560189`, cùng thread hiện tại. Đọc AGENTS/PROGRESS trên tree; đây là rework cụ thể của kết quả vừa trả.

1. Sửa `tools/local_integration/README.md`: lệnh W02 dùng `-m tools.local_integration.tests.run_w02_matrix`, nêu cwd; giải thích môi trường cần có và đường dẫn Python thực sự đã dùng. Không tạo môi trường giả định, cài dependency hoặc sửa shared venv.
2. Sửa `PHONG-HOA-W02-LOCAL-INTEGRATION-RESULT.md`: phân biệt lệnh mẫu với lệnh thực chạy; thay các đường dẫn `.venv` không tồn tại bằng đúng executable từ evidence. Ghi rõ fallback integration env có uvicorn; giữ lỗi đã gặp và lần chạy thành công, không gán exit 0 cho lệnh chưa chạy. Dùng raw log Leader làm bằng chứng tái chạy mới, không cần chạy matrix thêm.
3. Đối chiếu các run browser theo port/thời gian/artifact: report có 64139/54331/62630, lời trả cuối nhắc 52341. Chỉ gắn kết quả với run có evidence; phần thiếu ghi chưa có evidence. Giữ clipboard UNVERIFIED, không sửa kết quả thực tế.
4. Allowlist trong tree chỉ README trên và `docs/PROGRESS.md`; report ngoài tree và evidence mới tại `w02-local-integration-evidence/rework-docs/`. Giữ nguyên evidence cũ, tạo manifest riêng. Không sửa mã/fixtures/lock, không browser/listener. Kiểm lệnh tài liệu và đường dẫn đọc được, `git diff --check`, diff đúng allowlist, commit docs sạch; không chạy lại toàn test/build.

### Engineer — X01-INGEST-BROWSER-INTEGRATION

Lát cắt đã được chuẩn bị trong `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-BRIEF.md`; các SHA/điểm làm rõ dưới thay placeholder cũ. Tái sử dụng nghiên cứu, LocalRun, fault gateway và ma trận 8 ca hiện có; không nghiên cứu/viết lại kiến trúc.

- Target mới: `<root>\cti-x01-ingest-browser-integration`, branch `feat/x01-ingest-browser-integration-20261111`, base importer `fc08897a240d9e55198b1a8166b21e8e7caf7213` từ `<root>\cti-x01-ingest-queue`.
- Harness source chỉ đọc: `<root>\cti-x01-ingest-browser-prep@16e6f889b4e8cd2e3bd1fa7147c81106cf6a328c`. Producer chỉ đọc `<root>\cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`. W05 source `<root>\cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Trước sửa, kiểm target chưa có writer, các source sạch/đúng SHA, đọc AGENTS/PROGRESS/spec liên quan. Mang đúng delta `db36ec01b765dfd515c1d0ef13642a693b777172..16e6f889b4e8cd2e3bd1fa7147c81106cf6a328c` của **năm file tools/local_integration** dưới đây sang target bằng local patch có kiểm tra; không merge/cherry-pick/reset. PROGRESS cập nhật riêng, không đè importer progress.
- Allowlist: `tools/local_integration/runner.py`, `tests/run_ingest_browser_stix.py`, `tests/run_stix_e2e.py`, `tests/test_runner.py`, `README.md` (các tests/README trong tools/local_integration); `docs/PROGRESS.md`. Không sửa portal, API, importer, store, exporter, producer, dependency/lock, RUNS hay tài liệu Leader. Nếu cần ngoài allowlist, trả finding cụ thể thay vì mở rộng.
- Giữ verifier F1/F2/F3 đã nghiệm thu. Mở rộng browser-session cho PDF và các ca fault/denied; TDD cho hành vi mới. PDF fixture chỉ một IOC eligible: có thể lưu rỗng rồi phục hồi/lưu IOC đó, expected selection events `((), eligible)` và approve; không bịa IOC thứ hai. TXT bỏ IOC đầu, giữ thứ hai. Kỳ vọng actor/selection/audit phải do cấu hình ca xác định độc lập, không lấy kết quả thực để làm expected.
- Chạy trên cùng DB của mỗi run: TXT/PDF input→envelope→importer→UI lưu/reload/duyệt→STIX; duplicate không tăng counts; tự duyệt 403 và DB bất biến; 503 sau save/approve cho UI retry GET-only, một event mỗi hành động thành công. Không dùng HTTP thay browser cho các hành động đang tuyên bố đã kiểm UI. Self-approve denied không có final audit/export.
- Chỉ trình duyệt tích hợp OpenMausBot; loopback với TTL tối đa 300 giây mỗi run; stdin tiếp tục đúng process và thu exit thật. Không Playwright/browser tự khởi chạy/điều khiển màn hình host. Nếu surface không dùng được, báo đúng phần chưa chạy, giữ bằng chứng và cleanup.
- Dùng executable Python có thật và dependency sẵn có, cwd/module target rõ ràng. Có thể dùng integration env hiện có chỉ đọc; không pip sửa env chung. Cache web chỉ copy vào target ignored nếu cần. Build chỉ khi browser cần artifact mới. Kiểm runner/scenario mới, các probe hậu kiểm nguyên trạng, TXT/PDF offline, Ruff/format/diff; không chạy full repo 553 test hoặc bộ W02 không thay đổi.
- Cleanup chỉ process/thread/temp/cổng do run sở hữu; xác nhận chúng kết thúc/xóa thật. Socket OSError chung (đặc biệt Windows 10035) không đủ. Lưu URL/port/run-id/ảnh và summary cùng lượt; không lộ token hoặc raw source vào summary.
- Output: `<root>\PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-RESULT.md`, `<root>\x01-ingest-browser-integration-evidence\`, manifest; exact SHA/diff/commands/executable/cwd/exit/count, browser step/ảnh và cleanup, phần UNVERIFIED. Local commit sạch, source nguyên vẹn. Không push/PR/merge/deploy/cloud/model/OpenCTI/lab.

## Điều phối và giới hạn

Đã kiểm các cuộc mở: Leader khác và worker cũ đều idle; current Leader là lượt duy nhất xử lý. Receipt được ghi sau khi giao thành công trong RUNS và `leader-integration-review-20261111/dispatch-receipts.json`; tài liệu này tự nó không chứng minh đã giao.

Dự án vẫn active. Giữ hai lịch nối việc hiện có; không tạm dừng khi chỉ xong một lát cắt. OpenCTI, Cloudflare/JWKS/HTTPS thật, model/lab/production và clipboard browser chưa được xác minh.
