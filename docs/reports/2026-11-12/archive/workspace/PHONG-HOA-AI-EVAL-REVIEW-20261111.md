# AI-EVAL-IMPLEMENT — ACCEPTED cục bộ sau R1

## Kết quả recheck lúc02:03 ngày11/11

Đóng R1 tại `8694fa7244d181f421bb2733ded7bf9ae218ea93`. Leader đọc diff2file (+49/-1): kiểm role là string trước set membership; có ca đúng/sai cho C2/C3. Chạy nhóm role **18 passed, 21 deselected**, exit0; `ai-eval-evidence/leader-r1-green.log`. Đối chiếu artifact C1 baseline và c1-r1 cùng SHA256 `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f`. Tree sạch, diff-check exit0. Đã đọc worker evidence evaluator/C143; không lặp full84. Chấp nhận bộ đánh giá ngoại tuyến trên fixture tổng hợp; không kết luận chất lượng model/corpus thật. Finding/RED dưới đây được giữ làm lịch sử.

Leader kiểm độc lập commit `4b74fbb15bfe02fc499ada3ffe05f5dfa34f9120`, tree `cti-platform-ai-llm-adapter`, nhánh `feat/x01-eval-c2c3-offline-20261111`; tree sạch. Giữ brief và `PHONG-HOA-AI-EVAL-LEADER-ADDENDUM.md`, tái sử dụng nghiên cứu đã nghiệm thu.

## R1 — label role sai kiểu gây traceback (medium)

`extractor/eval/run.py:77`: `_validate_label_item()` kiểm membership trong set trước khi kiểm role là string. `role:[]` hoặc `role:{}` gây `TypeError: unhashable type`, thoát khỏi xử lý DatasetError của CLI C2/C3.

Leader chạy CLI C2 với từng dataset tổng hợp trong thư mục tạm. Cả list và dict đều exit1 nhưng có traceback. Output đã có vẫn được giữ. Bằng chứng: `ai-eval-evidence/leader-input-probe.json`; probe `leader_input_probe.py`. Validator này đã tồn tại, nhưng lỗi vi phạm hợp đồng input không hợp lệ của luồng C2/C3 vừa thêm.

Sửa ở biên validation bằng kiểm kiểu trước membership, trả DatasetError ổn định; không blanket-catch TypeError để che lỗi code. Không đổi metric/scorer/adapter/fallback/valid C1. Thêm regression C2 và C3 với role list, dict, null, boolean, number và enum lạ: exit1 sạch, không traceback/marker dữ liệu, output cũ không đổi. Kiểm role hợp lệ attacker/victim/benign và C1 hiện có không đổi. Nếu sửa helper chung, phải chạy các test C1 liên quan.

## Bằng chứng và yêu cầu bàn giao

- Leader chạy `pytest extractor/tests/test_eval_cli.py extractor/tests/test_llm_cli.py -o addopts= -q`: **30 passed**, exit0.
- Probe sai kiểu: **2 lỗi traceback**. Hai probe JSON lồng sâu (fixture/metadata) đã trả lỗi gọn và giữ output, không phải finding và không yêu cầu sửa.
- Phạm vi rework: `extractor/eval/run.py`, test evaluator liên quan, docs/PROGRESS nếu cần, `PHONG-HOA-AI-EVAL-RESULT.md` và evidence mới. Không sửa scorer, adapter, dependency, ledger/review hay probe/log Leader.
- TDD RED/GREEN, nhóm evaluator/C1 liên quan, Ruff/format/diff-check; không cần lặp toàn84 nếu phần ngoài evaluator không thay đổi. Dùng Python sẵn có ở `cti-platform-start/.venv/Scripts/python.exe` với cwd tree AI; không sửa môi trường chung.
- Commit cục bộ, báo exact SHA/diff/count/exit/tree. Không giao agent khác, gọi mạng/model thật/secret/SQLite/lab hoặc push/PR/merge/deploy.
- Model thật, chất lượng corpus hai người gán nhãn, C4/TTP và production vẫn UNVERIFIED.
