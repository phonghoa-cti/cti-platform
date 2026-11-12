# Lệnh kiểm chứng X01 ingest queue

Ngày chạy: 11/11/2026, Windows, Python 3.12.13 tại `cti-x01-ingest-queue\.venv\Scripts\python.exe`.

| Nhóm | Lệnh | Exit | Số test / kết quả |
|---|---|---:|---|
| Targeted | `python -m pytest extractor/tests/test_ingest_queue.py extractor/tests/test_ingest_queue_cli.py -q` | 0 | 26 passed |
| Store/queue/review/selection | `python -m pytest extractor/tests/test_store.py extractor/tests/test_store_cli.py extractor/tests/test_queue.py extractor/tests/test_queue_cli.py extractor/tests/test_draft_cli.py extractor/tests/test_review.py extractor/tests/test_selection.py -q` | 0 | 205 passed |
| STIX | `python -m pytest extractor/tests/test_stix_export.py extractor/tests/test_stix_export_cli.py -q` | 0 | 77 passed |
| Portal API in-process | `python -m pytest portal_api/tests/test_w05_api.py -q` | 0 | 115 passed |
| Full repo pytest | `python -m pytest -q` từ target | 0 | 553 passed |
| Ruff check | `python -m ruff check extractor` | 0 | `All checks passed!` |
| Ruff format | `python -m ruff format --check extractor` | 0 | 36 files formatted |
| Diff whitespace | `git diff --check` | 0 | Không lỗi |
| Synthetic demo | `python x01-ingest-queue-evidence/run_synthetic_demo.py --rerun-owned` | 0 | TXT/PDF import, retry, conflict, review, STIX đạt |

Đếm test dùng `pytest --collect-only -q` trong đúng target. Full suite được chạy sau lần format cuối. Không dùng số
test này làm bằng chứng browser/OpenCTI/lab/production.

Lần demo đầu tiên đã ghi đủ artifact nhưng exit 1 ở bước in summary do console CP1252 không biểu diễn tiếng Việt.
Harness evidence được sửa `sys.stdout` UTF-8, chỉ xóa đúng năm artifact synthetic do nó sở hữu và chạy lại exit 0;
source tại HEAD không thay đổi.
