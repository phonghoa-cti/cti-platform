# Lệnh và exit code — X01 local ingest

Ngày chạy: 11/11/2026. Runtime/test/demo ngoại tuyến sau khi wheel đã tải.

## Bootstrap và dependency

- Tạo worktree từ base, exit 0.
- Lượt tạo venv đầu ghép thừa tên target; `.venv` nằm trong thư mục con mới do
  lượt này tạo. Đã chuyển nguyên venv về đúng `<target>\.venv`, xóa thư mục con
  rỗng và kiểm lại Python 3.12.13; không sửa source.
- `pip install pytest==9.2.0 ruff==0.17.4`, exit 0.
- `pip download --only-binary=:all: --no-deps --require-hashes ...`, exit 0.
- `pip install --no-index --find-links ... --only-binary=:all: --no-deps
  --require-hashes ...`, exit 0.
- Wheel: 416136 byte; SHA-256
  `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`.

## TDD

- RED 1: hai test module mới, exit 2 khi collection; đúng nguyên nhân hai module
  `local_ingest`/`ingest` chưa tồn tại.
- RED 2: `test_temp_write_failure_is_not_misreported_as_link_unsupported`, exit
  1; nhận sai `output_publish_unsupported` trước khi tách pha write/link.
- RED 3: ba ca lifecycle/result-cap/temp-init, exit 1; phát hiện mã lỗi chưa đóng
  và child gán sai mã khi result vượt cap.
- GREEN mới: `pytest test_local_ingest.py test_ingest_cli.py -q`, exit 0,
  60 passed.

## Kiểm cuối trên tree đã commit

- `pytest test_local_ingest.py test_ingest_cli.py test_drafts.py
  test_draft_cli.py test_grounding.py -q`, exit 0, 99 passed.
- `ruff check` năm file Python mới, exit 0.
- `ruff format --check` năm file Python mới, exit 0; 5 files already formatted.
- `git diff --cached --check`, exit 0.
- Tested tree `cdf72bd083ffc06e83ac552baf6c883e34e9fb9d` bằng HEAD tree.
- Commit local `910ced561176b9753ffea113c93414ff77fac427`, không push/PR/merge/deploy.

## Demo HEAD

- TXT hai output mới: exit 0/0, byte-identical.
- PDF hai output mới: exit 0/0, byte-identical.
- Kiểm input hash trước/sau, draft span và PDF page ranges: exit 0.
- Temp mới sau demo: PDF 0; output `.x01-ingest-*.tmp` 0.
- Race barrier không sleep: 1 passed, exit 0.
- Timeout terminate/reap và terminate/kill/reap: 2 passed, exit 0.
