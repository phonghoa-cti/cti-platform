# Rework R1–R3 — lệnh và exit

Ngày chạy: 11/11/2026. Runtime/test/demo ngoại tuyến.

- Review SHA-256:
  `b159b9f814fea89680a48d2780b47e863059daa9470070d4541ef56dc09e3f70`.
- Probe SHA-256 trước/sau:
  `a1896975905607b0cb607b7e5a76a2d22256f8828bd9ee003b37b7f7ed0e11e9`.
- Probe RED nguyên trạng: 5 failed, 1 passed, exit 1.
- Regression nội bộ RED: 6 failed, 7 passed, exit 1.
- Regression nội bộ GREEN chọn lọc: 13 passed, exit 0.
- Probe GREEN nguyên trạng: 6 passed, exit 0.
- Bộ test mục tiêu mở rộng: 107 passed, exit 0.
- Ruff check ba file Python sửa: exit 0.
- Ruff format-check ba file Python sửa: exit 0, 3 files formatted.
- `git diff --check`: exit 0.
- Commit local: `732685f7f774fee925840cb7d97b894547bfd119`, exit 0.
- Tree đã test/HEAD tree:
  `7280781de9dbe4a4a90a8977d60425ccdfda3238`.
- Demo HEAD TXT hai lần: exit 0/0, bytes giống nhau.
- Demo HEAD PDF hai lần: exit 0/0, bytes giống nhau.
- Input hash TXT/PDF trước/sau giống nhau; temp mới sau demo: 0.

Lượt gọi RED đầu dùng ký tự nối dòng kiểu Bash trong PowerShell nên không sinh
output test và tạo artifact `test_localsystem.txt` 12 byte (`I have run`) trong
target. Đã đổi sang một dòng PowerShell, không lặp cách lỗi đó; artifact được
xóa theo đúng leaf và target sạch. Không có code sản phẩm nào được sửa trước
lần RED hợp lệ.
