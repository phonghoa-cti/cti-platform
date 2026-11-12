# W05-EDIT-IMPLEMENT — kết quả core/store selection

Ngày kiểm: 11/11/2026 (UTC+07). Kết luận: **PASS core-only sau rework R1–R3**. Không nối
API/UI/OpenCTI.

## Git và phạm vi

- Base: `d94afb1e24929f64f82a921cd29307be175fb04e`
- Branch: `feat/w05-selection-local-20261111`
- HEAD: `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`
- Worktree: `$WORKSPACE\cti-w05-selection`
- Diff từ base: 6 file, `+1063/-28`; rework từ `cf7120a`: 2 file, `+201/-9`; tree sạch sau commit.
- Không sửa `portal_api/**`, `portal/web/**`, harness, dependency/lock, extractor AI, RUNS hoặc tree nguồn.

## Kết quả kỹ thuật

- Store schema v2 thêm `selection_version`, `draft_selection_audit` và snapshot/hash ở final audit.
- `get_effective_selection` đọc bằng URI read-only + read transaction; `save_selection` dùng actor trusted,
  strict index, eligibility, no-op và optimistic concurrency.
- v0/v1→v2 chạy trong một transaction; v2 idempotent; schema/index/FK/check và canonical JSON/hash được validate.
- Approve và reject mới đều tham chiếu snapshot chính xác; empty approve bị từ chối; payload/source/evidence không đổi.
- Count tách `ai_extracted_count`, `ai_eligible_count`, `human_deselected_count`, `selection_save_count`.

## RED / GREEN / regression

| Kiểm | Kết quả | Bằng chứng |
|---|---:|---|
| RED selection trước implementation | exit 1, 11 failed đúng vì API/table chưa có | `w05-selection-evidence/01-red-selection.log` |
| Target cũ trước review | exit 0, **103** dấu PASS, không phải 104 như báo cáo ban đầu | `w05-selection-evidence/02-green-targeted.log` |
| Full Python suite sau thay đổi cuối | exit 0, 399 passed | `w05-selection-evidence/03-full-python.log` |
| Ruff check | exit 0 | `w05-selection-evidence/05-ruff-check.log` |
| Ruff format check | exit 0 | `w05-selection-evidence/06-format-check.log` |
| Git diff check | exit 0; chỉ cảnh báo LF→CRLF của Git | `w05-selection-evidence/07-diff-check.log` |
| Demo SQLite tổng hợp | exit 0; DB temp tự dọn | `w05-selection-evidence/04-demo.log` |
| RED rework bằng probe Leader nguyên trạng | exit 1, 18 passed/6 failed đúng R1–R3 | `w05-selection-evidence/rework-r1-r3/01-red.log` |
| RED regression R1–R3 trong repo | exit 1, 18 passed/9 failed | `w05-selection-evidence/rework-r1-r3/02-repo-red.log` |
| Selection repo + probe sau sửa | exit 0, 37 passed | `w05-selection-evidence/rework-r1-r3/03-selection-probe-green.xml` |
| Probe Leader nguyên trạng | exit 0, 10 passed | `w05-selection-evidence/rework-r1-r3/04-leader-probe-green.log` |
| Selection/review/store/queue/CLI | exit 0, 186 passed | `w05-selection-evidence/rework-r1-r3/05-targeted-green.log` |
| Ruff / format / diff-check rework | exit 0 cả ba | `06-ruff-check.log`, `07-format-check.log`, `08-diff-check.log` trong thư mục rework |

Full suite có 88 test API baseline nhưng chỉ chứng minh regression draft chưa edit; không chứng minh API hỗ trợ
selection/version >1.

## Ma trận acceptance

| # | Trạng thái | Bằng chứng ngắn |
|---:|---|---|
| 1 | PASS | v0 và v1 migrate lên v2, payload giữ nguyên, schema/index/FK/check được validate |
| 2 | PASS | migrate v2 lần hai byte-idempotent trong test v1 |
| 3 | PASS | future/counterfeit/mixed schema fail closed; UNIQUE dư cột DESC và thiếu NOT NULL bị từ chối |
| 4 | PASS | get/list legacy chỉ đọc; v1 chỉ pending=0/terminal=1; selection/decision yêu cầu v2 |
| 5 | PASS | baseline chỉ lấy IOC keep=true/status=ok, selection version 0 |
| 6 | PASS | deselect/reselect canonical, event actor/time/hash và version liên tiếp |
| 7 | PASS | empty save được audit, empty approve nhận DraftPolicyError |
| 8 | PASS | duplicate/unknown/negative/bool/string/float/out-of-range không mutate |
| 9 | PASS | allowlist/keep=false không thể chọn lại; unsupported kept kind policy còn nguyên |
| 10 | PASS | no-op sau auth/pending/version không tăng version hoặc event |
| 11 | PASS | role/subject sai bị typed error trước DB mutation |
| 12 | PASS | creator được save/reject; self-approve vẫn bị chặn bởi regression cũ |
| 13 | PASS | approve sau save copy exact version/JSON/hash; result version=2 |
| 14 | PASS | approve baseline ghi canonical baseline snapshot |
| 15 | PASS | self approve/creator null/unsupported kind regressions qua |
| 16 | PASS | reject yêu cầu reason và ghi snapshot, selection event không đổi |
| 17 | PASS | hai save đồng bộ bằng Barrier: đúng một winner, một conflict, một event |
| 18 | PASS | save-vs-approve đồng bộ bằng Barrier: đúng một winner; audit/event coherent |
| 19 | PASS | save/decision terminal và stale no-op conflict, không thêm audit/event |
| 20 | PASS | trigger ép event INSERT fail rollback pointer/version/event |
| 21 | PASS | final audit INSERT và commit failure regression rollback state/audit |
| 22 | PASS | write connection bật FK; schema validator kiểm exact FK |
| 23 | PASS | test + demo xác nhận payload_json/source_sha256 byte-identical |
| 24 | PASS | rework targeted 186, probe Leader 10/10; full Python 399 là bằng chứng trước rework và không chạy lặp |

Read-interleaving đã được kiểm bằng WAL + hook đồng bộ: writer commit giữa hai query nhưng getter cũ vẫn trả
snapshot version 0 nhất quán, lần đọc sau trả version 1. Test nằm trong repo và probe Leader, không dùng sleep.
Các corruption thiếu event, pointer lệch, hash sai và index không eligible đều fail closed, byte DB không đổi.

## Demo tổng hợp

Demo có 3 IOC: 2 eligible và 1 allowlist excluded; lưu `[1]`, getter báo extracted=3/eligible=2/deselected=1,
approve version 2. Selection event và final audit cùng version 1, JSON `[1]`, SHA-256
`080a9ed428559ef602668b4c00f114f1a11c3f6b02a435f0bdc154578e4d7f22`; payload byte-identical. Một draft
khác reject sau save đạt version 2; draft selection rỗng bị từ chối approve. DB nằm trong thư mục tạm do script
tạo và đã được dọn.

## Chưa tích hợp / chưa kiểm

- API/parser hiện khóa review version 0/1, chưa có selection object và **không tương thích draft đã edit**.
- UI chưa hiển thị effective selection; không chạy browser/build.
- Chưa có auth production/JWKS thật, OpenCTI ingestion/version/license, lab/deploy, DB thật hoặc benchmark DB lớn.
- Không gọi mạng, model, cloud, secret; không push/PR/merge/deploy.

## Học thêm

- **Optimistic concurrency:** caller gửi version đã đọc; version lệch thì từ chối để không ghi đè thay đổi mới.
- **Canonical JSON:** một cách serialize duy nhất giúp cùng selection luôn cho cùng SHA-256.
- **Read transaction:** nhiều câu SELECT cùng nhìn một snapshot database nhất quán.
- **Atomic migration:** mọi thay đổi schema commit cùng nhau hoặc rollback toàn bộ khi lỗi.
