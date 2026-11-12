# W05 API review R1–R3 — bằng chứng GREEN

Ngày 11/11/2026, commit `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`.

| Kiểm tra | Kết quả |
|---|---|
| Regression mới chọn lọc gồm audience/list sai/oversized/unexpected | exit 0; 30 passed, 58 deselected; 1.17s |
| API suite sau commit | exit 0; 88 passed; 2.57s |
| Review/store/queue + API sau commit | exit 0; 219 passed; 4.42s |
| Ruff toàn repo | exit 0; all checks passed |
| Format toàn repo | exit 0; 99 files formatted |
| `git diff --check` | exit 0 |
| Demo `demo_api.py --output demo-array-aud.json` | exit 0; JWT RS256 với `aud=[configured]`; 200/200/200/200/409 |
| `git status --porcelain=v1` | exit 0; output rỗng |

Rework diff từ `feac804`: 6 files, 84 insertions, 5 deletions. Cộng dồn từ base: 13 files,
1804 insertions, 17 deletions. Không đổi core/store/migration/dependency, không nối UI, không mạng/listener.

Full suite 355 không chạy lại theo brief vì rework chỉ sửa API/test/docs; regression 219 đã chứa toàn bộ 88 test API.
