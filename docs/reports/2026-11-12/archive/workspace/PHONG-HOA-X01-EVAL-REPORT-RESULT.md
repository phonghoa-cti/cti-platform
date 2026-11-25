# X01-EVAL-REPORT-IMPLEMENT — kết quả

Ngày 11/11/2026. **PASS phạm vi reporter offline synthetic đã chạy; các ranh giới production vẫn UNVERIFIED.**

## Kết quả và khả năng tái sử dụng

Đã triển khai phương án nghiên cứu được Leader duyệt: reporter `stdlib-only` tách khỏi evaluator, dùng lại
artifact/metrics hiện có thay vì thêm dependency bảng hoặc sửa producer. JSON stdlib được bổ sung duplicate-key,
nonfinite, depth/collection/string/size bounds; `os.link` dùng cho publish no-clobber và `os.replace` chỉ dùng
khi có `--overwrite`. Không gọi model, mạng, catalog loader hoặc DB.

Reporter nhận một đến ba artifact C1/C2/C3 schema 1.0 hoặc C2/C3 schema 1.1, kiểm exact projection, cohort,
aggregate/mode metrics và TTP consistency counts trước khi xuất Markdown deterministic. C1 document không bị
ép có `config`; C3 luôn ghi rõ grounded model candidates + regex, không phải model-only. Provenance có SHA-256
đúng bytes input đã parse; không render path, IOC, quote, URL hoặc free-text từ artifact.

## Git và phạm vi file

- Worktree: `cti-x01-eval-report`
- Branch: `feat/x01-eval-report-20261111`
- Base: `984bd2136872f4c5fba4118e33cf02b5ca615f2d`
- Commit local: `b765b8602785cee98b697f4c6319c7f17447741c`
- Commit message: `feat: add deterministic X01 evaluation reporter`
- Diff: 4 file, `+1298/-0`
- File: `extractor/eval/report.py`, `extractor/tests/test_eval_report.py`, `extractor/eval/README.md`,
  `docs/PROGRESS.md`
- Target status sau commit: sạch.
- Source read-only vẫn sạch tại `984bd2136872f4c5fba4118e33cf02b5ca615f2d`.

Không sửa evaluator/score/core/adapter/catalog/dataset/lock/dependency/artifact cũ, RUNS hoặc tài liệu Leader.

## TDD và checks fresh

- RED đầu: `32 failed`, đúng vì `extractor/eval/report.py` chưa tồn tại.
- RED còn bắt được lỗi `0 == False` của Python trong policy; implementation chuyển sang kiểm type bool chính xác.
- Reporter post-commit: `38 passed`, exit 0.
- `extractor/tests/test_eval_cli.py` post-commit: `64 passed`, exit 0.
- Ruff check: exit 0, `All checks passed!`.
- Ruff format check: exit 0, 2 file đã format.
- `git diff --check HEAD^ HEAD`: exit 0.
- Không chạy full suite theo brief; regression giới hạn ở evaluator CLI.

Test gồm C1/C2/C3 1.0, C2/C3 1.1 và official catalog metadata; zero denominator; aggregate/mode/TTP mismatch;
duplicate/nonfinite/huge/deep JSON; Markdown payload không render; safe argparse; alias/hardlink; sibling output;
no-clobber race; overwrite; lỗi trước commit; cleanup lỗi sau commit; hash/determinism và input bất biến.

## Demo fresh và hash

Demo dùng bản copy read-only của artifact synthetic đã có, không chỉnh baseline:

| Artifact/output | SHA-256 |
|---|---|
| `inputs/c1.json` | `8D4C217F95FB8A2B35DC4B8596A8D4D60E86501C61DAF7D778F0529675CDFD76` |
| `inputs/c2-audit.json` | `FD4A4669040499032E777A41B051826132354BB719B85EC309C5EBD212FB5443` |
| `inputs/c3-audit.json` | `4C50357744151BC036225CC14B7CA6ABC620E3C5A12DF6A6A5528E1DDE7ECD1D` |
| `demo-c1.md` | `F6441B2EBF0DACEF24287F02BD2797D847D1575480541E2B22D88906467EE3F3` |
| `demo-c23-audit.md` | `AA2DF9A4525679A907386E245EE0BA6079B7204C14C5186C5EB475C97BB4E66A` |

C1 và C2+C3 audit đều chạy lần đầu/rerun exit 0; từng output có SHA giống hệt sau `--overwrite`. Ba input có
SHA trước/sau không đổi. C2/C3 được đưa vào CLI theo thứ tự C3,C2 nhưng stdout/report vẫn sắp C2,C3.

## Evidence

- Thư mục: `x01-eval-report-evidence`
- Manifest: `x01-eval-report-evidence/manifest.sha256`
- Logs: `00-preflight.md`, `01-red-green.log`, `02-final-checks.log`, `03-demo.log`, `commands.md`
- Demo: `demo-c1.md`, `demo-c23-audit.md`
- Inputs: `inputs/c1.json`, `inputs/c2-audit.json`, `inputs/c3-audit.json`

## UNVERIFIED

- Chất lượng model/corpus thật và corpus hai người gán nhãn.
- Semantic truth của TTP; counts chỉ kiểm consistency source/quote/catalog.
- C4/RAG, latency, token/cost.
- W05, OpenCTI, HTTP/auth, browser, lab và production.
- Crash/power-loss durability và hostile concurrent directory mutation.

## Học thêm

- **No-clobber**: publish chỉ thành công nếu output chưa tồn tại, tránh ghi đè do race giữa kiểm tra và ghi.
- **Commit point**: thời điểm link/replace đã publish output; lỗi cleanup sau đó không được giả vờ rollback.
- **Projection validation**: chỉ nhận đúng envelope/schema đã chốt trước khi dùng dữ liệu không tin cậy.
- **Byte-deterministic**: cùng bytes input tạo cùng bytes output, không phụ thuộc timestamp, cwd hoặc thứ tự input.

## R1 — strict integer TTP counts

Review độc lập tại commit `b765b8602785cee98b697f4c6319c7f17447741c` phát hiện top-level TTP counts
chưa kiểm kiểu số nguyên trước khi so dict. Python coi bool/float tương đương integer, nên artifact sai kiểu vẫn
có thể được publish và `--overwrite` output cũ.

Đã sửa theo TDD và commit cục bộ:

- Commit R1: `d35f58dfa8de03827480e78d62153a75cc78365b`
- Message: `fix: reject noninteger TTP report counts`
- Diff R1: 2 file, `+70/-2`
- Validator kiểm exact keys rồi gọi integer check nghiêm ngặt cho `technique_items` và toàn bộ quote/catalog
  counts trước khi đối chiếu thống kê; không cast/coerce hoặc tự sửa input.
- Repo RED: 18 fail; GREEN: 18 pass cho 9 count paths x bool/float, gồm output mới, `--overwrite` sentinel và
  input bytes bất biến.
- Nguyên probe Leader: 20/20 pass trước và sau commit; SHA-256 probe giữ nguyên
  `62C8FA1205A908103ED5A572E0C086B08A8CD5549E956E346CC7034395E2D8E7`.
- Reporter suite post-commit: 56 pass, exit 0.
- Ruff check/format và diff-check: exit 0.
- Target/source đều sạch; source vẫn tại `984bd2136872f4c5fba4118e33cf02b5ca615f2d`.

Evidence R1: `x01-eval-report-evidence/rework-r1/`; manifest: `rework-r1/manifest.sha256`.

R1 không thay đổi các ranh giới UNVERIFIED đã liệt kê: model/corpus thật, semantic TTP, C4/RAG, W05,
OpenCTI, lab/production và crash/power-loss durability.
