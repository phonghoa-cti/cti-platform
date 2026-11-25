# ADR 0004 — Restricted ATT&CK catalog ngoại tuyến cho X01

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho fixture tổng hợp và đúng một release official v20.1

## Bối cảnh

X01 cần kiểm cú pháp và trạng thái mã kỹ thuật trước khi triển khai C4. Sau lát cắt tổng hợp, team đã review
snapshot Enterprise ATT&CK v20.1 local: 55.277.605 byte, SHA-256
`539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`, từ commit
`f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7`. Test không được gọi mạng.

## Các phương án

1. Mở loader stdlib hiện có cho đúng bộ pin official v20.1 đã review, giữ fixture tổng hợp.
2. Thêm thư viện `stix2`/MemoryStore cho snapshot thật.
3. Dùng TAXII trực tuyến khi tra cứu.

## Quyết định

Chọn phương án 1. Loader là restricted catalog: chỉ hiểu phần nhỏ của STIX 2.1 cần cho `attack-pattern`,
version và quan hệ `subtechnique-of`; fail-closed với dữ liệu mơ hồ. Nhánh official chỉ nhận đúng bảy trường
pin của Enterprise ATT&CK v20.1 đã review; mọi release/URL/hash khác bị từ chối trước I/O. Root official không
cần provenance riêng của Phong Hỏa, còn synthetic giữ contract provenance cũ. Semantic TTP luôn `unverified`
và kết quả không đủ điều kiện vào draft vận hành.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: deterministic, không egress, không dependency mới; public loader đọc được nguyên bytes v20.1 và vẫn
  kiểm taxonomy lỗi, lifecycle và graph.
- Xấu: thêm release cần review và cập nhật bộ pin; catalog không chứng minh ngữ nghĩa TTP, RAG/C4 hay runtime lab.
- Giảm thiểu: asset nằm ngoài repo, test cần path cấu hình và giữ LICENSE cùng metadata; NOTICE riêng, chữ ký
  tag/commit và các release khác vẫn chưa xác minh.
