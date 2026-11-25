# W03-S1 Frontend — kiểm độc lập bản sửa F5/F6

Task: W03-STATUS-FRONTEND-QA. Người nhận: CTI QA Security, Sol medium trực tiếp, không giao bot/worker con.

## Mục tiêu và phạm vi

Kiểm candidate Frontend sau rework2, trước tích hợp: chấp nhận snapshot công nghệ đổi hoa/thường đúng hợp đồng và giải khóa pending khi mutation cũ kết thúc sau close/reopen hoặc A→B→A, không phát lại PUT. Leader đã đọc delta nhưng chưa chạy kiểm lại trong lượt này; không coi báo cáo worker là nghiệm thu. Đây là review mã/test cục bộ, không browser/lab.

ROOT = $WORKSPACE
OUT = $THREADS/cf98b168-ecfc-4799-bd0f-0a78c1ed38ff
TARGET = ROOT/cti-w03-status-frontend (chỉ đọc)
HEAD yêu cầu: 2448b8600f9eff2c3e42b6742e220b46980f4ff4
Delta từ: 13b8025274a70ec88dc21dd9ca7f51c68961e881
Base chức năng: 7ff6eb3af21d8de65836bfbf707396ae5690de0b
Bốn file delta: portal/web/components/cve-status-panel.tsx; portal/web/data/cve-status-http.ts; portal/web/tests/cve-status-panel.test.tsx; portal/web/tests/cve-status.test.ts.

Đọc AGENTS.md và docs/PROGRESS.md trên TARGET; hợp đồng nguồn ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md, ROOT/PHONG-HOA-W03-STATUS-FRONTEND-REWORK2-BRIEF-20261112.md và ROOT/leader-w03-status-review-20261112/RECHECK.md. Tái sử dụng nghiên cứu ROOT/PHONG-HOA-W03-STATUS-RESEARCH-20261112.md và quyết định F5/F6 đã chốt; không điều tra lại accepted Backend 4f7100cf.
Báo cáo ứng viên: ROOT/PHONG-HOA-W03-STATUS-FRONTEND-REWORK2-RESULT.md; evidence ROOT/w03-status-frontend-rework2-evidence/. Kiểm hash so với ROOT/leader-w03-status-review-20261112/recheck-manifest.json.

## Kiểm cần làm

1. Xác nhận HEAD/status đầu-cuối, delta đúng bốn file, không sửa target/Backend/Engineer. Nếu HEAD khác thì báo blocker, không checkout/reset.
2. Chạy nguyên 3 probe F5/F6 và 7 probe cũ, lưu stdout/stderr/command/exit/count mới dưới OUT/w03-status-frontend-qa-evidence/. Probe/config/setup/wire phải giữ nguyên:
   - cwd ROOT/leader-w03-status-review-20261112: node_modules/.bin/vitest.cmd run --config vitest.recheck.config.ts --reporter=verbose
   - cùng cwd: node_modules/.bin/vitest.cmd run --config vitest.config.ts --reporter=verbose
   Hai lệnh tuần tự, không ghi đè log/evidence RED/GREEN cũ.
3. Review delta và coverage liên quan: same IDs nhưng snapshot không đổi version/dataset phải reject display/software drift; wrong relation IDs reject; version/dataset khác cho snapshot cũ; review_required iff version/dataset khác. Bối cảnh API thực casefold-api-wire.json là valid control.
4. Review registry subscriber đúng provider+relation: close/reopen conflict và known failure, A→B→A, callback khi đang B hoặc provider khác không làm sai màn hình; conflict GET lại context + nhập lại; pending/unknown chống double-submit, không tự replay PUT. Bổ sung probe độc lập nhỏ chỉ khi còn lỗ hổng bằng chứng; ghi trong OUT, import target bằng đường dẫn tuyệt đối. Không chạy lại full suite/typecheck/build đã có nếu không có nghi vấn cụ thể.
5. Báo PASS/FAIL/UNVERIFIED theo phạm vi. Nếu lỗi, đưa tái hiện tối thiểu, expected/actual và vị trí nguồn; không tự sửa mã. Không mở rộng thành audit toàn repo.

## Đầu ra và giới hạn

Chỉ ghi:
- OUT/PHONG-HOA-W03-STATUS-FRONTEND-QA-RESULT.md
- OUT/w03-status-frontend-qa-evidence/**

Báo cáo cần SHA/base/diff, hash probe trước/sau, lệnh/exit/count, bằng chứng source không đổi, findings và giới hạn. Không commit/push/PR/merge/deploy, browser, cloud/LLM thật, secret, lab hoặc truy cập dữ liệu thật. Engineer đang làm cti-w03-status-integration; không đọc/sửa tree đó. Không sửa RUNS hay báo cáo cũ. Nếu cùng một lỗi môi trường xảy ra tối đa hai lần, dừng cách đó và báo blocker cụ thể.

Leader sẽ đọc kết quả và nghiệm thu; chỉ ghép UI sau khi Frontend và HTTP prep đều đạt. Giữ nguyên hai request hiện có của Frontend và Engineer, không giao lại triển khai.
