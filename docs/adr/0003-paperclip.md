# ADR 0003 — Có dùng Paperclip không, dùng ở đâu

- Ngày: 22/10/2026
- Trạng thái: **Đề xuất**

## Bối cảnh
Paperclip (mã nguồn mở, MIT) điều phối một "công ty" gồm nhiều AI agent: sơ đồ tổ chức, ticket, ngân sách từng agent,
heartbeat (agent tự thức dậy theo chu kỳ để nhận việc), nhật ký kiểm toán. Có adapter cho `opencode_local` và `hermes_local`
— đúng hai công cụ nhóm đang dùng. Nhóm hỏi có nên áp dụng vào dự án.

## Các phương án
| Phương án | Mô tả | Ưu | Nhược |
|---|---|---|---|
| A. Không dùng | Giữ opencode + agy + GitHub Issues | Đơn giản, đã đủ | Bỏ lỡ một trải nghiệm đáng viết |
| **B. Dùng cho quy trình phát triển (thử nghiệm)** | Một "trưởng nhóm" agent chia ticket cho agent code (opencode_local) và agent review; mỗi agent một ngân sách | Thử cách làm mới; có số liệu thật về chi phí và năng suất; không ảnh hưởng sản phẩm | Tốn 1–2 ngày dựng; agent tự chạy dễ tiêu quota; code sinh ra vẫn phải qua PR và người duyệt |
| C. Đưa vào sản phẩm như "SOC ảo" (Collector/Analyst/Reporter agent) | Agent thay connector và cron | Nghe hấp dẫn khi bảo vệ | Trùng việc connector và Hermes đã làm; thêm rủi ro an toàn; khó đánh giá; tốn quota liên tục |

## Quyết định (đề xuất)
Phương án **B**, có giới hạn:
- Chỉ làm **sau khi MVP xong** (tuần 21–31/12/2026), đóng khung trong **1 ngày dựng + 1 tuần chạy thử**.
- Chạy trên laptop (WSL2), không trên máy chủ OpenCTI. Agent chỉ làm trên nhánh riêng; mọi thay đổi vẫn qua PR + CI + người duyệt.
- Ngân sách mỗi agent đặt thấp hơn hạn mức tuần của gói OpenCode Go; dừng ngay khi vượt.
- Ghi lại: số ticket hoàn thành, số PR bị từ chối, chi phí — làm một mục nhỏ trong chương "Phương pháp phát triển" hoặc phụ lục.
- **Không** đưa Paperclip vào sản phẩm (phương án C) trong phạm vi đồ án; nêu như hướng phát triển.

## Hệ quả
- Tốt: có trải nghiệm và số liệu thật về "phát triển phần mềm với đội AI agent có ngân sách" — điểm khác biệt khi bảo vệ.
- Xấu: thêm một công cụ phải học. Nếu đến 21/12 MVP chưa xong thì hủy thử nghiệm, không tiếc.
