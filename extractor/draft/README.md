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
```

`save` kiểm lại schema, `status`, SHA-256 và mọi `span` trước khi mở database. `get` chỉ đọc và không
tự tạo database nếu đường dẫn không tồn tại. `id` cùng `created_at` UTC do kho quản lý, không được phép
chèn sẵn trong draft đầu vào.

`span` dùng chỉ số ký tự Python theo khoảng `[start, end)`, và `text[start:end]` luôn bằng `evidence` cho
mục có bằng chứng hợp lệ. JavaScript dùng đơn vị UTF-16 nên frontend phải chuyển đổi offset nếu văn bản có
ký tự ngoài Basic Multilingual Plane, ví dụ emoji.

`injection_warning=true` chỉ có nghĩa bộ quét thấy dấu hiệu chèn lệnh. Giá trị `false` không chứng minh văn
bản an toàn; draft vẫn luôn chờ người duyệt và regex không đánh giá TTP hay ngữ nghĩa attacker/victim.
