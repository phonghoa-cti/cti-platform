# Rework R4 — lệnh và exit

Ngày chạy: 11/11/2026. Runtime/test/demo ngoại tuyến.

- Brief SHA-256: `a7b6f123385dfb3ea6b9cd545f855a8a79b0a6a0231f2a40d077b9df2da6d18c`.
- Probe UNC RED nguyên trạng: 1 failed, exit 1 (`DID NOT RAISE`).
- Regression nội bộ RED: 3 failed, 2 passed, exit 1; cả ba ca UNC cwd đã tới `lstat`.
- Regression nội bộ GREEN chọn lọc: 5 passed, exit 0.
- Hai test ingest: 74 passed, exit 0.
- Hai probe Leader nguyên trạng: 7 passed, exit 0.
- Ruff check hai file sửa: exit 0.
- Ruff format-check hai file sửa: exit 0, 2 files already formatted.
- `git diff --check` và `git diff --cached --check`: exit 0.
- Commit local: `8a16758601647fb3dbf935abecc2435f3b7a3fb6`, exit 0.
- HEAD tree: `5a316c0060bc697f6ec1e6001e932a8f6db27c38`.
- Demo HEAD dùng input TXT relative local: exit 0; input trước/sau cùng hash; temp mới 0.

Không chạy lại full C1 suite hoặc PDF demo theo brief R4.
