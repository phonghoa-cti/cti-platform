# R1–R5 RED→GREEN

- Target trước sửa: `9d278cfc1f9cbc2b6236b06c8e1c7541d7e7aed5`.
- Probe Leader nguyên trạng RED: 26 failed / 1 passed, exit 1.
- Regression repo sau khi thêm test trước: 25 failed / 9 passed, exit 1.
- Root cause: membership/hash trước type validation; URL parser exception/userinfo/control; chỉ lstat node cuối;
  `sorted(iterdir())` vật hóa toàn directory; fingerprint `read_bytes` không map lỗi.
- Target sau sửa: `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`.
- Regression repo GREEN: 34 passed, exit 0.
- Probe Leader nguyên trạng GREEN: 27 passed, exit 0.

Probe Leader giữ SHA-256 `e472ff28687beca7341b06e63a9ba86768d3be17db70ad3404f3e8b56c4c02c6`.
