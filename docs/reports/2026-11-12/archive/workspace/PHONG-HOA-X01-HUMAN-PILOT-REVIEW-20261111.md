# X01-HUMAN-PILOT-PREP — review Leader

Ngày 11/11/2026. Request `eb1010be-5dd1-46e5-aad5-88f61895aaae`. Kết luận: NEEDS_REWORK R1, chỉ tài liệu.

## Đã kiểm

- Source `cti-x01-gold-pilot` tại `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`, status sạch. Đọc trực tiếp parser và CLI, không chạy lại test sản phẩm không đổi.
- Hash SOURCES `af2ce287b0f6685421162afdb7209c872e47afcda575bb8272f05c0164be303b`; RUNBOOK `1ff406279eb2b9c130d1e288304f8bec4a218bbaa5e1133ea339468b7554875e`, khớp bàn giao.
- Leader mở lại năm URL chính thức trong SOURCES: tiêu đề/ngày/ngôn ngữ và nội dung hành vi/IOC phù hợp mô tả ứng viên. Chưa đo chính xác số từ; khoảng 300–3000 vẫn là ước lượng, không phải acceptance đã chạy.
- Đã đọc [điều khoản FPT IS](https://fpt-is.com/dieu-khoan-su-dung-website/) và [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use). Microsoft có quyền sử dụng Documents có điều kiện; chưa xác định điều khoản đó áp dụng cho bản corpus dự kiến. Giữ unknown/link-only là quyết định phạm vi hiện tại, không kết luận pháp lý tuyệt đối rằng mọi sử dụng đều bị cấm.
- Official pin path tồn tại; snapshot path trong lệnh tồn tại, 55.277.605 bytes. CLI flags và exit/status/no-clobber mô tả khớp mã.
- Chưa tải corpus, tạo annotation, xác nhận hai người thật hoặc thử model. Automation phục hồi còn enabled, mỗi 30 phút; lần 14:56 hoàn tất không lỗi. Không có Leader khác đang chạy khi kiểm threads.

## R1 — hướng dẫn chưa đủ dựng input hợp lệ (P2)

RUNBOOK mục “Chuẩn bị dataset cục bộ hợp lệ” liệt kê metadata với khẳng định key đóng nhưng thiếu `id`. `extractor/phonghoa_extractor/gold_pilot.py:366` yêu cầu `id`; `exact(...)` tại dòng 377 từ chối thiếu trường này, và filename phải khớp id tại dòng 383. Làm theo danh sách hiện tại sẽ trả `invalid_record`.

Cùng mục yêu cầu tạo `manifest.json` nhưng không chỉ rõ năm key bắt buộc và giá trị purpose/provenance/document_count (parser dòng 283–301). Không có cấu trúc các object source/raw/attack, IOC/TTP, cũng chưa có đường dẫn tới hợp đồng đầy đủ. Vì brief đòi gói thực hành đủ dùng cho hai người, người đọc đang phải tự đoán schema.

Sửa tối thiểu chỉ RUNBOOK: bổ sung `id`; bảng cấu trúc ngắn cho manifest, metadata và nested objects, annotation/IOC/TTP/evidence với required/optional, kiểu và enum/bounds thiết yếu đúng parser HEAD. Có thể dẫn chính xác hợp đồng Leader và mã để tránh chép dài, nhưng những key cần để dựng file phải tự đủ. Nêu mỗi danh sách IOC và TTP tối đa 256; duplicate IOC theo triple type/value/role; evidence span tối đa 2048 code points; JSON UTF-8 không BOM, duplicate keys hay NaN/Infinity. Không thay schema/code.

Bổ sung ví dụ Unicode tổng hợp đã có bằng một phép tính ngắn sử dụng normalizer hiện có và hash/span, không ghi file corpus/annotation, không tự nhận nhãn người thật. Có thể kiểm ví dụ trong bộ nhớ; không chạy model hay suite sản phẩm. Giữ lệnh CLI hiện tại và các giới hạn quyền/TLP/độc lập/semantic.

SOURCES không cần sửa ngoài việc nói rõ ước lượng độ dài nếu cần; không cần mở rộng nghiên cứu hay thay năm ứng viên chỉ để xử lý R1. Không suy TLP hay quyền từ public URL; không hỏi người dùng qua worker.
