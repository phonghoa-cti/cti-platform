# W05 API review R1–R3 — bằng chứng RED

Ngày 11/11/2026, base `feac804818713a314d7db6bdc065b3a676234f32`, cwd `cti-w05-backend`.

Lệnh:

`.venv\Scripts\python.exe -m pytest -o addopts= -q portal_api\tests\test_w05_api.py -k "audience_string_or_array_membership or oversized_integer_inputs or unexpected_store_error"`

Kết quả exit 1: `6 failed, 1 passed, 81 deselected in 1.03s`.

- R1: JWT RS256 hợp lệ với `aud=[AUD]` và `aud=[extra,AUD]` cùng trả 401 thay vì 200.
- R2: RuntimeError tổng hợp được làm sạch thành 503 nhưng thiếu `Cache-Control` (và `Vary`).
- R3: `limit`, `before_id` và path ID dài 5.000 chữ số cùng trả 503 thay vì 422.

Các test được chạy đỏ trước khi sửa `portal_api/auth.py` và `portal_api/app.py`.
