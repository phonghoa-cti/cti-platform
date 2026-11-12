# Lệnh và exit cuối R1–R5

Interpreter tuyệt đối: `cti-platform-start\.venv\Scripts\python.exe` (Python 3.12.13).

1. Probe Leader nguyên trạng trước sửa: 26 fail/1 pass, exit 1.
2. Repo regression mới trước sửa: 25 fail/9 pass, exit 1.
3. `pytest extractor/tests/test_gold_pilot.py -q -p no:cacheprovider --junitxml=...`:
   34 pass, exit 0.
4. `pytest x01-gold-pilot-leader-review/test_gold_pilot_leader.py -q -p no:cacheprovider
   --junitxml=...`: 27 pass, exit 0.
5. Ruff check và format-check đúng ba file Python: exit 0/0.
6. Diff-check rework và base: exit 0/0.
7. Writer semantics test chọn theo tên: exit 0.
8. Demo READY hai output: exit 0/0, byte-identical.
9. Demo NOT_READY: exit 2; INVALID: exit 2, không report.

Không chạy lại 349 regression cũ; không gọi model, mạng, DB, API, UI, lab, cloud hoặc production.
