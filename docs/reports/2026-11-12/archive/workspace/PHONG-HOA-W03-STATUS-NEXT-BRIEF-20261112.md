# W03-STATUS-NEXT — nghiên cứu bổ sung trạng thái xử lý

CTI Research làm trực tiếp, chỉ nghiên cứu; không code, không worker/bot con.
ROOT = `$WORKSPACE`.
Đọc source duy nhất `ROOT/cti-w03-read-integration` tại `7ff6eb3af21d8de65836bfbf707396ae5690de0b`, chỉ đọc. Không checkout/reset/tạo tree/sửa source hay ledger.

## Mục tiêu và tái sử dụng

Chọn phần W03-S nhỏ nhất giúp IT ghi trạng thái xử lý cho một công nghệ liên quan CVE, có lịch sử ai đổi/khi nào, và Leader chỉ đọc. Đây là tiêu chí còn thiếu trong spec W03, chưa phải triển khai hay xác nhận đã vá.

Đọc AGENTS/PROGRESS đúng ref; `docs/specs/W03-lo-hong-anh-huong.md`, contract API liên quan; ROOT `PHONG-HOA-W03-RESEARCH-20261112.md` mục W03-S, `PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md`, `leader-w03-final-acceptance-20261112/ACCEPTANCE.md`. Đối chiếu `portal_api/cves.py`, auth/tests, TechnologyStore và transaction/audit W04/W05 bằng tìm kiếm có mục tiêu. Không nghiên cứu lại CPE/ranking/KEV cơ bản hoặc nghiệm thu lại W03-R.

## Những điểm cần chốt

1. Granularity theo quan hệ technology/CVE; đánh giá khóa đã đề xuất `(technology_id,cve_id,vendor_key,product_key)`. Quy tắc khi sửa software_version, đổi tên, soft-delete rồi tạo lại: trạng thái “đã vá/không ảnh hưởng” không tự chuyển sang phiên bản hoặc danh tính khác. Lưu snapshot/history và cách hiển thị trạng thái cũ cần xem lại; lựa chọn đơn giản, có giải thích.
2. Trạng thái `open|patching|patched|not_affected`, chưa có row khác trạng thái đã lưu, chuyển trạng thái/reopen và ghi chú nào bắt buộc. Trạng thái là xác nhận của người dùng; không suy từ match tên thành bị ảnh hưởng hay từ phiên bản mới thành đã vá. Đề xuất nhỏ nhất cho status filter, KPI Leader, hạn KEV; tách phần chưa đủ dữ liệu/không cần cho lượt đầu. Không tự coi hạn CISA là nghĩa vụ SME.
3. Contract GET/ghi cụ thể: DTO/query/body, bounds/null/version, lỗi 401/403/404/409/422/503, role IT/analyst/admin và mixed-role, Leader redaction. Actor lấy từ danh tính đã xác thực; không tin metadata do client gửi. Ghi phải kiểm quan hệ/công nghệ và snapshot nguồn hiện hành, tránh ghi theo context đã cũ. Chỉ GET đối soát khi kết quả ghi chưa rõ, không tự gửi lại mutation.
4. SQLite migration additive, schema checks, optimistic status version và atomic status+append-only audit. Xử lý first write đồng thời, rollback, database thiếu/hỏng. GET W03 không tạo DB/migrate/ghi row. Chỉ rõ connection/transaction và cách không làm yếu kiểm read-only đã nghiệm thu.
5. W03 cursor/snapshot khi trạng thái đổi; giữ nguyên quyền, ranking/null/0/notice và giới hạn 1 MiB hiện có. Đề xuất tách status read/write port nếu hợp lý; không thêm nguồn thật hoặc seed fixture vào route thật.
6. UI tái dùng bố cục/provider hiện có: theo từng technology match, context ownership, double-submit, stale conflict, known commit/unknown outcome và lịch sử. Không redesign. Đủ contract để Backend/Frontend Sol medium làm độc lập trong tree riêng sau khi Leader chốt.

Tra cứu có mục tiêu 2–4 nguồn chính thức cho transaction/concurrency/audit hoặc workflow có thể tái dùng; ghi URL/ref/ngày và điều đã đọc trực tiếp. Tận dụng nghiên cứu cũ còn đúng, không dùng báo cáo như chứng cứ đã chạy. Nếu nguồn không truy cập được thì nêu đúng unknown; không truy cập feed/OpenCTI thật, lab, cloud LLM, secret.

## Đầu ra và điều kiện hoàn tất

Ghi **ROOT/PHONG-HOA-W03-STATUS-RESEARCH-20261112.md**, evidence nếu cần trong **ROOT/w03-status-research-evidence/**; không ghi sang thư mục riêng thay cho đích này. Báo cáo ngắn nhưng đủ contract: reuse/unknown/khuyến nghị, ma trận quyền và lỗi, migration/schema, acceptance matrix có first-write race, version/identity drift, rollback/non-mutation, cursor, quyền và UI recovery; kèm hai brief Backend/Frontend và integration gate. Nêu rõ phạm vi giai đoạn đầu/sau và base SHA/status đọc được. Chỉ giao đề xuất cho Leader review, không tự giao triển khai.

Không sửa source/DB/dependency/gateway/ledger; không push/PR/merge/deploy/lab hoặc chạy test full đã nghiệm thu. Đạt khi có contract đề xuất có nguồn và kiểm được, không phải khi chỉ gửi kế hoạch. Kết quả nghiên cứu không là implementation/test/runtime evidence.
