# Bàn giao — trạng thái dự án Phong Hỏa (cập nhật 25/11/2026)

Agent hoặc thành viên tiếp quản: đọc file này, rồi `AGENTS.md`, `docs/LUONG-HE-THONG.md`, `docs/PROGRESS.md` và `docs/reports/2026-11-12-stop/README.md`.

## Tổng quan mốc hiện tại
- **25/11/2026:** Toàn bộ 4 nhánh phát triển tính đến lúc tạm dừng 12/11/2026 đã được tích hợp và gộp vào nhánh `main` qua PR `#47` (`2e74d8d`), kèm sửa lỗi đồng thời trong `store.py` và tương thích Linux CI (CI GitHub Actions đã xanh cả `python` và `secrets`).
- **Tình trạng sản phẩm:** Đã có nhiều luồng chạy và kiểm thử **cục bộ / ngoại tuyến** (dữ liệu tổng hợp); chưa hoàn thành toàn bộ MVP và chưa chạy trên lab OpenCTI / dữ liệu thật.

## Quyết định đã chốt
| Chủ đề | Quyết định | Nguồn |
|---|---|---|
| Hướng làm | OpenCTI làm lõi; nhóm viết connector, AI extractor, MCP + Hermes, portal | ADR 0001 |
| Portal | Next.js + Tailwind + shadcn/ui; API FastAPI; SQLite; Cloudflare Access (chờ nhóm duyệt) | ADR 0002, W00 |
| Giao diện | SOC console tối, IBM Plex, lưới 8 px | DESIGN.md, mockup |
| Agent trong sản phẩm | Hermes qua Telegram, chỉ đọc + đề xuất, người duyệt mọi hành động | A01 |
| Paperclip | Chỉ thử cho quy trình dev sau MVP, không vào sản phẩm | ADR 0003 |
| Hạ tầng | Ubuntu i3 16 GB chạy OpenCTI (1 worker, tắt XTM One); laptop 32 GB chạy lab Wazuh/Windows/Kali | deploy/, hướng dẫn 03–04 |

## Đã có trên `main` (kiểm thử cục bộ)
- **Lõi (`core/phonghoa_core`):** chuẩn hóa IOC, trích regex, chấm điểm 0–100, allowlist.
- **AI Extractor (`extractor/`):**
  - Quét prompt injection, bọc dữ liệu (`wrap_as_data`), đối chiếu bằng chứng, kiểm mã ATT&CK, tính P/R/F1.
  - Adapter C2–C4 ngoại tuyến, catalog MITRE ATT&CK (hỗ trợ snapshot v20.1 local), evaluator/reporter C1–C4, kiểm định gold-pilot.
  - Nạp file TXT/PDF cục bộ (`local_ingest`) và hàng đợi SQLite có provenance (`ingest_queue`, schema v3).
  - Xuất STIX 2.1 từ bản đã duyệt (`stix_export`), kiểm chuẩn `stix2-validator`.
- **Portal (`portal/web/` & `portal_api/`):**
  - W05: duyệt/từ chối nháp, chọn IOC, audit bất biến.
  - W02: tra cứu IOC (`/tra-cuu`, `/tra-cuu/mau`).
  - W04: quản lý tài sản domain/CIDR & công nghệ (`/tai-san`, `/tai-san/mau`).
  - W03-R & W03-S1: danh sách CVE liên quan công nghệ, lọc KEV, cập nhật trạng thái/ghi chú/lịch sử (`/lo-hong`, `/lo-hong/mau`).
  - W03-S2 (mới có Backend): `GET /api/cves/status-view` lọc trạng thái & bộ đếm tổng hợp.
- **Tích hợp cục bộ (`tools/local_integration/`):** gateway Node.js + harness Python chạy các ma trận HTTP/SQLite/JWT giả lập.
- **Chuẩn bị lab (`deploy/demo/`):** cấu hình compose ghim digest và fixture mẫu cho OpenCTI.

## Việc tiếp theo khi tiếp tục phát triển
1. **W03-S2 Frontend:** triển khai giao diện lọc theo trạng thái & số tổng hợp trên `/lo-hong` nối với `GET /api/cves/status-view`.
2. **Hạ tầng & Lab:** dựng OpenCTI thật trên máy Ubuntu (`docs/huong-dan/00-viec-2-cai-opencti.md`), chạy thử connector MITRE / AlienVault OTX (`deploy/demo/`), đo RAM thực tế.
3. **AI & Dataset thật:** gán nhãn corpus báo cáo thật bởi 2 người độc lập, nối LLM API thật (chặn TLP:AMBER/RED).
4. **Còn chưa triển khai:** `connectors/` nguồn Việt Nam, `mcp-server/` + Hermes Telegram (A01), trang tổng quan W01, xuất CSV ở W04, Cloudflare Access/HTTPS thật, và quyển `thesis/`.

## Lưu ý kỹ thuật
- Mã CVE, điểm EPSS/CVSS, quốc gia/ASN trong mockup và các ma trận cục bộ đều là dữ liệu minh họa tổng hợp.
- Chi tiết lịch sử 52 nhánh trước khi gộp `main` xem tại `docs/reports/2026-11-12/README.md` và `docs/reports/2026-11-12-stop/README.md`.
