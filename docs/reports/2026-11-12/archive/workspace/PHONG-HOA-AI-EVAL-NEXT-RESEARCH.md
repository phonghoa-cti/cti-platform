# AI-EVAL-NEXT — nối evaluator C2/C3 ngoại tuyến

Ngày đối chiếu: 11/11/2026 (Asia/Saigon)
Phạm vi: nghiên cứu/brief; **không sửa và không chạy mã**.
Tree đã đọc: `cti-platform-ai-llm-adapter`, branch `feat/x01-llm-adapter-offline-20261110`, commit `ed24bd817de1e4633693d27f47e8e5fc629451ad`; `git status --porcelain=v1` không in dòng nào (sạch lúc đọc).

## Kết luận

**Chọn C1 — mở rộng evaluator tập dữ liệu hiện có (`extractor/eval/run.py`) để gọi trực tiếp `run_extraction()` với `ScriptedProvider`, sau đó dùng lại `score_iocs()` và `micro_average()`.**

Lựa chọn này tạo một lệnh chấm duy nhất cho C1/C2/C3, không cần model/mạng/SQLite và không nhân đôi thuật toán normalize, đếm TP/FP/FN hay contract adapter. C2 chấm **raw model predictions** (kể cả IOC bịa); C3 chấm **chỉ IOC `keep=true` sau grounding/evidence**. Mỗi báo cáo và tổng kết đều phải ghi `result_mode` để không trộn `model_completed` với `regex_fallback` và không gọi số liệu fixture là chất lượng LLM.

## Hiện trạng và phần tái sử dụng đã kiểm

| Thành phần | Bằng chứng tại `ed24bd8` | Dùng lại | Giới hạn |
|---|---|---|---|
| Chấm IOC | `extractor/phonghoa_extractor/evaluate.py`: `_norm_ioc`, `score_iocs`, `micro_average` | Set normalized, chỉ gold `role=attacker`, Precision/Recall/F1 và empty-set = 0 | Chưa có breakdown model/fallback hay provenance C2/C3 |
| Dataset C1 | `extractor/eval/run.py` | Validate raw/meta/label, dataset SHA-256, per-doc/by-type/micro artifact | CLI chỉ cho C1; metadata hiện không mang TLP; không có fixture map C2/C3 |
| Adapter | `extractor/phonghoa_extractor/llm_adapter.py` | `ScriptedProvider`, `run_extraction`, schema/policy/retry/fallback, `raw_iocs` C2, `iocs` grounded C3, provenance provider/source | Không phải evaluator; C3 hiện có thể hợp nhất regex vào tập để grounding |
| CLI mock | `extractor/llm/run.py` | Contract fixture, atomic JSON, lỗi chung không lộ raw CTI | Chạy cho một input, không có gold/micro aggregate |
| Nhãn | `extractor/dataset/GUIDELINE.md` | Gold IOC chuẩn hóa, attacker-only; kế hoạch khoảng 40 báo cáo và hai người gán | `synthetic-smoke` 6 mẫu không phải corpus/benchmark; chưa có corpus hai người gán nhãn |

Adapter là code đã được Leader nghiệm thu phạm vi offline; nghiên cứu này **không chạy lại** test/CLI và không suy ra runtime mới từ việc đọc code.

## Đối chiếu ba cách nối

| Cách | Mô tả | Tái dùng | Hạn chế | Quyết định |
|---|---|---|---|---|
| **C1 — mở rộng `eval/run.py` (chọn)** | Thêm nhánh C2/C3 đọc fixture theo `document id`, gọi library adapter, rồi chấm tập đã chọn | Tối đa: validator dataset, artifact C1, scorer và adapter | Cần giữ C1 không đổi, thêm manifest/provenance và test fallback | Chọn: lát cắt nhỏ nhất, một CLI/evaluator chuẩn |
| C2 — evaluator mới `eval/c2c3.py` | CLI mới import loader/adapter; C1 giữ nguyên | Chỉ scorer và adapter | Nhân đôi discovery/validation/dataset hash/output; hai đường CLI dễ lệch | Không chọn |
| C3 — chấm các artifact JSON đã tạo | Tạo artifact qua `llm/run.py`, evaluator chỉ đọc artifact | Adapter CLI và scorer | Cần hai bước, mapping artifact-source/gold dễ sai; provenance/fallback bị tách và demo kém tái lập | Không chọn |

## Contract và metric được chốt

### Dataset, fixture và xác định đầu vào

- Vẫn dùng layout `raw/<id>.txt`, `raw/<id>.meta.json`, `labels/<id>.json` và kiểm tập id khép kín như C1.
- Với C2/C3, `--responses-dir` là bắt buộc; mỗi `raw/<id>.txt` cần đúng một `responses/<id>.json` theo envelope strict hiện hữu của `extractor/llm/run.py` (`provider`, `responses`). Không có/thừa/malformed fixture: lỗi input, exit khác 0, không tạo output.
- `--tlp` bắt buộc cho toàn bộ run C2/C3 (chỉ các giá trị canonical adapter nhận). Nó là provenance của smoke, **không** suy ra nhãn TLP của tài liệu thật. `--language` lấy từ metadata đã validate (`vi`/`en`); giá trị khác lỗi input.
- C2/C3 chỉ nhận metadata `synthetic=true`, `purpose=synthetic-smoke` ở lát cắt này. Không mở URL, không gửi network; provider phải có `destination=fake_offline`, `egress=false`.

### Tập dự đoán và đếm

| Config | Tập đưa vào `score_iocs()` | Bắt buộc ghi | Không được làm |
|---|---|---|---|
| C1 | IOC regex như đang có | `result_mode=regex_baseline` | Thay đổi điểm/shape C1 |
| C2 | `raw_iocs[].value` từ artifact adapter khi `model_completed`; cả IOC bịa, normalized/deduplicate chỉ trong scorer | `model_items_used`, `result_mode`, `error_codes`, `operational_draft_eligible=false` | Ground hoặc lọc evidence trước khi đếm FP; đưa vào draft |
| C3 | `iocs[]` có `keep=true`; `keep=false` giữ trong per-doc audit nhưng **không** tính dự đoán | `grounding` audit (status/warning/span), mode/error, `operational_draft_eligible` | Đếm item rejected thành FP hay xóa audit |

`score_iocs()` đã canonicalize qua `normalize()` rồi set hóa: duplicate/defang/case không thể nhân TP/FP. Gold chỉ gồm `attacker`; IOC `victim`/`benign` bị dự đoán vẫn là FP. `Score` hiện định nghĩa precision/recall/F1 = 0.0 nếu mẫu số bằng 0; evaluator phải giữ quy ước đó và báo counts để người đọc thấy empty gold/prediction, không diễn giải 0.0 là thất bại model.

Theo tài liệu scikit-learn, precision/recall/F-score cần chính sách rõ với trường hợp zero division; quy ước zero hiện có là quyết định deterministic của Phong Hỏa, không phải một mục tiêu chất lượng. [scikit-learn: precision/recall/F-score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)

### Fallback và provenance

- `model_completed` và `regex_fallback` là hai nhóm bắt buộc. Tổng `micro` phải tách `micro_by_result_mode`; chỉ `micro_model_completed` mới là số của payload scripted. Nếu không có document `model_completed`, trường đó là `not_available`, không ghi 0 hay kết luận về model.
- Refusal, incomplete, provider error, schema invalid sau retry và fixture lỗi **không phải** model success. Adapter chịu retry/fallback có cấu trúc; evaluator không tự retry thêm.
- Artifact top-level phải có: `schema_version`, `config`, `purpose=synthetic-smoke`, `dataset_sha256`, `fixture_manifest_sha256`, `evaluator` (commit/ref hoặc `not_recorded` khi không có Git metadata), `runner` (Python version), `provider_policy` (`fake_offline`, `egress=false`), `document_count`, per-doc results, counts/micro/by_type và `limitations`.
- Manifest hash được tính deterministically trên đường dẫn tương đối + bytes của fixture đã dùng, cùng cách hash dataset hiện hữu. Output sắp thứ tự document/id/type; không timestamp ngẫu nhiên. Chạy cùng checkout/input/fixture phải byte-identical, trừ trường provenance runtime được quyết định loại khỏi artifact.

### Ranh giới dữ liệu và an toàn CTI

TLP là hạn chế chia sẻ; FIRST TLP 2.0 không làm cloud provider thành đích được phép. Lát cắt chỉ fake-offline, do đó `egress=false` với mọi TLP. [FIRST TLP](https://www.first.org/tlp/). Nội dung báo cáo/model response là dữ liệu không tin cậy, không là chỉ thị gọi tool. Không ghi raw text vào stderr; demo chỉ dùng marker tổng hợp.

## Dữ liệu và bằng chứng còn thiếu

- 6 `synthetic-smoke` fixtures chỉ chứng minh plumbing/contract/repeatability; không chứng minh recall, F1, chống prompt injection hay chất lượng model thật.
- Chưa có provider/model/key, corpus bản quyền hợp lệ, log chi phí/độ trễ, test lab, HTTP/W05/OpenCTI hay SQLite.
- `GUIDELINE.md` mới quy hoạch khoảng 40 báo cáo, 5 báo cáo đầu hai người gán độc lập và thỏa thuận >=80%; chưa có bằng chứng đã thực hiện. Chỉ khi có corpus/provenance/licensing và hai người gán thì mới đề xuất đánh giá chất lượng khác; không tự đặt ngưỡng.
- TTP C4 không nằm trong lát cắt; MITRE ATT&CK về sau phải ghim snapshot/version/provenance, không gọi mạng lúc test. [MITRE ATT&CK — Working with ATT&CK](https://attack.mitre.org/resources/working-with-attack/)

## Khuyến nghị thực thi

Điều chỉnh (không tự xây evaluator mới): một worker AI Agent mở rộng C1 CLI theo contract trên, với fixture tổng hợp có một IOC grounded, một IOC bịa, duplicate/defang và empty sets. Giữ `extractor/llm/run.py` là CLI demo đơn-input; evaluator import thư viện adapter, không subprocess CLI. Đợi review diff/test trước khi ghi `docs/PROGRESS.md`; không hứa chất lượng model.
