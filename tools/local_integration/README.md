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
.\.venv\Scripts\python.exe -X utf8 -B tools\local_integration\tests\run_w02_matrix.py
```

PASS ở đây chỉ chứng minh loopback cục bộ với JWT/nguồn tổng hợp. Nó không chứng minh
Cloudflare/JWKS, OpenCTI, HTTPS, lab hoặc production.
