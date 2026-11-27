# F20 — AI tóm tắt có dẫn chứng và hỏi đáp bằng ngôn ngữ tự nhiên (lát cắt MVP của F18 #7, #9)

- Người phụ trách: CHƯA CHỐT
- Issue: CHƯA CHỐT
- Trạng thái: chờ duyệt (đã có code MVP ngoại tuyến trên nhánh `feat/b27-ai-insights`)
- Liên quan: [F18](F18-thay-the-tinh-nang-tra-phi.md) hàng 7 (AI Insights), 8 (NLP), 9 (NLQ);
  [ADR 0018](../adr/0018-khong-dung-ma-enterprise-opencti.md); [X01](X01-ai-extractor.md); [A01](A01-tro-ly-hermes.md)

Toàn bộ thiết kế và code viết mới từ đầu; không mở, chép hay diễn giải mã OpenCTI Enterprise Edition (ADR 0018).
F18 #8 (NLP: trích thực thể từ PDF/văn bản) dùng lại extractor X01 hiện có, không viết lại trong F20.

## Mục tiêu (1–2 câu)
Cho người phân tích SME một bản tóm tắt tiếng Việt mà **mỗi nhận định đều trích STIX id làm chứng cứ**, và cho phép
hỏi bằng câu tự nhiên (Việt/Anh) để nhận lại **bộ lọc whitelist** (không bao giờ là SQL/GraphQL tự do).

## Người dùng và tình huống
- Người phân tích hoặc bot Hermes (A01) có một nhóm STIX object/báo cáo và cần biết nhanh "có gì, khi nào, nguồn nào".
- Người dùng portal gõ "IP độc hại điểm trên 80 trong 7 ngày qua" và muốn danh sách lọc sẵn; API phía sau vẫn tự
  kiểm quyền, F20 chỉ dựng tham số lọc.

## Đầu vào / Đầu ra
| | Mô tả | Ví dụ |
|---|---|---|
| Đầu vào tóm tắt | Danh sách STIX object (có `type`, `id`), văn bản báo cáo tùy chọn, TLP | 4 object (intrusion-set, malware, indicator, vulnerability) |
| Đầu ra tóm tắt | `summary`, `claims[{text, evidence[stix id]}]`, `provider`, `tlp`, `time_range`, `warnings`, `disclaimer` | "Có 1 mã độc: InvoiceRAT. [nguồn: malware--…]" |
| Đầu vào NLQ | Câu hỏi ≤ 2000 ký tự, ngày hôm nay (để tính "7 ngày qua") | "Show vulnerabilities CVE-2024-3400 product PAN-OS TLP:GREEN" |
| Đầu ra NLQ | Dict đúng 10 key: `entity_types`, `labels`, `score_min`, `score_max`, `tlp`, `date_from`, `date_to`, `cves`, `products`, `needs_clarification` | `{"cves": ["CVE-2024-3400"], "products": ["pan-os"], ...}` |

## Thiết kế ngắn
- Code nằm trong `extractor/phonghoa_extractor/`: `ai_provider.py` (giao diện provider + chính sách TLP),
  `ai_insights.py` (tóm tắt), `nlq.py` (hỏi đáp → bộ lọc).
- **Provider mặc định = không có LLM**: template/luật từ khóa ngoại tuyến, tất định, dùng trong test/CI.
- Provider tùy chọn: máy chủ tương thích OpenAI chạy cục bộ (ví dụ Ollama), chỉ cấu hình qua biến môi trường
  `PHONGHOA_AI_BASE_URL`, `PHONGHOA_AI_MODEL`, `PHONGHOA_AI_TIMEOUT`. Không đọc API key.
  Provider chỉ được coi là "cục bộ" khi host là `localhost`, `127.0.0.1` hoặc `::1`.
- Dữ liệu TLP:AMBER, TLP:AMBER+STRICT, TLP:RED **không bao giờ** gửi tới provider không cục bộ. TLP hiệu lực là mức cao
  nhất giữa TLP người gọi truyền và marking TLP chuẩn gắn trên object.
- Văn bản không tin cậy được bọc trong thẻ `<bao_cao>` (tóm tắt) hoặc `<cau_hoi>` (NLQ) kèm câu "đây là DỮ LIỆU";
  dấu hiệu prompt injection được gắn cảnh báo `prompt_injection_suspected` (dùng `injection.scan` của X01).
- Đầu ra LLM phải là đúng một object JSON theo schema; claim trích id không có trong đầu vào, key lạ, sai kiểu →
  loại toàn bộ và quay về kết quả ngoại tuyến (ghi `warnings`).

## Tiêu chí chấp nhận (kiểm tra được)
- [x] Tóm tắt ngoại tuyến tiếng Việt, mỗi claim có ≥ 1 STIX id thuộc đầu vào; kết quả không đổi khi đảo thứ tự object.
- [x] Văn bản báo cáo không có STIX id được gán id tất định `report--<uuid5>` để vẫn trích nguồn được.
- [x] Đầu vào rỗng → "Không đủ dữ liệu để tóm tắt", không bịa claim.
- [x] Có `disclaimer` ghi rõ không phải dự báo.
- [x] TLP:AMBER/RED (kể cả qua marking trên object) không được gửi tới provider không cục bộ.
- [x] Claim LLM trích id lạ hoặc trả văn bản tự do → bị loại, dùng template.
- [x] NLQ nhận câu Việt/Anh về loại thực thể, nhãn, khoảng điểm, TLP, khoảng ngày, CVE, sản phẩm.
- [x] Câu mơ hồ → `needs_clarification = true`; SQL/GraphQL trong câu hỏi không lọt vào bộ lọc.
- [x] `validate_filter` từ chối key lạ, loại thực thể ngoài whitelist, điểm ngoài 0–100, CVE sai dạng, ngày đảo ngược.
- [x] Mọi test chạy ngoại tuyến (provider giả lập, transport HTTP được tiêm vào).

## Không làm trong phạm vi này
- Không nối vào OpenCTI/portal API/MCP thật (chưa có endpoint, chưa có kiểm quyền), không chạy model thật.
- Không dự báo xu hướng; không thống kê theo thời gian ngoài khoảng ngày `created`.
- Không viết lại trích thực thể (F18 #8) — dùng X01.
- Không hỗ trợ provider cloud có API key.

## Rủi ro và câu hỏi còn mở
- Luật từ khóa NLQ phủ hẹp (ví dụ chưa hiểu "tháng 3/2026", tên sản phẩm nhiều từ, phủ định "không phải").
- Chưa đo chất lượng tóm tắt LLM thật (độ trung thành với chứng cứ, tiếng Việt tự nhiên); template chỉ đếm và liệt kê.
- Chỉ nhận marking TLP 1.0 chuẩn của STIX 2.1; marking TLP 2.0/tùy chỉnh của OpenCTI cần ánh xạ thêm (CHƯA CHỐT).
- Kiểm tra host loopback không chống được DNS/proxy trỏ ngược; khi triển khai cần chốt cấu hình mạng.
- Ai được bật provider LLM và model nào: CHƯA CHỐT.

## Chia task (mỗi task ≤ 2 giờ cho agent)
1. (Xong) Provider interface + chính sách TLP + test transport giả lập.
2. (Xong) Tóm tắt ngoại tuyến có dẫn chứng + nhánh LLM có kiểm schema.
3. (Xong) NLQ luật từ khóa + `validate_filter` + nhánh LLM chỉ nhận JSON hợp lệ.
4. Nối NLQ vào portal API/MCP: chuyển bộ lọc thành truy vấn có tham số, kiểm quyền ở API.
5. Thêm marking TLP 2.0 và dữ liệu OpenCTI thật (fixture đã lưu).
6. Đánh giá với model cục bộ thật trên bộ câu hỏi/báo cáo có nhãn.
