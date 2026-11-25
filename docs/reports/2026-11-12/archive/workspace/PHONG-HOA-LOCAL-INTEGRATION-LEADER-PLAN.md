# W05 Local Integration Implementation Plan

> Worker: CTI Engineer, Sol medium, tự thực hiện tuần tự theo `executing-plans` và TDD; không giao agent/bot phụ. Kế hoạch này là phần chốt của Leader, ưu tiên hơn brief nghiên cứu khi có khác biệt. Người dùng đã giao Leader tự quyết lựa chọn kỹ thuật có thể đảo ngược và nối việc; không cần hỏi lại cho phạm vi cục bộ dưới đây.

**Goal:** chạy và kiểm luồng UI → gateway loopback → FastAPI → SQLite tổng hợp, giữ xác minh JWT và quyền duyệt thật trong code.

**Architecture:** chọn phương án C, gateway Node riêng ngoài app. Một origin HTTP IPv4 loopback chỉ cho harness tổng hợp; production Settings và đường tạo app hiện có tiếp tục HTTPS-only. JWT ký trong RAM, JWKS fixture, danh tính cố định khi khởi động, DB tạm do runner sở hữu.

**Tech stack:** Python3.12, FastAPI/PyJWT đã khóa, Uvicorn0.54.0 minimal, Node HTTP, UI Next snapshot đã nghiệm thu.

**Spec:** `PHONG-HOA-LOCAL-INTEGRATION-IMPLEMENTATION-BRIEF.md`, nghiên cứu cùng tên, `cti-w05-backend/docs/specs/api-portal.md` tại02b0efe. Đọc cả brief và kế hoạch này; giữ acceptance matrix của brief.

## Các quyết định Leader đã chốt

1. Cho phép thêm **uvicorn==0.54.0** bản minimal, không extras; khóa đủ dependency/hash trong integration tree riêng. PyPI xác nhận wheel `uvicorn-0.54.0-py3-none-any.whl`, SHA256 `505bdb0f318731d45f1f712071fc781a8981f6847a31c902c9f5e652d4f67faf`, BSD-3-Clause, Python>=3.10. Chưa kiểm runtime tương thích: worker phải kiểm sau cài. Không nâng dependency API/UI khác nếu không có xung đột cụ thể; không cài global hoặc sửa venv nguồn.
2. Cho phép factory explicit test-only cho HTTP127.0.0.1 và DB temp trong **tree tích hợp riêng**. `Settings.from_env()` và constructor/default production vẫn phải từ chối HTTP; không có env flag mở bypass. Mọi trường còn lại phải qua validation thực, không monkeypatch `__post_init__`, không tạo Settings HTTPS giả rồi sửa attribute sang HTTP. Tách rõ local factory khỏi đường khởi động production, chạy regression fail-closed trước khi mở listener.
3. **Thay toàn bộ chỉ dẫn lấy bốn UI commit trong brief.** Backend02b0efe chưa có `portal/web`; lịch sử UI từ common ancestor có cả previewbe364bd và clipboard9b10223 trước bốn commit cuối. Chỉ lấy bốn commit sẽ thiếu nền. Tạo tree mới từ Backend02b0efe, nhập **toàn bộ tracked path `portal/web` tại UIa791a3f** thành snapshot có provenance. Không `git merge`, không cherry-pick, không lấy working copy, không lấy docs/PROGRESS từ UI. Không đổi hai nhánh/tree nguồn.
4. Chỉ chủ sở hữu Engineer sửa tree mới. UI snapshot giữ nguyên hành vi; nếu phát hiện lỗi UI cần sửa thì ghi finding cụ thể, không tự redesign hoặc sửa UI trong lượt này. Không tích hợp AI branch vào W05.
5. Có thể tải dependency công khai từ PyPI/npm theo lock vào tree riêng và mở listener loopback có thời hạn để kiểm. Không cloud/secret thật/lab/OpenCTI/push/PR/merge/deploy; không tạo chứng chỉ, thay trust store, tắt TLS validation hoặc đổi quyền.

## Tree, scope và bằng chứng

- Root: `$WORKSPACE`.
- Tree mới: root/`cti-w05-local-integration`; branch `feat/w05-local-integration-20261111`; base `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`. Nếu path/branch đã tồn tại không rõ owner, báo cụ thể, không reset/xóa.
- UI source `a791a3f2be19b4c1593f82706c47b5dca97ab51a`; Git tree hash của `portal/web`: `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`.
- Trong tree mới, nhập snapshot bằng `git restore --source=a791a3f2be19b4c1593f82706c47b5dca97ab51a --staged --worktree -- portal/web`. Ghi commit riêng cùng sourceSHA/treehash. Kiểm `git diff <UI-SHA> -- portal/web` rỗng và đầy đủ package-lock/config/app/components/tests trước sửa harness. Đây là snapshot cục bộ có nguồn, không hợp nhất nhánh sản phẩm.
- Cho phép sửa settings/test settings, requirements-api.in/lock, thêm `tools/local_integration/**`, cập nhật pytest.ini/ruff.toml/.gitignore chỉ để chạy/ignore harness nếu cần; docs/PROGRESS.md và `docs/adr/20261111-w05-local-harness.md`.
- `portal/web/**` chỉ nhập exact snapshot, `npm ci` và build/test trong tree mới; không thay package-lock hoặc component.
- Kết quả ngoài repo: `PHONG-HOA-LOCAL-INTEGRATION-RESULT.md` và `local-integration-evidence/`. Không sửa RUNS/brief/review cũ hoặc các evidence lịch sử.

## Review focus

- Thiếu nền UI khi ghép ref: test/manifest snapshot khớp treehash trước khi chạy.
- Local mode bị dùng nhầm production: test default/from_env vẫn reject HTTP và factory chỉ nhận exact literal127.0.0.1:port, temp DB của runner.
- Header lặp hoặc `Connection` nêu tên header: proxy phải xử lý hop-by-hop cả tên động, giữ Origin thật và thay JWT sau bước loại header; không cho caller đổi identity.
- Khởi động dở/port bận/client ngắt: timeout hữu hạn, không retry POST, cleanup chỉ handle/DB thuộc run này, không kill tiến trình khác.
- Token hết hạn khi đang kiểm browser: run có deadline tối đa300giây và cleanup tự động; không gia hạn vô hạn hoặc chuyển sang bỏ xác minh.

## Task1 — snapshot, runtime và local settings

Files: settings.py, test settings mới trong portal_api/tests, requirements-api.in/lock, tools/local_integration/local_settings.py nếu cần, docs ADR/progress.

- [ ] Dùng hướng dẫn worktree tạo đúng tree/base sạch, ghi refs; nhập nguyên snapshot UI và xác minh treehash; commit provenance.
- [ ] Viết RED `test_local_origin_requires_owned_temp_db`, `test_local_origin_rejects_noncanonical_address`, `test_production_settings_reject_http_despite_debug_env`: loopback/port hợp lệ pass; null/bool/list/dict, port0/>65535, localhost/LAN/IPv6/userinfo/path/query/fragment/trailing slash và DB ngoài temp root fail gọn.
- [ ] Thêm Uvicorn đúng phiên bản, lock/hash với constraints giữ dependency hiện tại; cài vào `.venv` tree mới, `npm ci` theo UI lock. Ghi preflight trước/sau; không dùng shared venv để cài.
- [ ] Implement local factory có tên rõ `make_local_settings(db_path: Path, temp_root: Path, gateway_port: int, roles_by_subject: Mapping) -> Settings` trong harness hoặc wrapper mỏng; sửa Settings tối thiểu để hỗ trợ đường này có validation rõ. Issuer/JWKS constants tổng hợp vẫn HTTPS; từ chối file DB có sẵn không do run tạo.
- [ ] Chạy GREEN nhóm settings + API regression; ghi RED/GREEN; commit cục bộ. Không mở listener trước khi gate này xanh.

## Task2 — gateway và runner sở hữu tài nguyên

Files: `tools/local_integration/gateway.mjs`, `runner.py`, fixture helper nếu cần; `tools/local_integration/tests/test_gateway.mjs`, `test_runner.py`.

- [ ] Viết RED gateway: giữ status/body/no-store/Vary/two Set-Cookie, Origin thiếu/sai không tự bổ sung, JWT caller lặp/case khác bị loại, dynamic hop-by-hop headers bị loại, body quá giới hạn413, timeout503 gọn, không retry POST. Đích upstream chỉ constant loopback; Host không phải gateway exact127.0.0.1:port bị từ chối.
- [ ] Implement `startGateway({apiPort, uiPort, port, jwt}) -> Promise<http.Server>`; jwt là string hoặc null chỉ từ runner, không từ caller. Route API allowlist như brief; UI upstream fixed; response API lỗi không lộ token/key/raw headers. Giữ API guard Origin thật.
- [ ] Viết RED runner start failure/port busy/deadline/cleanup ownership. Không dừng service có sẵn theo tên hoặc port; test dùng sentinel process/dir khác và xác nhận còn nguyên.
- [ ] Implement context manager `LocalRun(scenario: str, duration_seconds: int = 300)` với start/close và metadata đã loại bí mật; scenario allowlist gồm admin-other, analyst-self, insufficient-role, **missing-token**, expired, wrong-signature, post-ok-refresh-503. Missing-token không inject JWT nhưng vẫn loại JWT caller; các scenario khác token ký thật có expiry ngắn.
- [ ] Tạo RSA/JWKS ở RAM và inject `AccessJwtVerifier` có LocalJwksClient, không mock Principal/verifier.verify; fixture DB dùng core/store đã có. Chạy Uvicorn single-worker và Node/Next child không mở cửa sổ trên Windows; listener tất cả127.0.0.1.
- [ ] Readiness có deadline ngắn và timeout từng request. TTL run<=300giây, heartbeat/log không chứa token/key/body; cleanup cả thành công/lỗi/deadline. GREEN gateway/runner rồi commit.

## Task3 — luồng duyệt HTTP và browser tổng hợp

Files: `tools/local_integration/tests/run_http_matrix.py`, test integration cần thiết, docs progress/ADR; report/evidence ở root.

- [ ] Chạy matrix đầy đủ trong brief với HTTP thật qua gateway, mỗi scenario có run/DB riêng; đọc SQLite trực tiếp xác minh đúng review/audit và không đổi payload. Fault refresh503 chỉ ở harness, giữ POST đã ghi và không POST lại.
- [ ] Chạy toàn API/core hồi quy liên quan và UI52 trên bản snapshot trong integration tree; typecheck/lint/build/Ruff/diff-check. Ghi chính xác counts, không lấy log từ tree nguồn thay kiểm tree mới.
- [ ] Khi HTTP GREEN, chạy runner foreground có thời hạn qua công cụ shell cho phép giữ tiến trình sống trong khi kiểm browser; dùng đúng Trình duyệt tích hợp, công bố nơi thao tác trước lần đầu. Không dùng trình duyệt/surface khác hoặc fake viewport. Kiểm list/detail/approve/reject, double-click, refresh503, sample không gọi API; kèm SQLite assertions.
- [ ] Nếu bề mặt browser không truy cập được, ghi lỗi thực tế và đánh browser UNVERIFIED, giữ bằng chứng HTTP; không sửa chính sách máy để vượt. Bắt buộc cleanup và kiểm cổng đóng/child exits/temp DB xóa an toàn sau mọi run.
- [ ] Báo PASS/FAIL/UNVERIFIED riêng unit, HTTP, browser, Cloudflare/lab; commit cục bộ, đọc lại HEAD/status/diff; không để listener chạy khi bàn giao.

## Nguồn đã được Leader đối chiếu ngày11/11/2026

- [FastAPI cần ASGI server](https://fastapi.tiangolo.com/deployment/manually/): Uvicorn là runtime HTTP phù hợp, không cần cài toàn fastapi[standard].
- [Uvicorn0.54.0 trên PyPI](https://pypi.org/project/uvicorn/0.54.0/): metadata và wheelhash trên được kiểm từ trang phát hành; tương thích dự án phải kiểm bằng runtime thật.
- [MDN Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin): Origin gồm scheme/host/port, browser thường gửi cho same-origin POST. Gateway giữ nguyên; không giả HTTPS.
- [Cloudflare JWT validation](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/): giữ xác minh signature/issuer/audience, fixture không chứng minh Cloudflare SSO thật.

Leader đã self-review kế hoạch so với matrix: snapshot, runtime/HTTPS boundary, crypto/role, gateway header, HTTP/audit, browser và cleanup đều có bước kiểm. Ưu tiên một worker thực hiện, không thêm reviewer song song; Leader nghiệm thu kết quả sau.
