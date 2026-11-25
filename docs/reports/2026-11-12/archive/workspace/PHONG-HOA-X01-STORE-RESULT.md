# Kết quả X01-DRAFT-STORE / Bước 2

Ngày kiểm: 10/11/2026. Trạng thái: **PASS sau sửa hai lỗi review**, chờ Leader nghiệm thu lại.

## Git và phạm vi

- Checkout: `cti-platform-start`
- Nhánh: `feat/x01-draft-store-20261110`
- Base sửa review: `2cadea3048f7f0072938f7988197afc33e36db52`
- Commit: `165c6ca8abd2555348ad323e616dc6cf10b6f199`
- Diff sửa review: 5 file, 173 dòng thêm, 7 dòng bỏ.
- Checkout sau commit sạch (`git status --porcelain=v1` không có dòng nào).
- Không push, tạo PR, merge, deploy, gọi mạng/model hoặc dùng lab.

## Hai lỗi đã sửa

### R1 — kiểu dữ liệu `language` và `tlp`

Store kiểm hai trường là chuỗi trước khi kiểm membership. `list`, `object`, `null` và số đều trả
`DraftStoreError` nêu đúng tên trường. CLI bắt lỗi dự kiến, exit 1, không traceback và không in nội dung nguồn.
Dữ liệu sai bị từ chối trước khi mở DB: DB mới không được tạo, bản ghi cũ không đổi.

### R2 — IOC phải nằm trong đúng span evidence

Với item `kind=ioc`, `keep=true`, store dùng lại `phonghoa_core.ioc.normalize` và
`phonghoa_extractor.evidence.find_ioc_occurrences`. IOC chuẩn hóa phải đúng `type` và có một token nguyên vẹn
nằm trọn trong chính `[start, end)` đã khai báo trên toàn nguồn. Không viết regex mới, không sửa grounding.

Hai ca `[0,0]/''` và `[0,9]/'Synthetic'` bị từ chối. Ca cắt `evil.example` từ
`not-evil.example`, type sai và value không có trong span cũng bị từ chối. Lần xuất hiện hợp lệ về sau vẫn được
nhận; draft Unicode, defang, URL, IPv6 và item rejected `span=null` vẫn lưu/đọc nguyên vẹn.

## TDD và kiểm chứng

RED trước khi sửa, đúng Python 3.12.13:

```text
13 failed, exit 1
- list/object gây TypeError và CLI traceback
- span rỗng/không liên quan, substring hostname, type/value sai vẫn được lưu
```

GREEN cuối:

```text
Python 3.12.13
42 passed in 4.08s (hai file test store/CLI), exit 0
157 passed in 7.37s (toàn suite), exit 0
ruff check .: exit 0
ruff format --check .: 85 files already formatted, exit 0
git diff --check: exit 0
```

Các test R1 chạy cả API và CLI cho 8 tổ hợp trường/kiểu, đồng thời kiểm DB mới, dữ liệu cũ, traceback và rò
nội dung. Các test R2 kiểm hai probe review, biên token hostname, type/value, occurrence lặp, Unicode/defang,
URL/IPv6 và bảo toàn payload.

## Demo tạo → lưu → đọc

Ba tiến trình CLI riêng chạy trên dữ liệu tổng hợp:

```text
build_exit=0 save_exit=0 get_exit=0 verify_exit=0
id=1 created_at=2026-11-10T15:10:30.770248+00:00 items=3 exact_payload=True spans=True
```

Kết quả đọc lại nằm tại `PHONG-HOA-X01-STORE-SAMPLE.json`; DB demo và đầu vào nằm ngoài repo trong
`x01-store-evidence/review-demo-20261110/`.

## Bằng chứng

- `x01-store-evidence/12-review-red.log`: RED, SHA-256
  `AC7D9E3B83F9F2F1CC624E721285C1ED20DE0D85369B2E0070F2B7BD64AEBEC5`.
- `x01-store-evidence/13-review-green-targeted.log`: GREEN đầu tiên sau sửa.
- `x01-store-evidence/14-review-final-py312-tests.log`: 157 test, SHA-256
  `0A41255ED505096072870692F79A4B61BF86C55EFBDA70A251F872B0A7D9E01B`.
- `x01-store-evidence/15-review-static-checks.log`: Ruff/format/diff-check, SHA-256
  `2B0B06B9028A9E78D7118F72B381C0632F3F2BB84B7F6E816E143FF4C665466B`.
- `x01-store-evidence/16-review-demo.log`: demo, SHA-256
  `FE04D2DACBD3A7961EC0A243C7C28DCBDC91EC2E691CFA6F09A251F950472380`.
- `x01-store-evidence/17-review-post-commit-targeted.log`: 42 test sau commit, exit 0.
- `PHONG-HOA-X01-STORE-SAMPLE.json`: SHA-256
  `F3771EEDC13A69D6F8A3940052A598CE18BF7BBC80CC35F499A3D8D04048D09C`.
- Log `01`–`11` được giữ nguyên làm bằng chứng lịch sử của triển khai và review trước đó.

## Giới hạn còn lại

Đây chưa phải toàn bộ X01. Chưa có approve/reject, HTTP/auth, portal UI, tích hợp W05/OpenCTI, model/LLM,
dataset thật hai người gán nhãn, đánh giá TTP hoặc kiểm lab. Bước 3 chỉ bắt đầu sau khi Leader nghiệm thu lại
commit này.
