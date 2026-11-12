# W03 product boundary — RED/GREEN

Ngày kiểm: 12/11/2026. Worktree:
`$WORKSPACE\cti-w03-product-boundary`.

Interpreter:
`$WORKSPACE\cti-w03-read-backend\.venv\Scripts\python.exe`
(`Python 3.13.14`, pytest `9.2.0`). Không cài dependency.

## RED

Trước khi sửa `portal_api/cves.py`, chạy:

```powershell
& $python -m pytest portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'affected_product_boundary or affected_vendor_boundary or affected_product_controls or product_256_get_put_history or product_257_dataset' -q
```

- Exit: `1`.
- Count: `4 failed, 6 passed`.
- Fail đúng nguyên nhân thiếu boundary: product 129, product 256, product 256 astral trả 503; status product256 không có context.
- Các ca product128, vendor128/129, control và product257 đã giữ hành vi mong đợi.

## GREEN

Sau thay đổi tối thiểu `_text(value["product"], 128)` thành `256`, chạy lại cùng selector:

- Exit: `0`.
- Count: `10 passed`.

Kiểm cuối sau khi bổ sung regression 257/source contract:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'affected_product_boundary or affected_vendor_boundary or affected_product_controls or product_256_get_put_history or product_257_dataset or w03_synthetic_product_and_source_contract'
```

- Exit: `0`.
- Count: `12 passed, 106 deselected`.
- Bao phủ product 128/129/256 hợp lệ, 257 fail-closed; vendor 128/129 không đổi; 256 ký tự astral được đếm theo code point; Cc/Cf bị chặn; GET/PUT/GET/history product256 có đúng một status row và một audit; dataset257 không ghi status/audit.
