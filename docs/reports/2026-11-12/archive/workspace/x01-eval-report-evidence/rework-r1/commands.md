# R1 commands

1. Băm probe Leader trước/sau mỗi run để chứng minh file bất biến.
2. Chạy regression mới `-k equivalent_noninteger_ttp_counts` trước fix: 18 fail.
3. Sửa validator: exact keys, `_integer` nghiêm ngặt cho `technique_items` và tám count con, rồi mới so thống kê.
4. Chạy regression mới sau fix: 18 pass.
5. Chạy nguyên probe Leader trước và sau commit: mỗi lần 20 pass.
6. Chạy toàn bộ reporter suite post-commit: 56 pass.
7. Chạy Ruff check, Ruff format check và `git diff --check HEAD^ HEAD`: exit 0.

Không chạy evaluator regression/full suite/browser/model/network/DB/lab vì producer không đổi và brief không yêu cầu.
