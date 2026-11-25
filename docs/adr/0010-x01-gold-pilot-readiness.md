# ADR 0010: Validator readiness ngoại tuyến cho gold pilot

- Trạng thái: Chấp nhận
- Ngày: 11/11/2026

## Bối cảnh

X01 đã có normalizer IOC và ATT&CK catalog ghim, nhưng chưa có corpus thật được hai người gán nhãn. Chạy
benchmark ngay sẽ biến dữ liệu tổng hợp thành bằng chứng chất lượng sai mức.

## Quyết định

Tạo validator/readiness riêng cho pilot 5 record, dùng lại `phonghoa_core.ioc.normalize`, `load_catalog` và
`validate_technique`. Schema đóng, inventory có bound, report bất biến và writer no-clobber. Agreement chỉ đo
nhãn khai báo; TTP semantic luôn unverified.

## Hệ quả

Có thể kiểm cơ chế chuẩn bị dataset mà không cần model, mạng hoặc dữ liệu thật. Đổi lại, READY chỉ có nghĩa
hồ sơ đủ để adjudication; quyền nội dung, độc lập annotator, gold truth và chất lượng model vẫn chưa xác minh.
