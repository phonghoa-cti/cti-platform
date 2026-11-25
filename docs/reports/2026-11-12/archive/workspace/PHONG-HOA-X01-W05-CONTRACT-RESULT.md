# Kết quả X01-W05-CONTRACT / Bước 3

Ngày kiểm: 10/11/2026. Trạng thái: **PASS phạm vi tài liệu và fixture cục bộ**, chờ Leader nghiệm thu.

## Git và phạm vi

- Checkout: `cti-platform-start`
- Base: `165c6ca8abd2555348ad323e616dc6cf10b6f199`
- Nhánh: `docs/x01-w05-contract-20261110`
- Commit: `2959eb0540bd708eeae60fedd9d11b13d32b543b`
- Diff: 9 file, 344 dòng thêm, 3 dòng bỏ.
- Checkout sạch sau commit (`git status --porcelain=v1`: 0 dòng).
- Chỉ sửa tài liệu và ba JSON tổng hợp; không sửa runtime, test hoặc dependency.
- Không push, PR, merge, deploy, lab, cloud, HTTP, OpenCTI hoặc UI.

## Đầu ra

1. `docs/specs/W05-draft-offline-contract.md`
   - Bảng đầy đủ draft mới/draft đã lưu, source, item và finding.
   - Phân biệt trạng thái draft/item, `keep` với quyết định người duyệt, span null và schema thực tế/tương lai.
   - Quy ước hash text UTF-8, Unicode code point và ma trận khoảng trống tích hợp.
2. `docs/design/W05-draft-handoff.md`
   - Gói sẵn bàn giao cho Antigravity: người dùng, luồng, empty/error/permission/pending/no-span,
     render text an toàn, accessibility và ranh giới backend.
   - Chưa gửi hoặc thực thi vì Antigravity chưa có trong roster.
3. `extractor/draft/examples/`
   - `01-regular.json`: Unicode/emoji, IOC kept.
   - `02-warning-allowlist-rejected.json`: findings, kept, allowlist và rejected. Item rejected được thêm thủ công
     vào fixture đầu vào để kiểm hợp đồng, không phải regex tự trích.
   - `03-empty.json`: text/items rỗng.
   - `README.md`: nguồn gốc, cách dùng và giới hạn.
4. Đã liên kết phụ lục từ `docs/specs/api-portal.md`, `extractor/draft/README.md` và cập nhật
   `docs/PROGRESS.md` đúng trạng thái chưa triển khai.

## Kiểm chứng đã chạy

Môi trường: `.venv\Scripts\python.exe` Python 3.12.13; Node `v24.22.1` có sẵn.

| Kiểm tra | Kết quả |
|---|---|
| Tạo ba draft tổng hợp bằng builder hiện có | 3 file đầu vào, exit 0 |
| CLI save/get qua SQLite | ID 1/2/3, mọi lệnh exit 0 |
| Parse + exact top/item/finding/source keys | 3/3 PASS |
| `source.sha256 == SHA-256(text UTF-8)` | 3/3 PASS |
| Span khác null cắt đúng evidence | PASS |
| Save/get lại từ ba payload, bỏ metadata store | 3/3 `exact_payload=True`, exit 0 |
| Python Unicode | `[0,58)` khớp quote, exit 0 |
| JavaScript Unicode | `Array.from(...).slice(...)` khớp; `String.slice` trực tiếp không khớp, exit 0 |
| Liên kết tương đối | 6 Markdown, 9 link cục bộ, exit 0 |
| Phạm vi staged | đúng 9 file docs/fixtures, không runtime/test/dependency |
| `git diff --check` | exit 0 trước và sau commit |

Không chạy lại toàn suite vì commit chỉ thay docs/fixtures. Bằng chứng base ngay trước task là 157 test đạt trên
Python 3.12.13; task này không coi kết quả đó là suite vừa chạy.

## Bằng chứng

Thư mục: `x01-w05-contract-evidence/` (ngoài repo; DB và đầu vào tạm không commit).

- `01-build-synthetic-inputs.log` — SHA-256 `06087778636BAE2EBA9F3F4AF298257E1AAFBDA7810245FCA5744759EDC963B0`
- `02-save-get-roundtrip.log` — `2F1E73800B932C8ACFAFD286D2756ECDBEDC64F4C7691492FCEF746E69C8851D`
- `03-contract-validation.log` — `672F6816713B547EAD4A59F5EADEDD8967AB4294BF0C3F2F7D3BEDA2413ECD48`
- `04-unicode-python-js.log` — `C5F20BB68E69C3AFC11B18D1E72B5053E4419B39E6DDF48E70B632020D6B8425`
- `05-links-and-files.log` — `29F227234C0E6BC8CC9E8807A6ECB57DD7EBCFE921F3633583012F8AD96E3856`
- `06-git-scope-and-diff-check.log` — `434C52FC7FCFBECEA7DE4904F56A49A744DD94073D8EFDA5FEA5C1AE8A071E0C`
- `07-post-commit-git.log` — `844AA5D083D5073ED8811ABCABC8B02BB68DD424DD5D969AE841F930385BA1C8`

## Khoảng trống còn lại

Chưa có danh sách/phân trang HTTP, đọc chi tiết qua HTTP, xác thực/quyền Analyst/Admin, schema allowlist tại
biên API, lịch sử sửa/audit, approve/reject, chống tự duyệt, người đề xuất/người duyệt, đo thay đổi, tích hợp
OpenCTI hoặc UI W05. TLP/injection warning chưa phải phép gửi cloud hay bằng chứng dữ liệu an toàn.
