# W05 Selection — nghiên cứu tái sử dụng và brief tích hợp cục bộ

Ngày 11/11/2026. Task mới `W05-SELECTION-INTEGRATION`. CTI Engineer / Sol medium, một worker, không giao tiếp agent khác. Phạm vi đã được ủy quyền: tiếp tục triển khai cục bộ trước lab; không phát hành.

## Mục tiêu và lựa chọn

Kiểm luồng người duyệt bỏ chọn IOC → lưu → duyệt đúng snapshot qua trình duyệt, API thật và SQLite tổng hợp. Kết quả phải chứng minh dữ liệu/audit đúng, không chỉ UI hiện thông báo.

| Cách | Quyết định |
|---|---|
| Mở rộng harness loopback đã nghiệm thu | **Chọn**: tái dùng auth fixture, ownership/cleanup, HTTP matrix và UI/API cùng một base; chỉ bổ sung v1 và selection scenarios. |
| Thêm proxy/auth fixture vào ứng dụng Next | Không chọn: tăng bề mặt test-only trong sản phẩm, chưa cần thiết cho mục tiêu này. |

Tái sử dụng `PHONG-HOA-LOCAL-INTEGRATION-RESEARCH.md`, `PHONG-HOA-LOCAL-INTEGRATION-IMPLEMENTATION-BRIEF.md`, `PHONG-HOA-LOCAL-INTEGRATION-RESULT.md` và ADR `docs/adr/20261111-w05-local-harness.md`. Những mô tả thiếu Uvicorn, ghép UI commits và chỉ có API legacy trong nghiên cứu cũ đã lỗi thời; không làm lại chúng. Base mới đã chứa API v1, UI selection, Uvicorn lock và các sửa lỗi harness R1–R4.

Nguồn chính đọc lại ngày 11/11: [MDN Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin) xác định scheme/host/port và Origin do browser quản lý; tiếp tục forward nguyên Origin, không giả header. [Node HTTP](https://nodejs.org/api/http.html#messagerawheaders) mô tả raw headers giữ các header lặp; giữ tests Set-Cookie/hop-by-hop hiện có. Không nâng Node theo trang tài liệu hiện hành; dùng runtime/lock của dự án. Đây là cơ sở thiết kế, chưa phải bằng chứng tích hợp mới chạy.

## Ref, tree và phạm vi

- Root tuyệt đối: `$WORKSPACE`.
- Source đọc: `<root>\cti-w05-selection-ui`, HEAD `43737c000561c4d676705dbb564223a7bfa3596e`, sạch. UI subtree `dffcc2fa8f11a24ea34f5fe4c71e995bd68549f2`.
- Tạo worktree mới `<root>\cti-w05-selection-integration`, branch `feat/w05-selection-integration-20261111`, từ exact HEAD trên. Đường dẫn chưa tồn tại tại lúc Leader kiểm. Nếu xuất hiện trước khi tạo, kiểm ownership/HEAD, không xóa/ghi đè.
- Không cherry-pick/merge, không sửa source UI hoặc các tree đã nghiệm thu.
- Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-duyet.md`, `docs/specs/W05-draft-offline-contract.md`, ADR selection `0014`, `0015` và báo cáo UI acceptance trước code.
- Được sửa: `tools/local_integration/gateway.mjs`, `runner.py` nếu cần fixture/scenario; tests cùng thư mục (thêm matrix v1 riêng), `docs/adr/20261111-w05-local-harness.md`, `docs/PROGRESS.md`, `portal_api/README.md` phần hướng dẫn harness.
- UI `portal/web/**`, `portal_api` implementation/settings/auth, core/extractor, dependency/lock, deploy và dữ liệu thật giữ nguyên. Nếu integration bộc lộ lỗi ngoài phạm vi, lưu reproduction và báo Leader; không tự vá bằng cách nới policy.
- Cài dependency đã khóa vào môi trường/tree mới nếu cần; không thay lock hoặc cài global. `requirements-api.lock` đã có Uvicorn. Dùng môi trường phù hợp có FastAPI/Uvicorn; venv `cti-platform-start` chỉ đủ guard, không dùng làm bằng chứng API runtime.

## Khoảng trống được Leader quan sát trên source

1. `gateway.mjs` chỉ allowlist `/api/drafts`, `/{id}`, `/{id}/decision`; mọi `/api/v1/...` bị 404 tại gateway.
2. Gateway mặc định giới hạn body 8192 byte; API v1 nhận tối đa 65536 byte. Không để gateway vô tình chặn request v1 hợp lệ trong khoảng này.
3. Runner tạo bốn draft với một IOC/draft. Cần fixture có ít nhất hai IOC eligible để bỏ một nhưng vẫn approve được; schema v2 có sẵn qua `store.save_draft`/migration hiện hành, không viết migration mới.
4. Fault `post-ok-refresh-503` áp dụng sau bất kỳ POST thành công. Cần kiểm độc lập save thành công và decision thành công, tránh một lần save làm không còn đường thử decision trong cùng scenario.

## Hành vi cần triển khai

- Allowlist chính xác legacy và bốn đường v1: GET list/detail; POST `/{id}/selection`, POST `/{id}/decision`. Không mở proxy tùy ý cho `/api/*`; không dùng URL client làm upstream. Method/lỗi vẫn do API contract quyết định; giữ legacy behavior.
- Với v1, cho qua body đến 65536 byte và trả 413/no-store khi vượt; không thay đổi legacy/body cap ngoài mục tiêu. Kiểm biên bằng request JSON hợp lệ có whitespace padding hoặc fixture phù hợp, không suy diễn từ Content-Length; kiểm chunked nếu cơ chế khác.
- Giữ header/status/Origin, JWT fixture server-side, roles server-side, no-store, timeout/abort, không retry POST, production HTTPS-only. Dữ liệu và RSA/JWKS đều tổng hợp; không ghi private key/token vào file/log/browser.
- Chỉ thêm fixture/scenario cố định khi start. Không thêm URL hay dropdown đổi role/mint token. Fixture selection mới có provenance rõ và chỉ bật cho scenario selection mới; giữ bốn fixture và bảy scenario cũ để HTTP matrix legacy vẫn có ý nghĩa.
- Audit phải chỉ đọc hậu kiểm trong DB do run sở hữu: `payload_json` và `items.keep` bất biến; selection events/snapshot/hash/version đúng; final audit tham chiếu snapshot đã lưu. No-op không tăng event/version; lỗi không tạo event/decision ngoài lần thành công.
- Nếu cần số đếm request phục vụ bằng chứng, chỉ lưu method/path/status/count đã làm sạch; không headers/body/token. Không tạo API điều khiển dành cho browser.

## Kiểm chấp nhận bắt buộc

| Nhóm | Kiểm cần có |
|---|---|
| Routing/header | Bốn đường v1 tới đúng API; legacy vẫn chạy; đường ngoài allowlist 404; query/status/no-store/Origin giữ đúng; body hợp lệ >8192 đến65536 không bị chặn sớm, >65536 trả413. |
| Luồng lưu/duyệt | List/detail; bỏ một trong hai IOC rồi save → version1; no-op không tăng; approve → review version2 và final audit đúng selection version1/hash/indices; payload nguyên trạng. |
| Empty/reject | Lưu empty hợp lệ; approve empty403 không thêm decision; reject có lý do đạt, đúng version/audit. |
| Policy/error | Missing/expired/wrong-signature JWT401; role IT403; self-approve403; Origin thiếu/sai403; stale/repeated version409; invalid body/index/extra identity422 và content type415; không có write ngoài lần được chấp nhận. |
| Refresh fault | Save200→GET503 và decision200→GET503 ở hai run riêng: UI giữ xác nhận, snapshot không lùi, không gửi lại POST khi tải lại trạng thái. |
| Browser thật | Trình duyệt tích hợp mở `/duyet`, xem đúng dữ liệu; bỏ chọn/lưu/duyệt; run riêng empty/reject; dirty khóa điều hướng; `/duyet/mau` có nhãn mẫu, không gọi API/POST; chụp/ghi lại trạng thái then chốt và đối chiếu DB. |
| Cleanup | R1 malformed target, R2 timeout/abort, R3 cleanup retry, R4 single-use không regression; mỗi run đóng đúng owned processes/ports/temp, kể cả lỗi. |

Bằng chứng browser phải đến từ bề mặt Trình duyệt tích hợp đã cấp; thông báo nơi làm trước thao tác. Không dùng trình duyệt riêng của người dùng, shell-launched browser hoặc giả viewport. Dùng viewport thực được cấp; nếu truy cập/resize không được, ghi UNVERIFIED đúng phần, vẫn hoàn thành HTTP và cleanup. Không coi HTTPX/Vitest là browser E2E.

## Thứ tự và kiểm tra

1. Xác minh source/tree/branch; tạo tree mới sạch. Viết RED routing/body v1 và HTTP selection trước khi sửa harness.
2. Sửa tối thiểu, chạy targeted gateway/runner/settings và matrix v1. Chạy matrix legacy sẵn có (56 checks/7 scenarios ở mốc trước; báo số thực tế).
3. Kiểm regression API v1/legacy cùng tests harness vì đi qua cùng runtime. Không cần full Python447 hoặc toàn bộ tests UI nếu UI/backend không đổi; giữ bằng chứng trước và giải thích phạm vi.
4. Build UI tại tree mới từ exact source sau cài bằng lock; xác nhận subtree UI vẫn đúng. Chỉ chạy browser sau HTTP xanh. Không phục vụ build cũ từ tree khác.
5. Lưu log stdout/stderr, fresh exit, JUnit/count của tests, HTTP matrix từng case; browser steps/screenshots và audit trước/sau đã làm sạch. Dọn đúng tài nguyên sở hữu, chứng minh không còn owned process/listener/temp. Không kill theo tên hoặc xóa folder rộng.
6. Ruff check/format phần Python đổi, gateway tests Node, `git diff --check`; commit cục bộ. Báo HEAD/base/diff/status, hash lock và UI subtree không đổi. Nếu lệnh quá một phút, đặt timeout đủ và giữ lệnh foreground; không lấy launch exit làm kết quả kiểm.

Đầu ra root: `PHONG-HOA-W05-SELECTION-INTEGRATION-RESULT.md` và `w05-selection-integration-evidence/` gồm manifest. Không sửa RUNS, plan/review/probe hay evidence cũ. Báo PASS/UNVERIFIED riêng cho unit, HTTP, browser, cleanup; chưa có Cloudflare/JWKS/HTTPS thật, lab, OpenCTI hay production.

## Giới hạn và học thêm

Không push/PR/merge/deploy, secret, cloud LLM, lab hoặc đổi trust/quyền. Khái niệm: gateway cục bộ chuyển request tới đúng ứng dụng; snapshot là tập IOC đã lưu tại một version; audit ghi ai đã thay đổi/quyết định và dữ liệu tương ứng. Bước này kiểm giao tiếp giữa các phần đã có, không đồng nghĩa OpenCTI đã được nối.
