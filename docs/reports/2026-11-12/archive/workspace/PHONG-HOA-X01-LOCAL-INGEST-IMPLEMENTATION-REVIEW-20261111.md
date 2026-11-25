# Leader review — X01 local ingest: cần sửa R1–R3

Ngày kiểm: 11/11/2026. Chưa nghiệm thu implementation.

Root tuyệt đối: `$WORKSPACE`.

Target `<root>\cti-x01-ingest-local`, branch `feat/x01-ingest-local-20261111`, HEAD `910ced561176b9753ffea113c93414ff77fac427`. Source `<root>\cti-x01-gold-pilot` sạch tại `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`; target sạch. Diff-check base..HEAD exit 0. Leader chỉ tạo probe/log/review ngoài repo, không sửa mã sản phẩm hoặc worker evidence.

## Bằng chứng độc lập

- `<target>\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider extractor/tests/test_local_ingest.py extractor/tests/test_ingest_cli.py extractor/tests/test_drafts.py extractor/tests/test_draft_cli.py extractor/tests/test_grounding.py`: 99 dấu PASS, exit 0. Log `<root>\leader-local-ingest-review\regression.log`.
- Manifest worker: 13 mục/13 file thực, không thiếu/thừa/sai hash. Đây là kiểm tính toàn vẹn, không thay thế kiểm hành vi.
- Probe `<root>\leader-local-ingest-review\test_ingest_contract.py`, SHA-256 `a1896975905607b0cb607b7e5a76a2d22256f8828bd9ee003b37b7f7ed0e11e9`.
- Từ root: `<target>\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short leader-local-ingest-review/test_ingest_contract.py`: **5 failed, 1 passed**, exit 1. Log `leader-local-ingest-review/probe-red.log`.
- Probe dùng lỗi giả lập và fixture tổng hợp; không khởi chạy child bị treo thật, không tạo junction hay đọc network share. Ca JSON lồng 2.000 cấp đạt, không ghi nhận nó thành finding.

## R1 — kiểu mã lỗi child chưa được kiểm trước membership

`extractor/phonghoa_extractor/local_ingest.py:278` dùng `data.get("code") not in set` trước kiểm type. Result `{ "ok": false, "code": [] }` hoặc `{}` gây `TypeError`, thoát public `ingest_local_file()` thay vì mã đóng `pdf_child_invalid_result`. Hai probe tái hiện; CLI chỉ bắt LocalIngestError nên đường này cũng chưa có bảo đảm lỗi đóng.

Sửa nhỏ: exact string/type/schema trước membership; giữ sáu mã PDF cho phép, từ chối mọi kiểu/enum khác. Không bắt rộng để che lỗi lập trình. Test malformed result qua public ingest và boundary CLI: exit 1, không traceback/raw marker, input/output có sẵn không đổi. Giữ duplicate/nonfinite/cap/UTF-8 checks.

## R2 — lỗi wait/terminate bỏ qua kill/reap và xóa temp quá sớm

`local_ingest.py:210–242` đổi OSError thành pdf_child_failed nhưng không tiếp tục thu hồi child. `local_ingest.py:168` luôn gọi TemporaryDirectory.cleanup(). Hai probe (wait OSError, terminate OSError) đều quan sát `kill_attempted=false`, `reaped=false`, `temp_exists=false` dù fake child chưa kết thúc và vẫn có thể kill/reap được.

Yêu cầu: cleanup child là bước độc lập, hữu hạn; lỗi terminate không ngăn thử kill/reap, lỗi wait ban đầu không bỏ qua thu hồi. Chỉ dọn snapshot/result sau khi xác nhận child đã kết thúc. Nếu hết các bước hữu hạn vẫn không xác nhận được, trả pdf_child_failed, giữ temp owned, không để finalizer âm thầm xóa nó và không nhận là cleanup thành công. Không retry extraction hoặc chạy child thứ hai. Thêm fault-injection cả lỗi kill/final wait và ca child đã chết khi thao tác terminate báo lỗi; không sinh tiến trình mồ côi thật. Test xác nhận thứ tự và trạng thái process/temp, không chỉ assert mã lỗi như test_lifecycle_failure_is_closed hiện tại.

## R3 — input qua ancestor reparse vẫn được đọc

`local_ingest.py:105–118` chỉ kiểm lstat/is_symlink của file cuối. Thư mục cha là reparse point không được xét; đây có thể dẫn tới nơi ngoài phạm vi local hoặc network share. Probe gắn cờ reparse cho một ancestor tĩnh, leaf vẫn là file regular: public ingest đọc thành công thay vì từ chối trước đọc.

Kiểm từng ancestor lexical trước theo liên kết, kể cả đường dẫn tương đối và cha của cwd, giữ UNC/network/symlink/reparse bị từ chối bằng input_not_regular. Kiểm lỗi filesystem vẫn trả mã đóng đúng contract. Tái dùng cách kiểm đã có trong source khi phù hợp, không sửa module gold; không tuyên bố chống được hostile mutation/TOCTOU. Dùng fault-injection cho symlink/reparse ở nhiều mức và positive regular paths; không tạo junction thật nếu chính sách máy không cho phép.

## Gói sửa tự đủ

CTI AI Agent, một worker Sol medium, sửa trực tiếp trên target hiện có từ HEAD nêu trên; không reset, tạo tree/nhánh khác hay giao tiếp. Giữ nguyên Leader plan/research đã chấp nhận. Allowlist rework: `extractor/phonghoa_extractor/local_ingest.py`, `extractor/tests/test_local_ingest.py`, `extractor/tests/test_ingest_cli.py`; chỉ sửa `extractor/ingest/run.py` nếu boundary CLI cần và giải thích diff. Có thể cập nhật đúng ADR0011/PROGRESS để mô tả trạng thái cleanup chưa xác nhận; không đổi dependency, fixtures, C1/C4/gold/W05 hay source.

Chạy RED regression trước fix, GREEN sau; giữ nguyên probe Leader và kiểm hash trước/sau. Chạy 99-test set trên (cộng regression mới), Ruff check/format trên Python đã sửa, diff-check và scope. Không lặp toàn repo/model/browser/lab. Local commit Conventional Commit sau kiểm xanh, kiểm source/target sạch. Demo TXT/PDF hai output mới trên HEAD, bytes/input hash bất biến; nêu rõ cleanup fault-injection và PDF fixture thật là hai loại bằng chứng.

Cập nhật `PHONG-HOA-X01-LOCAL-INGEST-RESULT.md`; evidence mới trong `x01-local-ingest-evidence/rework-r1-r3/`, manifest riêng và root hai chiều. Không sửa/xóa probe/log/review/ledger/plan Leader. Báo exact SHA/diff/tests/exit, tình trạng R1–R3, tài nguyên còn lại và giới hạn. Không push/PR/merge/deploy, model/network runtime/real corpus/lab. Không coi 99 test cũ đạt là lý do bỏ qua năm probe đỏ.
