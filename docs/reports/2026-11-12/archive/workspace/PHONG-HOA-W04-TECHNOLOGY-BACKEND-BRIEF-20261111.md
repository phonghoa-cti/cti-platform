# W04-TECHNOLOGY-BACKEND

CTI Backend, một Sol medium trực tiếp; không giao bot/worker khác. Root `$WORKSPACE`.

## Mục tiêu/base

CRUD technology cục bộ/in-process theo **`PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md`**, đọc trước khi viết test. Contract Leader thay các lựa chọn wire/normalization/error còn mở trong nghiên cứu. Tái dùng nghiên cứu `PHONG-HOA-W04-TECHNOLOGY-RESEARCH-20261111.md`; không nghiên cứu kiến trúc lại.

Tạo tree mới `cti-w04-technology-backend`, branch `feat/w04-technology-backend-20261111`, từ accepted `8a767314b654d39c1ddc2995b7919c44a5b7027a`. Kiểm AGENTS/PROGRESS/spec đúng ref; không reset/xóa tree có sẵn, không chạm source/integration/Frontend tree.

## Allowlist và cách làm

- Thêm `portal_api/technologies.py`, tests `test_technologies*.py` và fixture tổng hợp liên quan; thêm model mới ở `portal_api/schemas.py`; wiring opt-in/route ở `portal_api/app.py`.
- Viết `docs/specs/W04-technology-local-contract.md` theo quyết định Leader, cập nhật mục riêng trong `docs/PROGRESS.md`.
- Không sửa `assets.py`, `ioc_lookup.py`, core/auth/settings, model Asset cũ, tests W02/domain cũ, dependency, gateway/runner, UI, RUNS/plan. Nếu blocker thật cần ngoài allowlist, trả repro + đề xuất hẹp cho Leader; không sửa lén.
- RED trước, GREEN sau. TechnologyStore riêng, schema additive transactional/idempotent, validate read-back và output trước commit, actor512, strict safe integers, duplicate classifier chính xác. Không biến lỗi audit thành duplicate; không dùng executescript commit sớm. Không refactor chung để giảm vài dòng.

## Kiểm rủi ro và bàn giao

1. Fresh/legacy W04 DB giữ nguyên row/audit; idempotent; partial/schema/index/marker hỏng; fault giữa DDL rollback thật. Verify close/lock cleanup.
2. Validation/bounds/code points/control/Cf/surrogate, trim+casefold, software_version giữ nguyên, duplicate update/create, soft-delete/recreate, zero/bool/float/string/overflow IDs và expected_version.
3. CRUD, quyền IT/analyst/admin/multi/leader/thiếu token, no-store/Vary; auth/role/Origin trước body/query/DB;413/415/422 đúng contract; unknown query/duplicate query.
4. Before/after audit, subject512 được/513 bị từ chối không ghi, record version overflow, read row/key corruption, 1000/1001; audit trigger/UNIQUE ở bảng khác không commit, true identity duplicate vẫn409. Concurrent writer/stale không lost update.
5. Regression technology create/update/delete không đổi W02/allowlist/asset_match. Chạy focused technology tests + existing asset/W02 suites một lần trên HEAD cuối, không full portal/UI/browser.
6. Ruff check/format delta, diff-check, base/HEAD/clean status. Dùng venv có pytest của dự án, không Python PATH hoặc install; ghi rõ interpreter/cwd. Nếu target chưa có venv, dùng absolute interpreter venv đã có tại `cti-w04-assets-local` hoặc `cti-w02-lookup-api` với PYTHONPATH target được xác nhận; không vô tình import source tree.

Trả fixture JSON wire technology created/list/duplicate/conflict/unavailable + hash cho Frontend, không tự gửi hoặc tích hợp với họ. Root report `PHONG-HOA-W04-TECHNOLOGY-BACKEND-RESULT.md`, evidence `w04-technology-backend-evidence/`; commit local/tree sạch; exit/count/RED-GREEN đúng nguyên nhân. Không push/PR/merge/deploy, browser/lab/secret/service ngoài.
