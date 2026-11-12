# X01-TTP-EVAL — nghiệm thu độc lập Leader

Ngày 11/11/2026. Request `123d6606-dcaf-4a2c-895e-9a2a397e1e51`, thread `88b7253f-7a26-4d13-9f40-f239be63fa7e`.

**PASS cục bộ/offline**, không finding sản phẩm còn mở trong phạm vi review. Không phải nghiệm thu toàn X01 hoặc dự án.

## Ref/phạm vi

- Target `$WORKSPACE\cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`, HEAD `984bd2136872f4c5fba4118e33cf02b5ca615f2d`.
- Base/source readonly `b896ad343a2e9876559649b1182c0a4feeecaaa5` tại `cti-x01-ttp-audit`.
- Đã đọc diff implementation/test/docs: đúng 5 file, +687/-15; source và target status sạch.
- Research/brief và đính chính bảy field theo `PHONG-HOA-X01-TTP-EVAL-LEADER-PLAN.md` được áp dụng.

## Bằng chứng Leader chạy mới

Cwd target, interpreter `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`:
- `-X utf8 -B -m pytest extractor/tests/test_eval_cli.py -q -p no:cacheprovider`: 64 test đạt, exit 0 (log quiet in 64 dấu PASS, không phải chạy lại full295).
- `-X utf8 -B -m pytest ../leader-x01-ttp-eval-review/test_leader_eval.py -o addopts='' -q -p no:cacheprovider`: **13 passed in 0.83s**, exit 0.
- Ruff check/format hai Python đổi, git diff --check base..HEAD: exit 0; 2 file đúng format.
- Manifest worker **21/21 hash khớp**; manifest SHA-256 `D5C7F75EF988F429D9CF88B8F66CA00DCD5E68D10C81993B122644E1AD19D759`.
- Đối chiếu compatibility artifacts C2/C3 đúng base/target Git refs: chỉ bỏ evaluator.git_ref, mọi phần khác bằng nhau.
- Không chạy lại full295/official suite/UI/build không liên quan. Worker full295 có raw log đã đọc; không nhận đó là lệnh Leader đã chạy.
- RED worker hiện lưu bản tóm tắt red.md; không tái hiện RED trên base và không gọi đó là fresh proof của Leader.

Probes bổ sung kiểm public catalog/adapter/audit/evaluator: actual provider.calls trên normal/retry/fallback là 1/2/2 cả C2/C3 bật/tắt; sau bỏ đúng audit fields/schema/limitation mới thì toàn artifact bằng nhau. Counts active/inactive/unknown/not_checked và matched/missing/not_found/ambiguous có keyset/zero rõ; trạng thái không phát ra từ public adapter vẫn giữ zero. Fault injection source hash và malformed mixed semantic list đi qua audit thật, trả exit1/generic error, giữ output cũ. Pin invalid UTF-8, nested duplicate, 1500-level nesting, 5000-digit integer và ±Infinity bị từ chối.

Lần probe đầu có 2 fail/11 pass do **fixture của Leader** đưa empty evidence và invalid technique ID vào public adapter vốn không cho phép. Đã sửa fixture thành payload hợp lệ, thêm spy xác nhận các ca fault thực sự đi qua audit; 13/13 đạt. Không có sửa source sản phẩm, không báo lỗi fixture này là bug/rework của worker.

## Artifact kiểm

- `leader-x01-ttp-eval-review/fresh-eval-tests.log`: SHA256 `CD6AEFE5277A860E9E16F076B14BC359F9C18088B4ADFD23D6C67308FA782C0A`.
- `leader-x01-ttp-eval-review/fresh-probes-corrected.log`: `D1A7A99044B096535D8BEFDC414F3408F1ADEBA4D2F5989426AACF722F79CD77`.
- `leader-x01-ttp-eval-review/test_leader_eval.py`: `E606D7016DC2FA57A6153D54C5AF82B72C94CB85406B17CE88C8AC87FA870759`.
- Quality command output lưu `leader-x01-ttp-eval-review/fresh-quality.log`.
- Report worker `PHONG-HOA-X01-TTP-EVAL-RESULT.md`.

## Giới hạn/nối việc

Semantic truth TTP, model thật, corpus hai người gán nhãn, C4/RAG, W05/OpenCTI/lab/production vẫn UNVERIFIED. Cờ audit thể hiện consistency/provenance, không nâng quyền technique và không đo chất lượng TTP.

Đã xem threads một lần: chỉ Leader cuộc hiện tại đang xử lý; AI/Research idle. Lịch đọc lúc 10:13 ICT enabled, kỳ kế 10:26; giữ. Không push/PR/merge/deploy.

Đặc tả `docs/specs/X01-ai-extractor.md` đã yêu cầu `extractor/eval/report.py` dựng bảng chương 4; tree hiện chưa có file này. Tìm các tài liệu root và lịch sử với X01 report.py không thấy brief đã làm. Chọn nghiên cứu nhỏ tiếp theo: reporter offline đọc artifact C1/C2/C3/schema1.0–1.1, xuất bảng có provenance và nhãn synthetic rõ; không gọi model/chấm semantic hoặc tạo số liệu thật. Chưa giao code trước nghiên cứu.
