# Connector MST (B03)

Thu RSS cảnh báo tiếng Việt, dùng `phonghoa_core.extract_iocs` và `extract_cves` để trích dấu hiệu, chuyển thành Report + observable/Vulnerability STIX 2.1 có link nguồn và ID ổn định. Chỉ là ứng viên chưa xác minh, không phải danh sách chặn.

## Chạy ngoại tuyến (từ gốc repo)

Python 3.12; đặt PYTHONPATH trỏ tới `core`. Ví dụ PowerShell:

```powershell
$env:PYTHONPATH = "core"
python -m connectors.mst.src.main --fixture connectors/mst/tests/fixtures/synthetic.rss --output bundle-mst-demo.json
```

Output phải là đường dẫn chưa tồn tại; không ghi đè. Fixture luôn được đánh dấu synthetic và không được nhập OpenCTI kể cả có token. Để kiểm mẫu rút gọn bài thật, thay tên fixture bằng `mst_excerpt.rss`. Test dùng fixture và mock, không gọi Internet:

```powershell
python -m pytest connectors/mst/tests
stix2_validator --version 2.1 --enforce-refs bundle-mst-demo.json
```

## Chạy live (chưa nghiệm thu)

Sau khi nhóm xác minh điều khoản/robots và nguồn được phép chia sẻ, chạy mỗi giờ bằng bộ lập lịch **bên ngoài** (không chạy nhiều tiến trình song song). Không dùng fixture làm dữ liệu thật.

```powershell
python -m connectors.mst.src.main --live --confirm-terms --output bundle-mst-live.json
```

CLI luôn tạo tệp STIX để kiểm tra; chưa tự bật mạng, chưa có crawler toàn văn. Chỉ khi người có quyền chủ động chọn `--publish` cho lần chạy live và cung cấp `OPENCTI_URL`, `OPENCTI_TOKEN` qua môi trường, CLI mới gọi pycti. Không đọc file .env tự động; không lưu token trong Git. Dùng pycti tương thích phiên bản OpenCTI lab; API `OpenCTIApiClient.stix2.import_bundle(..., update=False)`; TLS verification bật. Nếu nhập lỗi, tệp bundle vẫn còn; kiểm tra kết quả trên lab trước khi retry. Không dùng đường gửi trực tiếp này trong demo có yêu cầu duyệt từng bundle: dùng tệp và ImportFileStix chờ analyst duyệt theo Wiki F01.

B03 không cài pycti, Docker hay OpenCTI. Chưa xác minh import, xử lý trùng trên OpenCTI và RAM thực tế; không coi đây là một feed production đã hoạt động. Xem SOURCE.md để biết provenance, giới hạn, quyền dữ liệu.
