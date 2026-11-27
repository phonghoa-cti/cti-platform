# ADR 0018 — Không dùng mã Enterprise OpenCTI, tự viết dịch vụ ngoài lõi

- Ngày: 27/11/2026
- Trạng thái: Đề xuất — chờ nhóm duyệt (B25); không thay đổi runtime.

## Bối cảnh

Phong Hỏa là nền tảng tình báo mối đe dọa cho SME Việt Nam, dùng OpenCTI Community Edition (CE) làm kho STIX 2.1. Brief xác định đích CE 7.261124.0 (PR #56); origin/main khi tạo B25 là `4d1aeea`, chưa có bằng chứng PR #56 gộp, không nâng phiên bản ở đây. Enterprise Edition (EE) có các tính năng cần cho sản phẩm thương mại nhưng dùng giấy phép riêng; LICENSE công khai [1] xác nhận phân biệt CE/EE theo header từng file. Khả năng đọc mã trên GitHub không đồng nghĩa với quyền sử dụng hay phân phối EE.

## Các phương án

| Phương án | Ưu điểm | Nhược điểm / quyết định |
|---|---|---|
| Mua license EE chính thức | Tính năng gốc, hỗ trợ nhà cung cấp theo hợp đồng | Chi phí, phụ thuộc hợp đồng; không chọn cho bản CE thương mại của Phong Hỏa |
| Tự xây lớp nghiệp vụ ngoài CE dựa trên tài liệu/API công khai | Chủ động tiếng Việt, phù hợp SME, không cần thay lõi | Tốn giờ công, kiểm thử và bảo trì; đề xuất chọn, phạm vi F18/F19 |
| Chỉ dùng CE, bỏ toàn bộ tiện ích bổ sung | Nhanh, giảm rủi ro | Không đáp ứng mục tiêu tiện ích; giữ làm phương án thu hẹp nếu không đủ nguồn lực |

Không xem việc mở/chép/diễn giải mã EE, sửa khóa giấy phép hoặc kích hoạt EE không có quyền là phương án hợp lệ.

## Quyết định

Đề xuất lựa chọn phương án 2. Giữ nguyên lõi CE, dùng API/stream được tài liệu hóa; nhóm tự viết độc lập connector, portal, Hermes/MCP, extractor. Không mở, sao chép, phân tích, diễn giải hay chuyển thể mã EE (kể cả thử nghiệm, UI, assets); không sửa lõi hay kiểm license, không kích hoạt EE/trial trong bản bán, kể cả thông qua XTM One. Chỉ tham khảo tài liệu công khai về mục đích tính năng, không lấy implementation. F18 lập ma trận 15 tính năng; F19 là playbook YAML độc lập, mọi thao tác ghi OpenCTI chờ người duyệt.

Từ 7.260224.0, docs xác nhận SSO qua cấu hình lẫn UI thuộc EE; CE dùng local authentication [3]. Portal có cơ chế xác thực riêng theo W00/F08, không chuyển thành SSO lõi CE. Kiểm lại tag runtime theo docs trước nghiệm thu; nếu API/stream CE không đáp ứng, thu hẹp hoặc đề xuất giải pháp khác, không vượt cổng license.

Ràng buộc phát hành: bảo toàn LICENSE/NOTICE/attribution của Apache 2.0, kiểm quyền phân phối từng image/binary/dependency/connector/feed/model và dữ liệu, TLP/quyền nguồn/tenant. Nếu image upstream có thành phần EE dù chưa kích hoạt, không giả định được quyền tái phân phối toàn bộ; chủ chịu trách nhiệm rà điều khoản, có thể dùng CE do khách tự triển khai nếu phù hợp. Không quảng cáo đã có parity EE hay quan hệ chính thức với Filigran.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: tách trách nhiệm rõ, code do nhóm sở hữu theo nguồn gốc thực, giữ đường nâng cấp CE, không cần mua EE để dùng chức năng tự xây.
- Xấu: cần thiết kế và kiểm thử thay thế, không có đầy đủ giao diện/hiệu năng EE, phải duy trì adapter theo phiên bản; F18 232 giờ công dự kiến chưa tính dự phòng. Chốt P1 nhỏ, đo fixture rồi lab; không cam kết parity hay thời hạn thương mại.
- Giảm thiểu: hồ sơ provenance, review license/SBOM (danh mục phần mềm), kiểm tag/digest và runtime CE, cổng pytest `core/tests/test_no_opencti_ee_code.py` tìm marker `OpenCTI Enterprise Edition License` theo ví dụ header của LICENSE. Cổng dò chuỗi không phải chứng nhận pháp lý, không bắt được mã mất header/nén/dependency ngoài cây; review thủ công nguồn gốc và gói deploy vẫn bắt buộc.
- Bảo mật: RBAC/TLP/tenant và audit trước nối live, không tự chặn/xóa, mọi ghi OpenCTI qua W05; TLP:AMBER/RED không gửi cloud LLM, nội dung feed không tin cậy. W00 hiện single-tenant nên chưa bán SaaS nhiều khách trước cổng cô lập.
- Trạng thái thực: B25 chỉ tài liệu và test phòng ngừa. Chưa cài CE đích, chưa nghiệm thu runtime, feed/model thật, F19 hay thương mại. Chủ cần duyệt các quyết định mở trong F18.

Nguồn (27/11/2026):

1. https://github.com/OpenCTI-Platform/opencti/blob/master/LICENSE — LICENSE và ví dụ header; bản ghim chưa kiểm được qua web.
2. https://docs.opencti.io/latest/administration/enterprise/ — danh mục chức năng và điều kiện EE.
3. https://docs.opencti.io/latest/deployment/authentication/ — SSO từ 7.260224.0.
4. https://docs.opencti.io/latest/reference/streaming/ — giao diện công khai cho F19.
