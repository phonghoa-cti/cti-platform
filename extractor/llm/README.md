# Adapter LLM C2/C3 ngoại tuyến

Lát cắt này kiểm hợp đồng giữa model và extractor mà không gọi model thật. `ScriptedProvider` chỉ phát lại
response tổng hợp đã nạp từ fixture; destination duy nhất là `fake_offline` và `egress` luôn phải là `false`.

## Luồng

1. Kiểm input, TLP và metadata provider trước khi gọi `generate`.
2. Kiểm trạng thái/envelope và schema `x01-extraction-response/1.0`.
3. C2 giữ IOC thô để đánh giá và luôn ghi `operational_draft_eligible=false`.
4. C3 trộn IOC regex với IOC giả lập rồi dùng `ground_iocs` để đối chiếu evidence/span và loại mục bịa.
5. Response lỗi schema/provider được thử lại đúng một lần; nếu vẫn lỗi thì fallback C1 regex.
6. Refusal/incomplete là lỗi không retry. CLI không tạo hoặc ghi đè artifact khi lỗi.

Schema giới hạn response đã serialize ở 1 MiB, tối đa 500 item mỗi danh sách và 8 KiB mỗi field. Metadata
provider/model/error tối đa 256 byte. Đây là giới hạn độ bền của mock, không phải số đo model.

## Demo

Chạy từ root repo với Python 3.12 và `PYTHONPATH=core;extractor`:

```powershell
python extractor\llm\run.py --config C2 --input extractor\llm\fixtures\report.txt `
  --response extractor\llm\fixtures\c2c3-response.json --language vi --tlp TLP:AMBER `
  --output c2-result.json

python extractor\llm\run.py --config C3 --input extractor\llm\fixtures\report.txt `
  --response extractor\llm\fixtures\c2c3-response.json --language vi --tlp TLP:AMBER `
  --output c3-result.json
```

Fixture dùng TLP:AMBER được phép vì provider không egress. Điều này không cho phép gửi AMBER lên cloud. Cũng
không được suy từ TLP:GREEN rằng một provider cloud thuộc community được phép chia sẻ.

## Giới hạn

- Không có SDK, key, cloud/local model, HTTP, SQLite, W05, OpenCTI, Hermes hay MCP.
- `mock_only=true` chỉ chứng minh schema/policy/retry/grounding hoạt động trên fixture tổng hợp.
- Techniques, malware và actors nằm trong `unverified_semantic_items`; chưa có ATT&CK RAG/grounding.
- Chưa chứng minh chất lượng model, corpus hai người gán nhãn hoặc chống mọi prompt injection.
