# Prompt cho Gemini Deep Research (dán từng prompt, xuất kết quả ra Google Docs)

## 1. Tổng quan TIP
Tôi đang làm đồ án "Nền tảng Threat Intelligence cho doanh nghiệp vừa và nhỏ tại Việt Nam" dựa trên OpenCTI.
Hãy tổng hợp: (1) định nghĩa và vòng đời CTI theo NIST SP 800-150 và các tài liệu học thuật;
(2) so sánh OpenCTI, MISP, Yeti, IntelOwl và 3 TIP thương mại về kiến trúc, mô hình dữ liệu, chia sẻ, chi phí;
(3) các tiêu chí đánh giá một TIP được dùng trong nghiên cứu. Ưu tiên nguồn từ 2023 trở đi, trích dẫn đầy đủ.

## 2. LLM cho trích xuất CTI
Tổng hợp các nghiên cứu 2023–2026 dùng mô hình ngôn ngữ để trích xuất IOC, TTP (MITRE ATT&CK) và quan hệ STIX
từ báo cáo văn bản: phương pháp, bộ dữ liệu công khai, metric, kết quả, hạn chế. Lập bảng so sánh.
Có công trình nào xử lý tiếng Việt hoặc ngôn ngữ ít tài nguyên không?

## 3. Prompt injection trong pipeline CTI
Tổng hợp nghiên cứu và sự cố thực tế về prompt injection gián tiếp qua tài liệu đầu vào (indirect prompt injection),
đặc biệt khi LLM xử lý nội dung do kẻ tấn công kiểm soát. Các biện pháp phòng thủ và cách đánh giá định lượng.

## 4. Bối cảnh Việt Nam
Số liệu tấn công mạng vào doanh nghiệp Việt Nam 2024–2026 (NCA, NCSC, Viettel, BKAV, VSEC...), các nhóm APT và
chiến dịch ransomware nhắm vào Việt Nam/Đông Nam Á, các quy định pháp lý liên quan (Luật An ninh mạng, Nghị định
13/2023 về bảo vệ dữ liệu cá nhân, luật bảo vệ dữ liệu cá nhân mới). Ghi rõ nguồn và ngày.

## 5. Agent AI trong SOC
Xu hướng 2025–2026 về AI agent trong SOC/CTI: MCP, agent tự chủ có người duyệt, các sản phẩm và dự án mã nguồn mở
(Hermes Agent, OpenCTI MCP/XTM One...). Rủi ro bảo mật và nguyên tắc thiết kế an toàn.
