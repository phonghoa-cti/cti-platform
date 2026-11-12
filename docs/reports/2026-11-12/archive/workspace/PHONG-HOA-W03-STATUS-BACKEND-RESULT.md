# Kết quả W03-S1 Backend

## Kết luận

PASS cục bộ/in-process cho Backend W03-S1.

- Base: `7ff6eb3af21d8de65836bfbf707396ae5690de0b`
- Branch: `feat/w03-status-backend-20261112`
- HEAD sạch: `b8957e63acc7497ba835e06c05e52f4b16ef136c`
- Diff: 12 file, `+1311/-1`, đúng allowlist Backend
- Không push/PR/merge/deploy, không dependency/secret/feed thật/lab, không sửa ledger/tree khác

## Đã triển khai

- Migration status/audit explicit, additive và fail-closed; constructor/app/request không migrate hay tạo DB.
- GET status/history mở SQLite `mode=ro`; PUT mở `mode=rw`, `BEGIN IMMEDIATE`, kiểm W04 + status schema,
  technology/context/version trên connection giao dịch rồi ghi status + audit nguyên tử.
- Ba route riêng, giữ `GET /api/cves` nguyên; auth/role trước query/body/dependency, actor chỉ từ JWT server.
- Expected context cũ ưu tiên 409 và không ghi; optimistic version khóa race first-write/replay; mọi transition,
  reopen và same-state đều tăng version/thêm audit với note mới.
- Cursor history canonical gắn relation, role view, limit, dataset/technology và snapshot audit; paging giảm dần,
  không trùng, mutation làm cursor cũ 409.
- Body streaming 16 KiB, query/cursor/JS-safe integer/text/timestamp/response 1 MiB fail-closed; duplicate/missing/extra
  JSON bị từ chối; lỗi không lộ status/context/note/actor/SQL/path.

## RED → GREEN và kiểm chứng

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `pytest portal_api/tests/test_cves_status_api.py -q` trước code | 1 | RED: thiếu `portal_api.cves_status` |
| `pytest portal_api/tests/test_cves_status_api.py` sau commit | 0 | 14 passed |
| `pytest portal_api/tests` sau commit | 0 | 377 passed |
| `ruff check portal_api docs` | 0 | All checks passed |
| `ruff format --check portal_api` | 0 | 21 files already formatted |
| `git diff <base>..HEAD --check` | 0 | sạch |

Focused tests bao phủ concurrency hai connection, rollback giữa DML/audit, response cap trước commit,
non-mutation GET/lỗi, auth/role/actor forgery, Origin/media/body/bounds, missing config/schema damage, status replay,
version/identity/dataset drift, reopen/same-state và history paging/invalid/stale cursor. Hồi quy toàn portal bao gồm
W03-R, W04 technology và auth/API liên quan `app.py`.

## Wire và provenance

Wire unset/committed/review-required/history-2pages/conflict/unavailable đến từ API TestClient thật trong test,
dùng JWT RSA/SQLite/dataset tổng hợp. Manifest và bản xuất ở `w03-status-backend-evidence/`; fixture canonical được
commit tại `portal_api/tests/fixtures/w03-status-*.json` và được so byte trong test.

## Giới hạn

Chưa kiểm frontend/gateway/browser, Cloudflare Access/JWKS/HTTPS thật, feed/CISA/OpenCTI, lab, deploy hoặc
production. W03-S2 không thuộc lượt này.

## Rework B1/B2 ngày 12/11/2026

Candidate `b8957e63acc7497ba835e06c05e52f4b16ef136c` đã được sửa tại commit sạch
`4f7100cf83e57b1cb30a12472ed71a0cd985a413`. Delta rework đúng ba file allowlist, `+229/-24`.

- B1: toàn body được kiểm strict trước dataset/store; bool/float/string/null không còn qua integer check, note/status/
  dataset sai trả 422 mà không gọi dependency hoặc ghi DB.
- B2: persisted status/audit kiểm ngày UTC thật, relation binding và audit chain/event/version; corruption trả 503,
  PUT rollback/non-mutation; snapshot technology/dataset cũ hợp lệ vẫn dùng `review_required`.
- Probe Leader nguyên bản SHA-256 `d633a3f5b82c88f7ec57d97a2238f812d7965ea207bf3a27cac307777300a152`:
  8/8 GREEN, không sửa probe.
- Focused source + probe: 57/57; hồi quy W03/W04/auth liên quan: 174/174; Ruff/format/diff-check exit 0.

Bằng chứng rework: `ROOT/w03-status-backend-rework-evidence/` và
`ROOT/PHONG-HOA-W03-STATUS-BACKEND-REWORK-RESULT.md`. Chưa có bằng chứng tích hợp frontend/API qua gateway hoặc
browser; các giới hạn live/feed/OpenCTI/Cloudflare/lab/production giữ nguyên.
