# W00 — Portal Phong Hỏa: spec tổng thể

- Vai: Web & Red team (chính), AI & Agent (màn duyệt bản nháp) · Trạng thái: **Chờ nhóm duyệt**
- Thay thế phần giao diện của F05, F06; chi tiết từng màn ở W01–W05; API ở `api-portal.md`.

## 0. Quyết định cần nhóm duyệt (đọc trước)
| # | Quyết định | Đề xuất | Phương án khác |
|---|---|---|---|
| 1 | Công nghệ giao diện | Next.js + Tailwind + shadcn/ui (xem ADR 0002) | Streamlit; FastAPI + HTMX |
| 2 | Công nghệ API | FastAPI (Python, dùng chung `phonghoa_core`) | Gọi thẳng OpenCTI từ Next.js |
| 3 | Dữ liệu riêng của portal | SQLite (một file, không cần thêm dịch vụ) | PostgreSQL |
| 4 | Đăng nhập | Cloudflare Access đứng trước + bảng email → vai trò | Tự làm đăng nhập bằng mật khẩu |
| 5 | Ngôn ngữ | Tiếng Việt mặc định, có tiếng Anh | Chỉ tiếng Việt |

## 1. Portal để làm gì
OpenCTI rất mạnh nhưng là công cụ cho chuyên gia CTI, giao diện tiếng Anh, nhiều khái niệm.
Portal là **"mặt tiền" cho doanh nghiệp vừa và nhỏ**: trả lời nhanh 4 câu hỏi bằng tiếng Việt —
1. Hôm nay công ty mình có bị đe dọa gì đáng chú ý không? → **Tổng quan** (W01)
2. Cái IP/tên miền/link/file này có độc không? → **Tra cứu** (W02)
3. Phần mềm công ty đang dùng có lỗ hổng nào đang bị khai thác không? → **Lỗ hổng** (W03)
4. Công ty mình có những tài sản gì cần bảo vệ? → **Tài sản** (W04)

Và một chức năng cho analyst: **duyệt** bản nháp do AI trích xuất và hành động do agent đề xuất (W05).

Không làm trong portal: những gì OpenCTI đã làm tốt cho analyst (đồ thị quan hệ, quản lý connector, chỉnh STIX chi tiết) — portal chỉ dẫn link sang OpenCTI.

## 2. Người dùng và vai trò
| Vai trò | Ai | Thấy | Làm được |
|---|---|---|---|
| Lãnh đạo | Giám đốc, trưởng phòng | Tổng quan, Lỗ hổng (dạng tóm tắt) | Chỉ xem |
| IT | Nhân viên IT 1–3 người | Mọi màn trừ Duyệt; chỉ dữ liệu TLP:CLEAR/GREEN | Tra cứu, đề xuất chặn, quản lý tài sản, tạo API key |
| Analyst | Người phụ trách an ninh (hoặc dịch vụ thuê ngoài) | Tất cả, mọi mức TLP | Thêm: đánh dấu báo nhầm, duyệt bản nháp AI, duyệt hành động |
| Admin | Nhóm phát triển | Tất cả | Thêm: cấu hình, quản lý người dùng |

Ma trận quyền chi tiết nằm trong `api-portal.md` mục 2; backend kiểm tra quyền ở **mọi** endpoint (không tin giao diện).

## 3. Kiến trúc
```text
Trình duyệt ──HTTPS──> Cloudflare Access ──> portal-web (Next.js) ──> portal-api (FastAPI) ──> OpenCTI (GraphQL qua pycti)
                                                                                 └──> SQLite: tài sản, phê duyệt, nhật ký, cache
```
- `portal-web` không bao giờ giữ token OpenCTI; mọi dữ liệu đi qua `portal-api`.
- `portal-api` đọc người dùng từ header `Cf-Access-Authenticated-User-Email` do Cloudflare Access gắn; khi phát triển trên máy dùng biến `DEV_USER_EMAIL`.
- Thư mục: `portal/web/` (Next.js), `portal/api/` (FastAPI), `portal/docker-compose.yml`.

## 4. Sơ đồ trang
```text
/                    → chuyển tới /tong-quan
/tong-quan           W01  (mọi vai trò)
/tra-cuu?q=...       W02  (IT, Analyst, Admin)
/lo-hong             W03  (mọi vai trò; Lãnh đạo xem bản tóm tắt)
/tai-san             W04  (IT, Analyst, Admin)
/duyet               W05  (Analyst, Admin)
/cai-dat             API key, ngôn ngữ, allowlist (IT xem; Analyst/Admin sửa)
```
Thanh điều hướng bên trái (máy tính) hoặc thanh dưới (điện thoại); góc phải: tên người dùng, vai trò, nút VI/EN.

## 5. Quy tắc thiết kế chung
> Ngôn ngữ thiết kế đầy đủ (màu, chữ, bố cục, điều cấm): `docs/design/DESIGN.md`. Phần dưới là quy tắc nghiệp vụ.

- **Điểm và mức độ:** 0–39 *Thấp* (xám), 40–69 *Trung bình* (vàng/cam), 70–100 *Cao* (đỏ). Luôn có chữ đi kèm màu — không truyền đạt chỉ bằng màu.
- **IOC luôn hiển thị dạng defang** (`evil[.]com`), có nút sao chép giá trị thật.
- **Thuật ngữ:** giữ tiếng Anh (IOC, CVE, TTP), có tooltip giải thích tiếng Việt lấy từ Từ điển CTI.
- **Thời gian:** giờ Việt Nam, dạng "2 giờ trước" kèm tooltip ngày giờ đầy đủ.
- **Trạng thái trống và lỗi:** mỗi khối có thông báo khi không có dữ liệu ("Chưa có cảnh báo nào trong 7 ngày — tốt!") và khi lỗi ("Không lấy được dữ liệu từ OpenCTI, thử lại sau").
- **Thành phần giao diện** dùng shadcn/ui; biểu đồ dùng Recharts; icon dùng lucide.

## 6. Yêu cầu phi chức năng
| Mục | Yêu cầu |
|---|---|
| Tốc độ | Tổng quan tải < 2 giây (có cache 5 phút); tra cứu < 1 giây |
| Thiết bị | Dùng tốt ở màn hình 360 px (điện thoại) đến 1920 px |
| Ngôn ngữ | Mọi chữ hiển thị nằm trong file dịch `messages/vi.json`, `messages/en.json`; không viết cứng chữ trong component |
| Truy cập | Điều khiển được bằng bàn phím; độ tương phản đạt WCAG AA |
| Bảo mật | Không có secret trong mã frontend; CSP chặn script lạ; văn bản báo cáo hiển thị dạng text (không render HTML) để chống XSS; mọi hành động ghi được lưu nhật ký |
| Kiểm thử | Test API bằng pytest; test giao diện chính bằng Playwright (luồng tra cứu, luồng duyệt) |

## 7. Ngoài phạm vi
Ứng dụng di động riêng; thông báo đẩy (dùng Telegram/Hermes thay thế); nhiều doanh nghiệp trên một portal (multi-tenant).

## 8. Thứ tự làm (gợi ý cho planner)
| Đợt | Nội dung | Mốc |
|---|---|---|
| P0 | Khung dự án: Next.js + FastAPI + docker, layout, điều hướng, VI/EN, vai trò giả lập | 24/11 |
| P1 | W02 Tra cứu (giá trị dùng ngay nhất) | 01/12 |
| P2 | W01 Tổng quan | 08/12 |
| P3 | W04 Tài sản, W03 Lỗ hổng | 15/12 (MVP) |
| P4 | W05 Duyệt bản nháp AI và hành động | 12/01 |
| P5 | Đánh bóng, Playwright, kiểm thử vượt quyền (F08) | 31/01 |
