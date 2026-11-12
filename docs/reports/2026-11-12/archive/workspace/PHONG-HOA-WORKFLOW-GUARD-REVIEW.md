# Leader review WORKFLOW-GUARD

Ngày 10/11/2026. Verdict lượt đầu: NEEDS_FIX (đã khắc phục và nghiệm thu 11/11 bên dưới). SHA256 code cũ `fcebdc6e42c1c3993d332936233cd4914c3acea790aecf2fccdfbf6c08c3297a`; hash test/report khớp bàn giao. Repo sản phẩm vẫn sạch tại `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`.

Leader chạy lại bằng Python 3.12: `python -B -m unittest workflow.test_check_continuation -q`: 27 tests, OK, exit 0. Đã đọc implementation, tests và evidence. Chưa nghiệm thu vì hai lỗi tái hiện độc lập dưới đây.

## R1 — trạng thái sai kiểu không đi vào INVALID

Tạo bản sao sổ thật trong thư mục tạm; lần lượt đặt bốn trường thành `[]`: `project.status`, `project.completion_criteria[0].state`, `tasks[1].status`, `tasks[1].receipt.outcome`. Mỗi lần gọi CLI thật trả exit 1, stdout rỗng, stderr traceback kết thúc `TypeError: unhashable type: 'list'`.

Yêu cầu: kiểm kiểu trước phép membership trong set; list/dict/null/bool/number tại các trường enum phải trả JSON INVALID, exit 2, không traceback và không in lại sổ. Thêm regression CLI cho list và dict tại bốn vị trí; giữ ca hợp lệ hiện tại. Rà cùng lớp lỗi ở các trường enum khác, không bọc nuốt mọi exception để giả đạt.

## R2 — quan sát idle vẫn được dùng để YIELD

Trên bản sao sổ thật, đổi task WORKFLOW-GUARD thành running và thêm receipt.observation: `{source: 'thread inspection', status: 'idle', observed_at: '2026-11-10T23:31:00+07:00'}`. CLI trả YIELD, exit 0. `_validate_receipt` chỉ chặn queued nên còn nhận idle/completed/failed hoặc chuỗi tùy ý. Điều này có thể kéo dài trạng thái chờ sai.

Yêu cầu: observation hỗ trợ đúng trạng thái `running` cho task running. idle/completed/failed/queued/chuỗi không biết/sai kiểu phải INVALID exit 2 để Leader đối chiếu công việc thật; không tự sửa sổ, không tự gọi live API. README nói rõ quy ước trạng thái và giới hạn nguồn quan sát. Thêm regression rồi kiểm lại running hợp lệ vẫn YIELD.

## Phạm vi rework

Giữ nguyên phạm vi brief WORKFLOW-GUARD: chỉ workflow/*.py, README, workflow-evidence và báo cáo kết quả. Không sửa repo sản phẩm, RUNS hay file review này. Python 3.12 sẵn có; test đỏ cho ca mới trước sửa, unittest toàn nhóm, Ruff check/format, demo chỉ đọc sổ thật kèm hash trước/sau. Không chạy lại 236 test CTI. Báo hash mới và exit; tối đa một vòng sửa hai finding này rồi trả Leader nghiệm thu.

Nghiên cứu W05 đã được Leader chấp nhận về hướng B sau đối chiếu mã và nguồn; brief đã bổ sung quyết định Leader. Engineer làm W05 khi nhận giao tiếp sau nghiệm thu guard, không tự sửa sản phẩm trong nhiệm vụ này.

## Nghiệm thu rework — 11/11/2026

PASS cục bộ R1/R2. Leader đối chiếu hash code `3b781dd2aca755e129f26440a1253cf0f166280df9e714202f8f13fe4128a4f2`, đọc sửa enum và running observation, chạy `python -B -m unittest workflow.test_check_continuation -q`: 32/32, exit 0. Bằng chứng tổng hợp tại `PHONG-HOA-LEADER-ACCEPTANCE-20261111.md`. Cho dùng guard vào sổ thật; guard vẫn không kiểm worker sống và không là Stop hook tự cưỡng chế.
