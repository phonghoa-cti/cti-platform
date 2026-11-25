# WORKFLOW-GUARD — bộ kiểm tra trước khi nhường/kết thúc lượt

Owner CTI Engineer, Sol medium; tự làm, không giao tiếp cho bot khác. Mục đích sửa lỗi điều phối lặp lại, không xây scheduler hoặc sửa sản phẩm CTI.

## Cơ sở và phạm vi

Workspace là thư mục chứa brief. Đọc `PHONG-HOA-ORCHESTRATION-RESEARCH-20261110.md`, mục 11 `PHONG-HOA-WORKING-AGREEMENT.md`, và `PHONG-HOA-RUNS.json` (chỉ đọc; Leader sẽ cập nhật receipt song song). Tái sử dụng ý tưởng Stop gate đã nghiên cứu, không cần khảo sát lại. Lỗi cần bắt: task con đạt + sổ hết việc nhưng mục tiêu mẹ vẫn active thì không được cho COMPLETE.

Chỉ được viết `workflow/check_continuation.py`, `workflow/test_check_continuation.py`, `workflow/README.md`, `workflow-evidence/` và `PHONG-HOA-WORKFLOW-GUARD-RESULT.md` ở workspace. Kiểm file tồn tại trước khi thay. Không sửa repo `cti-platform-start`, sổ RUNS, working agreement, skill/config/ứng dụng OpenMausBot, ổ E hoặc cấu hình Claude. Không commit/push/PR/merge/deploy, mạng, bot, UI, máy người dùng, cron hay vòng chờ. Không thêm dependency. Python dùng `cti-platform-start\.venv\Scripts\python.exe` 3.12.13.

## Giao diện và quyết định

CLI chỉ đọc: `python workflow/check_continuation.py --ledger PHONG-HOA-RUNS.json`, stdout JSON UTF-8 gồm decision, task_ids, reasons. Không thực thi nội dung sổ; không tự gửi việc hoặc sửa trạng thái. Dùng unittest stdlib. Hàm thuần riêng để test được.

Schema đầu vào dùng đúng sổ hiện có: schema_version=1; project.status active/complete, user_paused boolean, pause_reason, completion_criteria có state pending/verified và evidence; tasks có id/status/owner/priority/depends_on/receipt/blocker/evidence; accepted_results ghi kết quả đã nhận. Có thể bỏ qua metadata chưa dùng, không tự sửa schema thật. Task states: planned, queued, dispatched, running, reported, accepted, blocked, failed, stalled. Receipt khi dispatched/running: request_id, thread_id, outcome queued hoặc accepted, recorded_at; running cần thêm observation có nguồn trạng thái thật. Kết quả công cụ chỉ queued không đủ gọi running.

Thứ tự đánh giá:
1. JSON/schema/ID/dependency sai (kể cả ID trùng, dependency thiếu hoặc cycle), status sai, receipt thiếu cho dispatched/running, blocked thiếu reason/owner/unblock_condition, accepted thiếu evidence → INVALID, exit 2. File thiếu/hỏng không được cho qua. Không log cả sổ hoặc dữ liệu ngoài lỗi trường cần thiết.
2. user_paused=true và có pause_reason → PAUSED, exit 0; không đề nghị giao mới.
3. project.status=complete chỉ hợp lệ khi mọi completion_criteria verified có evidence, không còn task chưa accepted. Nếu không → INVALID; đủ → COMPLETE, exit 0.
4. Có reported → REVIEW, exit 1. Có failed/stalled → REPLAN, exit 1. Báo IDs cần xử lý.
5. queued đủ dependency accepted, owner chưa bận dispatched/running → DISPATCH, exit 1; sắp priority giảm, chọn nhiều nhất một task/owner. Không cần hoàn thành mọi blocker mới giao được việc độc lập.
6. Có việc dispatched/running hợp lệ → YIELD, exit 0: có receipt/callback nên nhường lượt, không phải dự án đã xong. Nói rõ đây là dữ liệu ghi trong sổ, không phải live check.
7. Tất cả task chưa accepted đều blocked có lý do cụ thể → BLOCKED, exit 0, kèm IDs/lý do; không COMPLETE. Dependency chờ một task blocked có thể nêu trong reasons, không tự chuyển thành blocked.
8. Mọi trường hợp active còn lại, kể cả toàn task accepted hoặc danh sách task rỗng → PLAN_NEXT, exit 1. Mục tiêu đang mở thì cần đối chiếu backlog và chuẩn bị việc kế.

Không được nhầm receipt accepted với task accepted. Kết quả đã có request_id trong accepted_results chỉ là dữ liệu chống làm lại; không tự tạo task từ báo cáo cũ. Giới hạn quan trọng: script không chứng minh người đang chạy, không cưỡng chế engine dừng/tiếp; README phải nói rõ đây là cổng quy trình Leader chủ động gọi, chưa là Stop hook OpenMausBot.

## Kiểm chứng

Viết test trước cho các tình huống trên, đặc biệt: root active/all children accepted; empty queue; lab blocked nhưng offline ready; queued cần người đang bận; receipt giả/thiếu; reported chưa review; project complete nhưng tiêu chí còn thiếu; invalid JSON/cycle; paused; full verified complete. Mỗi ca kiểm decision và exit theo CLI ở nhóm cần thiết, không chỉ test gọi lại chính helper. Test không ghi sổ thật.

Chạy unittest, Ruff check/format nếu dùng được .venv có sẵn, demo đọc sổ thật (chỉ đọc) và so hash trước/sau. Không chạy lại 236 test CTI vì không đổi CTI. Báo Python/lệnh/exit/số test, SHA256 file mới, quyết định sổ thật, các hạn chế. Đầu ra mã không nằm trong repo Git nên báo hash, không bịa commit. Trả kết quả; Leader tự nghiệm thu và nối W05 sau nghiên cứu.
