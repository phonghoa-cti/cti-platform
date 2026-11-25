# W03-S1 Backend rework evidence

Evidence cho delta từ `b8957e63acc7497ba835e06c05e52f4b16ef136c` tới
`4f7100cf83e57b1cb30a12472ed71a0cd985a413`.

- `backend-probes-green.log`: raw output 49 focused source test + 8 probe Leader nguyên bản.
- `related-regression-green.log`: raw output 174 test W03-R/W04 technology/auth/API liên quan.
- `quality-green.log`: Ruff check, format và diff-check với exit code.
- `SHA256SUMS`: khóa ba raw log và probe ngoài thư mục.

Đây là kiểm chứng Python in-process với SQLite/JWT/dataset tổng hợp. Không phải browser/integration gateway, feed thật,
OpenCTI, Cloudflare, lab hoặc production.
