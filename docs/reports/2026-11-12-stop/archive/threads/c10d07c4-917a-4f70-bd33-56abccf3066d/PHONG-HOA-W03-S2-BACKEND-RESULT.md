# W03-S2 Backend — kết quả

Ngày 12/11/2026. Base `4a8f409fe50d861797c49d1c0a3bb48c30ac2fa7`.
Commit `82f8a6acc8f357645f7105a2cc84b46bf58f4e4f` (`feat: add W03 CVE status read model`).
Branch `feat/w03-status-s2-backend-20261112`; tree sạch sau commit.

## Kết quả

### PASS

- Thêm opt-in `GET /api/cves/status-view`; auth/role chạy sớm. Leader có `asset_id` hoặc `status` bị 403 trước
  dataset/SQLite; Leader-only chỉ nhận item W03-R lược và năm field summary. Mixed role nhận detail.
- Ghép status theo relation chính xác; unset/null, stale review, OR multi-relation, inactive/no-match/key cũ không
  tạo relation. Lọc status trước phân trang; rank W03-R giữ nguyên; counts trước filter/paging.
- `actionable_cves` và KEV quá hạn dùng ngày UTC lấy một lần/request. Cursor riêng canonical không chứa ngày trong
  context; dataset/Technology/status/date drift trả 409; malformed/cross-route/context/after sai trả 422.
- Dataset validate một lần. Technology + status đọc qua cùng connection/transaction SQLite `mode=ro`; schema và
  mọi status row được validate fail closed. GET không migration/DDL/audit/write. Test DB tạm WAL dùng writer thật
  commit giữa hai SELECT, không sleep/poll, và reader vẫn thấy snapshot cũ nhất quán.
- Cap UTF-8 1 MiB, 404 asset detail, 503 row/schema/cap/dependency và header no-store/Vary đã có test.
- Fixture thực từ API đủ envelope: `w03-status-view-detail.json`, `w03-status-view-leader.json`,
  `w03-status-view-error.json`; test khóa exact wire.
- TDD RED được quan sát trước implementation: 7/7 fail do `create_app` chưa nhận injection S2; raw tại
  `w03-s2-backend-evidence/01-red.txt`. GREEN sau commit: 127/127 test S2 + W03-R + W03-S1, exit 0.
- Ruff check/format đúng ba file và `git diff --check base..HEAD` exit 0; tree sạch.

### FAIL ngoài phạm vi

- Full suite: 819 pass, 4 fail, exit 1. Bốn test `extractor/tests/test_stix_export.py` fail vì venv hiện có thiếu
  package/executable `stix2-validator==3.3.2`; brief cấm đổi dependency. Không có failure W03 trong full run.

### UNVERIFIED

- Gateway/frontend/browser, feed CISA/OpenCTI, Cloudflare/JWKS/HTTPS thật, lab và production.
- Status `patched/not_affected` là ghi nhận người dùng, không chứng minh kỹ thuật rằng hệ thống đã vá hoặc không
  ảnh hưởng.

## Lệnh và bằng chứng

- `w03-s2-backend-evidence/01-red.txt`: RED exit 1.
- `w03-s2-backend-evidence/02-targeted-green.txt`: 127 passed, exit 0.
- `w03-s2-backend-evidence/03-full-suite.txt`: 819 passed/4 failed do validator thiếu, exit 1.
- `w03-s2-backend-evidence/04-quality-git.txt`: Ruff, format, diff-check, SHA, diff stat và clean status.

Venv checkout hiện tại không tồn tại; dùng Python API đã khóa sẵn tại sibling
`..\cti-w03-read-backend\.venv\Scripts\python.exe`, không cài/đổi dependency.

## Giải thích cho người mới

Read model là API chỉ đọc ghép dữ liệu từ nhiều bảng thành một màn nhìn nhất quán. Snapshot là ảnh dữ liệu tại
một thời điểm; cursor mang dấu vân tay snapshot nên trang sau không âm thầm trộn dữ liệu mới. Relation status là
trạng thái của đúng cặp CVE–công nghệ, không phải một nhãn chung cho toàn CVE. Projection lược giúp Leader xem số
tổng hợp mà không nhận chi tiết tài sản hoặc lịch sử nhạy cảm.
