# X01-INGEST-QUEUE-NEXT — Leader review

Ngày 11/11/2026. Kết luận: **NEEDS_REWORK R1–R4**. Giữ phương án A: importer envelope độc lập, tái dùng validator/store W05, không mang PDF parser sang nhánh W05. Đây là review tài liệu đối chiếu mã nguồn, chưa triển khai hay chạy test importer.

## Đầu vào đã đối chiếu

- Research: `PHONG-HOA-X01-INGEST-QUEUE-RESEARCH.md`, SHA-256 `4db46007f514a14c0894d98892b29147298627e0defe7903566082acb4612b54`.
- Brief: `PHONG-HOA-X01-INGEST-QUEUE-IMPLEMENTATION-BRIEF.md`, SHA-256 `20e374d5fb06fa70ec98fa206037c0ad876df5884c155734ec66e40823078d77`.
- Producer chỉ đọc: `cti-x01-ingest-local`, HEAD `8a16758601647fb3dbf935abecc2435f3b7a3fb6`, sạch.
- W05 chỉ đọc: `cti-x01-w05-stix-e2e`, HEAD `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`, sạch.
- Root tuyệt đối: `$WORKSPACE`.

## R1 — creator rỗng làm bản nháp không thể được duyệt

Brief bước ghi (dòng 88) đặt creator null. Nhưng W05 `extractor/phonghoa_extractor/store.py:1483` từ chối approve khi thiếu creator; đường đọc approved snapshot tại dòng 1353 cũng yêu cầu creator/reviewer khác nhau. `save_draft` đã nhận `created_by_subject` và dùng validator hiện có.

Chốt sửa hợp đồng:

- CLI bắt buộc `--created-by-subject`; library keyword bắt buộc `created_by_subject`, tái dùng kiểm tra subject hiện có. Đây là danh tính do người vận hành CLI khai báo, chưa phải xác thực HTTP thật. Không nhận danh tính từ envelope, không tự đặt danh tính giả, không nới chính sách chống tự duyệt.
- Cùng canonical envelope và cùng creator: duplicate. Cùng envelope nhưng creator khác: lỗi conflict hữu hạn, không trả nháp của người khác như thành công, không đổi chủ sở hữu. Giữ UNIQUE theo envelope hash và ghi rõ kiểm tra creator khi duplicate.
- Acceptance: import rồi list/get và duyệt bằng subject khác qua core hiện có; cùng subject hoặc thiếu creator vẫn bị chặn. Đây là kiểm cục bộ, không phải bằng chứng auth thật.

## R2 — migration và tương thích cần hợp đồng thực thi chính xác

Brief dòng 67–69 và 86 chưa chốt tương thích v2/v3. `_schema_mode` ở `store.py:576` và các reader so với `STORE_SCHEMA_VERSION`; chỉ tăng hằng từ 2 lên 3 sẽ làm reader từ chối hoặc diễn giải sai DB v2. `_migrate_connection` dòng 592 đang tự quản BEGIN/COMMIT; không được lồng thêm BEGIN.

Chốt sửa hợp đồng:

- Có bảng hành vi cho binary mới với DB 0/1/2/3/future: reader không ghi/migrate; giữ cách hiểu selection/version của DB v2, không vô tình giải mã v2 như v1. Xác định riêng yêu cầu của reader review/selection/export.
- Giữ ranh giới hai giai đoạn tương thích store hiện tại: kiểm toàn bộ input trước DB; migration là transaction riêng; sau đó insert draft+provenance trong một transaction. Nêu thẳng: nếu migration thành công rồi insert thất bại, schema mới có thể còn lại, nhưng không có bản nháp/provenance mồ côi. Không hứa toàn bộ DB byte-identical trong ca này.
- Mô tả đúng đường migrate 0/1 hiện có và thêm v2→v3; không giả định có ba transaction 0→1→2. Dưới khóa writer phải đọc lại phiên bản để tránh race hai migrator.
- Validation schema đầy đủ column/type/nullability/PK/FK/full UNIQUE key; draft cũ không có provenance vẫn hợp lệ. Duplicate phải kiểm row provenance liên kết đúng draft và hash nội dung, không coi hash là chữ ký xác thực.
- Test rollback của migration, lỗi insert/commit sau migration, v2/v3 read-only, repeated migration, writer race và regression các đường đọc/duyệt/xuất.

## R3 — kiểm envelope phải khớp producer và giới hạn tuyên bố integrity

Producer `local_ingest.py` dòng 31–36, 175–191 và 398–415 có giới hạn/semantics cụ thể mà brief còn thiếu.

- TXT là UTF-8 literal: `raw_bytes == len(text.encode('utf-8'))` và raw hash bằng canonical text hash. Không chuẩn hóa newline hoặc bỏ BOM ngầm. PDF raw hash chỉ là tự khai vì importer không có byte PDF gốc.
- Tổng text tối đa 1.000.000 code point; PDF tối đa 50 trang, mỗi trang 100.000 code point; ít nhất một trang có ký tự không phải whitespace. Chốt rõ khoảng trang rỗng, separator và toàn bộ bounds theo producer.
- Kiểm UTF-8 hợp lệ cho mọi chuỗi trước canonical serialization/hash; escaped surrogate không được gây traceback. Chốt kiểu DTO, thứ tự shape validation trước truy cập nested field, depth 64 được đếm ra sao, xử lý JSON quá sâu/kiểu list-dict-null-bool sai bằng mã lỗi đóng.
- Sửa tuyên bố “mọi mutation sau export bị từ chối”: chỉ phát hiện bất nhất nội bộ. Envelope đã sửa và tính lại hash nhất quán không tự chứng minh là bản gốc; có thể là input mới. Lưu bất biến sau import khác với xác thực nguồn trước import.

## R4 — brief cần tự đủ để giao một worker

- Target tuyệt đối dưới root: `cti-x01-ingest-queue`; branch `feat/x01-ingest-queue-20261111`, base W05 như trên. Ghi đầy đủ hai source path chỉ đọc.
- Allowlist file cụ thể: module/CLI/tests mới, các file store/test hiện có thật sự phải đổi, contract, ADR quyết định schema và PROGRESS/README cần thiết. Không scope wildcard toàn extractor.
- Chốt signature API/DTO, hàm đọc provenance nếu cần, bộ mã lỗi hữu hạn cùng mapping exit/stdout/stderr, đường bootstrap Python 3.12.13 và interpreter tuyệt đối của target.
- Gates phải bao phủ đúng đường bị ảnh hưởng: `test_store.py`, `test_store_cli.py`, `test_queue.py`, `test_queue_cli.py`, `test_draft_cli.py`, `test_review.py`, `test_selection.py`, `test_stix_export.py`, `test_stix_export_cli.py`; xác minh tên có thật và chọn API regression liên quan schema. Không yêu cầu test không tồn tại hoặc coi test chưa chạy là PASS.
- Report chính xác `PHONG-HOA-X01-INGEST-QUEUE-RESULT.md`; evidence `x01-ingest-queue-evidence/` với manifest/exit/count/demo và ownership cleanup. Cho phép fixture/DB/envelope tổng hợp khi cần chứng minh; cấm dữ liệu thật/secret. Ghi source trước/sau, exact commit, diff và giới hạn.

## Phạm vi rework và điều kiện trả lại

CTI Research chỉ sửa hai tài liệu research/implementation brief nêu trên, đồng bộ R1–R4. Không sửa repo, ledger, review Leader; không tạo worktree/commit, cài dependency hoặc chạy implementation. Đọc nguồn đúng HEAD, xác minh signature/filename và trả hash cuối cùng + vị trí đóng từng finding. Không giao bot khác. Bản brief đã sửa là điều kiện cho Leader giao một implementation worker Sol medium, chưa phải implementation hoàn thành.

Nguồn đối chiếu: [SQLite transactions](https://www.sqlite.org/lang_transaction.html), [PRAGMA user_version](https://www.sqlite.org/pragma.html#pragma_user_version), [Python JSON](https://docs.python.org/3.12/library/json.html), [Python sqlite3](https://docs.python.org/3.12/library/sqlite3.html). Nguồn hỗ trợ semantics transaction/JSON; quyết định identity và scope là quyết định Leader theo mã Phong Hỏa hiện có.
