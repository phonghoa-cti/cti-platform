# X01-C4-ADAPTER-IMPLEMENT — kế hoạch đã chốt, 11/11/2026

## Nghiệm thu nghiên cứu R1–R3

Chấp nhận research/contract từ request `2666e676-a79f-4903-922b-ecec4b064278`, thread `197da947-ee04-451c-9210-0df23d3720cd`. Đây là nghiệm thu tài liệu để giao triển khai, không phải C4 đã chạy.

- Research `PHONG-HOA-X01-C4-ADAPTER-RESEARCH.md`, SHA-256 `D9A780B2F8946DC37486E0EE1B0FFC9AB2166CF77A4B7ED3A56E5BE0CCBB92EB`.
- Brief `PHONG-HOA-X01-C4-ADAPTER-IMPLEMENTATION-BRIEF.md`, SHA-256 `F4DDD6ADAC856BF151ECF722D597CC4E3E8E043028BD1A440A5CCEEABE1492AB`.
- Leader đã đọc cả hai file, đối chiếu chữ ký public audit/retriever, snapshot serializer và result adapter. Hash khớp báo cáo; Git source đúng HEAD/branch, status sạch; các lệnh kiểm exit 0.
- R1 đóng: allowlist có audit và test; config C4 được giữ thật; semantic item vẫn đúng bốn khóa, wrapper gọi audit 0 lần, demo/caller composition gọi riêng.
- R2 đóng: metadata exact, trạng thái thành công/fallback phân biệt; không raw_iocs/query/context trong result C4; IOC candidate không nâng quyền semantic.
- R3 đóng: C4 UTF-8/source bound, lỗi theo public retriever, unsafe provider trước generate, terminal attempt 2 có đúng 2 calls, không fallback.
- Đã kiểm một lần các cuộc đang mở và lịch dự phòng lúc 12:09 Việt Nam: chỉ Leader hiện tại hoạt động trong luồng này, AI Agent rảnh; lịch dự phòng vẫn bật, lần gần nhất 11:56 trả NOTHING NEW. Không tạo lịch/worker trùng.

## Người làm, điểm bắt đầu và quyền sửa

Task `X01-C4-ADAPTER-IMPLEMENT`, owner CTI AI Agent, Sol medium. Một worker, không giao tiếp bot khác. Làm liên tục trong phạm vi từ preflight tới kiểm thử, commit và evidence; Leader nghiệm thu độc lập khi kết quả quay về.

Root tuyệt đối: `$WORKSPACE`.

- Source chỉ đọc: `root\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, base `d97f96362edcd92e87fc69cfa20a563109cec550`.
- Target được tạo: `root\cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`, đúng base trên. Leader đã kiểm target và branch chưa có; worker kiểm lại trước tạo. Nếu có dữ liệu lạ, không reset/xóa/ghi đè.
- Đọc AGENTS.md, PROGRESS, spec X01, ADR 0007 tại source/target; dùng research + implementation brief đã hash ở trên. Kế hoạch này chốt các chi tiết thực thi bên dưới.
- Chỉ 7 file allowlist trong brief. Source, RUNS, các tài liệu review/plan/research ngoài repo và pin/asset/dependency giữ nguyên. Không sửa CLI/evaluator/reporter/W05/UI.
- Không push/PR/merge/deploy, không model/cloud/network integration/secret/DB/listener/lab. Không cần cài thêm dependency hoặc venv.

## Chi tiết để tránh suy diễn khi code

Giữ phương án B và một vòng retry/consume/fallback chung. C4 gọi public `retrieve_techniques` đúng một lần sau base/TLP checks; C2/C3 không retrieval. Không thêm lần gọi provider để tạo query hay audit. Invariant về knowledge áp dụng request do public entry point tạo; không thêm validation constructor làm đổi C2/C3 cũ.

`RetrievalResult` không có trường snapshot đủ sáu khóa ở root; `results` có thể rỗng. Lấy schema/snapshot từ JSON context do retriever vừa tạo (hoặc pin đã validate trong catalog), không lấy `results[0]`, không parse STIX lần hai. Schema context hiện là `"1.0"`; SHA-256 lowercase và byte_length lấy đúng UTF-8 của nguyên context. Không serialize lại context trước gửi vì có thể đổi byte/hash/budget. C4 request dùng prompt version `extractor-v1-c4-context-v1`.

C4 result tái dùng các trường base C3, thay config/prompt và thêm đúng `attack_context` theo research. `warnings=[]`, `mock_only=true`, provider fake_offline/egress=false như cũ. Model completed có model_items_used=true; regex_fallback có false và semantic list rỗng. Cờ top-level eligible giữ convention C3 cho candidate IOC, từng IOC vẫn theo keep/status hiện có; không coi cờ đó là quyền ghi hay bằng chứng mọi IOC đúng. TechniqueAudit luôn unverified/ineligible. Ba cờ context requested/retrieval_completed/provider_context_sent đều true trong result trả về; c4_adapter_completed chỉ true khi model_completed. Terminal errors không tạo result.

ProviderRequest/text/context bất biến. Cùng request object được dùng qua retry. ScriptedProvider giữ hành vi copy input response list và consume responses của nó; recorder không sửa list đầu vào. Prompt document phải nói rõ report/knowledge là dữ liệu không tin cậy; chỉ report là evidence. Lát này chưa có prompt compiler hoặc model thực để chứng minh chống injection.

## TDD và kiểm tra cần thiết

Theo ma trận research/brief: viết test mới, giữ log RED đúng lý do rồi GREEN. Bổ sung các điểm biên trong cùng hai file test được phép: query/token/Unicode, zero-match với provenance đầy đủ, context-only IOC/evidence không được grounded/matched, source đúng 1 MiB và vượt một byte, surrogate, type bool/list/dict, bounds/error precedence khi nhiều input cùng sai; retry-success, exception/invalid response exhaustion, terminal ở lần đầu và lần hai; unsafe provider không generate; exact result/semantic keys và audit composition.

So C2/C3 trước/sau bằng payload/script tổng hợp deterministic hoặc golden assertions có kiểm toàn artifact: model success, retry-success và fallback, không chỉ kiểm vài field. Chỉ phép mở rộng config C4 trong audit, mọi kiểm source/mode/item/quote/catalog cũ phải còn nguyên.

Interpreter đã có (không dùng PATH): `root\cti-platform-start\.venv\Scripts\python.exe`; cwd target, PYTHONPATH gồm target/extractor và target/core, UTF-8. Dùng `-X utf8 -B`; pytest `-p no:cacheprovider -o addopts= -q` và JUnit XML ngoài repo để có tổng số/skip rõ.

Scoped regression chạy một lượt sau GREEN:

- `extractor/tests/test_llm_adapter.py`
- `extractor/tests/test_ttp_audit.py`
- `extractor/tests/test_attack_retrieval.py`
- `extractor/tests/test_attack_catalog.py`
- `extractor/tests/test_grounding.py`
- `extractor/tests/test_llm_cli.py`
- `extractor/tests/test_evaluate.py`
- `extractor/tests/test_eval_cli.py`
- `extractor/tests/test_eval_report.py`

Bốn file cuối kiểm consumers C1–C3 của shared adapter/audit, không mở tính năng C4 cho CLI/evaluator. Không cần lặp full repo/official asset/UI suite nếu không có failure hay concern mới. Ruff check/format-check bốn file Python thay đổi; `git diff --check base..HEAD`; direct demo wrapper → recorded request → public audit từ cùng report. Giữ synthetic evidence, không report CTI thật. Không nhận fake test là model quality.

## Hoàn tất và bàn giao

Self-review diff theo contract trước commit; sửa mọi finding trong phạm vi, ghi nhận kết quả. Cập nhật ADR/PROGRESS tiếng Việt. Commit Conventional Commit cục bộ, giữ branch/worktree sạch; source phải vẫn sạch đúng base. Nếu lỗi cùng nguyên nhân sau hai cách thử, trả blocker cụ thể và evidence, không mở rộng scope.

Report `root\PHONG-HOA-X01-C4-ADAPTER-RESULT.md`; evidence `root\x01-c4-adapter-evidence\`. Trả exact commands/exit/test counts/skips, RED→GREEN, demo JSON, source/target status trước/sau, base/HEAD/branch, diff stat, manifest SHA-256 đã tự kiểm và giới hạn. Cho biết test nào chạy tại HEAD nào; không gộp kết quả cũ thành test mới.

Điều kiện nghiệm thu: 7-file scope đúng, request context/hash/source separation và calls đúng, public audit C4 dùng report gốc, C1–C3 regression đạt, không đổi source/asset/dependency, code+evidence có thể kiểm độc lập. Sau nghiệm thu, Leader chọn lát evaluation C4 tiếp theo từ nghiên cứu phù hợp; model/corpus thật, semantic quality, lab/production chưa được xác minh.
