# Hướng dẫn 05 — Research bằng Gemini Deep Research và NotebookLM

**Ai làm:** vai AI & Agent dẫn dắt, cả nhóm dùng. Hạn đợt đầu: 03/11/2026 (phục vụ đề cương và chương 1–2).

**Mục tiêu:** có kho tài liệu nền đáng tin để học nhanh, viết chương 1–2 có trích dẫn, và ôn bảo vệ.

**Vì sao:** Deep Research tìm và tổng hợp rộng; NotebookLM chỉ trả lời dựa trên đúng các tài liệu bạn nạp vào, có trích dẫn từng câu, nên ít "bịa" hơn.

## Phân vai hai công cụ

| Công cụ | Giỏi | Dùng trong đồ án |
|---|---|---|
| Gemini Deep Research | Tìm và tổng hợp nhiều nguồn trên web thành báo cáo | Khảo sát TIP, nghiên cứu LLM–CTI, bối cảnh Việt Nam |
| NotebookLM | Hỏi đáp có trích dẫn trên tài liệu của bạn; tạo podcast, flashcard, sơ đồ tư duy | Học nền, tra cứu khi viết, ôn bảo vệ |

## Bước 1 — Chạy Deep Research (khoảng 30 phút cho 5 prompt)
1. Mở gemini.google.com, chọn **Deep Research**.
2. Dán từng prompt trong `docs/prompts/deep-research.md`. Gemini sẽ đưa kế hoạch tìm kiếm: đọc qua, sửa nếu lệch, rồi bấm bắt đầu.
3. Xong mỗi báo cáo: **Export to Docs**, đặt tên `DR-01-tong-quan-TIP`... trong thư mục Google Drive chung của nhóm.
4. Ghi 5–10 dòng tóm tắt + link vào `docs/research/<ten>.md` trong repo để agent cũng đọc được.

## Bước 2 — Kiểm chứng (bắt buộc trước khi đưa vào báo cáo)
Deep Research vẫn có thể trích sai hoặc gán nhầm nguồn. Với mỗi số liệu hay khẳng định sẽ đưa vào quyển:
1. Bấm vào trích dẫn, mở nguồn gốc.
2. Xác nhận nguồn thật sự nói điều đó, ghi lại ngày.
3. Không mở được nguồn → không dùng.

## Bước 3 — Dựng notebook NotebookLM
Tạo notebook **"Phong Hỏa – Nền tảng"** và nạp:
- Các báo cáo Deep Research (từ Google Docs).
- NIST SP 800-150 (PDF), tài liệu giới thiệu STIX 2.1 và TAXII 2.1 (OASIS).
- Các trang tài liệu OpenCTI: Installation, Connectors, MCP server (dán link).
- 4 paper: AZERG (arXiv 2507.16576), TTPXHunter (2403.03267), IntelEX (2412.10872), khảo sát LLM cho SOC (2509.10858).
- `docs/wiki/Tu-dien-CTI.md` của repo.

Chia sẻ notebook cho cả nhóm.

## Bước 4 — Dùng hằng ngày
- **Học:** *"Giải thích STIX Indicator khác Observable thế nào, cho người mới, kèm ví dụ."*
- **Viết chương:** *"Liệt kê các điểm chính về vòng đời CTI kèm trích dẫn."* Sau đó tự viết lại bằng lời của mình và giữ trích dẫn gốc.
- **Ôn:** tạo **Flashcards** và **Quiz** từ notebook; tạo **Audio Overview** (podcast) để nghe khi di chuyển.
- **Chuẩn bị bảo vệ (tháng 2):** *"Đóng vai hội đồng, hỏi tôi 10 câu khó nhất về đề tài này."*

## Lưu ý về bản quyền và liêm chính
- Không chép nguyên văn đoạn dài từ tài liệu hay từ AI vào quyển; luôn viết lại và trích nguồn.
- Ghi lại công cụ AI đã dùng vào `docs/ai-log/` (trường cho phép dùng AI, nhưng nên minh bạch).

## Kiểm tra là xong
- 5 báo cáo Deep Research trong Drive, 5 file tóm tắt trong `docs/research/`.
- Notebook NotebookLM được chia sẻ cho cả 3 người, có ít nhất 10 nguồn.

## Học thêm
- **Grounded (dựa trên nguồn):** AI chỉ trả lời từ tài liệu bạn đưa vào. Đây là lý do NotebookLM ít bịa hơn chatbot thường.
- **Kiểm chứng nguồn gốc:** đi tới tài liệu gốc thay vì tin bản tóm tắt; hội đồng hay hỏi "số liệu này lấy ở đâu".
- **Trích dẫn IEEE:** kiểu đánh số [1], [2] trong văn bản, danh sách đầy đủ ở cuối; phổ biến trong ngành kỹ thuật.
