# X01-QA-FIX — thống nhất kiểm dữ liệu đọc và timeout

Ngày 10/11/2026. CTI Engineer, Sol medium; một người sửa checkout, không giao tiếp cho worker khác.
Checkout `$WORKSPACE\cti-platform-start`.
Giữ nhánh `feat/x01-draft-queue-20261110`, base `d03fa10523b45b94182038b5b46fed8231319e6f`, kiểm sạch trước sửa.

Đọc AGENTS, PROGRESS, hợp đồng W05 offline và báo cáo đầy đủ `PHONG-HOA-X01-OFFLINE-QA-RESULT.md`
ở thư mục cha repo. Leader đã xác minh nguồn báo cáo, mã và tự tái hiện; đây là yêu cầu sửa của Leader.
Nghiên cứu dùng lại: cơ chế kiểm schema/hash/span và SQLite từ các brief STORE/QUEUE; không đổi kiến trúc.

## F1 — kiểm dữ liệu khi đọc (MEDIUM)

QA sửa riêng payload_json của ID 2 trong bản sao DB tổng hợp thành
`{"status":"approved","text":"tampered-local-copy"}`. list từ chối, get exit 0 và trả payload hỏng,
nhưng stdout lại ghi pending. Leader tái hiện cùng hành vi tại `x01-offline-qa-evidence/05-leader-confirmation.log`.

- Tách phần decode/validation của row dùng chung cho get và list; chọn cả schema_version, status,
  source_sha256, id, created_at, payload_json từ SQLite. Không tạo hai bộ kiểm gần giống nhau.
- Kiểm payload theo `_validate_draft`, cột schema/status/source hash khớp payload, ID hợp lệ,
  created_at là ISO có timezone như contract. Chỉ trả detail/summary khi đã kiểm đạt.
- Bảo toàn payload hợp lệ, metadata và thứ tự items. Lỗi trả DraftStoreError dự kiến; không ghi DB,
  không tạo/ghi đè output cũ, không in toàn văn/traceback. stdout phải lấy status đã xác thực thay vì báo sai.
- list vẫn lọc pending theo contract; không yêu cầu quét/validate mọi hàng đã bị lọc hoặc nằm ngoài trang.

## F2 — timeout nhất quán (LOW)

`list --timeout nan` từ chối, `get` vẫn đọc được, `save` còn tạo ID mới. Leader đã tái hiện trên DB mới.
Dùng một helper kiểm timeout cho cả ba thao tác trước mở DB: chỉ int/float, không bool, không âm,
biểu diễn được thành số hữu hạn; nan/inf/-inf/âm/sai kiểu phải bị từ chối. Không bắt mọi Exception.
Giữ giá trị hợp lệ/default và timeout khóa đang có; không thêm retry, dependency hoặc chính sách mới.

## Phạm vi và nghiệm thu

Chỉ store module, CLI, tests store/queue liên quan, README/contract nếu cần phản ánh hành vi và PROGRESS.
Không đổi schema SQLite, core/grounding, fixtures đã commit, UI, HTTP/auth, phê duyệt hoặc OpenCTI.

Test trước rồi sửa, bằng Python 3.12.13:
1. get với JSON hỏng/thiếu trường/sai hash/span, cột schema/status/hash không khớp, created_at lỗi/không timezone
   đều bị từ chối; DB byte và output đã có giữ nguyên. list cùng lỗi ở hàng pending được trả cũng từ chối.
2. Payload hợp lệ từ ba fixture W05 save→list→get nguyên vẹn; kiểm đầu ra status khớp, rejected/allowlist không mất.
3. timeout invalid qua API/CLI cho ba thao tác: không tạo DB mới, không thêm/sửa bản ghi cũ, không đổi output.
   Bool là ca API; nan/inf/âm là ca CLI. Timeout hợp lệ và lock timeout vẫn chạy đúng.
4. Nhóm store/queue và toàn suite cuối, Ruff/format/diff-check, một demo đủ luồng trên DB mới.

Giữ bằng chứng cũ. Thêm log RED/GREEN/demo dưới `x01-qa-fix-evidence/` ở thư mục cha repo;
báo cáo `PHONG-HOA-X01-QA-FIX-RESULT.md`, commit local sạch kèm SHA/diff/lệnh/exit/số test/giới hạn.
Không sửa harness/báo cáo QA để biến FAIL thành PASS; hồi quy mới thuộc tests repo, QA kiểm lại sau.
Không push/PR/merge/deploy, cloud, lab, secret hoặc thay quyền. Nếu cùng nguyên nhân vướng hai lần, báo cụ thể.

Sau bàn giao, Leader nghiệm thu tập trung rồi giao QA xác nhận lại F1/F2 trên SHA mới; chưa mở bước tính năng tiếp.
