# W05-API-NEXT — HTTP tối thiểu nối portal với lõi review

**Ngày kiểm:** 11/11/2026 (ICT). **Phạm vi:** nghiên cứu/brief, không sửa repository, không cài dependency, không mở listener, không dùng secret, lab, cloud, model hay OpenCTI.

## Câu hỏi và kết luận

Câu hỏi: lát cắt HTTP nào nhỏ nhất để thay ba fixture của portal bằng hàng đợi W05 thật, nhưng không biến email/header do client tự gửi thành danh tính?

**Khuyến nghị: B — một API W05 nhỏ gồm hai GET và một POST decision, cùng một dependency xác thực.** GET-only có auth (A) ít code hơn nhưng chỉ làm portal “xem được” hàng đợi; người dùng vẫn không thể hoàn tất human-in-the-loop và lần sau phải thiết kế lại cùng identity/role/error boundary cho POST. B dùng lõi `get_draft`, `list_drafts`, `decide_draft` đã kiểm chứng, không thêm endpoint tạo/sửa, không đổi payload 1.0, không gọi OpenCTI.

| Phương án | Phạm vi | Lợi ích | Giới hạn | Kết luận |
|---|---|---|---|---|
| A. GET có xác thực | list + detail | Thay fixture và chứng minh role đọc | Không có quyết định/audit qua portal; phải thêm POST và test auth lần sau | Không chọn |
| B. GET + decision cùng auth | list + detail + approve/reject | Luồng W05 đầu-cuối tới local review/audit; một trust boundary duy nhất | Cần contract lỗi 409 và identity adapter ngay từ đầu | **Chọn** |

`approved` trong B chỉ nghĩa là **đã duyệt cục bộ**. Nó không tạo STIX/Report, không xuất blocklist, không gửi sang OpenCTI và UI không được ghi “đã nhập OpenCTI”.

## Hiện trạng đã kiểm ở đúng ref

| Nguồn | Ref/quan sát | Phần dùng lại | Hạn chế/gap |
|---|---|---|---|
| Backend `cti-w05-backend` | branch `feat/w05-local-review-20261110`, HEAD `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`, sạch khi kiểm theo báo cáo W05 | `extractor/phonghoa_extractor/store.py`: `get_draft`, `list_drafts`, `decide_draft`, `Actor`, review metadata, `BEGIN IMMEDIATE`, audit | Không có FastAPI, HTTP, JWT, user/role DB hay dependency HTTP |
| W05 offline contract | `docs/specs/W05-draft-offline-contract.md` tại SHA trên | payload 1.0 bất biến; cursor `before_id`, limit 1–100, review tách payload, Unicode code-point | Yêu cầu API biên tự allowlist kind/item.status; chưa chốt HTTP status/error |
| API portal cũ | `docs/specs/api-portal.md` tại SHA trên | URL prefix `/api`, JSON error envelope, W05 chỉ Analyst/Admin | Mô tả cũ tin header email / dev env; chính file ghi W05 HTTP/auth là đề xuất, nên **không dùng** làm auth production |
| Frontend preview | `cti-portal-web`, `git show be364bd87cd87a86b37d83e8a74e1ff3583ea7ec:portal/web/{README.md,data/draft-adapter.ts,components/draft-review-app.tsx}` | parser TypeScript, loading/error/retry UI, route `/duyet`, fixture có dạng stored draft gần đủ | Có login/request ghi = không; `Draft` chưa có `review`; adapter hiện parse fixture chứ không gọi HTTP; ref working copy đang rework không dùng làm nguồn |

W05-B đã có bằng chứng cục bộ 278 pytest, Ruff và migration/audit ở SHA trên; đây là bằng chứng **lõi offline**, không phải bằng chứng FastAPI, JWT, browser hay lab.

## Ranh giới tin cậy và quyết định auth

### Điều phải tin và không được tin

```
Browser portal -- HTTPS same-origin --> FastAPI adapter --> verified Principal --> W05 SQLite core
                                     |                         |              |
                          body/query chỉ là data      subject+roles      Actor(subject, roles)
```

1. Không nhận `subject`, `role`, `email`, `created_by_subject` từ JSON body, query hay header email trần. Body POST chỉ chứa `decision`, `expected_version`, và `reason` khi reject.
2. API production chỉ lấy principal sau khi xác minh JWT từ `Cf-Access-Jwt-Assertion`: kiểm chữ ký RS256 bằng JWKS, `iss` đúng team domain, `aud` đúng application AUD, và các thời điểm `exp`/`nbf`; `sub` phải là string không rỗng. Cloudflare nêu token ở header này, xác minh chữ ký bằng public key/JWKS, cùng issuer/audience; `aud` xác định JWT hợp lệ cho application nào. [Cloudflare Access — Validate JWTs](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/)
3. `email` chỉ là display optional từ claim JWT đã verify, không phải key policy. Role phải lookup server-side theo `sub` trong allowlist cấu hình cục bộ (fixture/offline) hoặc bảng `users(subject, role, ...)` ở lát cắt sau. Role được phép đúng `analyst|admin`; role lạ/missing là 403.
4. Không có “dev header”, `DEV_USER_EMAIL`, bypass query flag hay fallback API key trong lát cắt này. Offline test inject một `Principal`/verifier giả qua FastAPI dependency override; đường đó chỉ tồn tại trong test process, không phải runtime mode. Không cần secret thật.
5. `created_by_subject` được core đọc từ SQLite; API không set nó hoặc cho caller override. Core vẫn chặn self-approve/creator-null. Adapter không viết lại policy đó.

Lý do tái dùng: FastAPI dependency phù hợp để một `get_current_principal` trả typed principal cho cả path operations, và `TestClient` chạy request in-process với pytest. [FastAPI dependency/auth](https://fastapi.tiangolo.com/tutorial/security/get-current-user/), [FastAPI TestClient](https://fastapi.tiangolo.com/tutorial/testing/). Không coi ví dụ decode giả trong tutorial là xác minh JWT.

### CORS, CSRF và cache

Chọn **same-origin**: Next portal và `/api` qua cùng origin/reverse proxy. Backend không thêm `CORSMiddleware`; browser không gửi cross-origin credentials. CORS là cơ chế header cho một origin khác và browser có preflight, nên chưa cần bật nó khi không có origin thứ hai. [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)

- Nếu tương lai tách origin: thay đổi này cần spec/PR riêng; allowlist exact HTTPS origin, methods/headers tối thiểu và không wildcard với credentials. Cookie-based auth khi đó cần CSRF defense riêng. Không làm ở W05-API-NEXT.
- GET list/detail: `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`; không cache browser/shared proxy vì body chứa text/evidence CTI. POST: `Cache-Control: no-store`.
- Không log token, raw Authorization/Cf-Access header, `text`, `evidence`, `findings`, reason hoặc full exception. Audit vẫn do core lưu metadata tối thiểu.

## Contract HTTP 1.0 được đề xuất

Tất cả response JSON, prefix `/api`; timestamp giữ ISO 8601 có timezone. Payload stored draft không đổi. `status` ở top-level luôn payload status `pending`; `review.status` độc lập.

### `GET /api/drafts?limit=20&before_id=<positive-integer>`

- Required role: `analyst` hoặc `admin`.
- Query: `limit` default 20, integer 1–100; `before_id` optional positive SQLite integer. Không có filter để lộ approved/rejected.
- Calls `list_drafts(db_path, limit, before_id)`; core giữ `mode=ro`, không migration/ghi.
- 200:

```json
{
  "items": [{
    "id": 5,
    "created_at": "2026-11-10T15:18:49.564135+00:00",
    "status": "pending",
    "source": {"name": "synthetic.txt", "sha256": "...64 hex..."},
    "language": "vi",
    "tlp": "TLP:GREEN",
    "item_count": 1,
    "injection_warning": false,
    "review_status": "pending",
    "review_version": 0
  }],
  "next_before_id": null
}
```

Summary không chứa `text`, `items`, `evidence`, `findings`, creator hoặc actor/audit.

### `GET /api/drafts/{draft_id}`

- Required role: `analyst` hoặc `admin`; only positive SQLite integer path ID.
- Calls `get_draft(db_path, draft_id)` and returns stored draft exactly, including `review`; never returns audit rows. Detail remains readable after local decision, enabling an honest status UI.
- Before response, API validates the persisted 1.0 shape using an explicit HTTP output model/allowlist: `schema_version == "1.0"`; payload status `pending`; supported kept item `kind == "ioc"`; item status only `ok|allowlist|bia`; exact field sets as offline contract. An unexpected stored shape is 503, not partially rendered.

### `POST /api/drafts/{draft_id}/decision`

- Required role: `analyst` hoặc `admin`.
- Exact body (forbid extra):

```json
{"decision":"approve","expected_version":0}
```

or

```json
{"decision":"reject","expected_version":0,"reason":"IOC không có bằng chứng trong văn bản"}
```

- `expected_version`: integer >= 0, no boolean. `approve` rejects any `reason`; `reject` requires non-blank reason after trim. API constructs `Actor(subject=principal.subject, roles=frozenset(principal.roles))` only after verified principal and calls `decide_draft`.
- 200 result:

```json
{"draft_id":5,"review":{"status":"approved","version":1,"decided_by_subject":"opaque-subject","decided_at":"2026-11-11T...+00:00","reason":null}}
```

Do not return a display email, JWT claims, raw payload, audit record or an OpenCTI identifier.

### Error envelope and mapping

All intentional errors return `{"error":{"code":"...","message":"..."}}`; messages Vietnamese, stable but generic. Debug detail stays server-side and sanitized.

| HTTP | `code` | Khi nào | Không được lộ |
|---:|---|---|---|
| 401 | `authentication_required` | header missing, malformed/expired token, missing/invalid `sub` | which check failed, token/JWKS/claims |
| 403 | `forbidden` | role missing/not Analyst/Admin; policy self-approval or creator-null/unsupported approval | role assignment, creator subject, policy internals |
| 404 | `draft_not_found` | verified caller requests absent ID | DB path or existence to unauthenticated caller |
| 409 | `draft_conflict` | stale version or already decided | current actor/audit or whether another person acted |
| 422 | `invalid_request` | path/query/body invalid, extra field, unsupported response input | raw validation trace, raw payload |
| 503 | `review_unavailable` | DB locked/unavailable/corrupt/unsupported schema or unexpected persisted contract | filesystem path, SQL, stack trace |

`DraftNotFoundError` maps to 404 only after auth. `DraftInputError` to 422; `DraftPolicyError` to 403; `DraftConflictError` to 409; `DraftSQLiteError`/unrecognised database failure to 503. Any unexpected exception also becomes 503 plus sanitized server log. SQLite permits multiple concurrent readers but one simultaneous writer, so a lock/error must not be mislabeled as authorization or conflict. [SQLite transactions](https://www.sqlite.org/lang_transaction.html)

## Dependency, license and maintenance decision

Current backend declares no web dependencies; implementation must add a small, pinned optional API dependency group/requirements file with hash lock generated by Backend, rather than alter `core` library dependencies.

| Component | Why | License/source checked 11/11/2026 | Decision |
|---|---|---|---|
| FastAPI | route, validation, dependency injection, TestClient integration | MIT; official docs/PyPI: [FastAPI](https://fastapi.tiangolo.com/), [PyPI](https://pypi.org/project/fastapi/) | Add a pinned current compatible release after `pip index`/lock in implementation; version not pinned in research because current workspace has none |
| PyJWT with `crypto` extra | RS256/JWKS JWT verification in Python | MIT; [PyJWT PyPI](https://pypi.org/project/PyJWT/) | Pin to a supported release; no homemade JWT parser/verification |
| cryptography | transitive crypto backend for RSA verification | Apache-2.0 OR BSD-3-Clause; [cryptography PyPI](https://pypi.org/project/cryptography/) | Pin through lock; verify Windows/Python 3.12 wheel in implementation |
| SQLite stdlib | existing storage and core | public domain; already used | Reuse; no ORM/migration library in this slice |

Exact resolved versions, hashes and transitive license scan are acceptance checks for the implementation branch, not claims made here. This avoids recording an uninstalled, unverified package version as evidence.

## Reuse/gap recommendation

| Work | Reuse / adjust / build | Reason |
|---|---|---|
| SQLite state, optimistic version, audit, policy | **Reuse unchanged** | Existing core is source of truth and has focused/full-suite evidence |
| Identity JWT verification and role mapping | **Build thin adapter** | Explicit gap; no verified production identity exists. Keep it outside store.py |
| HTTP contract and error translator | **Build thin adapter** | Converts stable core exceptions without reimplementing decisions |
| Frontend data loader | **Adjust later** | Replace `loadFixtureDrafts()` with API client only after Backend contract test passes; extend TS type for review/summary separately |
| CORS/CSRF/API keys/OpenCTI | **Defer** | Not necessary for same-origin W05 local decision; each changes trust/action scope |

## Chưa kiểm / điều kiện trước lab

- **UNVERIFIED:** Cloudflare team domain, AUD, issuer, JWKS reachability/rotation, JWT claim mapping, user provisioning, reverse-proxy topology and production role store.
- **UNVERIFIED:** actual FastAPI/PyJWT compatibility, dependency lock/license scan, browser behavior, CORS/CSRF, lab/network and any OpenCTI integration.
- A signed Cloudflare header may only be trusted after the checks above. An email header alone is never authentication.
