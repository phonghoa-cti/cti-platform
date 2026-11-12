# W03-S2 — hoàn tất bản Backend đang sửa dở

Ngày 12/11/2026, khoảng 10:28 giờ Việt Nam. Task W03-STATUS-S2-BACKEND, CTI Backend / Sol medium, cùng thread ec2f0709-b0f2-46ed-823d-9a461e1f1912. Đây là lần nối lại thứ hai; không tạo worker hoặc tree mới.

## Quan sát mới của Leader

- Thread Backend idle tại lần đọc danh sách đầu lượt. Không thấy Leader khác đang chạy trong danh sách trả về.
- HEAD vẫn 4a8f409fe50d861797c49d1c0a3bb48c30ac2fa7. Tree có 9 file thay đổi/mới: app.py, module cves_status_view.py, test_cves_status_view_api.py, 3 fixture, ADR 0017, contract và PROGRESS. Hai file module/test được ghi lúc 10:09:58. Đây là tiến triển so với lần trước tree sạch; chưa phải kết quả đã nghiệm thu.
- Báo cáo và thư mục raw evidence đúng nơi được giao chưa tồn tại. Chưa chạy lại test của worker; không suy diễn các test đã xanh từ code hoặc PROGRESS.
- Chi tiết request 51cd0bb6-7f73-4d20-9607-cfccb1911a91 không đọc được từ requester khác. Không kết luận request failed/cancelled/completed. Lượt Leader trước hết giới hạn 15 phút.
- Guard YIELD/exit 0 chỉ phản ánh receipt cũ, không chứng minh worker sống.

## Phần cần hoàn tất

Dùng nguyên tree $WORKSPACE\cti-w03-status-s2-backend, branch feat/w03-status-s2-backend-20261112. Giữ toàn bộ sửa đổi đang có; không reset hoặc làm lại implementation từ đầu.

Brief/hợp đồng gốc giữ nguyên: $THREADS\c10d07c4-917a-4f70-bd33-56abccf3066d\PHONG-HOA-W03-S2-DECISION-AND-BACKEND-BRIEF.md. Tái dùng nghiên cứu đã chốt, không mở thêm vòng nghiên cứu hay worker lồng.

1. Đọc trạng thái Git hiện tại và kiểm phần triển khai đang có. Chạy test S2 và hai nhóm hồi quy test_cves_api.py, test_cves_status_api.py bằng Python .venv hiện có với cwd/PYTHONPATH đúng checkout; lưu lệnh, stdout/stderr và exit code mới. Sửa đúng lỗi trong allowlist gốc, không mở rộng chức năng.
2. Bảo đảm có bằng chứng quyền Leader chặn trước dependency; DTO không lộ relation; filter trước paging; clock/date rollover; cursor drift; dữ liệu hỏng 503; GET không ghi; transaction chỉ đọc cùng connection và test writer commit giữa hai lần đọc. Kiểm fixture xuất từ API phù hợp contract đầy đủ. Nếu test thiếu, bổ sung đúng tiêu chí gốc.
3. Ruff đúng file, git diff --check. Nếu có bằng chứng RED trước đó, trả đúng log; nếu không còn, ghi RED UNVERIFIED, không dựng lại lịch sử test giả.
4. Commit cục bộ khi checks đạt, báo SHA/diff/tree status và các bằng chứng. Nếu bị ngắt hoặc gặp blocker, vẫn ghi ngay báo cáo tiến độ với lệnh cuối, lỗi cụ thể, phần thiếu để Leader tiếp tục; không chỉ trả lời đã nhận việc.

Báo cáo giữ tại $THREADS\c10d07c4-917a-4f70-bd33-56abccf3066d\PHONG-HOA-W03-S2-BACKEND-RESULT.md. Raw evidence ở thư mục w03-s2-backend-evidence cùng chỗ.

Không sửa RUNS, UI, gateway, tree nguồn hoặc dịch vụ kiểm thử cũ. Không push/PR/merge/deploy/lab/LLM thật/đổi dependency. Leader chưa giải phụ thuộc Frontend; chỉ giao UI sau review Backend. Nếu lần nối này lại dừng cùng nguyên nhân, Leader phải chẩn đoán/đổi cách, không tự động giao lại lần thứ ba.
