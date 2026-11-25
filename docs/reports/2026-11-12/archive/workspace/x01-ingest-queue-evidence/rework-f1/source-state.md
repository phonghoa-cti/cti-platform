# Trạng thái nguồn rework F1

- Branch: `feat/x01-ingest-queue-20261111`
- Parent: `db36ec01b765dfd515c1d0ef13642a693b777172`
- HEAD: `fc08897a240d9e55198b1a8166b21e8e7caf7213`
- Commit: `fix: reject control characters in ingest names`
- Diff: 4 file, `+57/-2`
- File thay đổi:
  - `docs/PROGRESS.md`
  - `extractor/phonghoa_extractor/ingest_queue.py`
  - `extractor/tests/test_ingest_queue.py`
  - `extractor/tests/test_ingest_queue_cli.py`
- `git status --short`: output rỗng sau commit.
- Không sửa migration, schema, store, API, UI, producer, evidence QA hay `tools/local_integration`.
- Không push, PR, merge, deploy, gọi model/network/OpenCTI/lab/VM.
