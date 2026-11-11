# Browser acceptance W04 Technology

Trạng thái: **UNVERIFIED**.

Phiên implementation này không có bề mặt browser/computer OpenMausBot phù hợp. Không mở browser bằng shell,
Playwright hoặc provider thay thế, không giả viewport. Mã frontend, build production và helper bounded đã hoàn
tất; các case CRUD/403/committed recovery/unknown recovery cùng viewport desktop/360 px phải được chạy bằng
bề mặt OpenMausBot theo `tools/local_integration/README.md`.
