# X01-DRAFT-QUEUE — tìm và đọc bản nháp đang chờ trên máy

Ngày 10/11/2026. CTI Engineer, Sol medium; một người sửa checkout, không giao tiếp cho worker khác.

## Đích và hiện trạng

Người dùng đóng/mở chương trình, xem danh sách bản nháp pending theo từng trang rồi chọn ID để đọc chi tiết,
thay vì phải nhớ ID từ lúc save. Đây là phần truy vấn kho trong khoảng trống W05; chưa phải màn duyệt/API.

Checkout: `$WORKSPACE\cti-platform-start`.
Base `2959eb0540bd708eeae60fedd9d11b13d32b543b`, sạch; tạo nhánh `feat/x01-draft-queue-20261110`.
Đã nghiệm thu store base `165c6ca`: 157 test trong log, Leader chạy 42 test store/CLI đạt.
Đã nghiệm thu contract: Leader tự chạy 3/3 fixture roundtrip đạt. Không coi các test base là test mới.

Đọc AGENTS, PROGRESS, docs/specs/W05-draft-offline-contract.md, api-portal.md phần drafts,
extractor/phonghoa_extractor/store.py, extractor/draft/store.py và tests tương ứng.
Yêu cầu tiếp tục dự án đã có; Leader chọn kỹ thuật có thể đảo ngược trong phạm vi ngoại tuyến.

## Nguồn và lựa chọn của Leader

Đã đọc tài liệu SQLite chính thức ngày 10/11/2026:
- [Scrolling window queries](https://www.sqlite.org/rowvalue.html#scrolling_window_queries): trang tiếp theo
  có thể dựa vào khóa cuối của trang trước; OFFSET phải bỏ qua các dòng trước đó.
- [ORDER BY/LIMIT](https://www.sqlite.org/lang_select.html#limitoffset): phải chỉ định thứ tự, giới hạn số dòng;
  LIMIT âm bỏ giới hạn nên cần kiểm đầu vào.

Chọn dùng lại SQLite/stdlb và ID khóa chính đã có: `id DESC`, trang sau `id < before_id`, lấy tối đa limit+1
để biết còn trang hay không. Không cần OFFSET, ORM, HTTP, cache hoặc schema DB mới cho phần này.
Đây là suy luận áp dụng mẫu SQLite vào một khóa ID, không phải benchmark hiệu năng đã chạy.
PR #1/#46 đã đối chiếu ở bước trước cùng tối nay, head không đổi; không checkout main hoặc merge PR.

## Hợp đồng cần triển khai

- Hàm `list_drafts(db_path, *, limit=20, before_id=None, timeout=5.0)` chỉ liệt kê `pending`.
- Limit là int thật, không bool, trong [1,100]. before_id null hoặc int dương trong miền INTEGER SQLite;
  sai kiểu/ngoài miền phải lỗi dự kiến, không traceback. Cursor không buộc phải là ID đang tồn tại.
- Trả `{"items": [summary...], "next_before_id": integer_or_null}`.
  Mỗi summary đúng các trường: id, created_at, status, source {name,sha256}, language, tlp,
  item_count, injection_warning. Không có text, evidence, findings.excerpt hoặc danh sách items đầy đủ.
- Sắp xếp id giảm dần. next_before_id là ID cuối trang nếu còn ít nhất một dòng, ngược lại null;
  trang rỗng trả items=[]/null. Không tự tạo DB/table khi đọc, không ghi/chuyển trạng thái.
- Dùng mode=ro, SQL tham số hóa, đóng connection cả khi lỗi và timeout hữu hạn như get hiện có.
  Lỗi DB/JSON/cấu trúc cần cho summary trả DraftStoreError rõ mà không in payload; không âm thầm bỏ bản ghi lỗi.
- CLI thêm `list --db <sqlite> --limit <n> [--before-id <id>] --output <json> [--timeout <seconds>]`.
  Terminal chỉ in số mục và cursor; output có summary đầy đủ. File đầu ra không được trùng DB
  (cả đường dẫn tương đương hoặc samefile nếu tồn tại); có thể dùng cùng guard cho get để tránh ghi đè DB.
  Lỗi trước khi xuất phải không tạo/ghi đè output. Không thay cách save/get bình thường.
- Khi có bản mới giữa hai lần đọc trang, cursor vẫn đi về ID thấp hơn; bản mới xem bằng tải lại trang đầu.
  Không tuyên bố đây là snapshot chung qua nhiều lần đọc.

## Phạm vi file và trình tự

Cho sửa store module/CLI, tests store/CLI (hoặc thêm test_queue.py/test_queue_cli.py), README draft,
docs/specs/W05-draft-offline-contract.md và PROGRESS. Viết đặc tả phần queue vào phụ lục trước code.
Hai chỉnh lý nhỏ cùng file contract: escape dấu pipe ở ô language; nói rõ kind/status chưa được siết đầy đủ
cho dữ liệu tự khai ngoài kind=ioc. Không biến sửa tài liệu này thành việc nới schema hoặc hỗ trợ TTP.
Không đổi core/grounding/fixtures, schema SQLite, dependencies, UI hoặc các endpoint HTTP.

## Kiểm chứng cần có

1. Test trước: DB có 5 draft, limit=2 → ID [5,4], [3,2], [1]; cursor 4,2,null; lấy get một ID từ trang thật.
2. Chèn ID mới giữa các trang: các ID cũ không lặp/mất; tải lại trang đầu thấy ID mới. Kiểm rỗng,
   đúng bội số limit, một trang, before_id không tồn tại và không trả trạng thái khác pending.
3. Metadata đúng nhưng không lộ nội dung report trong summary/log; Unicode và source hash không đổi.
4. Limit/cursor sai, DB thiếu/hỏng/bị khóa có timeout, JSON lỗi: lỗi dự kiến, không tạo DB, không sửa bản ghi
   hoặc output cũ. Kiểm nội dung DB trước/sau các lệnh đọc trên DB tổng hợp không có writer khác.
5. CLI qua tiến trình riêng: save nhiều mẫu → list trang → list trang sau → get ID; kiểm output và exit.
   Output trùng DB phải bị chặn, DB vẫn đọc được. Giữ regression save/get hiện có.
6. Đúng Python 3.12.13: test mới RED/GREEN, suite phù hợp và toàn suite cuối; Ruff/format/diff-check.
   Đặt DB/log ngoài repo tại `x01-queue-evidence/`, không ghi vào DB bằng chứng cũ.

Bàn giao local commit sạch, SHA/nhánh/diff, lệnh/exit/số test, `PHONG-HOA-X01-QUEUE-RESULT.md`,
`PHONG-HOA-X01-QUEUE-SAMPLE.json` và logs ở thư mục cha checkout. Ghi rõ các giới hạn HTTP/auth/UI/lab.
Không push/PR/merge/deploy, phê duyệt/từ chối, OpenCTI, cloud, lab hoặc thay quyền. Nếu cần ngoài phạm vi,
báo lỗi/tái hiện cụ thể; tối đa hai lần thử cùng blocker rồi báo Leader.

Leader sẽ nghiệm thu luồng tạo→lưu→liệt kê→đọc trước khi chọn bước tiếp trong phần ngoại tuyến.
