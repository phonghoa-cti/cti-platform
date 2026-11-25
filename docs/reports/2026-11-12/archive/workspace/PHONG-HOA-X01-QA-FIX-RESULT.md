# Kết quả X01-QA-FIX

Ngày kiểm: 10/11/2026. Trạng thái: **PASS phạm vi sửa F1/F2**, chờ Leader nghiệm thu và QA xác nhận độc lập.

## Git và phạm vi

- Checkout: `cti-platform-start`
- Nhánh: `feat/x01-draft-queue-20261110`
- Base: `d03fa10523b45b94182038b5b46fed8231319e6f`
- Commit: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
- Commit message: `fix: validate stored drafts and timeouts`
- Diff commit: 7 file, 230 dòng thêm, 22 dòng bỏ.
- Sau commit: `git status --porcelain=v1` có 0 dòng; `git diff --check` exit 0.

Không đổi schema SQLite, core/grounding, fixture W05, dependency, UI, HTTP/auth, OpenCTI hoặc harness/báo cáo QA.

## Thay đổi

1. `extractor/phonghoa_extractor/store.py`
   - Thêm một helper timeout dùng chung cho `save_draft`, `get_draft`, `list_drafts`.
   - Chỉ nhận `int`/`float` không phải boolean, hữu hạn và không âm; kiểm trước khi mở SQLite.
   - Thêm một helper decode/validate row dùng chung cho `get` và `list`.
   - Kiểm payload bằng `_validate_draft`, đối chiếu cột `schema_version`, `status`, `source_sha256`, kiểm ID và
     `created_at` ISO có múi giờ trước khi trả detail/summary.
2. `extractor/draft/store.py`
   - Stdout của `get` dùng trạng thái đã kiểm từ payload thay vì chuỗi `pending` cố định.
3. Tests
   - Hồi quy payload JSON hỏng/thiếu trường/sai hash/span/status; metadata schema/status/hash và thời gian hỏng.
   - Kiểm `get/list` không đổi byte DB, CLI không ghi đè output cũ và không lộ payload hỏng/traceback.
   - Kiểm timeout bool/sai kiểu/âm/NaN/±Inf qua API và CLI cho cả ba thao tác trước I/O SQLite.
4. Docs
   - Cập nhật README, hợp đồng W05 và PROGRESS theo hành vi đã chạy.

## RED → GREEN và kiểm thử

Runtime: `Python 3.12.13`.

| Pha | Lệnh | Kết quả |
|---|---|---|
| RED | `python -m pytest extractor/tests/test_store.py extractor/tests/test_store_cli.py -k ... -q` | 30 ca fail đúng lỗi đọc/timeout, exit 1 |
| GREEN tập trung | cùng nhóm hồi quy sau sửa | 40 ca đạt, exit 0 |
| Store/queue | bốn file `test_store*` và `test_queue*` | 121 test đạt, exit 0 |
| Toàn suite cuối | `python -m pytest -q` | 236 test đạt, exit 0 |
| Ruff | `ruff check .` | exit 0 |
| Format | `ruff format --check .` | 90 file đã đúng định dạng, exit 0 |
| Diff | `git diff --check` | exit 0 |
| Sau commit | nhóm hồi quy mới | 44 ca đạt, exit 0; cây Git sạch |

Pytest được đối chiếu bằng `--collect-only`: toàn suite 236 test, nhóm store/queue 121 test.

## Demo qua tiến trình CLI riêng

Script: `x01-qa-fix-evidence/qa_fix_demo.py`; log: `04-demo.log`, exit 0.

- Ba fixture W05 được bỏ metadata store rồi `save` thành ID 1, 2, 3.
- `list` trả `[3, 2, 1]`; `get` ID 2 roundtrip nguyên payload.
- Chuỗi trạng thái item `ok`, `allowlist`, `bia` còn nguyên; stdout `get` là `pending` từ payload đã kiểm.
- `save/get/list --timeout=nan` cùng exit 1; DB và output có sẵn giữ nguyên.
- Trên bản sao DB có payload `approved/tampered`, cả `get` và `list` cùng exit 1; không traceback, không lộ toàn
  văn, không đổi DB và không ghi đè output.
- Các lần đọc hợp lệ giữ nguyên SHA-256 DB.

## Bằng chứng

Thư mục: `x01-qa-fix-evidence/`

| File | SHA-256 |
|---|---|
| `01-red.log` | `61F9B4D0AA926F2A5521D43A5965CFC5542958A7722979AF73F09226BED467B1` |
| `02-green.log` | `33E65AACDB05901B1F4EBF2AFCD3392DAD16BD18777D36F6B44133A4B8D921B5` |
| `03-related.log` | `5F8982998BD931E14F4B2E357075061183B15C4609E5D9CEB5D7D7BA20D382A6` |
| `04-demo.log` | `D97D00B03D4DFDDE303FEB5257413B5111E30B08ABA9278A8A8F179B3A6BD0AE` |
| `06-static.log` | `E1FD0BDABF6A6DBFDD019DCE22C567E667BB1D428E1758A3DDD761C3BB019019` |
| `07-final-suite.log` | `54FEB3437D50B221E35DB25C48BC9BA69F035A6CDF29476B2C8DE4FA6EBB4745` |
| `08-post-commit.log` | `FE83A4BE3F596DE4FA1DBF879EE1797E78CA4A52234170F9BA6F7B244CD4E6EA` |
| `qa_fix_demo.py` | `CE1C232F956816BB3613783752619CFD6E8C98934D3292E0EBA835071816B14B` |

## Giới hạn

- PASS chỉ cho SQLite/CLI ngoại tuyến và dữ liệu tổng hợp trên máy cục bộ.
- Chưa xác minh HTTP, quyền/auth, UI, approve/reject, OpenCTI, lab, cloud hoặc dữ liệu thật.
- Đây là tự rà soát theo brief không gọi worker khác; QA cần chạy lại hai finding trên SHA mới để có xác nhận
  độc lập.
