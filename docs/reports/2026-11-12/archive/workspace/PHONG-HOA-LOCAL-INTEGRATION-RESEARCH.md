# W05-LOCAL-INTEGRATION-NEXT — nghiên cứu tích hợp cục bộ

**Ngày đọc nguồn:** 11/11/2026 (ICT). **Trạng thái:** nghiên cứu, chưa tích hợp/chưa chạy listener.

## Câu hỏi và kết luận

Câu hỏi: làm sao kiểm browser → UI → API → SQLite với JWT ký thật mà vẫn giữ đúng Origin, policy review và ranh giới production HTTPS?

**Khuyến nghị: phương án C — harness loopback tách biệt, một gateway cùng origin cho browser.**
Gateway test lắng nghe duy nhất trên `127.0.0.1`, chuyển trang/UI sang Next và `/api/drafts*` sang FastAPI.
JWT tổng hợp ngắn hạn được gateway gắn phía server; browser không nhận private key/token và không tự khai role.
FastAPI dùng verifier/JWKS fixture đã có, DB tạm và một factory test-only cho Origin HTTP loopback chính xác.
`Settings.from_env()` production tiếp tục chỉ nhận HTTPS; không có biến môi trường bật tắt policy production.

## Hiện trạng đọc tại exact ref

| Thành phần | Ref và quan sát | Tái sử dụng | Khoảng trống |
|---|---|---|---|
| Backend `cti-w05-backend` | `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`, branch `feat/w05-api-local-20261111`, tree sạch | `portal_api` ba route; JWT RS256/issuer/aud/exp/sub; role theo `sub`; Origin exact; no-store; SQLite decision/audit | Chưa có ASGI server/runtime listener; `PORTAL_ORIGIN` chỉ HTTPS |
| UI `cti-portal-web` | `a791a3f2be19b4c1593f82706c47b5dca97ab51a`, branch `feat/portal-w05-api-client-20261111`, tree sạch | URL tương đối `/api/drafts*`; same-origin/no-store; state list/detail/decision; chống gửi kép; giữ success khi refresh lỗi | `/api/drafts*` hiện 404 vì không có routing; browser chưa có JWT tổng hợp |
| Common ancestor | `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`; hai ref không là ancestor của nhau | Có thể tạo tree tích hợp mới, base Backend rồi lấy đúng 4 commit UI | `docs/PROGRESS.md` sẽ cần giải xung đột có chủ ý |
| UI commit provenance | `bec6b2c`, `733d82c`, `8e20595`, `a791a3f` từ base `9b10223` | Giữ đủ API client, race guard, refresh-after-write và R1/R2 | Không lấy working copy hoặc chép tay không provenance |

Backend khóa FastAPI `0.119.1`, Starlette `0.48.0`, HTTPX `0.28.1`, PyJWT `2.15.1`.
UI khóa Next `16.4.6`, React `19.3.1`, Node quan sát được `24.22.1`.
`portal_api.app.create_app(..., verifier=...)` đã có điểm inject verifier; test hiện có tạo RSA/JWK cục bộ và không dùng mạng.
`portal_api.settings._portal_origin()` hiện gọi `_https_origin()`, nên HTTP `127.0.0.1` bị từ chối đúng thiết kế.

Runtime vừa đọc cho thấy `.venv` có FastAPI nhưng không có `uvicorn`/`hypercorn`.
`fastapi.exe --help` thoát `1`: CLI yêu cầu cài `fastapi[standard]`; do đó hiện chưa thể mở API bằng runtime đã khóa.
FastAPI chính thức cũng nêu ứng dụng ASGI cần một ASGI server như Uvicorn.
Uvicorn `0.54.0` là bản PyPI hiện hành ngày đọc, Python `>=3.10`, BSD-3-Clause; chưa cài và chưa kiểm tương thích repo.

## Ba phương án thực sự

| Cách | Cơ chế | Ưu điểm | Vấn đề trong W05 | Kết luận |
|---|---|---|---|---|
| A. Next rewrite thẳng tới FastAPI | `next.config.ts` map `/api/:path*` tới backend | Ít code, URL browser vẫn relative | Không tạo được `Cf-Access-Jwt-Assertion`; browser không có Cloudflare Access local; vẫn vướng HTTP Origin và ASGI server | Không đủ auth end-to-end |
| B. Next Route Handler/Proxy | Handler server-side forward method/body và gắn JWT fixture | Có thể inject token, giữ browser cùng origin | Đưa auth-test proxy vào bề mặt ứng dụng; dễ lệch header/status/cache và bị dùng nhầm khi deploy | Khả thi nhưng scope/rủi ro lớn hơn |
| C. Gateway harness loopback riêng | Node `http` proxy UI và API; backend runner inject JWKS; DB temp | Không đổi contract UI; tách production; kiểm được request/response thật và vòng đời tiến trình | Cần code harness, ASGI server ghim/khóa và test proxy header | **Chọn** |

Next mô tả rewrite là URL proxy; Route Handler dùng Web Request/Response và GET không cache mặc định.
Hai khả năng đó chứng minh A/B khả thi về routing, không chứng minh chúng tự cung cấp danh tính Cloudflare.
Node HTTP là API thấp cấp, cho phép giữ raw/duplicate headers; nếu dùng C phải test riêng `Set-Cookie` và hop-by-hop headers.

## HTTP, HTTPS và Origin

Origin là bộ ba **scheme + hostname + port**; `http://127.0.0.1:3002` khác mọi origin HTTPS.
MDN ghi browser thường tự thêm `Origin` cho same-origin POST và đây là forbidden request header.
Vì vậy gateway phải chuyển nguyên `Origin` browser gửi, không tổng hợp/đổi thành HTTPS và không nhận Origin từ query/body.
Backend vẫn là nơi so sánh exact Origin; thiếu, `null`, sai port/host/scheme tiếp tục 403.

Next có `--experimental-https`, nhưng nó sinh/chạy với chứng chỉ tự ký qua `mkcert` và chỉ dành cho development.
Brief cấm tạo chứng chỉ, đổi trust store hoặc tắt TLS validation; bề mặt browser chưa chứng minh tin CA đó.
Do đó không chọn HTTPS giả cục bộ và không dùng `NODE_TLS_REJECT_UNAUTHORIZED=0`, `verify=False` hay tương đương.

Chế độ HTTP đề xuất chỉ tồn tại trong harness:

1. origin duy nhất là `http://127.0.0.1:<gateway-port>`; không nhận `localhost`, wildcard, hostname LAN hoặc `0.0.0.0`;
2. mọi listener bind `127.0.0.1`, không bind all interfaces;
3. `Settings.from_env()` và production app factory vẫn từ chối mọi `http://`, kể cả khi có env lạ;
4. factory/classmethod test-only tạo Settings với cờ immutable, DB dưới thư mục tạm và synthetic issuer HTTPS;
5. unit test chứng minh production fail-closed và HTTP non-loopback luôn bị từ chối.

Đây là thay đổi policy cần Leader duyệt trước code; nghiên cứu này không tự sửa policy.

## JWT/JWKS tổng hợp và danh tính

Cloudflare ghi JWT ứng dụng ở `Cf-Access-Jwt-Assertion`, khóa công khai ở team JWKS và phải kiểm signature, issuer, audience.
Harness mô phỏng đúng cryptographic boundary: RSA key tạo trong RAM, public JWK đưa vào `LocalJwksClient`, token RS256 có `kid`, `iss`, `aud`, `sub`, `iat`, `nbf`, `exp` ngắn.
Nó **không** mô phỏng Cloudflare login, cookie `CF_Authorization`, key rotation, team domain, Access policy hay tunnel.

Private key không ghi file; token chỉ truyền vào môi trường child gateway và bị xóa khi process dừng.
Không in env, token, claim đầy đủ, key hoặc raw request headers vào log/evidence.
Gateway bỏ mọi JWT header từ browser và gắn một token cố định theo scenario khởi động.
Không có role dropdown, header impersonation, query đổi user hoặc endpoint mint token.
Role vẫn lookup server-side qua `roles_by_subject`; claim `roles/email` không tạo quyền.

Danh tính fixture tối thiểu:

| Scenario cố định khi start | Subject/role server-side | Mục đích |
|---|---|---|
| `admin-other` | `admin-sub` → admin | list/detail; approve/reject draft của người khác |
| `analyst-self` | `analyst-sub` → analyst | approve draft của chính mình phải 403; reject có lý do được phép |
| `insufficient-role` | `it-sub` → it | mọi route W05 trả 403, DB không đổi |
| `expired` / `wrong-signature` | token không hợp lệ | 401 trước store; DB không tạo/đổi |

Mỗi run chỉ có một identity cố định; đổi scenario phải dừng sạch rồi start run mới.

## Gateway và bảo toàn HTTP

Browser chỉ mở gateway. `/api/drafts` và descendants đi FastAPI; mọi đường khác đi Next đã build/start.
Đích upstream là constant loopback do harness cấp, không lấy từ URL người dùng để tránh SSRF.
Gateway giữ method, pathname, query, body, status và Origin; thay `Host`, bỏ hop-by-hop headers và tự tính framing.
Gateway phải ghi đè JWT header bằng fixture server-side, không forward giá trị caller gửi.
Response giữ content type, cache-control, vary, location và mọi `Set-Cookie`; nhiều `Set-Cookie` không được nối sai.
Test proxy dùng upstream tổng hợp để chứng minh status 401/403/409/503 và header lỗi không bị biến thành 200/generic error.
Không cache GET/POST; response API thực vẫn phải có `Cache-Control: no-store` và không wildcard CORS.

## Vòng đời và cleanup

Một runner sở hữu DB temp, Uvicorn, Next và gateway; ghi PID/process handle nội bộ, không ghi token.
Thứ tự start: tạo DB/fixture → tạo key/JWKS/token → API ready → Next ready → gateway ready.
Readiness dùng TCP/HTTP có timeout; không dựa vào sleep cố định hoặc log chuỗi.
Khi lỗi/CTRL+C/test xong: ngừng nhận request, dừng gateway, Next, Uvicorn; chờ timeout rồi chỉ terminate PID do runner tạo.
Chỉ xóa thư mục tạm do runner tạo sau khi các handle đóng; không `taskkill` theo tên, không quét/xóa DB khác.
Sau cleanup kiểm ba port không còn listener và file DB temp không còn; thất bại cleanup làm test fail.

## Bề mặt browser và giới hạn bằng chứng

Kết quả UI đã nghiệm thu chỉ chứng minh browser tích hợp ở 1280×720: `/duyet` 404 an toàn và `/duyet/mau` không gọi API.
Bề mặt đó chưa có resize hợp lệ; 360/1440 vẫn UNVERIFIED, không dùng CSS/zoom/browser khác để giả viewport.
W05-LOCAL có thể dùng chính bề mặt này sau khi harness chạy; không điều khiển browser riêng của người dùng.
Nếu bề mặt không truy cập loopback hoặc không gửi Origin đúng, ghi blocker browser và chỉ báo HTTP integration PASS.
HTTP client/in-process không được gọi là browser E2E.

## Nguồn chính thức và khả năng tái sử dụng

- Next.js 16 CLI/HTTPS dev: https://nextjs.org/docs/app/api-reference/cli/next
- Next.js Route Handlers: https://nextjs.org/docs/app/getting-started/route-handlers
- Next.js rewrites/BFF proxy: https://nextjs.org/docs/app/guides/backend-for-frontend
- FastAPI ASGI server: https://fastapi.tiangolo.com/deployment/manually/
- Uvicorn 0.54.0 metadata/license/provenance: https://pypi.org/project/uvicorn/0.54.0/
- MDN Origin: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin
- MDN same-origin/CORS: https://developer.mozilla.org/en-US/docs/Glossary/Origin
- Cloudflare Access JWT validation: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- Node HTTP: https://nodejs.org/download/release/v24.17.0/docs/api/http.html

Tái sử dụng nguyên trạng: UI client/state tests, backend routes/service/core policy, RSA/JWK fixture logic, SQLite temporary fixtures và error contract.
Điều chỉnh nhỏ cần duyệt: explicit loopback Settings factory, Uvicorn direct dependency/lock, integration runner/gateway/tests.
Không tái xây auth/decision/audit; không thêm CORS, dev user, API key, OpenCTI hoặc production proxy.

## Chưa biết / chưa kiểm

- **UNVERIFIED:** Uvicorn 0.54.0 với dependency lock và Windows/Python 3.12 của tree; phải lock/hash/test sau duyệt.
- **UNVERIFIED:** gateway Node giữ duplicate `Set-Cookie` đúng trên runtime 24.22.1; cần focused test.
- **UNVERIFIED:** bề mặt browser truy cập gateway loopback và behavior process termination trên host hiện tại.
- **UNVERIFIED:** Cloudflare Access thật, JWKS rotation/network, HTTPS certificate, reverse proxy/lab và OpenCTI.
- Không có integration nào được thực hiện trong lượt nghiên cứu này.
