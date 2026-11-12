# Chốt triển khai evaluator — 11/11/2026

Áp dụng cùng PHONG-HOA-AI-EVAL-IMPLEMENTATION-BRIEF.md, bản này ưu tiên khi khác. Leader đã đọc hai tài liệu, đối chiếu scorer, adapter và evaluator đúng ed24bd8. Chọn mở rộng eval/run.py, tái dùng scorer/adapter; không thêm thư viện chấm điểm. Tên phương án “C1” trong nghiên cứu chỉ là số thứ tự phương án, không giới hạn cấu hình chạy C1.

## Những chỗ cần chốt trước code

- **Giữ nguyên C1:** không thêm result_mode hoặc đổi shape/hash/điểm của artifact C1; nghiên cứu có câu thêm mode cho C1 trái yêu cầu tương thích. Chỉ artifact C2/C3 mang metadata mới. C4 vẫn không hỗ trợ.
- **Refusal/incomplete/nonretryable AdapterError:** adapter hiện ném lỗi có mã, không tự fallback. Lát cắt evaluator phải dừng toàn run, stderr thông báo ổn định không lộ input, exit 1, không tạo/ghi đè output. Không tự retry hoặc biến thành dự đoán rỗng/điểm 0. Retryable/schema lỗi hai lần đi regex_fallback theo adapter; tách metric nhóm đó khỏi model_completed.
- **C2 fallback:** raw_iocs có thể là regex; chấm nhưng giữ model_items_used=false và result_mode=regex_fallback. C3 gồm model + regex rồi grounding theo adapter hiện tại; mô tả đúng provenance, không tuyên bố chỉ model đạt điểm đó.
- **C2 giá trị IOC không normalize được:** giữ trong tổng dự đoán để scorer hiện có đếm FP, không bỏ silently. by_type dùng loại từ normalize khi được, nếu không thì bucket `invalid`; không tin type do model tự khai. Có regression chứng minh invalid FP không mất giữa tổng và breakdown.
- **Fixture strict:** dùng đúng envelope CLI đã có; type-check language/TLP/provider/response trước membership. Không cho enum list/dict gây traceback. Có thể tách hai parser fixture từ llm/run.py thành helper thuần `extractor/phonghoa_extractor/llm_fixture.py` và cho cả CLI/evaluator dùng; không đổi contract adapter. Đây là phạm vi bổ sung được phép, không cần xin lại. Nếu chọn helper mới, kiểm cả CLI cũ. Không subprocess CLI hoặc import private CLI bằng mẹo path.
- **Hash/determinism:** dataset hash C1 hiện dùng 4-byte độ dài relative path UTF-8, path bytes, rồi file bytes theo thứ tự; không đổi thuật toán cũ. Fixture manifest có thể dùng cùng helper và phải tài liệu hóa framing đúng. Source/fixture hashes từng document, config/TLP, mock_only=true, provider fake_offline/egress=false, schema_version, evaluator ref và Python version có mặt ở C2/C3; không timestamp. Chỉ so byte-identical trong cùng checkout/runtime.
- **Output:** C2/C3 ghi atomic sau khi toàn bộ input hợp lệ và xử lý xong. Không output vào dataset/responses hoặc alias/symlink/hardlink của input; output cũ không đổi khi lỗi. CLI usage sai có thể exit 2 theo argparse; input/fixture/provider refusal sai exit 1, đều khác 0 và không traceback/raw marker.

## Phạm vi, kiểm và bàn giao

Owner AI Agent Sol medium, không giao người khác. Tree cti-platform-ai-llm-adapter đang sạch ed24bd817de1e4633693d27f47e8e5fc629451ad; tạo branch `feat/x01-eval-c2c3-offline-20261111` tại tree này, không merge/cherry-pick. File scope brief + helper/parser/test CLI nếu cần + docs/PROGRESS.md. Không sửa scorer chính sách/adapter orchestration/store/portal.

Dùng interpreter sẵn `../cti-platform-start/.venv/Scripts/python.exe`, không phải .venv trong tree AI (brief ví dụ chưa đúng môi trường). Không cài thêm dependency hoặc đổi venv dùng chung.

TDD các ca mới, chạy evaluator tests, adapter/CLI regressions nếu dùng chung parser thay đổi; Ruff check/format, git diff --check. Full suite chỉ khi thay đổi ngoài evaluator/shared fixture parser tạo rủi ro rộng; không chạy lặp theo thói quen. Demo C1 baseline, C2 và C3 trên 6 mẫu tổng hợp, lặp C2/C3 để kiểm byte-identical; ghi counts/modes/invalid và hash, không kết luận chất lượng LLM. Không mạng/model/secret/SQLite/lab.

Đầu ra ngoài repo tại workspace Leader: `PHONG-HOA-AI-EVAL-RESULT.md`, `ai-eval-evidence/` (logs RED/GREEN, artifact và hashes). Local commit được phép; không push/PR/merge/deploy, không RUNS hoặc sửa hai báo cáo nghiên cứu. Phân biệt kiểm cục bộ với model/corpus thật còn UNVERIFIED.
