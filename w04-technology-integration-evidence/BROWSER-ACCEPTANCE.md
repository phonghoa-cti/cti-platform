# Bằng chứng browser W04 Technology

Ngày chạy: 12/11/2026 (UTC+07). Bề mặt: Browser tab OpenMausBot, desktop thật. Fixture/JWT/SQLite tổng hợp
loopback; không gọi Internet, lab, Cloudflare, OpenCTI hoặc feed.

## Kết quả

| Case | Quan sát UI | Trace | DB/audit trước cleanup | Kết quả |
|---|---|---|---|---|
| CRUD + duplicate/stale | Tạo Fortinet/FortiOS 7.2.1 v1; sửa note + software version thành 7.2.2 v2; duplicate giữ form và báo conflict; cập nhật ngoài lên v3 rồi browser stale báo conflict; xác nhận xóa và danh sách rỗng | `POST 201`, `PUT 200`, `POST 409`, `PUT 200`, `PUT 409`, `DELETE 204`; GET refresh chỉ đọc | 1 row soft-deleted, 0 active, 4 audit: create, browser update, setup stale update, delete; duplicate/stale không thêm audit | PASS |
| leader 403 | Tab Công nghệ hiển thị “Bạn không có quyền quản lý công nghệ.”, không có thông báo lưu thành công | Chỉ `GET /api/assets/technologies 403` và GET assets 403 | 0 technology row, 0 technology audit, assets/audit 0 | PASS |
| committed recovery | Sau POST, UI giữ “Đã lưu nhưng chưa tải lại…”; bấm tải lại lần đầu vẫn giữ notice; lần hai hiện Microsoft/Exchange 2019 v1 | Technology `POST 201 → GET 503 → GET 503 → GET 200` | 1 active row, 1 audit; assets/audit 0 | PASS |
| unknown outcome | POST hiển thị trạng thái chưa rõ và khóa thêm; đổi sang tab Tên miền rồi quay lại vẫn khóa; GET đối soát 503 không mở khóa, GET 200 mới hiện Cisco/IOS XE 17.9 v1 | Technology `POST 503 → GET 503 → GET 200`; GET assets khi đổi tab chỉ đọc | 1 active row, 1 audit; assets/audit 0 | PASS |

Mutation count/audit lấy từ SQLite snapshot, không suy từ screenshot. Trace chỉ chứa counter/method/path/status,
không có JWT, key hoặc header danh tính.

## Artifact

- `browser-screenshots/crud-created-v1.png`, `crud-deleted.png`.
- `browser-screenshots/leader-403.png`.
- `browser-screenshots/committed-second-get-503.png`, `committed-recovered.png`.
- `browser-screenshots/unknown-reconciled.png`.
- Mỗi thư mục `browser-technology-*` có `assets-before-cleanup.sqlite`, `db-summary.json`,
  `gateway-trace.jsonl`; file state cùng tên ở thư mục evidence chứng minh cleanup.

## Giới hạn

- Công cụ Browser tab không trả `Recorded as step`, nên không có step ID.
- Không có điều khiển resize viewport thật; mobile 360 px **UNVERIFIED**, không giả bằng CSS.
