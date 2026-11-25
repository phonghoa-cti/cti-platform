# W04 — nghiệm thu Frontend và HTTP prep, 11/11/2026

**PASS hai đầu vào cục bộ, đủ điều kiện giao tích hợp. Chưa nghiệm thu luồng giao diện + API trên trình duyệt.**

| Đầu vào | SHA được chấp nhận | Kiểm Leader mới |
|---|---|---|
| Frontend | `fd04f95e5c98e60fb648c5811d7d7c966040db84` | 6/6 probe độc lập PASS, exit 0, F1–F3 đóng; đúng SHA/tree sạch |
| HTTP/gateway prep | `652545688fb5dd7bb4fe974c597fed370e9ad0f0` | 64/64 assertion HTTP thật PASS, exit 0, cùng DB/role/recovery/cleanup; đúng SHA/tree sạch |

## Frontend

Đọc delta từ `be131133`: 18 file +442/-6, phần sản phẩm chỉ sửa bound created_by, mapping lỗi mutation và context guard sau refresh; còn lại tests/docs/evidence. Backend và W02 không đổi. Leader chạy nguyên `leader-w04-frontend-review-20261111/leader-regressions.test.tsx` qua config hiện hữu, ghi mới tại `frontend-probes.txt/xml`: 6 passed, exit 0. Actor254/512 nhận,513 từ chối; gateway503 POST thành unknown-mutation; refresh cũ sau create/delete không còn ghi notice lên tab mới. Tree sau kiểm sạch, metadata `frontend-verification.json`.

Đã đọc test mở rộng của worker và raw focused53/53, build route `/tai-san/mau`, typecheck/lint được report có exit0. Leader không chạy lại full222 hoặc tự nhận đã chạy build. Component/parser evidence không chứng minh browser hay toàn luồng.

## HTTP/gateway prep

Đọc delta từ Backend accepted `90b26287`: 8 file +469/-7, đúng local harness/tests/docs, không sửa core/API/UI. Kiểm raw_sha256 trong verification worker: 4/4 khớp. Đọc runner/gateway/fixture/matrix; route exact, asset store opt-in dùng cùng file SQLite, fault GET một lần không có endpoint điều khiển.

Leader chạy từ target: `cti-x01-ingest-browser-prep/.venv/Scripts/python.exe -X utf8 -B -m tools.local_integration.tests.run_w04_matrix --output <evidence>/http-matrix.json`, PYTHONPATH target root/core/extractor. Kết quả exit0, 64 assertions, raw `http-matrix.txt/json`, SHA/tree ở `prep-verification.json`.

- Primary: 2 create/1 update/1 delete; còn1 active asset,4 audit; duplicate/stale version409, Origin403 và cap8KiB413 không ghi DB.
- Lookup cùng DB nhận domain/subdomain/CIDR/URL-path asset-match; delete thay kết quả lookup ngay.
- Roles: IT/analyst/multi200, leader403, thiếu token401. Header client được gateway thay bằng principal tổng hợp của run.
- Recovery script:1 mutation,GET503 rồi200, asset/audit1/1; temp roots removed và gateway ports closed. Đây là HTTP script không có browser; số request là chuỗi đã thực thi trong script và DB đối chiếu, chưa phải trace người dùng thao tác UI.
- Worker runner31/gateway12 và lint/format là raw đã đối chiếu, không nhận là Leader vừa chạy lại.

## Quyết định tiếp

Giữ Backend accepted `90b26287`. Chấp nhận `W04-ASSETS-FRONTEND` và `W04-INTEGRATION-PREP`, giao `W04-LOCAL-INTEGRATION` cho một CTI Engineer/Sol medium trên tree mới. Brief `PHONG-HOA-W04-LOCAL-INTEGRATION-BRIEF-20261111.md` chốt cả hai SHA và điều kiện browser/cùng DB/phục hồi/không ghi lặp.

Hai lịch nối việc đã đọc, enabled, dự án active nên giữ nguyên. Không push/PR/merge/deploy. UI/browser W04 tích hợp, viewport360, Cloudflare/JWKS/HTTPS thật, OpenCTI/lab/production còn UNVERIFIED.
