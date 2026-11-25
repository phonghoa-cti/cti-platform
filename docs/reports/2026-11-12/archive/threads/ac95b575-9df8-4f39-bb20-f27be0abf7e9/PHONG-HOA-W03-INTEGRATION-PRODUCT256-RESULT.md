# W03 STATUS integration — product256 và WIRE-01

Ngày 12/11/2026. Kết quả lát cắt: **PASS local delta**. Đây không phải nghiệm thu toàn W03-S1, browser chặng A/B không chạy lại và lab/production vẫn chưa xác minh.

## Git

- Tree: `$WORKSPACE\cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Base: `170a38bb92fee09bd2e917faedc8de6342046b54`
- Backend cherry-pick: `9721523` từ đúng `1401402122a58baa7dba2b3f1a75abc080baabab`
- WIRE-01: `3973331 fix(w03): keep wire fixture checkout on LF`
- Capture/parser: `867bdcaeffded177ee119fe5e05015c4700979db`
- Final status: sạch (`git status --short --branch` chỉ in tên branch).
- Delta từ base: 9 file, `+170/-32`; đúng allowlist. Không đổi UI runtime, auth, audit, gateway policy, dependency hoặc RUNS.

## Thay đổi

- Backend nhận product tối đa 256 Unicode code point; product 257 vẫn fail-closed. Vendor vẫn tối đa 128; vendor 129 bị chặn.
- `.gitattributes` chỉ có rule `portal_api/tests/fixtures/w03-cves-synthetic.json text eol=lf`.
- Capture HTTP thật tạo product 256 bằng 256 ký tự astral, product 257 và vendor 129 trả `503 status_unavailable`; boundary cũ vẫn chứng minh vendor 128.
- Test Frontend đưa response product 256 từ capture qua `parseCveStatusResponse` production, đồng thời đưa hai error envelope quá giới hạn qua HTTP provider production.

## Kiểm tra đã chạy

1. RED WIRE-01 tại HEAD base:
   - `python -m pytest -o addopts='' portal_api/tests/test_cves_api.py::test_checked_in_wire_fixtures_equal_real_api_responses`
   - exit `1`, `1 failed`; sai khác dataset id do fixture checkout CRLF.
2. RED capture sau cherry-pick Backend:
   - `PYTHONPATH=<repo> python tools/local_integration/tests/capture_w03_status_wire.py --output <evidence>/capture-red`
   - exit `1`, lỗi đúng mong đợi: `product 256 unexpectedly passed CVE dataset validation` vì harness còn kỳ vọng cũ.
   - Lần gọi đầu không đặt `PYTHONPATH` lỗi import; không phải lỗi product và đã lưu riêng.
3. Wire hiện tại:
   - cùng test WIRE-01 ở trên; exit `0`, `1 passed`.
4. Capture:
   - `PYTHONPATH=<repo> python tools/local_integration/tests/capture_w03_status_wire.py --output <evidence>/capture`
   - exit `0`; `12` response, capture `PASS`.
   - status: product256 `200`, product257 `503`, vendor129 `503`; vendor128 nằm trong boundary response `200`.
5. Parser Frontend production:
   - `W03_STATUS_WIRE_REQUIRED=1 W03_STATUS_WIRE_FIXTURE_DIR=<evidence>/capture npm test -- --run tests/cve-status-wire-capture.test.ts`
   - RED đầu: `1 failed/6 passed` do assertion JS đếm UTF-16 (`512`) thay vì code point.
   - GREEN sau sửa assertion `[...value]`: exit `0`, `7 passed`.
6. Focused Backend:
   - `python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'affected_product_boundary or affected_vendor_boundary or affected_product_controls or product_256_get_put_history or product_257_dataset or w03_synthetic_product_and_source_contract'`
   - exit `0`, `12 passed, 106 deselected`.
7. Ruff:
   - `python -m ruff check portal_api/cves.py portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py tools/local_integration/tests/capture_w03_status_wire.py`
   - exit `0`, `All checks passed!`.
8. `git diff --check`: exit `0`; chỉ có cảnh báo Git rằng các file không có rule riêng có thể dùng CRLF trên Windows.

## Checkout Git mới với autocrlf=true

- Clone local mới được tạo bằng `git -c core.autocrlf=true clone --no-hardlinks --local --branch feat/w03-status-integration-20261112 ...`.
- `git check-attr`: `text: set`, `eol: lf` cho đúng fixture.
- Raw fixture: `1361` byte, `CRLF=0`, `LF=1`, SHA-256 `89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73`.
- Test WIRE-01 trong checkout mới: exit `0`, `1 passed`.
- Checkout kiểm chứng đã xóa sau khi lưu log; source tree vẫn sạch.

## Bằng chứng và cleanup

- Evidence: `$THREADS\ac95b575-9df8-4f39-bb20-f27be0abf7e9\w03-product256-integration-evidence`
- `manifest.sha256`: 51 artifact được băm trước khi thêm chính manifest.
- Helper do capture của lượt này đã thoát; clone kiểm chứng đã xóa.
- Có gateway cũ PID `31176`, listener `127.0.0.1:52963`, khởi tạo lúc `06:04:48`, trước lượt này hơn hai giờ. Không phải helper do lượt product256 tạo; giữ nguyên vì ngoài phạm vi và có thể thuộc bằng chứng/browser cũ.

## Chưa xác minh

- Không chạy lại browser chặng A/B, full suite, lab, cloud, LLM thật hoặc production.
- Không kết luận toàn W03-S1 hoàn tất; candidate cần Leader nghiệm thu.
