# RED — X01-TTP-EVAL

- CWD: `cti-x01-ttp-eval`
- Lệnh: Python dự án `-m pytest extractor/tests/test_eval_cli.py -q`
- Exit: `1`
- Kết quả quan sát: `39 passed, 17 failed`.
- Nguyên nhân đúng mục tiêu: CLI chưa nhận `--ttp-audit/--attack-snapshot/--attack-pin`; module chưa có
  `load_catalog`; `evaluate_llm_dataset` chưa nhận keyword-only `attack_catalog`.
- Không có lỗi baseline trước RED: sáu file regression trên exact base đã đạt `270 passed`, exit `0`.
