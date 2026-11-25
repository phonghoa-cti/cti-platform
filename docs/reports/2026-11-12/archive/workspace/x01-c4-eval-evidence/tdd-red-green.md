# X01-C4-EVAL — RED/GREEN đã quan sát

Ngày chạy: 11/11/2026. Interpreter: `cti-platform-start\.venv\Scripts\python.exe` (Python 3.12.13).

| Vòng | Lệnh rút gọn | RED quan sát | GREEN |
|---|---|---|---|
| Manifest/evaluator/writer | `pytest -q test_c4_eval_contract.py` | exit 1, 12 failed; thiếu `load_c4_query_manifest`, `evaluate_c4_dataset`, writer C4 | 12 passed, sau đó mở rộng thành 15 passed |
| CLI C4 | `pytest -q test_eval_cli.py -k "c4_cli or c4_flag or c4_rejects_ttp"` | exit 1, 2 failed; C4 chưa nhận query-manifest/contract flags | 3 passed |
| Reporter | `pytest -q test_eval_report.py -k c4` | exit 1, 2 failed; C4-only và C3.1+C4 bị từ chối | 11 passed |
| Preflight | test `test_c4_preflights_all_documents_before_first_generate` | exit 1; `provider_loads == 2`, yêu cầu 0 khi document cuối lỗi | 1 passed sau khi chuyển provider construction sau toàn bộ document input |
| Schema-before-publish | test `test_c4_writer_validates_exact_schema_before_publish` | exit 1; writer không raise với artifact thiếu field | 1 passed sau khi tái dùng strict C4 validator trước serialize/publish |

Failure integration được phát hiện sau đó: CLI subprocess thiếu repo root nên import `extractor.eval.report` thất bại.
Nguyên nhân được tái hiện bằng test CLI đơn; sửa sang runtime path `eval.report`. Verification sau sửa: 16 passed
(test CLI liên quan + toàn bộ contract), rồi bộ bắt buộc 291/291 passed.

Đây là bằng chứng TDD/contract bằng fixture tổng hợp, không phải bằng chứng chất lượng model hoặc RAG.
