# W03-S1 Backend — sửa B1/B2

ROOT = `$WORKSPACE`.

Tiếp tục cùng tree `ROOT/cti-w03-status-backend`, thread `93a366c6-3c4c-4bb7-8b6c-9c7801aa0c3a`, candidate `b8957e63acc7497ba835e06c05e52f4b16ef136c`. Một Sol medium trực tiếp, không worker/bot con. Giữ edits nếu xuất hiện, không reset/tạo writer mới. Đọc `ROOT/leader-w03-status-review-20261112/REVIEW.md`, raw log/probe và brief S1 gốc. Allowlist và contract gốc giữ nguyên.

## Sửa cụ thể

1. **B1:** validate toàn bộ body/path/query/cursor syntax trước configured dependencies/port/DB, sau auth/role/Origin/media đúng thứ tự. Expected technology/status version phải type int chính xác, trong JS-safe range; không bool/float dù bằng1, kiểm đầy đủ status/note/dataset string. Note sai phải422 ngay cả nguồn/DB không dùng được. Không gọi port/DB và không ghi cho request sai. Không thay precedence409 của context so với status.
2. **B2:** timestamp của persisted status/audit phải là ngày UTC có thật, đúng wire fraction1..6 hoặc không fraction. Dữ liệu lưu invalid status/note/context/time phải503 status_unavailable, không chuyển thành422 client error. Bind saved context và audit before/after với technology_id/cve_id/vendor_key/product_key của row/relation được chọn; kiểm nhất quán event/version trước/after trong phạm vi record được đọc. Cho phép snapshot technology version/dataset cũ hợp lệ và báo review_required; không nhầm đó với corruption. Validate persisted data trước bất cứ DML và serialize/validate response trước commit. GET, PUT bị chặn và history lỗi giữ nguyên schema/rows/version/audit.

Không sửa `technologies.py`, `cves.py`, auth/shared/frontend/gateway/dependency. Có thể tái dùng helper hiện có hoặc helper riêng trong cves_status*.py. Không thêm network/migration trong request. Không tự mở rộng S2.

## Kiểm và bàn giao

- Giữ nguyên 8 probe Leader tại `ROOT/leader-w03-status-review-20261112/test_backend_probes.py` (hash manifest), làm GREEN cả8. Leader đã chạy baseline14PASS +8FAIL; không cần diễn lại RED y hệt trước sửa. Thêm regression vào source cho các nhánh còn lại cùng nguyên nhân: numeric/string/null bounds, malformed request trước dependency, status/history invalid persisted field và relation, valid UTC leap-day/fraction, review_required snapshot cũ hợp lệ.
- Chứng minh non-mutation bằng SQL snapshot khi reject, đặc biệt PUT gặp record hỏng. Giữ valid controls và transaction/concurrency tests cũ. Focused status + phần app/W03/W04 liên quan, Ruff check/format/diff-check. Không lặp full377 khi không đổi shared rộng.
- Chạy probe bằng venv `ROOT/cti-w03-read-backend/.venv/Scripts/python.exe` từ status backend (tree này không có venv); command trong REVIEW.md. Không sửa probe/helper test để né assertion; nếu helper cần đổi API nội bộ, giữ compatibility cho probe và giải thích.
- Commit sạch, báo base/candidate/final SHA, diff allowlist, command/exit/count, hash probe không đổi. Cập nhật `ROOT/PHONG-HOA-W03-STATUS-BACKEND-RESULT.md`; thêm `ROOT/PHONG-HOA-W03-STATUS-BACKEND-REWORK-RESULT.md`, evidence mới `ROOT/w03-status-backend-rework-evidence/` với log GREEN/manifest. Giữ evidence RED cũ. Wire phải vẫn khớp contract; nếu file wire thay hợp lệ cập nhật provenance/hash.
- Không chạm RUNS/brief/Leader evidence/Frontend tree. Không push/PR/merge/deploy/browser/live feed/lab. Chưa coi input hoặc toàn W03 đạt cho đến review lại.
