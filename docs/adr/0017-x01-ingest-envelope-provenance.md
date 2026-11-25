# ADR-0017: Import envelope X01 độc lập với provenance SQLite

- Trạng thái: Chấp nhận
- Ngày: 11/11/2026

## Bối cảnh

X01 local ingest đã xuất envelope TXT/PDF, còn W05 đã có payload pending, review/selection và STIX. Cần nối hai
phần mà không kéo PDF parser/model vào W05, không sửa payload đã trích và không tạo đường ghi OpenCTI tự động.

## Quyết định

Dùng CLI importer độc lập. Nó kiểm envelope strict, yêu cầu creator từ tham số tin cậy, migrate store v2→v3 trong
một transaction rồi ghi draft cùng provenance trong transaction thứ hai. Bảng provenance có khóa duy nhất trên
hash JSON canonical của toàn envelope; duplicate chỉ hợp lệ khi creator giống nhau. Reader W05 chấp nhận cả v2
và v3 nhưng không migrate; writer importer mới yêu cầu v3 dưới khóa `BEGIN IMMEDIATE`.

## Phương án đã cân nhắc

1. Thêm `--db` vào producer: ít lệnh hơn nhưng ghép parser với store và làm failure boundary khó hiểu.
2. Importer độc lập (chọn): tái dùng validator/store, phạm vi nhỏ và giữ hai checkout tách biệt.
3. Service/outbox mới: phù hợp async về sau nhưng thêm listener, retry protocol và quyền ngoài scope offline.

## Hệ quả và giới hạn

- Retry cùng envelope/creator là idempotent; đây không phải exactly-once qua crash hoặc mất response.
- `raw_sha256` PDF là tuyên bố provenance, không phải byte đã được importer tự xác minh.
- Migration thành công nhưng insert thất bại có thể để schema v3, không được để draft/provenance mồ côi.
- Không có bằng chứng browser, Cloudflare/JWKS thật, OpenCTI, lab hoặc production từ quyết định này.
