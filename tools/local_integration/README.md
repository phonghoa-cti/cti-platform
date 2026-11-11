# Harness tích hợp cục bộ W05 và W02

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

## W02 — tra cứu IOC qua UI → gateway → API

Các scenario `w02-it`, `w02-it-hidden-mutated`, `w02-analyst`, `w02-multi-role`,
`w02-missing-token`, `w02-forbidden` và `w02-lookup-503` chỉ dùng fixture tổng hợp
deterministic tại `w02_fixture.py`. Gateway chỉ mở đúng `/api/ioc`, thay header JWT do
caller gửi bằng JWT tổng hợp của run và không đưa JWT vào UI, URL hay output.

Chạy ma trận HTTP cùng stack UI/gateway/API:

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w02-local-integration
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w02_matrix
```

Lệnh phải chạy từ root của target để Python resolve package `tools`. Target này không có
`.venv`; executable ở trên là môi trường tích hợp có sẵn đã được dùng cho lần tái chạy và
có các dependency của harness, gồm `uvicorn`. Không thay bằng môi trường API chỉ vì nó có
Python: môi trường đó đã được kiểm và thiếu `uvicorn`. Hướng dẫn này không yêu cầu cài hay
sửa môi trường dùng chung.

PASS ở đây chỉ chứng minh loopback cục bộ với JWT/nguồn tổng hợp. Nó không chứng minh
Cloudflare/JWKS, OpenCTI, HTTPS, lab hoặc production.

## W04 — tài sản qua gateway và cùng SQLite với W02

Các scenario `w04-it`, `w04-analyst`, `w04-multi-role`, `w04-missing-token`,
`w04-forbidden`, `w04-refresh-503` và `w04-unknown-outcome` bật `AssetStore` theo kiểu opt-in. Store được khởi tạo
trong temp root do chính run sở hữu và dùng cùng file SQLite cho CRUD, audit và snapshot W02;
các scenario cũ không tự bật kho tài sản. Gateway chỉ mở `/api/assets` và
`/api/assets/<positive-id>`, vẫn dùng giới hạn body 8 KiB và thay JWT phía client bằng JWT
tổng hợp của run.

Chạy ma trận HTTP không khởi động UI:

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w04-integration-prep
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w04_matrix
```

Ma trận dùng domain `.example`, CIDR public không gọi mạng và JWT/RSA sinh cục bộ. Scenario
refresh chỉ làm hỏng một GET sau mutation thành công, rồi phục hồi 200; nó không mở endpoint
điều khiển và không retry mutation. Kết quả chỉ chứng minh HTTP loopback cục bộ; UI/browser,
Cloudflare/JWKS/HTTPS thật, lab và production chưa được kiểm.

### Helper browser bounded

Build frontend trước, rồi chạy `start` ở một terminal riêng. Lệnh giữ stack trong foreground tối đa 300 giây;
`stop` chỉ tạo marker đúng `run_id`, không kill process khác. `status` đọc trạng thái an toàn, không chứa JWT.

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w04-local-integration
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.w04_browser_helper start --scenario w04-it --duration 300 --evidence ..\w04-local-integration-evidence\browser-w04-it --state ..\w04-local-integration-evidence\browser-w04-it.json
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.w04_browser_helper status --state ..\w04-local-integration-evidence\browser-w04-it.json
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.w04_browser_helper stop --state ..\w04-local-integration-evidence\browser-w04-it.json
```

Đổi scenario sang `w04-forbidden`, `w04-refresh-503` hoặc `w04-unknown-outcome` cho ba tình huống còn lại.
Mỗi run cần evidence/state riêng. Trước cleanup, helper sao lưu SQLite bằng backup nhất quán, ghi count tổng hợp và
giữ `gateway-trace.jsonl` chỉ có counter/method/path/status. Browser vẫn phải được mở bằng bề mặt OpenMausBot;
helper không tự mở browser và không chứng minh browser acceptance.
