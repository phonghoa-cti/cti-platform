# TDD RED — W05-B

Lệnh (cwd là `cti-w05-backend`):

```powershell
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -m pytest -q extractor/tests/test_review.py
```

Kết quả đầu tiên sau khi test collect được: **exit 1, 25 failed**. Các lỗi đúng nguyên nhân tính năng chưa có:
`review` chưa được trả, thiếu `Actor`, `migrate_store`, các lớp lỗi review và `save_draft(...,
created_by_subject=...)`.

Một vòng RED bổ sung cho validation kiểu chạy với `-k malformed_actor_and_decision_types`: **exit 1,
1 failed, 2 passed, 27 deselected**; lỗi thực tế là `TypeError: unhashable type: 'list'` thay vì
`DraftInputError`, sau đó mới sửa thứ tự kiểm kiểu.

## Rework reviewer ngày 11/11/2026

Lệnh RED:

```powershell
python -m pytest -o addopts= -q extractor/tests/test_review.py extractor/tests/test_store.py `
  extractor/tests/test_store_cli.py -k "broken_constraints or invalid_id or above_sqlite_integer"
```

Kết quả: **exit 1, 7 failed, 9 passed, 111 deselected**. Năm case schema `user_version=1` có đúng tên cột
nhưng lần lượt thiếu CHECK review, UNIQUE audit, FK audit, CHECK action hoặc index queue vẫn lọt qua validator.
Hai case còn lại cho thấy API/CLI xử lý ID `2**63` như database thiếu thay vì từ chối ID trước I/O.

## Rework FK ghép ngày 11/11/2026

Lệnh RED:

```powershell
python -m pytest -o addopts= -q extractor/tests/test_review.py -k "broken_constraints and audit_composite_fk"
```

Kết quả: **exit 1, 1 failed, 35 deselected**. Schema current hợp lệ ở mọi invariant khác nhưng dùng
`FOREIGN KEY(draft_id, reason) REFERENCES drafts(id, created_by_subject)` vẫn lọt validator; `get_draft()` đi
tiếp và trả `DraftNotFoundError` thay vì từ chối schema bằng `DraftSQLiteError` trước I/O dữ liệu.
