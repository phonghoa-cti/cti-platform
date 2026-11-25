# Kiểm chứng baseline Phong Hỏa — PR #46

Ngày kiểm tra: **10/11/2026**
Checkout riêng: `$WORKSPACE\cti-platform-start`
Nhánh cục bộ: `baseline/pr46-verify-20261110`
SHA đã kiểm tra: `36259c118f519d3ac9cfc1f7b79e7180c2448a88`

## Kết luận

| Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|
| Ref PR #1 và PR #46 đúng remote | PASS | `git ls-remote`: PR1 `8d9d7df...`, PR46 `36259c1...`, exit 0 |
| Quan hệ commit | PASS | PR1 là cha trực tiếp của PR46; `merge-base --is-ancestor` exit 0; `rev-list` = `0 1` |
| Toàn bộ test tại PR46 | PASS | 61 test đạt, exit 0 |
| Ruff kiểm tra mã | PASS | `ruff check .`, exit 0 |
| Ruff kiểm tra định dạng | PASS | 67 file đã đúng định dạng, exit 0 |
| Test không gọi feed/cloud/LLM thật | PASS trong phạm vi test hiện có | Đã đọc 7 file test; quét import/lời gọi mạng không có kết quả |
| Checkout sạch sau kiểm tra | PASS | HEAD giữ nguyên; `git diff --exit-code` exit 0; không có file chưa theo dõi ngoài ignore |
| Cấu hình Compose hợp nhất | UNVERIFIED | Máy không có Docker; repo thiếu base `deploy/docker-compose.yml` |
| OpenCTI/connector chạy trên lab và giới hạn RAM | UNVERIFIED | Không cài/khởi động service, không gọi feed theo phạm vi được giao |

## Quan hệ PR và phạm vi core/extractor

- Remote PR #1: `8d9d7df54e90a1811b58a713cfe7ec56072ed0a7`.
- Remote PR #46: `36259c118f519d3ac9cfc1f7b79e7180c2448a88`.
- Commit PR #46 có đúng một parent là PR #1. Hai head lệch `0` commit bên PR1 và `1` commit bên PR46.
- Chênh lệch là 10 file, `327` dòng thêm và `3` dòng xóa: thêm các bước không cần LLM của extractor (quét chèn lệnh, đối chiếu bằng chứng, chấm P/R/F1), 14 test extractor, và chỉnh `pytest.ini`/`ruff.toml`; core được kế thừa nguyên từ PR #1.
- Một lần chạy toàn bộ tại PR #46 đã phủ cả `core/tests` và `extractor/tests`; không chạy trùng PR #1.

## Môi trường kiểm tra hiệu lực

| Thành phần | Phiên bản/cấu hình |
|---|---|
| Git | `2.55.0.windows.1` |
| uv | `0.11.15` |
| Python trong `.venv` | `3.12.13` |
| pytest | `9.2.0` |
| Ruff | `0.17.4`; target `py312` |
| CI trong repo | Python `3.12`; `pytest` và `ruff` không ghim phiên bản |

Máy ban đầu không có Python 3.12. `uv` tải bản CPython 3.12.13 do mình quản lý và tạo `.venv` ngay trong checkout; chỉ cài phụ thuộc kiểm thử vào môi trường này. `pytest`/`ruff` có sẵn trên PATH thuộc môi trường Hermes khác nên không được dùng. `make` không có trên Windows; các lệnh Python tương đương với nội dung Makefile được chạy trực tiếp.

## Lệnh và kết quả mới

```text
.venv\Scripts\python.exe -m pytest -ra
61 passed in 0.29s
exit 0

.venv\Scripts\python.exe -m ruff check .
All checks passed!
exit 0

.venv\Scripts\python.exe -m ruff format --check .
67 files already formatted
exit 0
```

Test hiện có chỉ dùng chuỗi dữ liệu trong mã, phép tham số hóa và `tmp_path` (thư mục tạm của pytest). Không có import/lời gọi `requests`, `httpx`, `aiohttp`, `socket`, `urllib.request`, OpenAI hay Anthropic trong `core`/`extractor`. Vì vậy lượt chạy này không gọi feed, cloud hoặc LLM thật.

## Cấu hình deploy: điều đã chọn và khoảng trống

- Repo **không ghim phiên bản OpenCTI**: hướng dẫn clone `OpenCTI-Platform/docker` nhưng không chỉ tag/commit.
- Connector AlienVault dùng `opencti/connector-alienvault:latest`; đây là phiên bản trôi, không tái hiện chắc chắn.
- Base `deploy/docker-compose.yml` không có trong commit, dù Makefile gọi đúng đường dẫn đó. Chỉ có file override, nên không thể xác minh cấu hình Compose hoàn chỉnh từ checkout.
- CI chọn Python 3.12 nhưng không ghim `pytest`/`ruff`; kết quả trên chỉ chứng minh với phiên bản đã ghi ở trên.
- CI quét secret bằng image `gitleaks:latest` và chế độ `dir`; đây không phải bản ghim và không chứng minh quét lịch sử Git. Chưa sửa theo phạm vi lượt này.
- `.env.example` còn mô tả gửi `TLP:CLEAR/GREEN` tới LLM; nghiên cứu đã chỉ ra TLP:GREEN không tự cho phép gửi tới mọi nhà cung cấp cloud. Chưa sửa TLP theo phạm vi lượt này.

Docker không có trên máy kiểm tra (`docker --version` và `docker compose version` đều exit 1). Do đó chưa kiểm tra hợp nhất YAML, pull image, health, nạp dữ liệu, mạng, tài nguyên hoặc tính tương thích OpenCTI/connector trên lab.

## Trạng thái trước/sau và giới hạn

- Trước: thư mục đích chưa tồn tại; clone mới từ repo, checkout đúng SHA và tạo nhánh riêng.
- Sau: SHA vẫn là `36259c118f519d3ac9cfc1f7b79e7180c2448a88`; Git diff rỗng; `.venv` nằm trong danh sách ignore.
- Không sửa logic sản phẩm, TLP, CI hoặc deploy; không push, PR, merge, deploy, đổi quyền, gọi LLM/feed hoặc UI.
- Checkpoint sạch sẵn sàng cho lát cắt tích hợp #9 tiếp theo. Các blocker nên được tách thành task nhỏ: ghim version deploy/tooling; cung cấp base Compose theo ref; sửa quy tắc TLP và phạm vi quét secret.

## Bằng chứng

- `baseline-evidence/01-git-and-scope.txt`
- `baseline-evidence/02-environment.txt`
- `baseline-evidence/03-pytest.txt`
- `baseline-evidence/04-ruff.txt`
- `baseline-evidence/05-deploy-readonly.txt`

Các log chỉ chứa lệnh, phiên bản, SHA, counts và kết quả đã lọc; không đọc hoặc ghi secret.

## Học thêm

- **SHA** là mã định danh duy nhất của một commit Git; ghim SHA giúp lần kiểm tra sau dùng đúng mã nguồn.
- **Virtual environment (`.venv`)** là môi trường Python tách biệt, tránh làm thay đổi thư viện toàn hệ thống.
- **Image tag `latest`** luôn có thể trỏ sang bản mới, nên khó tái hiện hơn tag phiên bản hoặc digest cố định.
- **UNVERIFIED** nghĩa là chưa có bằng chứng trực tiếp trong môi trường cần kiểm tra, không đồng nghĩa hỏng.
