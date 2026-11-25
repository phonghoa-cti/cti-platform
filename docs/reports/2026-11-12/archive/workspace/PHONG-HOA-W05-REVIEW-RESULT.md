# Kết quả W05-B — quyết định cục bộ và audit draft SQLite

Ngày kiểm: 10/11/2026. Working tree: `cti-w05-backend`. Branch:
`feat/w05-local-review-20261110`. Base: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`.

## Kết quả

**PASS cục bộ** cho phạm vi W05-B offline. Commit:
`137749cab79906bca71e4eb920961048ef3cca3a` (`feat: add offline draft review decisions`).

- Payload draft 1.0 và `payload_json` giữ bất biến; review state/version và tác giả nằm ở metadata SQLite.
- `Actor` chỉ cho `analyst`/`admin`; chặn self-approve kể cả admin, chặn approve creator null, cho creator reject
  với lý do.
- Migration `user_version=1` chạy transaction, rollback khi schema/audit lỗi, idempotent khi chạy lại.
- `get/list` dùng `mode=ro`, không migration/không tạo DB; schema legacy hợp lệ được đọc pending/0/creator null.
- Approve/reject dùng `BEGIN IMMEDIATE`; update state/version và insert audit cùng transaction; stale/lặp/race chỉ
  một quyết định và một audit.
- Audit chỉ chứa metadata review; không có payload/text/items/evidence/findings. Audit SQLite chưa chống người có
  quyền sửa file DB.
- CLI get phân biệt `payload_status` với `review_status`/`review_version`; không có cờ actor tự khai.

## TDD và lệnh kiểm

Interpreter cho mọi lệnh Python:
`cti-platform-start\.venv\Scripts\python.exe` (Python 3.12.13), cwd `cti-w05-backend`.

| Giai đoạn | Lệnh rút gọn | Exit / kết quả |
|---|---|---|
| RED ban đầu | `python -m pytest -q extractor/tests/test_review.py` | `1`; 25 failed do thiếu review metadata/API/types/authorship |
| RED validation | `python -m pytest -o addopts= -q extractor/tests/test_review.py -k malformed_actor_and_decision_types` | `1`; 1 failed, 2 passed, 27 deselected; lộ `TypeError` thay vì lỗi input ổn định |
| RED mutation CLI | `python -m pytest -o addopts= -q extractor/tests/test_store_cli.py -k distinguishes_payload` khi tạm phục hồi stdout cũ | `1`; 1 failed, 23 deselected; chứng minh test bắt được nhập nhằng payload/review |
| Focused cuối | `python -m pytest -o addopts= -q test_review.py test_store.py test_queue.py test_store_cli.py test_queue_cli.py` (đường dẫn đầy đủ dưới `extractor/tests`) | `0`; **152 passed** trong 10.62s |
| Full suite, chạy đúng một lần sau focused green | `python -m pytest -o addopts= -q` | `0`; **266 passed** trong 13.89s |
| Lint | `python -m ruff check .` | `0`; All checks passed |
| Format | `python -m ruff format --check .` | `0`; 91 files already formatted |
| Evidence lint/format | `python -m ruff check/format --check ..\w05-review-evidence\demo_review.py` | `0` / `0` |
| Diff whitespace | `git diff --check` và `git diff --cached --check` | `0` / `0` |

Full suite được chạy trước lần thêm assertion CLI stdout cuối; sau thay đổi đó không chạy lại full suite theo yêu
cầu “full suite đúng một lần”. Focused cuối 152 test bao phủ toàn bộ store/review/queue/CLI đã thay đổi, rồi Ruff
được chạy lại và đạt.

## Demo và bằng chứng

Demo final dùng hai tiến trình Python khác PID, với `PYTHONPATH=cti-w05-backend\core;...\extractor`:

1. `demo_review.py write --db demo.sqlite --output write.json` → exit 0, PID 37172.
2. `demo_review.py read --db demo.sqlite --output read.json` → exit 0, PID 38508.

Quan sát trong `read.json`:

- review state: `approved`, `rejected`, `pending`;
- cả ba payload vẫn `status=pending`;
- queue chỉ còn draft pending ID 3;
- đúng hai audit metadata cho approve/reject;
- SHA-256 database trước/sau read cùng là
  `7dcc75325cd9119eae2d04896512180c6071330dba42bb01c445f4697ecd75c9`.

Artifact:

- `w05-review-evidence/RED.md`
- `w05-review-evidence/demo_review.py`
- `w05-review-evidence/demo.sqlite`
- `w05-review-evidence/write.json`
- `w05-review-evidence/read.json`

Hai lần gọi demo chuẩn bị đầu tiên exit 1 trước khi tạo DB: lần đầu thiếu `PYTHONPATH`, lần sau fixture thiếu đối số
`language`; script được sửa đúng nguyên nhân và lần chạy final ở trên đạt. Không dùng output lỗi làm evidence PASS.

## Git diff

- `10 files changed, 1217 insertions(+), 50 deletions(-)` so với base.
- File commit: `docs/PROGRESS.md`, hai spec W05/API, README/CLI draft, store core, bốn file test gồm
  `test_review.py` mới.
- `git status --short --branch` sau commit chỉ còn dòng branch, không có file bẩn.
- Evidence và báo cáo nằm ngoài Git tree nên không nằm trong commit.

## UNVERIFIED / ngoài phạm vi

- **UNVERIFIED:** HTTP/FastAPI endpoint, JWT/Cloudflare Access/API-key hash, role lookup server-side và 401/403.
- **UNVERIFIED:** UI/Playwright, chỉnh item và số liệu bỏ/thêm/sửa.
- **UNVERIFIED:** OpenCTI/STIX ingestion, outbox/retry remote, lab/VM/cloud/network và production deployment.
- **UNVERIFIED:** audit chống sửa file DB, backup/restore và tải đa tiến trình ngoài race/lock test SQLite cục bộ.
- Không push, PR, merge hoặc deploy; không gọi Internet, LLM, OpenCTI, lab hay secret.

## Rework reviewer — 11/11/2026

Đã sửa đúng hai finding trên HEAD `137749cab79906bca71e4eb920961048ef3cca3a`:

Commit rework: `91b5224c9a254865b2baa0259be5073a1ee79a47`
(`fix: validate review schema invariants`). Diff riêng rework: **4 files, +200/-4**.

1. Validator schema current không còn chỉ so tên cột. Nó kiểm `NOT NULL`/default, CHECK review state/version và
   audit action, UNIQUE `draft_audit(draft_id)`, FK tới `drafts(id)`, cùng index queue đúng
   `(review_status ASC, id DESC)` bằng `PRAGMA table_info/index_list/index_xinfo/foreign_key_list`; chỉ dùng
   `sqlite_master.sql` cho ba biểu thức CHECK có mục tiêu.
2. `get_draft()` từ chối bool, 0, số âm và ID vượt `2**63-1` trước database I/O; CLI trả lỗi ổn định, không
   traceback và không ghi đè output.

TDD RED được ghi thêm tại `w05-review-evidence/RED.md`: exit 1, **7 failed, 9 passed, 111 deselected**.

Kiểm chứng mới:

| Lệnh | Exit / kết quả |
|---|---|
| Test RED mục tiêu trước fix | `1`; 7 failed, 9 passed, 111 deselected |
| Test mục tiêu sau fix | `0`; 16 passed, 111 deselected |
| Focused changed tests trước format | `0`; 162 passed trong 10.98s |
| Full suite sau focused green | `0`; **277 passed** trong 16.13s |
| Focused cuối sau format | `0`; **162 passed** trong 11.69s |
| `python -m ruff check .` | `0`; All checks passed |
| `python -m ruff format --check .` | `0`; 91 files already formatted |

Rework không thay đổi các mục UNVERIFIED và không thêm HTTP/UI/OpenCTI/network.

## Rework reviewer FK ghép — 11/11/2026

Trên HEAD `91b5224c9a254865b2baa0259be5073a1ee79a47`, regression mới dựng schema current hợp lệ ở mọi invariant
khác nhưng dùng FK ghép `(draft_id, reason) -> drafts(id, created_by_subject)`. RED chứng minh validator cũ chỉ
nhìn thấy mapping đầu tiên nên chấp nhận sai. `_has_audit_foreign_key()` nay nhóm `PRAGMA foreign_key_list`
theo FK id và chỉ chấp nhận đúng một nhóm có đúng một mapping `draft_id -> drafts.id`; FK ghép hoặc FK thừa đều
bị từ chối trước write.

| Lệnh | Exit / kết quả |
|---|---|
| RED regression FK ghép | `1`; **1 failed, 35 deselected** |
| Regression FK ghép sau fix | `0`; **1 passed, 35 deselected** trong 0.14s |
| Focused changed tests trước format | `0`; **163 passed** trong 10.72s |
| Full suite sau focused green | `0`; **278 passed** trong 13.94s |
| Focused cuối sau format | `0`; **163 passed** trong 10.50s |
| `python -m ruff check .` | `0`; All checks passed |
| `python -m ruff format --check .` | `0`; 91 files already formatted |
| `git diff --check` | `0` |

Commit rework: `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`
(`fix: reject composite audit foreign key`). Diff riêng: **2 files, +22/-6**. Sau commit,
`git status --short --branch` chỉ còn dòng branch. Các mục UNVERIFIED giữ nguyên.

## Học thêm

- **Optimistic concurrency**: caller gửi version đã đọc; version stale bị từ chối để không ghi đè quyết định khác.
- **Atomic transaction**: state và audit cùng commit hoặc cùng rollback, nên không có trạng thái nửa chừng.
- **Opaque subject**: định danh ổn định nhưng core không suy diễn nó là email hay danh tính đã xác thực.
- **Migration idempotent**: chạy lại migration đã hoàn tất không đổi record hoặc audit.
