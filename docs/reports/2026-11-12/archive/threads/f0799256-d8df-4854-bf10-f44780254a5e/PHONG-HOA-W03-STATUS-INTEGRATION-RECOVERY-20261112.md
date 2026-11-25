# W03-STATUS-INTEGRATION — phục hồi phần kiểm còn thiếu

Ngày 12/11/2026. Đây là tiếp tục cùng task, không mở tính năng mới.

## Trạng thái Leader đã đọc trực tiếp

- Lúc kiểm, các lượt Leader khác và thread Engineer `b05471df-3a0c-49c0-b02b-4019e1cf15d4` đều idle. Lượt Leader trước bị dừng ở giới hạn 15 phút.
- Receipt cũ: `e392c56c-eed3-4452-9ca9-ec88f4a6cf2c`. Công cụ không cho cuộc hiện tại đọc trạng thái receipt do cuộc trước gửi; không suy lỗi đó thành worker thất bại. Không có báo cáo kết quả tại đường dẫn đã giao; chỉ có bộ bằng chứng browser ban đầu.
- Tree: `$WORKSPACE/cti-w03-status-integration`.
- HEAD `5ee40dc9b9e96be9cfd7457c1a9151cc1b8c33b1`. Ba cherry-pick UI đã có trong log: `57c1dc1`, `0241b29`, `5ee40dc`; không cherry-pick lại.
- Hai tệp chưa commit: `tools/local_integration/w04_browser_helper.py` và `tools/local_integration/tests/test_w04_browser_helper.py`, 36 dòng thêm/1 dòng xóa. Nội dung thêm ba scenario và đếm status/audit trong snapshot. Giữ nguyên, kiểm rồi hoàn thiện; Leader chưa chạy test cho các sửa này.
- SHA256 helper: `c3633420b9964891f39aa2ebac0f09a382433c5ab554783f687c8f57b1d4d6bc`; test: `6359672c07a039316a2e723be8572db24333073f099d7e7c33f68fdaa9dc686f`.
- State browser cũ ghi PID 8900, port 62685, hết hạn 05:00:19 giờ Việt Nam. Kiểm mới: PID không tồn tại, port không có listener. Không coi trường `running` trong file cũ là tiến trình còn sống.
- Guard trước phục hồi trả YIELD vì receipt trong sổ; đây không phải chứng cứ worker sống hoặc đã hoàn tất.

## Việc giao tiếp

Một CTI Engineer dùng Sol medium trực tiếp, giữ thread/tree/branch hiện có; không bot/worker con, không reset, không sửa RUNS hoặc source tree khác. Đây là lần phục hồi đầu tiên của task tích hợp này.

Đọc và giữ toàn bộ phạm vi/tiêu chí ở brief gốc:
`$THREADS/484d57b0-1cb9-4264-b24a-54cecff6e454/PHONG-HOA-W03-STATUS-INTEGRATION-BRIEF-20261112.md`.

Tái dùng nghiên cứu S1 và hợp đồng đã chốt tại ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md (SQLite transactions/isolation, RFC 9110, OWASP Logging); không nghiên cứu lại hoặc đổi thiết kế. Backend `4f7100cf`, Frontend `2448b860`, prep `65e31980` vẫn đã nghiệm thu đúng phạm vi cũ, không chạy lại toàn bộ suite.

1. Đối chiếu HEAD và giữ hai sửa dở; kiểm parity UI với `2448b8600f9eff2c3e42b6742e220b46980f4ff4`. Hoàn thiện helper/tests trong allowlist cũ. Chạy focused helper/wire/component checks, typecheck/lint/build theo brief; ghi command/cwd/exit/count. Không tự sửa product Backend/Frontend nếu thấy lỗi: trả repro tối thiểu.
2. Tạo fixture từ API thật đúng HEAD cho parser UI; thiếu fixture phải FAIL, không skip. Tận dụng bằng chứng còn đúng; không gọi bằng chứng cũ chưa đủ là PASS.
3. Chạy các tình huống browser còn thiếu bằng trình duyệt OpenMausBot được cấp: lưu hai lần/lịch sử, known commit GET503→503→200, unknown outcome sau upstream commit rồi GET503→200, đổi quan hệ/đóng mở panel, context409/history cursor409. Mỗi tình huống cần ảnh, trace, SQLite cùng lượt; mutation không replay. Giữ smoke summary/sample/filter theo brief.
4. Dùng run_id/thư mục bằng chứng mới để giữ nguyên phần dở. Khởi động helper có thời hạn, chỉ loopback; xác minh cleanup bằng PID/port sở hữu thật. Không shell-launch browser/Playwright/CDP hoặc điều khiển màn hình máy người dùng thay bề mặt được cấp. Nếu browser không dùng được, hoàn thiện code/wire/tests rồi trả blocker chính xác cùng cách chạy lại; không treo chờ và không báo toàn luồng PASS.
5. Tối đa hai thử lại cho cùng một lỗi; ghi việc thiếu cụ thể nếu không thể hoàn tất. Báo cáo phần đã kiểm ngay khi kết thúc lượt để không mất tiến độ. Không push/PR/merge/deploy, đổi quyền/deps, lab/live feed/OpenCTI/cloud/LLM/secret hoặc W03-S2.

## Đầu ra

Giữ các đầu ra được chỉ định trong brief gốc tại `484d57b0-1cb9-4264-b24a-54cecff6e454`: `PHONG-HOA-W03-STATUS-INTEGRATION-RESULT.md` và `w03-status-integration-evidence/` (thêm thư mục recovery mới, không ghi đè evidence cũ). Trả HEAD/diff/status, mapping cherry-pick, manifest và cleanup; phân biệt test chạy mới, kết quả cũ tái dùng, browser chưa kiểm. Kết quả quay về Leader của lượt giao này để nghiệm thu và nối tiếp.
