# Kết quả AI-EVAL-IMPLEMENT — C2/C3 offline

## Kết luận

**PASS trong phạm vi synthetic/mock offline.** Evaluator giữ nguyên C1 và thêm C2 raw/C3 grounded bằng adapter
`fake_offline`; fallback được chấm thành nhóm riêng, refusal/incomplete/nonretryable dừng toàn run, output C2/C3
ghi atomic và bảo toàn input/output cũ khi lỗi.

Không gọi model thật, mạng, key, SQLite, OpenCTI, W05, lab hoặc cloud. Các điểm smoke dưới đây chỉ kiểm hợp
đồng kỹ thuật; không phải bằng chứng chất lượng LLM/extractor hay chống prompt injection.

## Git và phạm vi

- Tree: `cti-platform-ai-llm-adapter`
- Branch: `feat/x01-eval-c2c3-offline-20261111`
- Base: `ed24bd817de1e4633693d27f47e8e5fc629451ad`
- Commit: `8694fa7244d181f421bb2733ded7bf9ae218ea93`
- Diff từ base: 13 file, 837 dòng thêm, 94 dòng xóa; working tree sạch.
- R1 so với commit Leader review `4b74fbb`: 2 file, 49 dòng thêm, 1 dòng xóa.
- Thay đổi chỉ ở evaluator, fixture tổng hợp, parser fixture dùng chung, test liên quan, README và PROGRESS.
- Không sửa adapter orchestration/scorer/store/draft/portal/SQLite/RUNS; không push/PR/merge/deploy.

## Ma trận nghiệm thu

| Tiêu chí | Kết quả và bằng chứng |
|---|---|
| C1 regression | PASS — demo 6 tài liệu exit 0, byte-identical baseline, SHA-256 không đổi |
| C2 raw | PASS — raw prediction giữ hallucination/duplicate/defang; scorer canonicalize/deduplicate |
| Invalid IOC | PASS — regression chứng minh vẫn tăng FP tổng và bucket `invalid`, không bị bỏ im |
| C3 grounded | PASS — chỉ `keep=true` được chấm; item `keep=false` còn span/status/warning trong audit |
| C3 provenance | PASS — artifact nói rõ adapter trộn model candidate và regex trước grounding; không tuyên bố model-only |
| Empty gold/pred | PASS — TP/FP/FN và precision/recall/F1 đều 0, không NaN/crash |
| Fallback | PASS — retryable + invalid response thành `regex_fallback`, `model_items_used=false`, metric tách nhóm |
| Refusal/incomplete/nonretryable | PASS — exit 1, không retry evaluator, output cũ giữ nguyên, không traceback/raw marker |
| Fixture contract | PASS — thiếu/thừa/malformed/unsafe provider bị từ chối; language sai kiểu không traceback |
| Output safety | PASS — từ chối output trong dataset/responses và alias/hardlink/symlink tới input; ghi atomic |
| Determinism/provenance | PASS — C2/C3 lặp byte-identical; có dataset/manifest/source/fixture hash, TLP, config, policy, Python và Git ref |
| Adapter/CLI regressions | PASS — parser fixture dùng chung; adapter/CLI cũ cùng nằm trong 84 test đạt |

## R1 — validation `role`

- Đã kiểm kiểu `role` là chuỗi trước khi kiểm enum; không thêm blanket catch `TypeError`.
- C2 và C3 từ chối ổn định `list`, `dict`, `null`, boolean, number và enum lạ: exit 1, không traceback,
  không lộ marker nguồn và không ghi đè output cũ.
- Ba enum hợp lệ `attacker`, `victim`, `benign` tiếp tục được chấp nhận ở cả C2 và C3.
- RED: 4/18 ca mới lỗi đúng ở `list`/`dict` cho C2/C3; GREEN: 18/18 đạt sau sửa.
- Hậu commit: evaluator/C1 liên quan 43/43 đạt; C1 6 tài liệu byte-identical baseline.

## RED/GREEN và lệnh kiểm chứng

Môi trường: Python `3.12.13`, Ruff `0.17.4`; interpreter từ `cti-platform-start\.venv`, cwd/PYTHONPATH là
tree AI. Không cài hoặc sửa dependency.

| Lệnh/kiểm tra | Exit | Quan sát |
|---|---:|---|
| Baseline `pytest test_evaluate.py test_eval_cli.py -q` | 0 | 11/11 đạt trước sửa |
| RED `pytest test_eval_cli.py -q` | 1 | 11 lỗi/19 ca vì C2/C3 chưa được hỗ trợ |
| GREEN bước evaluator `pytest test_eval_cli.py -q` | 0 | 19/19 đạt |
| `pytest test_evaluate.py test_eval_cli.py test_llm_adapter.py test_llm_cli.py -q --junitxml=.../targeted.xml` | 0 | 84/84 đạt; 0 failure/error |
| `ruff check` trên evaluator/helper/CLI/test | 0 | All checks passed |
| `ruff format --check` cùng phạm vi | 0 | 5 file đúng format |
| `git diff --check HEAD` | 0 | Không lỗi whitespace |
| Demo C1 6 mẫu | 0 | Byte-identical baseline |
| Demo C2 6 mẫu + chạy lặp | 0/0 | Hai artifact byte-identical |
| Demo C3 6 mẫu + chạy lặp | 0/0 | Hai artifact byte-identical |
| R1 RED `pytest ... -k label_role` | 1 | 4 lỗi traceback ở list/dict C2/C3; 14 ca còn lại đạt |
| R1 GREEN `pytest ... -k label_role` | 0 | 18/18 đạt |
| R1 hậu commit `pytest test_evaluate.py test_eval_cli.py` | 0 | 43/43 đạt; 0 failure/error |
| R1 Ruff check / format / diff-check | 0/0/0 | 2 file đạt; không lỗi whitespace |

Không chạy full suite 282 theo addendum: thay đổi chỉ ở evaluator và parser fixture dùng chung; các test evaluator,
adapter và hai CLI liên quan đã chạy chung. Tự review toàn diff sau commit không còn finding; đây là self-review
theo brief cấm giao bot/agent khác và yếu hơn reviewer độc lập.

## Demo synthetic sau commit

| Config | Docs | TP/FP/FN | Mode | Ghi chú |
|---|---:|---:|---|---|
| C1 | 6 | 7/3/1 | regex baseline cũ | Shape/hash/byte giữ nguyên |
| C2 | 6 | 7/2/1 | 5 `model_completed`, 1 `regex_fallback` | Raw mock; hallucination tạo FP |
| C3 | 6 | 7/3/1 | 5 `model_completed`, 1 `regex_fallback` | 1 IOC bịa bị audit `keep=false`; regex cũng tạo candidate/FP |

Chênh lệch điểm C2/C3 không phải so sánh chất lượng model: C3 dùng thêm regex trước grounding theo adapter hiện
tại. Dataset SHA-256: `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5`.
Fixture manifest SHA-256: `e9dab94cbd16776ddad927295e9d24a237e79845a89e823fdf2e62c39ba8d441`.

## Artifact

Thư mục: `ai-eval-evidence`

| File | Byte | SHA-256 |
|---|---:|---|
| `c1-smoke.json` | 5068 | `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f` |
| `c2-smoke.json` | 11377 | `346abae5e8468196926bf095a5d2d40ad6ba7689643e0d7948e26aeea95a01a3` |
| `c3-smoke.json` | 13521 | `af74c26c07314a4d3376d38983ca59b0795c563f7751ac339120bb91d1a14d9a` |
| `targeted.xml` | 12066 | `3b6de13f1f5cd8ddbc9ff4c8b15f72244f39a33a53d3e7de208e3b70a99b08ac` |
| `WORK-LEDGER.md` | 1620 | `91190367d4fc80da84d75f7eaca6a886e50f3b0ee432ba70a3e89b85def64534` |
| `r1-targeted.xml` | 6016 | `23742e098916159ead451f0baaafc6a72d4ad0896a40d6062c940251d8ea8733` |
| `c1-r1.json` | 5068 | `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f` |

`c2-repeat.json` và `c3-repeat.json` được giữ làm bằng chứng byte-identical với artifact chính tương ứng.

## Chưa kiểm chứng

- Provider/model thật, SDK mapping, token/chi phí/latency và quyền destination: **UNVERIFIED**.
- Corpus CTI thật và tập nhãn hai người gán độc lập: **UNVERIFIED**.
- C4/TTP, prompt injection, HTTP/auth/OpenCTI, W05, lab và production: **UNVERIFIED / ngoài scope**.
- Không được dùng F1 synthetic này để tuyên bố chất lượng hoặc readiness production.
