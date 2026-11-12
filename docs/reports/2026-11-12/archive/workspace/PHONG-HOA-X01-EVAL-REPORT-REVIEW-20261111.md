# X01-EVAL-REPORT — review độc lập

Ngày 11/11/2026, 10:59 ICT. **NEEDS_REWORK R1**, chưa nghiệm thu implementation.

- Request đã trả: `77d490c0-c54a-4c03-9849-a9e2e7e1ec57`; AI thread `c77b8100-4b1c-405c-ba90-7ef4affc48f1`.
- Target `cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`, HEAD `b765b8602785cee98b697f4c6319c7f17447741c`.
- Base/source `cti-x01-ttp-eval` tại `984bd2136872f4c5fba4118e33cf02b5ca615f2d`. Diff đúng bốn file, +1298/-0. Hai tree sạch trước/sau review, không sửa source.
- Đã đọc reporter, tests, kế hoạch Leader, research contract, báo cáo, log kiểm cuối và demo. Manifest worker 10/10 mục khớp; SHA-256 manifest `27247A7BB20ADD38BB907548B53514769AA0AFD0C3E41CB258BB44CAEAA4CD84`.
- Fresh Leader: reporter suite 38/38 PASS, exit 0; diff-check không có lỗi. 64 evaluator regression là bằng chứng worker, Leader không chạy lại vì producer không đổi.

## R1 — số đếm TTP chấp nhận bool/float (P2)

Vị trí `extractor/eval/report.py:461`: `_validate_ttp_top()` so counts trực tiếp với số thống kê bằng `==`; chưa xác thực từng số bằng kiểm kiểu integer. Python coi `True == 1 == 1.0`, `False == 0 == 0.0`, cả trong dict. `_walk_bounds()` cho phép bool và float 0..1 nên không chặn trường hợp này.

Tái hiện từ artifact C2 schema 1.1 hợp lệ, chỉ đổi một trong chín count sang bool/float bằng giá trị cũ: CLI exit 0, stderr rỗng, Markdown in `True`/`False` hoặc `1.0`/`0.0`. Input invalid vẫn tạo parent/output mới; khi có `--overwrite`, nó thay output cũ. Vi phạm hợp đồng strict JSON count integer và validation trước publish. Đây không phải lỗi no-clobber; nguyên nhân là validation count thiếu kiểm kiểu.

Probe độc lập: `leader-x01-eval-report-evidence/test_r1_ttp_counts.py`, SHA-256 `62C8FA1205A908103ED5A572E0C086B08A8CD5549E956E346CC7034395E2D8E7`.

Lệnh từ root với interpreter tuyệt đối `cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest leader-x01-eval-report-evidence/test_r1_ttp_counts.py -q -p no:cacheprovider --tb=short --junitxml=leader-x01-eval-report-evidence/r1-red.xml`: **18 failed / 2 passed, exit 1**. Log `leader-x01-eval-report-evidence/r1-red.log`. Hai positive control dùng nguyên input C2/C3 của worker và giữ input bytes.

## Phạm vi sửa và acceptance

Một worker CTI AI Agent / Sol medium, tiếp tục đúng target/branch trên. Không giao bot/helper khác. Chỉ sửa `extractor/eval/report.py`, `extractor/tests/test_eval_report.py`; README/PROGRESS chỉ cập nhật khi cần mô tả kết quả. Không đổi producer/evaluator, adapter/catalog, dependency/lock, input/demo cũ hoặc probe/review/RUNS của Leader.

1. Validate exact keys cho cả hai count map; gọi kiểm integer nghiêm ngặt (không bool/float/coerce) cho `technique_items` và toàn bộ quote/catalog count, bounds hiện có, rồi mới đối chiếu thống kê document. Không chỉ format/cast thành int, không tự sửa input.
2. RED→GREEN regression trong repo cho cả bool và float trên các count; chứng minh invalid trả exit 2/stderr cố định/stdout rỗng, input bất biến, không tạo parent mới/không thay output cũ ngay cả `--overwrite`. Giữ positive C2/C3 schema 1.1.
3. Chạy nguyên probe Leader (hash không đổi), reporter suite, Ruff check/format trên file đổi, diff-check; chỉ lặp evaluator regression nếu producer hoặc contract liên quan thay đổi. Không chạy full suite/browser/model/lab vì không cần cho R1.
4. Commit cục bộ sau self-review; giữ tree/branch. Cập nhật báo cáo `PHONG-HOA-X01-EVAL-REPORT-RESULT.md`, evidence mới dưới `x01-eval-report-evidence/rework-r1/` có lệnh, exit, count, RED/GREEN, SHA/manifest, sạch target/source. Bảo toàn evidence cũ. Không push/PR/merge/deploy, network/model/DB/lab.

Root tuyệt đối: `$WORKSPACE`.

Đã xem cuộc mở một lần đầu lượt: chỉ Leader hiện tại đang xử lý, không có Leader trùng; AI thread idle. Automation tự tiếp tục còn enabled, mục tiêu dự án vẫn active nên giữ lịch. Không coi lịch/receipt là bằng chứng worker đang chạy. Model/corpus thật, TTP semantics, C4/RAG, OpenCTI/lab/production chưa kiểm chứng.
