# X01 ingest queue rework F1 — lệnh và exit

Ngày 11/11/2026. Tree: `cti-x01-ingest-queue`. HEAD:
`fc08897a240d9e55198b1a8166b21e8e7caf7213`.

| Pha | Lệnh | Exit | Kết quả |
|---|---|---:|---|
| RED | `.\.venv\Scripts\python.exe -m pytest extractor\tests\test_ingest_queue.py::test_control_characters_in_matching_names_fail_before_database_mutation extractor\tests\test_ingest_queue.py::test_vietnamese_spaces_and_emoji_in_matching_names_are_valid extractor\tests\test_ingest_queue_cli.py::test_cli_rejects_control_characters_without_database_mutation -q` | 1 | 4 fail/4 pass; U+0085/U+009F được nhập sai ở library và CLI |
| GREEN mục tiêu | Cùng lệnh RED sau sửa | 0 | 8 pass |
| Regression bắt buộc | `.\.venv\Scripts\python.exe -m pytest extractor\tests\test_ingest_queue.py extractor\tests\test_ingest_queue_cli.py -q` | 0 | 34 pass |
| Ruff check | `.\.venv\Scripts\python.exe -m ruff check extractor\phonghoa_extractor\ingest_queue.py extractor\tests\test_ingest_queue.py extractor\tests\test_ingest_queue_cli.py` | 0 | `All checks passed!` |
| Ruff format | `.\.venv\Scripts\python.exe -m ruff format --check extractor\phonghoa_extractor\ingest_queue.py extractor\tests\test_ingest_queue.py extractor\tests\test_ingest_queue_cli.py` | 0 | 3 file đã định dạng |
| Diff check | `git diff --check HEAD^ HEAD` | 0 | Không có lỗi whitespace |
| Source state | `git status --short` | 0 | Output rỗng |

`red.log` là output lỗi trước sửa. Các log còn lại được chạy lại tại đúng HEAD sau commit.
