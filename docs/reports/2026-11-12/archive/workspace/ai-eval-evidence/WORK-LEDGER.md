# AI-EVAL implementation ledger

- Plan: `PHONG-HOA-AI-EVAL-IMPLEMENTATION-BRIEF.md`; addendum ưu tiên.
- Base: `ed24bd817de1e4633693d27f47e8e5fc629451ad`.
- Branch: `feat/x01-eval-c2c3-offline-20261111`.
- Pre-flight: C1 baseline 11 test đạt, exit 0; demo 6 tài liệu SHA-256 `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f`.
- Shared interfaces: evaluator tiêu thụ `run_extraction`/`ScriptedProvider`; addendum yêu cầu parser fixture strict có thể dùng chung. Chọn helper thuần dùng chung để tránh hai contract parser lệch nhau; chi phí là phải chạy regression adapter CLI.
- Ruling: không thay C1 output/CLI path; mọi metadata mới chỉ có ở C2/C3, theo addendum.
- RED: `test_eval_cli.py` có 11 lỗi/19 ca, exit 1 vì C2/C3 và các cờ chưa được hỗ trợ.
- GREEN bước evaluator: `test_eval_cli.py` 19/19 đạt, exit 0.
- Review finding: parser fixture dùng chung có thể ảnh hưởng JSON lồng sâu của CLI cũ; regression mới đạt ngay trên helper, nên không cần sửa production thêm.
- C1 regression: artifact sau thay đổi byte-identical baseline, SHA-256 `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f`.
- Commit: `4b74fbb15bfe02fc499ada3ffe05f5dfa34f9120`.
- Final verification: 84/84 test đạt; Ruff check/format và diff check exit 0; C1/C2/C3 demo exit 0; C1 giữ byte-identical, C2/C3 repeat byte-identical.
- Final review: self-review vì brief cấm giao bot/agent khác; không còn finding Critical/Important/Minor trong phạm vi diff. Self-review yếu hơn reviewer độc lập.
