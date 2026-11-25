# ADR 0005 — Audit kỹ thuật ATT&CK ngoại tuyến sau adapter X01

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho adapter giả lập C2/C3 ngoại tuyến

## Bối cảnh

Adapter C2/C3 đã xuất các technique dưới dạng chưa kiểm chứng, còn catalog ATT&CK ngoại tuyến đã tra được
trạng thái ID. Hai khả năng này chưa chứng minh adapter xử lý đúng nguyên văn nguồn, quote xuất hiện duy nhất
trong nguồn, hay technique đúng về ngữ nghĩa. Không được biến cờ đủ điều kiện của IOC C3 thành quyền ghi draft
cho technique.

## Các phương án

1. Tái dùng grounding technique hiện có, nhưng đường này chuẩn hóa ID và có khái niệm `keep` trái contract.
2. Thêm audit opt-in sau adapter, bind SHA-256 của nguyên văn nguồn rồi kiểm quote literal và catalog độc lập.
3. Triển khai C4/RAG đầy đủ với retriever và corpus gán nhãn, vượt phạm vi lát cắt offline hiện tại.

## Quyết định

Chọn phương án 2. Audit chỉ nhận projection fail-closed của kết quả `run_extraction`, đúng `AttackCatalog` đã
nạp và nguyên văn nguồn. Nó so SHA-256 UTF-8 trước mọi output, giữ offset theo Unicode code point, coi quote
lặp kể cả chồng nhau là mơ hồ, và chỉ copy provenance bất biến từ lookup catalog. Mọi technique luôn có
`semantic_status="unverified"` và `operational_draft_eligible=false`.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: deterministic, không egress/I/O, không dependency mới, không sửa hành vi C1–C3.
- Xấu: exact quote và ID catalog không chứng minh technique đúng nghĩa; audit hậu xử lý không phải RAG/C4.
- Giảm thiểu: giữ taxonomy lỗi hữu hạn, bound input trước lọc, output frozen/tuple và bắt buộc người duyệt;
  chỉ đánh giá semantic khi có corpus TTP được gán nhãn phù hợp.
