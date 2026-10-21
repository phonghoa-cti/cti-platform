# Bàn giao — trạng thái dự án Phong Hỏa (22/10/2026, 00:50)

Agent nào tiếp quản: đọc file này, rồi `AGENTS.md`, `docs/LUONG-HE-THONG.md`, `docs/PROGRESS.md`.

## Tài liệu ngoài repo (bản chính)
- Tài liệu khung đồ án (định hướng, phản biện, phân vai, lộ trình): https://claude.ai/artifact/97QDxdinyj3f65gtcsoVao
- Bản nháp đề cương (hạn gửi giảng viên 03/11): https://claude.ai/artifact/1BXC5NtUGXW9n37veBmkBp
- Mockup 5 màn portal (SOC console): https://claude.ai/artifact/2ejJdxV3a1nUPrsmTaCwxm
- Nếu tài liệu khung lệch với repo: **repo đúng hơn** (đặc biệt `docs/design/DESIGN.md`).

## Quyết định đã chốt
| Chủ đề | Quyết định | Nguồn |
|---|---|---|
| Hướng làm | OpenCTI làm lõi; nhóm viết connector, AI extractor, MCP + Hermes, portal | ADR 0001 |
| Portal | Next.js + Tailwind + shadcn/ui; API FastAPI; SQLite; Cloudflare Access (chờ nhóm duyệt) | ADR 0002, W00 |
| Giao diện | SOC console tối, IBM Plex, lưới 8 px | DESIGN.md, mockup |
| Agent trong sản phẩm | Hermes qua Telegram, chỉ đọc + đề xuất, người duyệt mọi hành động | A01 |
| Paperclip | Chỉ thử cho quy trình dev sau MVP, không vào sản phẩm | ADR 0003 |
| Hạ tầng | Ubuntu i3 16 GB chạy OpenCTI (1 worker, tắt XTM One); laptop 32 GB chạy lab Wazuh/Windows/Kali | deploy/, hướng dẫn 03–04 |

## Đã xong
- Repo + PR #1 (bộ khởi động đầy đủ, CI xanh: lint, 47 test, quét secret).
- Thư viện `core/phonghoa_core`, spec F01–F08, W00–W05, A01, 6 hướng dẫn, wiki, backlog 41 issue.

## Việc tiếp theo (theo thứ tự)
1. Merge PR #1 (cần 1 người khác duyệt).
2. Bật cài đặt bảo mật repo: Secret scanning, Push protection, Dependabot, tự xóa nhánh sau merge (issue #43).
3. Việc 2: cài OpenCTI (`docs/huong-dan/00-viec-2-cai-opencti.md`), rồi Việc 3 (`03-...`).
4. Gửi đề cương trước 03/11.
5. Dựng khung portal (P0) bằng prompt bên dưới.

Đã xong 22/10: 42 issue + 5 milestone trên GitHub (chạy lại `scripts/create_issues.py` không tạo trùng).

## Prompt sẵn cho opencode (agent planner, rồi implementer)
**P0 — khung portal:**
> Đọc AGENTS.md, docs/specs/W00-portal-tong-the.md, docs/specs/api-portal.md, docs/design/DESIGN.md.
> Lập kế hoạch dựng khung `portal/web` (Next.js App Router, TypeScript, Tailwind, shadcn/ui, next-intl vi/en, font IBM Plex)
> và `portal/api` (FastAPI, GET /api/health và GET /api/me với DEV_USER_EMAIL), kèm `portal/docker-compose.yml`.
> Giao diện chỉ gồm khung: sidebar + thanh trên theo mockup, 5 trang rỗng có tiêu đề. Frontend dùng dữ liệu giả theo api-portal.md.
> Chia task ≤ 2 giờ, mỗi task có cách kiểm tra. Hỏi tôi trước khi cài gói. Làm theo chế độ học.

**X01 — AI extractor (tháng 12):**
> Đọc docs/specs/X01-ai-extractor.md và extractor/dataset/GUIDELINE.md. Bắt đầu từ task 1–2 (tải văn bản, quét chèn lệnh), test trước.

**F01 — connector đầu tiên:**
> Đọc docs/specs/F01-thu-thap-feed.md và skill stix-connector. Liệt kê connector chính thức của OpenCTI khớp bảng nguồn,
> chỉ ra nguồn nào phải tự viết. Chưa viết code; trình bày phương án để tôi duyệt.

## Lưu ý kỹ thuật
- Phiên Claude Code chỉ dùng được GitHub REST API (`gh api ...`), không dùng được GraphQL (`gh pr create` sẽ lỗi).
- Mã CVE, điểm EPSS/CVSS, quốc gia/ASN trong mockup đều là dữ liệu minh họa.
- Ví dụ điểm 84 trong spec/mockup đã được tính lại khớp công thức `phonghoa_core.scoring`.
