# X01-C4-EVAL — review nghiên cứu/brief ngày 11/11/2026

Kết luận: giữ **phương án A, evaluator và reporter cùng một lát offline**, nhưng cần sửa R1–R4 trước khi giao code. Đây là review tài liệu và mã hiện có, không phải bằng chứng implementation/test C4 đã chạy.

Root: `$WORKSPACE`.

Source `root\cti-x01-c4-adapter`: HEAD `654443e6ede6557f0629fc0886ca56fff782b193`; status porcelain rỗng, `git diff --exit-code --quiet` exit 0 sau review. Không sửa source, không chạy test sản phẩm trong lượt review tài liệu.

Hai bản đã đọc và kiểm SHA-256:

- Research: `DBDF9B3ACAF03B4C8A35288BC871CF135B9AE87F46C82E8D7260E1F66768A4D5`.
- Implementation brief: `E7404008F4395E14324B9A8E8731CB01B1A53938FBD113E8B9E366A981A28235`.

## R1 — sửa thông tin nền và chốt compatibility

Research:43,53,57–59 và brief phần Flags/Reporter đang lệch source hoặc còn câu hỏi chưa giải quyết.

- `llm_adapter.py:216–240` chấp nhận đủ năm TLP với provider `fake_offline`, `egress=False`; `run.py:530` cũng có đủ năm nhãn. Chốt C4 CLI dùng đúng năm nhãn hiện hữu, chỉ dữ liệu tổng hợp, không mở egress. Bỏ diễn giải CLEAR/GREEN là giới hạn của adapter.
- `run.py:405` dùng literal `adapter_grounded_model_plus_regex`; C4 tái dùng đúng literal này khi model_completed, `regex_fallback` khi fallback.
- Chốt tập mới: **C4 schema 1.2 đơn lẻ**, hoặc **C3 schema 1.1 có audit + C4 schema 1.2**. Không C3 1.0, không C3 1.2, không C1/C2 trong cohort có C4. Cohort C1–C3 cũ giữ nguyên.
- `report.py:505` hiện từ chối mọi cohort khác schema. Thêm nhánh C4 rõ ràng, thêm thứ tự C4 sau C3; giữ thứ tự/validation/Markdown cũ. Không yêu cầu giữ nguyên toàn bộ CONFIG_ORDER.
- C3+C4 phải cùng dataset hash/count, fixture manifest, provider policy/mock_only, evaluator (chạy cả hai bằng cùng HEAD/Python), catalog projection. Ghép document theo ID duy nhất, so source hash, fixture hash, language, TLP từng ID; không yêu cầu query hash ở C3, không so prediction/result_mode vì đó là kết quả cần trình bày.
- Kiểm tương thích qua hai commit: C1 giữ bytes; C2/C3 chỉ được loại `evaluator.git_ref` khi so baseline, nêu rõ ngoại lệ này. Rerun tại cùng HEAD phải byte-identical. Markdown baseline dùng cùng input artifact cố định.

## R2 — input preflight, API và lỗi phải khả thi với code tái dùng

Brief chưa định nghĩa DTO/signature đủ cụ thể; câu “không tạo provider trước khi inputs pass” xung đột với loader fixture hiện trả ScriptedProvider.

- Định nghĩa chính xác parser và immutable DTO (kể cả field raw-byte digest và mapping bất biến); hàm public evaluator phải kiểm DTO/type/mapping, không tin dataclass được tự dựng. Chốt signature đầy đủ, thứ tự tham số và lỗi; không để `evaluate_c4_dataset(...)` làm hợp đồng duy nhất.
- Đọc manifest tối đa **16384+1 bytes**, chỉ chấp nhận <=16384; JSON/UTF-8 strict, no BOM/duplicate/nonfinite. Ghi rõ query không bị sửa; hashing là bytes của file, không phải JSON reserialize.
- Câu “non-empty query” chưa đủ: `_validate_query` tại `attack_retrieval.py:85` còn từ chối whitespace hoặc chuỗi không sinh token như `!!!`/`a`. Tái dùng validator này cho preflight, không chép tokenizer và không chạy retrieval thêm. Đây là phụ thuộc nội bộ được cho phép, không cần sửa module retrieval.
- Trước **generate đầu tiên**, validate toàn bộ mapping, pin/catalog, dataset metadata/labels/report và fixture shape; cho phép loader dựng ScriptedProvider trong preflight vì chưa gọi generate. Chốt lỗi của document sau cùng vẫn khiến tổng generate=0. Report dùng cùng chuỗi đã đọc/chuẩn hóa universal newline như C3; giới hạn C4 report 1 MiB UTF-8 và hash/source/span theo chuỗi thực gửi adapter. Không trộn raw-file hash với source-text hash.
- Giữ lookup/retrieval đúng một lần/document trong wrapper; không preflight retrieval. Chốt top_k=5, budget=4096 cho lát này, không thêm cờ tuning.
- Phân biệt input preflight với lỗi response/terminal lúc thực thi: lỗi terminal ở document sau có thể xảy ra sau các calls của document trước; không hứa tổng calls=0 cho loại lỗi này. Output vẫn chưa publish.

## R3 — output và schema C4 cần quyết định riêng, không gọi nhầm là hành vi sẵn có

Research:45 gọi writer hiện có là no-clobber, nhưng `run.py:508–519` dùng `os.replace`, ghi thay thế output. Reporter mới có chính sách riêng. Leader chốt:

- **C4 evaluator chỉ publish output mới, không ghi đè**, không thêm `--overwrite` trong lát này. Output đã tồn tại (kể cả cùng bytes) bị từ chối; race xuất hiện target khi publish cũng không được ghi đè. Ghi temp cùng thư mục, publish no-clobber qua `os.link`; nêu commit point, cleanup và lỗi trước/sau publish. Không đổi writer/hành vi CLI C1–C3. Reporter giữ `--overwrite` và contract đang có.
- Input bảo vệ gồm dataset, responses, query manifest, snapshot và pin; chặn alias samefile/hardlink và lexical/resolved path, kể cả output nằm trong dataset/responses. Chốt hành vi symlink/reparse, không tuyên bố chống hostile directory mutation hoặc crash/power loss. Kiểm lỗi không làm thay input/output cũ và cleanup temp thuộc lượt chạy.
- Liệt kê exact document keys, type/bounds và closed literals `limitations`; không chỉ “C3 envelope + ...”. Nêu cụ thể bool khác int, integer khác float/bool và kích thước đầu vào tương thích giới hạn reporter.
- `attack_context`: đúng 10 keys đã có; ba cờ requested/retrieval_completed/provider_context_sent phải là True; c4_adapter_completed đúng theo mode; context schema 1.0; SHA hex 64; byte_length integer dương <=4096; top_k=5, budget_bytes=4096. Snapshot đúng sáu keys như `attack_retrieval.py:168`, khớp projection sáu field tương ứng trong root catalog (catalog còn field provenance riêng).
- Chốt invariants model_completed/fallback theo adapter thực: attempts 1 hoặc 2 cho success, error_codes rỗng kể cả retry-success; fallback attempts=2, hai retryable codes, model_items_used=False, TTP list rỗng; document operational_draft_eligible=True theo C3/C4 nhưng từng technique audit luôn False/unverified. Không suy ra model quality từ cờ này.
- Audit source_sha256/config/pin phải khớp document/root, counts khớp document; context hash và report hash là hai đại lượng khác nhau. Không thể suy ra số retrieval hits hay knowledge use chỉ từ context hash/byte_length; zero-match kiểm bằng request recorder trong test, không bịa hit count trong reporter.
- Bổ sung ca âm cụ thể cho bool/float substitution, schema mix, document TLP/ID/source mismatch, catalog/context mismatch, oversized input, output-exists/race và terminal preservation. Không cần test implementation trong nhiệm vụ sửa tài liệu này.

## R4 — handoff tự đủ và nguồn có giới hạn

- Target cố định `root\cti-x01-c4-eval`; branch `feat/x01-c4-eval-20261111`, base giữ nguyên 654443e. Chỉ một worker CTI AI Agent/Sol medium, không giao tiếp bot khác.
- Chốt tên test/file/fixture được thêm; bỏ allowlist mở “test mới thật cần thiết”. Nếu cần ADR cho query policy/schema1.2/publish/cohort mới, chỉ định đúng một tên và đưa vào allowlist. Không sửa adapter/retriever/catalog/audit/fixtures cũ.
- Interpreter có thật: `root\cti-platform-start\.venv\Scripts\python.exe`; xác minh Python/dependencies và đặt PYTHONPATH từ target/core + target/extractor. Không dựa vào `.venv` chưa có của worktree mới hoặc Python trên PATH.
- Ghi đủ targeted/regression liên quan, Ruff check + format-check file thay đổi, diff-check base..HEAD, source/target status, demo C4 và C3+C4 cùng HEAD, commit local và manifest hash. Không lặp full repo theo thói quen.
- Output `root\PHONG-HOA-X01-C4-EVAL-RESULT.md`; evidence `root\x01-c4-eval-evidence\`. Bắt buộc ghi command/exit/count/ref, PASS/FAIL/UNVERIFIED; không push/PR/merge/deploy/model/network/lab.
- [RAGAS bản gốc](https://aclanthology.org/2024.eacl-demo.16.pdf) tách context relevance, faithfulness và answer relevance; đánh giá metrics bằng human judgments ở §4–5 và nêu giới hạn ở §8. “Không thay thế gold” nên ghi là quyết định áp dụng cho Phong Hỏa, không gán thành kết luận nguyên văn của bài. [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) hỗ trợ ghi assumptions/limitations/provenance, không chứng minh pipeline của dự án chạy đúng.

Research chỉ sửa đúng hai tài liệu đã giao, đối chiếu các quyết định trên thành contract/test matrix thống nhất, trả hash mới và Git nguồn trước/sau. Không sửa review này, ledger, code hoặc tạo worktree. Không có quyết định nào trong R1–R4 cần hỏi lại người dùng.
