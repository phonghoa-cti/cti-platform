# F21 — Báo cáo tình báo hoàn chỉnh và gửi có duyệt

- Người phụ trách: [NHÓM ĐIỀN] (Web)
- Issue: [NHÓM ĐIỀN]
- Trạng thái: Chờ duyệt — lát cắt MVP đã có code thử nghiệm offline (B28), 27/11/2026.
- Liên quan: F18 dòng 10 (Fintel templates), 11 (Dissemination list), 12 (Email template); ADR-0018 (không dùng mã
  Enterprise OpenCTI); W03 (đọc CVE khớp tài sản), W05 (mô hình duyệt), F07 (xuất dữ liệu).

## Mục tiêu (1–2 câu)

Tạo báo cáo lỗ hổng tuần bằng tiếng Việt cho một doanh nghiệp SME (CVE khớp tài sản, cờ KEV, số liệu tổng hợp) và
gửi tới danh sách người nhận của doanh nghiệp đó **chỉ sau khi có người duyệt** (preview → approve → send).

## Người dùng và tình huống

- **IT/analyst** của SME mở báo cáo HTML trên portal mỗi tuần, in ra PDF để họp nội bộ.
- **Analyst** tạo lô gửi (outbox) cho danh sách nhận; **admin** (người khác) xem trước đúng nội dung, duyệt rồi bấm
  gửi. Không có đường nào gửi tự động hoặc agent tự gửi (AGENTS.md mục 5).

## Đầu vào / Đầu ra

| | Mô tả | Ví dụ |
|---|---|---|
| Đầu vào | Read model W03 (`CveReadService`, view `detail`) + kho technology W04 | 2 technology, 3 CVE ứng viên |
| Đầu vào | Danh sách nhận (email hoặc Telegram chat id) do admin quản lý | `it@abc.example`, `-100123` |
| Đầu ra | Trang HTML tự chứa, không script, có CSS in A4 | `GET /api/reports/weekly-vulnerability` |
| Đầu ra | Lô outbox: mỗi người nhận một thư đã render, `content_hash` để duyệt | `POST /api/dissemination/outbox` |
| Đầu ra | Bản ghi audit: tạo lô, duyệt/từ chối, bắt đầu gửi, kết quả gửi | bảng `dissemination_audit` |

### API (MVP)

| Method + path | Quyền | Ghi chú |
|---|---|---|
| `GET /api/reports/weekly-vulnerability[?tlp=]` | it, analyst, admin | HTML, CSP `default-src 'none'`, `no-store` |
| `GET /api/dissemination/recipients` | analyst, admin | Chỉ người nhận đang hoạt động |
| `POST /api/dissemination/recipients` | admin | JSON `{display_name, channel, address}`, kiểm Origin |
| `DELETE /api/dissemination/recipients/{id}` | admin | Vô hiệu hóa (giữ lịch sử), kiểm Origin |
| `POST /api/dissemination/outbox` | analyst, admin | Tạo lô `pending_approval`; không gửi |
| `GET /api/dissemination/outbox/{id}` | analyst, admin | Preview đầy đủ subject/text/HTML từng thư |
| `POST /api/dissemination/outbox/{id}/decision` | admin | `{decision: approve/reject, content_hash}`; người duyệt ≠ người tạo |
| `POST /api/dissemination/outbox/{id}/send` | admin | Body bắt buộc `{confirm: true}`; chỉ lô `approved`, gửi đúng một lần |

## Thiết kế chính

- **Mẫu báo cáo và mẫu thư là tĩnh**, viết trong code (`portal_api/reports.py`, `portal_api/email_templates.py`);
  người dùng không tải mẫu lên. Biến thư nằm trong allowlist; render bằng `string.Template` sau khi **escape HTML mọi
  giá trị** (tương đương autoescape bật). Văn bản text/plain và subject bị bỏ ký tự điều khiển, gộp một dòng để chặn
  chèn header. Không thêm Jinja2 để tránh dependency mới khi lock có hash.
- **PDF**: lock hiện không có thư viện PDF thuần Python; MVP xuất HTML có `@page A4` và `@media print`. Bước PDF:
  mở trang báo cáo trên trình duyệt → In → "Lưu thành PDF". Renderer PDF nội bộ (ví dụ một thư viện thuần Python có
  license phù hợp) là task sau, cần rà license theo F18.
- **TLP** mặc định `TLP:AMBER` (dữ liệu tài sản nội bộ khách); cho chọn CLEAR/GREEN/AMBER/AMBER+STRICT; RED bị từ
  chối. Báo cáo ghi dataset id, thời điểm dữ liệu, loại nguồn và lưu ý "chưa đánh giá phiên bản".
- **Email** chỉ chứa tóm tắt + tối đa 10 CVE ưu tiên; chi tiết đầy đủ xem trên portal có xác thực. **Telegram** chỉ
  thông báo tối thiểu (số lượng, không mã CVE, không tên tài sản) theo F18 dòng 11.
- **Outbox** (SQLite riêng, `DisseminationStore`): `pending_approval → approved|rejected`, `approved → sending →
  sent|partially_failed`. Duyệt phải gửi kèm `content_hash` của nội dung đã preview; chuyển sang `sending` trong
  transaction `BEGIN IMMEDIATE` nên không gửi trùng. Kênh chưa có sender được ghi `skipped/no_sender`.
- **SMTP** chỉ đọc từ env: `F21_SMTP_HOST`, `F21_SMTP_PORT` (mặc định 587), `F21_SMTP_USERNAME`, `F21_SMTP_PASSWORD`,
  `F21_SMTP_FROM`, `F21_SMTP_TIMEOUT`. Luôn STARTTLS với `ssl.create_default_context()` (không tắt kiểm chứng chỉ).
  Test dùng sender giả; không test nào mở mạng.
- **Tenant**: portal hiện chạy một SME mỗi triển khai (chưa có khái niệm tenant trong `portal_api`), nên "danh sách
  nhận theo tenant" = danh sách trong DB của triển khai đó; tên doanh nghiệp truyền vào `create_app`.

## Tiêu chí chấp nhận (kiểm tra được)

- [x] Báo cáo chỉ đếm CVE khớp tài sản theo logic W03, có số KEV, phân bố CVSS, số technology bị ảnh hưởng.
- [x] Chuỗi độc hại trong tiêu đề CVE/tên doanh nghiệp bị escape trong HTML báo cáo và HTML thư.
- [x] Subject không chứa xuống dòng dù dữ liệu có `\r\n`; ký tự `$` trong dữ liệu không bị diễn giải lại.
- [x] Không gửi được lô chưa duyệt, lô bị từ chối, hoặc gửi lần hai; người tạo không tự duyệt; hash sai bị từ chối.
- [x] Audit có `outbox_created`, `outbox_approved`/`outbox_rejected`, `outbox_send_started`, `outbox_send_finished`.
- [x] Ghi từ trình duyệt phải đúng Origin; route cần JWT và đúng role; HTML có CSP và `no-store`.
- [ ] Nhóm duyệt mẫu nội dung tiếng Việt và chính sách nhận/hủy nhận.
- [ ] Chạy thử SMTP thật trên lab với tài khoản thử, không phải dữ liệu khách.

## Không làm trong phạm vi này

- Renderer PDF phía server, biểu đồ, giao diện web (portal/web) cho outbox.
- Gửi Telegram thật (chưa có sender), xác minh địa chỉ nhận (double opt-in), link hủy nhận, lịch gửi định kỳ.
- Đa tenant trong một DB; hai người duyệt cho gửi ra ngoài (câu hỏi mở F18 #4).
- Mọi mã hoặc mô phỏng tính năng OpenCTI EE (ADR-0018): toàn bộ viết mới.

## Rủi ro và câu hỏi còn mở

- Email đi qua máy chủ ngoài: báo cáo AMBER chỉ gửi tới người trong tổ chức; cần chính sách xác minh địa chỉ.
- Gửi nửa chừng khi tiến trình chết: lô kẹt ở `sending`, cần thao tác khôi phục thủ công (CHƯA CHỐT).
- Validate email đơn giản bằng regex ASCII; chưa hỗ trợ địa chỉ quốc tế hóa.
- Chọn thư viện PDF và license (F18 dòng 10) — CHƯA CHỐT.

## Chia task (mỗi task ≤ 2 giờ cho agent)

1. (Xong, B28) Mẫu báo cáo HTML + print CSS, mẫu thư tĩnh, outbox duyệt, API, test offline.
2. Giao diện portal: trang báo cáo, quản lý người nhận, màn hình preview/duyệt/gửi.
3. Sender Telegram tối thiểu + cấu hình env, test giả lập.
4. Renderer PDF nội bộ sau khi chốt thư viện/license.
5. Khôi phục lô kẹt `sending`, link hủy nhận, xác minh địa chỉ.
