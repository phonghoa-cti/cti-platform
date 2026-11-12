# Kết quả X01-TTP-AUDIT-IMPLEMENT

Ngày: 11/11/2026 (Asia/Saigon).

## Kết luận

**PASS phạm vi implementation offline đã giao.** Module public `audit_techniques` đã nối kết quả thật của
`ScriptedProvider`/`run_extraction` C2 và C3 với source SHA binding, exact quote/code-point span và lookup
`AttackCatalog`. Mọi technique luôn `semantic_status="unverified"` và
`operational_draft_eligible=false`. Không gọi đây là semantic proof, C4 hay RAG.

Không có FAIL còn mở trong phạm vi. Đây là self-review; chưa có review độc lập của Leader/QA.

## Git và phạm vi

- Source chỉ đọc: `cti-x01-attack-official`, branch `feat/x01-attack-official-20261111`, HEAD
  `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`, status sạch trước/sau.
- Worktree: `cti-x01-ttp-audit`, branch `feat/x01-ttp-audit-20261111`.
- Commit local: `b896ad343a2e9876559649b1182c0a4feeecaaa5` —
  `feat: add offline ATT&CK technique audit`.
- Worktree status sau commit: sạch. Không push/PR/merge/deploy.
- Diff base..HEAD: 4 file, `+682/-0`.
  - `extractor/phonghoa_extractor/ttp_audit.py` (mới)
  - `extractor/tests/test_ttp_audit.py` (mới)
  - `docs/adr/0005-x01-offline-technique-audit.md` (mới)
  - `docs/PROGRESS.md` (cập nhật evidence/giới hạn)
- Không sửa adapter/catalog/grounding/evidence/evaluator/CLI/spec/dependency/fixture/RUNS/review/research.

## RED → GREEN và kiểm tra

Interpreter tuyệt đối:
`$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`
(Python 3.12.13).

| Cổng | Lệnh/tóm tắt | Exit | Kết quả |
|---|---|---:|---|
| RED | pytest `extractor/tests/test_ttp_audit.py` trước module | 1 | lỗi đúng mục tiêu: `ModuleNotFoundError: phonghoa_extractor.ttp_audit` |
| GREEN targeted | cùng pytest sau commit | 0 | 53 passed, 0 skipped, 0.14s |
| Regression bắt buộc | pytest 5 file adapter/catalog/grounding/evaluate/eval_cli | 0 | 217 passed, 0 skipped, 10.72s |
| Ruff check | 2 file Python đổi | 0 | All checks passed |
| Ruff format --check | 2 file Python đổi | 0 | 2 files already formatted |
| `git diff --check` | post-commit | 0 | sạch |
| Import path | import bằng checkout `extractor;core` | 0 | trỏ đúng `cti-x01-ttp-audit\extractor\phonghoa_extractor\ttp_audit.py` |

Không chạy full/official166 vì brief chốt không lặp compatibility suite official đã nghiệm thu riêng; đây là
SKIP có chủ đích, không tính PASS.

## Contract đã kiểm

- Source exact string, character/UTF-8 bounds, SHA shape và mismatch trước empty/fallback/output; có emoji,
  CRLF, NFC/NFD và code-point span.
- Projection fail-closed: exact native dict/list, schema/config/mock/provider/mode/flag/hash; semantic item
  thiếu/thừa/sai kiểu, unknown kind và encoding lỗi làm hỏng toàn call mà không rò marker.
- Bound trước lọc: 501 mixed items, malware/actor value/evidence quá 8192 byte, source quá 1 MiB.
- Quote literal: missing/not found/one match/overlap `aaa` trong `aaaa`/lặp CRLF; không normalize.
- Catalog độc lập: active/inactive/unknown/not_checked/subtechnique; reason precedence đúng contract.
- Mixed-list/duplicate giữ thứ tự và `item_index`; outer tuple, frozen record, scalar provenance; input/catalog
  không đổi.
- Fault-injection marker là dữ liệu; guard socket/SQLite/file không phát hiện side effect.

## Demo public C2/C3

Demo synthetic đi qua `ScriptedProvider -> run_extraction -> audit_techniques` cho cả C2/C3:

- `provider_calls_after_audit=1` ở mỗi config: audit không gọi provider thêm.
- `source_sha256=a23a19fbb81635fb0898c4168d02c46eebe52121f44b44fff6ffe488c08a6091`.
- `quote_status=matched`, `catalog_status=active`, pin `synthetic-audit-1`.
- Cả C2 và C3 đều `semantic_status=unverified`, `operational_draft_eligible=false`.

Lần chạy demo stdin đầu tiên exit 1 vì chưa đặt checkout `extractor/core` vào import path; chạy lại với đúng
checkout path exit 0. Đây là lỗi lệnh phụ trợ, không phải lỗi module/pytest.

## Evidence

Thư mục: `x01-ttp-audit-evidence\`.

- `00-red.log`: raw RED/cwd/interpreter/exit.
- `01-green-targeted.log`: GREEN post-commit.
- `02-regression.log`: đúng 5 file regression và ghi rõ skip official166.
- `03-quality-and-state.log`: Ruff/diff/import/Git/source status.
- `04-demo-c2-c3.json`: demo public adapter/audit và provenance.
- `MANIFEST.sha256`: hash từng artifact; verify 5/5 match.

SHA-256 của `MANIFEST.sha256`:
`6c7dbffda95c233ff32c6ae3e1fd74e34db1ebea5714658829534f432bc706e9`.

## UNVERIFIED

- Technique semantic truth và chất lượng model/TTP.
- C4/RAG, real model/provider, corpus/gold hai người gán nhãn, precision/recall/F1.
- W05/SQLite/API/UI/OpenCTI, TLP cloud authorization, lab và production.
- Review độc lập; Leader cần review exact commit/diff trước khi nhận.

## Học thêm

- **Source binding**: gắn output với SHA-256 của đúng bytes nguồn để tránh audit nhầm văn bản.
- **Code-point span**: offset tính theo ký tự Unicode của Python, không theo số byte UTF-8.
- **Fail-closed**: dữ liệu sai cấu trúc bị từ chối toàn bộ thay vì cố đoán/chuyển kiểu.
- **Post-hoc audit**: kiểm sau generation giúp phát hiện inconsistency, nhưng không biến lookup thành RAG hay
  chứng minh ngữ nghĩa.
