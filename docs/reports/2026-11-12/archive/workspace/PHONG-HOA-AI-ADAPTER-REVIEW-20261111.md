# Leader review AI-IMPLEMENT

Base reviewed: `2ac8605e4f96e7b888205a5fe302a840ffca72bc`, tree `cti-platform-ai-llm-adapter`. Verdict: **NEEDS_FIX R1**, không phủ định demo/mock đã chạy.

Leader đọc implementation/CLI/test và artifact C3; tự chạy hai nhóm adapter/CLI: **46 passed**, exit 0, 2.99s. Phạm vi diff 9 file; không thấy store/portal/deploy thay đổi. Model thật vẫn chưa kiểm.

## R1 — sai kiểu language/config thoát khỏi lỗi ổn định

`extractor/phonghoa_extractor/llm_adapter.py`, `_validate_request`: phép membership trong set thực hiện trước kiểm kiểu cho `language` và `config`. Tái hiện độc lập bằng `run_extraction(text='synthetic evil.example', language=[], tlp='TLP:GREEN', config='C3', provider=<ScriptedProvider>)`; thay language bằng `{}`, hoặc giữ language='vi' và config bằng `[]`/`{}`, đều nhận **TypeError**, provider.calls=0. Các giá trị None/bool/int đã đi AdapterError.

Bằng chứng máy đọc: `ai-adapter-evidence/leader-validation.json`. Mỗi trường được thử list/dict/None/bool/int. Phép kiểm CLI JSON lồng sâu trong cùng artifact đã trả lỗi ổn định và giữ nguyên output; **không có finding cho ca đó**, không cần mở rộng sửa parser.

Yêu cầu: kiểm string trước membership; toàn bộ input language/config sai kiểu hoặc enum sai phải `AdapterError(code='invalid_input')` trước provider, không TypeError/traceback, không lộ source marker. Viết test đỏ cho list/dict của hai trường trước sửa; giữ ca vi/en/C2/C3 hợp lệ. Không bọc nuốt mọi exception, không thay signature/interface hoặc hợp đồng C2/C3.

## Phạm vi rework

CTI AI Agent Sol medium, tự làm không giao bot khác. Chỉ llm_adapter.py, test liên quan, README/PROGRESS nếu cần mô tả; báo/evidence cùng đường dẫn đã giao. Không sửa RUNS/tree khác, không model/network/secret/SQLite, không push/PR/merge/deploy. Local commit được phép. Chạy regression mới rồi hai nhóm adapter/CLI, Ruff và diff check; không cần chạy lại toàn suite 282 chỉ vì thay kiểm kiểu nếu không có sửa khác. Báo RED/GREEN, SHA/diff/count/exit. Sau đó Leader nghiệm thu rồi chọn bước nối evaluator; không tự mở rộng task.

## R1 đã nghiệm thu ngày 11/11/2026 khoảng 01:10

SHA `ed24bd817de1e4633693d27f47e8e5fc629451ad`, diff 2 file +47/-3, tree sạch. Leader đọc diff và tự chạy 12 regression sai kiểu/enum của language/config, exit 0; đủ đóng R1. Adapter fake offline ACCEPTED, không nâng thành chất lượng model thật. Chi tiết `PHONG-HOA-LEADER-REVIEW-20261111-0110.md`. Bước nghiên cứu kế tiếp nối evaluator tách khỏi code đã nghiệm thu.
