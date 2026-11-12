# Lệnh rework recovery

Working directory: `cti-x01-ingest-browser-integration`

```powershell
node --test tools/local_integration/tests/test_gateway.mjs
& '<root>\cti-x01-ingest-queue\.venv\Scripts\python.exe' -m pytest -q tools/local_integration/tests/test_runner.py
& '<root>\cti-x01-ingest-queue\.venv\Scripts\python.exe' -m ruff check tools/local_integration/runner.py tools/local_integration/tests/run_ingest_browser_stix.py tools/local_integration/tests/test_runner.py
```

Browser run save recovery:

```powershell
& '<root>\cti-x01-ingest-queue\.venv\Scripts\python.exe' -X utf8 -B tools/local_integration/tests/run_ingest_browser_stix.py browser-session --input-kind txt --case save-refresh-recovery --producer-root '<root>\cti-x01-ingest-local' --producer-python '<root>\cti-x01-ingest-local\.venv\Scripts\python.exe' --duration-seconds 300
```

Browser run decision recovery:

```powershell
& '<root>\cti-x01-ingest-queue\.venv\Scripts\python.exe' -X utf8 -B tools/local_integration/tests/run_ingest_browser_stix.py browser-session --input-kind txt --case decision-refresh-recovery --producer-root '<root>\cti-x01-ingest-local' --producer-python '<root>\cti-x01-ingest-local\.venv\Scripts\python.exe' --duration-seconds 300
```

`<root>` = `$WORKSPACE`.
