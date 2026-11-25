# W03-STATUS-INTEGRATION-PREP — sửa R1 phạm vi fault

ROOT=$WORKSPACE
OUT=$THREADS/cf98b168-ecfc-4799-bd0f-0a78c1ed38ff
Một CTI Engineer Sol medium trực tiếp; không worker/bot con. Tiếp tục cùng thread b05471df-3a0c-49c0-b02b-4019e1cf15d4, tree ROOT/cti-w03-status-integration, branch feat/w03-status-integration-20261112, candidate sạch32b5c068c4d6da5a0abb00906c619f92f13b9177. Giữ edits nếu có, không reset. Đây là rework prep, chưa ghép Frontend/browser.

Đọc OUT/leader-w03-status-inputs-review/ACCEPTANCE.md, brief gốc ROOT/PHONG-HOA-W03-STATUS-INTEGRATION-PREP-BRIEF-20261112.md, AGENTS/PROGRESS trên target. Tái dùng nghiên cứu/hợp đồng S1 đã chốt, không nghiên cứu lại.
Frontend2448b860 đã accepted cục bộ nhưng chỉ được cherry-pick sau Leader nghiệm thu prep mới. Backend4f7100cf accepted giữ nguyên.

## Lỗi đã tái hiện

Gateway dùng statusGetFailuresRemaining chung cho mọi status/history. SauPUT A, GET B hoặc GET A/status-history tiêu thụ lỗi của A. Hai probe tại OUT/leader-w03-status-inputs-review/fault-scope-probe.mjs đềuFAIL, exit1; log fault-scope-red.log. Upstream trong probe là tổng hợp để cô lập gateway.

## Sửa và kiểm cần đạt

- Ràng buộc fault GET vào exact pathname /status của mutation tương ứng; history và relation khác không tiêu thụ hoặc nhận fault. Không đổi endpoint contract, quyền, bodycaps hoặc JWT.
- Giữ knownPUT200 rồi A GET503→503→200; unknownPUT503 sau upstreamcommit rồi A GET503→200; đúng1PUT/1status/1audit mỗi scenario. Nếu nhiều relation được ghi xen kẽ, bộ đếm không được chuyển nhầm relation.
- Chạy nguyên2probe Leader ở OUT, lưu GREEN mới vào evidence bên dưới; không sửa probe/logRED. Thêm regression nhỏ trong gateway test và caseHTTP thực có GET relationB/history xen giữa PUTA và GETA để chứng minh fault scope cùngSQL, không chỉstub.
- Chạy targeted node gateway tests, HTTP matrix W03 status cập nhật và Ruff/format/diff-check. Không lặp backend98/W03-R120/W0451/fullfrontend/build khi không sửa phạm vi đó; nếu một thay đổi buộc kiểm thêm thì ghi lý do.
- Trace sanitized, SQL snapshots/cleanup ports/process/temp như brief gốc. Giữ evidence144assertion cũ; ghi kết quả mới riêng. Nếu error cùng nguyên nhân hai lần, đổi cách hoặc trả blocker cụ thể.

## Phạm vi và đầu ra

Cho phép sửa tools/local_integration/gateway.mjs, tests liên quan và README/docsPROGRESS/contract phần giải thích tích hợp trong allowlist gốc. Không portal_api/core/auth/frontend/dependency/RUNS, không browser/lab/cloudsecret/push/PR/merge/deploy.

Output:
- OUT/PHONG-HOA-W03-STATUS-INTEGRATION-PREP-REWORK-RESULT.md
- OUT/w03-status-integration-prep-rework-evidence/**

Báo finalSHA/delta/cleanstatus, command/exit/count, probehash không đổi, manifest/trace/SQL/cleanup. Không ghi đè report cũ. Leader kiểm delta R1 rồi mới nối UI/browser cùngtree/thread.
