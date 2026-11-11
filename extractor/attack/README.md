# X01 restricted ATT&CK catalog ngoại tuyến

Module `phonghoa_extractor.attack_catalog` đọc một STIX bundle tổng hợp đã ghim SHA-256 và cho phép tra
cứu cú pháp/trạng thái mã kỹ thuật Enterprise. Đây là **catalog giới hạn** cho kiểm thử, không phải bộ
validator STIX đầy đủ, RAG hay bằng chứng tương thích với dữ liệu MITRE thật.

## Contract

- Chỉ nhận pin `kind=synthetic`, provenance `hand-authored-test-fixture`, metadata MITRE để `None`.
- Kiểm giới hạn byte và SHA-256 trước UTF-8/JSON; JSON từ chối khóa trùng, số đặc biệt/quá lớn và độ sâu
  vượt giới hạn.
- Chuẩn hóa version theo `modified` UTC chính xác đến 18 chữ số thập phân, từ chối payload xung đột và
  không hồi sinh version/cạnh đã `revoked`.
- Kiểm quan hệ `subtechnique-of` theo chiều child → parent; active child cần đúng một active parent.
- Catalog, record và kết quả tra cứu là bất biến. Mọi kết quả có `semantic_status=unverified` và
  `operational_draft_eligible=false`.

`AttackCatalogError` chỉ hiển thị mã lỗi an toàn; không kèm đường dẫn, payload hoặc nội dung exception.
Module không gọi mạng, không ghi draft và chưa được nối vào C4.
