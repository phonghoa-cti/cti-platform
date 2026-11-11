# Harness tích hợp cục bộ W05

Harness tạo JWT/RSA và SQLite tổng hợp, chỉ bind loopback, rồi sở hữu trọn vòng đời API, gateway, UI tùy
scenario và thư mục tạm. Scenario `stix-e2e` không khởi động UI: nó gọi extractor CLI và store CLI thật để tạo
một draft, review qua HTTP gateway/API v1, sau đó gọi STIX CLI trên cùng DB trước cleanup.

Chạy ma trận E2E ngoại tuyến:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tools\local_integration\tests\run_stix_e2e.py
```

Kết quả PASS chỉ in summary hash/count đã lược dữ liệu. Fixture hoàn toàn synthetic; không gọi Internet, model,
feed, OpenCTI hay lab. Đây là bằng chứng CLI + HTTP cục bộ, không phải browser cùng draft, Cloudflare/JWKS thật,
OpenCTI import hoặc production.

## Chuẩn bị demo X01 ingest → browser → STIX

`run_ingest_browser_stix.py` dùng producer CLI đã ghim, importer CLI của checkout này và một SQLite tạm duy
nhất. Chế độ `offline-check` nhập hai lần để chứng minh duplicate không nhân bản, thực hiện selection/approve
qua core rồi hậu kiểm source/envelope/provenance, final audit và STIX read-only. Nó không mở listener hay browser:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tools\local_integration\tests\run_ingest_browser_stix.py offline-check `
  --input-kind txt `
  --producer-root <cti-x01-ingest-local> `
  --producer-python <cti-x01-ingest-local>\.venv\Scripts\python.exe
```

Sau khi importer được nghiệm thu, `browser-session --input-kind txt` sẽ seed fixture hai IOC vào cùng DB, mở stack loopback W05 do
`LocalRun` sở hữu, in một dòng `READY`, rồi chờ tối đa `--duration-seconds` để người chạy hoàn tất thao tác bằng
trình duyệt tích hợp và nhấn Enter. EOF/timeout đều FAIL đóng; cleanup luôn thuộc context manager. Chưa chạy chế
độ này và chưa có bằng chứng browser/end-to-end cho importer hiện tại.

Hậu kiểm fail-closed tính lại canonical SHA-256 của toàn envelope bằng cùng quy tắc importer; đối chiếu actor
phiên độc lập, từng selection event và final audit (action/version/hash); đồng thời khóa allowlist cấu trúc STIX
và năm marker riêng cho source name/raw/evidence/creator/reviewer trên chuỗi semantic đã parse, không phụ thuộc
JSON escape/whitespace. IOC được chọn chỉ hợp lệ trong SCO tương ứng; IOC đã bỏ phải vắng trong toàn bundle semantic
(sau khi trừ giá trị trùng vẫn được chọn). Các kiểm này bảo vệ harness, không chứng minh exporter hiện từng làm lộ
dữ liệu và không thay thế browser run.
