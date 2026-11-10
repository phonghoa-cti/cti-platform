# Tạo bản nháp IOC ngoại tuyến

CLI này đọc một file `.txt` UTF-8, dùng regex C1 hiện có, kiểm bằng chứng trên nguyên văn và ghi JSON
`status=pending` để analyst duyệt. Công cụ không gọi mạng, LLM hoặc OpenCTI.

```powershell
.\.venv\Scripts\python.exe extractor\draft\run.py `
  --input .\bao-cao.txt `
  --output .\draft.json `
  --language vi `
  --tlp TLP:AMBER
```

Lưu mỗi draft thành một bản ghi SQLite mới và đọc lại theo ID:

```powershell
.\.venv\Scripts\python.exe extractor\draft\store.py save `
  --db .\drafts.sqlite `
  --input .\draft.json

.\.venv\Scripts\python.exe extractor\draft\store.py get `
  --db .\drafts.sqlite `
  --id 1 `
  --output .\stored-draft.json

.\.venv\Scripts\python.exe extractor\draft\store.py list `
  --db .\drafts.sqlite `
  --limit 20 `
  --output .\draft-page.json

.\.venv\Scripts\python.exe extractor\draft\store.py list `
  --db .\drafts.sqlite `
  --limit 20 `
  --before-id 42 `
  --output .\draft-page-2.json
```

`save` kiểm lại schema, `status`, SHA-256 và mọi `span` trước khi mở database. `language` và `tlp` phải
là chuỗi thuộc tập giá trị hỗ trợ. Với IOC được giữ, đúng IOC sau chuẩn hóa phải nằm trọn trong chính
`span` đã khai báo; một quote ở vị trí khác không hợp thức hóa span sai. `get` chỉ đọc và không tự tạo
database nếu đường dẫn không tồn tại. `id` cùng `created_at` UTC do kho quản lý, không được phép chèn sẵn
trong draft đầu vào.

`list` chỉ đọc draft `pending`, sắp xếp ID giảm dần và dùng cursor `before_id` thay vì OFFSET. Summary chỉ có
ID/thời gian/trạng thái/source/ngôn ngữ/TLP/số item/cờ injection; không chứa toàn văn, evidence hoặc findings.
`next_before_id` là ID cuối trang khi còn dữ liệu, nếu hết thì là `null`. Insert mới chỉ xuất hiện khi tải lại
trang đầu, không làm lặp/mất các ID cũ ở trang sau; đây không phải snapshot chung qua nhiều lần đọc.

Output của `get`/`list` phải khác file DB, kể cả đường dẫn tương đương hoặc hard link tới cùng file. Các lệnh đọc
dùng SQLite `mode=ro`, không tạo database thiếu và không chuyển trạng thái.

`span` dùng chỉ số ký tự Python theo khoảng `[start, end)`, và `text[start:end]` luôn bằng `evidence` cho
mục có bằng chứng hợp lệ. JavaScript dùng đơn vị UTF-16 nên frontend phải chuyển đổi offset nếu văn bản có
ký tự ngoài Basic Multilingual Plane, ví dụ emoji.

`injection_warning=true` chỉ có nghĩa bộ quét thấy dấu hiệu chèn lệnh. Giá trị `false` không chứng minh văn
bản an toàn; draft vẫn luôn chờ người duyệt và regex không đánh giá TTP hay ngữ nghĩa attacker/victim.

Hợp đồng dữ liệu đầy đủ để nối W05 nằm tại
[`docs/specs/W05-draft-offline-contract.md`](../../docs/specs/W05-draft-offline-contract.md). Ba kết quả `get`
SQLite bằng dữ liệu tổng hợp nằm trong [`examples/`](examples/README.md); đây là fixture UI/hợp đồng, không phải
bằng chứng endpoint HTTP hay màn duyệt đã hoạt động.
