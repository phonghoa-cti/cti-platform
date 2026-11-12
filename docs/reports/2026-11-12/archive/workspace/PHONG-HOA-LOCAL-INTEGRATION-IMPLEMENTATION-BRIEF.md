# W05-LOCAL-INTEGRATION-NEXT — brief triển khai sau duyệt kỹ thuật

## Mục tiêu và trạng thái đầu vào

Tạo một harness tổng hợp cục bộ để kiểm browser → UI Next → gateway cùng origin → FastAPI → SQLite tạm.
Người dùng có thể list, mở detail, approve/reject; quyết định phải ghi review + audit thật vào DB fixture.
JWT phải được ký RSA và xác minh bằng JWKS fixture; không dùng `Principal` giả ở route, không đưa token/key vào browser.

Đây là brief, **chưa cho phép triển khai tự động**. Leader phải duyệt hai quyết định trước khi giao worker:

1. thêm Uvicorn direct dependency được khóa/hash vì runtime hiện thiếu ASGI server;
2. thêm factory Settings test-only cho exact HTTP IPv4 loopback, trong khi production `from_env` vẫn HTTPS-only.

Không cloud, secret thật, Cloudflare/lab/OpenCTI, push, PR, merge hoặc deploy.

## Exact refs, tree và provenance

| Mục | Giá trị bắt buộc |
|---|---|
| Backend source | `cti-w05-backend` @ `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04` |
| UI source | `cti-portal-web` @ `a791a3f2be19b4c1593f82706c47b5dca97ab51a` |
| Common ancestor | `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424` |
| Integration tree mới | `...\7f8ce74d-7efd-4136-940a-c5fab132c149\cti-w05-local-integration` |
| Branch đề xuất | `feat/w05-local-integration-20261111` |
| Base đề xuất | Backend exact SHA `02b0efe...` |
| UI commits lấy vào | `bec6b2c`, `733d82c`, `8e20595`, `a791a3f` theo đúng thứ tự |

Chỉ một CTI Engineer/Sol medium sở hữu tree này. Không sửa hai tree đã nghiệm thu.
Trước khi sửa, chứng minh tree mới sạch và HEAD/base đúng; ghi mọi conflict khi lấy UI commits.
Chỉ resolve phần xung đột cần thiết, dự kiến `docs/PROGRESS.md`; không squash làm mất provenance.
Không sửa `PHONG-HOA-RUNS.json`, các research/review/evidence lịch sử hoặc working tree của người khác.

## Quyết định kỹ thuật cần triển khai

Kiến trúc:

```text
browser
  -> http://127.0.0.1:<gateway>  (origin duy nhất browser thấy)
       /api/drafts* -> Node gateway + JWT fixture -> Uvicorn/FastAPI 127.0.0.1:<api>
       đường khác   -> Node gateway               -> Next start 127.0.0.1:<ui>
                                                        |
FastAPI -> verified Principal -> ReviewService -> SQLite temp + draft_audit
```

Mặc định port có thể lấy port trống tự động; URL thực phải được runner in **không kèm token**.
Mọi listener bind literal `127.0.0.1`; không `localhost`, `0.0.0.0`, LAN address hoặc public listener.

## File scope dự kiến

| File/phạm vi | Thay đổi được phép |
|---|---|
| `portal_api/settings.py` | Thêm explicit test-only loopback factory/cờ immutable; production `from_env` giữ HTTPS-only |
| `portal_api/tests/test_w05_api.py` hoặc test settings mới | Regression HTTP loopback test-only và production fail-closed |
| `requirements-api.in`, `requirements-api.lock` | Thêm `uvicorn>=0.54,<0.55` rồi resolve/hash; không dùng unpinned install |
| `tools/local_integration/runner.py` | Sở hữu temp DB, RSA/JWKS/token, Uvicorn và child processes |
| `tools/local_integration/gateway.mjs` | Reverse proxy loopback, fixed upstreams, JWT fixture server-side |
| `tools/local_integration/tests/**` | Gateway headers/status, HTTP matrix, cleanup/process ownership |
| `portal/web/**` | Chỉ conflict/integration bug được test chứng minh; không redesign |
| `docs/PROGRESS.md` | Ghi đúng mức local integration/browser, không tuyên bố lab/Cloudflare |

Không đặt harness auth vào `extractor/phonghoa_extractor/store.py`, không đổi policy self-review/audit.
Không thêm CORS, cookie auth, dev user, role selector, query/header impersonation hoặc production route proxy.
Không thêm certificate, CA, trust-store mutation hay tùy chọn bỏ TLS validation.

## Interface/config của harness

Runner cung cấp các scenario cố định, ví dụ:

```text
python tools/local_integration/runner.py --scenario admin-other
python tools/local_integration/runner.py --scenario analyst-self
python tools/local_integration/runner.py --scenario insufficient-role
python tools/local_integration/runner.py --scenario expired
python tools/local_integration/runner.py --scenario wrong-signature
python tools/local_integration/runner.py --scenario post-ok-refresh-503
```

Đây là tên scenario khởi động, không phải API/query do browser chọn.
Không nhận subject/role/token/key tùy ý từ command line. Fixture map là constant trong test code.
Runner chỉ in URL gateway, scenario và PID/port không nhạy cảm; không in env, JWT/JWK private hoặc CTI body.

### Settings invariants

- `Settings.from_env()` luôn yêu cầu `PORTAL_ORIGIN=https://...` và không đọc flag bypass.
- Factory test-only chỉ nhận `http://127.0.0.1:<valid-port>`, DB dưới temp root do runner tạo.
- `http://localhost`, IPv6 nếu chưa hỗ trợ, hostname, userinfo, path/query/fragment và non-loopback bị từ chối.
- Issuer/JWKS vẫn là synthetic HTTPS origin/path hợp lệ; verifier injected dùng public JWK cục bộ, không network.
- Test production gọi `from_env` với HTTP và mọi env giả `LOCAL/TEST/DEBUG` vẫn phải raise `SettingsError`.

### JWT/JWKS fixture

- Tạo RSA key mới trong RAM mỗi run; `kid` random không nhạy cảm; token RS256 sống tối đa 5 phút.
- Claims bắt buộc: synthetic exact `iss`, `aud`, non-empty `sub`, numeric `iat`, `nbf`, `exp`.
- `roles_by_subject` phía server quyết định role; bỏ qua `roles/email` claim nếu test đưa vào.
- Private key không ghi file. Token chỉ đi qua child environment gateway và `Cf-Access-Jwt-Assertion` upstream.
- Gateway xóa/ghi đè mọi header JWT do browser/caller gửi; không log raw headers.
- `expired` và `wrong-signature` dùng token ký thật nhưng không hợp lệ theo verifier; API phải trả 401 trước store.

## Quy tắc gateway

1. Route chỉ exact `/api/drafts`, `/api/drafts/<id>`, `/api/drafts/<id>/decision`; API path khác trả 404, không proxy mở.
2. UI paths proxy tới fixed Next loopback upstream; API paths tới fixed FastAPI loopback upstream.
3. Giữ method, pathname, query, request body và browser `Origin` nguyên giá trị.
4. Không tổng hợp, normalize hoặc đổi Origin; backend quyết định 403.
5. Thay `Host` theo upstream; bỏ hop-by-hop headers (`connection`, `keep-alive`, `transfer-encoding`, `upgrade`, ...).
6. Không tự retry POST. Đặt timeout hữu hạn; upstream lỗi trả 503 sanitized và `Cache-Control: no-store`.
7. Trả nguyên status/body; giữ end-to-end headers gồm `content-type`, `cache-control`, `vary`, `location`.
8. Giữ từng `Set-Cookie` riêng; focused test có hai cookie. Không cache response API hoặc lỗi.
9. API upstream base không lấy từ request/env tự do; runner truyền exact loopback URL đã kiểm.
10. Giới hạn request body nhỏ phù hợp decision JSON; quá giới hạn trả 413 trước upstream, không buffer vô hạn.

## Vòng đời tiến trình

1. Tạo một `TemporaryDirectory` và DB fixture mới; migrate/lưu draft bằng core hiện có.
2. Tạo RSA/JWKS/token trong parent; tạo FastAPI app với injected `LocalJwksClient` equivalent đã test.
3. Start Uvicorn single worker trong thread/process thuộc runner, bind `127.0.0.1`; không reload.
4. Build UI trước phép thử hoặc dùng build đã tạo trong chính run; start `next start -H 127.0.0.1 -p <ui>`.
5. Start gateway Node với token trong child env; không ghi env vào evidence.
6. Readiness bằng TCP/HTTP polling có deadline ngắn; nếu một bước fail, cleanup các bước trước và exit non-zero.
7. Khi Ctrl+C/test kết thúc: stop gateway → Next → Uvicorn; chờ graceful timeout, rồi terminate **chỉ handle/PID đã tạo**.
8. Đóng DB/threads, xóa temp root; kiểm ports không accept kết nối và child handles đều exited.

Không dùng `taskkill /IM`, không kill theo port/tên process, không xóa thư mục ngoài temp root.
Cleanup thất bại là FAIL, kèm PID/port không nhạy cảm để người thực hiện xử lý thủ công.

## Dữ liệu fixture và audit

Tạo tối thiểu bốn draft tổng hợp, không lấy report thật:

- hai draft creator `author-sub` cho admin approve và reject;
- một draft creator `analyst-sub` cho self-approve 403 và self-reject 200;
- một draft giữ pending để kiểm conflict/permission không ghi nhầm.

Sau mỗi quyết định, đọc trực tiếp SQLite bằng test code:

- payload JSON gốc vẫn `status=pending` và byte/JSON semantic không bị sửa;
- review status/version/actor/reason đúng;
- đúng một audit row cho một POST thành công;
- 401/403/409/422/415/503 và double-submit không thêm audit ngoài lần thành công;
- approve chỉ là local review, không có OpenCTI ID/call.

## TDD và thứ tự triển khai

1. Viết RED cho production từ chối HTTP, factory loopback chỉ nhận exact `127.0.0.1`, gateway headers/status và cleanup.
2. Cập nhật direct dependency + lock; cài **chỉ vào venv của integration tree** sau khi Leader duyệt, ghi version/hash/license.
3. Implement settings factory tối thiểu, giữ `from_env` nguyên invariant.
4. Implement runner/JWT fixture/Uvicorn và HTTP tests không browser.
5. Implement gateway, proxy-focused tests rồi full HTTP matrix.
6. Ghép exact UI commits, resolve conflict, chạy toàn bộ Backend/UI regressions.
7. Chỉ khi HTTP matrix xanh mới mở bề mặt browser tích hợp để kiểm `/duyet` và `/duyet/mau`.
8. Dừng toàn bộ, kiểm cleanup/tree/diff; commit cục bộ một mục đích. Không push/PR/merge/deploy.

## Acceptance matrix

| Case | Unit/in-process | HTTP qua gateway | Browser tích hợp | Kỳ vọng/DB |
|---|---:|---:|---:|---|
| list pending + detail | ✓ | ✓ | ✓ | 200; no-store; detail đúng payload/review |
| admin approve draft khác | ✓ | ✓ | ✓ | 200; review approved v1; 1 audit |
| admin reject có reason | ✓ | ✓ | ✓ | 200; reason trim; 1 audit |
| analyst tự approve | ✓ | ✓ scenario riêng | tùy bề mặt | 403; DB/audit không đổi |
| role IT/không đủ quyền | ✓ | ✓ scenario riêng | không bắt buộc | 403 trước store write |
| JWT thiếu/sai chữ ký/hết hạn | ✓ | ✓ scenario riêng | không bắt buộc | 401 sanitized; DB không đổi |
| Origin thiếu/sai scheme/host/port/null | ✓ | ✓ direct request | không giả header | 403; DB không đổi |
| production nhận HTTP Origin | ✓ | n/a | n/a | app factory fail-closed |
| stale/repeat expected_version | ✓ | ✓ | ✓ | lần đầu 200, lần hai 409; 1 audit |
| Content-Type/body/extra identity field sai | ✓ | ✓ | không bắt buộc | 415/422; DB không đổi |
| no-store/error/status/header | ✓ | ✓ | quan sát network nếu có | status không bị đổi; no-store; không wildcard CORS |
| hai `Set-Cookie` upstream tổng hợp | gateway unit | ✓ focused | n/a | giữ hai header riêng, không nuốt |
| double-click decision | UI component | ✓ count request | ✓ | chỉ 1 POST/1 audit; không auto retry |
| POST 200 rồi refresh 503 | UI component | ✓ fault scenario | ✓ | success vẫn hiện; DB/audit đã ghi; reload không POST lại |
| `/duyet/mau` | UI test | gateway log | ✓ | không request `/api/drafts*`; buttons disabled |
| cleanup success | runner unit | ✓ | sau browser | chỉ child PIDs dừng; ports đóng; temp DB bị xóa |

Browser không resize được thì chỉ kiểm viewport bề mặt cung cấp (đã quan sát 1280×720), không giả 360/1440.
Nếu browser không truy cập loopback, đánh `UNVERIFIED browser`, nhưng HTTP matrix vẫn có thể PASS độc lập.

## Lệnh kiểm dự kiến

Các lệnh dưới đây chạy từ integration tree; worker phải ghi exact command, exit code và test count.

```powershell
git rev-parse HEAD
git status --short --branch
.\.venv\Scripts\python.exe -m pytest portal_api/tests tools/local_integration/tests -q
.\.venv\Scripts\python.exe -m ruff check portal_api tools/local_integration
.\.venv\Scripts\python.exe -m ruff format --check portal_api tools/local_integration
Set-Location portal\web
npm test
npm run typecheck
npm run lint
npm run build
Set-Location ..\..
.\.venv\Scripts\python.exe tools\local_integration\tests\run_http_matrix.py
git diff --check
git status --short
```

Không đưa token/private key vào command line hoặc log. `run_http_matrix.py` tự tạo fixture và tự cleanup.
Browser evidence phải ghi URL loopback, viewport thật, các bước và ảnh; không chụp token/headers nhạy cảm.

## Bàn giao bắt buộc

- SHA/branch/base, danh sách UI commits đã lấy và conflict đã resolve.
- Diff file/count; dependency version/hash/license; output runtime preflight trước/sau.
- RED/GREEN, full Backend/UI, HTTP matrix, browser steps và cleanup, mỗi mục có exit/count.
- SQLite assertions: review/audit counts cho approve/reject/conflict/self-review/double-submit.
- PASS/FAIL/UNVERIFIED tách bốn tầng: unit/in-process, HTTP integration, browser tổng hợp, Cloudflare/lab thật.
- Nêu rõ Cloudflare Access/HTTPS/lab/OpenCTI vẫn UNVERIFIED; không gọi JWT fixture là SSO thật.
- Cách hoàn tác: bỏ integration branch/worktree sau khi giữ commit/evidence; không đụng hai tree nguồn.

## Khái niệm học thêm

- **Origin:** bộ ba scheme/host/port mà browser dùng làm ranh giới web; path không thuộc Origin.
- **ASGI server:** chương trình như Uvicorn nhận HTTP rồi gọi ứng dụng FastAPI; framework một mình chưa mở cổng.
- **JWKS fixture:** bộ khóa công khai tổng hợp để kiểm chữ ký JWT trong test mà không gọi Cloudflare.
- **Optimistic concurrency:** client gửi version đã đọc; version cũ bị 409 để tránh ghi đè quyết định mới hơn.
