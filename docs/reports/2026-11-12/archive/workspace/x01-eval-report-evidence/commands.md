# Commands

Các lệnh đều chạy từ worktree `cti-x01-eval-report` với Python tuyệt đối đã pin trong brief.

1. `pytest extractor/tests/test_eval_report.py -q -p no:cacheprovider` — RED rồi GREEN reporter.
2. `pytest extractor/tests/test_eval_cli.py -q -p no:cacheprovider` — regression evaluator CLI.
3. `ruff check extractor/eval/report.py extractor/tests/test_eval_report.py` — lint file đổi có mã.
4. `ruff format --check extractor/eval/report.py extractor/tests/test_eval_report.py` — format check.
5. `git diff --check HEAD^ HEAD` — whitespace/diff check commit.
6. `report.py --input inputs/c1.json --output demo-c1.md` — demo C1 schema 1.0.
7. `report.py --input inputs/c3-audit.json --input inputs/c2-audit.json --output demo-c23-audit.md` — demo C2+C3 schema 1.1, đồng thời chứng minh output sort theo config.
8. Lặp 6–7 với `--overwrite`, băm output và input — kiểm byte-identical và source bất biến.

Không chạy full suite theo brief; chỉ reporter target và `test_eval_cli.py` regression.
