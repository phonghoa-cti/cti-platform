# WORKFLOW-GUARD — kết quả triển khai

Ngày: 10/11/2026. Owner: CTI Engineer. Trạng thái: **PASS cục bộ sau rework R1/R2** trong phạm vi brief.

## Kết quả

Đã tạo bộ kiểm tra CLI chỉ đọc cho `PHONG-HOA-RUNS.json`, dùng Python stdlib và không thêm dependency. Công cụ xác thực schema/ID/phụ thuộc/receipt/blocker/evidence trước khi phân loại quyết định theo thứ tự brief.

Các quyết định được phân biệt và có test chạy CLI thật: `INVALID`, `PAUSED`, `COMPLETE`, `REVIEW`, `REPLAN`, `DISPATCH`, `YIELD`, `BLOCKED`, `PLAN_NEXT`. Rework bổ sung kiểm kiểu trước mọi phép enum membership và chỉ chấp nhận `receipt.observation.status=running` cho task `running`.

Lỗi trọng tâm đã được khóa bằng regression test:

- Project còn `active`, toàn bộ task con `accepted` → `PLAN_NEXT`, exit `1`.
- Project còn `active`, danh sách task rỗng → `PLAN_NEXT`, exit `1`.
- `receipt.outcome=accepted` trên task `dispatched` vẫn → `YIELD`, không biến task thành `accepted`.
- Lab bị blocked nhưng task offline độc lập queued và sẵn sàng → `DISPATCH` task offline.

## File tạo mới và SHA256

| File | Dòng | SHA256 |
|---|---:|---|
| `workflow/check_continuation.py` | 425 | `3b781dd2aca755e129f26440a1253cf0f166280df9e714202f8f13fe4128a4f2` |
| `workflow/test_check_continuation.py` | 379 | `010c186988175246885ebd15e4b9ba42abbb372476b88ade9c01d4faa3eebb1c` |
| `workflow/README.md` | 63 | `7d64fb4a0c4226e725f06fb3e301e7e61449bb692e667753ac7c551a05cb1090` |
| `workflow-evidence/verification.md` | 128 | `ad84a9a374e298ad316b66af03cea128b2b47f55a2fa661b9337bcc30ba5f4a8` |

Đầu ra nằm ngoài repo Git; không có commit/SHA Git và không push/PR/merge/deploy.

## Kiểm chứng đã chạy

1. RED trước production code:

   ```powershell
   cti-platform-start\.venv\Scripts\python.exe -m unittest workflow.test_check_continuation.ContinuationCliTests.test_active_project_with_all_children_accepted_plans_next -v
   ```

   Kết quả: `FAILED (failures=1)`, exit `1`, đúng vì script chưa tồn tại.

2. Python: `Python 3.12.13`, exit `0`.

3. Toàn bộ unittest:

   ```powershell
   cti-platform-start\.venv\Scripts\python.exe -m unittest workflow.test_check_continuation -v
   ```

   Kết quả tươi sau rework: `Ran 32 tests in 5.871s`, `OK`, exit `0`.

4. Ruff:

   ```powershell
   cti-platform-start\.venv\Scripts\python.exe -m ruff check workflow\check_continuation.py workflow\test_check_continuation.py
   cti-platform-start\.venv\Scripts\python.exe -m ruff format --check workflow\check_continuation.py workflow\test_check_continuation.py
   ```

   Kết quả: check exit `0`; format check exit `0`, hai file đã formatted.

5. Demo sổ thật:

   ```powershell
   cti-platform-start\.venv\Scripts\python.exe workflow\check_continuation.py --ledger PHONG-HOA-RUNS.json
   ```

   Kết quả sau rework: `YIELD`, task IDs `WORKFLOW-GUARD`, `W05-IMPLEMENT`, `UI-IMPLEMENT`, `AI-NEXT`, exit `0`. Guard nói rõ đây là dữ liệu receipt/callback trong ledger, không phải live check.

   SHA256 sổ trước và sau đều là `e9198c8009b6f5dee310a1e0aecc8e81c6001f08d93dc3679437495d5a901ee4`; `LEDGER_UNCHANGED=True`.

   Hash đầu vào ở lượt kiểm trước là `bca1f32891303b40e45edb27eb74e558cc3b14a4123d5ac263cec2e8988beb09`, nên sổ đã được cập nhật ngoài guard giữa hai lượt. Trong từng lần chạy, hash trước/sau vẫn giống nhau.

## Tiêu chí brief

| Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|
| CLI stdout JSON UTF-8 gồm decision/task_ids/reasons | PASS | 27 test CLI và demo sổ thật |
| Schema/ID/dependency/receipt/blocker/evidence sai → INVALID exit 2 | PASS | Test JSON hỏng, file thiếu, ID trùng, dependency thiếu/cycle, status/receipt/evidence sai |
| Phân biệt 8 nhánh hành động và COMPLETE | PASS | Test riêng từng nhánh; có cả REPLAN và INVALID |
| Active + all accepted/empty → PLAN_NEXT | PASS | Hai regression test, exit 1 |
| Chọn tối đa một queued task/owner theo priority | PASS | Test `E-HIGH`, `R`; không chọn `E-LOW` |
| Không ghi sổ thật | PASS | SHA256 trước/sau giống nhau |
| Không sửa repo/sổ/config | PASS theo phạm vi file đã tạo | Chỉ tạo 5 đường dẫn được brief cho phép; không chạy lệnh Git hay sửa repo CTI |

## Rework R1/R2

- RED: 5 test mới, 12 failure, exit `1`; tái hiện đúng 8 traceback enum list/dict và 4 observation sai bị nhận là running.
- GREEN đích: 6 test, `OK`, exit `0`, gồm regression running hợp lệ vẫn `YIELD`.
- Enum `project.status`, criterion `state`, task `status`, receipt `outcome` giờ kiểm `str` trước membership; list/dict/null/bool/number đều đi `INVALID`, exit `2`, stdout JSON và không traceback.
- Observation `idle`, `completed`, `failed`, `queued`, chuỗi lạ hoặc sai kiểu đi `INVALID`, exit `2`; chỉ `running` hợp lệ.

## Giới hạn và hoàn tác

- Đây là cổng quy trình Leader chủ động gọi, **không phải Stop hook tự cưỡng chế của OpenMausBot**.
- `YIELD` không chứng minh worker đang sống; `BLOCKED`, `PAUSED`, `YIELD` exit `0` cũng không có nghĩa dự án complete.
- Script không xác minh chất lượng nghiệp vụ của evidence và không tự cập nhật sổ, giao việc, đọc backlog hay lập brief.
- Không chạy lại 236 test CTI vì không đổi mã CTI; trạng thái lab/production vẫn **UNVERIFIED**.
- Hoàn tác: xóa đúng năm đầu ra mới nêu trong báo cáo; sổ và repo sản phẩm không cần phục hồi vì không bị sửa.
