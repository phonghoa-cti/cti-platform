# X01-TTP-EVAL-NEXT — brief triển khai cho CTI AI Agent

Ngày 11/11/2026. Owner đề xuất: **CTI AI Agent, Sol medium, một tree riêng**.

## Mục tiêu

Thêm audit TTP **opt-in** vào JSON artifact C2/C3 offline để người xem đối chiếu từng technique với đúng source hash, quote/span và catalog ATT&CK đã pin. Không chấm TTP semantics và không đổi bất cứ phép chấm IOC nào.

## Điểm xuất phát và phạm vi

- Root tuyệt đối: `$WORKSPACE`; source chỉ đọc tuyệt đối: `$WORKSPACE\cti-x01-ttp-audit`.
- Exact base: `b896ad343a2e9876559649b1182c0a4feeecaaa5`, branch nguồn `feat/x01-ttp-audit-20261111`.
- Target tuyệt đối: `$WORKSPACE\cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`; chỉ tạo/dùng sau khi xác minh ownership, base và `git status --short` sạch; không dùng tree tồn tại chưa xác minh.
- Có thể sửa: `extractor/eval/run.py`, `extractor/tests/test_eval_cli.py`, `extractor/eval/README.md`, `docs/PROGRESS.md`, và ADR mới `docs/adr/0006-x01-evaluator-technique-audit.md` nếu chưa có.
- Chỉ khi test seam công khai thật sự cần: `extractor/tests/test_ttp_audit.py`. Không sửa `llm_adapter.py`, `ttp_audit.py`, `attack_catalog.py`, dataset, pin/asset official, ADR0005, dependency hoặc provider fixture baseline.
- Không network/download/cài dependency/LLM/DB/SQLite/W05/OpenCTI/lab/push/merge/deploy. Không thêm C4/RAG, corpus, metric semantic hay gọi provider thêm.

## Thiết kế bắt buộc

1. Giữ `--config` hiện có. Thêm `--ttp-audit` (`store_true`), `--attack-snapshot PATH`, `--attack-pin PATH` trong cùng CLI.
2. C2/C3 chỉ nhận audit khi **cả ba** cờ hiện diện; không audit thì hai path đều phải `None`. C1 từ chối mọi cờ mới; C4 vẫn từ chối trước. Sai tổ hợp là stderr usage an toàn, exit 2, không tạo output. Set `allow_abbrev=False`: đây cố ý từ chối long-option rút gọn, không phải cam kết CLI byte-compatible cho abbreviation cũ.
3. Parse `--attack-pin` binary bound 16 KiB + 1, UTF-8 strict/no BOM, JSON strict exact eight keys `kind`, `version`, `sha256`, `source_url`, `release_tag`, `commit`, `provenance`. Dùng `object_pairs_hook` reject duplicate ở mọi object, `parse_constant` reject nonfinite, dùng recursion/error guard để reject deep/numeric failure. Dataclass không validate annotation: parser phải kiểm native exact `str` và `str|None` đúng loại pin, không `str()`/trim/default/bool-number coercion. Bọc lỗi thành code nội bộ không path/nội dung. `load_catalog(snapshot, pin)` đúng **một lần** sau kiểm cờ/an toàn và trước document loop; pin invalid không gọi provider/writer.
4. Public evaluator giữ signature cũ, chỉ thêm keyword-only `attack_catalog: AttackCatalog | None = None`; `None` disabled, sai type fail **trước** provider. Library không tự đọc file/load pin. Trong `evaluate_llm_dataset`, giữ một `adapter_result = run_extraction(...)`/document. Khi audit enabled, gọi `audit_techniques(adapter_result=adapter_result, source_text=text, catalog=attack_catalog)` sau adapter; serialize dataclass sang JSON scalar/list mà không mutate adapter/audit result. Reuse chính text đã đọc: reader hiện hữu universal-newline dịch CRLF/CR thành LF, không đọc lại/đổi `newline=''`/normalize. Audit thêm zero provider calls: normal=1, retry-completed=2, two retryable failures/fallback=2; nonretryable/refusal abort/no output theo policy cũ.
5. Disabled giữ root `schema_version="1.0"` và không field mới; enabled root `schema_version="1.1"`, thêm top-level `ttp_audit` catalog/provenance/counts và `documents[].ttp_audit`. Catalog đúng tám pin fields đã public/validate. Counts exact keysets, zero explicit and invariants theo research: `technique_items`; quote matched/missing/not_found/ambiguous; catalog active/inactive/unknown/not_checked; mỗi map sum=technique_items, duplicate theo item/index. Không thêm `ttp` score/F1/rate; limitations nói audit chỉ consistency và semantic TTP/C4 chưa đánh giá.
6. Mở rộng `_ensure_output_safe` (hoặc helper) để protect tất cả regular input files: dataset, response fixture, snapshot, pin. Resolve paths và `samefile` cho file tồn tại để từ chối inside/alias/hardlink/symlink; không được overwrite input. Duy trì `_write_json_atomic`; không gọi nó nếu loader/audit bất kỳ document nào lỗi.
7. Giữ lỗi runtime C2/C3 ở `Lỗi: offline_eval_failed`, exit 1, không traceback/nội dung report/fixture/snapshot/pin/path. Catch chính xác `AttackCatalogError`, `TtpAuditError`, JSON/OSError/Unicode errors theo cần thiết; không nuốt `KeyboardInterrupt`/`SystemExit`. Giữ stdout success JSON hiện có.

## TDD acceptance matrix

Viết test đỏ trước, sau đó implementation. Mỗi criterion phải PASS/FAIL/UNVERIFIED kèm lệnh/exit/số test.

| Nhóm | Phải chứng minh |
|---|---|
| Default compatibility | C1/C2/C3 không audit giữ byte-identical với baseline fixture/output cũ **trừ** `evaluator.git_ref` khi HEAD khác; C4 exit 2; IOC score, prediction, provider attempts, draft eligibility không đổi |
| Opt-in C2/C3 | Public `load_catalog` với fixture synthetic, public `run_extraction`/fixture provider và public `audit_techniques`; document output có hash/source/quote/span/catalog pin/provenance; C2 raw/C3 grounding vẫn nguyên |
| One load/no extra provider | monkeypatch/count seam: catalog load một lần/run; audit on/off không tăng provider calls. Prove normal completed=1, retry-completed=2, two retryable failures/fallback=2 and audit=[]; không network |
| Audit data | valid empty semantic, fallback, mixed malware/actor, duplicate technique/index order; quote missing/not found/ambiguous; fixture `write_bytes` với emoji/CRLF/CR/NFC/NFD prove universal-newline text/hash/span and raw bytes hash khác text hash |
| Error/refusal | missing/partial/wrong config flags exit 2; invalid pin 16KiB/16KiB+1, UTF-8/BOM/duplicate/nonfinite/deep/extra/missing/type, asset/hash mismatch, malformed projection/source mismatch/audit error exit 1, marker không lộ stderr; nonretryable/refusal no output |
| Output safety | output old bytes giữ nguyên khi tất cả failure ở trên; reject output inside/alias/hardlink/symlink to dataset/responses/snapshot/pin; inputs unchanged |
| Determinism | two outputs cùng checkout/input byte-identical; `json` uses UTF-8/non-ASCII, sorted deterministic keys/newline; counts are counts only, no `precision`, `recall`, `f1`, or rate under TTP |

Không chạy lại toàn official suite chỉ vì không đổi loader. Regression tối thiểu đúng vùng: `test_eval_cli.py`, `test_ttp_audit.py`, `test_attack_catalog.py`, `test_llm_adapter.py`, `test_grounding.py`, `test_evaluate.py`. Nếu sửa scope khác thì bổ sung test liên quan, không tự mở rộng scope.

## Lệnh bắt buộc và bằng chứng

Từ cwd tree mới, dùng chính interpreter sau (không dùng Python PATH):

```powershell
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -m pytest extractor/tests/test_eval_cli.py extractor/tests/test_ttp_audit.py extractor/tests/test_attack_catalog.py extractor/tests/test_llm_adapter.py extractor/tests/test_grounding.py extractor/tests/test_evaluate.py
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -m ruff check <mọi-file-Python-thực-đổi>
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -m ruff format --check <mọi-file-Python-thực-đổi>
git diff --check b896ad343a2e9876559649b1182c0a4feeecaaa5..HEAD
```

Chạy thêm demo local C2 và C3 với `synthetic-smoke`, responses baseline `extractor/eval/fixtures/c2c3`, TLP:CLEAR, snapshot có thật `extractor/attack/fixtures/synthetic-catalog.json` và pin tạm tạo từ chính hash/provenance fixture. Thêm demo/test temporary semantic items để chứng minh không chỉ `[]`. Ghi raw stdout/stderr/cwd/command/exit, artifact SHA-256 và manifest input tại evidence. Không tạo/ghi output dưới dataset/responses/snapshot/pin. Chỉ dùng official v20.1 nếu asset đã có local và pin khớp; không download để làm demo.

## Điều không được tuyên bố

PASS ở đây chỉ là audit/evaluator offline. Không tuyên bố semantic TTP, F1/precision/recall TTP, chất lượng model, C4/RAG, model/cloud, W05/draft write, OpenCTI, lab hay production. Báo cáo tuyệt đối: `$WORKSPACE\PHONG-HOA-X01-TTP-EVAL-RESULT.md`; evidence: `$WORKSPACE\x01-ttp-eval-evidence\`. Kết quả cần trả: base/HEAD, diff thống kê, status trước-sau, file đổi, từng lệnh + exit/count, demo artifact/manifest hash, local Conventional Commit và UNVERIFIED còn lại.
