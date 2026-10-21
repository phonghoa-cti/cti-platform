# Phong Hỏa

> A threat intelligence platform for Vietnamese SMEs, built on OpenCTI, with an LLM-based report extractor
> and an AI analyst assistant (MCP + Telegram). Graduation project, 2026–2027.

Phong hỏa đài là những tháp đốt lửa báo giặc: trạm này thấy thì trạm sau truyền tiếp.
Phong Hỏa làm điều tương tự với thông tin về mối đe dọa mạng cho doanh nghiệp vừa và nhỏ.

## Thành phần
- **Lõi:** OpenCTI (STIX 2.1, knowledge graph, TAXII)
- **Connector:** feed quốc tế miễn phí và nguồn cảnh báo tiếng Việt
- **AI extractor:** regex + LLM trích IOC/TTP từ báo cáo, analyst duyệt trước khi lưu
- **Trang SME:** tổng quan, tra cứu IOC, lỗ hổng ảnh hưởng tài sản (tiếng Việt / English)
- **Agent:** MCP server + Hermes Agent gửi bản tin và trả lời qua Telegram

## Bắt đầu
1. Đọc `AGENTS.md` (quy ước cho người và AI agent).
2. Làm theo `docs/tuan-1-checklist.md`.
3. Triển khai lab: `deploy/README.md`.

## Nhóm
| Vai | Thành viên |
|---|---|
| Web & Red team | |
| Hạ tầng & Dữ liệu | |
| AI & Agent | |

Tài liệu chi tiết, nhật ký tuần và quyết định kiến trúc: xem Wiki và thư mục `docs/`.
