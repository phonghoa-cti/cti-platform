# Phong Hỏa — nghiệm thu bằng hành vi, không cần đọc code

Ngày 11/11/2026. Đây là kế hoạch nghiệm thu cho người dùng, không phải báo cáo các ca đã chạy. Bằng chứng cũ chỉ chứng minh phạm vi cũ; chưa có buổi người dùng trực tiếp nghiệm thu toàn hệ thống.

## Sản phẩm phải trả lời được gì

Threat intelligence là thông tin mối đe dọa đã được xử lý/phân tích và thêm ngữ cảnh để hỗ trợ quyết định ([NIST](https://csrc.nist.gov/glossary/term/cyber_threat_intelligence)). Mỗi kết quả hữu ích cần giải thích: điều gì đáng chú ý, nguồn nào, quan sát/cập nhật khi nào, mức tin cậy và giới hạn, có liên quan đến tổ chức không, bước xử lý được đề xuất vì sao. Chỉ tìm thấy chuỗi IP trong báo cáo chưa chứng minh IP độc hại; mã ATT&CK tồn tại chưa chứng minh gán kỹ thuật đúng ngữ cảnh.

## Bộ tình huống trình diễn

| Tình huống | Người xem làm/quan sát | Đạt khi | Hiện trạng bằng chứng |
|---|---|---|---|
| Báo cáo có dấu hiệu biết trước | Mở báo cáo tổng hợp, đối chiếu danh sách dấu hiệu và đoạn trích | Có vị trí bằng chứng đúng; phân biệt dấu hiệu của kẻ tấn công, nạn nhân và ví dụ vô hại; công bố mục bỏ sót/sai | Nạp TXT/PDF và kiểm bằng chứng đã có kiểm cục bộ; chất lượng hiểu ngữ cảnh bằng model thật chưa kiểm |
| Người duyệt kiểm soát đầu ra | Chọn/bỏ một IOC, lưu, duyệt rồi xem đầu ra | Chỉ lựa chọn đã duyệt được xuất; người tạo không tự duyệt; có lịch sử người/quyết định/thời gian | UI lựa chọn đã kiểm cục bộ; TXT/PDF đến hàng chờ đang nối; chưa chứng minh toàn chuỗi trong một lần trình diễn |
| Dữ liệu lỗi và thao tác lặp | Nhập lại dữ liệu, thử sai định dạng, gây lỗi tải lại sau khi lưu | Không tạo bản sao ngoài contract, không mất dữ liệu, không gửi quyết định hai lần, thông báo rõ | Có kiểm lỗi của các thành phần; importer mới chưa triển khai |
| Nhập và tra lại trong OpenCTI | Từ bản đã duyệt, nhập rồi tìm đúng dấu hiệu và nguồn | Dữ liệu tra lại khớp bản duyệt, quyền truy cập đúng | Chưa kiểm trên lab; file STIX hợp lệ chưa đủ chứng minh mục này |
| Liên quan đến tài sản doanh nghiệp | Thêm tài sản/phần mềm mẫu có phiên bản biết trước, xem cảnh báo | Cảnh báo giải thích điều kiện ảnh hưởng, nguồn và lý do ưu tiên; tài sản không khớp không bị gán chắc chắn | Chưa nghiệm thu luồng đầy đủ |
| Chất lượng AI trên báo cáo chưa từng dùng phát triển | Hai người gán nhãn độc lập rồi đối chiếu kết quả AI | Báo cáo riêng tỷ lệ đúng, tỷ lệ tìm đủ, lỗi bịa/bỏ sót, ngữ cảnh TTP, thời gian/chi phí; ngưỡng đạt thống nhất trước chạy | Chưa có corpus thật được xác minh quyền và hai người gán nhãn; giả lập không tính là chất lượng model |

## Hồ sơ mỗi lần nghiệm thu

- Bản chạy được nhận diện rõ; ngày chạy; môi trường cục bộ/lab/thật; dữ liệu tổng hợp hay thật.
- Đầu vào và kết quả mong đợi được xác định trước, có ít nhất một tình huống lỗi.
- Người dùng tự chọn một ví dụ chưa diễn sẵn và làm lại thao tác; cung cấp ảnh/video khi có công cụ phù hợp, kèm bảng kết quả có thể đọc.
- Mỗi dòng có kết luận ĐẠT / KHÔNG ĐẠT / CHƯA KIỂM và dẫn chứng của chính lần chạy đó. Không cộng số unit test thành phần trăm hoàn thành sản phẩm.
- Kiểm kỹ thuật và quyền truy cập vẫn do đội thực hiện; người dùng nghiệm thu tính đúng nghiệp vụ và khả năng sử dụng. Cả hai lớp đều cần, không yêu cầu người dùng đọc code.

## Chia trách nhiệm cho nhóm ba người

1. Hạ tầng/dữ liệu: nguồn feed, OpenCTI, chất lượng nguồn, nhập/tra lại, vận hành và bằng chứng lab.
2. Web/API/kiểm duyệt: tra cứu/tài sản/tổng quan, danh tính/quyền, duyệt/audit, các ca thao tác thật và lỗi giao diện.
3. AI/trợ lý: trích xuất có bằng chứng, C1–C4, đánh giá chất lượng, trợ lý có dẫn nguồn và quyền tạo đề xuất.

Mỗi người có module, test, demo và phần báo cáo riêng. Hai người gán nhãn độc lập; người còn lại hòa giải theo hướng dẫn chung. Cả nhóm cùng nghiệm thu một chuỗi đầu-cuối; không coi ba demo rời là hệ thống đã tích hợp.
