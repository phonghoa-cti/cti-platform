# Đánh giá extractor C1/C2/C3 ngoại tuyến

Evaluator chạy trên `synthetic-smoke` gồm sáu văn bản tự tạo. C1 dùng regex hiện có; C2/C3 dùng
`ScriptedProvider` và fixture tổng hợp trong `fixtures/c2c3`. Không có model thật, mạng, key, SQLite, OpenCTI
hoặc W05.

## Chạy demo

Từ thư mục gốc repo, dùng Python của môi trường dự án:

```powershell
python extractor/eval/run.py --config C1 `
  --dataset extractor/dataset/synthetic-smoke --output x01-c1-smoke-result.json

python extractor/eval/run.py --config C2 `
  --dataset extractor/dataset/synthetic-smoke `
  --responses-dir extractor/eval/fixtures/c2c3 --tlp TLP:CLEAR `
  --output x01-c2-smoke-result.json

python extractor/eval/run.py --config C3 `
  --dataset extractor/dataset/synthetic-smoke `
  --responses-dir extractor/eval/fixtures/c2c3 --tlp TLP:CLEAR `
  --output x01-c3-smoke-result.json
```

C1 không nhận `--responses-dir`/`--tlp`. C2/C3 bắt buộc cả hai cờ; fixture phải có đúng một file `<id>.json`
cho mỗi document và chỉ được cấu hình `destination=fake_offline`, `egress=false`.

## Ý nghĩa output

- C1 giữ nguyên contract cũ: `micro`, `by_type`, `dataset_sha256`, `ttp.status=not_evaluated`.
- C2 chấm mọi `raw_iocs[].value`. IOC bịa hoặc không normalize được vẫn là FP; duplicate/defang/case được
  scorer hiện có canonicalize và khử trùng. Artifact luôn không đủ điều kiện draft vận hành.
- C3 chỉ chấm IOC `keep=true`; `grounding_audit` vẫn giữ item bị loại cùng span/status/warning. Adapter C3 trộn
  candidate model với regex trước grounding, nên điểm C3 không phải điểm riêng của model.
- `micro_by_result_mode` tách `model_completed` và `regex_fallback`; nhóm không có mẫu ghi
  `status=not_available`, không ghi metric 0 giả.
- C2/C3 có SHA-256 dataset, fixture manifest, source và từng fixture; policy provider, TLP, config, adapter mode,
  Python version và Git ref. Dataset/manifest hash dùng thứ tự relative path lexical, 4 byte big-endian cho độ
  dài path UTF-8, rồi path bytes và file bytes.
- JSON dùng key sort, newline cố định, không timestamp/random; cùng checkout/runtime và input cho byte-identical.

Output C2/C3 chỉ được ghi atomic sau khi toàn bộ dataset/fixture xử lý thành công. Đường output nằm trong hoặc
alias/hardlink/symlink tới dataset/fixture bị từ chối; output cũ được giữ khi refusal, incomplete, fixture lỗi
hoặc provider không an toàn.

## Giới hạn

Đây là smoke kỹ thuật với fixture giả lập, không phải benchmark model, corpus thật hoặc tập gold hai người gán
nhãn. F1 không chứng minh chất lượng LLM hay chống prompt injection. TTP/C4, chi phí/token/latency, cloud/local
model, lab, HTTP/auth, OpenCTI và bước ghi/duyệt draft chưa được kiểm chứng.
