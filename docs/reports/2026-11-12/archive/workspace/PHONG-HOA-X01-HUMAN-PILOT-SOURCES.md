# X01 — nguồn ứng viên cho pilot gán nhãn người thật

Ngày kiểm: 11/11/2026 (Asia/Saigon). Đây là shortlist **link-only**, không phải corpus đã được duyệt, không chứa raw report hay danh sách IOC. Đã mở từng bài tại URL chính thức và điều khoản của nhà phát hành; không dùng search snippet làm bằng chứng.

## Kết luận

Có **5 ứng viên: 3 tiếng Việt, 2 tiếng Anh**. Nội dung đã mở cho thấy mỗi bài có mô tả hành vi và ít nhất một IOC; độ dài hiển thị có vẻ nằm trong khoảng guideline 300–3000 từ (cần đếm lại trên bản raw được phép lưu trước nhập). Cả năm đều chưa có quyền lưu/phân phối raw rõ ràng và không thấy marking TLP trên bài. Nếu chỉ xét quyền, `source_license: "unknown"` đi với `storage_right: "link-only"`, raw vắng mặt và không annotation. Nhưng `gold-pilot-v1` bắt buộc `tlp` là `TLP:CLEAR` hoặc `TLP:GREEN`, không có giá trị “unknown”; vì không được suy một trong hai từ URL công khai, **chưa được tạo metadata/record cho bất cứ ứng viên nào**.

| ID đề xuất (chưa tạo) | Ngôn ngữ | Báo cáo đã mở / publisher / ngày báo cáo | Dấu hiệu phù hợp đã quan sát | Trùng/translation | Quyền và TLP |
|---|---|---|---|---|---|
| `vi-fpt-appdomain-2024` | vi | [Chiến dịch tấn công mạng có chủ đích nhắm tới Việt Nam](https://fpt-is.com/goc-nhin-so/chien-dich-tan-cong-mang-co-chu-dich-nham-toi-viet-nam/), FPT IS / FPT Threat Intelligence, 13/11/2024 | Mô tả chuỗi ZIP/MSC → GrimResource → JavaScript → DLL/AppDomainManager → beacon; có mục IOC domain. | Không phải bản dịch trong shortlist; có tham khảo nguồn bên thứ ba, không coi FPT là chủ thể cấp quyền cho nguồn đó. | Điều khoản FPT IS nói nội dung thuộc FPT IS/đối tác và cấm sao chép, sử dụng khi chưa có chấp thuận bằng văn bản: `unknown/link-only`. Không thấy TLP: **unmarked**. |
| `vi-fpt-amazon-pdf-2025` | vi | [Cảnh báo chiến dịch lừa đảo PDF độc hại giả mạo Amazon](https://fpt-is.com/goc-nhin-so/chien-dich-lua-dao-pdf-gia-mao-amazon/), FPT IS / FPT Threat Intelligence, 06/05/2025 | Có mô tả email–PDF–redirect–trang giả và mục hash/URL IOC; phù hợp đào tạo role attacker/benign nhưng không suy nhãn trước. | Khác chiến dịch và khác văn bản với các mục còn lại; bài dẫn Unit 42, không sao chép raw bên thứ ba. | Cùng điều khoản FPT IS: `unknown/link-only`. Không thấy TLP: **unmarked**. |
| `vi-fpt-tycoon2fa-2025` | vi | [Cảnh báo Phishing: Nhóm Tycoon2FA nhắm vào người dùng Microsoft 365](https://fpt-is.com/goc-nhin-so/canh-bao-phishing-tycoon2fa-microsoft-365/), FPT IS / FPT Threat Intelligence, 10/07/2025 | Có luồng phishing, malformed URL/redirect/cloud infrastructure và bảng URL IOC. | Không phải bản dịch của hai bài FPT kia; cùng publisher nên cần hai người kiểm tra tránh lặp hạ tầng/diễn giải. | Cùng điều khoản FPT IS: `unknown/link-only`. Không thấy TLP: **unmarked**. |
| `en-ms-marbled-dust-2025` | en | [Marbled Dust leverages zero-day in Output Messenger for regional espionage](https://www.microsoft.com/en-us/security/blog/2025/05/12/marbled-dust-leverages-zero-day-in-output-messenger-for-regional-espionage/), Microsoft Threat Intelligence, 12/05/2025 | Có attack chain, CVE, file/hunting evidence, C2 detection query và mitigation. | Không phải translation của nguồn Việt trong shortlist. | [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use) bảo lưu quyền, cấm copy/distribute trừ khi có quy định khác; không xác định blog này là “Document” được cấp phép. `unknown/link-only`. Không thấy TLP: **unmarked**. |
| `en-ms-device-code-2026` | en | [Inside an AI-enabled device code phishing campaign](https://www.microsoft.com/en-us/security/blog/2026/04/06/ai-enabled-device-code-phishing-campaign-april-2026/), Microsoft Defender Security Research, 06/04/2026 | Có attack chain device-code, hành vi persistence/exfiltration và mục IOC IP range; đủ đa dạng với bốn mục còn lại. | Không phải translation; cùng publisher với mục trước, cần tránh dùng cùng một đoạn hay cùng chiến dịch. | Cùng Terms of Use Microsoft: `unknown/link-only`. Không thấy TLP: **unmarked**. |

## Bằng chứng quyền và giới hạn

- [Điều khoản FPT IS](https://fpt-is.com/dieu-khoan-su-dung-website/) (cập nhật 13/05/2024) nêu nội dung thuộc FPT IS hoặc đối tác và yêu cầu chấp thuận bằng văn bản trước khi sao chép/sử dụng. Vì thế citation/link không phải quyền lưu raw cục bộ hoặc phân phối bộ dữ liệu.
- [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use) (cập nhật 07/02/2022) giữ quyền đối với nội dung dịch vụ và hạn chế copy/distribute nếu không có quy định khác. Nó không đủ để tự gán một quyền dataset cho Security Blog.
- Không thấy giấy phép Creative Commons, điều khoản cấp quyền corpus, email cho phép, hay TLP marking trên năm URL khi mở ngày kiểm. “Không thấy” không chứng minh không tồn tại ở nơi khác.
- License Apache-2.0 của mã TRAM chỉ áp dụng mã TRAM, không cấp quyền cho năm báo cáo này. ATT&CK catalog chỉ là catalog pin-able, không là corpus.

## Điều kiện trước khi một mục thành dữ liệu pilot

Người phụ trách phải lưu bằng chứng quyền bằng văn bản cho đúng bài và phạm vi lưu local/repo, rồi xác nhận TLP/nhãn chia sẻ từ publisher hoặc chủ sở hữu. Sau đó mới chọn `source_license`, `storage_right` và TLP đúng schema. Nếu quyền chỉ cho lưu local, dùng `local-only`; nếu quyền repo rõ, dùng `repo-allowed`. Nếu không xác nhận được, giữ ứng viên ngoài dataset (hoặc chỉ theo dõi link ở danh sách này), không tải/lưu raw, không bịa provenance, hash hay nhãn.

Không bài nào ở đây là gold corpus, human annotation, test model, hay bằng chứng chất lượng extractor/model/RAG.
