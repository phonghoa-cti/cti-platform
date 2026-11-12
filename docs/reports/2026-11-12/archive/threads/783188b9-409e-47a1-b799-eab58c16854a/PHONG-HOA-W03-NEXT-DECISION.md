# W03-S1 — quyết định nối việc sau B và nghiên cứu giới hạn

12/11/2026. Ref d09929311b4b6447aac8b2ec6adac5999beda25d, tree integration sạch khi kiểm.

Chặng B: 19/19 hash đã được Leader kiểm lại theo schema files/name; trace GET200/PUT503/GET503/GET200, một PUT; đã đọc DOM và nhật ký thao tác. Lần đọc manifest đầu dùng nhầm schema artifacts/path bị lỗi, không dùng dòng HASHES_OK của lần đó làm bằng chứng. Chưa xem lại ảnh/SQLite gốc trong lượt này nên không nâng kết quả toàn B thành accepted. Còn thiếu quan sát khóa sau remount trước GET200.

Nghiên cứu product: chấp nhận kết luận cục bộ và brief với sửa đổi. W03 spec/loader128, W04 và parser UI256 đã đối chiếu trực tiếp. Quyết định nâng riêng affected product W03 lên256 code point, vendor128 giữ nguyên. Đây là sửa tính nhất quán trong phạm vi local. Không dựa vào khẳng định chưa kiểm độc lập rằng mọi chuẩn bên ngoài không có cap128. Không thêm sửa Cf/whitespace vào task: giữ normalization/control policy hiện hành; trim theo contract, không áp dụng đề xuất chung từ chối whitespace của Research một cách máy móc.

Hai phần độc lập: Backend sửa loader/contract/test trong tree mới; Engineer hoàn thành bằng chứng khóa ghi với fault hữu hạn trên tree integration. Sau hai đầu vào được review, Engineer mới ghép fix và cập nhật capture/parser gates product256. Không coi d099293 là toàn W03-S1 đạt.
