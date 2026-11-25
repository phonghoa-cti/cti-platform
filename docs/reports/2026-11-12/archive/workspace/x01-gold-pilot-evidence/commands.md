# Lệnh kiểm chứng cuối

Mọi lệnh chạy tại `cti-x01-gold-pilot`, với `PYTHONPATH=<target>\core;<target>\extractor`.

1. `python -m pytest extractor/tests/test_gold_pilot.py -q --junitxml <evidence>\gold-pilot-junit.xml` → exit 0, 9/9.
2. `python -m pytest` đúng sáu file regression trong Leader plan, có env official snapshot → exit 0, 349/349.
3. `python -m ruff check` đúng ba file Python mới → exit 0.
4. `python -m ruff format --check` đúng ba file Python mới → exit 0.
5. CLI synthetic READY hai output mới → exit 0/0, SHA-256 bằng nhau.
6. CLI synthetic NOT_READY → exit 2 và publish report hợp lệ.
7. CLI synthetic INVALID → exit 2, stderr `invalid_manifest`, không tạo report.
8. CLI compatibility human-supplied khai báo với pin/snapshot official v20.1 local → exit 0.
9. `git diff --check 5e0cbf4d..9d278cfc` → exit 0.

Không gọi model, mạng, DB, API, UI, lab, cloud hoặc production.
