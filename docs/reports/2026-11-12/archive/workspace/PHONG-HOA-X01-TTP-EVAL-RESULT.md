# X01-TTP-EVAL — kết quả triển khai

Ngày 11/11/2026. Kết luận: **PASS cục bộ/offline** theo brief; không phải bằng chứng model/lab/production.

## Git và phạm vi

- Source chỉ đọc giữ nguyên, sạch: `cti-x01-ttp-audit`, `b896ad343a2e9876559649b1182c0a4feeecaaa5`.
- Target sạch: `cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`.
- Commit: `984bd2136872f4c5fba4118e33cf02b5ca615f2d` — `feat: add opt-in TTP audit to evaluator`.
- Diff: 5 file, `+687/-15`; chỉ `run.py`, test CLI, README, PROGRESS và ADR 0006 đúng scope.
- Không sửa audit/catalog/adapter/grounding, fixture baseline, dependency, RUNS, DB/UI/lab; không push/merge/deploy.

## Kết quả hành vi

| Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|
| Default compatibility | PASS | C2/C3 target bằng base sau khi chỉ bỏ `evaluator.git_ref`; schema 1.0, không field mới |
| Opt-in C2/C3 | PASS | schema 1.1, full per-item audit và pin/provenance 7 trường |
| One load/no extra provider | PASS | test seam xác nhận load 1 lần; attempts normal/retry/fallback = 1/2/2 |
| Audit data | PASS | empty/fallback/mixed/duplicate, Unicode code-point span, CRLF/CR→LF, NFC/NFD và counts exact |
| Pin parser | PASS | UTF-8 strict, duplicate/nonfinite/deep/key/type; padded 16 KiB nhận, 16 KiB+1 từ chối |
| Error/refusal | PASS | exit 1/2 đúng contract, output cũ giữ nguyên, stderr không lộ marker/path/traceback |
| Output safety | PASS | reject inside/alias/hardlink/symlink tới dataset/responses/snapshot/pin; input không đổi |
| Determinism | PASS | C2 và C3 audit rerun byte-identical; JSON UTF-8, sorted keys, newline cố định |
| TTP metrics/eligibility | PASS | chỉ counts; không TTP precision/recall/F1/rate; semantic unverified, draft false |

## Lệnh và exit

- Baseline exact base, sáu file: exit 0, `270 passed in 11.73s`.
- RED `test_eval_cli.py -q`: exit 1, `39 passed, 17 failed` đúng vì feature chưa có.
- Post-commit sáu file bắt buộc: exit 0, `295 passed in 19.34s` (lần fresh cuối).
- Ruff check hai Python đổi: exit 0, `All checks passed!`.
- Ruff format check hai Python đổi: exit 0, `2 files already formatted`.
- `git diff --check b896ad3..984bd21`: exit 0.
- Demo C2/C3: mỗi lệnh exit 0; 6 document; schema 1.1; 1 technique matched; attempts giữ `1,1,1,1,2,1`.

## Demo và hash

- Snapshot synthetic SHA-256: `05F5AF7BCF44F158DA47E3645BD44CF193D0FCA2B52B4D12A16FEE5827C9653F`.
- Pin tạm SHA-256: `5BBB0BD6A8399E88BCBE178EC10BDFF2638ECE5044F9C3239D7D75E5E7070CD2`.
- Demo C2 SHA-256: `FD4A4669040499032E777A41B051826132354BB719B85EC309C5EBD212FB5443`.
- Demo C3 SHA-256: `4C50357744151BC036225CC14B7CA6ABC620E3C5A12DF6A6A5528E1DDE7ECD1D`.
- Dataset manifest trong artifact: `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5`.
- Temporary response manifest: `5631818b600449cfda95e0d0fb0df25a1337831e4dd5e76b8d628970c2f27be8`.
- Evidence manifest (21 entries) SHA-256: `D5C7F75EF988F429D9CF88B8F66CA00DCD5E68D10C81993B122644E1AD19D759`.
- Evidence: `x01-ttp-eval-evidence/` gồm RED, log GREEN/Ruff, base/target compatibility, fixture tạm, pin và demo/rerun.

## UNVERIFIED

Semantic truth TTP, gold/corpus hai người gán nhãn, chất lượng model/provider thật, C4/RAG, W05/draft write,
OpenCTI, cloud, lab và production đều **UNVERIFIED**. Synthetic smoke chỉ chứng minh contract kỹ thuật offline.
