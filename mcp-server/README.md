# B10 — Máy chủ MCP chỉ đọc cho Hermes

MCP (Model Context Protocol) là giao thức giúp trợ lý AI hỏi một hệ thống dữ liệu bằng các công cụ có tên và tham số rõ ràng. Máy chủ này sử dụng SDK Python chính thức `mcp` (FastMCP), transport stdio. Mặc định nó đọc fixture giả lập đóng gói cùng mã; không tải báo cáo từ URL, không gửi IOC ra Internet, không dùng LLM và không có công cụ ghi, xóa, chặn, duyệt hay tạo đề xuất.

## Chạy demo ngoại tuyến trên Windows

Từ gốc repo, mở PowerShell (Python 3.12 và uv đã cài):

```powershell
$env:PYTHONPATH = "$PWD\mcp-server;$PWD\core;$PWD\extractor;$PWD"
$env:PHONGHOA_MCP_SOURCE = "fixture"
uv run --no-project --python 3.12 --with-requirements requirements-api.lock --with-requirements mcp-server/requirements.lock python -m phonghoa_mcp.server
```

Lệnh cuối khởi động tiến trình stdio; không phải HTTP server và không có trang web riêng. Nhật ký gọi tool đi qua stderr, không trộn vào JSON-RPC trên stdout. Dừng bằng Ctrl+C. Fixture không đại diện cho IOC/CVE thật.

### MCP Inspector

Cần Node.js/npm; lần đầu npx có thể phải tải Inspector. Chạy ở gốc repo với các biến môi trường trên:

```powershell
npx -y @modelcontextprotocol/inspector uv run --no-project --python 3.12 --with-requirements requirements-api.lock --with-requirements mcp-server/requirements.lock python -m phonghoa_mcp.server
```

Mở URL giao diện cục bộ do Inspector in ra, chọn STDIO, Connect, Tools, List Tools. Thử các tool:

| Tool | Tham số minh họa | Kết quả |
|---|---|---|
| lookup_ioc | value = hxxp://sample[.]example | Điểm, lý do, nguồn giả lập; IOC hiển thị defang |
| related_cves | technology = nginx hoặc web-demo | CVE liên quan theo tên công nghệ/tài sản, không khẳng định phiên bản bị ảnh hưởng |
| kev_affecting | không cần | CVE KEV liên quan công nghệ |
| pending_drafts | không cần | Tóm tắt bản nháp đang chờ duyệt |
| search_reports | query = demo | Tìm báo cáo, nội dung ngoài bọc trong tai_lieu |
| overview | không cần | Số mục chờ duyệt/KEV nhìn thấy (có cờ partial) |
| weekly_brief | không cần | Tổng hợp sự kiện trong 7 ngày, bản nháp/KEV |
| events_since | timestamp = 2026-11-25T00:00:00Z | Sự kiện sau mốc ISO 8601 |

Giới hạn limit từ 1–50 (mặc định 20). Giá trị sai trả invalid_input; nguồn lỗi/chưa cấu hình trả unavailable thay vì giả vờ có dữ liệu. Trường data_mode phân biệt fixture/opencti, partial báo kết quả bị giới hạn. JSON nằm trong thẻ tai_lieu; ký tự có thể đóng thẻ được escape theo JSON. Nội dung báo cáo vẫn là dữ liệu không tin cậy, không phải chỉ thị; lớp bao không bảo đảm LLM chống injection tuyệt đối. Chỉ trả bản ghi TLP:CLEAR/GREEN, loại bản ghi thiếu/không rõ nhãn hoặc mang nhãn hạn chế trong dữ liệu OpenCTI. Không suy ra IOC an toàn chỉ vì không tìm thấy.

## Chế độ live (chưa nghiệm thu trên server thật)

Chỉ bật khi có môi trường được phép, token dịch vụ OpenCTI **chỉ đọc** và HTTPS có chứng chỉ hợp lệ. Đặt biến môi trường (không ghi secret vào repo):

- PHONGHOA_MCP_SOURCE=opencti
- OPENCTI_URL, OPENCTI_TOKEN
- PHONGHOA_PORTAL_URL, PHONGHOA_PORTAL_TOKEN (tùy chọn; cần cả hai nếu bật)

Chạy cùng PYTHONPATH như trên nhưng thay dependency bằng `mcp-server/requirements-live.lock` (không ghép requirements-api.lock vì ràng buộc FastAPI của pycti khác).

```powershell
uv run --no-project --python 3.12 --with-requirements mcp-server/requirements-live.lock python -m phonghoa_mcp.server
```

Adapter pycti dùng list chỉ đọc để tìm IOC và Report; tìm IOC bằng giá trị chuẩn, không tính điểm Phong Hỏa nếu không có facts nguồn. Nếu cấu hình portal, GET /api/ioc tái dùng dịch vụ tính điểm; GET /api/cves và GET /api/drafts đọc tài sản/công nghệ và W05 do portal quản lý. Portal hiện chưa có hợp đồng auth/role agent hoàn chỉnh theo A01: chưa cấp quyền analyst/admin thay thế, chưa kiểm JWT/API key live; khi không có quyền/cấu hình thì tool báo unavailable. API CVE hiện là dữ liệu synthetic, trường dataset_kind được giữ để không nhầm với dữ liệu thật. Live event stream chưa triển khai; events_since/weekly_brief báo unavailable trong chế độ này. Không gọi API ghi. SDK pycti đã pin, nhưng tương thích với phiên bản OpenCTI của lab chưa xác minh. HTTPS bắt buộc; nếu OpenCTI lab chỉ HTTP, cần cổng TLS phù hợp trước khi bật.

Lock được tạo bằng uv trên Windows/Python 3.12; cần xác minh/cập nhật lock cho Ubuntu trước khi triển khai Hermes. Hai lock tách riêng nhằm không đổi lock portal hiện có. Không triển khai Hermes, Telegram, cron, tạo nháp hay đề xuất chặn trong B10.

## Kiểm thử

Từ gốc repo (sau khi uv đã tải dependency vào cache):

```powershell
$env:PYTHONIOENCODING = "utf-8"
$deps = @('--offline','--no-project','--python','3.12','--with-requirements','requirements-api.lock','--with-requirements','requirements-stix-test.lock','--with-requirements','extractor/requirements-local-ingest.lock','--with-requirements','mcp-server/requirements.lock')
uv run @deps ruff check .
uv run @deps ruff format --check .
uv run @deps python -m pytest
```

Test dùng fixture và mock, có kiểm tra handshake MCP qua stdio thật (tiến trình con), không dùng OpenCTI/portal thật. CI hiện chưa nạp lock MCP; cần điều phối cập nhật lệnh cài dependency CI ở việc riêng trước khi merge, không bỏ qua test.
