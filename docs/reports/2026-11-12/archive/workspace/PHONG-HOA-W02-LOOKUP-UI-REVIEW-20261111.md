# W02 view — review Leader và rework R1/R2

Ngày 11/11/2026. Target `cti-w02-lookup-ui`, HEAD `d5a3aa4eda20491937da3ab4b4e29198f9563c7c`, base `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`. Leader kiểm HEAD/status, diff 9 file +514, đọc component/source/test và ảnh browser bàn giao. Tree sạch trước/sau probe; không sửa code sản phẩm.

Kết luận: **NEEDS_FIX**, chưa nghiệm thu view. Phạm vi đúng và đã có UI mẫu rõ nhãn; bộ 103 test trong raw log bàn giao không bao phủ hai lỗi dưới đây.

## R1 — dữ liệu mẫu nhận nhầm thuộc tính kế thừa

Mức Important, `portal/web/data/ioc-lookup.ts:59`. `fixtures[value]` trên object thường đọc cả `__proto__`, `constructor`, `toString`, `hasOwnProperty`, `valueOf`. Đây không phải fixture được khai báo nhưng trả object/function thay vì `{state:"not-found"}`; component nhận response sai cấu trúc và không báo không tìm thấy đúng thiết kế. Không gọi đây là khai thác prototype pollution: hiện là lookup sai dữ liệu kế thừa.

Sửa tối thiểu dùng own-key check hoặc Map, giữ exact-match hiện tại và không tự normalize/score. Test cả năm giá trị trên cùng fixture hợp lệ và unmatched thông thường.

## R2 — thông báo sao chép của kết quả cũ xuất hiện ở kết quả mới

Mức Important, `portal/web/components/ioc-lookup.tsx:76–84`. Copy IOC A tạo Promise chờ; người dùng tra B và đã thấy B; Promise của A hoàn thành sau đó ghi success/error lên màn hình B. Thành công hiển thị dưới B mặc dù clipboard đã nhận giá trị A, dễ khiến người dùng dùng nhầm IOC.

Probe tái hiện cả resolve và reject. Ràng buộc completion với kết quả/query và lần copy sở hữu nó; vô hiệu callback khi submit mới/unmount; nhiều lần copy trong cùng kết quả không để completion cũ ghi đè lần mới. Giữ chỉ báo thành công sau resolve và lỗi sạch; không đọc clipboard/fallback/HTTP hoặc ghi log IOC/lỗi thô.

## Bằng chứng độc lập

- `<root>\leader-w02-ui-review\probe.test.tsx`: SHA-256 `ca72dacd31f465b5b03bbd3cdd5711902bc42dcbb3551f592d7a0012998052af`.
- Config ngoài source `<root>\leader-w02-ui-review\vitest.config.mjs`.
- Từ `<root>\cti-w02-lookup-ui\portal\web`: `node node_modules/vitest/vitest.mjs run --config ../../../leader-w02-ui-review/vitest.config.mjs --reporter verbose`.
- Lượt hợp lệ cuối: **7 failed**, exit 1, log `leader-w02-ui-review/probe-red-valid.log`; 5 ca R1, 2 ca R2. Đây là failure đúng assertion sản phẩm.
- `probe-red.log` trước đó có 5 lỗi R1 nhưng 2 lỗi harness vì user-event diễn giải dấu `[` thành phím. Leader đổi input test sang paste rồi chạy lại; không dùng hai lỗi harness đó làm finding.
- Ảnh đã xem: `w02-lookup-ui-evidence/browser-desktop-result.png`. Chưa tự chạy lại browser; mobile, API/auth/TLP/OpenCTI vẫn UNVERIFIED.

## Gói rework cho CTI Frontend

Một worker GPT-5.6 Sol medium, không giao bot khác. Tiếp tục chính target/branch hiện có từ HEAD trên. Tái dùng nghiên cứu/state/clipboard đã có; không thiết kế lại UI hoặc đợi API contract đang được Research sửa.

Cho phép sửa hai file lỗi, `portal/web/tests/ioc-lookup.test.tsx`, `docs/PROGRESS.md` mục W02; cập nhật `PHONG-HOA-W02-LOOKUP-UI-RESULT.md` và `w02-lookup-ui-evidence/rework-r1-r2/`. Không sửa probe/config/log Leader, API, W05, package/lock, RUNS hoặc tree khác.

TDD cho R1/R2, thêm test interleaving copy phù hợp; chạy probe Leader nguyên trạng 7/7, targeted W02, toàn test web, typecheck/lint/build/diff-check sau thay đổi cuối. Chỉ một lần full web cuối, không Python/full backend. Ghi command/raw output/exit/count, hash probe trước-sau, exact commit/diff và source/target clean. Nếu dùng browser thì chỉ trình duyệt tích hợp, port 3012 trống/loopback/cleanup owned; không giả mobile. Không cần mở browser để bấm riêng lỗi Promise nếu probe deterministic đã chứng minh; ghi rõ cấp bằng chứng.

Commit local sau checks; không push/PR/merge/deploy. Tab title W05 là giới hạn metadata nhỏ đã ghi nhận, xử lý ở bước tích hợp được phép, không trộn vào R1/R2. Contract HTTP/8 IOC types sẽ được map ở task nối API, không tự thay contract trong lượt này.

QA importer và Research R1–R4 đang chạy ở các thread riêng đã quan sát; callback Research cũ `869a4c0a...` không thay thế request rework `217d52c9...`. Không giao lại hai việc đó.
