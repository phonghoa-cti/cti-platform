# W03 Backend — sửa B1/B2 sau QA, 12/11/2026

ROOT = $WORKSPACE

Một CTI Backend Sol medium trực tiếp, không worker con/bot khác. Cùng tree ROOT\cti-w03-read-backend, branch feat/w03-read-backend-20261112; candidate a49486caf39942019259e41514457bdb85498347. Giữ sửa đổi có trước, không reset hoặc thay tree. Frontend đang sửa độc lập, không chạm tree đó.

## Căn cứ đã kiểm

Đọc hợp đồng r1 trong ROOT\PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md, AGENTS/PROGRESS tại candidate và ROOT\PHONG-HOA-W03-BACKEND-QA-RESULT.md. Tái dùng nghiên cứu đã chốt, không nghiên cứu/feed/live mới.

Leader đã đọc source và chạy nguyên probe QA ngoài source trên đúng candidate: **3 failed, 0 passed, exit1**, gồm một DB schema lỗi và hai URL authority lỗi; tất cả actual200 thay expected503/cves_unavailable. HEAD trước/sau đúng, status sạch. Raw: ROOT\leader-w03-backend-review-20261112\probe-run.log và probe-results.xml. Đây là nghiệm thu kết quả QA, **Backend FAIL**, chưa tích hợp.

Probe gốc phải giữ nguyên:
`$THREADS\4431b864-0d00-4d10-93c9-a10bcad43317\w03-backend-qa-evidence\test_w03_backend_qa_probes.py`.

## B1 — schema SQLite phải được kiểm trong snapshot chỉ đọc

ReadOnlyTechnologyStore hiện gọi list kế thừa chỉ SELECT rows, bỏ _validate_schema; DB mất audit/migration/index vẫn200. Trên **cùng kết nối mode=ro và cùng read transaction**, kiểm schema bằng validator hiện có, rồi đọc bounded MAX_TECHNOLOGIES+1 và validate rows đầy đủ. Dùng transaction đọc, không BEGIN IMMEDIATE, initialize, migrate, seed hay sửa TechnologyStore chung. Lỗi trả503 cves_unavailable, không partial.

Không chỉ sửa cho probe gộp xanh: test thiếu audit, thiếu marker, thiếu index từng cái; marker version/schema sai; DB valid200; missing DB503 không tạo file. Chứng minh validation và data read dùng cùng connection/transaction, tránh check một connection rồi SELECT connection khác. Đối chiếu schema/rows/audit/version trước-sau trên DB test; với schema bị thiếu, đọc những đối tượng còn tồn tại. Không dùng file-byte equality làm bằng chứng duy nhất trong trường hợp WAL.

## B2 — advisory_url phải có HTTPS authority hợp lệ

Hai input đã tái hiện: `https://:443/advisory` và `https:// example.invalid/advisory`. Cả dataset phải503. Validate hostname thực và port trong try/except, từ chối host rỗng, whitespace/control/backslash và authority malformed; giữ cấm credentials. Bắt ValueError từ urlsplit/hostname/port đúng lớp lỗi.

Thêm regression hai case gốc và các cạnh liên quan: port không phải số/vượt range, bracket IPv6 lỗi, whitespace/escaped authority gây diễn giải khác. Giữ control URL HTTPS thông thường, explicit valid port và IPv6 hợp lệ nếu parser đang hỗ trợ. Không áp chính sách hostname mới như chỉ domain công khai hoặc DNS lookup; đây là kiểm cú pháp local, không truy cập URL, không SSRF test/live network. Không normalize/sửa link lỗi âm thầm hoặc nới hợp đồng cho test xanh.

## Phạm vi và kiểm

Allowed: portal_api/cves.py, portal_api/tests/test_cves_api.py, docs/PROGRESS.md một đoạn, docs/specs/W03-read-local-contract.md chỉ làm rõ bản sửa. Không sửa app.py/auth/technologies/core/frontend/tools/deps/brief/ledger nếu không có nhu cầu cụ thể đã báo Leader.

RED→GREEN regressions mới trước sửa; chạy nguyên3probe QA, focused W03, Ruff check/format/diff-check. Không lặp toàn345 vì không đổi app/auth/shared store. Nếu phát hiện ảnh hưởng rộng thì nêu lý do kiểm bổ sung. Dùng .venv của candidate và PYTHONPATH đúng cây; giữ source path/command/exit/count. Không sửa probe gốc.

Ví dụ chạy probe ở cwd candidate: `.venv\Scripts\python.exe -X utf8 -B -m pytest -c pytest.ini --rootdir . -o addopts='' -p no:cacheprovider <probe-path> -q`, PYTHONPATH=candidate;candidate\core.

Output ROOT\PHONG-HOA-W03-BACKEND-REWORK-RESULT.md và ROOT\w03-backend-rework-evidence\ gồm RED/GREEN, test/lint output, hash probe trước/sau, non-mutation proof, SHA commit sạch và delta so candidate. Phân biệt hai finding đóng với kiểm toàn luồng. Không browser/gateway/feed/OpenCTI/LLM/lab/push/PR/merge/deploy/secret hoặc đổi quyền.

Sau trả kết quả Leader kiểm phần mới/rủi ro; chỉ tích hợp khi cả Backend và Frontend accepted.
