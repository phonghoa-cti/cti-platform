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

`save` kiểm lại schema, `status`, SHA-256 và mọi `span` trước khi mở database. `get` và từng hàng `list`
được trả cũng kiểm lại payload cùng metadata SQLite trước khi tạo output, nên dữ liệu cục bộ hỏng không bị
trả như draft hợp lệ. `language` và `tlp` phải
là chuỗi thuộc tập giá trị hỗ trợ. Với IOC được giữ, đúng IOC sau chuẩn hóa phải nằm trọn trong chính
`span` đã khai báo; một quote ở vị trí khác không hợp thức hóa span sai. `get` chỉ đọc và không tự tạo
database nếu đường dẫn không tồn tại. `id` cùng `created_at` UTC do kho quản lý, không được phép chèn sẵn
trong draft đầu vào.

Kho review dùng `PRAGMA user_version=1`. `get` trả object `review`; stdout của `get` ghi riêng
`payload_status`, `review_status` và `review_version`. `list` chỉ lấy review pending và summary có
`review_status`/`review_version`, nhưng không lộ text/items/evidence/findings. Hai lệnh đọc mở `mode=ro`, không
migration và không làm đổi byte database; schema legacy hợp lệ được đọc như creator null, pending/version 0.

API Python cho caller tin cậy có thể lưu tác giả và quyết định cục bộ:

```python
from phonghoa_extractor.store import Actor, decide_draft, migrate_store, save_draft

draft_id = save_draft(db, draft, created_by_subject="opaque-author-subject")
result = decide_draft(
    db,
    draft_id,
    actor=Actor("opaque-reviewer-subject", frozenset({"analyst"})),
    decision="approve",
    expected_version=0,
)
```

Database legacy phải gọi `migrate_store(db)` rõ ràng trước khi quyết định. CLI không có cờ actor tự khai vì
đó sẽ không phải đăng nhập; draft lưu bằng CLI không có creator nên không thể approve. Lõi chỉ kiểm policy
offline, không xác minh JWT/header. Approve nghĩa là đã duyệt cục bộ, không gọi mạng hay nhập OpenCTI.

Ba lệnh chỉ nhận `timeout` là số hữu hạn không âm; giá trị sai bị từ chối trước khi mở SQLite.

`list` chỉ đọc review `pending`, sắp xếp ID giảm dần và dùng cursor `before_id` thay vì OFFSET. Summary chỉ có
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
