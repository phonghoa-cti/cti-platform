# X01-QA-RECHECK — kiểm độc lập F1/F2 sau sửa

Ngày kiểm: 10/11/2026
Repo: `cti-platform-start`
Nhánh: `feat/x01-draft-queue-20261110`
SHA đầu/cuối: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
Python: `3.12.13`
Verdict: **PASS trong phạm vi recheck — F1 CLOSED, F2 CLOSED**.

Đây là lần chạy độc lập bằng CLI thật trên DB và output mới. Không dùng exit 0 của Engineer/Leader thay bằng
chứng cứ QA; không chạy lặp 44 regression hay toàn suite 236 test đã được Leader đối chiếu.

## Kết quả

| Tiêu chí | Trạng thái | Bằng chứng quan sát |
|---|---|---|
| Đúng ref, worktree sạch | PASS | HEAD đầu/cuối `e83bb3f...`; `git status --short --branch` chỉ có tên nhánh. |
| F1: payload thiếu trường/trạng thái tampered | CLOSED | `get` và `list` đều exit 1; không traceback/payload; DB và output sentinel không đổi. |
| F1: span không khớp evidence | CLOSED | `get` và `list` đều exit 1; DB và output sentinel không đổi. |
| F1: cột `source_sha256` mâu thuẫn payload | CLOSED | `get` và `list` đều exit 1; DB và output sentinel không đổi. |
| F2: `nan`, `inf`, `-1` cho save/get/list | CLOSED | Cả 9 lệnh đều exit 1, báo lỗi timeout, không traceback; DB cũ vẫn 3 hàng và giữ nguyên SHA-256. |
| F2: save `nan` vào đường DB chưa tồn tại | CLOSED | Exit 1 và không tạo file DB. |
| Smoke ba fixture W05 | PASS | Save ID 1–3; list `[3,2]` rồi `[1]`; get cả ba ID giữ nguyên payload/hash/span. |
| Summary tối thiểu | PASS | Chỉ 8 trường hợp đồng; không có `text`, `evidence`, `findings`. |
| Lệnh đọc hợp lệ chỉ đọc | PASS | SHA-256 DB trước/sau smoke list/get không đổi. |

## F1 — CLOSED

Ba bản sao riêng của DB hợp lệ được sửa có chủ đích:

1. ID 2 có `payload_json={"status":"approved","text":"tampered-local-copy"}`.
2. ID 1 có `span=[0,1]` không khớp evidence.
3. ID 1 có cột SQLite `source_sha256` đổi thành 64 số 0 trong khi payload không đổi.

Với từng bản sao, QA chạy hai tiến trình `get` và `list`. Cả 6 lệnh đều exit 1. Trước mỗi lệnh, output được
ghi sentinel; sau lỗi, sentinel vẫn nguyên. SHA-256 DB trước/sau lệnh giữ nguyên. Stdout/stderr không chứa
`tampered-local-copy` hoặc traceback. `list` chỉ đánh giá hàng `pending` thực sự nằm trong trang trả về; QA
không mở rộng kết luận sang hàng bị lọc.

Code liên quan tại SHA này:

- `extractor/phonghoa_extractor/store.py:173` dùng chung decode/validation cho row.
- `extractor/phonghoa_extractor/store.py:245` cho `get_draft`; `:274` cho `list_drafts`.
- `extractor/draft/store.py:75` in trạng thái lấy từ payload đã kiểm.

## F2 — CLOSED

QA chạy `save`, `get`, `list` với từng giá trị `nan`, `inf`, `-1`: 9/9 lệnh exit 1 với lỗi timeout rõ,
không traceback. DB hợp lệ vẫn đúng 3 hàng và không đổi byte; output có sẵn của get/list không bị ghi đè.
Thêm một lệnh `save --timeout nan` trỏ tới DB chưa tồn tại cũng exit 1 và không tạo DB.

Code liên quan: helper chung tại `extractor/phonghoa_extractor/store.py:161`, được gọi trước SQLite trong
`save_draft` (`:211`), `get_draft` (`:245`) và `list_drafts` (`:274`).

## Smoke hợp lệ

Ba fixture đã có trong `extractor/draft/examples/` được bỏ `id/created_at`, rồi chạy qua CLI:

- 3 lệnh `save` → ID 1, 2, 3;
- 2 lệnh `list --limit 2` → `[3,2]`, cursor 2, rồi `[1]`, cursor null;
- 3 lệnh `get` → payload sau khi bỏ metadata store bằng đúng đầu vào của từng fixture;
- `source.sha256` khớp UTF-8 của text; mọi span khác null cắt đúng evidence;
- allowlist/rejected/findings của fixture thứ hai được bảo toàn;
- summary không chứa toàn văn/evidence/findings; các lệnh đọc không đổi DB.

## Lệnh, số tiến trình và artifact

Lệnh điều phối:

```text
.venv\Scripts\python.exe ..\x01-qa-recheck-evidence\qa_recheck.py <repo> <python>
```

Kết quả exit 0; harness đã chạy **24 tiến trình CLI**:

- 8 smoke hợp lệ, đều exit 0;
- 6 ca F1 âm tính, đều exit 1 như mong đợi;
- 9 ca F2 trên DB cũ, đều exit 1 như mong đợi;
- 1 ca F2 trên DB chưa tồn tại, exit 1 như mong đợi.

Artifact ngoài repo, không ghi đè bằng chứng cũ:

- `x01-qa-recheck-evidence/qa_recheck.py` — harness độc lập.
- `x01-qa-recheck-evidence/01-qa-recheck.log` — log tổng, exit 0.
- `x01-qa-recheck-evidence/qa-recheck-result.json` — toàn bộ 24 command, exit/stdout/stderr và assertion;
  SHA-256 `0246ed897b331d3ff68748bc4f084d02b83c1f36c7c55a4bd1886efbbac9ad96`.
- `x01-qa-recheck-evidence/recheck-valid.sqlite` — DB smoke tổng hợp;
  SHA-256 `9a56a58084fb0c2b5ec1e8d0929809ed1302421d2227d189121ff1f4fa995bc6`.
- Ba DB `f1-*.sqlite` là bản sao bị sửa chỉ để kiểm âm tính; các file output F1/F2 giữ sentinel để chứng minh
  lỗi không ghi đè.

Không sửa source/test/docs trong repo, không checkout/reset/commit, mạng, LLM, lab, UI, push/PR/merge/deploy.

## Giới hạn

PASS này chỉ đóng F1/F2 và xác nhận smoke SQLite/CLI ngoại tuyến bằng dữ liệu tổng hợp. HTTP, auth/quyền,
approve/reject, UI, OpenCTI, lab, cloud, dữ liệu thật và khả năng chống mọi prompt injection vẫn UNVERIFIED/
ngoài phạm vi. Không phát hiện finding mới trong phạm vi recheck tập trung.
