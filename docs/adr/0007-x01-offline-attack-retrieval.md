# ADR 0007 — Truy hồi ATT&CK lexical ngoại tuyến cho X01

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho component context trước generation

## Bối cảnh

X01 đã có catalog ATT&CK ghim phiên bản và audit kỹ thuật sau adapter, nhưng lookup hậu xử lý không phải RAG.
Lát cắt này cần đưa ATT&CK knowledge vào một context có provenance trước generation tương lai, đồng thời không
gọi model, mạng, database hoặc biến knowledge thành evidence của báo cáo.

## Các phương án

1. Tiếp tục exact-ID lookup sau generation; đơn giản nhưng không cung cấp context trước generation.
2. Dùng lexical overlap trên ID, tên, description và parent từ canonical catalog hiện có.
3. Dùng embedding/vector semantic; có thể hiểu gần nghĩa tốt hơn nhưng cần model, dependency và benchmark riêng.

## Quyết định

Chọn phương án 2 làm baseline deterministic. Tokenizer dùng Unicode NFKC/casefold, ranking bằng tỉ lệ token query
khớp và tie-break theo ATT&CK ID. Component chỉ nhận `AttackCatalog` trong bộ nhớ, loại record inactive và trả
raw result bất biến cùng JSON context được đo trên toàn envelope theo UTF-8. Description có thể bị cắt trong
context theo budget, nhưng raw result giữ nguyên. Mọi technique luôn `semantic_status="unverified"` và
`operational_draft_eligible=false`.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: không egress/dependency mới, tái dùng hash/pin/canonical/lifecycle/parent của loader và tái hiện được.
- Xấu: lexical overlap không hiểu đồng nghĩa Việt–Anh và ranking score không phải confidence hay semantic truth.
- Giảm thiểu: giữ provenance trong context, fail-closed với catalog/record/budget sai, không đổi grounding/audit/TLP/
  human review; semantic retriever, model C4 và đánh giá corpus thật là các lát cắt riêng.
