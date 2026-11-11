# Xuất final approved draft thành STIX 2.1

## Mục tiêu

CLI này đọc final approve audit trong SQLite v2 và tạo đúng một bundle STIX 2.1 ngoại tuyến. Nó không gọi
OpenCTI, không gửi mạng, không thay đổi database và không tạo manifest sidecar.

## Chuẩn bị dependency kiểm thử

Runtime exporter chỉ dùng Python standard library và `phonghoa_core`. Validator là dependency test riêng:

```powershell
uv pip install --python .\.venv\Scripts\python.exe `
  --require-hashes `
  -r .\requirements-stix-test.lock
```

## Chạy

```powershell
.\.venv\Scripts\python.exe extractor\draft\stix_export.py export-approved `
  --db .\drafts.sqlite `
  --id 1 `
  --exporter-config .\extractor\draft\examples\stix\exporter-config.example.json `
  --output .\approved-bundle.json `
  --timeout 5
```

Config mẫu là dữ liệu tổng hợp. Hãy dùng namespace/name do tổ chức quản lý trong cấu hình thật; TLP phải bằng
TLP snapshot. Không đưa subject/email người duyệt vào config vì Identity là exporter, không phải reviewer.

Output mới được publish nguyên tử theo điều kiện local NTFS bằng hardlink từ temp đã ghi hoàn chỉnh. Chạy lại
cùng bytes thành công mà không sửa file; output khác nội dung bị từ chối. Parent phải tồn tại và không được là
symlink/reparse. DB, sidecar SQLite, config và alias của chúng không thể làm output.
Alias tĩnh của DB/config vẫn đọc được; bộ bảo vệ áp dụng cho cả tên được nhập và đích đã resolve cùng các tên
`-wal`, `-shm`, `-journal` tương ứng.

Stdout thành công chỉ có `draft_id`, SHA-256 bundle và số object. Lỗi nghiệp vụ chỉ có một dòng stderr an toàn.
Bundle đạt validator 3.3.2 ở MUST/schema/ref và `strict except 103`; đây không phải bằng chứng import OpenCTI,
quyền chia sẻ TLP, reviewer mapping thật, lab hay production.
