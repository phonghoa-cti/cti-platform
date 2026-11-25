# Cleanup và lược dữ liệu

- Ma trận và mọi `LocalRun` đóng gateway/API, xóa temp root; Python harness cuối đạt 42/42.
- Helper bounded smoke `w04-technology-it` kết thúc `status=stopped`, `gateway_port_closed=true`,
  `temp_root_removed=true`; xem `helper-smoke-state.json`.
- Trace chỉ chứa `counter`, `method`, `path`, `status`; fault committed có `201,503,503,200`, fault unknown có
  `503,503,200`. Không suy mutation count từ ảnh; DB snapshot xác nhận đúng một row/audit cho mỗi fault.
- Quét evidence theo các mẫu chuỗi bí mật: không có match.
- Source Backend và Frontend không bị sửa. `node_modules` vật lý trong target là bản sao ignored phục vụ build,
  không được commit và không thay lock/dependency.
- Bốn helper browser Technology đều kết thúc `status=stopped`, `gateway_port_closed=true`,
  `temp_root_removed=true`; mỗi run giữ SQLite backup, summary và trace trước cleanup.
- Có sáu screenshot desktop từ Browser tab OpenMausBot. Công cụ không trả `Recorded as step`, nên không có
  step ID. Mobile 360 px không chạy vì Browser tab không có điều khiển resize viewport.
