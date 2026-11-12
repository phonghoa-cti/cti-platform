# W03 product boundary — kiểm chứng cuối

Base: `d09929311b4b6447aac8b2ec6adac5999beda25d`
HEAD: `1401402122a58baa7dba2b3f1a75abc080baabab`
Branch: `fix/w03-product-boundary-20261112`

## PASS

1. Focused boundary/status:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'affected_product_boundary or affected_vendor_boundary or affected_product_controls or product_256_get_put_history or product_257_dataset or w03_synthetic_product_and_source_contract'
```

Exit `0`; `12 passed, 106 deselected`.

2. Hai module, tách test wire nền:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'not checked_in_wire_fixtures_equal_real_api_responses'
```

Exit `0`; `117 passed, 1 deselected`.

3. Ruff:

```powershell
& $python -m ruff check portal_api/cves.py portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py
& $python -m ruff format --check portal_api/cves.py portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py
```

Hai lệnh exit `0`; `All checks passed!`; `3 files already formatted`.

4. Git: commit exit `0`; `git status --short` rỗng. Diff từ base: 5 file allowlist, `+90/-6`.

## FAIL nền đã cô lập

Lệnh chính xác hai module:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py
```

Exit `1`; `117 passed, 1 failed`. Test duy nhất:
`test_checked_in_wire_fixtures_equal_real_api_responses`.

Đối chiếu field-level cho thấy chỉ `body.source.dataset_id` khác:

- bytes fixture checkout CRLF: SHA-256 `1c44a50597b702259dc89b242f4e16cfd37f7a574efda48743e61a440c51a872`;
- bytes blob LF mà wire fixture ghim: SHA-256 `89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73`.

Tree nguồn Engineer tại cùng base cũng có hash CRLF `1c44...`; lỗi không do delta product. Fixture/wire nằm ngoài allowlist nên không sửa.

## UNVERIFIED

Không sửa/chạy capture product256 integration, browser, gateway thật, feed/OpenCTI, lab, cloud hoặc production. Capture integration hiện vẫn cố ý kỳ vọng product256 trả 503 và phải do Engineer cập nhật sau review đầu vào này.
