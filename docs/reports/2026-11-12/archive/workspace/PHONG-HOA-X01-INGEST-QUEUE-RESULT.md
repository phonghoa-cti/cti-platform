# Kết quả X01-INGEST-QUEUE-IMPLEMENT

Ngày 11/11/2026. Kết luận sau rework F1: **PASS cục bộ/offline tại commit
`fc08897a240d9e55198b1a8166b21e8e7caf7213`**. Không phải bằng chứng browser, OpenCTI, lab hay production.

## Rework F1 — tên chứa ký tự điều khiển Unicode

QA phát hiện U+0085/U+009F (nhóm Unicode `Cc`) lọt qua kiểm tra tên và tạo draft. Library và CLI nay từ
chối toàn bộ `Cc` trước khi mở database; slash/backslash vẫn bị chặn, còn tên tiếng Việt, khoảng trắng và emoji
vẫn hợp lệ. Không dùng `isprintable()` vì cách đó sẽ chặn cả khoảng trắng hợp lệ.

| Thao tác | Mong đợi | Thực tế tại HEAD | Trạng thái |
|---|---|---|---|
| Library nhận tên có U+0085/U+009F | Từ chối, database giữ nguyên từng byte | `invalid_input_metadata`; byte database trước/sau bằng nhau | ĐẠT |
| CLI nhận tên có U+0085/U+009F | Exit 1, thông báo an toàn, database không đổi | Exit 1; stdout rỗng; `Lỗi: invalid_input_metadata`; byte database bằng nhau | ĐẠT |
| Tên có C0/DEL | Tiếp tục bị từ chối | U+0000, U+001F, U+007F đều bị từ chối | ĐẠT |
| Tên `Báo cáo Việt Nam 😀 01.txt` | Nhập bình thường | `imported`, provenance giữ đúng tên | ĐẠT |
| Tên gây nhầm thị giác nhưng không thuộc `Cc` | Không tuyên bố đã giải quyết | Không kiểm ngoài phạm vi F1 | CHƯA KIỂM |

RED trước sửa: 4 fail/4 pass, đúng U+0085/U+009F lọt qua library và CLI. GREEN mục tiêu: 8 pass.
Toàn bộ hai file regression ingest: 34 pass. Log mới ở
[`rework-f1`](x01-ingest-queue-evidence/rework-f1/commands.md).

## Đã làm

- Thêm CLI/library nhập một envelope TXT/PDF `x01-local-ingest/1.0` đã có vào queue W05.
- Creator bắt buộc từ caller; envelope không được tự khai identity. Payload draft, `keep`, evidence, findings và text
  được lưu bất biến.
- Nâng SQLite từ schema v2 lên v3 bằng migration riêng, rồi ghi draft+provenance nguyên tử trong transaction sau.
- Retry exact envelope cùng creator trả `duplicate`; creator khác conflict không đổi owner và không lộ draft ID.
- Reader W05 chấp nhận v2/v3 mà không migrate; review/selection/STIX giữ semantics cũ. Self-approve vẫn bị cấm.
- JSON/path/Unicode/cap/range được fail-closed; CLI chỉ lộ mã lỗi hữu hạn, không raw CTI/path/SQL/traceback.

## Demo synthetic tại đúng HEAD

| Thao tác | Mong đợi | Thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| Import envelope TXT Unicode | Tạo draft pending + provenance | `draft_id=2`, `imported`; queue/get/provenance đọc được | ĐẠT | `demo-summary.json`, `synthetic-demo.sqlite` |
| Import envelope PDF 2 trang | Giữ raw/canonical/range | `draft_id=3`, ranges `[[0,22],[25,46]]` | ĐẠT | `demo-summary.json`, PDF envelope |
| Retry cùng creator | Không tạo bản sao | `draft_id=2`, `duplicate` | ĐẠT | `demo-summary.json` |
| Cùng envelope, creator khác | Conflict đóng, không đổi dữ liệu | `Lỗi: duplicate_creator_conflict` | ĐẠT | `demo-summary.json` |
| Creator tự approve | Bị policy chặn | `self_approve=blocked` | ĐẠT | `demo-summary.json` |
| Analyst khác approve | Final approved, reviewer khác creator | reviewer `analyst-reviewer` | ĐẠT | `demo-summary.json`, DB synthetic |
| STIX qua core | Chỉ IOC đã duyệt; bundle hợp lệ nội bộ | 4 object, chứa `evil.example`, selected `[0]` | ĐẠT | `synthetic-approved-bundle.json` |
| Browser cùng luồng | Không thuộc scope | Không chạy | CHƯA KIỂM | — |
| OpenCTI/lab/production | Không thuộc scope | Không chạy | CHƯA KIỂM | — |

Demo dùng CLI import và core list/get/provenance/review/STIX, không mở listener, browser, mạng, model hay OpenCTI.
`raw_sha256` PDF là provenance tự khai; importer không đọc lại byte PDF. Kiểm tra integrity chỉ phát hiện bất nhất
nội bộ, không chứng minh envelope chưa bị sửa rồi tính lại hash nhất quán.

## Kiểm chứng

| Gate | Kết quả mới nhất |
|---|---|
| Importer + CLI | 34 passed, exit 0 tại rework HEAD |
| Store/queue/review/selection | 205 passed, exit 0 |
| STIX | 77 passed, exit 0 |
| Portal API in-process | 115 passed, exit 0 |
| Full pytest repo | 553 passed, exit 0 ở commit ban đầu; không chạy lại trong rework F1 theo kế hoạch song song |
| Ruff check / format | exit 0 / exit 0 |
| `git diff --check` | exit 0 |
| Demo synthetic tại HEAD | exit 0 |

Unit test chứng minh contract local trong tập ca đã chạy, không đại diện cho toàn hệ thống. Lệnh và exit cụ thể ở
[`commands.md`](x01-ingest-queue-evidence/commands.md).

## Git, nguồn và giới hạn

- Branch: `feat/x01-ingest-queue-20261111`.
- Base: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Commit ban đầu: `db36ec01b765dfd515c1d0ef13642a693b777172`.
- Commit rework F1: `fc08897a240d9e55198b1a8166b21e8e7caf7213`.
- Diff rework F1: 4 file, `+57/-2`; đúng allowlist, target sạch sau commit.
- W05 source giữ nguyên/sạch tại `cf9e609`; producer giữ nguyên/sạch tại `8a167586`.
- Không push/PR/merge/deploy; không nâng dependency; không gọi cloud/model/OpenCTI/lab/VM.

## Học thêm

- **Idempotency**: gửi lại cùng thao tác không tạo thêm bản ghi, nhưng không đồng nghĩa exactly-once khi process chết.
- **Provenance**: metadata mô tả nguồn và hash; với PDF ở đây nó là tuyên bố được lưu, chưa phải chữ ký xác thực.
- **Migration transaction**: đổi schema trong một giao dịch để lỗi có thể rollback cả DDL lẫn version.
- **Read-only compatibility**: binary mới đọc cả v2/v3 mà không tự sửa database chỉ vì có người xem dữ liệu.
