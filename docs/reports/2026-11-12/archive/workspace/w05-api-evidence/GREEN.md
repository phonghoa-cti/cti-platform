# W05 API — bằng chứng GREEN

Ngày 11/11/2026, cwd `cti-w05-backend`, Python 3.12.13 trong `.venv` riêng.

| Kiểm tra | Kết quả |
|---|---|
| API targeted: `.venv\Scripts\python.exe -m pytest -o addopts= -q portal_api\tests\test_w05_api.py` | exit 0; 77 passed; 2.53s |
| Review/store/queue + API: `.venv\Scripts\python.exe -m pytest -o addopts= -q extractor\tests\test_review.py extractor\tests\test_store.py extractor\tests\test_queue.py portal_api\tests\test_w05_api.py` | exit 0; 208 passed; 4.98s |
| Full suite: `.venv\Scripts\python.exe -m pytest -o addopts= -q` | exit 0; 355 passed; 27.35s |
| Full suite sau commit | exit 0; 355 passed; 20.31s |
| `.venv\Scripts\ruff.exe check .` | exit 0; all checks passed |
| `.venv\Scripts\ruff.exe format --check .` | exit 0; 99 files formatted |
| `.venv\Scripts\python.exe -m compileall -q portal_api` | exit 0 |
| `git diff --check` | exit 0 |
| Demo `demo_api.py --output demo.json` | exit 0; không mạng/listener; list/detail/decision/reread/repeat đúng 200/200/200/200/409 |

Commit: `feac804818713a314d7db6bdc065b3a676234f32`.
Diff từ base `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`: 13 files, 1725 insertions, 17 deletions.
Không có thay đổi dưới `core/`, `extractor/`, migration hoặc store. `git status --porcelain=v1` rỗng.
