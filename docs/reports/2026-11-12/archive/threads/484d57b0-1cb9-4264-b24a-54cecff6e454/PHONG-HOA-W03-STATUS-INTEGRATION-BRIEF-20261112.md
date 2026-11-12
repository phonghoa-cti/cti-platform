# W03-STATUS-INTEGRATION — ghép UI và kiểm luồng trạng thái

ROOT=`$WORKSPACE`.
OUT=`$THREADS/484d57b0-1cb9-4264-b24a-54cecff6e454`.

Mục tiêu: người dùng mở quan hệ công nghệ/CVE, ghi trạng thái có ghi chú, đọc lịch sử và phục hồi lỗi đọc mà không ghi lặp. Một CTI Engineer Sol medium trực tiếp, không bot/worker con; giữ thread `b05471df-3a0c-49c0-b02b-4019e1cf15d4` và tree `ROOT/cti-w03-status-integration`, branch `feat/w03-status-integration-20261112`. Không sửa tree nguồn hoặc RUNS.

## Đầu vào đã nghiệm thu

- HEAD prep `65e31980ac01910b825951676bae428ca3bf1742`, Backend `4f7100cf83e57b1cb30a12472ed71a0cd985a413` đã nằm trong đó. Xem `OUT/leader-w03-status-prep-acceptance/ACCEPTANCE.md`.
- Frontend `2448b8600f9eff2c3e42b6742e220b46980f4ff4`. Cherry-pick đúng ba commit theo thứ tự: `e31f0b40ac7ed8a8acb31968485c281fc2b3b7b0`, `13b8025274a70ec88dc21dd9ca7f51c68961e881`, `2448b8600f9eff2c3e42b6742e220b46980f4ff4`. Giải xung đột docs/PROGRESS bằng giữ cả hai tiến độ; không bỏ sửa Backend/prep. Đối chiếu source UI với commit accepted sau ghép.
- Đọc AGENTS, PROGRESS, `docs/specs/W03-status-local-contract.md`, README local_integration và `ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md`. Tái dùng nghiên cứu S1 và SQLite/RFC/OWASP đã chốt ở brief đó; không thiết kế lại.
- Giữ edits nếu có; không reset. Nếu HEAD khác input ngoài thay đổi do chính task này, dừng sửa và báo ref/diff. Local integration đã được phép; không hỏi duyệt lại đa file.

## Phạm vi sửa

Chỉ ghép ba commit UI đã accepted; thêm/sửa `tools/local_integration/**`, test fixture/wire `portal/web/tests/*cve-status*`, `portal/web/tests/fixtures/w03-status-*`, docs/PROGRESS và hướng dẫn integration. Không tự sửa product Backend/Frontend ngoài cherry-pick; nếu phát hiện defect trả repro và đề xuất tối thiểu cho Leader. Không deps/lockfile/auth/core/contract change, không W03-S2, redesign, push/PR/merge/deploy/lab/live feed/cloud/LLM/secret.

## Kiểm cần đạt

1. Tạo wire fixture từ API thực của đúng HEAD tích hợp cho unset/committed/review_required/history/conflict/unavailable. Dùng schema reader UI thật kiểm chúng, có giới hạn note/actor/context và history lớn hợp lệ theo contract. Fixture thiếu/hỏng phải fail trước test, không skip/fallback PASS. Đây là kiểm hợp đồng, tách khỏi browser.
2. Dùng helper/harness sẵn; nếu cần mở rộng helper cho scenario S1 thì bounded lifetime, loopback only, port trống và cleanup tài nguyên sở hữu. Chỉ dùng trình duyệt được OpenMausBot cấp, không Playwright/CDP hay shell-launch browser thay thế. Chỉ Engineer dùng browser. Ghi kích thước thật, không giả mobile bằng CSS/zoom; nếu bề mặt không có chức năng cần thì báo giới hạn.
3. Luồng cơ bản trên `/lo-hong`: chọn CVE và technology đúng; chưa có trạng thái; lưu status+note bằng form, thấy status/version/notice đúng; cập nhật lần hai và xem history newest-first. Trace cùng SQLite chứng minh mỗi lần thao tác đúng một PUT và một audit tăng tương ứng. Có ảnh trạng thái trước/sau và lịch sử; không biến status do người nhập thành bằng chứng đã vá thật.
4. Known commit: PUT200 rồi GET503→503→200. Giữ thông báo đã lưu qua lỗi đọc; nút thử lại chỉ GET. Unknown outcome: PUT503 sau upstream commit rồi GET503→200; khóa ghi trước đối soát, không tự khẳng định PUT thành công từ GET. Mỗi scenario đúng một PUT, một status, một audit; ảnh/trace/SQL liên kết cùng lượt. Kiểm đổi A→B→A hoặc đóng/mở panel trong quá trình phục hồi; callback A không sửa B. B/history đọc200 không tiêu thụ fault của A.
5. Conflict/context/history: tạo thay đổi context bằng API W04 trên cùng DB có ghi nhãn setup, quan sát review_required; lần ghi với context cũ409 không thêm audit; reload/xác nhận lại là quyết định mới có note mới. History cursor cũ sau mutation409 rồi bắt đầu lại200, không ghép snapshot cũ. Ưu tiên kiểm qua browser phần hiển thị/reentry; phép tạo race/stale setup có thể dùng harness và phải ghi rõ.
6. Leader-only summary không gọi status/history/technology; sample route không HTTP mutation; smoke W03-R filter còn 3 KEV→16 tất cả→3 KEV. Không lặp toàn ma trận auth/backend/W04 đã nghiệm thu nếu không đổi phạm vi đó.

Focused wire/component tests + typecheck/lint/build sau ghép; test helper/gateway chỉ khi thay helper/gateway, Ruff/format/diff-check tương ứng. Không chạy lại fullsuite lịch sử. Mọi kiểm báo command, cwd, interpreter, exit, count. Tối đa hai lần cùng lỗi rồi trả blocker/repro; không tự sửa vượt allowlist.

## Bàn giao

`OUT/PHONG-HOA-W03-STATUS-INTEGRATION-RESULT.md`, `OUT/w03-status-integration-evidence/**`. Ghi base/finalSHA/cherry-pick mapping/diff/clean status; ảnh + bước browser + request trace đã loại secret + SQL snapshots + manifest + cleanup ports/process/temp. Ghi rõ kiểm mới, kết quả cũ tái dùng và UNVERIFIED. Nếu browser bị chặn vẫn trả code/wire/local tests hoàn chỉnh và blocker cụ thể; không báo toàn luồng PASS. Leader nghiệm thu kết quả rồi chọn bước kế; không worker tự giao tiếp.
