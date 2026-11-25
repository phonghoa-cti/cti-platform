# W05 API — dependency cục bộ

`requirements-api.lock` có 25 package được ghim phiên bản và SHA-256. Lock sinh bằng `uv pip compile`
từ registry công khai; `.venv` nằm riêng trong tree Backend, không sửa môi trường dùng chung.

| Package chính | Version | License |
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

Đây là kiểm chứng dependency cục bộ, không phải bằng chứng production hay kiểm Cloudflare/JWKS thật.
