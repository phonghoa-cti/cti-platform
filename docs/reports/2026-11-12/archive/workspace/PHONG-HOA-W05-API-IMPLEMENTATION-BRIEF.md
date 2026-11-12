# W05-API-NEXT — brief giao Backend

## Mục tiêu và phạm vi

Triển khai một adapter FastAPI **offline/in-process** nối portal W05 với lõi review SQLite hiện có: Analyst/Admin đã xác thực có thể list draft pending, đọc chi tiết, approve/reject một lần. Đây là demo API cục bộ; không mở public listener, không deploy/lab/cloud/OpenCTI, không bổ sung endpoint tạo/sửa draft, không export blocklist.

**Quyết định đã chốt:** làm GET list + GET detail + POST decision trong một lát cắt, same-origin `/api`, production path chỉ chấp nhận Cloudflare Access JWT đã verify. Không có `DEV_USER_EMAIL`, email/header trần, query bypass, subject/role body hoặc fallback API key. Test inject principal bằng dependency override chỉ trong process pytest.

Đọc trước khi code: `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/api-portal.md`, `docs/specs/W05-draft-offline-contract.md`, và [nghiên cứu W05 API](PHONG-HOA-W05-API-RESEARCH.md).

## Base, tree và giới hạn Git

| Mục | Giá trị |
|---|---|
| Working tree được sửa | `$WORKSPACE\cti-w05-backend` |
| Base bắt buộc | `f87b7f51acd51961eb9de26af42cea9d65d9cc9b` (`feat/w05-local-review-20261110`) |
| Frontend reference read-only | `be364bd87cd87a86b37d83e8a74e1ff3583ea7ec`; dùng `git show`, không lấy working copy Frontend rework |
| Không làm | push, PR, merge, deploy, listener public, secret thật, Cloudflare/OpenCTI request, sửa `PHONG-HOA-RUNS.json` |

Trước khi sửa: xác minh `git rev-parse HEAD` đúng base và `git status --short` sạch/ghi rõ file có trước. Làm một nhánh mới từ base theo working agreement, ví dụ `feat/w05-api-local-20261111`.

## File scope

Tạo/chỉnh tối thiểu (tên package có thể điều chỉnh sau khi kiểm tree nhưng không được đặt logic HTTP vào `store.py`):

| File | Thay đổi |
|---|---|
| `portal_api/__init__.py`, `portal_api/app.py` | App factory `create_app(settings, store)`; chỉ routes W05 `/api/drafts` |
| `portal_api/auth.py` | `Principal`, JWT verifier interface, `get_current_principal`, role check; không đọc email header trần |
| `portal_api/schemas.py` | Pydantic request/response exact models; `extra="forbid"`; error envelope |
| `portal_api/service.py` | Translation từ HTTP principal/request sang core calls/exceptions; no policy duplication |
| `portal_api/settings.py` | runtime settings: DB path, Access issuer/AUD/JWKS URL; fail closed if missing |
| `portal_api/tests/test_w05_api.py` (và fixture JWT/public key local) | test in-process, no network |
| API dependency manifest/lock | FastAPI, PyJWT crypto extra and resolved transitive pins/hashes; leave `core/pyproject.toml` dependency-free |
| `docs/specs/api-portal.md`, `docs/PROGRESS.md` | cập nhật contract trạng thái/endpoint đã làm, evidence thực chạy và gaps; không tuyên bố lab/auth thật |

Không sửa `extractor/phonghoa_extractor/store.py`, migration, core review policy hoặc payload 1.0 trừ khi test chứng minh một adapter-blocking bug; khi đó dừng và báo scope change, không tiện thể refactor.

## Hành vi bắt buộc

### Principal/auth boundary

`Principal(subject: str, roles: frozenset[Literal["analyst", "admin"]], email: str | None)` được tạo sau verify. Implementation production:

1. lấy JWT chỉ từ `Cf-Access-Jwt-Assertion`;
2. verify RS256 signature qua configured JWKS; issuer exactly configured `CF_ACCESS_ISSUER`; audience exactly configured `CF_ACCESS_AUD`; enforce normal expiration/not-before validation;
3. reject empty/non-string `sub`; lookup roles server-side by `sub`, never from JWT role claim/body/header email;
4. unset/malformed config or token => 401/503 fail closed, never an anonymous/dev user.

Offline tests use a local generated test RSA public key and signed fixture token, injected JWKS/verifier/settings without network. Do not commit a production key, token, team domain or AUD. A test private key is allowed only under test fixtures, clearly synthetic and not accepted by production settings.

`require_review_role` applies identically to all three routes. Only Analyst/Admin passes. `email` is never response identity/audit actor. Core receives `Actor(subject=principal.subject, roles=frozenset(principal.roles))` only at decision.

### Routes

Implement exact contract in research document:

- `GET /api/drafts?limit=20&before_id=` → pending summaries, `list_drafts`; `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`.
- `GET /api/drafts/{draft_id}` → stored payload plus review, `get_draft`; detail can be an already decided draft.
- `POST /api/drafts/{draft_id}/decision` → exact `decision`, `expected_version`, optional reject `reason`; call `decide_draft` once. Return only normalized review result.

Preserve top-level payload `status: "pending"`. Never rename it to approved/rejected; those belong in `review.status`. API must reject unexpected item shapes before emitting detail: exact known fields, `schema_version=1.0`, `kind=ioc` for kept items, `item.status in {ok,allowlist,bia}`. Do not render/return partial unknown data.

Map exceptions exactly: unauthenticated 401 `authentication_required`; role/core-policy 403 `forbidden`; absent draft 404 `draft_not_found`; stale/repeat 409 `draft_conflict`; malformed input 422 `invalid_request`; DB/schema/lock/unexpected output 503 `review_unavailable`. All have only `{"error":{"code":"...","message":"..."}}`; no token, claim, SQL, filesystem, actor/audit, payload, traceback or raw validation data in response/log.

## TDD acceptance matrix

Write tests first and capture a red result before implementation. Use a temporary SQLite database built from existing synthetic draft fixtures; no Internet/process listener/browser.

| Case | Expected |
|---|---|
| valid signed token + Analyst, GET list | 200, pending summaries, cursor, no text/items/evidence/findings |
| valid signed token + Admin, GET detail | 200, payload status pending and review object separate |
| missing/malformed/expired/wrong issuer/wrong audience/bad signature/no sub | 401 same sanitized envelope; no store call |
| valid token but role absent/IT | 403; no store call |
| list invalid limit/before_id; invalid path; POST body extra/bool version/reason wrong | 422 exact envelope |
| valid Analyst approve own creator / creator-null / unsupported kept kind | 403; review/audit unchanged |
| valid Analyst reject own creator with trimmed reason | 200 and one review/audit written by core |
| valid Admin approves another creator version 0 | 200 version 1; payload JSON/top-level status unchanged; exactly one audit |
| repeat/stale decision | 409; no second audit |
| unknown authenticated ID | 404 |
| DB missing/locked/unsupported schema + unexpected persisted item contract | 503, sanitized response |
| all three routes | `Cache-Control: no-store`; same-origin app has no wildcard CORS configuration |

Also retain/rerun existing review/store tests to prove adapter did not regress core. Test headers/log capture to ensure raw JWT and text/evidence never appear. Check Pydantic/OpenAPI does not expose a role/subject input field.

## Commands and evidence to report

Use the repository virtual environment interpreter explicitly, with working directory `cti-w05-backend`:

```powershell
..\cti-platform-start\.venv\Scripts\python.exe -m pytest -o addopts= -q portal_api/tests/test_w05_api.py
..\cti-platform-start\.venv\Scripts\python.exe -m pytest -o addopts= -q extractor/tests/test_review.py extractor/tests/test_store.py extractor/tests/test_queue.py portal_api/tests/test_w05_api.py
..\cti-platform-start\.venv\Scripts\python.exe -m pytest -o addopts= -q
..\cti-platform-start\.venv\Scripts\python.exe -m ruff check .
..\cti-platform-start\.venv\Scripts\python.exe -m ruff format --check .
git diff --check
git status --short --branch
git rev-parse HEAD
```

Report each exact command, exit code, test count/time, resolved dependency versions/hashes/licenses, changed file list and commit SHA. If a package install/lock cannot happen offline, mark dependency verification **UNVERIFIED** and do not run loose/unpinned runtime tests as a passing production result.

## Demo and Frontend handoff

Demo is in-process only: create temp DB with two synthetic drafts/creators, override auth with signed fixture principal, then show HTTP JSON for (1) list has only summary; (2) detail shows `status=pending` plus `review.pending`; (3) approved response has review approved/version 1 while re-read payload status stays pending; (4) second decision returns 409. Do not start Uvicorn or browse a public port.

After Backend passes, Frontend changes separately on its own tree: replace `loadFixtureDrafts` with an API client, map list summaries vs detail DTO, render `review.status/version`, submit `expected_version`, and handle 401/403/404/409/422/503 explicitly. It must not manufacture identity/role, send a self-declared actor, or claim an approved draft reached OpenCTI. Test Unicode spans with `Array.from` as existing W05 contract requires.

## Done / not done

**PASS only when:** API in-process tests cover all matrix rows, existing core regression tests and full suite/lint/format/diff checks pass, contract/PROGRESS updated, no public service/secret/network is used, and the route behavior matches this brief.

**Still UNVERIFIED after PASS:** real Cloudflare Access deployment/JWKS reachability and rotation, actual portal browser wiring, CORS/CSRF for a split origin, lab, OpenCTI/STIX ingestion, cache/proxy behavior, production database backup/permissions, and end-to-end user auth.
