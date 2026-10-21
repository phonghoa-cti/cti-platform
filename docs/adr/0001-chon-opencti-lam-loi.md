# ADR 0001 — Chọn OpenCTI làm lõi lưu trữ và phân tích

- Ngày: 21/10/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh
Nhóm 3 người, mỗi người khoảng 7 giờ/tuần, kỹ năng code chủ yếu nhờ AI agent. Hạn nộp 27/02/2027.
Mục tiêu là một sản phẩm hoàn chỉnh, demo được. Máy chủ lab: Ubuntu, i3, 16 GB RAM.

## Các phương án
1. Chỉ cài và cấu hình MISP + OpenCTI (ít code, ít đóng góp).
2. OpenCTI làm lõi, nhóm tự viết connector, AI extractor, MCP server, trang SME, bot.
3. Tự xây toàn bộ TIP (FastAPI + PostgreSQL + UI).

## Quyết định
Chọn phương án 2. Không chạy instance MISP; dùng connector MISP feed của OpenCTI.

## Hệ quả
- Tốt: có sẵn STIX 2.1, knowledge graph, ATT&CK, TAXII, phân quyền → dồn sức cho phần mới.
- Xấu: stack nặng (OpenSearch/Elasticsearch, Redis, RabbitMQ, S3) trên máy i3 16 GB; phải học API pycti/GraphQL.
- Giảm thiểu: giới hạn RAM từng container, bật ít connector, thuê VPS tháng demo nếu cần.
