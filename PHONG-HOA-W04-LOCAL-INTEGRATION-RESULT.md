# W04 local integration — kết quả

Ngày kiểm: 11/11/2026. Phạm vi: tích hợp cục bộ, dữ liệu tổng hợp, không gọi Internet.

## Kết quả

- Tree: `cti-w04-local-integration`; branch `feat/w04-local-integration-20261111`.
- Base prep: `652545688fb5dd7bb4fe974c597fed370e9ad0f0`.
- Frontend nguồn đã nghiệm thu: `318fa9779de3212ad2bcccf774312de582ec7a13`, `be131133da7b63a3054da032ed1ab8a85af48bc6`, `fd04f95e5c98e60fb648c5811d7d7c966040db84`; cherry-pick cục bộ tương ứng `3299b35`, `f317876`, `1aeedc4`.
- Commit tích hợp: `59d679e0949fea5ece953645cd6b80303546b43a`; 12 file, `+388/-4`.
- `portal/web` tại `1aeedc4` khớp cây Frontend `fd04f95`; `core`, `portal_api` và `tools/local_integration` không đổi qua ba cherry-pick so với prep. Không có conflict được ghi nhận.
- `/tai-san` dùng `AssetsApp` + `createAssetsHttpDataSource`; `/tai-san/mau` giữ nguồn mẫu. CRUD tài sản và `/tra-cuu` dùng chung SQLite/AssetStore trong một `LocalRun`.

## Kiểm tự động mới

Chạy từ root tree, Python dùng `..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe`:

| Kiểm tra | Kết quả |
|---|---|
| Vitest assets + W02 bị ảnh hưởng | exit 0; 5 file, 150 test PASS |
| `npm run typecheck` | exit 0 |
| `npm run lint` | exit 0 |
| `npm run build` | exit 0; có route `/tai-san`, `/tai-san/mau`, `/tra-cuu` |
| Gateway Node | exit 0; 13/13 PASS |
| Runner + browser helper pytest | exit 0; 34/34 PASS |
| Ruff phạm vi thay đổi | exit 0 |
| W04 HTTP matrix | exit 0; 71 assertion PASS |

Ma trận HTTP xác nhận cùng DB, role `200/403/401`, cleanup, refresh `POST x1; GET 503→200`, unknown outcome `POST x1; GET 200`, mỗi fault có đúng một asset và một audit.

## Browser desktop 1280 × 720

- CRUD + lookup: thêm `company.example` và `8.8.8.0/24`; lookup domain/subdomain, IP và URL-path hiện asset-match; sửa note làm version `v1→v2`; xóa đúng domain và lookup sau xóa không còn match. Snapshot trước cleanup: 2 asset row, 1 active, 4 audit.
- Quyền: GET và POST `/api/assets` đều 403; màn hình báo không có quyền; snapshot DB trước cleanup là 0 asset, 0 audit.
- Refresh sau commit: UI báo đã lưu nhưng chưa tải danh sách; bấm `Tải lại danh sách` hiện bản ghi. Trace đúng `POST 201 x1`, `GET 503`, `GET 200`; DB 1 asset, 1 audit.
- Unknown outcome: UI báo chưa rõ kết quả và không tự gửi lại; bấm `Tải lại danh sách` hiện bản đã commit. Trace đúng `POST 503 x1`, sau đó `GET 200`; DB 1 asset, 1 audit.
- Sáu run browser/helper đều kết thúc `status=stopped`, `gateway_port_closed=true`, `temp_root_removed=true`. Trace chỉ có counter/method/path/status; không có JWT/header danh tính.
- Browser không trả Recorded step ID. Bề mặt được cấp không có lệnh đổi viewport, vì vậy viewport thật 360 px là **UNVERIFIED**.

## Bằng chứng

Thư mục: `..\w04-local-integration-evidence\`.

- Exit/log mới: `recovery-frontend-exits.json`, `recovery-backend-exits.json`, `recovery-*.log`, `recovery-harness-pytest.xml`, `recovery-w04-http-matrix.json`.
- Browser: các thư mục `browser-w04-*` chứa screenshot, `gateway-trace.jsonl`, `db-summary.json`, SQLite backup trước cleanup; state JSON ở root evidence chứng minh cleanup.
- `manifest-sha256.txt` chứa SHA-256 của toàn bộ artifact, trừ chính manifest.

## Giới hạn và hoàn tác

- Chỉ chứng minh loopback cục bộ với JWT/RSA, SQLite và fixture tổng hợp. Cloudflare/JWKS/HTTPS thật, OpenCTI, lab, feed/LLM, mobile 360 px và production chưa kiểm.
- Không push, PR, merge, deploy, đọc secret hoặc gọi mạng IOC.
- Hoàn tác phần tích hợp bằng `git revert 59d679e0949fea5ece953645cd6b80303546b43a`; ba cherry-pick Frontend là đầu vào riêng, không nằm trong revert này.

## Học thêm

- Unknown outcome là trường hợp server có thể đã ghi nhưng client không nhận được kết quả; cách an toàn là GET đối soát, không tự lặp POST.
- Optimistic version dùng số phiên bản để ngăn một bản sửa cũ ghi đè bản mới.
- Snapshot SQLite trước cleanup giữ bằng chứng dữ liệu nhất quán dù thư mục chạy tạm được xóa sau đó.
