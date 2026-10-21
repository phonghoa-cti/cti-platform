# W04 — Trang Tài sản (`/tai-san`)

- Vai: Web & Red team · Mốc: P3 (15/12/2026) · API `/api/assets`

## Mục tiêu
Lưu "hồ sơ" của doanh nghiệp để biến thông tin chung thành thông tin **của mình**: IOC nào liên quan, CVE nào ảnh hưởng.

## Loại tài sản
| Loại | Ví dụ | Dùng để |
|---|---|---|
| Tên miền | `congty.vn` (gồm cả subdomain) | Khớp IOC tên miền giả mạo, email; tự thêm vào allowlist |
| Dải IP | `113.160.0.0/24` | Khớp IOC nhắc tới IP của công ty; tự thêm vào allowlist |
| Công nghệ | Fortinet / FortiOS / 7.2; WordPress / 6.x; Microsoft / Exchange | Khớp CVE (W03) |
| Thương hiệu / từ khóa | "Công ty ABC", "abc logistics" | Phát hiện tên miền giả mạo (mở rộng) |

## Bố cục
Bốn tab theo bốn loại; mỗi tab là bảng + nút "Thêm". Form thêm có kiểm tra định dạng (tên miền hợp lệ, CIDR hợp lệ).
Tab Tên miền có thêm cột "Phơi nhiễm" (mở rộng, mức S): số subdomain tìm thấy qua crt.sh, số cổng mở qua Shodan.

## Hành vi quan trọng
- Thêm tên miền/dải IP → tự thêm vào allowlist (không bao giờ chặn tài sản của chính mình), có ghi chú nguồn gốc "từ tài sản".
- Xóa tài sản cần xác nhận; ghi nhật ký.
- Nhập/xuất CSV để khai báo nhanh.

## Tiêu chí chấp nhận
- [ ] CRUD đủ 4 loại; dữ liệu không hợp lệ bị từ chối với thông báo tiếng Việt rõ ràng.
- [ ] Thêm `congty.vn` → tra cứu `mail.congty.vn` ở W02 hiện "thuộc tài sản của bạn".
- [ ] Vai trò Lãnh đạo không vào được trang (API trả 403).
