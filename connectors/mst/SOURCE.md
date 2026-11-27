# Nguồn MST — Cổng Thông tin điện tử Bộ Khoa học và Công nghệ

- Website: https://mst.gov.vn/ (cơ quan nhà nước Việt Nam).
- Danh mục RSS và điều kiện sử dụng: https://mst.gov.vn/index.rss (đối chiếu 26/11/2026). Nguồn công bố RSS và yêu cầu ghi rõ “Theo Cổng Thông tin điện tử Bộ Khoa học và Công nghệ” hoặc tên cổng khi dùng lại tin.
- Endpoint: https://mst.gov.vn/rss/tin-tuc-su-kien/khoa-hoc-va-cong-nghe.rss (có trong danh mục; [CẦN KIỂM] response RSS hiện hành trên lab).
- Bằng chứng nguồn từng đăng cảnh báo Cục An toàn thông tin: https://mst.gov.vn/phat-hien-them-7-lo-hong-bao-mat-tren-he-thong-thong-tin-viet-nam-197240702145439592.htm (22/06/2024). VNCERT có website hoạt động nhưng chưa xác minh được kênh RSS cảnh báo tương ứng, nên ưu tiên MST có RSS được công bố.
- RSS gồm tiêu đề, mô tả, link. Mẫu `mst_excerpt.rss` là tái dựng rút gọn từ metadata và hai mã CVE của bài trên, không phải bản RSS tải trực tiếp. `synthetic.rss` là dữ liệu giả lập, miền .example, không đại diện cảnh báo thật. Không lưu lại toàn văn hay thông tin cá nhân.
- Chỉ trích tiêu đề và mô tả RSS của bài có chủ đề cảnh báo/an ninh; chưa mở toàn văn HTML. Giữ URL gốc trong Report, ghi nguồn. Không truy cập các IOC; chỉ xử lý chuỗi. Chặn email, URL có query/userinfo và URL trỏ về nguồn.
- Quyền sử dụng: điều kiện ghi nguồn nêu trên; [CẦN KIỂM] toàn bộ điều khoản, quyền lưu/chia sẻ IOC và giấy phép cụ thể trước khi chạy lab/đưa vào sản phẩm. TLP:CLEAR không thay thế giấy phép.
- TLP mặc định: CLEAR cho dữ liệu công khai, biểu diễn WHITE theo marking STIX 2.1 chuẩn và label TLP:CLEAR trên Report, tương tự profile W05. Không dùng với dữ liệu hạn chế chia sẻ.
- Mức Admiralty F (chưa đánh giá độ tin cậy IOC); regex không biết đâu là IOC của nạn nhân hay bên tấn công. Vì vậy xuất observable và Vulnerability thay vì Indicator khẳng định độc hại. Không tự chấm điểm hay chặn IOC.
- Quota chính thức chưa xác minh. Đề xuất chạy tối đa mỗi giờ; tối thiểu 5 giây giữa request trong một tiến trình, timeout 15 giây, tối đa 5 lần thử với exponential backoff và Retry-After; cache bộ nhớ một giờ, tối đa 2 MiB/100 bài mỗi RSS. Không tự theo redirect.
- [CẦN KIỂM] robots.txt không đọc được qua công cụ web trong phiên này; live mặc định tắt và từ chối tải RSS nếu không đọc được robots.txt hoặc bị cấm. Xem `README.md`.
- Chưa gọi RSS thật hay OpenCTI thật. Cần xác minh phiên bản pycti tương thích lab, quyền tài khoản, luồng review, RAM (mục tiêu ≤ 256 MB), và khả năng không tạo trùng khi nhập lặp.
- Tham khảo API: https://opencti-python-client.readthedocs.io/en/latest/pycti/pycti.utils.opencti_stix2.html ; chuẩn STIX: https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html .
