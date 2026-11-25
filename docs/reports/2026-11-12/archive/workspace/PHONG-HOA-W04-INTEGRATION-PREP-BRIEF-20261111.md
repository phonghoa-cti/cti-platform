# W04 — chuẩn bị HTTP/gateway độc lập trong lúc Frontend sửa

Task `W04-INTEGRATION-PREP`, CTI Engineer, một Sol medium trực tiếp, không giao người khác. Đây là chuẩn bị phần chạy API cục bộ đã có hợp đồng, không phải nghiệm thu tích hợp giao diện.

Root: `$WORKSPACE`.

## Nguồn, base và ranh giới độc lập

- Backend đã nghiệm thu `90b26287eccc416fd7e7e736b0ad37632e0c34b1` tại `cti-w04-assets-local`; xem `leader-w04-backend-acceptance-20261111/ACCEPTANCE.md`. Không sửa tree đó.
- Tạo tree riêng `cti-w04-integration-prep`, branch `feat/w04-integration-prep-20261111`, **từ đúng Backend SHA trên**. Nếu đích có sẵn thì kiểm owner/dirty/ref và báo, không reset/xóa. Frontend đang sửa tree khác từ `be131133`; không đọc file đang sửa để lấy mã, không cherry-pick Frontend chưa nghiệm thu.
- Đọc AGENTS/PROGRESS/spec W04 và contract trên base. Tái dùng `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md`, `PHONG-HOA-W04-IMPLEMENT-BRIEF-20261111.md`, runner/gateway W02 trong base. Không nghiên cứu lại toàn dự án.
- Leader đã đối chiếu: gateway chưa mở `/api/assets`; LocalRun chưa inject asset_store. Cả hai sửa độc lập với UI. Backend schema/logic đã đủ, không cần sửa sản phẩm Backend.

## Đầu ra nhỏ nhất cần có

1. Cho gateway chuyển đúng `/api/assets` và `/api/assets/<positive-id>` tới API, giữ exact route boundary, Origin, body cap 8 KiB, strip JWT do client gửi, no-store/Vary, timeout và lỗi chung; đường API khác vẫn đóng theo rule hiện có. Không thêm retry mutation.
2. Thêm scenario W04 opt-in vào LocalRun: AssetStore khởi tạo trong temp root do run sở hữu, inject cùng instance/path cho CRUD và W02 lookup. Tái dùng lookup fixture tổng hợp đã có, tài sản domain/CIDR synthetic. Scenario cũ không tự mở/bật asset store.
3. Identity vẫn do local runner tạo JWT tổng hợp ở server; IT/analyst/multi-role được đúng quyền, lãnh đạo 403, thiếu token 401. Không ghi token/private key vào stdout/evidence, không dùng secret thật.
4. Ma trận HTTP `start_ui=False` qua gateway thật chứng minh: create/list/update/delete và audit/version trên cùng DB; duplicate/stale version 409; domain/subdomain/CIDR/URL-path asset-match và thay đổi sau delete; forbidden/missing-token/Origin/body-limit trước mutation; JWT client không vượt quyền. Kiểm đầy đủ cùng một run nơi cần so trước/sau, không ghép output của nhiều DB.
5. Chuẩn bị một ca lỗi GET sau mutation đã commit rồi phục hồi 200 trong cùng run. Fault chỉ trên scenario tổng hợp, giới hạn một lần hoặc điều khiển in-process; không mở endpoint điều khiển thiếu bảo vệ. Ghi trace đếm mutation/GET và audit để xác nhận refresh không replay. Không cần dựng UI hoặc browser trong task này.
6. Listener/process/temp root thuộc run được cleanup kể cả lỗi; log PID/port/outcome không secret, xác nhận port đã đóng. Không kill process không thuộc run, không fallback desktop/browser.

## File, kiểm và báo cáo

Allowlist: `tools/local_integration/runner.py`, `gateway.mjs`, module fixture W04 mới, tests dưới `tools/local_integration/tests/`, `tools/local_integration/README.md`, `docs/PROGRESS.md`. Nếu thật sự cần local_settings thì chỉ mở trong cùng local harness, nêu lý do. Không sửa `portal_api`, core, `portal/web`, dependencies, RUNS hoặc source tree khác.

Viết targeted regression trước; chạy tests runner/gateway liên quan một lần, ma trận HTTP mới với exit/count/assertion thực, lint/diff-check. Dùng interpreter đã có `uvicorn`, ưu tiên checkout-local .venv; nếu chưa có, `cti-x01-ingest-browser-prep/.venv/Scripts/python.exe` là nguồn được README W02 chỉ ra, xác minh tồn tại/module target trước dùng; không tự cài hoặc sửa môi trường nguồn. Không chạy lại full Backend/UI, build UI hoặc mở browser cho nhiệm vụ không cần UI này.

Commit cục bộ, tree sạch; trả base/head/delta/lệnh/exit/count/module path/DB and cleanup evidence. Báo cáo **root** `PHONG-HOA-W04-INTEGRATION-PREP-RESULT.md`, evidence root `w04-integration-prep-evidence/`. Không push/PR/merge/deploy/lab/cloud/LLM/feed thật. Bước sau do Leader giao: nối SHA chuẩn bị này với Frontend đã nghiệm thu và kiểm trình duyệt. Không tự tuyên bố W04 hoàn tất.
