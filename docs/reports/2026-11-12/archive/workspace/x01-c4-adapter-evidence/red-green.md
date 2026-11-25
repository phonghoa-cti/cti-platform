# TDD RED → GREEN

- RED command: `python.exe -X utf8 -B -m pytest -p no:cacheprovider -o addopts= -q extractor/tests/test_llm_adapter.py extractor/tests/test_ttp_audit.py`
- RED exit: `2`.
- RED đúng nguyên nhân: collection `test_ttp_audit.py` thất bại với `ImportError: cannot import name 'run_c4_extraction'`; public C4 seam chưa tồn tại.
- GREEN cùng hai file sau implementation: exit `0`, `125 passed in 0.23s`.
- Sau bổ sung boundary exact 1 MiB và format: exit `0`, `126 passed in 0.22s`.
- Final scoped tại commit: exit `0`, `428 passed in 36.94s`, skipped `0`.
