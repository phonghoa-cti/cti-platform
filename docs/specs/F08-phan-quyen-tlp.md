# F08 — Phân quyền và nhãn TLP

- Vai: Web & Red team · Mốc: v0.5 · Trạng thái: Nháp

## Mục tiêu
Đúng người thấy đúng dữ liệu: analyst thấy tất cả; nhân viên IT chỉ thấy TLP:CLEAR/GREEN; lãnh đạo chỉ xem tổng quan.

## Cách làm
- OpenCTI: tạo 3 group (Analyst, IT, Leadership) với marking được phép tương ứng.
- Portal: đăng nhập bằng Cloudflare Access (email nhóm + giảng viên); API dùng API key theo group.
- Agent/bot chỉ dùng tài khoản OpenCTI quyền đọc + tạo bản nháp, không có quyền xóa.

## Tiêu chí chấp nhận
- [ ] Tài khoản IT không xem được object TLP:AMBER (chụp màn hình làm bằng chứng).
- [ ] Bạn Red team thử 5 kiểu vượt quyền trên API (đổi API key, sửa tham số...) → ghi kết quả vào báo cáo.
