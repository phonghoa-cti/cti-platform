# Phong Hỏa

> A threat intelligence platform for Vietnamese SMEs, built on OpenCTI, with an LLM-based report extractor
> and an AI analyst assistant (MCP + Telegram). Graduation project, 2026–2027.

Phong hỏa đài là những tháp đốt lửa báo giặc: trạm này thấy thì trạm sau truyền tiếp.
Phong Hỏa làm điều tương tự với thông tin về mối đe dọa mạng cho doanh nghiệp vừa và nhỏ.

## Trạng thái hiện tại (25/11/2026)
Toàn bộ các nhánh phát triển đến mốc tạm dừng 12/11/2026 đã được gộp về `main` qua PR `#47`:
- **Đã chạy & kiểm thử cục bộ (ngoại tuyến / dữ liệu giả lập):**
  - `core/phonghoa_core`: chuẩn hóa IOC, trích IOC bằng regex, chấm điểm 0–100, allowlist.
  - `extractor/`: AI extractor X01 (quét prompt injection, đối chiếu bằng chứng, catalog ATT&CK, evaluator C1–C4, gold-pilot validator, nạp TXT/PDF cục bộ & `ingest_queue`, xuất STIX 2.1).
  - `portal/web` & `portal_api/`: giao diện & API cho các luồng duyệt nháp (W05), tra cứu IOC (W02), quản lý tài sản & công nghệ (W04), xem CVE liên quan (W03-R), cập nhật trạng thái CVE (W03-S1) và read model lọc trạng thái ở Backend (W03-S2 Backend).
  - `tools/local_integration/`: gateway & harness kiểm thử tích hợp cục bộ qua HTTP/SQLite/JWT giả lập.
- **Chưa hoàn thành / chưa xác minh:**
  - Giao diện Frontend cho W03-S2 (lọc trạng thái & số tổng hợp).
  - Triển khai thực tế trên lab OpenCTI, kết nối feed thật, LLM thật, Wazuh, Cloudflare Access/HTTPS và corpus báo cáo thật do 2 người gán nhãn.

## Cấu trúc repo
- `core/` — thư viện lõi `phonghoa_core` dùng chung cho connector và extractor.
- `extractor/` — AI extractor X01, `ingest_queue`, xuất STIX 2.1 và bộ kiểm định dữ liệu.
- `portal/web/` — giao diện SME (Next.js, TypeScript, Tailwind, tiếng Việt / English).
- `portal_api/` — API backend (FastAPI + SQLite).
- `tools/local_integration/` — gateway Node.js và harness kiểm thử tích hợp cục bộ.
- `deploy/` — cấu hình Docker Compose tham khảo và gói `deploy/demo/` cho OpenCTI.
- `docs/` — quy ước (`AGENTS.md`), đặc tả (`specs/`), ADR (`adr/`), hướng dẫn (`huong-dan/`), tiến độ (`PROGRESS.md`) và hồ sơ bàn giao (`reports/`).
- `connectors/`, `mcp-server/`, `thesis/` — thư mục khung chờ triển khai tiếp.

## Kiểm thử nhanh tại máy local
- **Python (từ thư mục gốc repo, cần cài `requirements-api.lock`, `requirements-stix-test.lock`, `extractor/requirements-local-ingest.lock`):**
  ```bash
  ruff check . && ruff format --check .
  python -m pytest
  ```
- **Frontend (`portal/web/`):**
  ```bash
  cd portal/web
  npm ci
  npm test
  npm run typecheck && npm run lint && npm run build
  ```
- **Smoke test lab OpenCTI (Ubuntu/WSL, stack `deploy/demo` đang chạy):** `make smoke` (hoặc `bash scripts/smoke_opencti.sh` nếu chưa có Make) kiểm stack healthy, HTTP 200 ở loopback, đăng nhập API admin (đọc `.env`, không in secret), số Attack-Pattern/Vulnerability, worker có tối đa 3 ERROR kết nối nhất thời trong 5 phút (0 lỗi import hoặc lỗi chưa phân loại), `portal_api` trả 200 ở `/api/cves` (fixture tổng hợp) và playbook dry-run ra đúng 1 cảnh báo. In PASS/FAIL từng mục, exit ≠ 0 nếu có FAIL. Đổi thư mục stack bằng `DEMO_DIR=...`, Python bằng `PYTHON=...` (mặc định `.venv/bin/python`).

## Tài liệu đọc tiếp
1. [AGENTS.md](AGENTS.md) — quy ước cho người và AI agent.
2. [docs/PROGRESS.md](docs/PROGRESS.md) & [docs/HANDOFF.md](docs/HANDOFF.md) — tiến độ và bàn giao hiện tại.
3. [docs/reports/2026-11-12-stop/README.md](docs/reports/2026-11-12-stop/README.md) — hồ sơ chi tiết khi tạm dừng 12/11/2026.
4. [tools/local_integration/README.md](tools/local_integration/README.md) — cách chạy các ma trận tích hợp cục bộ.
5. [deploy/README.md](deploy/README.md) — hướng dẫn triển khai lab trên Ubuntu 16 GB RAM.
