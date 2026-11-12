# X01-HUMAN-PILOT-PREP — nghiệm thu tài liệu

Ngày 11/11/2026. Request gốc `eb1010be-5dd1-46e5-aad5-88f61895aaae`, rework R1 `b236121b-7aac-4975-b62d-5e5af49b028c`. Kết luận: **PASS trong phạm vi chuẩn bị nguồn và hướng dẫn**, đóng R1; chưa có corpus hoặc nhãn người thật.

## Bằng chứng Leader

- Đọc lại parser manifest/source/record/raw/annotation/evidence trên `cti-x01-gold-pilot` HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`; Git status rỗng. Bảng mới có `id` và đủ key đóng, enum, giới hạn danh sách, filename, phiên bản/hash và quy tắc nhãn rỗng đúng mã.
- Tính lại ví dụ tổng hợp trong bộ nhớ bằng Python của `cti-platform-start/.venv`, import thực tế `phonghoa_core.ioc.normalize`; gọi thêm `gold_pilot.evidence_list` trên cùng substring. Exit 0: span `[11,32)`, hai SHA-256 và URL chuẩn hóa đều khớp RUNBOOK. Kết quả lưu tại `PHONG-HOA-X01-HUMAN-PILOT-EXAMPLE-CHECK.json`. Lần thử đầu dùng sai tên module import nên thất bại; đã sửa import rồi chạy lại thành công, không sửa source.
- SOURCES không đổi, SHA-256 `af2ce287b0f6685421162afdb7209c872e47afcda575bb8272f05c0164be303b`. Năm nguồn/điều khoản đã được Leader mở trong lượt review trước, ghi tại `PHONG-HOA-X01-HUMAN-PILOT-REVIEW-20261111.md`; không mở lại khi nội dung tài liệu không đổi. Khoảng 300–3000 từ vẫn là ước lượng.
- RUNBOOK bàn giao R1 có SHA-256 `a3d2da526472a5dedc640568218be1bd0feab0789eb763cf3de2baf97d55d405`. Leader chỉ escape dấu `|` bên trong code của bảng để Markdown không tách nhầm cột; 11 dòng bảng đều còn đúng ba cột. SHA-256 bản dùng cuối: `03600d589c6c98577be299302c722626825c4576730ae2c665a4d4c769c426d4`.
- Không chạy lại suite sản phẩm vì chỉ đổi tài liệu. Không tạo raw corpus/annotation, không gọi model, cài dependency, sửa repo, commit, push, merge hoặc deploy.

## Điều kiện còn thiếu và bước độc lập

Pilot người thật cần nguồn có quyền lưu và nhãn chia sẻ được xác minh, hai người gán nhãn độc lập, rồi người hòa giải bất đồng. Năm bài hiện chỉ là ứng viên ngoài dataset. Quyền do chủ sở hữu nguồn xác nhận; người dùng không mặc nhiên có thể cấp quyền thay nhà xuất bản. READY của validator chỉ kiểm hồ sơ đã khai báo, không chứng minh các điều kiện đó hoặc chất lượng model.

Đã đối chiếu `docs/specs/X01-ai-extractor.md`: bước nạp URL/PDF/text còn trong mục tiêu. CLI hiện đọc `.txt`; không thấy thành phần nạp PDF trong thư viện extractor. Chọn nghiên cứu lát nạp file văn bản/PDF cục bộ tiếp theo, độc lập với corpus người thật; chưa quyết định thư viện hoặc triển khai. Giữ nguồn URL, OCR, mạng/model thật ngoài phạm vi nghiên cứu triển khai đầu tiên.

Các task đã accepted không nghiệm thu lại. Dự án vẫn active; giữ lịch dự phòng 30 phút. Đã đọc trạng thái lịch: enabled=true, lần scheduled 14:56 hoàn tất NOTHING NEW, không lỗi; điều đó chưa chứng minh phục hồi việc bỏ dở. Không có Leader khác đang xử lý khi kiểm các cuộc mở trong lượt này.
