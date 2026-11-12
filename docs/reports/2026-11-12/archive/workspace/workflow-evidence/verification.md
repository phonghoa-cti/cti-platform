# WORKFLOW-GUARD verification evidence

Thời điểm kiểm: 10/11/2026, workspace Phong Hỏa. Không chạy mạng, không sửa repo `cti-platform-start`, không sửa `PHONG-HOA-RUNS.json`.

## TDD RED

Lệnh:

```powershell
cti-platform-start\.venv\Scripts\python.exe -m unittest workflow.test_check_continuation.ContinuationCliTests.test_active_project_with_all_children_accepted_plans_next -v
```

Quan sát trước khi có production code:

- `FAILED (failures=1)`
- `TEST_EXIT=1`
- Nguyên nhân đúng mong đợi: `workflow\check_continuation.py` chưa tồn tại.

## GREEN và kiểm tra tươi

Python:

```text
Python 3.12.13
PYTHON_EXIT=0
```

Unittest:

```powershell
cti-platform-start\.venv\Scripts\python.exe -m unittest workflow.test_check_continuation -v
```

```text
Ran 27 tests in 2.601s
OK
UNITTEST_EXIT=0
```

Ruff:

```powershell
cti-platform-start\.venv\Scripts\python.exe -m ruff check workflow\check_continuation.py workflow\test_check_continuation.py
cti-platform-start\.venv\Scripts\python.exe -m ruff format --check workflow\check_continuation.py workflow\test_check_continuation.py
```

```text
All checks passed!
RUFF_CHECK_EXIT=0
2 files already formatted
RUFF_FORMAT_EXIT=0
```

## Demo chỉ đọc sổ thật

Lệnh guard:

```powershell
cti-platform-start\.venv\Scripts\python.exe workflow\check_continuation.py --ledger PHONG-HOA-RUNS.json
```

Kết quả:

```json
{"decision":"YIELD","task_ids":["WORKFLOW-GUARD","W05-NEXT-RESEARCH"],"reasons":["The ledger records dispatched or running work with a receipt/callback.","This is ledger data, not a live check that a worker is currently running."]}
```

```text
DEMO_EXIT=0
LEDGER_SHA256_BEFORE=b8baccc4365f276cca5b8928337bb370c92bef790be564f253867a6652caa233
LEDGER_SHA256_AFTER=b8baccc4365f276cca5b8928337bb370c92bef790be564f253867a6652caa233
LEDGER_UNCHANGED=True
```

`YIELD` chỉ phản ánh receipt/callback đã ghi trong sổ, không phải kiểm tra live worker và không phải `COMPLETE`.

Hash đầu vào của sổ ở lượt kiểm trước là `bca1f32891303b40e45edb27eb74e558cc3b14a4123d5ac263cec2e8988beb09`, cho thấy sổ được cập nhật ngoài guard giữa hai lượt. Ở cả hai lượt, hash trước/sau trong cùng một lần chạy đều giống nhau.

## Rework R1/R2 sau Leader review

RED, chỉ chạy năm test mới trước khi sửa production code:

```text
Ran 5 tests in 1.672s
FAILED (failures=12)
RED_EXIT=1
```

- 8 failure enum list/dict tái hiện traceback `TypeError: unhashable type` ở `project.status`, criterion `state`, task `status`, receipt `outcome`.
- 4 failure observation `idle`, `completed`, `failed`, `unknown` tái hiện việc trả `YIELD`/exit 0 sai. `queued` và sai kiểu đã bị validation cũ chặn nhưng vẫn được giữ trong regression mới.

GREEN đích sau sửa:

```text
Ran 6 tests in 1.592s
OK
TARGETED_GREEN_EXIT=0
```

Lượt kiểm toàn bộ cuối:

```text
Python 3.12.13
PYTHON_EXIT=0
Ran 32 tests in 5.871s
OK
FINAL_TEST_EXIT=0
All checks passed!
RUFF_CHECK_EXIT=0
2 files already formatted
RUFF_FORMAT_EXIT=0
```

Demo sổ thật sau rework:

```json
{"decision":"YIELD","task_ids":["WORKFLOW-GUARD","W05-IMPLEMENT","UI-IMPLEMENT","AI-NEXT"],"reasons":["The ledger records dispatched or running work with a receipt/callback.","This is ledger data, not a live check that a worker is currently running."]}
```

```text
DEMO_EXIT=0
LEDGER_SHA256_BEFORE=e9198c8009b6f5dee310a1e0aecc8e81c6001f08d93dc3679437495d5a901ee4
LEDGER_SHA256_AFTER=e9198c8009b6f5dee310a1e0aecc8e81c6001f08d93dc3679437495d5a901ee4
LEDGER_UNCHANGED=True
GIT_STATUS_EXIT=0
```

Không sửa `PHONG-HOA-RUNS.json`, repo sản phẩm hoặc file review; không chạy 236 test CTI vì thay đổi chỉ thuộc workflow guard.
