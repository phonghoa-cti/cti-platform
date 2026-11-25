# W04-TECHNOLOGY-INTEGRATION — nối và kiểm toàn luồng cục bộ

CTI Engineer, **một Sol medium trực tiếp**, không worker con/không giao bot khác. Root:
`$WORKSPACE`.
Mục tiêu: tab Công nghệ thật tại /tai-san dùng API/gateway/SQLite cục bộ, CRUD/quyền/phục hồi có trace và audit chứng minh. Chưa W03/feed/production.

## Đầu vào đã được Leader nghiệm thu

- Backend tree cti-w04-technology-backend HEAD **f4c19d44a33fe588046e0e974af9c18cbf8a1a12**.
- Frontend tree cti-w04-technology-frontend HEAD **cfb612f05f6ae57952362580e35ad59d2aff0a3f**.
- Base chung8a767314b654d39c1ddc2995b7919c44a5b7027a là domain/CIDR integration đã đạt; không làm lại.
- Đọc leader-w04-technology-acceptance-20261111/ACCEPTANCE-20261112.md, PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md và nghiên cứu Technology hiện có. Đây là nối phương án đã chốt; không mở nghiên cứu kiến trúc lại.
- Đọc AGENTS/PROGRESS/spec/design đúng ref. Người dùng đã cho phép triển khai cục bộ liên tục; không hỏi lại cho lựa chọn kỹ thuật đảo ngược trong brief.

## Tree và ghép mã

Tạo **cti-w04-technology-integration**, branch **feat/w04-technology-integration-20261112**, base Backendf4c19d44. Nếu có sẵn phải kiểm owner/ref/dirty, không reset/xóa.
Chỉ tree này có writer. Hai source tree và cti-w04-local-integration không được sửa.
Cherry-pick cục bộ lần lượt Frontend:
1. 2419b29656092edcf2bb20b0d7c62a12fa0774c0
2. cfb612f05f6ae57952362580e35ad59d2aff0a3f

PROGRESS conflict: giữ cả nội dung đúng bằng chứng. Không merge branch/main/PR; không đổi SHA nguồn hoặc mang uncommitted edits. Xác minh Backend giống input, Frontend giống input ngay sau ghép trước thêm wiring.

## Phạm vi thay đổi mới

1. portal/web/components/assets-http-client.tsx: tạo Technology HTTP provider ổn định theo lifetime wrapper, inject vào AssetsApp sourceMode local-api. /tai-san/mau tiếp tục mẫu, /tai-san không gắn fixture. Không redesign, không sửa panel/provider đã đạt.
2. tools/local_integration/: runner tạo/inject TechnologyStore opt-in cho các scenario technology tổng hợp, **cùng db_path với AssetStore**. Tạo schema trong setup, không trong request. Tái dùng role/JWT tổng hợp và lifecycle cleanup.
3. gateway.mjs: thêm allowlist chính xác cho /api/assets/technologies và /api/assets/technologies/{positive-id}; giữ route cũ, giới hạn body, Origin, header/danh tính do server quản lý. Không mở proxy /api/* tổng quát. Forward response lớn hợp lệ, không vô tình cap1MiB. Test path gần đúng/traversal không vượt boundary.
4. Thêm/mở rộng fixture, HTTP matrix, helper bounded browser và tests trong tools/local_integration; snapshot cả technology_assets/audit và assets/audit. Chỉ fault tổng hợp trong scenario: refresh GET503 hai lần rồi200; mutation được upstream commit nhưng trả lỗi gateway bất định, GET đối soát503 rồi200. Không endpoint điều khiển công khai, không lưu JWT/key/header.
5. Cho phép wrapper test, harness/gateway tests, README/PROGRESS và report. Không sửa portal_api/core/schema/auth/settings/dependencies/lock, các component/adapter đã đạt, source trees hoặc RUNS. Nếu thấy lỗi thật ngoài phạm vi, trả repro cụ thể để Leader giao đúng owner; không tự nới phạm vi.

## Kiểm cần thiết

- RED→GREEN cho wiring mới/gateway/runner faults; test cần thiết cho file đổi. Frontend focused technology+assets+wrapper một lần trên HEAD cuối, typecheck/lint/build; Python/Node harness tests bị ảnh hưởng, Ruff/format/diff. Không full portal/core/Backend hoặc lặp toàn bộ lịch sử.
- HTTP thật qua gateway, JWT synthetic: CRUD chuẩn vendor/product/software_version/version; duplicate409, stale409, soft-delete/recreate; IT/analyst/multi-role được, leader403, thiếu token401; quyền không tin claim client. Validate sameDB; technology CRUD không thay assets/audit và không tạo W02 asset_match. Giữ một smoke domain/CIDR+lookup trên gateway đã đổi. B1 row timestamp hỏng503 và không ghi qua gateway.
- Danh sách1000 hợp lệ qua gateway đủ nội dung/schema; dùng fixture Leader hoặc tạo qua store trong DB tạm, không trộn vào dữ liệu browser thường. 1001 vẫn từ chối, không truncate. Không cần browser render1000 record.
- Browser thật bằng **bề mặt OpenMausBot được cấp**, không shell-launched/Playwright/providerbrowser thay thế. Đọc browser-integration-acceptance và dùng helper đã có. Nếu bề mặt không khả dụng, hoàn tất mã/HTTP/build rồi bàn giao helper hữu hạn và phần browser còn thiếu; không tự nhận đã đạt toàn luồng.

Các browser case tối thiểu:
1. CRUD trên /tai-san tab Công nghệ: tạo, sửa note/softwareVersion và version tăng, duplicate/stale hiển thị đúng, xác nhận xóa; screenshot + trace + snapshot/audit cùngDB.
2. Leader403, UI không báo lưu thành công, DB/audit không đổi (HTTP matrix chứng minh số ghi).
3. Committed refresh: một mutation thành công → GET503 → bấm tải lại GET503 vẫn giữ “đã lưu” → GET200 thấy dữ liệu, mutation count vẫn1.
4. Unknown outcome: upstream đã commit1lần nhưng gateway trả lỗi bất định → UI chưa rõ/khóa; đổi tab rồi quay lại và GET503 vẫn khóa; GET đối soát200 mở khóa/hiện record; mutation count1, audit1. Kiểm không có JWT/secret trong evidence.
5. Pending qua đổi tab đã có component test; chạy lại focused đó trên tree ghép, browser chỉ cần thêm nếu helper hỗ trợ bounded delay dễ kiểm. Không mở rộng harness lớn chỉ để tạo thêm ca giống nhau.

Browser dùng viewport thật; desktop,360px nếu bề mặt có resize. Nếu thiếu resize thì mobile UNVERIFIED, không giả bằng CSS. Khi có Recorded as step, ghi step IDs. Không suy số request từ ảnh; trace chứng minh request, DB/audit chứng minh commit. Cả thành công/lỗi phải dọn đúng temp/PID/port của run và kiểm lại; giữ snapshots trước cleanup. Không đợi/poll worker hoặc chờ trạng thái trong vòng lặp shell; helper process chỉ chạy hữu hạn theo quy trình đã đạt.

## Bàn giao

Commit cục bộ sạch, exact base/source/cherry-pick/finalSHA, conflict/diff/allowlist, test command/cwd/interpreter/exit/count; giữ riêng original source changes và integration delta. Root report **PHONG-HOA-W04-TECHNOLOGY-INTEGRATION-RESULT.md**, evidence **w04-technology-integration-evidence/**: raw logs, HTTP assertions, browser steps/ảnh, sanitized traces, DB before-after/audit, cleanup, SHA256 manifest, lệnh tái chạy.

Không push/PR/merge/deploy, lab/Cloudflare/JWKS/HTTPS thật/OpenCTI/NVD/LLM/cloud/secret. Không nâng cấp thư viện. Kết quả tự về Leader; không sửa sổ/giao việc thêm.
