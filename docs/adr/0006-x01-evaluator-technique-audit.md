# ADR 0006 — Gắn audit technique ATT&CK tùy chọn vào evaluator C2/C3

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho evaluator giả lập C2/C3 ngoại tuyến

## Bối cảnh

ADR 0005 đã chốt API audit hậu xử lý để đối chiếu source hash, quote/span và trạng thái ID trong catalog ATT&CK.
Evaluator C2/C3 trước đây bỏ semantic item khỏi artifact, nên người xem phải tự nối nhiều đầu ra và dễ dùng lệch
snapshot hoặc nguồn. Mặc định hiện hữu và phép chấm IOC không được đổi.

## Các phương án

1. Thêm audit tùy chọn vào artifact C2/C3 hiện hữu, dùng lại đúng kết quả adapter và catalog đã pin.
2. Tạo CLI audit riêng rồi yêu cầu người dùng join artifact theo document/hash.
3. Chờ C4/RAG và corpus TTP gán nhãn trước khi xuất provenance.

## Quyết định

Chọn phương án 1. Ba cờ `--ttp-audit`, `--attack-snapshot`, `--attack-pin` phải cùng xuất hiện. CLI đọc pin JSON
UTF-8 strict tối đa 16 KiB, nạp catalog đúng một lần trước vòng document rồi gọi public `audit_techniques` trên
chính `adapter_result` và chuỗi source đã đưa vào adapter. Audit tắt giữ schema 1.0; audit bật dùng schema 1.1,
thêm projection đầy đủ theo item và số đếm quote/catalog, không thêm metric TTP.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: một artifact tái lập được source/quote/catalog provenance mà không thêm provider call hoặc đổi điểm IOC.
- Xấu: schema 1.1 chỉ tương thích khi opt-in; snapshot/pin phải được chuẩn bị và quản lý ngoài evaluator.
- Giảm thiểu: mặc định bất biến, parser pin/đường output fail-closed, writer atomic, mọi technique luôn semantic
  `unverified` và không đủ điều kiện ghi draft; C4/RAG chỉ triển khai khi có corpus và nhãn phù hợp.
