# F22 — Nhật ký kiểm toán hợp nhất và hồ sơ PIR

- Người phụ trách: [NHÓM ĐIỀN] (Web)
- Issue: [NHÓM ĐIỀN]
- Trạng thái: Chờ duyệt — lát cắt MVP đã có code thử nghiệm offline (B30), 27/11/2026.
- Liên quan: F18 dòng 1 (Activity monitoring → audit portal) và dòng 13 (PIR); ADR-0018 (không dùng mã Enterprise
  OpenCTI, viết mới hoàn toàn); F21 (outbox duyệt/gửi), W03 (danh sách CVE khớp tài sản), F19 (playbook, dùng PIR sau).

## Mục tiêu (1–2 câu)

Ghi lại "ai làm gì, lúc nào, lên đối tượng nào, kết quả ra sao" vào một nhật ký **chỉ ghi thêm** có chuỗi băm để
phát hiện bị sửa; đồng thời cho doanh nghiệp khai báo nhu cầu tình báo ưu tiên (PIR) để sắp CVE theo mối quan tâm.

## Người dùng và tình huống

- Admin doanh nghiệp: xem/lọc nhật ký khi cần giải trình (ví dụ "ai đã duyệt gửi báo cáo tuần?"), kiểm tra chuỗi
  còn nguyên vẹn.
- Analyst/IT: muốn danh sách CVE (W03) đưa lên đầu những gì liên quan hãng/sản phẩm/từ khóa doanh nghiệp quan tâm.

## Đầu vào / Đầu ra
| | Mô tả | Ví dụ |
|---|---|---|
| Đầu vào | Thao tác duyệt/gửi F21, thay đổi PIR; hồ sơ PIR do admin nhập | `PUT /api/pir` `{"vendors":["Fortinet"],"min_cvss":9}` |
| Đầu ra | `GET /api/audit` (lọc actor/action/target/since/until/limit), `GET /api/audit/verify`, `GET/PUT/DELETE /api/pir`, `GET /api/cves?pir=true` có `pir_score`, `pir_reasons` | `{"ok":true,"checked":3,"broken_at":null}` |

## Thiết kế ngắn

- `portal_api/audit_log.py`: bảng SQLite `audit_log(at UTC, actor, action, target, result, detail, prev_hash,
  row_hash)`; `row_hash = SHA-256(JSON chuẩn hóa + prev_hash)`; trigger chặn UPDATE/DELETE; ghi trong
  `BEGIN IMMEDIATE` để không rẽ nhánh chuỗi; `verify_chain()` trả dòng đầu tiên bị lệch.
- `portal_api/pir.py`: một hồ sơ cho mỗi triển khai (single-tenant W00): vendors, products, sectors, keywords,
  min_cvss. `score_cves()` là hàm thuần: vendor +40, product +40, keyword trong id/tiêu đề +15, CVSS ≥ ngưỡng +20;
  sắp ổn định (cùng điểm giữ thứ tự W03).
- `portal_api/governance_api.py`: route; nhật ký không có route ghi/xóa. PIR ghi cần admin + Origin portal.
- F21 `decide`/`send` ghi nhật ký cả thành công lẫn thất bại.

## Tiêu chí chấp nhận (kiểm tra được)
- [x] Mốc thời gian lưu UTC dạng `YYYY-MM-DDTHH:MM:SSZ` kể cả khi đồng hồ ở múi +07.
- [x] UPDATE/DELETE trực tiếp bằng SQL bị chặn; sửa dữ liệu (sau khi bỏ trigger) bị `verify_chain` phát hiện.
- [x] `GET /api/audit` chỉ admin; query lạ → 422; không có store → 503 (fail-closed).
- [x] Duyệt/gửi F21 sinh dòng `dissemination.decide` / `dissemination.send` với `success`/`failure`.
- [x] CRUD PIR: analyst đọc, admin ghi/xóa; khóa lạ hoặc giá trị sai → 422; thay đổi PIR được ghi nhật ký.
- [x] `GET /api/cves` mặc định không đổi; `?pir=true` sắp lại theo PIR; giá trị khác `true/false` → 422.

## Không làm trong phạm vi này

- Đa tenant (cột tenant), màn hình portal, xuất CSV nhật ký, chính sách lưu giữ/xoay vòng.
- Gom nhật ký cũ W03/W04/W05/F21 vào bảng mới (các bảng audit riêng vẫn giữ nguyên).
- Dùng `sectors` để chấm điểm (dữ liệu CVE chưa có ngành); bản tin PIR qua F19/Hermes.

## Rủi ro và câu hỏi còn mở

- Chuỗi băm chỉ **phát hiện**, không chống được người có quyền ghi file viết lại cả chuỗi: cần định kỳ sao lưu
  hash cuối ra nơi khác (CHƯA CHỐT nơi lưu).
- Lỗi ghi nhật ký trong luồng F21 hiện chỉ log, không hủy thao tác đã gửi (tránh gửi lặp); cần chốt có chuyển sang
  fail-closed trước thao tác hay không.
- `?pir=true` chỉ sắp lại **trong trang hiện tại** để không phá con trỏ phân trang W03.
- Chưa có cấu hình đường dẫn SQLite qua Settings/env; app nhận `audit_log`/`pir_store` qua `create_app`.

## Chia task (mỗi task ≤ 2 giờ cho agent)
1. (Xong B30) Module audit + verify + route đọc; nối F21.
2. (Xong B30) PIR store + hàm chấm + cờ `pir` W03.
3. Settings/env cho đường dẫn SQLite, nối khởi động thật.
4. Gom audit W03/W04/W05 về `AuditLog`; xuất CSV; màn hình portal.
5. Dùng PIR trong F19 playbook và bản tin Hermes.
