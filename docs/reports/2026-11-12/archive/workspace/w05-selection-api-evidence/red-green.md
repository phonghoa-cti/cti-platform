# W05 Selection API — TDD receipt

- Baseline: `pytest` theo `pytest.ini` → exit 0, 415 passed.
- Core RED: `extractor/tests/test_selection.py` → exit 1, 5 failed / 30 passed; thiếu composite read,
  list v2, decision snapshot result, version cap và typed missing-DB error.
- Core GREEN: cùng file → exit 0, 35 passed.
- HTTP RED: `portal_api/tests/test_w05_api.py -k v1_` → exit 1, 12 failed do bốn route v1 chưa tồn tại.
- HTTP GREEN mở rộng: cùng selection v1 matrix → exit 0, 26 passed / 88 deselected.
- Self-review RED: legacy decision trên DB thiếu trả 503 thay vì contract cũ 404 → exit 1, 1 failed.
- Self-review GREEN và targeted cuối sau format: selection + API cũ/mới → exit 0, 150 passed.
- Full Python cuối sau format: exit 0, 447 passed; JUnit `full-python-final-postformat.xml`.
- Ruff changed Python: check exit 0; format-check exit 0. `git diff --check`: exit 0.
- Demo tổng hợp in-process: exit 0; `demo-summary.json`. Cleanup: `DEMO_TEMP_LEFT=0`.
