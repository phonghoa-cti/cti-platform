# X01-C4-RETRIEVAL-IMPLEMENT — kết quả

Ngày: 11/11/2026 (Asia/Saigon).

## Kết quả

**PASS** component lexical retrieval ATT&CK ngoại tuyến theo phạm vi Leader plan. Component dùng canonical
`load_catalog()` làm input, trả raw result frozen cùng JSON context có provenance và budget đo trên toàn envelope
UTF-8. Không gọi model, mạng, DB, API/UI/OpenCTI hoặc lab; không nối generator/C4 CLI.

- Source chỉ đọc: `cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`, HEAD
  `d35f58dfa8de03827480e78d62153a75cc78365b`, sạch trước/sau.
- Target: `cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`.
- Commit cục bộ: `4067598c87772dac88af309b01d127f748f369fd`
  (`feat: add offline ATT&CK retrieval context`).
- Target sạch sau commit; không push/PR/merge/deploy.
- Diff đúng 7 nhóm file: 7 file, `+729/-1`.
- Plan hash: `09982c6d37ee62d46da357a8936e58159cc329e668ae166d455f1050617852cb`.
- Research hash: `01a015a31fd4da21705accd38e594d0730f0bb8b337ee32199bac117a42150ee`.
- Implementation brief hash: `3584cf7c517149be47affbc46d5ab3e24afeb6b45ab96d241ea9a2effa5fdcc8`.

## Thay đổi

1. `TechniqueRecord.description` optional ở cuối dataclass; canonical version missing/empty thành `None`, present
   sai kiểu/null/surrogate/quá 32 KiB UTF-8 fail `invalid_attack_pattern`; không fallback description bản cũ.
2. Thêm `attack_retrieval.py`: tokenizer NFKC/casefold và regex Unicode đã chốt; score overlap, sort ID ổn định,
   loại inactive; guard catalog/record fail-closed; output frozen giữ `unverified`/`false`.
3. Context JSON compact có thứ tự field cố định, provenance snapshot, prefix result đúng item thực sự đưa vào
   context; chỉ snippet đầu được cắt theo code point, raw description không đổi; envelope/item không vừa trả
   `context_budget_exceeded`.
4. Test gồm fixture tổng hợp Việt/Anh qua public loader, malformed/no-mutation/no-I/O, exact fit/one-byte-short/
   multibyte/escape/zero-match/later-unfit, official description và regression C1–C3/audit/reporter.
5. Thêm ADR 0007 và cập nhật `docs/PROGRESS.md` với ranh giới chưa xác minh.

## TDD và kiểm chứng

| Kiểm tra | Kết quả | Bằng chứng |
|---|---:|---|
| RED ban đầu retriever chưa tồn tại | exit 2, collection error đúng nguyên nhân | `01-red.log` |
| RED catalog description | exit 1, 9 failure; 104 test cũ vẫn qua | `02-red-catalog.log` |
| Mutation later-unfit (đổi `break` thành `continue`) | exit 1; test bắt việc skip đảo rank, sau đó khôi phục | `10-mutation-later-unfit-red.log` |
| Scoped regression exact brief, có asset official | exit 0; 428/428, 0 skip | `11-final-scoped-regression.log` |
| Toàn bộ pytest repo | exit 0; 662/662, 0 skip | `12-final-full-pytest.log` |
| Ruff check 5 file scope | exit 0 | `13-final-ruff-check.log` |
| Ruff format check 5 file scope | exit 0 | `14-final-ruff-format-check.log` |
| `git diff --check` | exit 0 | `15-final-git-diff-check.log` |
| Demo official loader → retrieval → context | exit 0 sau khi đặt `PYTHONPATH=extractor` | `08-demo-rerun.log` |

Interpreter cho mọi test/lint/demo:
`cti-platform-start\.venv\Scripts\python.exe -X utf8 -B` (Python checkout-local). Scoped regression chạy đúng
8 file test trong brief với `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT` trỏ asset local; log có 428 dấu pass và không có
skip. Full suite chạy `-m pytest -q -p no:cacheprovider` với cùng asset.

Asset official trước/sau demo đều:

- bytes: `55,277,605`
- SHA-256: `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`

Demo official nạp 867 record; query English `phishing spearphishing` trả context 2,311 byte trong budget 4,096,
hash context `d6c61125291fe1bd601215149cab4ffcb3b59e876ced9c5a339d07d13b89adab`; rerun context/result byte-deterministic,
zero-match trả 0, provenance parsed khớp pin và raw description không đổi. Lần demo đầu exit 1 do Python stdin
chưa có đường import `extractor`; log `07-demo.log` được giữ, lần chạy lại sửa đúng môi trường và exit 0.

## PASS / FAIL / UNVERIFIED

### PASS

- Optional canonical description và backward-compatible builder.
- Lexical retrieval deterministic, immutable raw result và context JSON có budget UTF-8.
- Guard input/catalog/record, inactive exclusion, inert external text, no mutation/no I/O trong retriever.
- Official asset local đúng hash/kích thước, public loader chạy thật; acceptance không skip.
- Scoped regression, full repo tests, lint, format và diff-check đều exit 0.

### FAIL

- Không còn failure trong trạng thái commit. Hai RED/mutation failure và demo import failure ban đầu được giữ làm
  bằng chứng quá trình; nguyên nhân đã được sửa và kiểm lại bằng lệnh fresh.

### UNVERIFIED

- Chất lượng semantic/TTP, multilingual recall, corpus thật hai người gán nhãn và model/provider thật.
- Tích hợp context trước generation, full C4/RAG, token/cost/latency và model-context quality.
- W05/OpenCTI/API/UI, lab/runtime/production, release khác, NOTICE/chữ ký tag/commit.
- Component không biến ATT&CK knowledge thành report evidence và không cấp quyền ghi/duyệt/chặn.

## Rework R1 sau review Leader

Trạng thái cập nhật ngày 11/11/2026: **PASS R1**. Commit hiện hành thay cho HEAD implementation ban đầu:
`d97f96362edcd92e87fc69cfa20a563109cec550` (`fix: validate canonical ATT&CK description`). Commit nền trước
rework là `4067598c87772dac88af309b01d127f748f369fd`.

Review đã tái hiện đúng lỗi: `_parse_pattern()` từng validate description của mọi version trước canonical
selection. Rework giữ raw STIX trong `_PatternVersion`, dời `_description()` sang `_build_records()` sau khi
`_canonical_patterns()` đã chọn version hiện hành. Vì vậy description sai ở bản cũ không chặn bản mới hợp lệ;
description sai ở bản canonical vẫn fail `invalid_attack_pattern`; canonical missing/empty vẫn là `None` và
không fallback bản cũ. Không đổi retrieval, pin, fixture, lookup, lifecycle hay parent graph.

### TDD và kiểm chứng rework

| Kiểm tra rework | Kết quả | Bằng chứng dưới `rework-r1/` |
|---|---:|---|
| Repo regression mới, 5 loại description cũ × 2 thứ tự | RED 10 failed, exit 1 → GREEN 10 passed, exit 0 | `01-repo-red.log`, `02-repo-green.log` |
| Nguyên probe Leader | 18/18 passed, exit 0 | `08-final-leader-probe.log` |
| Hash probe trước/sau | cùng `d636c4ba3c2de1aa14139e11a015ca0b9179d6f9565bc384f704b6787f7409ab` | `08-final-leader-probe-meta.txt` |
| Catalog + official + retrieval | 211/211 passed, 0 skip, exit 0 | `09-final-three-file-regression.log` |
| Asset official trước/sau | cùng `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5` | `09-final-three-file-regression-meta.txt` |
| Ruff check / format check / diff-check | cả ba exit 0 | `10-final-ruff-check.log`, `11-final-ruff-format-check.log`, `12-final-git-diff-check.log` |

Diff rework: 2 file, `+30/-3`; chỉ `attack_catalog.py` và regression `test_attack_catalog.py`. Target và source
đều sạch sau commit; source vẫn ở `d35f58dfa8de03827480e78d62153a75cc78365b`. Không chạy lại full 662 hoặc
scoped 428: hai số đó là bằng chứng **trước rework**; theo brief rework chỉ chạy probe và ba file trực tiếp bị
ảnh hưởng. Không network/model/DB/lab/push/PR/merge/deploy.

UNVERIFIED sau rework không đổi: semantic/TTP quality, multilingual recall, model/full C4, corpus thật,
OpenCTI/lab/production.
