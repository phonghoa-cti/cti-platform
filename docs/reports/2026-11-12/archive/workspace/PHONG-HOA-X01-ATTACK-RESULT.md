# X01-ATTACK — kết quả triển khai restricted catalog ngoại tuyến

Ngày: 11/11/2026 (Asia/Saigon)

## Kết quả

**PASS cục bộ trong phạm vi synthetic fixture.** Đã triển khai library tra cứu ATT&CK catalog giới hạn,
fixture tổng hợp, tài liệu/ADR và test fail-closed. Kết quả lookup chỉ xác nhận syntax/trạng thái trong
fixture; `semantic_status` luôn `unverified`, `operational_draft_eligible` luôn `false`.

- Tree: `$WORKSPACE/cti-x01-attack-offline`
- Branch: `feat/x01-attack-offline-20261111`
- Base: `8694fa7244d181f421bb2733ded7bf9ae218ea93`
- HEAD/commit cục bộ: `4e894c37df3ad53c16022909ae6df113dd89aa04`
- Commits: `a5663b12d37bcec6a75b639409096fe4943192fd` (implementation) và
  `4e894c37df3ad53c16022909ae6df113dd89aa04` (rework R1/R2).
- Diff tổng từ base: 8 file, `+1358/-1`; working tree sau commit sạch.
- Không push, PR, merge, deploy, cài package, gọi mạng/model, chạy lab hoặc đọc secret.

## Phần đã làm

- `attack_catalog.py`: pin synthetic strict, đọc có giới hạn, SHA-256 trước decode/parse, UTF-8/JSON strict,
  taxonomy lỗi an toàn, canonical version chính xác tới 18 chữ số thập phân, chống resurrection,
  `subtechnique-of` graph, mapping/record/result bất biến.
- `test_attack_catalog.py`: 104 test cho pin/type/bounds, I/O/hash/UTF-8/JSON, pattern/relationship, version,
  graph, lookup, immutability, no-egress và fixture commit.
- Fixture: một bundle hợp lệ active parent/child + inactive record; một fixture khóa JSON trùng có chủ đích.
- Tài liệu: README catalog/fixture, ADR 0004 và cập nhật `docs/PROGRESS.md` với giới hạn synthetic-only.
- Không thay đổi `llm_adapter.py`, `evaluate.py`, `grounding.py`, `store.py`, `drafts.py` (diff exit 0).

## TDD RED → GREEN

| Bước | Lệnh/kết quả | Exit | Bằng chứng |
|---|---|---:|---|
| RED import | `pytest extractor/tests/test_attack_catalog.py -q` thiếu module | 2 | `01-red.log` |
| RED hành vi | cùng file sau API skeleton; 87 failure do `NotImplementedError` | 1 | `02-red-behavior.log` |
| GREEN đầu | catalog còn 2 lỗi setup/depth taxonomy | 1 | `03-green-attempt.log` |
| GREEN catalog | test catalog ban đầu xanh | 0 | `04-green.log` |
| Fixture RED→GREEN | fixture chưa tồn tại → fixture hợp lệ/lỗi được đọc đúng | 1 → 0 | `05-fixture-red.log`, `06-fixture-green.log` |
| UUID policy RED→GREEN | bỏ ép UUID version ngoài canonical syntax | 1 → 0 | `10-uuid-policy-red.log`, `11-uuid-policy-green.log` |
| Final catalog sau rework | `pytest -o addopts='' -p no:cacheprovider extractor/tests/test_attack_catalog.py -q` → **104 passed** | 0 | `rework-r1-r2/10-final-catalog.log` |

## Kiểm chứng cuối

| Cổng | Kết quả mới chạy | Exit | Raw evidence |
|---|---|---:|---|
| Catalog sau rework | 104 passed / 1.72s | 0 | `rework-r1-r2/10-final-catalog.log` |
| Probe Leader bất biến | 13 passed / 0.27s; SHA-256 `688B…CC35` | 0 | `rework-r1-r2/11-final-leader-probe.log` |
| Regression đúng 5 file | 122 passed / 12.32s ở implementation; không chạy lại theo brief R1/R2 vì module liên quan không đổi | 0 | `final-regression.log` |
| Strict input focus | 36 passed, 53 deselected | 0 | `focus-strict-input.log` |
| Version focus | 6 passed, 83 deselected | 0 | `focus-version.log` |
| Graph focus | 16 passed, 73 deselected | 0 | `focus-graph.log` |
| Immutability + no-egress | 2 passed, 87 deselected | 0 | `focus-immutable-no-egress.log` |
| Ruff check | `All checks passed!` | 0 | `final-ruff-check.log` |
| Ruff format check | 2 file already formatted | 0 | `final-ruff-format.log` |
| Import origin + demo | module đúng tree; active/inactive/unknown/not_checked; unverified/false | 0 | `final-import-demo.log` |
| C4 | từ chối `C4 chưa được hỗ trợ`, không tạo output | 2 (mong đợi) | `final-c4.log` |
| Diff check/phạm vi cấm | diff check 0; 5 module cấm diff 0 | 0 | `final-summary.log`, `post-commit-git.log` |

Regression command:

```text
python -m pytest -o addopts='' extractor/tests/test_evaluate.py extractor/tests/test_eval_cli.py
  extractor/tests/test_llm_adapter.py extractor/tests/test_llm_cli.py extractor/tests/test_grounding.py -q
```

Không chạy full suite/UI/browser/lab theo phạm vi Leader: thay đổi chỉ ở library mới, fixture, test và docs;
5 file hồi quy đã được chỉ định thay cho full suite.

## Rework Leader R1/R2

- R1: exact JSON duplicate nay so sánh đệ quy theo kiểu JSON, bỏ qua thứ tự key object nhưng phân biệt
  `true` với `1` và `false` với `0`; vẫn giữ số JSON `1` và `1.0` là cùng giá trị.
- R2: đường dẫn có NUL được chuyển thành `AttackCatalogError("snapshot_io_error")`; `str`/`repr` không lộ
  marker hay exception nội bộ. Missing path và pin-invalid-before-I/O giữ nguyên contract.
- RED nguyên probe Leader: 9 failed / 4 passed, exit 1 (`rework-r1-r2/01-leader-probe-red.log`).
- RED regression repo: 9 failed / 4 passed, exit 1 (`rework-r1-r2/02-repo-regression-red.log`).
- GREEN regression repo: 13 passed, exit 0; GREEN nguyên probe: 13 passed, exit 0.
- Probe không bị sửa: SHA-256
  `688B06F844B0DAA96E902AB73A9737517D0D2975D04C850965F3C54C5BC9CC35` trước/sau.
- Rework diff từ reviewed HEAD `a5663b1`: 3 file, `+109/-3`; diff-check exit 0.
- Không chạy lại 122 regression/full/UI theo chỉ định vì adapter/eval/grounding không đổi.

## Fixture manifest

- `synthetic-catalog.json`: 2160 byte; SHA-256
  `5ed4cbf64b9472ae0fda013b5ed2d218c9be4a739a85a1cc670b1351d36bfaff`.
- `invalid-duplicate-key.json`: 303 byte; SHA-256
  `01b90c2bfd42ef1f1c911c23bd104e947a1c25da00962dc8f278123ba8973a57`.
- Provenance: `kind=synthetic`, `generator=hand-authored-test-fixture`,
  `purpose=restricted-catalog-test`; MITRE release/source/tag/commit đều null.
- Manifest máy đọc: `x01-attack-evidence/fixture-manifest.json`.

## Self-review

Review riêng sau GREEN, không dùng bot/subagent theo brief. Không còn finding Critical/Important/Minor trong
phạm vi. Đã refactor các hàm dài vượt quy ước AGENTS và đóng R1/R2 rồi chạy lại Ruff và 104 test. Self-review của tác giả
yếu hơn reviewer độc lập; Leader vẫn cần nghiệm thu diff/commit trước mọi tích hợp.

Declined to judge do ngoài phạm vi: snapshot/compatibility MITRE thật, licensing/NOTICE cho dữ liệu thật,
semantic correctness của TTP, adapter/C4/RAG, model/corpus thật, W05/OpenCTI/lab/production.

## UNVERIFIED — không được suy ra từ kết quả này

- Chưa tải hoặc chạy snapshot MITRE ATT&CK thật; chưa chứng minh compatibility/version/license/NOTICE.
- Chưa tích hợp catalog vào adapter, grounding pipeline, evaluator C4 hoặc RAG.
- Chưa đánh giá semantic TTP bằng model/corpus hai người gán nhãn; không có precision/recall/F1 C4.
- Chưa nối W05/OpenCTI, chưa chạy lab, browser, production hoặc cloud/model thật.

## Đường dẫn bằng chứng

`$WORKSPACE/x01-attack-evidence`

## Học thêm

- **Fail-closed:** gặp dữ liệu mơ hồ thì từ chối thay vì đoán, giảm nguy cơ catalog sai đi tiếp vào pipeline.
- **Canonical version:** chọn bản hiện hành bằng thời điểm đã chuẩn hóa, không phụ thuộc thứ tự object đầu vào.
- **Immutable mapping:** bảng tra cứu bị khóa sau khi tạo, nên code gọi không thể âm thầm sửa catalog đã kiểm.
