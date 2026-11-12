# W04-INTEGRATION-PREP — kết quả chuẩn bị HTTP/gateway cục bộ

## Kết quả

**PASS cục bộ tại commit `652545688fb5dd7bb4fe974c597fed370e9ad0f0`.** Tree riêng sạch, bắt đầu đúng Backend accepted `90b26287eccc416fd7e7e736b0ad37632e0c34b1`. Đây là local harness chuẩn bị cho bước nối Frontend sau nghiệm thu; chưa phải nghiệm thu W04 UI/browser.

- Tree: `cti-w04-integration-prep`
- Branch: `feat/w04-integration-prep-20261111`
- Delta: 8 file, `+469/-7`, chỉ `tools/local_integration/`, tests, README và `docs/PROGRESS.md` theo allowlist.
- Gateway mở chính xác `/api/assets` và `/api/assets/<positive-id>`, giữ cap body 8 KiB, Origin do client gửi, thay JWT client bằng JWT tổng hợp phía runner, không mở route API khác.
- Scenario W04 opt-in khởi tạo `AssetStore` trong temp root và inject cùng instance/path SQLite cho CRUD/audit với snapshot W02; scenario cũ không tự bật store.
- Fault W04 chỉ làm hỏng một GET assets sau mutation thành công rồi tự phục hồi; không có endpoint điều khiển và không retry mutation.

## Kiểm chứng vừa chạy

Interpreter: `cti-x01-ingest-browser-prep/.venv/Scripts/python.exe`, Python 3.12.13; module `uvicorn` được resolve trong chính môi trường này.

| Kiểm | Kết quả |
|---|---|
| `python -m pytest tools/local_integration/tests/test_runner.py -o addopts= -q --junitxml <evidence>/runner-tests.xml` | exit 0; **31 passed**, 0 failed |
| `node --test tools/local_integration/tests/test_gateway.mjs` | exit 0; **12 passed**, 0 failed |
| `python -m tools.local_integration.tests.run_w04_matrix --output <evidence>/http-matrix.json` | exit 0; **64 assertions**, PASS |
| `python -m ruff check tools/local_integration` | exit 0; All checks passed |
| `python -m ruff format --check tools/local_integration` | exit 0; 12 files already formatted |
| `git diff --check` | exit 0 |
| `git status --porcelain` sau commit | 0 dòng; tree sạch |

RED→GREEN mới:

- Gateway asset route/fault: RED 2/2 fail đúng vì route chưa mở; GREEN 2/2 pass.
- Runner W04 opt-in/role/shared DB: RED 6/6 fail đúng vì scenario chưa tồn tại; GREEN 6/6 pass.
- Lần đầu ma trận phát hiện chính script kiểm chứng giữ connection SQLite trên Windows nên cleanup không xóa được DB; sửa test dùng connection đóng tường minh, sau đó 64/64 assertion và cleanup đều đạt.

## Ma trận HTTP và DB

- Cùng run chính: create domain + CIDR, list, update version `1→2`, delete; duplicate và stale version đều 409.
- Lookup cùng SQLite: domain, subdomain, CIDR và URL có path/query có `asset_match`; sau delete, subdomain trở về `not_found` và không còn match.
- Audit cùng DB: 2 create + 1 update + 1 delete = **4 row**; actor đều `it-sub`; update có before/after, delete có before và after null.
- Quyền: IT 200, analyst 200, multi-role 200, lãnh đạo 403, thiếu token 401. JWT giả phía client không vượt quyền.
- Sai Origin 403 và body >8 KiB 413 đều xảy ra trước mutation: DB/audit vẫn `0/0`.
- Recovery: đúng **1 mutation**, hai GET có status `[503, 200]`, DB giữ **1 asset/1 audit**; chứng minh không replay mutation.
- Cleanup: temp root đã xóa, API thread dừng và gateway port đóng trong cả run chính lẫn run fault.

Raw evidence: `w04-integration-prep-evidence/` gồm JUnit, log runner/gateway, JSON ma trận, lint/format/diff-check và `verification.json` có SHA256 artifact chính.

## Phạm vi chưa kiểm chứng

**UNVERIFIED:** ghép commit này với Frontend accepted, UI/browser W04, build UI, Cloudflare/JWKS/HTTPS thật, OpenCTI, feed/LLM thật, lab và production. Không push, PR, merge hoặc deploy.

## Hoàn tác

Từ nhánh có commit này, dùng `git revert 652545688fb5dd7bb4fe974c597fed370e9ad0f0` để tạo commit đảo ngược; không reset/xóa tree đang được owner khác dùng.

## Học thêm

- **Opt-in dependency injection:** chỉ truyền kho tài sản cho scenario W04, nhờ đó luồng cũ giữ nguyên mặc định.
- **Optimistic concurrency:** client gửi version đã đọc; version cũ bị 409 để tránh ghi đè thay đổi mới hơn.
- **One-shot fault:** lỗi tổng hợp chỉ xảy ra một lần để kiểm recovery mà không tạo cơ chế điều khiển nguy hiểm.
- **Owned cleanup:** runner chỉ dừng process/listener và xóa temp root do chính run tạo.
