# RED/GREEN

Interpreter: `cti-platform-start\.venv\Scripts\python.exe` (Python 3.12.13).

## RED

1. Sau khi viết test trước, lần chạy đầu dừng ở collection với
   `ModuleNotFoundError: phonghoa_extractor.gold_pilot`, exit 2.
2. Thêm khung API không có logic và chạy lại: `9 failed`, exit 1; lỗi đầu tiên là
   `GoldPilotError: invalid_arguments` thay vì READY. Đây là RED hành vi mong đợi.

## GREEN

- `python -m pytest extractor/tests/test_gold_pilot.py -q --junitxml ...`: 9 passed, exit 0.
- JUnit: `gold-pilot-junit.xml`, tests=9, failures=0, errors=0.
- Named regression JUnit: `regression-junit.xml`, tests=349, failures=0, errors=0.
