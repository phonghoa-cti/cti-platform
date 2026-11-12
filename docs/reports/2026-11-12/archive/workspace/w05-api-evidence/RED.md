# W05 API — bằng chứng TDD RED

Ngày 11/11/2026, cwd `cti-w05-backend`, interpreter `.venv/Scripts/python.exe` 3.12.13.

1. `python -m pytest -o addopts= -q portal_api/tests/test_w05_api.py` → exit 1 khi collect:
   `ModuleNotFoundError: No module named 'portal_api.app'`. Test được viết trước implementation.
2. Sau skeleton đầu tiên: exit 1, `5 failed, 63 passed`; lỗi chỉ ra span list bị strict tuple từ chối,
   OpenAPI chưa công bố body schema và ba setup/assertion test sai.
3. Regression strict audience: targeted exit 1, `1 failed, 20 passed, 54 deselected`; token có
   `aud=[expected, extra]` lọt auth và chạm DB. Sau đó mới bật `strict_aud`.
4. Runtime settings: targeted exit 1 vì `Settings.from_env` chưa tồn tại; sau đó mới thêm loader fail-closed.
