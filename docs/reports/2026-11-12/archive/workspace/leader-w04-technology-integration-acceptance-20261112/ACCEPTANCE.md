# Nghiệm thu W04 Technology Integration — 12/11/2026

**PASS luồng Công nghệ cục bộ, gồm bằng chứng browser desktop đã đối chiếu.** Không phải toàn bộ W04 hoặc toàn dự án hoàn tất.

## Ref và phạm vi

- Request: 54e7bae2-b6c9-4aab-b84f-79735b5f2078.
- HEAD được kiểm mới và tree sạch trước/sau: **273196e2d23b36172d57cc61b289522786d61b2a** tại cti-w04-technology-integration.
- Base Backend f4c19d44a33fe588046e0e974af9c18cbf8a1a12.
- Frontend accepted2419b296→cfb612f0 được cherry-pick thành0e1e898de29faaedb6deb2a25119545b7912cc64→d5bb1b46e8893cdfbce0dd9f500620ca34fc42b9.
- Integrationf016d6cae6c81424ae6b46618624e1f8a418ccf5, evidence273196e2.
- Delta integration71file +2116/-24, gồm12file code/docs/test và59file evidence. Không nhầm71file này là71file code.
- Leader kiểm diff và git diff --exit-code: portal_api/core khớp Backend; data/panel/assets-app/route mẫu Frontend khớp input đã đạt. Wiring mới chỉ wrapper/gateway/runner/helper/tests/docs/evidence.

## Kiểm Leader chạy mới

1. Ma trận HTTP qua gateway đúng HEAD: **51/51 assertion, exit0**. CRUD/duplicate/stale, quyền, cùngDB, không biến technology thành asset-match, timestamp hỏng503 không ghi,1000/1001, hai recovery scenario. Raw http-fresh.log, http-assertions-fresh.json, http-db/.
2. Node test chọn theo delta: **1/1 pass,exit0**, exact routes/traversal cases và stream response hơn1MiB. Raw gateway-targeted-fresh.log. Không coi test này là chứng minh mọi dạng URL bất thường.
3. Manifest evidence worker: **58/58 hash khớp**; SHA256 manifest802c7f7726a2890152044246ac17806b0290d0c7a1643af73e068c60dd814beb. Validator thử dữ liệu bị thêm byte trong bộ nhớ và từ chối đúng; không sửa artifact gốc.
4. Bốn SQLite snapshot mở read-only, so row/active/audit/actions với trace/schema. Raw returned-evidence-verified.json và verify_returned_evidence.py.
5. Đọc trực tiếp sáu ảnh desktop1280×720: createv1, sau xóa,403, notice sau GET lỗi lần2, committed đã phục hồi, unknown đã đối soát.

Lệnh fresh HTTP, cwd cti-w04-technology-integration:
`../cti-x01-ingest-browser-prep/.venv/Scripts/python.exe -X utf8 -B -m tools.local_integration.tests.run_w04_technology_matrix --output ../leader-w04-technology-integration-acceptance-20261112/http-assertions-fresh.json --evidence-dir ../leader-w04-technology-integration-acceptance-20261112/http-db`.
Gateway:
`node --test --test-name-pattern='gateway proxies exact technology routes' tools/local_integration/tests/test_gateway.mjs`.

## Đối chiếu browser, trace và lưu trữ

| Luồng | Bằng chứng kiểm | Kết luận |
|---|---|---|
| CRUD/duplicate/stale | POST201, PUT200, POST409, setupPUT200, PUT409, DELETE204;1row xóa mềm,0active,4audit; ảnh tạo/xóa | Không ghi khi duplicate/stale; version theo chuỗi v1→v2→setupv3→deletev4 |
| Leader403 | GET403; ảnh thông báo thiếu quyền;0row/0audit | Không ghi DB |
| Committed recovery | POST201 đúng1lần; GET503,503,200; ảnh notice vẫn còn sau lỗi lần2 và danh sách Exchange2019 sau phục hồi;1row/1audit | Không replay, trạng thái đã lưu được giữ |
| Unknown recovery | POST503 đúng1lần; GET assets khi đổi tab; GET technology503,200; ảnh kết quả Cisco/IOS XE17.9;1row/1audit | Commit có thật, đối soát thành công và không ghi lại |

Cả bốn DB đều assets0/asset_audit0. Trạng thái helper ghi stopped và hai cờ port đóng/temp xóa đều true. Đây là đối chiếu record cleanup đã trả; không tuyên bố Leader đã tự chạy lại bốn browser run hay kiểm lại các port cũ không được lưu trong state. Fresh HTTP chạy trong LocalRun và kết thúc exit0.

Bằng chứng browser do Engineer chạy bằng bề mặt OpenMausBot được cấp; Leader kiểm manifest/trace/DB/screenshot/observations, không thao tác browser lại. Ảnh unknown chỉ ghi trạng thái đã phục hồi; trạng thái khóa trung gian được ghi trong browser observations và đã có component regression độc lập trước đó. Không suy request count từ ảnh. Công cụ không trả Recorded as step nên không có stepID.

## Evidence kế thừa và giới hạn

Worker gateway14, runner/helper42, frontend120, typecheck/lint/build9trang/Ruff/format/diff0 được giữ với rawlogs/manifest; Leader không chạy lại các suite này toàn bộ. Hai input vẫn theo acceptance trước, không nghiệm thu lại.

Mobile360px, Cloudflare/JWKS/HTTPS thật, OpenCTI/NVD/feed/LLM, lab và production UNVERIFIED. W04 còn brand/keyword, CSV và phần mở rộng theo spec; không ghi hoàn tất W04. W03 khớp tên sản phẩm chỉ là liên quan, chưa đối chiếu phiên bản hoặc dữ liệu CVE thật.

Hai automation Phong Hỏa đã kiểm lúc00:45 và vẫn bật vì dự án active. Không dừng lịch hoặc đụng lịch email.

## Nối việc

Chọn nghiên cứu bounded W03 theo spec W03-lo-hong-anh-huong.md và api-portal.md. Dependency technology đã đạt; chưa có triển khai W03/GET cves trong baseline và không tìm được brief W03 riêng đã làm khi tìm hồ sơ hiện có. Giao CTI Research phần reuse/contract/giới hạn trước khi quyết định triển khai, không tự mở live OpenCTI hoặc status mutation.
