# Đánh giá extractor C1 ngoại tuyến

Lệnh này chạy baseline C1: dùng regex có sẵn để trích IOC rồi so với nhãn `attacker` trong dataset.
Nó không gọi mạng, LLM, OpenCTI hoặc Docker.

## Chạy lại smoke test

Từ thư mục gốc repo trên Windows:

```powershell
.\.venv\Scripts\python.exe extractor\eval\run.py `
  --config C1 `
  --dataset extractor\dataset\synthetic-smoke `
  --output .\x01-c1-smoke-result.json
```

`synthetic-smoke` gồm 6 văn bản ngắn tự tạo bằng tiếng Việt và tiếng Anh. Đây chỉ là phép kiểm tra kỹ
thuật (smoke test), không phải benchmark, tập gold do hai người gán nhãn hoặc bằng chứng chất lượng cho luận
văn.

## Đầu ra

- `documents`: IOC dự đoán, SHA-256 của nguồn và TP/FP/FN theo từng báo cáo.
- `micro`: cộng TP/FP/FN của mọi báo cáo trước khi tính Precision, Recall và F1.
- `by_type`: các số đo micro tách theo loại IOC.
- `dataset_sha256`: dấu vân tay của toàn bộ text, metadata và nhãn để kiểm tra lần chạy dùng cùng input.
- `ttp.status = not_evaluated`: C1 regex không chấm TTP, vì vậy không ghi điểm 0 gây hiểu nhầm.

Precision là tỷ lệ dự đoán đúng trong các IOC máy trích; Recall là tỷ lệ IOC trong nhãn mà máy tìm thấy; F1
cân bằng hai tỷ lệ này. Theo `extractor/dataset/GUIDELINE.md`, chỉ nhãn có `role=attacker` được tính là đúng
cho điểm chính. IOC `victim` hoặc `benign` vẫn có thể bị regex trích và trở thành FP vì regex không hiểu ngữ
cảnh.

## Giới hạn

- Chỉ `--config C1` được hỗ trợ; C2–C4 trả lỗi rõ ràng.
- CLI chỉ đọc file cục bộ và không mở URL có trong văn bản.
- Kết quả smoke hiện tại không đại diện cho khoảng 40 báo cáo thật hoặc bước đồng thuận hai người gán nhãn.
- Baseline hiện chưa trích IPv6 trong văn bản; mẫu tổng hợp giữ ca này làm FN quan sát được, không sửa thuật
  toán hoặc nhãn để tăng điểm.
