# Connector VSEC (B14)

Connector lấy tin từ một trang danh mục tiếng Việt, đọc tiêu đề, mô tả, ngày và liên kết rồi tạo Report, observable và Vulnerability STIX 2.1 để người phân tích kiểm tra. Dấu hiệu trích được chưa phải bằng chứng độc hại. Dùng chung kiểu Article, fetcher và bộ xuất STIX với MST; không ghi OpenCTI trực tiếp.

## Chạy ngoại tuyến từ gốc repo

Python 3.12, PYTHONPATH trỏ core. Ví dụ PowerShell:

    $env:PYTHONPATH = "core"
    python -m connectors.vsec.src.main --fixture connectors/vsec/tests/fixtures/synthetic.html --output bundle-vsec-demo.json
    python -m pytest connectors/mst/tests connectors/vsec/tests
    stix2_validator --version 2.1 --enforce-refs bundle-vsec-demo.json

Tệp output phải chưa tồn tại. Dùng vsec_excerpt.html để kiểm một mẫu tái dựng theo tin công khai; cả hai đều được gắn synthetic. Không đưa fixture lên OpenCTI. Test sử dụng fixture/mock, không gọi nguồn mạng.

## Live (chưa nghiệm thu)

**Chưa bật** trước khi nhóm xác nhận điều khoản và quyền lưu/chia sẻ, kiểm robots/quota và thiết lập lịch chạy một tiến trình tối đa mỗi giờ. Chỉ sau đó mới dùng:

    python -m connectors.vsec.src.main --live --confirm-terms --output bundle-vsec-live.json

Mặc định không truy cập mạng; chỉ rõ --live và --confirm-terms mới gọi nguồn. Không có --publish và không cần secret, không gửi LLM. Bundle là ứng viên chưa duyệt; kiểm lại bằng tay rồi dùng ImportFileStix ở chế độ draft theo Wiki F01 nếu có quyền. Không dùng fixture hoặc kết quả chưa duyệt làm cảnh báo thật. Xem SOURCE.md để biết bằng chứng, quy ước ngày và giới hạn.
