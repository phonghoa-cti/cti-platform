# W03-READ-BACKEND-QA — kiểm độc lập phần Backend

ROOT = $WORKSPACE
OUT = $THREADS\4431b864-0d00-4d10-93c9-a10bcad43317
Owner: CTI QA Security, Sol medium tự kiểm, không worker con.
Source chỉ đọc ROOT\cti-w03-read-backend; branch feat/w03-read-backend-20261112.
Base 273196e2d23b36172d57cc61b289522786d61b2a; candidate a49486caf39942019259e41514457bdb85498347.
Đây là việc mới kiểm Backend, không chạy lại QA Frontend vừa trả. Frontend đang sửa F1–F3 trong tree riêng; không đọc/sửa tree Frontend đang hoạt động.

Đọc AGENTS/PROGRESS/spec đúng candidate, ROOT\PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md (r1 ưu tiên DTO lịch sử), ROOT\PHONG-HOA-W03-BACKEND-RESULT.md và ROOT\w03-backend-evidence\r1-final.log. Tái dùng nghiên cứu nguồn có trong brief, không mở phạm vi nguồn thật. Leader đã kiểm HEAD/status sạch; 41 focused/230 regression/345 all là nhật ký worker, chưa bằng chứng độc lập.

## Kiểm theo rủi ro
- Auth/query precedence và role detail/mixed/leader summary. Leader asset_id bị chặn trước dependencies; lỗi/envelope/cursor không chứa metadata tài sản. notice đúng literal r1. Không giả test adapter thành JWT/Cloudflare thật.
- Dataset/snapshot strict và fail-closed: bool/NaN/null, ngày/fraction, duplicate CVE/product, bounds, Unicode normalization theo W04; toàn dataset phải được validate kể cả không match. Không tự suy thiếu KEV là false.
- Cursor canonical/context/snapshot/after: replay cùng dữ liệu không bỏ/lặp; thay technology/fixture thì409; invalid/mismatched role không tăng quyền; null vs0/rank đúng. UTF8 response cap, query cap/unknown/duplicate validation trước dependency.
- SQLite chỉ đọc thực sự: missing path không tạo file, corrupt schema/row/invalid timestamp fail; không initialize/migrate/seed. Đối chiếu DB trước/sau cả success và error bằng SQLite queries (DB test riêng OUT), không sửa DB thực.
- Kiểm tính khớp năm wire fixtures với actual API response và contract r1, headers no-store/Vary trên errors. Không cần parser/frontend mới vì đang có writer khác.
Ưu tiên source review + probes cho khoảng trống, không viết lại các test đã đủ. Có thể chạy focused41 làm baseline; không lặp all345/build. Test mới chỉ OUT\w03-backend-qa-evidence hoặc sandbox riêng trong OUT. Dùng Python .venv của đúng source nếu có hoặc ROOT\cti-platform-start\.venv\Scripts\python.exe với cwd/PYTHONPATH đúng candidate; báo module.__file__, tránh chạy nhầm cây. Source/HEAD/index/branch và dependency không thay đổi; giữ cache/temp ngoài source nếu có thể.

Output: OUT\PHONG-HOA-W03-BACKEND-QA-RESULT.md; probes, logs, manifest hashes ở OUT\w03-backend-qa-evidence.
Mỗi finding: mức độ, file:line, expected/actual, input tái hiện, exit/count, tác động, sửa tối thiểu. PASS chỉ phạm vi đã kiểm; liệt kê việc cố ý bỏ qua. Verify Git HEAD/status/diff-check trước/sau.
Không fix sản phẩm, sửa ledger, dùng browser/live feeds/LLM/secrets/lab, push/PR/merge/deploy hoặc thay quyền. Không thử lại cùng lỗi quá hai lần. Leader kiểm kết quả rồi giao rework nếu cần; tích hợp chờ cả hai input accepted.
