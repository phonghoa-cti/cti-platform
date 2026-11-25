# Đánh giá extractor C1/C2/C3/C4 ngoại tuyến

Evaluator chạy trên `synthetic-smoke` gồm sáu văn bản tự tạo. C1 dùng regex hiện có; C2/C3 dùng
`ScriptedProvider` và fixture tổng hợp trong `fixtures/c2c3`. Không có model thật, mạng, key, SQLite, OpenCTI
hoặc W05.

C4 dùng lại chính response fixture C2/C3, thêm query manifest explicit trong `fixtures/c4`, snapshot ATT&CK
và pin đã review. Retrieval chạy đúng một lần cho mỗi document trước khi adapter giả lập generate; raw query và
raw context không được ghi vào artifact.

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

python extractor/eval/run.py --config C4 `
  --dataset extractor/dataset/synthetic-smoke `
  --responses-dir extractor/eval/fixtures/c2c3 --tlp TLP:CLEAR `
  --query-manifest extractor/eval/fixtures/c4/query-manifest.json `
  --attack-snapshot extractor/attack/fixtures/synthetic-catalog.json `
  --attack-pin path/to/reviewed-pin.json `
  --output x01-c4-smoke-result.json
```

C1 không nhận `--responses-dir`/`--tlp`. C2/C3 bắt buộc cả hai cờ; fixture phải có đúng một file `<id>.json`
cho mỗi document và chỉ được cấu hình `destination=fake_offline`, `egress=false`.

### Bật audit technique ATT&CK

C2/C3 nhận thêm audit tùy chọn khi cả ba cờ cùng xuất hiện:

```powershell
python extractor/eval/run.py --config C2 `
  --dataset extractor/dataset/synthetic-smoke `
  --responses-dir extractor/eval/fixtures/c2c3 --tlp TLP:CLEAR `
  --ttp-audit `
  --attack-snapshot extractor/attack/fixtures/synthetic-catalog.json `
  --attack-pin path/to/reviewed-pin.json `
  --output x01-c2-audited-result.json
```

Pin là JSON UTF-8 tối đa 16 KiB với đúng bảy trường `kind`, `version`, `sha256`, `source_url`,
`release_tag`, `commit`, `provenance`. Snapshot và pin phải có sẵn tại máy; evaluator không tải mạng và
không chọn asset mặc định. C1 từ chối các cờ audit. C2/C3 cần đủ ba cờ audit. C4 không nhận `--ttp-audit`
nhưng bắt buộc snapshot, pin và query manifest vì audit source/quote/catalog luôn là một phần artifact 1.2.

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
- Khi audit tắt, contract C2/C3 vẫn là schema `1.0` và không có trường mới. Khi audit bật, schema là `1.1`,
  mỗi document có `ttp_audit`, còn root có pin/provenance và số đếm đầy đủ theo quote/catalog status.
- Audit dùng đúng chuỗi đã đọc bằng universal newline, nên CRLF/CR trở thành LF trước khi hash và tính span.
  Nó không gọi provider thêm, không thay prediction/score IOC và mọi technique vẫn `semantic_status=unverified`,
  `operational_draft_eligible=false`.
- C4 artifact schema `1.2` ghi digest query manifest, provenance context và audit TTP. `prediction_basis` phân biệt
  grounded model+regex với regex fallback; đây không phải metric model-only hoặc bằng chứng model dùng tri thức.
- C4 chỉ ghi output mới bằng temp + `fsync` + hardlink no-clobber. Output tồn tại hoặc race đều bị từ chối. Nếu
  cleanup temp lỗi sau commit point, CLI báo lỗi I/O nhưng giữ output đã publish; đó không phải rollback. Không
  tuyên bố crash durability hoặc chống tiến trình hostile sửa thư mục.

## Dựng báo cáo Markdown ngoại tuyến

Reporter đọc cohort cũ C1/C2/C3, hoặc C4 đơn, hoặc C3 audit schema 1.1 + C4 schema 1.2, rồi dựng Markdown
byte-deterministic:

```powershell
python extractor/eval/report.py `
  --input x01-c1-smoke-result.json `
  --input x01-c2-smoke-result.json `
  --input x01-c3-smoke-result.json `
  --output x01-eval-report.md
```

Reporter kiểm exact projection, cohort, aggregate/mode metrics và consistency counts của TTP schema 1.1 trước
khi ghi. Nó không chấm lại prediction, không đọc catalog, không gọi model/mạng/DB và không render IOC, quote,
đường dẫn hoặc URL từ input. Báo cáo luôn mang nhãn `SYNTHETIC SMOKE`; C3 được mô tả là model candidates
trộn regex rồi grounding, không phải metric model-only.

Với C4, reporter chỉ render digest query, provenance catalog, IOC aggregate/mode và consistency counts. Nó không
render query/context/evidence và luôn nói rõ retrieval/context transmission không chứng minh model dùng tri thức.

Mặc định output đang tồn tại bị từ chối và được giữ nguyên. `--overwrite` mới cho phép thay thế; output không
được alias input qua tên, symlink hoặc hardlink. Commit point là lúc link/replace thành công: lỗi trước đó không
được publish; lỗi dọn temp sau đó được báo là I/O nhưng output đã publish vẫn được giữ. Reporter không tuyên bố
chống power loss hoặc thay đổi thư mục đồng thời bởi tiến trình hostile.

Output C2/C3 chỉ được ghi atomic sau khi toàn bộ dataset/fixture xử lý thành công. Đường output nằm trong hoặc
alias/hardlink/symlink tới dataset/fixture bị từ chối; output cũ được giữ khi refusal, incomplete, fixture lỗi
hoặc provider không an toàn.

## Giới hạn

Đây là smoke kỹ thuật với fixture giả lập, không phải benchmark model, corpus thật hoặc tập gold hai người gán
nhãn. Số đếm audit chỉ chứng minh tính nhất quán source/quote/catalog, không phải precision/recall/F1 hay semantic
truth của TTP. Chất lượng model/RAG, semantic TTP, chi phí/token/latency, cloud/local model, corpus hai người gán
nhãn, lab, HTTP/auth, OpenCTI và bước
ghi/duyệt draft chưa được kiểm chứng.
