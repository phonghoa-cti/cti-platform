# Brief triển khai AI-EVAL-NEXT — evaluator C2/C3 offline

## 1. Mục tiêu, owner và Git boundary

Mở rộng evaluator X01 để chấm C2/C3 trên **dataset/fixture tổng hợp**, dùng adapter offline đã nghiệm thu; C2 đo raw predictions, C3 đo giữ lại sau grounding. Không gọi model/mạng/SQLite/W05. Đây là brief, chưa phải implementation hay kết quả test.

| Mục | Giá trị bắt buộc |
|---|---|
| Owner | CTI AI Agent, Sol medium; một người/một tree; không giao tiếp tiếp bot khác |
| Repo/tree | `$WORKSPACE\cti-platform-ai-llm-adapter` |
| Base/branch | `ed24bd817de1e4633693d27f47e8e5fc629451ad`; `feat/x01-llm-adapter-offline-20261110` |
| Trước khi sửa | `git rev-parse HEAD` phải đúng SHA; `git status --porcelain=v1` phải sạch, nếu không dừng và báo thay đổi có trước |
| Không làm | Không push/PR/merge/deploy; không sửa `PHONG-HOA-RUNS.json`, W05, portal, store/draft/queue/SQLite, cloud/local model, key, HTTP, OpenCTI, C4/TTP |

## 2. File scope chính xác

| File | Thay đổi được phép |
|---|---|
| `extractor/eval/run.py` | Mở rộng CLI/evaluator C2/C3; giữ hành vi C1 và public output hiện có không đổi. Import `ScriptedProvider`, `ProviderResponse`, `run_extraction` trực tiếp từ `phonghoa_extractor.llm_adapter`. |
| `extractor/eval/README.md` | Ghi lệnh C1 cũ, C2/C3 smoke, fixture map, output/provenance và giới hạn. |
| `extractor/tests/test_eval_cli.py` | Thêm contract tests cho C2/C3; bảo toàn test C1. |
| `extractor/tests/test_evaluate.py` | Chỉ thêm test scorer nếu cần chứng minh normalize/empty/duplicate mà test hiện tại chưa bao phủ. |
| `extractor/eval/fixtures/c2c3/` | Fixture response tổng hợp mapping theo document id; không dùng CTI thật. |

Không sửa `extractor/phonghoa_extractor/llm_adapter.py` trừ khi evaluator không thể sử dụng public classes hiện có; nếu thật sự cần, chỉ thêm một helper thuần để parse fixture, có unit test, và báo Leader trước review. Không subprocess `extractor/llm/run.py`.

## 3. CLI/interface phải có

Giữ nguyên:

```powershell
.\.venv\Scripts\python.exe extractor\eval\run.py --config C1 --dataset extractor\dataset\synthetic-smoke --output .\x01-c1-smoke-result.json
```

Thêm C2/C3:

```powershell
.\.venv\Scripts\python.exe extractor\eval\run.py `
  --config C2 `
  --dataset extractor\dataset\synthetic-smoke `
  --responses-dir extractor\eval\fixtures\c2c3 `
  --tlp TLP:CLEAR `
  --output .\x01-c2-smoke-result.json
```

`--responses-dir` và `--tlp` bắt buộc với C2/C3, bị từ chối với C1. Fixture file là `<id>.json`, strict envelope giống `extractor/llm/run.py`:

```json
{"provider":{"name":"fake_offline","destination":"fake_offline","egress":false},"responses":[{"status":"completed","model_id":"scripted-v1","payload":{"iocs":[],"techniques":[],"malware":[],"actors":[]},"retryable":false,"error_code":null}]}
```

Vẫn chỉ nhận `metadata.synthetic=true`, `purpose=synthetic-smoke`, `language` trong `vi|en`. Không mở URL hay tự suy ra TLP từ raw metadata.

## 4. Thuật toán/output contract

1. Reuse validation/discovery/hash của C1. Với C2/C3, xác minh fixture IDs khớp text IDs trước khi xử lý; không có, thừa, malformed, provider không phải fake-offline hoặc `egress != false` => exit 1, không tạo/ghi đè output.
2. Mỗi document gọi `run_extraction(text, language, tlp, config, ScriptedProvider)` đúng một lần. Adapter quản lý retry 1 lần và fallback; evaluator không retry/provider call riêng.
3. **C2:** lấy `raw_iocs[].value` làm prediction. Bao gồm IOC bịa, duplicate/defang/case; `score_iocs()` làm canonicalize/deduplicate. `operational_draft_eligible` luôn false.
4. **C3:** giữ `iocs[]` có `keep=true` làm prediction; serialized mọi IOC grounded (cả `keep=false`, status/warning/span) vào per-doc audit. Không biến `keep=false` thành FP. `operational_draft_eligible` chỉ là cờ nối ứng viên, không ghi draft.
5. Dùng `score_iocs(predicted, gold)` và `micro_average` hiện có. Gold attacker-only; per-type chấm sau normalize/deduplicate như C1. Empty gold/prediction giữ TP/FP/FN và 0.0 theo `Score`, không thêm exception/NaN.
6. Giữ `result_mode`: đặt `regex_baseline` cho C1; với C2/C3 pass-through `model_completed`/`regex_fallback`. Aggregate ít nhất: `micro_all`, `micro_by_result_mode`; nếu group rỗng, value `{ "status": "not_available" }`, không phải metric 0.
7. Top-level C2/C3 thêm: `fixture_manifest_sha256`, `provider_policy`, `document_count`, `documents`, `micro_all`, `micro_by_result_mode`, `by_type`, `limitations`. Mỗi document phải gồm source SHA, fixture SHA, language/TLP, adapter `provider`, `attempts`, `result_mode`, `error_codes`, `model_items_used`, prediction/audit và score.
8. Dataset hash và fixture manifest hash theo relative path UTF-8 + length + bytes, thứ tự lexical. Serialize deterministic (`sort_keys=True`, newline, không timestamp/random). Cùng input/checkout phải byte-identical.

## 5. Acceptance matrix và TDD

Viết test thất bại trước implementation; chỉ chạy những test/bộ lệnh dưới đây sau thay đổi.

| Ca | Expected |
|---|---|
| C1 regression | C1 CLI/artifact cũ còn passing và không đòi `--responses-dir`/`--tlp` |
| C2 success | Raw grounded + hallucinated IOC đều xuất hiện prediction; hallucinated tạo FP; `model_completed`, `model_items_used=true`, không eligible draft |
| C3 success | Chỉ `keep=true` được chấm; hallucinated `keep=false` còn audit với status/warning và không thành FP |
| Normalize/duplicate | `EVIL[.]example`, `evil.example`, duplicate chỉ đếm một prediction |
| Empty gold/pred | Output deterministic counts 0 đúng `Score`; không NaN/crash |
| Fallback | Retryable error rồi lỗi/schema-invalid tạo `regex_fallback`, `model_items_used=false`, error codes; aggregate tách group |
| Refusal/incomplete | Không bị coi `model_completed`; fallback/typed result đúng contract |
| Fixture contract | missing/extra/malformed fixture, unsafe/non-fake egress, thiếu required C2 flag => exit 1, output không tồn tại/không bị thay |
| Determinism/provenance | Cùng dataset+fixture chạy hai lần byte-identical; hash fixture/dataset, SHA source/fixture có mặt |
| Rò dữ liệu | stderr lỗi không chứa raw text/IOC marker tổng hợp; không network/mock provider `egress=false` |

Lệnh tối thiểu sau implementation (ghi output, exit code và số test thật):

```powershell
.\.venv\Scripts\python.exe -m pytest extractor\tests\test_evaluate.py extractor\tests\test_eval_cli.py
.\.venv\Scripts\python.exe extractor\eval\run.py --config C2 --dataset extractor\dataset\synthetic-smoke --responses-dir extractor\eval\fixtures\c2c3 --tlp TLP:CLEAR --output .\x01-c2-smoke-result.json
.\.venv\Scripts\python.exe extractor\eval\run.py --config C3 --dataset extractor\dataset\synthetic-smoke --responses-dir extractor\eval\fixtures\c2c3 --tlp TLP:CLEAR --output .\x01-c3-smoke-result.json
```

## 6. Demo offline và báo cáo bàn giao

Demo dùng một fixture tổng hợp có IOC hiện trong text, IOC bịa, duplicate/defang và một fixture fallback. Trình bày C2 có FP của raw prediction; C3 cho thấy evidence/`keep=false`; sau đó chỉ ra `mock_only=true`, `destination=fake_offline`, `egress=false`. Không diễn giải F1 smoke là chất lượng model.

Báo về Leader: commit SHA; `git status`; files changed; từng tiêu chí PASS/FAIL/UNVERIFIED; lệnh/exit code/số test; đường dẫn+SHA-256 hai artifact demo; diff review note; và giới hạn (không model/corpus hai người gán/cloud/lab/W05). Chỉ cập nhật `docs/PROGRESS.md` nếu toàn bộ acceptance bắt buộc PASS và wording nói rõ mock/offline.
