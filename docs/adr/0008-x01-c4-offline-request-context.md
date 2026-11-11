# ADR 0008 — Request context ATT&CK ngoại tuyến cho X01/C4

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho adapter giả lập C4 ngoại tuyến

## Bối cảnh

Retriever lexical ở ADR 0007 đã tạo context ATT&CK có provenance trước generation. Adapter C2/C3 hiện chỉ nhận
báo cáo và không được thay đổi artifact. C4 cần gửi context đó cùng báo cáo, nhưng knowledge không được trở thành
evidence, không được đổi source hash và không được mở mạng hay quyền ghi.

## Các phương án

1. Ghép context vào `text`: đơn giản nhưng làm sai source hash, grounding và quote audit.
2. Thêm wrapper C4 và ba trường knowledge riêng trong request: giữ C2/C3, source và audit độc lập.
3. Derive query từ báo cáo hoặc dùng semantic/vector retrieval: tăng tự động hóa nhưng cần prompt/model, dependency
   và benchmark riêng.

## Quyết định

Chọn phương án 2. `run_c4_extraction` kiểm báo cáo/TLP, gọi public retriever đúng một lần, rồi tạo một request bất
biến chứa nguyên context, SHA-256 UTF-8 và schema version. Cùng request được dùng cho tối đa hai lần generate của
provider `fake_offline`; retry hết thì fallback regex như C3. Kết quả chỉ công bố metadata/provenance trong
`attack_context`, không công bố query hoặc raw context.

Caller gọi public `audit_techniques` riêng với chính báo cáo gốc. Audit C4 tiếp tục kiểm quote/span từ báo cáo và
catalog; technique luôn `unverified` và không đủ điều kiện ghi draft. Prompt tuyên bố report/knowledge là dữ liệu
không tin cậy và chỉ report là evidence.

## Hệ quả và giới hạn

- Tốt: C2/C3 giữ nguyên; retrieval, generation và audit tách rời; không egress, database hay side effect mới.
- Xấu: query vẫn do caller truyền; lexical context và provider giả lập không chứng minh model hiểu ATT&CK.
- Chưa xác minh: model thật, prompt-injection resilience, semantic/multilingual recall, corpus hai người gán nhãn,
  evaluator/reporter C4, OpenCTI, lab và production.
