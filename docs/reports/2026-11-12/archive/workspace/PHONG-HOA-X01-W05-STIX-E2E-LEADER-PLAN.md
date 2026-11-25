# X01 → W05 → STIX: nghiệm thu nghiên cứu và quyết định triển khai của Leader

Ngày 11/11/2026. Trạng thái: **ACCEPTED nghiên cứu với các quyết định dưới đây; chưa có bằng chứng chạy toàn chuỗi mới**.

## Cơ sở đã đối chiếu
- Research: `PHONG-HOA-X01-W05-STIX-E2E-RESEARCH.md`, SHA256 `17C4227262264B01E305286AA1F9EAEDD81CA87176711079566AB62A567EA154`.
- Implementation brief: `PHONG-HOA-X01-W05-STIX-E2E-IMPLEMENTATION-BRIEF.md`, SHA256 `188D57719AB1295BEC0F61B6751AF307A370370170296DA90C9868930102160A`.
- Source `cti-w05-stix-offline`: Leader đọc mã và kiểm Git sạch tại `ed829a0344b2d3d4392fae933e41a9c44fdcd853`, nhánh `feat/w05-stix-offline-20261111`.
- Đã đối chiếu store CLI/core, extractor CLI, LocalRun start/close, HTTP selection matrix, exporter provenance. Source CLI chưa truyền creator; core đã hỗ trợ. Harness đang seed bằng library nên chưa chứng minh CLI chain.
- Tree `cti-x01-w05-stix-e2e` và nhánh `feat/x01-w05-stix-e2e-20261111` chưa tồn tại tại lượt kiểm. Worker phải kiểm lại trước tạo.
- Không chạy test implementation trong lượt review nghiên cứu. Không dùng báo cáo nghiên cứu làm bằng chứng test/integration.
- Đã xem các cuộc: không có Leader khác làm đồng thời. Lịch tiếp tục còn bật, chu kỳ 30 phút; không thay đổi lịch.

## Quyết định
Mục tiêu: một văn bản tổng hợp đi qua CLI extractor → CLI store → HTTP selection/approve → CLI STIX trong cùng run/draft/DB.

Chọn tái dùng LocalRun và các lệnh hiện có. Cách chỉ ghép fixture trong bộ nhớ không kiểm được ranh giới CLI; thêm browser/importer/framework lúc này mở rộng phạm vi mà chưa cần thiết. Lát cắt mới chỉ chứng minh **CLI + HTTP cục bộ**; browser cùng draft và OpenCTI vẫn chưa được kiểm.

Theo ủy quyền tiếp tục phát triển cục bộ của người dùng, giao Engineer/Sol medium triển khai trên tree mới. Quy định chờ xác nhận thay đổi nhiều file trong AGENTS.md không tạo lần xin phép mới cho phạm vi đã được giao. Không mở quyền phát hành, dữ liệu thật hoặc lab.

## Các điểm sửa/chốt thay thế phần mơ hồ trong brief
1. **Creator qua CLI là metadata do người vận hành cục bộ khai báo, không phải chứng minh danh tính.** Chỉ thêm option cho `save`, giữ stdout và hành vi không truyền option. Truyền nguyên giá trị cho core. Core hiện chỉ yêu cầu chuỗi có ký tự khác khoảng trắng, không có giới hạn độ dài; bỏ yêu cầu từ chối “quá dài” thiếu căn cứ trong brief, không tự thêm policy mới hoặc sửa core. Test chuỗi rỗng/whitespace bị từ chối trước DB I/O, giá trị hợp lệ được giữ nguyên. Argparse cung cấp chuỗi; không bịa ca CLI list/dict. HTTP vẫn chỉ lấy reviewer từ JWT đã kiểm; không nhận subject từ body.
2. **Input chính xác trên Windows:** ghi fixture bằng UTF-8 bytes với LF `\n`, không BOM. Extractor đọc text với chuyển newline chuẩn của Python; byte hash khớp trong fixture LF này, không suy thành tính bất biến byte cho mọi input CRLF. Kiểm Unicode bằng lát cắt code point thật; không sửa nội dung sau khi CLI tạo draft.
3. **Hai lệnh seed, một lệnh export ở giai đoạn sau.** Seed chạy extractor rồi store bằng argv list, `shell=False`, `sys.executable`, cwd tree mới, timeout hữu hạn, môi trường Python phù hợp. Store stdout phải parse đúng object id nguyên dương không bool và status pending; nonzero/timeout/malformed stdout thành lỗi an toàn. Không bỏ lọt stdout/stderr/exception chain chứa source, subject hay token.
4. **Đo bất biến đúng giai đoạn.** Source/draft/payload_json/items.keep giữ nguyên từ seed qua review. DB có thay đổi hợp lệ khi save selection và approve. Chụp baseline DB/sidecars riêng ngay trước pending export, và baseline mới sau approve ngay trước successful export; so trước/sau từng lần export, không so DB sau approve với DB pending. Đóng mọi handle SQLite đọc trước snapshot file; không checkpoint hoặc sửa journal mode chỉ để làm hash đạt.
5. **Thời hạn run:** dùng TTL 120 giây cho scenario/matrix mới thay ví dụ 30 giây; từng subprocess timeout 10 giây, HTTP có timeout. Export/kiểm artifact phải hoàn tất trước close. Không thêm cơ chế sleep chờ việc ngoài, không giữ listener để đợi callback.
6. **Cleanup là tiêu chí thực:** kiểm temp root thuộc run; ghi nhận process object/PID owned và API thread trước close; sau close process đã kết thúc, API thread dừng, không listener owned, temp root không tồn tại. Dùng phép kiểm listener có ý nghĩa, không diễn giải lỗi connect 10035 thành port đóng. Chỉ in PASS sau cleanup. Thêm test lỗi child/start và lỗi giữa HTTP/export để chứng minh context cleanup; lỗi cleanup phải làm lượt chạy thất bại. Không thay lifecycle single-use/retry-cleanup đã có.
7. **Bằng chứng:** lưu command/exit/count/hash và summary đã bỏ dữ liệu nhạy cảm; không chép raw source/draft/DB/bundle/JWT/private key/subject vào evidence. Command có subject tổng hợp phải thay giá trị bằng nhãn redacted khi ghi evidence, nói rõ sự thay thế. Giá trị synthetic trong test source được phép. Không chạy quét secret ngoài file mới và phạm vi task.
8. **Phạm vi triển khai:** bảy file trong implementation brief; cho phép tạo README tại `tools/local_integration/README.md` nếu chưa có. Không sửa dependency/lock/core/schema/API/UI/gateway/exporter hoặc bất cứ tree cũ nào. Nếu cần mở scope, báo lỗi cụ thể cho Leader. Không giao tiếp bot khác.

## Bàn giao và nghiệm thu
- Worktree: `$WORKSPACE/cti-x01-w05-stix-e2e`.
- Branch: `feat/x01-w05-stix-e2e-20261111`; exact base `ed829a0344b2d3d4392fae933e41a9c44fdcd853`.
- Báo cáo mới: `PHONG-HOA-X01-W05-STIX-E2E-RESULT.md` tại workspace Leader.
- Evidence mới: `x01-w05-stix-e2e-evidence/` tại workspace Leader; manifest SHA256, RED/GREEN, exact Git refs/diff, exit và counts thực. Không sửa evidence/review/acceptance cũ hay RUNS.
- Test phải RED trước code rồi GREEN. Chạy store CLI + runner + STIX export CLI targeted; ma trận CLI+HTTP mới; regression selection matrix; Ruff check/format và git diff --check. Không lặp full500/UI/build/browser khi không có thay đổi liên quan.
- Chỉ commit cục bộ, clean tree; không push/PR/merge/deploy. Leader kiểm diff và focused evidence sau callback.
- Giới hạn giữ nguyên: browser cùng draft, OpenCTI import/workbench, danh tính tổ chức thật, Cloudflare/HTTPS/JWKS thật, chất lượng model/dataset, network share/crash/lab/production chưa xác minh. Dự án vẫn active.

## Giải thích ngắn
CLI là lệnh chạy thành chương trình riêng; kiểm qua CLI bắt được lỗi truyền tham số mà gọi library có thể bỏ sót. Hash là dấu kiểm nội dung file; phải so đúng khoảng thời gian không có thay đổi hợp lệ. Cùng run nghĩa mọi bước sử dụng đúng một bản nháp và một DB trước khi dọn tài nguyên.
