# Kết quả X01/C1 ngoại tuyến

## Kết quả

PASS cho lát cắt C1 smoke ngoại tuyến: một lệnh dùng lại `phonghoa_core.extract.extract_iocs` và
`phonghoa_extractor.evaluate`, đọc 6 mẫu tổng hợp Việt/Anh rồi xuất JSON theo báo cáo, micro và loại IOC.

- Nhánh: `feat/x01-c1-offline-20261110`
- Base: `9cf935cddcb9f84bd8045cbd62f228121041d1a6`
- Commit: `c858990f372c0557e0ee3da8b1a8475149d77af4`
- File kết quả: `PHONG-HOA-X01-C1-SMOKE-RESULT.json`
- SHA-256 file kết quả: `8D4C217F95FB8A2B35DC4B8596A8D4D60E86501C61DAF7D778F0529675CDFD76`
- Dataset SHA-256 trong kết quả: `43fe0cab40d669fa0d2622349fcc9d34e05f2072c21939eeea4da49a08654557`

## Số đo trên mẫu tổng hợp

| Phạm vi | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Micro, 6 mẫu | 7 | 3 | 1 | 0.7000 | 0.8750 | 0.7778 |
| domain | 2 | 2 | 0 | 0.5000 | 1.0000 | 0.6667 |
| email | 1 | 1 | 0 | 0.5000 | 1.0000 | 0.6667 |
| ipv6 | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 |
| md5 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| sha1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| sha256 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| url | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

FP xuất hiện vì regex không hiểu vai trò victim/benign và giữ phân biệt hoa thường ở phần local của email. FN
là IPv6 có trong văn bản/nhãn nhưng baseline hiện chưa trích. Không sửa thuật toán hoặc nhãn để nâng điểm.
TTP có trạng thái `not_evaluated`, không được đưa điểm 0 vào kết quả.

## File thay đổi

- `extractor/eval/run.py`: CLI C1, kiểm cấu trúc dataset, trích IOC, chấm điểm và xuất JSON ổn định.
- `extractor/tests/test_eval_cli.py`: 7 test cho số đếm tính tay, tái hiện, input hỏng/mồ côi, dataset rỗng và C2.
- `extractor/dataset/synthetic-smoke/`: 6 mẫu tự tạo, 3 tiếng Việt + 3 tiếng Anh, gồm metadata và nhãn.
- `extractor/eval/README.md`: cách chạy, ý nghĩa chỉ số và giới hạn.
- `docs/PROGRESS.md`: trạng thái C1 và phần X01 còn thiếu.

## Kiểm chứng đã chạy

| Lệnh/kiểm tra | Kết quả |
|---|---|
| `.venv\\Scripts\\python.exe -m pytest` | exit 0, 81 passed |
| `python -m ruff check` trên 2 file Python đổi | exit 0 |
| `python -m ruff format --check` trên 2 file Python đổi | exit 0, 2 file đã đúng định dạng |
| Demo C1 hai lần cùng input | exit 0 cả hai, SHA-256 output giống nhau |
| Demo `--config C2` | exit 2, nêu chưa hỗ trợ, không tạo output |
| `git diff --check` | exit 0 |
| Quét import mạng trong CLI | không có `requests`, `urllib`, `httpx`, `socket`, `openai` |

Lệnh chạy lại từ gốc repo:

```powershell
.\.venv\Scripts\python.exe extractor\eval\run.py `
  --config C1 `
  --dataset extractor\dataset\synthetic-smoke `
  --output .\x01-c1-smoke-result.json
```

## Giới hạn và phần chưa kiểm chứng

- Đây là smoke test kỹ thuật trên 6 mẫu tự tạo, không phải benchmark, tập gold do hai người gán nhãn hoặc
  bằng chứng chất lượng cho luận văn.
- Chưa làm C2–C4, TTP, LLM, RAG, UI, OpenCTI hoặc toàn pipeline X01.
- Không gọi mạng, không dùng API key, Docker hoặc máy lab; do đó chưa có kết luận runtime/chất lượng trên lab.
- Không push, tạo PR, merge hoặc deploy.
- Tự review bởi tác giả theo brief không giao việc tiếp; chưa có review độc lập.

## Hoàn tác

Nhánh chưa được push/merge. Có thể tạo commit hoàn tác bằng `git revert
c858990f372c0557e0ee3da8b1a8475149d77af4`; không dùng reset phá hủy lịch sử.

## Học thêm

- **Smoke test**: phép chạy nhỏ để chứng minh đường đi kỹ thuật hoạt động, không chứng minh chất lượng trên dữ liệu thật.
- **Micro average**: cộng TP/FP/FN của mọi báo cáo trước rồi mới tính Precision/Recall/F1.
- **SHA-256**: dấu vân tay giúp xác nhận hai lần chạy dùng cùng input và tạo cùng nội dung output.
