# W04 — nối giao diện tài sản và kiểm toàn luồng cục bộ

Task `W04-LOCAL-INTEGRATION`, CTI Engineer, một Sol medium trực tiếp, không giao tiếp bot khác. Root: `$WORKSPACE`.

## Đầu vào đã nghiệm thu, không làm lại

- Backend `90b26287eccc416fd7e7e736b0ad37632e0c34b1`, acceptance `leader-w04-backend-acceptance-20261111/ACCEPTANCE.md`.
- Prep `652545688fb5dd7bb4fe974c597fed370e9ad0f0` tại `cti-w04-integration-prep`, có Backend trên. Frontend `fd04f95e5c98e60fb648c5811d7d7c966040db84` tại `cti-w04-assets-frontend`; acceptance chung `leader-w04-inputs-acceptance-20261111/ACCEPTANCE.md`.
- Đọc AGENTS/PROGRESS/spec W04/contract/design đúng ref; tái dùng nghiên cứu/brief W04 hiện có và quy trình browser-integration-acceptance. Không mở lại nghiên cứu kiến trúc, không đổi contract.

## Tree và ghép mã

Tạo `cti-w04-local-integration`, branch `feat/w04-local-integration-20261111`, **base prep `65254568...`**. Nếu đích có sẵn, kiểm owner/dirty/ref, không reset/xóa. Chỉ writer tại tree mới. Không sửa hai source tree.

Ghép ba commit Frontend đã nghiệm thu bằng cherry-pick cục bộ theo thứ tự:

1. `318fa9779de3212ad2bcccf774312de582ec7a13`
2. `be131133da7b63a3054da032ed1ab8a85af48bc6`
3. `fd04f95e5c98e60fb648c5811d7d7c966040db84`

Nếu PROGRESS/README conflict, giữ thông tin cả hai phần đúng mức bằng chứng, không mất các mục đã nghiệm thu. Không merge main/PR, không push/deploy. Không mang sửa đổi chưa commit hoặc tự chọn SHA khác. Sau ghép xác nhận file Backend không đổi so prep, file Frontend khớp accepted trước khi bổ sung wrapper.

## Luồng và phạm vi triển khai

- Thêm `/tai-san` và client wrapper theo mẫu `IocLookupHttpClient`, dùng `AssetsApp` + `createAssetsHttpDataSource`, sourceMode local-api. Giữ `/tai-san/mau` nguồn mẫu. Không redesign/nhúng JWT hay role phía client.
- `/tai-san` CRUD và `/tra-cuu` dùng cùng gateway/API/AssetStore của một LocalRun. UI phản ánh canonical/version đã trả từ API; thay đổi tài sản phải đổi asset-match trong tra cứu cùng DB.
- Tái dùng runner/gateway đã đạt. Chỉ mở rộng local harness nếu cần sanitized trace, snapshot DB trước cleanup và một fault mô phỏng response mutation thất lạc **sau commit** để kiểm unknown outcome. Fault chỉ bật scenario tổng hợp, không endpoint điều khiển công khai, không retry. Chỉ log method/path/status/counter và dữ liệu tổng hợp cần kiểm, tuyệt đối không log JWT/RSA/header danh tính.
- Allowlist thay đổi mới: route `portal/web/app/tai-san/page.tsx`, wrapper `portal/web/components/assets-http-client.tsx`, test wrapper/focused assets nếu cần; `tools/local_integration/` harness/tests/helper evidence cần thiết; README/PROGRESS. Không đổi core/portal_api/schema/validator/auth/dependencies hoặc sửa lại UI/adapter đã đạt. Nếu phát hiện lỗi ở phần đã đạt, trả repro rõ để Leader giao đúng owner.

## Kiểm cần thiết

1. Sau ghép: targeted assets UI/HTTP + W02 parser/view bị ảnh hưởng, typecheck/lint/build để chứng minh route mới. Tái dùng dependencies hiện có; Next/Turbopack không chấp nhận junction ngoài workspace, có thể copy local dependency như Frontend đã làm, không cài mới/sửa source. Không lặp full Backend55/99 hoặc full portal chỉ vì có sẵn.
2. Chạy ma trận HTTP W04 trên tree kết hợp đúng module target một lần; test harness bị đổi nếu có. Kiểm cùng DB, quyền và cleanup giữ đúng; không cần chạy lại mọi suite prep nếu không đổi chúng.
3. Browser bằng **bề mặt OpenMausBot được cấp**, không Playwright tự mở browser, shell browser hay desktop người dùng. Leader hiện thấy nhóm browser `agent_browser_open/snapshot/...` khả dụng; worker tự discover trong lượt của mình. Nếu không có bề mặt đó, hoàn tất mã/HTTP/build, chuẩn bị lệnh/helper bounded start/status/stop + báo chính xác phần browser chưa kiểm để Leader chạy tiếp; không coi thiếu browser là hoàn tất W04 hoặc cần lab.
4. Các run browser cần bằng chứng:
   - **CRUD + lookup cùng DB:** thêm domain và CIDR, sửa note/version, xác nhận xóa đúng đối tượng; domain/subdomain hoặc IP hiển thị asset-match; URL có path chưa có threat vẫn giữ nhãn tài sản; sau xóa lookup không còn match. Dùng dữ liệu tổng hợp `.example`/fixture, không gọi mạng IOC.
   - **Quyền:** màn403 của leader, không thành công mutation và DB/audit không tăng. HTTP401/role khác đã có matrix, không cần lặp tất cả trên browser.
   - **Đã lưu, refresh503→200:** mutation đúng1 lần, thấy thông báo đã lưu/chưa tải lại, bấm GET retry, thấy bản đã lưu; trace và DB/audit xác nhận không replay. Không chấp nhận chỉ503 lặp mãi.
   - **Unknown outcome:** mutation đã commit nhưng gateway không trả thành công; UI báo chưa rõ kết quả, không tự mutation lại; GET đối soát200 hiển thị bản đã ghi, DB/audit đúng1 lần. Giữ timeout/fault hữu hạn và cleanup sau run.
5. Ghi viewport thật; kiểm desktop, thêm360px nếu bề mặt resize hỗ trợ. Không giả mobile bằng CSS. Screenshot chứng minh trạng thái nhìn thấy, trace/counter thực chứng minh request, DB snapshot chứng minh lưu. Ghi step ID khi công cụ trả Recorded as step. Không suy từ screenshot sang count hoặc từ API tests sang browser.
6. Cleanup trong cả success/error: chỉ PID/listener/temp root thuộc run, kiểm đóng port và giữ snapshot trước khi xóa. Không để service tự chạy vô hạn; mỗi run bounded theo LocalRun. Không đọc secret hoặc kill process khác.

## Bàn giao

Commit cục bộ/tree sạch; báo prep base, ba source frontend commits, integration HEAD, conflict/delta thật và allowlist. Root `PHONG-HOA-W04-LOCAL-INTEGRATION-RESULT.md`, evidence root `w04-local-integration-evidence/`: raw logs/JUnit/build, browser step/ảnh, sanitized traces, DB/audit before-after, cleanup, manifest SHA256 và lệnh tái chạy đúng cwd/interpreter. Nếu worker không có browser, trả ready-to-run helper cùng phần còn lại rõ ràng để Leader hoàn tất, không tự gắn PASS browser.

Không push/PR/merge/deploy, lab/OpenCTI/Cloudflare thật/cloud/LLM/secret. W04 chỉ được nghiệm thu toàn luồng sau browser cùng DB và recovery thực đạt; trước đó chỉ báo mức code/HTTP/component đã kiểm.
