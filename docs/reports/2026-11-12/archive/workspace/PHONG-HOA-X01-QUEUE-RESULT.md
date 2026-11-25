# Kết quả X01-DRAFT-QUEUE

Ngày kiểm: 10/11/2026. Trạng thái: **PASS phạm vi hàng đợi ngoại tuyến**, chờ Leader nghiệm thu.

## Git và phạm vi

- Checkout: `cti-platform-start`
- Base: `2959eb0540bd708eeae60fedd9d11b13d32b543b`
- Nhánh: `feat/x01-draft-queue-20261110`
- Commit: `d03fa10523b45b94182038b5b46fed8231319e6f`
- Diff: 7 file, 534 dòng thêm, 11 dòng bỏ.
- Checkout sạch sau commit (`git status --porcelain=v1`: 0 dòng).
- Không đổi schema SQLite, core/grounding, fixture W05 hoặc dependency.
- Không push, PR, merge, deploy, lab, cloud, HTTP, UI, quyền, approve/reject hoặc OpenCTI.

## Đã triển khai

- `list_drafts(db_path, *, limit=20, before_id=None, timeout=5.0)`:
  - chỉ đọc hàng `pending` bằng SQLite `mode=ro`;
  - `id DESC`, trang sau `id < before_id`, lấy `limit+1` để xác định cursor;
  - limit 1–100, cursor trong miền INTEGER SQLite, timeout hữu hạn không âm;
  - summary allowlist đúng 8 trường và không chứa text/items/evidence/findings;
  - kiểm payload/schema/hash/span, metadata cột, `created_at` ISO có múi giờ;
  - lỗi DB/JSON/cấu trúc trả `DraftStoreError`, không bỏ qua bản ghi lỗi.
- CLI `list --db ... --limit ... [--before-id ...] --output ...` ghi trang JSON, terminal chỉ in count/cursor.
- Guard output áp dụng cho cả `list` và `get`: chặn đường dẫn trùng, tương đương hoặc hard link cùng DB trước khi
  ghi. Đây cũng sửa ca `get` có thể tự ghi hỏng DB nếu output trỏ lại file SQLite.
- README, PROGRESS và hợp đồng W05 được cập nhật; hai chỉnh lý language pipe và giới hạn kind/status đã áp dụng.

## TDD và kiểm chứng

RED:

```text
25 failed, 4 passed, exit 1: chưa có list_drafts/CLI list và get chưa chặn output DB.
6 failed, exit 1: timeout chưa được kiểm hữu hạn và created_at hỏng chưa bị từ chối.
```

GREEN trên `.venv\Scripts\python.exe` Python 3.12.13:

```text
35 queue tests passed in 4.12s, exit 0 (sau commit)
77 store + queue tests passed in 7.79s, exit 0
192 full-suite tests passed in 10.96s, exit 0
ruff check .: exit 0
ruff format --check .: 90 files already formatted, exit 0
git diff --check: exit 0 trước và sau commit
```

Ca kiểm gồm 5 draft/3 trang, exact multiple, trang rỗng/một trang, cursor không tồn tại, non-pending,
insert xen giữa, Unicode/hash, limit/cursor/timeout sai, DB thiếu/hỏng/khóa, JSON/schema metadata hỏng, không rò
toàn văn, output cũ không bị ghi đè và hash DB không đổi qua lệnh đọc.

## Demo CLI qua tiến trình riêng

```text
save ID 1..5
list: [5,4], next=4
insert ID 6
list before 4: [3,2], next=2
list before 2: [1], next=null
reload first: [6,5]
get selected ID 3: exit 0
```

Kết quả kiểm:

```text
old_ids_exact=True
unique=True
summary_safe=True
first_read_db_unchanged=True
later_reads_db_unchanged=True
```

Mẫu trang đầu: `PHONG-HOA-X01-QUEUE-SAMPLE.json`, SHA-256
`D9D428D9509E89A8DD748CFDAFDFBD8892BC19D9CCA7E01BAF7EA24C4490BCD9`.

## Bằng chứng

Thư mục `x01-queue-evidence/` nằm ngoài repo; DB và JSON tạm không commit.

- `01-red.log` — `CFF30AFBB6E3A15570831898DA5E6DC642FE33C599404C46253B199F717AFF76`
- `06-final-store-queue.log` — `EFED5AFA322668A8D61ABDA319AD48F16322D95052B9717F4E072EC5F5E3758E`
- `07-final-py312-suite.log` — `2EF82F404F8B1A19432EBFFA28E2AE954B60C5AB1F53D38868B620BFE97D6ECB`
- `08-static-checks.log` — `0A77A6E3E46587D01AB93127F9E99B38D501A4BC2522B0C3A78E3EC2C47B046B`
- `09-cli-demo.log` — `349D72527FDE442A1CC61F1B73A960A2E7A8734881C8046AC4F29EB71A23947C`
- `10-self-review.log` — `7BD061BE0EF9E5A3BF006BFD0102DDA21E0D53B4BDA401E849EBAB6856B70FE6`
- `11-post-commit-queue.log` — `AAE5897E9F21B4EFA035AB314BD62BB44F242C52494AC92248F3A3D516D21059`
- `12-post-commit-git.log` — `4CF38249FAE61A47CB3DB2A29D0B484BE9A86680A59C82382714DE85885CBF7B`

Task cấm gọi worker khác nên lượt review cuối là self-review của tác giả, yếu hơn reviewer độc lập; không có finding
Critical/Important/Minor còn mở trong phạm vi.

## Giới hạn

Cursor bảo toàn hướng đi về ID cũ khi có insert mới nhưng không tạo snapshot chung qua nhiều lần đọc. Chưa có
HTTP, auth/quyền Analyst/Admin, filter khác pending, tìm kiếm, update/audit, approve/reject, OpenCTI, UI hoặc lab.
