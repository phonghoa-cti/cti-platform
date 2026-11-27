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


## B11 — Bot Telegram (lát cắt Hermes)

Bot dùng python-telegram-bot (polling: chủ động lấy tin từ Telegram), gọi B10 bằng MCP stdio trong tiến trình Python riêng. Hiện **chỉ fixture tổng hợp**, không kết nối OpenCTI/portal thật, không có token OpenCTI trong bot. Đây là bot Python độc lập theo brief B11, chưa phải tích hợp gateway của Hermes Agent upstream, cron, W05 hoặc LLM. Mỗi lệnh đọc gọi một tool cố định (timeout 25 giây); không có diễn giải lệnh tự nhiên hoặc tool thực thi.

### Cấu hình chạy thử (chỉ khi nhóm có bot Telegram riêng)

1. Tạo bot bằng BotFather; giữ token ngoài Git. Tự đặt các biến env theo .env.example (file mẫu chỉ chứa tên biến, không tự nạp file .env).
2. HERMES_TELEGRAM_CHAT_IDS: danh sách chat ID số, phân cách dấu phẩy; không có allowlist thì bot không chạy. HERMES_TELEGRAM_USER_IDS: danh sách user ID dương được phép ra lệnh. Nếu chỉ có chat riêng ID dương và bỏ trống user list, dùng chính các ID chat riêng; chat nhóm ID âm bắt buộc khai báo user list.
3. HERMES_TELEGRAM_REVIEWER_IDS: các user ID có quyền quyết định, là tập con của user list; bỏ trống nghĩa là không ai có quyền duyệt. Nút chỉ hoạt động trong chat gốc của đề xuất. Nếu cần hai người khác nhau, dùng nhóm riêng chỉ có người được phép đọc dữ liệu; trong chat riêng chỉ chủ chat đã được cấp vai reviewer mới quyết định được. B11 không áp dụng tách nhiệm vụ người đề xuất/người duyệt.
4. HERMES_TELEGRAM_DB: đường dẫn tuyệt đối tới file .sqlite trong thư mục riêng đã tồn tại, ngoài repo; chỉ cấp quyền đọc/ghi cho tài khoản chạy bot và quản trị được phép. PHONGHOA_MCP_SOURCE bỏ trống hoặc fixture; từ chối opencti. HERMES_TELEGRAM_TOKEN lấy từ env.
5. Từ gốc repo, dùng PowerShell (Python 3.12, uv):
   ```powershell
   $env:PYTHONPATH = "$PWD\mcp-server;$PWD\core;$PWD\extractor;$PWD"
   uv run --no-project --python 3.12 --with-requirements requirements-api.lock --with-requirements mcp-server/requirements.lock python -m hermes_bot
   ```
   Lệnh bắt đầu polling thật, chỉ chạy nếu đã được phép kết nối Telegram. Dừng bằng Ctrl+C. Khởi động bỏ update tồn từ trước, không tự phát lại lệnh; đề xuất đã lưu vẫn nằm trong SQLite.

| Lệnh | Kết quả |
|---|---|
| /start | Hướng dẫn tiếng Việt |
| /ioc hxxp://sample[.]example | Tra IOC (dấu hiệu có thể liên quan nguy cơ); lấy điểm và nguồn từ MCP, không tự suy điểm |
| /cve nginx | CVE liên quan tên công nghệ, chưa khẳng định phiên bản bị ảnh hưởng |
| /cve | CVE trong danh mục KEV liên quan tài sản mẫu |
| /nhap | Chỉ đọc danh sách bản nháp đang chờ |
| /tomtat | Tổng quan; /tomtat tuan đọc tóm tắt tuần |
| /dexuat chan sample[.]example Kiểm tra | Tạo đề xuất chặn cục bộ |
| /dexuat nhap hxxps://sample[.]example/report | Tạo đề xuất đọc/trích báo cáo cục bộ; không tải URL, không tạo draft W05 |

Nút Duyệt/Từ chối ghi ID người quyết định, thời điểm UTC và trạng thái cuối trong SQLite; cập nhật có điều kiện theo ID + chat gốc + pending, chống nhấn lại và tranh chấp. Trạng thái approved không phải đã chặn, đã nhập hay đã thực thi. Nếu gửi tin Telegram lỗi sau khi SQLite ghi thành công, không tự chạy lại; quản trị kiểm SQLite trước khi gửi yêu cầu mới. Không có tác vụ nền đọc hàng approved để thực thi.

Dữ liệu MCP được kiểm bao tai_lieu, trạng thái, giới hạn kích thước và nhãn TLP hạn chế; B10 lọc CLEAR/GREEN. Bot hiển thị văn bản thuần, vô hiệu hóa xem trước link, defang IOC và escape dấu thẻ, không chạy chỉ thị lấy từ dữ liệu, không gửi dữ liệu tới LLM. Không đưa dữ liệu AMBER/RED, thông tin mật hay tài sản thật vào bot demo. Allowlist kiểm người gửi, **không** ngăn thành viên khác trong một chat nhóm nhìn thấy nội dung; chỉ dùng nhóm kín đã kiểm thành viên và quyền chia sẻ TLP. Telegram là dịch vụ bên ngoài, không phải kho bí mật. Dữ liệu chưa tìm thấy không chứng minh an toàn.

### Test B11

Dùng prefix uv ngoại tuyến ở mục Kiểm thử B10 (lock hiện đã chứa python-telegram-bot); chạy thêm `python -m pytest mcp-server/tests/test_hermes_bot.py`. Test tạo đối tượng Update thật từ payload Telegram tổng hợp, giả lập các phương thức Bot và reader, lưu SQLite tạm; có round-trip stdio B10 thật với fixture, không gọi mạng Telegram, LLM hoặc OpenCTI. Chưa kiểm polling thật, thành viên nhóm thật, lịch 07:00, điều tra chủ động hay W05; không tuyên bố nghiệm thu toàn bộ A01.
