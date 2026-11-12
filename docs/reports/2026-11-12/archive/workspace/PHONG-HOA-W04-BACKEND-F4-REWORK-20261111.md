# W04 — sửa nốt phân loại UNIQUE ở F4

Owner CTI Backend, một Sol medium trực tiếp, không giao tiếp người khác. Giữ task `W04-ASSETS-IMPLEMENT`, thread `12614171-9e62-4c0d-a75b-b7f852c15b02`, tree `cti-w04-assets-local`, branch `feat/w04-assets-local-20261111`. Base `5316422ef6091f48edca443f886358a4475d8e04`; không reset/recreate tree. Root tuyệt đối: `$WORKSPACE`.

## Đã kiểm, không làm lại từ đầu

Leader đọc delta 4 file +387/-44, kiểm đúng SHA/tree sạch, chạy assets + W02: 99 test exit 0; nguyên 7 probe QA hash không đổi đều đúng expected. F1–F3 và rollback F4 đã đạt phạm vi cục bộ này. Chưa nghiệm thu Backend vì F4 còn thiếu điều kiện đã ghi trong brief trước: UNIQUE không thuộc active asset canonical phải trả unavailable.

## Lỗi còn lại đã tái hiện

`AssetStore._raise_write_integrity()` dùng `SQLITE_CONSTRAINT_UNIQUE` + một row canonical đang tồn tại. Nó không xác định constraint nào bị lỗi, và update cùng canonical luôn tìm thấy chính row đang sửa.

Tạo bảng tổng hợp `synthetic_guard(value TEXT UNIQUE)`, seed `'taken'`; trigger BEFORE INSERT hoặc UPDATE ON assets chèn lại `'taken'`. Một asset `company.example` đã tồn tại. POST cùng canonical hoặc PUT chỉ đổi note đều thất bại vì `UNIQUE constraint failed: synthetic_guard.value`, nhưng API trả **409 asset_exists**, thay vì **503 assets_unavailable**. Asset/audit giữ 1/1, row/version không đổi: rollback đúng, phân loại sai.

Probe độc lập nguyên bản: `leader-w04-rework-acceptance-20261111/f4_unrelated_unique_probe.py`; raw `f4-http-results.json`, 2 FAIL, exit 1. Giữ nguyên các bằng chứng lịch sử. Lệnh từ root, sau khi đặt PYTHONPATH về target root/core/extractor và PYTHONUTF8=1:

```powershell
& .\cti-w02-lookup-api\.venv\Scripts\python.exe .\leader-w04-rework-acceptance-20261111\f4_unrelated_unique_probe.py <new-output-directory>
```

## Sửa và tiêu chí đạt

- Chỉ active canonical UNIQUE thực sự mới map 409. Xác định đúng constraint, không chỉ dựa error code + row có sẵn. Lỗi UNIQUE ở bảng/cột khác hoặc trigger phải 503; không lộ thông điệp SQLite cho client. Giữ transaction/rollback và duplicate thật 409.
- Sửa tối thiểu `portal_api/assets.py`, regression `portal_api/tests/test_assets_api.py`, `docs/PROGRESS.md`. Không đổi hợp đồng, schema, fixture, auth, W02 validator, Frontend hoặc RUNS.
- Thêm regression API cho hai ca ở probe, RED trên base rồi GREEN. Chạy nhóm assets một lần sau sửa; thêm kiểm duplicate thật create/update và audit lỗi đã có. Không cần chạy lại full portal hoặc W02 nếu không chạm chúng.
- Chạy nguyên probe mới với output riêng dưới `w04-assets-evidence/rework-f4-unique/`, bắt buộc 2/2 PASS và exit 0; không sửa probe Leader. Ruff check/format phần đổi, git diff --check, commit cục bộ/tree sạch.
- Trả base/head/delta/exit/count, bổ sung kết quả vào `PHONG-HOA-W04-ASSETS-RESULT.md`. Không push/PR/merge/deploy/browser/lab/network/secret. Nếu không phân biệt chắc constraint trong giới hạn hiện tại, trả lựa chọn cụ thể; không tự đổi hợp đồng lỗi.

Frontend tiếp tục độc lập trong tree riêng. Sau nghiệm thu Backend và Frontend, Leader nối hai phần rồi kiểm cùng cơ sở dữ liệu. Đây là lần sửa tiếp đúng F4, không mở thêm tính năng.
