# Fixture restricted catalog X01

Các file trong thư mục này hoàn toàn tổng hợp, được viết tay để kiểm thử loader cục bộ. Chúng không sao
chép tên, nội dung, release, tag, commit hoặc snapshot của MITRE ATT&CK.

## Provenance bắt buộc

`synthetic-catalog.json` khai báo `x_phonghoa_provenance`:

- `kind`: `synthetic`;
- `generator`: `hand-authored-test-fixture`;
- `purpose`: `restricted-catalog-test`;
- toàn bộ `mitre_release`, `source_url`, `release_tag`, `commit`: `null`.

Fixture hợp lệ chỉ dùng mã minh họa `T1000`, `T1000.001`, `T2000` và tên bắt đầu bằng `Synthetic`.
SHA-256 được tạo từ đúng byte của file trong manifest bằng chứng khi chạy nghiệm thu.

## Fixture lỗi có chủ đích

- `invalid-duplicate-key.json`: phá trường gốc bằng cách lặp khóa `type`; loader phải trả `invalid_json`.

Các fixture lỗi là dữ liệu test không tin cậy, không được dùng làm catalog vận hành.
