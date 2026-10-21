# F05 — Tra cứu IOC và REST API

> **Đã chi tiết hóa:** giao diện xem `W02-tra-cuu-ioc.md`, API xem `api-portal.md`. Phần dưới giữ làm tóm tắt.

- Vai: Web & Red team · Mốc: v0.5 · Trạng thái: Nháp

## Mục tiêu
Nhân viên IT dán một IP/domain/URL/hash vào ô tìm kiếm (hoặc gọi API) và nhận ngay: có xấu không, điểm, lý do, nguồn.

## Thiết kế
- Backend: FastAPI trong `portal/api/`, đọc OpenCTI qua `pycti`; chuẩn hóa đầu vào bằng `phonghoa_core.normalize`.
- `GET /api/ioc?value=...` → `{type, value, found, score, reason, sources[], first_seen, last_seen, related_ttps[]}`.
- Xác thực bằng API key (header `X-API-Key`); ghi log mỗi lần tra cứu (audit).
- Giao diện: ô tìm kiếm trên trang SME, hiển thị IOC ở dạng defang.

## Tiêu chí chấp nhận
- [ ] Nhập `hxxp://evil[.]com` vẫn tìm đúng `http://evil.com/`.
- [ ] Không có API key → 401; tra cứu ≥ 60 lần/phút từ một key → 429.
- [ ] Trả kết quả < 1 giây với kho 100.000 IOC (đo và ghi lại).
- [ ] Có test cho API (giả lập OpenCTI bằng fixtures).
