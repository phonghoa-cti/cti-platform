# Browser observations W04

Surface: OpenMausBot Browser tab. Viewport ảnh: 1280 × 720. Recorded step ID: không được công cụ trả về.

## CRUD + lookup

- Tạo `company.example` và `8.8.8.0/24` trên `/tai-san`.
- `/tra-cuu` hiện nhãn tài sản cho `mail.company.example`, `8.8.8.7` và URL `https://mail.company.example/path?q=synthetic`; URL vẫn ở trạng thái chưa có dữ liệu đe dọa.
- Sửa note domain, UI hiện `v2`; xóa domain có xác nhận; lookup lại không còn asset-match.
- Trace có POST x2, PUT x1, DELETE x1 và các GET lookup; DB summary: 2 row, 1 active, 4 audit.

## Quyền 403

- GET `/api/assets` trả 403 và màn hình báo không có quyền.
- Thử lưu `forbidden.example`; POST trả 403.
- DB summary: 0 asset, 0 audit.

## Refresh 503 sau commit

- UI hiện thông báo đã lưu nhưng chưa tải lại danh sách và không gửi lại thao tác ghi.
- Bấm `Tải lại danh sách`; bản ghi `refresh-button.example` hiện `v1`.
- Trace: GET 200 ban đầu; POST 201 x1; GET 503; GET 200. DB summary: 1 asset, 1 audit.

## Unknown outcome

- UI hiện thông báo chưa xác định thao tác đã ghi hay chưa và không tự gửi lại.
- Bấm `Tải lại danh sách`; bản ghi `unknown-button.example` hiện `v1`.
- Trace: GET 200 ban đầu; POST 503 x1 (gateway che response sau khi backend commit); GET 200. DB summary: 1 asset, 1 audit.

## Cleanup và giới hạn

- Tất cả state JSON ghi `stopped`, `gateway_port_closed=true`, `temp_root_removed=true`.
- Mobile 360 px UNVERIFIED vì bề mặt Browser tab không cung cấp thao tác đổi viewport.
