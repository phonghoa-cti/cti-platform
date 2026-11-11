# ADR 0006 — W03-R dùng SQLite read-only và cursor theo snapshot

## Trạng thái

Đã chấp nhận cho lát cắt W03-R cục bộ.

## Bối cảnh

`TechnologyStore._connect()` có thể tạo file SQLite khi path chưa tồn tại. W03-R chỉ được đọc và cursor phải
phát hiện cả thay đổi dataset lẫn technology giữa các trang, không được dùng offset dễ ghép hai snapshot.

## Quyết định

Kế thừa validation/list của `TechnologyStore`, override `_connect()` trong adapter W03 bằng SQLite URI
`mode=ro`. Cursor v1 chứa hash snapshot, hash context và CVE cuối trang; backend tự kiểm canonical encoding,
tính lại rank và xác nhận CVE cuối tồn tại. Không ký cursor vì nó không cấp quyền và mọi request vẫn xác thực.

## Hệ quả

- Path thiếu/DB lỗi trả 503 mà không tạo hoặc sửa file.
- Bất kỳ create/update/delete technology hay thay đổi dataset làm cursor cũ trả 409.
- Cursor không lộ metadata asset nhưng dài hơn offset đơn giản; thay filter/view/limit phải bắt đầu lại.
- Đây không phải bảo vệ chống người có quyền đọc sửa cursor; sửa sai chỉ bị từ chối, không tăng quyền.
