# X01-C4-EVAL — review implementation, yêu cầu R1–R4

Ngày 11/11/2026. Kết luận **NEEDS_REWORK**, chưa nghiệm thu implementation.

Root: `$WORKSPACE`.
Task `X01-C4-EVAL-IMPLEMENT`; request trả về `580e9770-9dfe-4910-855d-facaa119efb7`;
thread `fc56dfb3-fa5c-44ca-992b-8e32451d6d18`.

## Bằng chứng đã kiểm

- Target `root\cti-x01-c4-eval`, branch `feat/x01-c4-eval-20261111`, HEAD `7ece3c3a47541c40e7baa430792d631bc22c623d`.
- Source `root\cti-x01-c4-adapter` sạch tại `654443e6ede6557f0629fc0886ca56fff782b193`; target sạch; diff đúng 9 file, +1269/-33; diff-check exit 0.
- Manifest worker: 18/18 hash khớp. JUnit đã đọc: 291 test, 0 failure/error/skip. Đây là bằng chứng worker; Leader không chạy lại 291 test.
- Leader đối chiếu artifact: C1 byte-identical; C2/C3 bằng nhau sau khi bỏ duy nhất evaluator.git_ref; Markdown cũ byte-identical; hai C4 output cùng hash. Phép đọc C2/C3 đầu dùng encoding mặc định Windows bị lỗi, sau đổi rõ UTF-8 đã chạy exit 0; không tính lỗi thao tác này là lỗi sản phẩm.
- Đọc diff run.py/report.py, research/brief/Leader plan, spec X01, AGENTS.md và test liên quan.
- Probe Leader bên ngoài repo: `root\x01-c4-eval-leader-evidence\test_c4_review_probe.py`.
  SHA-256 cuối: `0041669CDF155CAB72DBC6F2C082F534A9B7ACB20F2ECD86FD303565F5DB5147`.
- Vòng đầu 17 test: **13 failed, 4 passed**, exit 1; `probe-red.log`, `probe-red.xml`.
  Sau đó thêm test preflight empty và chỉ chạy ca mới: **1 failed, 17 deselected**, exit 1; `empty-preflight-red.log`.
  Không báo 18 test chạy chung; hiện có 18 ca để worker chạy sau sửa.
- Hai artifact control hợp lệ và hai ca deep-JSON đã PASS. Tất cả đầu vào tổng hợp, không mạng/model/listener/DB.

## R1 — P1: audit C4 chưa ràng buộc vào document và catalog

`extractor/eval/report.py:551–596`, nhất là dòng 596, chỉ gọi `_validate_audit_item()` để kiểm hình dạng.
Thay riêng `source_sha256`, `snapshot_sha256`, `snapshot_version` hoặc `pin_kind` bằng giá trị hợp kiểu nhưng khác nguồn vẫn cho reporter exit 0, kể cả ghi đè báo cáo có sẵn. Tám probe chứng minh lỗi.

Hậu quả: bảng đếm consistency trộn audit của nguồn/snapshot khác nhưng vẫn được xuất như dữ liệu hợp lệ. Contract R3 yêu cầu audit source/hash/pin match document/root.

Sửa trong nhánh C4: mỗi audit phải có `source_sha256 == document.source.sha256`, `snapshot_sha256 == catalog.sha256`, `snapshot_version == catalog.version`, `pin_kind == catalog.kind`, ngoài config C4 hiện có. Giữ C1–C3 compatibility. Dữ liệu lệch phải exit 2, không tạo báo cáo mới/không đổi báo cáo cũ với --overwrite. Writer C4 dùng cùng validator cũng phải từ chối artifact lệch trước publish.

## R2 — P2: fallback nhận lỗi terminal hoặc mã không tồn tại

`extractor/eval/report.py:574–580` chỉ kiểm hai chuỗi trong error_codes.
Artifact fallback gắn `provider_refusal`, `provider_incomplete` hoặc `unknown_error` đều exit 0; ba probe fail.

Contract yêu cầu hai lỗi retryable; tại adapter ref đã ghim, mã kết quả retryable chỉ là `provider_error` và `invalid_response`.
Sửa validator C4 dùng tập mã hữu hạn này, không sửa adapter và không đổi validator C1–C3. Positive control gồm cả hai mã phải PASS; test cả reporter và writer-before-publish. Không render/echo error string lạ.

## R3 — P2: JSON số quá dài thoát khỏi lỗi an toàn C4

`extractor/eval/run.py:603` gọi `_read_document_inputs()` → `_load_json()` dòng 168.
Metadata hoặc labels chứa JSON integer 5000 chữ số làm json.loads ném ValueError, không được đổi thành DatasetError; CLI in traceback/path thay vì đúng `Lỗi: offline_eval_failed`. Hai probe fail, output chưa tạo và input giữ nguyên.

Sửa hẹp tại ranh giới đọc/parse input C4 để đổi ValueError/RecursionError có thể phát sinh từ JSON thành DatasetError an toàn, không bắt Exception rộng hoặc đổi C1–C3 ngoài scope. Kiểm metadata và labels; fail trước provider generate, stderr đúng một dòng, output/input giữ nguyên. Deep JSON hiện PASS trong probe vẫn giữ regression, không tuyên bố ca đó đã FAIL.

## R4 — P2: report rỗng ở document cuối lọt preflight

`extractor/eval/run.py:603–610` chỉ kiểm cận trên độ dài; report rỗng hợp metadata/label được đưa vào prepared. Với a-good rồi z-empty, provider của a-good được gọi 1 lần trước khi adapter từ chối z-empty.

Sửa kiểm report không rỗng trong C4 preflight, theo chính điều kiện adapter C4 đã có. Không tự mở thêm policy strip/whitespace. Test yêu cầu total generate=0 với lỗi document cuối; giữ chính sách Unicode/universal-newline hiện hành và một retrieval/document hợp lệ.

## Giao sửa và tiêu chí đạt

- Một CTI AI Agent dùng Sol medium làm trực tiếp trong target/branch hiện có; không tạo worker phụ, không đổi base, reset, fetch/pull, sửa source hoặc sửa probe/log/ledger Leader.
- Cho phép sửa `extractor/eval/run.py`, `extractor/eval/report.py`, các test thuộc allowlist gốc, và docs/PROGRESS.md/README nếu cần mô tả hành vi. Không sửa adapter/catalog/retrieval/audit/dependency/UI/core/DB.
- Dùng lại nghiên cứu đã nghiệm thu; bốn finding là sai khác với contract, không cần nghiên cứu mới hoặc hỏi phép giữa các bước.
- RED test repo theo từng finding → sửa nhỏ → GREEN. Chạy nguyên probe 18 ca và lưu SHA trước/sau. Interpreter `root\cti-platform-start\.venv\Scripts\python.exe`; PYTHONPATH target root/core/extractor.
- Hồi quy cần chạy: `test_c4_eval_contract.py`, `test_eval_report.py`, `test_eval_cli.py`, `test_evaluate.py`; Ruff check/format file Python đổi, diff-check. Không cần lặp toàn bộ 291/full repo nếu adapter/audit/scorer không đổi và không có regression mới.
- Giữ C1 bytes/C2-C3 compatibility và Markdown cũ; chạy demo C4-only/C3.1+C4 tại commit mới, không ghi đè fixture cũ; C4 lặp ra file mới để so deterministic.
- Commit local; trả SHA/diff/status/commands/exits/counts, cập nhật `PHONG-HOA-X01-C4-EVAL-RESULT.md`; evidence mới trong `x01-c4-eval-evidence\rework-r1-r4\` có manifest. Không sửa/xóa evidence gốc hoặc Leader.
- Không push/PR/merge/deploy, model thật, mạng, secret hoặc lab. Chưa xác minh model/RAG/TTP/corpus thật; sửa bốn lỗi không thay đổi giới hạn này.

Sau handoff Leader kiểm đúng SHA và bốn finding, rồi nối việc đủ điều kiện; project còn active.
