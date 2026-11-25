# X01-C4-ADAPTER-IMPLEMENT — kết quả sau rework R1

Ngày: 11/11/2026. Trạng thái: **PASS cục bộ/offline tại commit R1**, chưa được Leader nghiệm thu và không phải bằng chứng model/lab/production.

## Ref và thay đổi

- Source read-only: `cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, sạch tại `d97f96362edcd92e87fc69cfa20a563109cec550`.
- Target: `cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`, sạch tại `654443e6ede6557f0629fc0886ca56fff782b193`.
- Commit adapter gốc: `e5e6751c7c1b35cc22e96c8765be2ee4f2f2a521` — `feat: add offline C4 ATT&CK request context`.
- Commit R1: `654443e6ede6557f0629fc0886ca56fff782b193` — `fix: reject invalid UTF-8 provider metadata`.
- Diff `d97f963..654443e`: 7 file, `+555/-12`. Diff R1 `e5e6751..654443e`: đúng 2 file cho phép, `+31/-1`.

Wrapper C4 gốc vẫn kiểm source/TLP, gọi retriever lexical một lần, gửi context ATT&CK có hash/provenance trong request bất biến và tái dùng retry/fallback C3. R1 chỉ sửa seam metadata dùng chung: `model_id` hoặc `error_code` chứa surrogate không mã hóa UTF-8 được nay trở thành `_RetryableError("invalid_response")`, không mang raw value; không bắt rộng lỗi pipeline.

## Bằng chứng adapter gốc trước R1

- Báo cáo ban đầu ghi suite 9 file `428 passed`, Ruff và so sánh 6/6 artifact tại commit `e5e6751`; đây là bằng chứng lịch sử trước review R1, không được chạy lại trong lượt rework.
- Leader review tái hiện probe 12 ca đỏ tại `e5e6751`: `UnicodeEncodeError` thoát retry sau một call. Review SHA-256 `528454B63757982E69353EF2D5A28109D22A3E76ED6EF709AB7F442CA21D4A46`; probe SHA-256 `52DC1FBA95B55D365B34489DA7F4C62887566283BE5A06E776EC98681DDD6792`.

## R1 RED → GREEN và kiểm chứng mới

- Regression trong repo trước sửa: exit `1`, `12 failed, 71 deselected`; cả C2/C3/C4 × `model_id`/`error_code` × recovery/exhaustion đều lỗi đúng `UnicodeEncodeError`.
- Regression hẹp sau sửa: exit `0`, `12 passed, 71 deselected`.
- Probe Leader nguyên bản sau sửa: exit `0`, `12 passed`; hash probe vẫn `52DC1FBA95B55D365B34489DA7F4C62887566283BE5A06E776EC98681DDD6792`.
- `test_llm_adapter.py` + `test_ttp_audit.py`: exit `0`, `138 passed`.
- `test_llm_cli.py` + `test_eval_cli.py`: exit `0`, `73 passed`. Lần gọi đầu từ root lỗi collection do cwd không chứa package `extractor`; chạy lại từ target với cùng Python/PYTHONPATH đạt và không cần sửa code.
- Ruff format, Ruff check và Ruff format-check trên hai file Python đổi: đều exit `0`.
- `git diff --check` cho cả `d97f963..654443e` và `e5e6751..654443e`: exit `0`.
- So sánh whole-artifact C2/C3 source→target: exit `0`, đủ 6/6 ca `success`, `retry_success`, `fallback` bằng nhau.

Chi tiết lệnh/output ở `x01-c4-adapter-evidence/rework-r1/`. Manifest gốc `x01-c4-adapter-evidence/SHA256SUMS.txt` bao phủ báo cáo này và toàn bộ evidence đệ quy, trừ chính manifest.

## PASS / FAIL / UNVERIFIED

- **PASS:** metadata sai UTF-8 đi qua retry/fallback hiện có; recovery và exhaustion đều đúng 2 calls; cùng request object; marker không xuất hiện trong result; terminal semantics và response hợp lệ giữ nguyên qua regression; C2/C3 giữ nguyên 6/6 artifact; source/target sạch đúng ref.
- **FAIL:** không còn finding trong phạm vi R1.
- **UNVERIFIED:** model thật và chất lượng semantic TTP/RAG; chống prompt injection thực tế; recall đa ngôn ngữ; corpus thật do hai người gán nhãn; evaluator/reporter C4; OpenCTI; lab; production. Provider giả lập chỉ chứng minh contract, calls và fallback.

## Học thêm

- **Unicode surrogate** là mã trung gian không tự tạo thành ký tự UTF-8 hợp lệ; dữ liệu ngoài có thể chứa nó dù kiểu Python vẫn là `str`.
- **Retry seam** là ranh giới chuyển lỗi provider thành mã lỗi ổn định để retry/fallback xử lý mà không che lỗi lập trình khác.
- **Non-leakage** nghĩa là lỗi và output không lặp lại metadata thô có thể chứa dữ liệu nhạy cảm.
