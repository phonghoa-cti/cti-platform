# Leader kiểm rework W04, 11/11/2026

**Kết luận: CHƯA NGHIỆM THU Backend.** F1–F3 và các probe cũ đạt; F4 còn phân loại nhầm UNIQUE của bảng khác. Đây là kiểm cục bộ/in-process, không có browser/listener/lab.

- Base `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`; HEAD `5316422ef6091f48edca443f886358a4475d8e04`, tree sạch. Delta đúng phạm vi: 4 file, +387/-44.
- Đã đọc implementation/test diff và schema liên quan, không sửa sản phẩm. Dùng lại nghiên cứu W04 và yêu cầu F1–F4 hiện hành; không review lại kết quả nghiên cứu đã nghiệm thu.
- Chạy `python -m pytest portal_api/tests/test_assets_api.py portal_api/tests/test_w02_ioc_api.py -q` trong target: exit 0, 99 dấu PASS (72 + 27; chế độ quiet không in dòng tổng). Raw `assets-w02-tests.txt`. Interpreter từ `cti-w02-lookup-api/.venv`, module từ target theo `module-paths.txt`.
- Chạy nguyên `w04-assets-qa-evidence/targeted_probes.py`: exit 0, đọc actual so với expected: 7/7 đúng. SHA256 `6597F542EEB0BC96651B068CD68E7C0BF5B4CDC83AC51D7CA39D95455C06C0B5`. Raw `probe-results.json`, trạng thái Git/exit tại `verification.json`.
- F1: domain DB hỏng trả 503 lookup_unavailable, adapter 0 call. F2: subject 513 trả 422, asset/audit 0/0. F3: tên 129 trả 200 found. Audit RAISE(ABORT) cũ trả 503 và rollback 0/0; concurrent writer/Origin/private-IP/overflow giữ đúng.
- Phát hiện F4 còn thiếu khi đọc classifier: UNIQUE của bảng khác + canonical có sẵn bị coi là duplicate asset. Probe store tại `unrelated-unique-probe.json`; probe API độc lập `f4_unrelated_unique_probe.py` trả 2 FAIL, exit 1, raw `f4-http-results.json`. POST/PUT thực tế 409 asset_exists thay vì 503 assets_unavailable; cả hai giữ row/audit 1/1 và asset không đổi.
- Chỉ định sửa tiếp trong `PHONG-HOA-W04-BACKEND-F4-REWORK-20261111.md`, giữ owner/thread/tree; Frontend hiện running, giữ request cũ. Chưa tích hợp candidate này.
- Hai lịch nối việc Phong Hỏa đã được đọc: vẫn enabled; mục tiêu chưa đạt nên giữ nguyên. Lịch 30 phút có phần cuối instructions bị dịch vụ cắt khi đọc; phần điều kiện tiếp tục/dừng hiện đầy đủ trong quy trình cục bộ. Không suy ra hoạt động worker từ lịch.

UNVERIFIED: Frontend W04/browser, tích hợp cùng DB, Cloudflare/JWKS thật, OpenCTI, lab/production. Không push/merge/deploy.
