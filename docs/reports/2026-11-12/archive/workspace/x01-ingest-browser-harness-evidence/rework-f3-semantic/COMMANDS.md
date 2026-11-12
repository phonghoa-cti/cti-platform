# X01 ingest browser harness — F3 semantic commands

Chạy từ `cti-x01-ingest-browser-prep` bằng `.venv\Scripts\python.exe`.

```powershell
python -m pytest tools/local_integration/tests/test_runner.py -k semantic_description_leak -q
python -X utf8 ..\leader-api-harness-acceptance-20261111\verify.py
python -m pytest tools/local_integration/tests/test_runner.py -q -p no:cacheprovider --junitxml ..\x01-ingest-browser-harness-evidence\rework-f3-semantic\08-runner-postformat.xml
python -X utf8 -B tools/local_integration/tests/run_ingest_browser_stix.py offline-check --input-kind txt --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
python -X utf8 -B tools/local_integration/tests/run_ingest_browser_stix.py offline-check --input-kind pdf --producer-root ..\cti-x01-ingest-local --producer-python ..\cti-x01-ingest-local\.venv\Scripts\python.exe
python -m ruff check tools/local_integration/tests/run_ingest_browser_stix.py tools/local_integration/tests/test_runner.py
python -m ruff format --check tools/local_integration/tests/run_ingest_browser_stix.py tools/local_integration/tests/test_runner.py
git diff --check
```

`01-red-semantic-description.log` là RED mong đợi: hai ca đều `DID NOT RAISE RuntimeError`, exit 1.
Các log GREEN/final có exit 0. `03-leader-verify-green.log` ghi lần đầu bị console CP1252 chặn khi in tiếng Việt;
chạy lại nguyên script với `PYTHONUTF8=1` ở `04-leader-verify-green-utf8.log` đạt exit 0, không đổi code/probe.
