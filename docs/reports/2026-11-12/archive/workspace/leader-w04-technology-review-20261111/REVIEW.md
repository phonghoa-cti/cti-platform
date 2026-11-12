# Nghiệm thu nghiên cứu và chốt W04 Technology

Leader kiểm ngày 11/11/2026, request Research `4fa536de-ba5c-4e2d-a6b6-8bcc5a574a9d`. Kết luận: chấp nhận nghiên cứu **với điều chỉnh bắt buộc** trong `PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md`. Chưa có implementation/test technology.

- Xác nhận baseline `cti-w04-local-integration@8a767314b654d39c1ddc2995b7919c44a5b7027a`, tree sạch; đối chiếu app/auth/schema/AssetStore/adapter/UI và spec W03/W04.
- Chấp nhận store/bảng/audit công nghệ riêng, tái dùng pattern W04, không thêm vào matcher/allowlist. Wire chốt `software_version` chuỗi, `version` số bản ghi.
- Loại NFKC khỏi khóa: chỉ trim+casefold theo giới hạn spec. Không giả lowercase JS là Unicode casefold backend.
- Sửa phân loại Origin403/body413/media415, giữ schema422. Migration phải rollback DDL thật; không copy executescript có thể commit sớm. Pre-commit validate toàn bộ response, subject512, safe integer và lỗi audit/UNIQUE như bài học F1–F4.
- Đã mở nguồn NIST overview và Python3.12 sqlite3, dẫn tại contract. PDF NIST timeout/NVD rỗng ở lần mở Leader không được coi là bằng chứng nội dung. Các nguồn khác ghi đúng mức Research đã đọc, không chứng minh runtime/license.
- Đã xem một lần các thread: không có Leader khác đang làm, các task W04 đã trả đều idle. Không lặp nghiệm thu domain/CIDR hoặc suite cũ.
- Backend và Frontend nhận hai brief/tree độc lập từ cùng baseline. Frontend làm provider mẫu + HTTP adapter mock ngay; tab thật/gateway/browser chỉ nối sau khi cả hai đầu vào đạt. Hai receipt thực ở `dispatch-receipts.json`, queued chưa chứng minh đang chạy.
- Hai lịch tiếp tục dự án được đọc lại và giữ enabled; dự án active, không tạo lịch/worker trùng. Không push/PR/merge/deploy/lab.
