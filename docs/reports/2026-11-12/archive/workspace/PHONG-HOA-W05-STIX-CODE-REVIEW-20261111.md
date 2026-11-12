# W05-STIX — review độc lập của Leader, 11/11/2026

Kết luận: **REWORK REQUIRED**, chưa chấp nhận request `87704ab8-79af-4019-8e2c-6b5d8b3e70d0`.
Review exact HEAD `dbec016e9ff13dbcfef0fa215a7a0406430d1e7b`, branch `feat/w05-stix-offline-20261111`, tree `$WORKSPACE\cti-w05-stix-offline`.
Base `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`. Diff đúng 12 file, +2277/-2; working tree sạch trước/sau kiểm.
Leader không sửa source sản phẩm; probe riêng ngoài repo.

## Bằng chứng Leader đã chạy
- `.venv/Scripts/python.exe -X utf8 -B -m pytest -q -p no:cacheprovider extractor/tests/test_stix_export.py extractor/tests/test_stix_export_cli.py`: 53 dấu PASS, exit 0. Do pytest.ini đã có -q, output không có summary chữ. Hai file có 53 ca parametrized.
- Manifest hiện hữu: 11/11 hash khớp.
- API dependency files và portal lock diff từ base rỗng.
- Source integration vẫn HEAD d3cbaa6, status sạch.
- Probe mới `w05-stix-evidence/leader-review/test_stix_review.py`: **14 failed in 1.27s**, exit 1. R1 8 ca, R2 6 ca. Cả file-symlink và directory-symlink hoạt động thật trên Windows, không skip/mô phỏng.
- Raw output: `w05-stix-evidence/leader-review/probe-red.log`.
- Probe SHA256 `8ED38838B86F546826808DC820A7A9EF795526AE94B5E9277B70F3EFEAD80BDA`.
- RED log SHA256 `9C9B17B09447A73B9576C466F4D611DFF33FBF9FDC8E7449D6B52BF69D7AEB95`.

Không chạy lại full 500. Con số full-suite/TDD lịch sử trong báo cáo Backend chưa được Leader tái chạy; evidence hiện hữu có README và demo/manifest, chưa có raw log của các lượt đó. Không dựng lại lịch sử RED bằng suy diễn. Các kiểm chứng cục bộ trước vẫn hữu ích nhưng không bao phủ hai lỗi mới.

## R1 — P2: config sai kiểu/UTC vượt miền thoát khỏi lỗi nghiệp vụ
Vị trí `extractor/phonghoa_extractor/stix_export.py:175`, `:152`; CLI `extractor/draft/stix_export.py:50`.
- `tlp=[]` hoặc `tlp={}` gây TypeError khi membership vào set.
- `created=0001-01-01T00:00:00+01:00` và `9999-12-31T23:59:59-01:00` parse được nhưng chuyển UTC gây OverflowError.
- Library không trả StixExportError; CLI in traceback nhiều dòng/path nội bộ thay vì JSON an toàn một dòng.
- Ca CLI dùng DB chưa tồn tại: lỗi xảy ra khi đọc config, trước đọc DB; không cần dữ liệu thật.

Sửa tại biên validation: kiểm type trước enum membership, normalize thời gian trong biên lỗi domain gồm overflow UTC. Rà các trường config cùng đường đi theo list/dict/null/bool/number và surrogate để không sót cùng lớp lỗi; không bắt Exception tổng quát để che bug. Giữ --help/argparse usage behavior.
Đạt khi library trả StixExportError và CLI exit1, stdout rỗng, stderr chính xác `{"error":"export_failed"}\n`, không output/temp và không thay input.

## R2 — P1: chưa bảo vệ sidecar của DB sau resolve alias
Vị trí `extractor/phonghoa_extractor/stix_export.py:407` (_protected_aliases), `:422` (so normalized path), `:529` (đầu export); getter store dùng `path.resolve()` khi mở DB.
- DB được đưa qua file symlink `alias.sqlite -> real/approved.sqlite`, hoặc parent directory symlink.
- Output là `real/approved.sqlite-wal`, `-shm`, `-journal`, ban đầu chưa tồn tại.
- Bộ bảo vệ chỉ tạo sidecar theo tên alias được truyền; normalized path không resolve. Getter mở DB thật, nhưng publisher chấp nhận và tạo bundle JSON vào cả ba tên dành riêng cho SQLite. Cả 6 ca trả thành công thay vì từ chối.
- Đây là đường dẫn alias tĩnh trong thư mục tin cậy, **không** phải hostile directory race ngoài phạm vi.
- Probe chứng minh ghi vào tên sidecar; không khẳng định đã gây mất dữ liệu/khôi phục SQLite hỏng. Nguy cơ là làm bẩn tệp điều phối/recovery của DB.

Sửa: bảo vệ cả đường dẫn lexical và đường dẫn resolved của DB/config và các sidecar tương ứng trước publish; giữ samefile/alias checks cho file đã tồn tại. Có thể từ chối rõ ràng alias input nếu chọn không hỗ trợ, nhưng không được âm thầm cho phép ghi sidecar thật. Không tuyên bố tìm được mọi hardlink alias trên disk; không scan disk. Giữ fail-closed khi path resolution lỗi và boundary trusted local directory đã chốt.
Đạt khi cả 6 ca bị chặn, không target/temp, DB bytes giữ nguyên; thêm positive bình thường và alias-input export tới tên bundle hợp lệ nếu tiếp tục hỗ trợ alias. Re-run race same/different bytes, existing identical/different output, DB/config/sidecar alias và cleanup.

## Brief rework cho CTI Backend / Sol medium
- Sửa đúng tree/branch/HEAD trên, một writer, không giao bot khác.
- Phạm vi source: `extractor/phonghoa_extractor/stix_export.py`, hai file test STIX; CLI chỉ nếu cần theo R1. Docs export/ADR/PROGRESS chỉ cập nhật đúng giới hạn mới. Không đổi store/core/API/UI/gateway/schema/migration/dependencies/locks.
- Không sửa probe/RED log/review/Leader plan/RUNS. Có thể đọc và chạy probe nguyên trạng. Evidence mới trong `w05-stix-evidence/rework-r1-r2`; cập nhật báo cáo kết quả và manifest.
- Tái hiện RED bằng regression repo bổ sung trước sửa. GREEN: 14 probe Leader nguyên trạng + toàn bộ hai file test STIX (gồm validator, Windows race, CLI). Ruff check/format đúng file; git diff --check; git status và source status cuối.
- Không lặp full500 hoặc UI/build/browser vì scope chỉ exporter/validation/path protection; chỉ mở rộng nếu có thay đổi/lo ngại cụ thể.
- Lưu raw stdout/stderr, exact command, exit code, số ca và hash cho rework; không biến README kể lại thành log chạy. Không làm giả raw log lịch sử. Báo count mới thực tế, không gọi 53 cũ là số cuối nếu thêm regression.
- Commit cục bộ Conventional Commits, tree sạch. Báo HEAD, diff, bằng chứng RED/GREEN, không push/PR/merge/deploy/lab/secret/LLM/OpenCTI/dữ liệu thật.
- Vẫn UNVERIFIED: OpenCTI import/workbench, mapping identity tổ chức thật, network share/crash/power-loss/hostile mutation, lab/production.
