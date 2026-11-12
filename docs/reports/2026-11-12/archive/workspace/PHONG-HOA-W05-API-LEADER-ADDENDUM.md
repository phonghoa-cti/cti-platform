# Quyết định Leader cho W05-API-IMPLEMENT — 11/11/2026

Áp dụng cùng `PHONG-HOA-W05-API-IMPLEMENTATION-BRIEF.md`; bản này ưu tiên nếu khác brief nghiên cứu. Chấp nhận phương án ba endpoint GET list/detail + POST decision, tái dùng W05 core. Đây là triển khai và test cục bộ, chưa nối Cloudflare/lab thật.

## Phạm vi và môi trường

- Owner CTI Backend, Sol medium, không giao bot/agent khác. Tree `cti-w05-backend` hiện sạch ở `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`; tạo branch `feat/w05-api-local-20261111` ngay trên tree riêng này. Không merge/cherry-pick nhánh khác.
- Tạo **venv riêng tại cti-w05-backend/.venv**, không cài hoặc đổi `cti-platform-start/.venv` mà AI đang dùng. Tải package công khai từ registry chính thức để cài/lock được phép; không gửi dữ liệu CTI, không gọi Cloudflare/OpenCTI/provider thật. Tất cả test/demo không mạng. Không coi tải dependency là kiểm production.
- Ngoài file scope brief, cho sửa `.gitignore` để bỏ .venv/artifact, `pytest.ini` để thêm testpaths/pythonpath API, `ruff.toml` nếu cần nhận diện package, `portal_api/README.md`, manifest/lock API. Full suite phải thực sự chứa test API; ghi số collect cho nhóm mới. Không sửa core/store/migration.
- Lock đầy đủ runtime và test dependencies tương thích Python 3.12; có FastAPI/PyJWT[crypto]/httpx và pytest/Ruff khi cần. Ghi version/license/hash; không `--force` để bỏ conflict. Không commit venv/cache/private key thật.
- Đầu ra ngoài repo: `PHONG-HOA-W05-API-RESULT.md`, `w05-api-evidence/` ở workspace Leader. Local commit được phép; không push/PR/merge/deploy hoặc mở listener.

## Chốt auth và cấu hình

- JWT phải **có** `exp`, `iss`, `aud`, `sub`; không chỉ bật verify nếu claim tình cờ tồn tại. NumericDate là số hợp lệ hữu hạn, không bool; `nbf`/`iat` khi có phải hợp lệ và kiểm thời gian. Algorithm allowlist cố định RS256; loại alg none/HS256, key sai/unknown kid, chữ ký sai. Role chỉ từ cấu hình server theo sub. Token có role/admin tự khai không thay role server.
- JWKS URL chỉ từ cấu hình HTTPS đã kiểm và gắn đúng issuer tin cậy; không lấy URL từ token `jku`/`x5u`/`iss` chưa xác minh. Client có timeout/cache hữu hạn và lỗi trả 503/401 theo loại; test dùng keyset local/injected transport, cấm network thật. Không nhúng sample issuer/domain/AUD thành fallback.
- Phải chạy kiểm chữ ký thật với RSA test key sinh trong test; dependency override chỉ dùng cho test route thuần, không thay tất cả auth tests bằng Principal giả. Thiếu cấu hình: app factory từ chối khởi tạo rõ ràng hoặc fail closed 503, chọn một cách và ghi/test; token thiếu/sai ở cấu hình hợp lệ là 401.
- Giữ DB missing/unavailable/corrupt là 503; missing draft ID trong DB hợp lệ là 404. Core get_draft đã trả DraftNotFoundError khi không có row. Không parse nội dung exception để đoán HTTP status.

## POST và chống yêu cầu ghi giả mạo

Nghiên cứu nói cùng origin nên chưa cần CSRF là chưa đủ: browser trước Access còn có cookie. **CSRF** là trang khác khiến trình duyệt gửi yêu cầu ghi bằng phiên đăng nhập sẵn có. Chốt tối thiểu cho POST:

1. Chỉ nhận media type `application/json` (cho charset); thiếu hoặc media type khác trả 415 `unsupported_media_type`, envelope chuẩn, no-store, không gọi decide/store.
2. `Origin` bắt buộc khớp chính xác `PORTAL_ORIGIN` cấu hình, gồm scheme/host/port. Origin thiếu, `null`, sai, nhiều giá trị, suffix giả hoặc credentials/path không hợp lệ → 403 `forbidden`, không ghi. Không suy origin tin cậy từ Host/X-Forwarded-* client tự khai. Test origin dùng URL tổng hợp; không cần listener.
3. Không bật CORS wildcard hoặc lấy `Cf-Access-Jwt-Assertion` làm bằng chứng Origin. Không cho user-facing override bỏ kiểm. Nếu cần client không-browser, đó là hợp đồng riêng về sau.
4. Auth/role phải được kiểm trước truy cập store. Requests thiếu/sai auth không lộ DB/path/record qua validation. GET không có side effect/migration.

Nguồn đã đối chiếu 11/11: [PyJWT require claims](https://pyjwt.readthedocs.io/en/stable/usage.html#requiring-presence-of-claims), [Cloudflare Access JWT](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/), [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). Origin policy trên là quyết định triển khai bảo thủ của Leader; kiểm qua in-process test không chứng minh topology/proxy thật.

## Contract/output và kiểm

- Giữ ba endpoint, payload 1.0 + review riêng. Allowlist item status ở lát cắt C1 này `ok|allowlist|bia`; dữ liệu trạng thái khác cần contract riêng khi nối C3, không tự mở rộng trong API task. Summary không trả text/items/evidence/findings. Detail không trả token/claims/audit ngoài metadata review đã chốt.
- `Cache-Control: no-store` trên cả response thành công lẫn lỗi ở `/api/drafts`; không response/log token, body validation raw, text/evidence/reason/SQL/path. Response validation fail → generic503. Chặn body thừa subject/role/email, bool version và invalid enum đúng matrix.
- Thêm test claims thiếu, thời gian sai kiểu, alg confusion, role claim giả, Origin/media type và dependency không mạng vào matrix gốc. Run targeted auth/API, core regressions, full suite chứa API, Ruff/format/diff check. Demo ký token synthetic và gọi app in-process, không giả auth thành công chỉ bằng override.
- Frontend mới nhất là `9b10223d90e529432d976177e14fdf2b6ce46bb7`; chỉ đọc tham khảo. Bước UI/API wiring giao riêng sau khi Backend trả contract và evidence đủ.
