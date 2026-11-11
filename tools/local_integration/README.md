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

## W04 — Technology qua cùng gateway và SQLite

Các scenario `w04-technology-it`, `w04-technology-analyst`, `w04-technology-multi-role`,
`w04-technology-missing-token`, `w04-technology-forbidden`, `w04-technology-refresh-503` và
`w04-technology-unknown-outcome` bật cả `AssetStore` lẫn `TechnologyStore` trên cùng file SQLite. Hai schema
được tạo trong setup trước khi listener nhận request. Gateway chỉ mở chính xác collection
`/api/assets/technologies` và item `/api/assets/technologies/<positive-id>`; route gần đúng hoặc traversal trả
404, không mở proxy `/api/*` tổng quát.

Chạy ma trận HTTP Technology ngoại tuyến:

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w04-technology-integration
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w04_technology_matrix --output .\w04-technology-integration-evidence\http-assertions.json --evidence-dir .\w04-technology-integration-evidence\db
```

Fault refresh trả hai GET 503 rồi 200 sau một mutation thành công. Fault unknown để upstream commit đúng một
lần nhưng gateway trả 503, sau đó GET đối soát trả 503 rồi 200. Cả hai chỉ được bật bằng scenario nội bộ, không
có endpoint điều khiển công khai.

Helper browser dùng bốn scenario Technology tương ứng:

```powershell
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.w04_browser_helper start --scenario w04-technology-it --duration 300 --evidence ..\w04-technology-integration-evidence\browser-technology-it --state ..\w04-technology-integration-evidence\browser-technology-it.json
```

Đổi scenario sang `w04-technology-forbidden`, `w04-technology-refresh-503` hoặc
`w04-technology-unknown-outcome`. Helper không tự mở browser; phải dùng bề mặt OpenMausBot và viewport thật.
Nếu bề mặt hoặc resize không có, ghi browser/mobile là UNVERIFIED.

## W03 — CVE chỉ đọc qua gateway và SQLite W04

Scenario `w03-*` bật fixture 16 CVE tổng hợp và `TechnologyStore` trên cùng SQLite; scenario cũ
không tự bật nguồn CVE. Gateway chỉ cho `GET /api/cves`, giữ nguyên query và thay JWT phía
server. Ma trận ghi wire API thật, SQL snapshot, trace và response gần/vượt cap 1 MiB:

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w03-read-integration
..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w03_matrix --output ..\w03-integration-rework-evidence\http-matrix.json --evidence-dir ..\w03-integration-rework-evidence\http
```

Wire test dùng mặc định các response API đã capture và khóa hash trong
`portal/web/tests/fixtures/w03-integration`, nên clone/worktree mới không cần biến môi trường:

```powershell
Set-Location .\portal\web
Remove-Item Env:W03_WIRE_DIR -ErrorAction SilentlyContinue
npm test -- --run tests/cves-wire-integration.test.ts
```

Muốn đối chiếu capture mới, đặt `W03_WIRE_DIR` tới thư mục `wire` do ma trận vừa tạo:

```powershell
$env:W03_WIRE_DIR='..\..\..\w03-integration-rework-evidence\http\wire'
npm test -- --run tests/cves-wire-integration.test.ts
```

Preflight nạp và parse đủ chín fixture trước khi chạy assertions. Đường dẫn thiếu, file thiếu hoặc JSON hỏng
làm suite dừng với thông báo `[W03 wire preflight]`; lỗi đầu vào không được adapter đổi thành một test 503 PASS.
Near-cap được đọc qua HTTP provider thật với cả response có và không `Content-Length`; body vượt 1 MiB bị từ chối.
Ma trận còn thực hiện W04 PUT/POST/DELETE trên cùng SQLite, chứng minh matches và cursor thay đổi trong khi mọi
W03 GET vẫn giữ nguyên schema/row/audit/user version.

Browser helper cho bốn scenario bounded: `w03-it`, `w03-leader`, `w03-snapshot-change`,
`w03-refresh-503`. Helper lưu DB ban đầu/cuối, trace đã lược và cleanup; nó không tự mở
browser. Kết quả này chỉ chứng minh loopback/desktop cục bộ với dữ liệu tổng hợp.

## W03-S1 — status/history qua gateway và cùng SQLite W04

Các scenario `w03-status-*` bật `CveStatusStore`, `TechnologyStore`, fixture CVE tổng hợp và schema bằng
bootstrap explicit trước khi listener nhận request. Scenario cũ không tự bật status. Gateway chỉ cho `GET|PUT`
trên `/api/cves/<CVE>/technologies/<positive-id>/status` và `GET` trên `status-history`; route/method gần đúng trả
404. Chỉ PUT status có cap 16 KiB, các cap cũ không đổi.

```powershell
Set-Location C:\Users\ABC\.openmausbot\task-workspaces\0c356bb4-b9e0-4899-a6f5-232bc89b4048\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w03-status-integration
..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w03_status_matrix --output ..\w03-status-integration-prep-evidence\http-matrix.json --evidence-dir ..\w03-status-integration-prep-evidence\http
```

Fault `known-commit` trả PUT 200 rồi GET `503→503→200`; fault `unknown-outcome` để upstream commit đúng một lần
nhưng trả PUT 503 rồi GET `503→200`. Trace chỉ ghi counter/method/path/status, và client chỉ retry GET. Ma trận
chứng minh HTTP loopback cục bộ bằng JWT, SQLite và dữ liệu tổng hợp; chưa ghép UI, chưa chạy browser và không
chứng minh Cloudflare/JWKS/HTTPS thật, feed/OpenCTI, lab hay production.
