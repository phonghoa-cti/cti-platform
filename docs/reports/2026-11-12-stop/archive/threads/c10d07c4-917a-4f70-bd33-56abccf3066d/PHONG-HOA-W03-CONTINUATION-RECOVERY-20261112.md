# Phong Hỏa W03 — nối phần còn thiếu ngày 12/11/2026

ROOT = `$WORKSPACE`

Brief gốc cho cả hai việc: `$THREADS\ac95b575-9df8-4f39-bb20-f27be0abf7e9\PHONG-HOA-W03-PRODUCT256-ACCEPTANCE-NEXT.md`.

## Quan sát Leader trước giao tiếp

- Danh sách cuộc việc: Engineer `b05471df-3a0c-49c0-b02b-4019e1cf15d4` và Research `05beb527-c2dd-4aa5-adbf-58125f63f63c` đều idle. Không thấy một cuộc Leader khác đang chạy trong danh sách được trả.
- Sổ vẫn active, user_paused=false; hai việc dispatched với receipts `934cd526-c973-4664-b13c-8011b8f9d6c9` và `d13cd680-3475-40d1-a76c-b441874a1d73`. Công cụ đọc assignment từ cuộc khác từ chối; chưa biết outcome của hai request, không coi là failed/completed.
- Không thấy `PHONG-HOA-W03-S1-CLOSEOUT-RESULT.md` hoặc `PHONG-HOA-W03-S2-RESEARCH.md` tại đường dẫn chỉ định, cả sau tìm theo đúng tên trong hai thư mục của Leader.
- Tree `ROOT\cti-w03-status-integration` có HEAD `f5d2315e94b7f83e44360a04b67902cb5b0ba4bd`; status sạch. So với `867bdcaeffded177ee119fe5e05015c4700979db` chỉ đổi `docs/PROGRESS.md`; diff-check exit 0. Không chạy lại kiểm thử chức năng đã accepted.
- PID 31176 vẫn là node chạy đúng `cti-w03-status-integration\tools\local_integration\gateway.mjs`, parent 32440, creation `2026-11-12T06:04:48.078039+07:00`; port 52963 vẫn Listen của PID 31176. Parent không còn trong kết quả truy vấn. Đây là quan sát, chưa phải quyền dừng hoặc bằng chứng cleanup.
- Guard và receipt chỉ phản ánh sổ, không chứng minh worker đang chạy. Giữ lịch tiếp tục và lịch khôi phục hạn mức; chưa đủ điều kiện hoàn tất dự án.

## Engineer — hoàn tất closeout còn thiếu trong cùng thread

Một Sol medium trực tiếp, không worker lồng; giữ tree/nhánh hiện tại và commit f5d2315e. Tái dùng brief gốc, chỉ làm phần chưa có bằng chứng. Không chạy lại suite/browser đã accepted, không triển khai chức năng mới.

1. Đọc delta docs f5d2315e và xác nhận mô tả chặng A/B/product256 không mâu thuẫn trạng thái hiện tại. Nếu cần sửa, chỉ `docs/PROGRESS.md`; các mô tả lịch sử phải rõ là lịch sử. Không sửa source/runtime/contract/fixture.
2. Đối chiếu metadata/run_id/artifact của chính nhiệm vụ để chứng minh quyền sở hữu gateway PID 31176/port 52963. Kiểm lại danh tính process ngay trước thao tác. Chỉ dừng đúng process đã chứng minh thuộc nhiệm vụ và không còn người dùng; không dừng theo tên node hoặc port chung. Nếu thiếu bằng chứng sở hữu, giữ nguyên và ghi blocker với điều còn thiếu. Không xóa dữ liệu/clone/evidence, không tác động tiến trình khác.
3. Viết báo cáo gốc còn thiếu tại `$THREADS\ac95b575-9df8-4f39-bb20-f27be0abf7e9\PHONG-HOA-W03-S1-CLOSEOUT-RESULT.md`: HEAD, diff docs, trạng thái tree, diff-check exit code, chứng cứ sở hữu và trạng thái process/port sau thao tác hoặc blocker cụ thể. Phân biệt cleanup task này với toàn máy; tách bằng chứng cũ tái dùng và kiểm mới. Nếu cần artifact bổ sung, chỉ ghi thư mục `w03-s1-closeout-evidence` cạnh báo cáo.

Không sửa RUNS, không push/PR/merge/deploy/cloud/LLM/lab, không tự giao người khác. Kết quả chỉ là closeout để Leader nghiệm thu W03-S1 đúng phạm vi cục bộ.

## Research — trả nghiên cứu S2 còn thiếu trong cùng thread

Giữ phạm vi nghiên cứu và output gốc: `$THREADS\ac95b575-9df8-4f39-bb20-f27be0abf7e9\PHONG-HOA-W03-S2-RESEARCH.md`.

Đọc brief gốc; source bằng Git tại ref cố định 867bdca để không đọc theo docs đang sửa. Tái dùng nghiên cứu W03-S đã có, đối chiếu spec/source và nguồn chính thức cần thiết. Không làm lại phần đã phù hợp. Chốt đề xuất lát cắt nhỏ cho lọc trạng thái toàn danh sách và tổng hợp Leader: quan hệ CVE–technology nhiều-nhiều, unset/review_required/inactive, hạn vá và timezone/null, quyền summary, snapshot/cursor khi status đổi, ranking/KEV/count/pagination. Nêu 2–3 phương án, phần tái dùng, đề xuất, giới hạn/chưa biết và brief Backend/Frontend cùng cổng tích hợp. Không coi ghi nhận đã vá là chứng minh vá thật.

Chỉ ghi báo cáo; không code, không đổi UI/quyền, không live feed/model/lab, không sửa RUNS hoặc giao tiếp người khác. Nếu công cụ/nguồn bị chặn, vẫn trả báo cáo những gì đã xác minh cùng blocker, không để thiếu đầu ra. Leader phải nghiệm thu/chọn hợp đồng trước mọi triển khai S2.
