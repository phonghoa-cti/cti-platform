# ADR 0004 — Restricted ATT&CK catalog ngoại tuyến cho X01

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho lát cắt fixture tổng hợp

## Bối cảnh

X01 cần kiểm cú pháp và trạng thái mã kỹ thuật trước khi triển khai C4. Dự án chưa chọn, tải, cấp phép hay
kiểm tương thích một snapshot MITRE ATT&CK thật; test cũng không được gọi mạng.

## Các phương án

1. Dùng loader nội bộ bằng Python stdlib với fixture tổng hợp và pin SHA-256.
2. Thêm thư viện `stix2`/MemoryStore và snapshot thật ngay trong lát cắt này.
3. Dùng TAXII trực tuyến khi tra cứu.

## Quyết định

Chọn phương án 1. Loader là restricted catalog: chỉ hiểu phần nhỏ của STIX 2.1 cần cho `attack-pattern`,
version và quan hệ `subtechnique-of`; fail-closed với dữ liệu mơ hồ. Chỉ pin synthetic được nhận. Semantic
TTP luôn `unverified` và kết quả không đủ điều kiện vào draft vận hành.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: deterministic, không egress, không dependency mới, test được taxonomy lỗi và graph.
- Xấu: fixture không chứng minh tương thích MITRE, không có RAG/C4 và không đánh giá đúng ngữ nghĩa TTP.
- Giảm thiểu: giữ interface pin tách biệt; bước sau phải kiểm catalog thật/licensing/NOTICE trước khi tích hợp.
