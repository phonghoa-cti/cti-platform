# X01 ingest browser harness F1–F3 — commands

Chạy từ `cti-x01-ingest-browser-prep` bằng `.venv\Scripts\python.exe`.

```powershell
python -m pytest tools/local_integration/tests/test_runner.py -q -p no:cacheprovider --junitxml ..\x01-ingest-browser-harness-evidence\rework-f1-f3\runner-final.xml
python -X utf8 -B tools\local_integration\tests\run_stix_e2e.py
python -X utf8 -B tools\local_integration\tests\run_ingest_browser_stix.py offline-check --input-kind txt --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
python -X utf8 -B tools\local_integration\tests\run_ingest_browser_stix.py offline-check --input-kind pdf --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
python -X utf8 -B ..\x01-ingest-browser-harness-evidence\rework-f1-f3\qa_wrapper.py
python -m ruff check tools\local_integration\runner.py tools\local_integration\tests\run_ingest_browser_stix.py tools\local_integration\tests\run_stix_e2e.py tools\local_integration\tests\test_runner.py
python -m ruff format --check tools\local_integration\runner.py tools\local_integration\tests\run_ingest_browser_stix.py tools\local_integration\tests\run_stix_e2e.py tools\local_integration\tests\test_runner.py
git diff --check
```

Kết quả cuối: mọi lệnh exit `0`. Các log `f1-red`, `f2-red`, `f3-red`, `f3-sco-red` ghi RED mong đợi; các log `*-green` và `*-final` ghi GREEN.
