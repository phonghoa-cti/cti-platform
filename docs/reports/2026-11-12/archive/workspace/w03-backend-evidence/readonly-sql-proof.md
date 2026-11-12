# Bằng chứng chỉ đọc W03-R

Test `test_read_does_not_create_missing_database_or_modify_sql_state` gọi API với path SQLite không tồn tại và
xác nhận response 503 cùng `Path.exists() == false`. Với database hợp lệ, test đọc trước/sau bằng SQL:

- `SELECT type,name,sql FROM sqlite_master ORDER BY type,name`
- `SELECT * FROM technology_assets`
- `SELECT * FROM technology_asset_audit`
- `PRAGMA user_version`

Bốn kết quả phải bằng nhau sau GET thành công. R1 còn chụp cùng bốn kết quả trước/sau failure 404 sau dependency
read và failure 409 sau khi snapshot đã thay đổi; response không gây thêm row/version/audit/schema change. Các
test dataset lỗi chạy cùng adapter `mode=ro`; implementation không gọi `initialize`, DDL, transaction ghi hoặc
mutation W04. Suite portal R1 345/345 exit 0 bao gồm các test này.

Giới hạn: đây là bằng chứng SQLite cục bộ bằng dữ liệu tổng hợp, không phải lab/production hoặc filesystem có
quyền/driver khác.
