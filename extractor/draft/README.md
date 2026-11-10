# Tạo bản nháp IOC ngoại tuyến

CLI này đọc một file `.txt` UTF-8, dùng regex C1 hiện có, kiểm bằng chứng trên nguyên văn và ghi JSON
`status=pending` để analyst duyệt. Công cụ không gọi mạng, LLM, OpenCTI hoặc SQLite.

```powershell
.\.venv\Scripts\python.exe extractor\draft\run.py `
  --input .\bao-cao.txt `
  --output .\draft.json `
  --language vi `
  --tlp TLP:AMBER
```

`span` dùng chỉ số ký tự Python theo khoảng `[start, end)`, và `text[start:end]` luôn bằng `evidence` cho
mục có bằng chứng hợp lệ. JavaScript dùng đơn vị UTF-16 nên frontend phải chuyển đổi offset nếu văn bản có
ký tự ngoài Basic Multilingual Plane, ví dụ emoji.

`injection_warning=true` chỉ có nghĩa bộ quét thấy dấu hiệu chèn lệnh. Giá trị `false` không chứng minh văn
bản an toàn; draft vẫn luôn chờ người duyệt và regex không đánh giá TTP hay ngữ nghĩa attacker/victim.
