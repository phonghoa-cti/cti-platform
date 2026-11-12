# X01 ingest browser harness — lệnh bằng chứng

Worktree: `cti-x01-ingest-browser-prep`

```powershell
.\.venv\Scripts\python.exe -m pytest tools/local_integration/tests/test_runner.py -q -p no:cacheprovider --basetemp ..\x01-ingest-browser-harness-evidence\runner-final-tmp --junitxml ..\x01-ingest-browser-harness-evidence\runner-final.xml
.\.venv\Scripts\python.exe -X utf8 -B tools\local_integration\tests\run_ingest_browser_stix.py offline-check --input-kind txt --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -X utf8 -B tools\local_integration\tests\run_ingest_browser_stix.py offline-check --input-kind pdf --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m ruff check tools\local_integration\runner.py tools\local_integration\tests\test_runner.py tools\local_integration\tests\run_ingest_browser_stix.py
.\.venv\Scripts\python.exe -m ruff format --check tools\local_integration\runner.py tools\local_integration\tests\test_runner.py tools\local_integration\tests\run_ingest_browser_stix.py
git diff --check
```

Kết quả cuối: tất cả exit `0`. `offline-*-verified.log`, `runner-final.log/XML`, `static-final.log` là raw output cuối. Các log FAIL trước đó là RED/debug được giữ nguyên, không phải kết quả cuối.
