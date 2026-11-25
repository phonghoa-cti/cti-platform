# W03-S1 — phục hồi bổ sung bằng chứng, chặng A
Ngày 12/11/2026; Leader chỉ điều phối và đọc, chưa sửa source và chưa nghiệm thu toàn bộ.

## Mục tiêu và giới hạn lượt
Một CTI Engineer, GPT-5.6 Sol medium trực tiếp, không worker con, giữ thread b05471df-3a0c-49c0-b02b-4019e1cf15d4.
Chốt phần mã/kiểm hợp đồng/tài liệu đang dở và trả commit + báo cáo ngay. Lượt này KHÔNG mở browser mới; ca unknown cùng trang là chặng B sau khi Leader nhận chặng A. Đây là chia nhỏ công việc để tránh lặp lượt hết 15 phút, không bỏ tiêu chí E2.

TREE=$WORKSPACE\cti-w03-status-integration
HEAD quan sát=a2c4ffa245297a8714b0023bf4e4bb248869dc36
Branch=feat/w03-status-integration-20261112
Giữ nguyên sáu tệp chưa commit: portal/web/tests/cve-status-wire-capture.test.ts; tools/local_integration/runner.py; tools/local_integration/tests/capture_w03_status_wire.py; tools/local_integration/tests/test_runner.py; tools/local_integration/tests/test_w04_browser_helper.py; tools/local_integration/w04_browser_helper.py.
Không reset, không cherry-pick lại, không sửa tree khác/RUNS.

## Tài liệu và nghiên cứu kế thừa
Đọc AGENTS, docs/PROGRESS, docs/specs/W03-status-local-contract.md trong TREE.
Brief gốc=$THREADS\484d57b0-1cb9-4264-b24a-54cecff6e454\PHONG-HOA-W03-STATUS-INTEGRATION-BRIEF-20261112.md
Rework E1/E2/E3=$THREADS\7720a19d-5db9-427d-9e14-e5ce81e15744\PHONG-HOA-W03-STATUS-INTEGRATION-REVIEW-20261112.md
Nghiên cứu S1=$WORKSPACE\PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md
Dùng lại contract đã chốt và nguồn SQLite/RFC/OWASP; không nghiên cứu hay thiết kế lại.

## Trạng thái đã quan sát
- Thread idle; báo cáo EVIDENCE-REWORK-RESULT chưa có ở nơi yêu cầu. Đọc trạng thái assignment cũ bị từ chối vì khác requester, nên Leader không kết luận request đã cancelled/failed.
- EVIDENCE_OLD=$THREADS\7720a19d-5db9-427d-9e14-e5ce81e15744\w03-status-evidence-rework
- wire-capture.log ghi 9 fixture PASS/exit0; wire-parser.log ghi 6 pass/exit0. Log thiếu file/JSON lỗi đều exit1. Đây là log đã đọc, chưa phải Leader tái chạy/nghiệm thu.
- browser-known có hai ảnh temporary-error/recovered-same-page, trace PUT200 rồi GET503,503,200, db-summary 1 status/1 audit. Không chạy lại mặc định.
- session known run_id 7fbd1465149a445da582c0e762a181d9 ghi stopped. Leader kiểm trực tiếp PID26176 không còn, port59272 không listen, temp-root w05-local-v8891g1q đã mất.
- Chưa có browser-unknown mới, chưa có manifest/report cuối, docs vẫn ghi chưa ghép UI.

## Việc cần chốt trong chặng A
1. Giữ capture/API thật và các gate đã có. Nhãn "every text boundary" hiện quá rộng: product được thử128 còn request256; toàn bộ giá trị mới là ASCII. Bổ sung Unicode hợp lệ có ý nghĩa (ví dụ tiếng Việt) trong response thực và kiểm production parser, không viết tay envelope để giả capture.
2. Ghi rõ giới hạn product: portal_api/cves.py:_product dùng128 trong dataset, cves_status.py:_validate_context dùng256; chưa tự kết luận lỗi product. Trả repro nhỏ qua loader/API cho product256 và phân biệt boundary đạt128 với256 chưa đạt/không biểu diễn được. Không đổi product source/contract/giới hạn để lách kiểm, không ghi E1 đạt toàn bộ.
3. Review lỗi startup mới trong helper: finally dùng biến running nhưng chỉ gán sau with run và snapshot_assets_database; nếu enter/snapshot ném lỗi có thể che lỗi gốc bằng UnboundLocalError. Tái hiện bằng focused test fault injection trước sửa, sửa nhỏ trong helper được phép; chứng minh cleanup và lỗi gốc còn nguyên. Không mở browser để kiểm này.
4. Chạy focused tests tương ứng thay đổi runner/helper và wire; Ruff/format/diff. Không lặp toàn bộ HTTP matrix, build hoặc 58 component test nếu product/build không đổi. Ghi lệnh đầy đủ, cwd, interpreter tuyệt đối, exit/count.
5. E3: thêm lệnh capture/wire/env đầy đủ README; sửa phần tiến độ/giới hạn của docs/PROGRESS và docs/specs/W03-status-local-contract.md trung thực: đã có bằng chứng browser cũ, known mới, unknown reentry mới chưa kiểm. Không đổi nội dung contract.
6. Commit local phần code/docs đã kiểm, HEAD sạch. Lưu manifest SHA256 và report cho phần đã làm; E2 unknown ghi PENDING và chỉ rõ một lượt browser tiếp theo cần thực hiện. Đừng treo chờ hoặc mở rộng lượt để hoàn tất E2.

## Đầu ra mới
OUT=$THREADS\662556d5-bef1-4bf9-b1f8-ce0ad295308c
Report=OUT\PHONG-HOA-W03-STATUS-EVIDENCE-STAGE-A-RESULT.md
Evidence=OUT\w03-status-evidence-stage-a\
Không ghi đè evidence/report cũ. Có thể tham chiếu/copy artifact cũ với hash và nguồn; phân biệt kiểm mới với tái dùng. Ghi SHA/diff/status/command/output/giới hạn và bước B.
Nếu có blocker, vẫn trả báo cáo phần hoàn tất cùng nguyên nhân, người giải và điều kiện mở. Tối đa hai lần cùng nguyên nhân; không gọi worker khác.

## Phạm vi
Giữ allowlist E1/E3 của rework, thêm duy nhất báo cáo/evidence ở OUT này. Không product Backend/Frontend, S2, deps/lockfile/auth, push/PR/merge/deploy, cloud/LLM/feed thật, lab, secret, chi tiền hay đổi quyền.
Việc nhiều file trong scope đã được giao; không hỏi duyệt lại. Leader nhận chặng A rồi giao chặng B unknown browser và nghiệm thu đúng phạm vi; chưa gọi W03-S1 hoàn tất.
