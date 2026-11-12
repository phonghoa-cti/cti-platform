# PHONG HỎA W05 API — RESULT

## Kết luận

**PASS cục bộ sau rework R1–R3** tại commit `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`, branch
`feat/w05-api-local-20261111`, base `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`.

Đã triển khai đúng ba route `GET /api/drafts`, `GET /api/drafts/{draft_id}` và
`POST /api/drafts/{draft_id}/decision` trên adapter FastAPI, tái dùng nguyên lõi review SQLite.
Không sửa core/store/migration, không mở listener, không dùng Cloudflare/OpenCTI/model/secret/lab thật.

## Contract và biên an toàn

- JWT chỉ đọc từ `Cf-Access-Jwt-Assertion`; verify chữ ký RSA/RS256 bằng JWKS cấu hình, exact issuer và audience
  là chuỗi exact hoặc mảng chuỗi không rỗng có exact member cấu hình; bắt buộc `exp/iss/aud/sub`, kiểm
  NumericDate hữu hạn không-bool và thời gian `exp/nbf/iat`.
- Loại `alg=none`, HS256, sai chữ ký, unknown `kid`, claim thiếu/sai. JWKS URL HTTPS, cùng origin issuer,
  có timeout/cache; lỗi kết nối làm sạch thành 503.
- Role chỉ tra server-side theo `sub`; role/admin/email/header/body tự khai không được tin. Cả ba route cùng
  chặn 401/403 trước DB/validation.
- POST chỉ nhận exact `Origin == PORTAL_ORIGIN` và `application/json` (cho `charset=utf-8`). Không CORS wildcard.
- Payload 1.0 vẫn có top-level `status=pending`; quyết định nằm riêng ở `review.status/version`.
  Summary không lộ text/items/evidence/findings; output lạ bị chặn 503 thay vì trả một phần.
- Error envelope chỉ có `error.code/message`; mọi success/error dưới `/api/drafts` đều `no-store` và `Vary` JWT.
- ID, cursor và limit quá dài bị chặn 422 trước `int()`/store, không đổi giới hạn số toàn tiến trình.

## TDD và kiểm thử

RED được lưu tại `w05-api-evidence/RED.md`: collect đầu tiên exit 1 do chưa có `portal_api.app`; tiếp theo
5 fail/63 pass; strict-audience từng 1 fail/20 pass; loader runtime từng fail vì chưa tồn tại rồi mới triển khai.
Rework RED ở `REWORK-RED.md`: 6 fail/1 pass/81 deselected, tái hiện đủ audience mảng, header lỗi bất ngờ và
ba số 5.000 chữ số trước khi sửa production code.

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `.venv\Scripts\python.exe -m pytest -o addopts= -q portal_api\tests\test_w05_api.py` sau commit rework | 0 | 88 passed, 2.57s |
| `.venv\Scripts\python.exe -m pytest -o addopts= -q extractor\tests\test_review.py extractor\tests\test_store.py extractor\tests\test_queue.py portal_api\tests\test_w05_api.py` sau commit rework | 0 | 219 passed, 4.42s |
| `.venv\Scripts\python.exe -m pytest -o addopts= -q` | 0 | 355 passed, 27.35s |
| full suite sau commit cùng lệnh trên | 0 | 355 passed, 20.31s |
| `.venv\Scripts\ruff.exe check .` | 0 | all checks passed |
| `.venv\Scripts\ruff.exe format --check .` | 0 | 99 files already formatted |
| `.venv\Scripts\python.exe -m compileall -q portal_api` | 0 | compiled |
| `git diff --check` | 0 | sạch |
| `git status --porcelain=v1` sau commit | 0 | output rỗng |

88 test API bao phủ matrix dương/âm: list/detail/decision, JWT và claims, audience string/singleton-array/
multi-array cùng wrong/empty/mixed/nested array, role giả, auth-before-store,
query/path/body strict, Origin/media type, policy Analyst/Admin, audit/atomic conflict, DB missing/corrupt/locked,
schema/output tương lai, lỗi bất ngờ, số quá dài, headers, OpenAPI, runtime settings, không mạng và không rò
token/nội dung. Full suite 355 là lần chạy ở commit đầu; theo brief rework không lặp full suite vì chỉ đổi API/docs.

## Demo và dependency

`w05-api-evidence/demo_api.py` sinh RSA key/JWK và SQLite tạm lúc chạy, ký JWT thật rồi gọi app in-process.
`demo-array-aud.json` dùng JWT `aud=[configured]` và ghi: list/detail/decision/reread lần lượt 200; payload đọc
lại vẫn `pending`, review `approved/version=1`;
quyết định lần hai 409 `draft_conflict`. Không lưu private key/token, không mạng, không listener.

Dependency nằm trong `.venv` riêng. `requirements-api.lock` ghim 25 package cùng SHA-256. Version/license chính:
FastAPI 0.119.1 MIT; HTTPX 0.28.1 BSD-3-Clause; PyJWT 2.15.1 MIT; cryptography 50.0.2
Apache-2.0 OR BSD-3-Clause; Pydantic 2.14.3 MIT; Starlette 0.48.0 BSD-3-Clause; AnyIO 4.11.0 MIT;
pytest 9.2.0 MIT; Ruff 0.17.4 MIT. Chi tiết ở `portal_api/README.md` và `w05-api-evidence/DEPENDENCIES.md`.

## Git và phạm vi thay đổi

- Commit: `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`
- Rework diff từ `feac804`: 6 files, 84 insertions, 5 deletions.
- Diff cộng dồn từ base: 13 files, 1804 insertions, 17 deletions.
- Files: package/test `portal_api/`, `requirements-api.in`, `requirements-api.lock`, `pytest.ini`,
  `docs/specs/api-portal.md`, `docs/PROGRESS.md`.
- Worktree sạch sau commit; không push/PR/merge/deploy.

## Còn UNVERIFIED

Cloudflare Access/JWKS thật và rotation; topology proxy/cache; portal/browser wiring; auth E2E; CORS/CSRF khi khác
origin; quyền/backup DB production; lab; OpenCTI/STIX ingestion; deploy. PASS này chỉ là API cục bộ với RSA/JWKS/SQLite
tổng hợp và dependency đã khóa.
