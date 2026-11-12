# W04-ASSETS-IMPLEMENT — kết quả Backend cục bộ

Ngày kiểm: 11/11/2026. Trạng thái: **PASS cục bộ / in-process**.

## Kết quả

- Thêm kho SQLite opt-in cho asset `domain` và `ip_range`, canonical/validation, partial unique index,
  optimistic version, soft delete và audit before/after trong cùng transaction.
- Thêm CRUD `/api/assets` với JWT/role phía server, Origin cho mutation, streaming body cap 8 KiB,
  lỗi ổn định, no-store/Vary và giới hạn hữu hạn.
- Nối snapshot asset vào W02 mà không bật mặc định: match domain/IP/URL/email, effective allowlist giữ
  luật homepage URL, gắn asset vào allowlisted/not_found/found và tính lại score từ facts visible.
- Thêm contract, tiến độ, test SQLite/JWT/in-process và 3 response fixture + 1 error fixture cho bước
  Frontend kế tiếp.

## Git và allowlist

- Base: `aeff542a20ecc6fe436a0884801fdd69ab0435f6`
- HEAD/commit local: `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`
- Branch: `feat/w04-assets-local-20261111`
- Commits: `28a7532 feat: add local domain and CIDR assets`; `bfd3272 fix: use asset error for
  invalid identifiers`.
- Diff lũy kế: 8 file, 1.000 insertions, 21 deletions. Rework riêng: 2 file, 45 insertions,
  7 deletions.
- File đổi đúng allowlist: `portal_api/assets.py`, nối `app.py`/`schemas.py`/`ioc_lookup.py`, hai file
  test, contract mới và `docs/PROGRESS.md`. Không có file ngoài allowlist; không sửa RUNS.
- `git status --porcelain` sau commit: rỗng (tree sạch).

## Môi trường thực thi

Target không có `.venv`. Theo brief, dùng interpreter chỉ đọc:

`$WORKSPACE\cti-w02-lookup-api\.venv\Scripts\python.exe`

- Python `3.12.13`; Ruff `0.17.4`.
- CWD là worktree `cti-w04-assets-local`.
- `PYTHONPATH` trỏ lần lượt target root, target `core`, target `extractor`.
- Module thực tế: `portal_api` và `phonghoa_core` đều được load từ worktree target, không từ tree nguồn.

## Lệnh và bằng chứng

Prefix chung cho lệnh Python:

```powershell
$env:PYTHONPATH = "$wt;$wt\core;$wt\extractor"
& $python -m <module> ...
```

| Trạng thái | Lệnh nguyên văn | Exit / kết quả | Raw evidence |
|---|---|---|---|
| EXPECTED RED | `& $python -m pytest portal_api/tests/test_assets_api.py -q` | exit 2; collection dừng đúng vì `portal_api.assets` chưa tồn tại | `01-red-assets-tests.txt` |
| PASS GREEN | `& $python -m pytest portal_api/tests/test_assets_api.py portal_api/tests/test_w02_ioc_api.py -q` | exit 0; 63/63 | `02-green-targeted-tests.txt` |
| PASS suite | `& $python -m pytest portal_api/tests -q` | exit 0; 197/197 tại cổng suite duy nhất | `03-portal-api-suite.txt` |
| RESOLVED | `& $python -m ruff check portal_api` | lần đầu exit 1 do import-only; đã sửa | `04-ruff-check.txt` |
| PASS lint | `& $python -m ruff check portal_api` | exit 0 | `15-final-ruff-check.txt` |
| PASS format | `& $python -m ruff format --check portal_api` | exit 0; 13 file formatted | `05-ruff-format-check.txt` |
| PASS whitespace | `git diff --check` | exit 0; chỉ có warning LF→CRLF của Git | `06-git-diff-check.txt` |
| PASS review regression | `& $python -m pytest portal_api/tests/test_assets_api.py -q` | exit 0; 18/18 sau bổ sung DB-failure và hidden-TLP | `14-targeted-review-regressions-final.txt` |
| PASS fixtures | `IocLookupResponse.model_validate_json(...)` cho 3 fixture và exact error assertion | exit 0; 3 response + 1 error | `09-fixture-validation-json-mode.txt` |

Hai lượt trung gian `10`/`12` ghi lỗi fixture/syntax test-only khi chỉnh import để Ruff không báo F811;
đã sửa dứt điểm, bằng chứng cuối là `14` và `15`. Không có test/lint fail chưa xử lý.

## Artifact

Thư mục: `w04-assets-evidence/`

- `fixture-allowlisted-asset.json`
- `fixture-not-found-url-asset.json`
- `fixture-found-url-asset.json`
- `fixture-error-assets-unavailable.json`
- Raw RED/GREEN/suite/lint/format/diff/env/allowlist/postcommit: `01` đến `17` như bảng trên.

## Rework finding: mã lỗi ID/version assets

Review tái hiện `PUT /api/assets/0` và `DELETE /api/assets/1?expected_version=0` trả nhầm
`invalid_request`. Rework thêm wrapper parser chỉ dùng cho assets; parser dùng chung của review/W02 không đổi.

| Trạng thái | Lệnh nguyên văn | Exit / kết quả | Raw evidence |
|---|---|---|---|
| EXPECTED RED | `& $python -m pytest portal_api/tests/test_assets_api.py -q -k "invalid_path_id or invalid_version"` | exit 1; 8/8 fail vì thực tế là `invalid_request` | `18-rework-red-invalid-asset-identifiers.txt` |
| PASS GREEN | cùng lệnh targeted trên | exit 0; 8/8 | `19-rework-green-invalid-asset-identifiers.txt` |
| PASS targeted cuối | `& $python -m pytest portal_api/tests/test_assets_api.py -q` | exit 0; 26/26 | `28-rework-final-assets-targeted-suite.txt` |
| PASS lint | `& $python -m ruff check portal_api` | exit 0 | `25-rework-final-ruff-check.txt` |
| PASS format | `& $python -m ruff format --check portal_api` | exit 0; 13 file formatted | `26-rework-final-ruff-format-check.txt` |
| PASS whitespace | `git diff --check` | exit 0; warning LF→CRLF của Git | `27-rework-final-git-diff-check.txt` |
| PASS Git | `git status --porcelain` sau commit | rỗng; HEAD `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb` | `29-rework-postcommit-state.txt` |

Không chạy lại full `portal_api` theo brief rework. Mốc full suite trước commit cũ vẫn là 197/197;
thay đổi rework được phủ bằng targeted 26/26 trên trạng thái cuối.

## PASS / FAIL / UNVERIFIED

**PASS:** domain/CIDR validation và boundary matching; CRUD/version/duplicate/audit rollback; auth/role
trước body/query/DB; Origin/body limit; store opt-in/off; DB failure mapping; default allowlist sau delete;
TLP hidden invariant; asset match ở ba lookup state; response fixture schema; allowlist file; commit/tree sạch.

**FAIL chưa xử lý:** không có. Các RED/lint/fixture lỗi trung gian đều có raw log và đã được sửa.

**UNVERIFIED / ngoài phạm vi:** UI/Frontend parser, browser/listener, CSV, technology/brand, OpenCTI,
Cloudflare/JWKS/HTTPS thật, network/feed/LLM thật, lab, deploy và production. Không push/PR/merge/deploy.

## Học thêm

- Partial unique index chỉ áp dụng unique cho hàng active, nên soft-delete không khóa việc tạo lại asset.
- Optimistic version từ chối ghi bằng dữ liệu cũ thay vì âm thầm ghi đè thay đổi của người khác.
- Snapshot read giữ danh sách asset và rule match nhất quán trong một lượt lookup.
- Opt-in dependency giữ W02 cũ không tự mở DB hoặc thay đổi hành vi khi W04 chưa được cấu hình.

---

## Rework Backend F1–F4 ngày 11/11/2026 — supersedes candidate FAIL

Trạng thái: **PASS cục bộ / in-process**. Phần này thay thế kết luận candidate FAIL tại
`bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`; không thay đổi bằng chứng QA lịch sử.

### Delta

- Base: `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`.
- HEAD/commit local: `5316422ef6091f48edca443f886358a4475d8e04`
  (`fix: harden local asset invariants`).
- Branch: `feat/w04-assets-local-20261111`.
- Delta: 4 file, 387 insertions, 44 deletions: `portal_api/assets.py`,
  `portal_api/ioc_lookup.py`, `portal_api/tests/test_assets_api.py`, `docs/PROGRESS.md`.
- Không sửa auth/settings/core/frontend/RUNS, schema/fixture Frontend hoặc probe QA gốc.

### Sửa F1–F4

- **F1:** list, snapshot và mutation read cùng kiểm row active: ID/version JSON-safe, type,
  canonical domain/CIDR, note, actor và timestamp. Snapshot đọc/kiểm cả row trước khi tạo rule;
  một row hỏng làm lookup trả `503 lookup_unavailable`, không gọi adapter và không trả partial.
- **F2:** actor phải dài 1..512 trước transaction; object create/update được kiểm đủ output trước
  audit/commit; update/delete chặn version tăng quá `2^53-1`. Mọi ca lỗi kiểm DB/audit không đổi.
- **F3:** `AssetFact.name` có validator riêng 1..253; source/related vẫn dùng bound 128.
- **F4:** chỉ lỗi SQLite `SQLITE_CONSTRAINT_UNIQUE` kèm active canonical trùng thật map thành
  `409 asset_exists`; trigger/audit/constraint/storage khác map `503 assets_unavailable` và rollback.

### RED → GREEN và kiểm cuối

Interpreter cụ thể: `cti-w02-lookup-api/.venv/Scripts/python.exe` (Python 3.12.13), CWD là target,
`PYTHONPATH` là target root, `core`, `extractor`, `PYTHONUTF8=1`; module `portal_api` và
`phonghoa_core` đều load từ target.

| Cổng | Kết quả | Evidence |
|---|---|---|
| Regression F1–F4 trước sửa | exit 1; 21 fail, 4 pass, 26 deselected; subject 513 riêng xác nhận 422 nhưng DB/audit 1/1 | `rework-qa/01-regressions-red.txt`, `02-long-subject-red-corrected.txt` |
| Regression phân loại trigger F4 | exit 1; 2 fail, 51 deselected vì trigger bị báo nhầm 409 | `rework-qa/04-f4-trigger-red.txt` |
| Regression cuối | exit 0; 27 passed, 26 deselected | `rework-qa/05-regressions-final-green.txt` |
| Assets + W02 bị ảnh hưởng | exit 0; 99 passed | `rework-qa/06-assets-w02-final.txt` |
| Probe QA nguyên bản | script exit 0; kiểm actual theo expected **7/7** | `rework-qa/07-targeted-probes.json`, `08-probe-verdict.txt` |
| Ruff check `portal_api` | exit 0 | `rework-qa/09-ruff-check.txt` |
| Ruff format check `portal_api` | exit 0; 13 file formatted | `rework-qa/10-ruff-format-check.txt` |
| `git diff --check` | exit 0; chỉ warning LF→CRLF của Git | `rework-qa/11-git-diff-check.txt` |

Raw evidence mới: `w04-assets-evidence/rework-qa/`. Probe gốc không sửa, SHA-256
`6597F542EEB0BC96651B068CD68E7C0BF5B4CDC83AC51D7CA39D95455C06C0B5`.

### PASS / FAIL / UNVERIFIED

- **PASS cục bộ:** F1–F4, rollback create/update, duplicate thật 409, actor/version/output bounds,
  AssetFact 128/129/253 pass và 254 fail, assets + W02 99/99, probe expected 7/7, lint/format/diff.
- **FAIL còn lại trong phạm vi rework:** không có.
- **UNVERIFIED / ngoài phạm vi:** browser/listener, UI/Frontend, Cloudflare/JWKS/HTTPS thật,
  OpenCTI, CSV/technology/brand, network/feed/LLM, lab, deploy và production. Không push/PR/merge/deploy.

---

## Rework F4 classifier UNIQUE ngày 11/11/2026

Trạng thái: **PASS cục bộ / in-process**. Sửa nốt finding F4: classifier nhận diện đúng UNIQUE
`assets(type, canonical_value)` từ lỗi SQLite; UNIQUE ở bảng/cột khác không còn bị suy diễn từ row
canonical đang tồn tại. Message SQLite không được trả cho client và transaction vẫn rollback.

### Git và delta

- Base: `5316422ef6091f48edca443f886358a4475d8e04`.
- HEAD/commit local: `90b26287eccc416fd7e7e736b0ad37632e0c34b1`
  (`fix: classify asset unique constraints precisely`).
- Branch: `feat/w04-assets-local-20261111`.
- Delta: 3 file, 40 insertions, 15 deletions: `portal_api/assets.py`,
  `portal_api/tests/test_assets_api.py`, `docs/PROGRESS.md`.
- Probe Leader giữ nguyên, SHA-256
  `67D718C3D77C2973E6DE517612B2D120B487835B2F790F0609106220CB061F56`.
- `git status --porcelain` sau commit: rỗng.

### RED → GREEN và kiểm cuối

Interpreter: `cti-w02-lookup-api/.venv/Scripts/python.exe`; CWD là target; `PYTHONPATH` gồm target
root, `core`, `extractor`; `PYTHONUTF8=1`.

| Cổng | Kết quả | Evidence |
|---|---|---|
| Regression API unrelated UNIQUE trước sửa | exit 1; 2/2 fail đúng vì actual 409 thay vì expected 503 | `rework-f4-unique/red-pytest.txt`, `red-junit.xml`, `red-exit.txt` |
| Regression API sau sửa | exit 0; 2/2 pass | `rework-f4-unique/green-targeted-pytest.txt`, `green-targeted-junit.xml`, `green-targeted-exit.txt` |
| Nhóm `portal_api/tests/test_assets_api.py` | exit 0; 55/55 pass | `rework-f4-unique/assets-suite-pytest.txt`, `assets-suite-junit.xml`, `assets-suite-exit.txt` |
| Probe Leader nguyên bản | exit 0; 2/2 pass; create/update đều 503, counts 1/1, asset unchanged | `rework-f4-unique/f4-http-results.json`, `leader-probe.txt`, `leader-probe-exit.txt` |
| Targeted cuối sau format | exit 0; 2/2 pass | `rework-f4-unique/final-targeted-pytest.txt`, `final-targeted-junit.xml`, `final-targeted-exit.txt` |
| Ruff check `portal_api` | exit 0 | `rework-f4-unique/final-ruff-check.txt`, `final-ruff-check-exit.txt` |
| Ruff format apply/check `portal_api` | exit 0; 1 file reformatted, sau đó 13 file đã formatted | `rework-f4-unique/ruff-format-apply.txt`, `final-ruff-format-check.txt` |
| `git diff --check` | exit 0; chỉ warning LF→CRLF của Git | `rework-f4-unique/final-git-diff-check.txt`, `final-git-diff-check-exit.txt` |
| Git sau commit | HEAD đúng và tree sạch | `rework-f4-unique/postcommit-state.txt` |

Raw evidence mới: `w04-assets-evidence/rework-f4-unique/`. Lượt format-check đầu exit 1 vì một dòng
classifier chưa theo formatter; `ruff format portal_api` đã sửa cơ học và ba cổng cuối đều exit 0.

### PASS / FAIL / UNVERIFIED

- **PASS cục bộ:** unrelated UNIQUE POST/PUT trả `503 assets_unavailable`, không lộ SQLite message,
  asset/audit giữ 1/1; duplicate canonical thật create/update vẫn được nhóm assets xác nhận 409;
  lint/format/diff và commit/tree sạch đạt.
- **FAIL còn lại trong phạm vi F4:** không có.
- **UNVERIFIED / ngoài phạm vi:** full portal/W02 không chạy lại theo brief; browser/listener,
  UI/Frontend, Cloudflare/JWKS/HTTPS thật, OpenCTI, network/feed/LLM, lab, deploy và production.
  Không push/PR/merge/deploy.
