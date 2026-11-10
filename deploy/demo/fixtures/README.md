# Fixture STIX 2.1 cho demo F01

`demo-bundle.json` là dữ liệu **tổng hợp**, chỉ dùng để review và thử đường nhập. Nó không mô tả chiến dịch,
nguồn CTI hoặc quan hệ ATT&CK có thật.

- Domain dùng hậu tố dành riêng `.example`.
- IP `198.51.100.42` thuộc TEST-NET-2 dành cho tài liệu.
- Tên/description và external reference đều ghi rõ nguồn tổng hợp.
- ID/timestamp cố định để fixture tái hiện được; không lấy ID từ hệ thống thật.
- Marking dùng STIX 2.1 TLP:WHITE chuẩn, tương ứng nhãn chia sẻ công khai TLP:CLEAR hiện hành. Analyst vẫn phải
  duyệt quyền dữ liệu và policy trước khi nhập.

## Kiểm tra đã thiết kế

Validator được ghim ở `stix2-validator==3.3.2` trong `.venv` kiểm schema, pattern và tham chiếu SRO:

```powershell
.venv\Scripts\stix2_validator.exe --version 2.1 --strict --enforce-refs deploy/demo/fixtures/demo-bundle.json
```

Hai negative case phải sửa **bản tạm ngoài repo**: một bản làm pattern sai, một bản trỏ relationship tới ID
không có trong bundle. Validator phải trả exit khác 0 cho từng bản. Không sửa fixture gốc để tạo negative case.

## Manifest

- Số object: **7**.
- Số relationship: **1**.
- Loại object: marking-definition, identity, ipv4-addr, domain-name, indicator, relationship, report.
- SHA-256: `aa2cdb91575d2cf8b56a16ac48e1b1d7147a5512698b6c1ffc525ea937336195`.

Parse/validate chỉ chứng minh cấu trúc fixture. Nó không chứng minh OpenCTI boot, import thành công, chống trùng
hoặc dữ liệu hiển thị đúng trên lab.
