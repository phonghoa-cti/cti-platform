# W03-READ-INTEGRATION — kết quả tích hợp cục bộ

## Kết luận

**PASS cục bộ** tại `93962d9ec771c49855c213e6332be0632e33debd` trên nhánh `feat/w03-read-integration-20261112`.

- Base Backend: `abcd14dacca361791b17719632d2ce38557d6baf`.
- Cherry-pick UI: `d7ded2a1fdcfed75c4fa7d32312d17dca4e7ca42` (nguồn `5c968c74...`) và `c4a274ab1b7324e096c54417c9db7e92c9bebc08` (nguồn `f650f04d...`).
- Commit tích hợp: `93962d9ec771c49855c213e6332be0632e33debd`.
- Delta so với base: 27 file, `+2541/-16`; đúng phạm vi W03 frontend đã nghiệm thu, `tools/local_integration/**`, kiểm wire mới và tài liệu W03.
- Worktree tích hợp và hai source worktree sạch; không push, PR, merge, deploy, lab, feed hay đọc secret.

## Kiểm chứng đã chạy

| Lớp | Lệnh/kiểm | Kết quả |
|---|---|---|
| HTTP + SQL | `python -m tools.local_integration.tests.run_w03_matrix --evidence ...` | exit 0; **103/103** kiểm, 8 scenario, PASS |
| Gateway | `node --test tools/local_integration/tests/test_gateway.mjs` | exit 0; **15/15** PASS |
| Python tích hợp | `pytest` cho runner, browser helper và backend CVE | exit 0; **112/112** PASS |
| Frontend trọng tâm | `vitest` cho CVE app, HTTP và wire | exit 0; **58/58** PASS |
| W04 smoke | `python -m tools.local_integration.tests.run_w04_technology_matrix` | exit 0; **51/51** PASS |
| Backend W03 trọng tâm | pytest CVE backend | exit 0; **59/59** PASS |
| Static/build | TypeScript, ESLint, Next production build | cả ba exit 0; build có 10 route, gồm `/lo-hong` và `/lo-hong/mau` |
| Python hygiene | Ruff check + format check | exit 0 |

Không lặp toàn suite Backend 66 và Frontend 54 đã được Leader nghiệm thu; chỉ chạy các kiểm tích hợp và hồi quy có liên quan.

## Ma trận HTTP, quyền và wire

- Detail `200`: IT, analyst, admin và multi-role; Leader nhận `view=summary` và UI không có combobox công nghệ/nút detail.
- Quyền: thiếu token `401`, role không hợp lệ `403`; tham số sai `422`; asset không tồn tại `404`; dịch vụ không sẵn sàng `503`.
- Bộ lọc exact/casefold, sắp hạng, phân trang 16 CVE, `0` khác `null`, hiển thị version và giới hạn response đều qua parser frontend thật.
- Payload lớn: `1,027,338` byte, 6 candidate; payload vượt trần trả `503`.
- Cursor cũ sau một W04 PUT có kiểm soát trả `409`; tải lại từ đầu trả `200` và snapshot mới.
- Gateway chỉ nối GET chính xác `/api/cves`; near-route và phương thức thay đổi không được nhận là W03.
- GET lỗi/đúng không bị tự phát lại phương thức ghi; lượt `503` chỉ retry GET rồi `200`.

Nguồn máy đọc được: `w03-integration-evidence/http-matrix.json`, `w03-integration-evidence/http/` và kiểm wire `portal/web/tests/cves-wire-integration.test.ts`.

## Bất biến SQLite

- Ma trận tự động chụp schema, `user_version`, số dòng từng bảng và SHA-256 toàn bộ row trước/sau mỗi GET `200/404/409/503`; tất cả giữ nguyên.
- DB không tồn tại không bị GET tạo mới.
- Chỉ W04 PUT có kiểm soát thay đổi DB: `technology_asset_audit` từ 2 lên 3, `technology_assets` vẫn 2, schema SHA-256 và `user_version=2` không đổi.
- Browser Leader và recovery: DB summary trước/sau giống hệt; snapshot browser chỉ tăng đúng một technology audit do PUT có chủ ý.

## Browser desktop trên SHA cuối

Viewport quan sát: **1280×720, DPR 1**.

| Scenario | Trace quan sát | DB | Ảnh |
|---|---|---|---|
| Detail + snapshot | CVE GET `200`; W04 PUT `200`; next GET `409`; tải lại GET `200` | audit 2→3, các count khác giữ nguyên | `final-browser-snapshot/01..04` |
| Leader summary | một CVE GET `200`; không gọi Technology API | hoàn toàn bất biến | `final-browser-leader/01-summary.png` |
| Recovery | CVE GET `503→200`; không có W03 mutation | hoàn toàn bất biến | `final-browser-recovery/01..02` |

Mỗi lượt có `gateway-trace.jsonl`, SQLite ban đầu/trước cleanup, DB summary, metadata gắn SHA và state `stopped`; cả ba xác nhận port đóng và thư mục tạm đã xóa. Các thư mục `browser-*` cũ là thăm dò trước commit và **không** được dùng làm bằng chứng nghiệm thu; chỉ `final-browser-*` được tính.

## Chưa xác minh

- **UNVERIFIED:** viewport mobile thật 360 px vì công cụ Browser tab không cung cấp resize viewport; không tự suy diễn từ CSS.
- **UNVERIFIED:** Cloudflare/JWKS/HTTPS, lab/VM, OpenCTI, feed CISA/live, production và độ chính xác dữ liệu thực tế/version-range.
- Fixture là dữ liệu tổng hợp cục bộ có provenance trong `tools/local_integration/fixtures/README.md`; không phải bằng chứng chất lượng feed thật.

## Hoàn tác

Trên nhánh này, hoàn tác riêng phần tích hợp bằng `git revert 93962d9ec771c49855c213e6332be0632e33debd`; không dùng reset phá hủy lịch sử. Hai cherry-pick UI vẫn tách commit để truy vết.
