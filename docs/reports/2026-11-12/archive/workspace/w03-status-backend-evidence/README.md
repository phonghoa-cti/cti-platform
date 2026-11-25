# W03-S1 Backend evidence

Nguồn duy nhất: worktree `cti-w03-status-backend`, base
`7ff6eb3af21d8de65836bfbf707396ae5690de0b`, commit
`b8957e63acc7497ba835e06c05e52f4b16ef136c`.

Sáu wire JSON trong thư mục này được xuất lại nguyên byte từ fixture đã kiểm bằng
`test_checked_in_status_wire_fixtures_come_from_real_api`: TestClient gọi app thật, JWT RSA tổng hợp, SQLite tạm,
dataset tổng hợp và timestamp cố định. Các trạng thái gồm unset, committed, review-required, history hai trang,
conflict và unavailable. Đây là API in-process cục bộ, không phải production capture.

`commands.txt` ghi lệnh, exit code và số test. `SHA256SUMS` khóa byte của wire. Không có secret/feed thật.

Chưa kiểm: frontend/gateway/browser, Cloudflare Access/JWKS/HTTPS thật, feed/CISA/OpenCTI, lab, deploy hoặc
production.
