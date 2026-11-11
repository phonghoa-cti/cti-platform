# W03 integration wire fixtures

Các JSON này là response tổng hợp được capture từ API thật bằng
`tools.local_integration.tests.run_w03_matrix`; không gọi Internet, CISA hay OpenCTI.
Chúng được lưu trong repo để wire test chạy mặc định, không phụ thuộc đường dẫn evidence trên máy.

Tái tạo từ root repo:

```powershell
..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w03_matrix --output ..\w03-integration-rework-evidence\http-matrix.json --evidence-dir ..\w03-integration-rework-evidence\http
```

Sau khi review output mới, có thể chạy test trực tiếp với capture đó bằng biến tùy chọn
`W03_WIRE_DIR=..\w03-integration-rework-evidence\http\wire`; không ghi đè fixture mặc định tự động.

| File | SHA-256 |
|---|---|
| `detail.json` | `cbd39dcdadc0857c5ee93646cda13c7b50de9bb5388cdb76fdce93c28ef3db05` |
| `empty.json` | `b2ea793ec2c54708ff7f4c2976187bbb297ad996a5d3fb9a15007d70f7053291` |
| `near-cap.json` | `4fe1472e60c74ca0c69cc1e1d0fc6988721d4958fa12d634c5cf99fddd48f140` |
| `over-cap.json` | `08f50e839eb70dfd1dc20f541ad450299c487f770d291fc70d7a17a72fa8ceab` |
| `snapshot-changed.json` | `55a8ec40e05099b0edab64b2087009ac25ef6c5c3dd551cccdbee4fe5743aa0b` |
| `summary.json` | `216e32b1207b96e83658354495ad162aa3e16fb007ffbfa5558931f443f06c7c` |
| `unavailable.json` | `08f50e839eb70dfd1dc20f541ad450299c487f770d291fc70d7a17a72fa8ceab` |
| `w03-forbidden.json` | `ed10e98418d6ddad3cd83b8e578ed36b66fcfd15d059635e71e4e3321cd63fe4` |
| `w03-missing-token.json` | `01d9f2da5e721f59cb87ce572d28bb5b596d978f71f448eb1a12dd978877873f` |
