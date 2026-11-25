# W05 API cục bộ

Package này cung cấp đúng ba endpoint FastAPI cho hàng đợi review SQLite:

- `GET /api/drafts`: summary của draft còn `review.status=pending`;
- `GET /api/drafts/{id}`: payload 1.0 đầy đủ và metadata `review` tách riêng;
- `POST /api/drafts/{id}/decision`: approve/reject cục bộ qua core đã có.

`approved` chỉ là quyết định cục bộ, chưa nhập OpenCTI. App không có listener mặc định, không nhận email/role
từ client và không có dev user. Production factory dùng `Settings.from_env()`; thiếu một giá trị bắt buộc sẽ dừng:

| Biến | Ý nghĩa |
|---|---|
| `W05_DB_PATH` | File SQLite review đã migrate |
| `CF_ACCESS_ISSUER` | HTTPS issuer chính xác, không path |
| `CF_ACCESS_AUD` | Một audience tin cậy; claim nhận chuỗi exact hoặc mảng chuỗi có exact member |
| `CF_ACCESS_JWKS_URL` | HTTPS JWKS cùng origin với issuer |
| `PORTAL_ORIGIN` | Origin portal chính xác gồm scheme/host/port |
| `W05_ROLES_JSON` | JSON map `sub` sang danh sách role phía server |

POST bắt buộc JWT hợp lệ, role `analyst|admin`, `Origin` chính xác và `Content-Type: application/json`
(có thể thêm `charset=utf-8`). Mọi response dưới `/api/drafts` có `Cache-Control: no-store` và không trả token,
claim, SQL/path hay lỗi validation thô.

## Dependency

`requirements-api.in` là constraint trực tiếp; `requirements-api.lock` ghim toàn bộ dependency và SHA-256.
Các license chính được đọc từ metadata package cài trong `.venv` riêng:

| Package | Version đã khóa | License |
|---|---:|---|
| FastAPI | 0.119.1 | MIT |
| HTTPX | 0.28.1 | BSD-3-Clause |
| PyJWT | 2.15.1 | MIT |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| Pydantic | 2.14.3 | MIT |
| Starlette | 0.48.0 | BSD-3-Clause |
| AnyIO | 4.11.0 | MIT |
| pytest | 9.2.0 | MIT |
| Ruff | 0.17.4 | MIT |

Tải/cài package từ registry chính thức chỉ xác minh dependency cục bộ, không chứng minh Cloudflare/lab production.

## Harness tích hợp cục bộ

`tools/local_integration/runner.py` dựng một stack loopback do từng run sở hữu: Uvicorn, production build Next,
gateway same-origin, JWT RSA và SQLite đều là dữ liệu tổng hợp. Gateway chỉ chuyển tiếp ba route legacy và bốn
route selection v1 đã allowlist; cap body legacy là 8.192 byte, cap v1 là 65.536 byte. Chạy ma trận riêng bằng:

```powershell
.\.venv\Scripts\python.exe tools\local_integration\tests\run_http_matrix.py
.\.venv\Scripts\python.exe tools\local_integration\tests\run_selection_matrix.py
```

Mỗi scenario phải dùng `LocalRun` mới; `close()` chỉ dừng process/listener và xóa temp do chính run đó tạo.
Harness không nới cấu hình HTTPS production, không dùng secret thật và không nối OpenCTI.
