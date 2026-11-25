# W05 Selection API — kết quả triển khai Backend

Ngày 11/11/2026. Kết luận: **PASS trong phạm vi API in-process**.

## Ref và phạm vi

- Worktree: `cti-w05-selection-api`
- Branch: `feat/w05-selection-api-20261111`
- Base: `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`
- HEAD/commit cục bộ: `812dae1ffbdc8e8866342cc075d925fdc99ef12d`
- Commit: `feat(portal-api): add v1 selection workflow`
- Diff: 10 file, `+1009/-19`; không sửa source tree, UI/auth/settings/dependency/CLI/harness/RUNS.

File đổi: `store.py`, `test_selection.py`, `portal_api/{schemas,service,app}.py`,
`portal_api/tests/test_w05_api.py`, ba contract/progress docs và ADR 0015.

## Đã triển khai

- Bốn thao tác `/api/v1/drafts`: list, detail, save selection, decision; `/api/drafts` legacy giữ nguyên.
- Detail đọc payload/review/selection bằng một connection và một read transaction. List chỉ thêm
  `selection_version`, không tạo count giả hoặc N selection query.
- `SelectionView` ánh xạ tường minh, bỏ `draft_id`, tuple core thành JSON list. Decision có result riêng chứa
  snapshot selection đã ghi final audit; wrapper legacy vẫn đúng sáu field và không reread sau commit.
- Adapter v1 truyền `max_version=9007199254740991`; changed mutation vượt cap bị 409 trước ghi, no-op hợp lệ tại
  cap vẫn 200. Mọi integer public v1 strict/safe; `selected_indices` input tối đa 1.024.
- Hai POST đọc stream raw body tối đa 65.536 byte (quá giới hạn 413), giữ JWT/role server-side, exact Origin,
  JSON content type, no-store/Vary và error envelope. Không nhận identity/role client tự khai.
- Missing database dùng typed subclass: v1 trả 503, missing row 404; legacy decision missing DB vẫn 404.
- Payload, source/evidence và `items.keep` không đổi; approve/reject final audit giữ đúng canonical indices/hash.

## TDD và checks thực chạy

| Check | Kết quả |
|---|---|
| Baseline full Python | exit 0, 415 passed |
| Core RED | exit 1, 5 failed / 30 passed đúng khoảng trống mới |
| Core GREEN | exit 0, 35 passed |
| HTTP v1 RED | exit 1, 12 failed do route chưa có |
| HTTP v1 GREEN mở rộng | exit 0, 26 passed / 88 deselected |
| Self-review compatibility RED | exit 1, 1 failed: legacy missing DB bị đổi 404→503 |
| Targeted cuối selection + API cũ/mới | exit 0, **150 passed** |
| Full Python cuối theo `pytest.ini` | exit 0, **447 passed** |
| Ruff check changed Python | exit 0 |
| Ruff format-check changed Python | exit 0, 6 file already formatted |
| `git diff --check` | exit 0 |
| Demo in-process tổng hợp | exit 0; temp cleanup `DEMO_TEMP_LEFT=0` |
| Local commit | exit 0 |

Self-review toàn diff không giao agent khác theo brief. Finding compatibility nói trên đã được sửa bằng
RED→GREEN; không còn finding Critical/Important/Minor trong phạm vi.

## Demo và invariant quan sát

- List/detail trả version 2; detail có `review.version == selection.review_version == selection_version`.
- Changed save → version 3, `changed=true`; lặp đúng version/indices → `changed=false`, không tăng event/version.
- Stale save → 409; empty approve → 403.
- Reject → review version 4, selection version 3, `[]` và SHA-256 canonical tương ứng.
- Approve draft khác → review version 3, selection version 2, `[0]`; final audit khớp hash.
- `payload_json_byte_equal=true`, `items_keep_equal=true` trước/sau toàn chuỗi thao tác.

## Bằng chứng

Thư mục `w05-selection-api-evidence/`:

- `targeted-final-postformat.xml` — JUnit targeted 150 test.
- `full-python-final-postformat.xml` — JUnit full 447 test.
- `demo_in_process.py`, `demo-summary.json` — demo tổng hợp và JSON rút gọn.
- `red-green.md` — receipt RED→GREEN.
- `manifest.sha256` — SHA-256 các file bằng chứng.

## Chưa xác minh

UNVERIFIED: listener/network thật, browser/UI integration, reverse proxy/gateway v1, Cloudflare/JWKS thật,
lab/VM, OpenCTI ingestion, cloud/model thật, deployment và production. Không push/PR/merge/deploy.

## Học thêm

- **SQLite snapshot:** read transaction giữ cùng một ảnh dữ liệu qua nhiều câu SELECT.
- **Optimistic concurrency:** client gửi version đã đọc; stale version bị 409 thay vì ghi đè thay đổi mới.
- **JSON safe integer:** giới hạn số nguyên mà JavaScript biểu diễn chính xác, tối đa `2**53-1`.
- **TDD:** test đỏ chứng minh khoảng trống trước khi code xanh chứng minh hành vi đã được bổ sung.
