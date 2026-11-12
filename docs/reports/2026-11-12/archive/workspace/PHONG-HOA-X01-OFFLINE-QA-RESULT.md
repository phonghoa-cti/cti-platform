# X01-OFFLINE-QA — kết quả kiểm độc lập

Ngày kiểm: 10/11/2026
Repo: `cti-platform-start`
Nhánh: `feat/x01-draft-queue-20261110`
SHA đầu/cuối: `d03fa10523b45b94182038b5b46fed8231319e6f`
Python: `3.12.13`
Verdict: **NEEDS_FIX** trong phạm vi luồng ngoại tuyến.

Luồng hợp lệ văn bản tổng hợp → draft → SQLite → list phân trang → get đã chạy được và giữ đúng
hash/span/evidence/findings. Tuy nhiên, đường đọc chi tiết `get` không kiểm lại schema và metadata của payload
đã nằm trong SQLite; trên bản sao DB bị sửa cục bộ, `list` từ chối nhưng `get` trả thành công payload hỏng và
CLI còn in trạng thái `pending` trái với file đầu ra. Đây là lỗi toàn vẹn cần sửa trước khi W05 dựa vào `get`.

## Kết quả theo tiêu chí

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Đúng ref, không sửa repo | PASS | SHA đầu/cuối như trên; `git status --short --branch` chỉ hiện nhánh, không có file thay đổi. |
| Grounding/hash/span với emoji, Unicode, xuống dòng, defang `[dot]`, quote lặp, allowlist và dấu hiệu injection | PASS | `run-3/qa-probe-result.json`: năm kiểm `builder_*` đều `true`; draft vẫn `pending`. |
| Roundtrip payload và rejected item hợp lệ do QA bổ sung rõ là fixture | PASS | ID 2 đọc lại giống payload trước save; rejected item còn `status=bia`, `span=null`. |
| JSON sửa tay sai hash bị từ chối, bản ghi cũ không đổi | PASS | `save` exit 1, không traceback; DB vẫn 3 hàng và hash byte không đổi ở pha kiểm này. |
| Demo CLI đủ luồng với nhiều draft | PASS | Ba lần save tạo ID 1,2,3; list trang `[3,2]` rồi `[1]`; chọn ID 2 và get thành công. |
| Summary không trả text/evidence/findings | PASS | Mỗi summary chỉ có 8 trường hợp đồng; bốn marker nhạy cảm tổng hợp không xuất hiện. |
| `list`/`get` hợp lệ là chỉ đọc | PASS | SHA-256 DB trước và sau pha list/get cùng là `b676ecfe5aba0402f9f795da7734d550d628b8fbb70e816ba2441cd9f24e8265`. |
| DB/payload hỏng bị từ chối nhất quán | **FAIL** | `list` exit 1, nhưng `get` ID 2 exit 0 và xuất `status=approved`, `text=tampered-local-copy`. |
| Timeout không hữu hạn bị từ chối nhất quán | **FAIL (LOW)** | `list --timeout nan` exit 1; `get` exit 0; `save` exit 0 và tạo ID 4. |
| HTTP/auth/UI/approve/OpenCTI/lab/model/dữ liệu thật | UNVERIFIED / ngoài phạm vi | Không có implementation tương ứng; không gọi mạng, model, lab hay UI. |

## Finding 1 — MEDIUM — `get` chấp nhận payload SQLite hỏng và báo trạng thái mâu thuẫn

- SHA: `d03fa10523b45b94182038b5b46fed8231319e6f`.
- Code: `extractor/phonghoa_extractor/store.py:223-245` chỉ parse JSON object rồi trả về; không gọi
  `_validate_draft`, không đối chiếu cột `status/source_sha256/schema_version`, cũng không kiểm `created_at`.
  Trong khi đó `extractor/phonghoa_extractor/store.py:161-187` thực hiện phần lớn kiểm này cho `list`.
  `extractor/draft/store.py:72-75` ghi file do `get` trả nhưng luôn in `status=pending`.
- Tái hiện: sao chép DB tổng hợp; dùng SQLite thay `payload_json` của ID 2 bằng
  `{"status":"approved","text":"tampered-local-copy"}`; chạy `list` và `get` trên cùng bản sao.
- Thực tế: `list` exit 1 và không tạo output; `get` exit 0, tạo `corrupt-get.json` chứa payload hỏng;
  stdout lại là `{"id": 2, "status": "pending"}`.
- Mong đợi: đường đọc chi tiết từ chối payload/schema/metadata không hợp lệ bằng `DraftStoreError`, không tạo
  hoặc ghi đè output.
- Ảnh hưởng: W05 hoặc công cụ offline dùng `get` có thể nhận cấu trúc/trạng thái không thuộc hợp đồng trong khi
  danh sách đã coi cùng hàng là hỏng. Đây không phải chứng minh chống người có toàn quyền sửa DB; nó là kiểm
  toàn vẹn và phát hiện hỏng/không nhất quán trong ranh giới hiện tại.
- Khắc phục tối thiểu: cho `get_draft` chọn cả các cột metadata, gọi `_validate_draft`, kiểm
  `status/source_sha256/schema_version` và `created_at` như `_draft_summary`; chỉ trả payload sau tất cả kiểm.
  Thêm test âm tính cho payload thiếu trường, sai hash/span và metadata cột không khớp.
- Artifact: `run-3/qa-corrupt-copy.sqlite`, `run-3/corrupt-get.json`, các command 11–12 trong
  `run-3/qa-probe-result.json`.

## Finding 2 — LOW — `save/get` nhận timeout NaN trong khi `list` từ chối

- SHA: `d03fa10523b45b94182038b5b46fed8231319e6f`.
- Code: `extractor/phonghoa_extractor/store.py:190-200` và `:223-234` chuyển timeout thẳng cho SQLite;
  chỉ `list_drafts` kiểm số hữu hạn tại `:264-270`. CLI nhận `float` tại
  `extractor/draft/store.py:26,32,39`.
- Tái hiện: chạy lần lượt `list/get/save --timeout nan` trên DB tổng hợp.
- Thực tế: list exit 1 có lỗi dự kiến; get exit 0; save exit 0 và thêm ID 4.
- Mong đợi: ba thao tác từ chối timeout không hữu hạn nhất quán trước khi mở/ghi DB.
- Ảnh hưởng: tham số cấu hình sai không được báo ở `save/get`, và `save` vẫn gây thay đổi dữ liệu. Đây là lỗi
  độ bền/CLI cục bộ, không phải lỗ hổng vượt quyền.
- Khắc phục tối thiểu: dùng chung một hàm kiểm timeout hữu hạn, không âm cho `save_draft`, `get_draft` và
  `list_drafts`; thêm test CLI/API cho `nan`, `inf`, số âm và bool ở cả ba thao tác.
- Artifact: ba command cuối và `nan_timeout_results` trong `run-3/qa-probe-result.json`.

## Lệnh và exit code

1. `.venv\Scripts\python.exe --version` → exit 0, `Python 3.12.13`.
2. `.venv\Scripts\python.exe ..\x01-offline-qa-evidence\qa_probe.py <repo> <python>` → exit 0 ở lần xác
   nhận `run-3`; script điều phối 15 tiến trình CLI và kiểm payload/DB. Log: `03-qa-probe.log`.
3. Các exit âm tính được mong đợi trong script: invalid hash exit 1; corrupt list exit 1; NaN list exit 1.
   Corrupt get và NaN save/get exit 0 là bằng chứng cho hai finding, không được tính là PASS.
4. Hai lần dựng harness trước đó exit 1: lần 1 do giả định sai về CRLF so với text đã giải mã; lần 2 do console
   Windows CP1252 khi in tiếng Việt. Không lần nào là lỗi sản phẩm; log giữ ở `01-qa-probe.log` và
   `02-qa-probe.log`. Lần xác nhận đã đổi sang UTF-8 và exit 0.

Không chạy lại 77 test store/queue hoặc toàn suite 192 test vì brief yêu cầu dùng bằng chứng đã có và tập trung
ca mới sau đọc code. Không sửa source/test/docs trong repo; không checkout/reset/commit/push/PR/merge/deploy.

## Artifact

- `x01-offline-qa-evidence/qa_probe.py`: harness kiểm độc lập, ngoài repo.
- `x01-offline-qa-evidence/03-qa-probe.log`: log lần xác nhận exit 0.
- `x01-offline-qa-evidence/run-3/qa-probe-result.json`: 15 command, exit/stdout/stderr và kết quả assertion.
- `x01-offline-qa-evidence/run-3/qa-demo.sqlite`: DB tổng hợp; ID 4 được tạo có chủ đích bởi ca NaN.
- `x01-offline-qa-evidence/run-3/qa-corrupt-copy.sqlite`: chỉ là bản sao bị sửa để tái hiện finding 1.
- `x01-offline-qa-evidence/run-3/page-1.json`, `page-2.json`, `selected-detail.json`: demo phân trang/get.

Giới hạn: PASS trên dữ liệu tổng hợp và runtime cục bộ không chứng minh chất lượng extractor trên dữ liệu thật,
không chứng minh miễn nhiễm prompt injection, và không xác minh quyền/auth/UI/OpenCTI/lab. Giới hạn kind và
item.status chưa khóa đầy đủ đã có trong hợp đồng; không ghi lại thành finding mới.

Bước ngoại tuyến hữu ích tiếp theo sau khi sửa: thêm đúng các test hồi quy âm tính cho `get` trên payload/metadata
hỏng và timeout chung, rồi chạy lại nhóm store/queue liên quan; chưa cần mở HTTP hay UI.

## Học thêm

- **Validation on read** là kiểm lại dữ liệu khi đọc, giúp phát hiện DB hỏng hoặc metadata không nhất quán thay vì
  mặc định mọi byte đã lưu vẫn đúng hợp đồng.
- **NaN** là giá trị số dấu phẩy động “không phải số”; parser vẫn có thể nhận nó như `float`, nên phải kiểm
  `isfinite` trước khi dùng làm timeout.
- **Mode=ro** mở SQLite chỉ đọc; nó ngăn lệnh đọc tự ghi DB nhưng không thay thế kiểm schema và hash payload.
