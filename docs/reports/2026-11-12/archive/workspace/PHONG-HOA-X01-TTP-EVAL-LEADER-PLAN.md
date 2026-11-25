# X01-TTP-EVAL — nghiệm thu nghiên cứu và kế hoạch Leader

Ngày 11/11/2026. Owner triển khai: CTI AI Agent, Sol medium đã cấu hình, một người/một tree, không giao tiếp bot khác hoặc helper.

## Nghiệm thu tài liệu

PASS nghiên cứu sau R1–R5 của request `6bb305a8-0910-4317-a5d2-f8ee5aeb6204`, với đính chính rõ dưới đây. Đây chưa phải bằng chứng implementation/test evaluator đã chạy.

- Research: `PHONG-HOA-X01-TTP-EVAL-RESEARCH.md`, SHA-256 `D69532C609B6C40C943282DF488BAFAC1A2F5FFF282E71BC7DB85D9FF97A97C3`.
- Brief: `PHONG-HOA-X01-TTP-EVAL-IMPLEMENTATION-BRIEF.md`, SHA-256 `736273EFDB884BC602EDBAB43E046F6BB0801EFE0C81BA8F39C39DF2B09BE78D`.
- Đã đọc hai tài liệu đầy đủ và kiểm hash; nguồn `cti-x01-ttp-audit` đúng HEAD `b896ad343a2e9876559649b1182c0a4feeecaaa5`, branch `feat/x01-ttp-audit-20261111`, status/diff-check sạch. Target/branch mới và ADR0006 chưa tồn tại khi kiểm.
- R1 đóng: research 9/40/77, brief 23/36 — một adapter invocation/document; normal 1, retry thành công 2, fallback 2 provider calls; audit không thêm calls.
- R2 đóng: research 75, brief 23/37 — tái dùng cùng text universal newline, phân biệt hash raw bytes và UTF-8 text, kiểm Unicode/CRLF/CR.
- R3 đóng: research 71, brief 22/38 — pin có exact keyset, bounded binary read, JSON/type strict, lỗi an toàn trước provider/writer.
- R4 đóng: research 40–71, brief 23–24 — API optional, schema 1.0/1.1, full projection, keyset/count invariants và giới hạn ý nghĩa.
- R5 đóng: brief 11–15/50–59 — tree/base/scope/ADR/PROGRESS, demo, checks và evidence đủ giao độc lập.

## Đính chính của Leader, ưu tiên hơn câu chữ mâu thuẫn trong research/brief/review cũ

1. SnapshotPin có **7 trường**, không phải tám. Tôi đã đếm sai trong review R3; code thật `extractor/phonghoa_extractor/attack_catalog.py:17–24` xác nhận exact keyset:
   `kind, version, sha256, source_url, release_tag, commit, provenance`.
   Parser và catalog projection đều dùng đúng bảy tên này; không phát minh trường thứ tám. Giữ strict native types và semantics do public loader kiểm.
2. Biên kích thước pin: JSON hợp lệ được đệm whitespace tới **16 KiB** phải được nhận nếu mọi validation khác đạt; **16 KiB + 1 byte** phải bị từ chối. Đọc tối đa limit+1; không nhầm cả hai biên đều invalid.
3. Ví dụ research là minh họa. Chuỗi `Đoạn mô tả` có 10 code points; nếu đặt tại đầu source thì span là `[0,10]`, không phải `[0,12]`. Implementation luôn dùng span từ audit công khai; không hardcode ví dụ.
4. Cụm “không provider/model attempt” chỉ có nghĩa audit không gây **thêm** attempt. Các attempt do retry/fallback hiện hữu vẫn giữ nguyên.
5. Khi so baseline khác HEAD, chỉ bỏ `evaluator.git_ref`; giữ toàn bộ phần còn lại. Cờ đầy đủ tương thích; việc không nhận abbreviation là thay đổi đã nêu.

## Giao triển khai

Root: `$WORKSPACE`.
Source chỉ đọc: `$WORKSPACE\cti-x01-ttp-audit`.
Base: `b896ad343a2e9876559649b1182c0a4feeecaaa5`.
Tạo worktree mới `$WORKSPACE\cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`. Kiểm lại source/ref/status và target ownership trước thao tác; không ghi chồng tree lạ.

Đọc AGENTS.md/spec liên quan trên đúng base, research và implementation brief đã ghim ở trên. Áp dụng toàn bộ contract/matrix của brief, với đính chính Leader ưu tiên. Tái sử dụng audit/catalog/adapter đã nghiệm thu; không nghiên cứu hoặc viết lại chúng.

Phạm vi sửa trong tree mới:
- `extractor/eval/run.py`
- `extractor/tests/test_eval_cli.py`
- `extractor/eval/README.md`
- `docs/PROGRESS.md`
- ADR mới `docs/adr/0006-x01-evaluator-technique-audit.md`
- `extractor/tests/test_ttp_audit.py` chỉ nếu test seam công khai cần.

Mục tiêu: thêm opt-in `--ttp-audit --attack-snapshot --attack-pin` cho C2/C3; defaults giữ schema1.0, enabled schema1.1; audit đúng source/provenance, immutable result, count đầy đủ, không đổi IOC prediction/score/eligibility/retry. Mọi technique vẫn semantic unverified và operational_draft_eligible=false. C4 vẫn từ chối. Không coi active catalog hoặc matched quote là ngữ nghĩa TTP đúng.

Bảo vệ output/input alias (resolve/samefile, hardlink/symlink khi khả dụng); lỗi không thay output cũ/input và không rò path/nội dung. Duy trì writer atomic. Không thêm dependency, network/download, LLM thật, DB/W05, UI, OpenCTI, lab, cloud, secret, push/PR/merge/deploy. Không sửa RUNS hoặc báo cáo/probe Leader; không sửa fixture baseline, adapter/audit/catalog/grounding, official pin/asset, ADR0005.

## Chạy và bàn giao

Tự thực hiện nghiên cứu đã chốt → RED → GREEN → regression liên quan → lint/format/diff → local Conventional Commit → evidence; không dừng xin duyệt giữa các bước đã giao. Nếu blocker thật ngoài scope, trả bằng chứng và phần đã làm.

Interpreter tuyệt đối: `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`; cwd target. Dùng UTF-8 stdout/stderr. Các fixture/provider hoàn toàn giả lập offline.

Chạy đúng sáu file regression: test_eval_cli.py, test_ttp_audit.py, test_attack_catalog.py, test_llm_adapter.py, test_grounding.py, test_evaluate.py dưới extractor/tests. Ruff check/format mọi Python đổi và git diff --check base..HEAD. Không lặp full suite/official suite/UI build không liên quan.

Demo C2/C3 synthetic-smoke với responses `extractor/eval/fixtures/c2c3`, TLP:CLEAR, snapshot `extractor/attack/fixtures/synthetic-catalog.json`, pin tạm đúng hash/provenance. Thêm semantic fixture tạm để demo không chỉ []. Chứng minh deterministic on/off và attempts; không thay baseline fixture.

Report: `$WORKSPACE\PHONG-HOA-X01-TTP-EVAL-RESULT.md`.
Evidence: `$WORKSPACE\x01-ttp-eval-evidence\`.
Ghi base/HEAD/branch/status trước-sau/diff, từng lệnh cwd/exit/count, RED/GREEN, demo artifact và manifest SHA-256, từng acceptance PASS/FAIL/UNVERIFIED. Giữ tree sạch và branch để Leader review độc lập. Không gọi self-review là review độc lập.

## Tiếp tục và giới hạn

Đã kiểm các cuộc đang mở một lần trước ghi sổ/giao việc: không Leader khác đang sửa Phong Hỏa. Đọc lịch tiếp tục lúc 09:53 ICT: enabled, kỳ kế 09:56; giữ vì dự án active. Receipt giao việc chỉ chứng minh đã nhận, không chứng minh worker đang chạy hay code hoàn thành. Leader review kết quả trả về và nối bước nhỏ tiếp theo theo spec sau nghiệm thu; semantic truth/model/corpus/C4/RAG/lab/production còn UNVERIFIED.
