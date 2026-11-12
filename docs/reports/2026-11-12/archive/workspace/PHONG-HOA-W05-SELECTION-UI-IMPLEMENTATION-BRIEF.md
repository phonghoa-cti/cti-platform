# Brief triển khai W05 Selection UI

## Mục tiêu và phạm vi

**Owner:** CTI Frontend, Sol medium. Tạo worktree mới (chưa tạo trong lượt nghiên cứu):

```text
tree:   $WORKSPACE\cti-w05-selection-ui
branch: feat/w05-selection-ui-20261111
base:   812dae1ffbdc8e8866342cc075d925fdc99ef12d
source: cti-w05-selection-api (feat/w05-selection-api-20261111; clean when researched)
```

Mục tiêu: trong `/duyet`, analyst sửa **lựa chọn IOC đủ điều kiện** (không sửa payload extractor), bấm **Lưu lựa chọn**, rồi chỉ có thể duyệt/từ chối snapshot selection đã lưu. `/duyet/mau` tiếp tục là dữ liệu mẫu có nhãn và không gọi POST. Dùng UI SOC hiện có, không dựng dashboard/route/design framework mới.

Không làm: backend/API/gateway/settings/dependency, JWT/role client, OpenCTI, auto-save, retry POST tự động, browser/lab/Cloudflare integration. Gateway v1 + browser same-origin là **handoff CTI Engineer sau khi UI được accepted**, không giả in-process/fake-fetch là tích hợp thật.

## File/scope dự kiến

- `portal/web/data/api-client.ts`: type v1 riêng, exact parser/request cho list/detail/save/decision v1; giữ legacy parser/API riêng hoặc bỏ call site legacy có kiểm soát, không nới lỏng parser/fallback.
- `portal/web/components/draft-review-app.tsx`: state selection + dirty/navigation/action locking.
- `portal/web/components/draft-review.tsx`: checkbox eligible, indicator/count/action/copy hooks; giữ text-only rendering, source/evidence, defang, clipboard và focus span.
- `portal/web/messages/vi.json`, `portal/web/messages/en.json`: copy tương đương.
- `portal/web/tests/api-client.test.ts`, `draft-review-app.test.tsx`, `draft-review.test.tsx` và fixture/test helper cần thiết; `portal/web/README.md`/`docs/PROGRESS.md` nếu mô tả trạng thái thay đổi.

Không đổi `portal_api/**`, `tools/local_integration/**`, fixture sample để mô phỏng write, dependency lockfile nếu không bắt buộc.

## Contract bắt buộc

Chỉ dùng `/api/v1/drafts` trong `mode="api"`:

| Operation | Request | Success phải parse exact |
|---|---|---|
| List | `GET /api/v1/drafts?limit=20[&before_id=n]` | legacy summary + `selection_version` safe integer. |
| Detail | `GET /api/v1/drafts/{id}` | payload + `review` + `selection` (mọi key exact). |
| Save | `POST /api/v1/drafts/{id}/selection`, `{"expected_version":n,"selected_indices":[0,3]}` | full `selection`; indices unique/sorted/subset eligible; sha lowercase 64 hex. |
| Decision | `POST /api/v1/drafts/{id}/decision`, approve/reject + `expected_version` from committed `selection.review_version` | response includes final audit snapshot: `selection_version`, `selected_indices`, `selected_sha256`. |

`fetch`: `credentials:"same-origin"`, `cache:"no-store"`; POST `Content-Type: application/json`. IDs, versions, indices/counts must be `Number.isSafeInteger`, no boolean/coercion; public range max `9007199254740991`; `selected_indices.length <= 1024`. Exact parser rejects unknown/missing fields and any malformed response. Response/draft association: reject parser/result if returned decision `draft_id` differs URL/current request, or audit snapshot differs committed selection expected for that decision.

Eligible = `item.kind === "ioc" && item.keep === true && item.status === "ok"`. `items.keep` stays raw immutable extractor suggestion. Do not toggle allowlist, `bia`, non-IOC or `keep:false`; do not fabricate indices. Empty `[]` can save but disables approve; reject remains possible only after selection is clean/saved (subject to backend policy). `selection` has no draft id; never apply it across draft IDs.

## State machine và UI flow

Maintain one per-current-draft selection model:

```text
loaded clean ─checkbox─> dirty ─save POST─> saving
  ^       ^                  │               ├─ valid response ─> clean
  │       └─ cancel ─────────┘               ├─ 409 ─> stale (reload required)
  │                                          ├─ known failure ─> dirty
  │                                          └─ network/invalid response ─> save-unknown
  └─ reload success from clean / after explicit discard
```

- `savedSelection`: committed indices + `selection_version`, `review_version`, hash, server counts; `editingSelection`: Set cloned from saved. `dirty = !setEqual(saved, editing)`; never mutate either source array.
- Render **“Đã có thay đổi chưa lưu” / “You have unsaved selection changes”** when dirty, plus `Lưu lựa chọn` / `Save selection`, `Hủy thay đổi` / `Discard changes`. Always label selected count as pending save when dirty. Detail count labels come from server, not recomputed as extractor facts.
- When `dirty|saving|save-unknown|save-refresh-failed|decision in-flight`, disable queue row switching, load-more, detail reload, all selection controls and approval/rejection appropriately. Smallest flow: tell user to save/discard; do not silently change page/draft. For a browser navigation event, use a confirmation only if existing app routing has one; otherwise no new navigation behavior is required in this slice.
- Save allowed only pending + dirty + not locked. Snapshot draft ID, request generation, and committed selection/review version before await. `saving` locks all mutable actions. On valid response for same draft/generation, replace both saved/editing, show `Đã lưu lựa chọn` or `Không có thay đổi để lưu`; do not cascade decision.
- Optionally refresh list/detail after response only to update display. If refresh fails after valid save, show **“Lựa chọn đã được lưu nhưng chưa tải lại được trạng thái. Tải lại trạng thái trước khi quyết định.”** / equivalent EN; keep response as committed local state, lock decision, offer reload. Never repost save.
- `save-unknown` means request was sent but network/abort/invalid response left commit unknown: preserve edits visible, lock save+decision, show **“Chưa xác định lựa chọn đã được lưu. Không gửi lại; hãy tải lại trạng thái.”** / EN equivalent. Reload detail only; user must explicitly discard stale local edits before response replaces model. Do not retry.
- `409`: retain visible edits, label data changed, lock mutations and require reload; reload must not overwrite dirty input until explicit discard. 401/403 retain edits and show login/permission; 413/422 retain edits and no automatic retry; 503/service error retains edits and re-enables only save if outcome is known failure.
- Decision allowed only `clean`, pending, nonempty saved selection, no action lock. Use committed `review_version`; success must match draft+snapshot. Reuse current post-decision refresh behavior: valid decision stays visible if refresh fails, action remains locked, and user can explicitly reload. Unknown decision POST stays locked and offers refresh only; no duplicate POST.
- Preserve AbortController + active/generation guard for detail load. Aborting a request never proves the server did not commit a POST.

## Error matrix

| Case | Message/action | State after |
|---|---|---|
| Empty selection | “Chưa chọn IOC nào để duyệt; có thể lưu lựa chọn trống.” / EN | Save allowed; approve disabled. |
| >1024 locally | Prevent 1025th toggle; “Có thể lưu tối đa 1.024 IOC.” / EN | Dirty remains, no POST. |
| 401 / 403 | Valid signed-in session / no permission | Keep edits; no client identity workaround. |
| 409 | “Dữ liệu đã thay đổi. Tải lại trước khi lưu hoặc quyết định.” / EN | stale; reload-required. |
| 413 | “Yêu cầu lưu quá lớn. Hãy giảm lựa chọn rồi gửi lại.” / EN | Keep edits; no retry. |
| 422 | “Lựa chọn không còn hợp lệ. Tải lại trạng thái.” / EN | Keep edits; reload-required. |
| 503, malformed response | “Dịch vụ duyệt tạm thời chưa sẵn sàng. Thử lại thủ công.” / EN | Keep edits; no sample/legacy fallback. |
| POST network ambiguity | Unknown-save/unknown-decision copy above | Lock duplicate request; explicit refresh only. |
| Response for other A/B draft | Generic safe service failure; do not display it as saved | Keep current B state. |

Map 415 only to generic safe API error (UI sends JSON); preserve existing 404 handling. Never reveal server response detail. Do not call `/duyet/mau` as recovery from any API failure.

## Regression/acceptance matrix

| Group | Required assertion |
|---|---|
| Contract/parser | v1 list/detail/save/decision accepts exact valid shape; rejects extra/missing keys, unsafe integer/boolean, out-of-range/version, duplicate/unsorted/noneligible indices, bad hash, wrong response draft/snapshot. Legacy parser does not silently accept v1. |
| Main flow | Load detail → eligible checkbox changes dirty only → explicit save exact body → valid selection response clean → explicit approve/reject uses saved review version, not UI dirty version. |
| Boundaries | Empty can save/no approve; no-op shows no-op; 1024 accepted and 1025 prevented; versions at safe ceiling parse but server 409 flow does not send another write. |
| Dirty/navigation | Approve/reject disabled dirty; discard restores exact saved set; draft switch/load-more/reload blocked while dirty/saving; A response cannot overwrite B. |
| POST/race | Double click sends one save/one decision; save success + refresh fail retains committed response and locks decision; network ambiguity sends no retry; 409 preserves edits/requires reload; 401/403/413/422/503 safe copy/state. |
| Existing behavior | Sample labeled/no POST; API failure never sample fallback; VI/EN both strings; unsafe CTI renders text/no links; Unicode code-point evidence still uses `Array.from`; defang display and copy-original clipboard/error behavior pass. |
| Local checks | Run targeted Vitest, then `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`; report fresh exit code/count/log paths. These prove UI locally only. |

Run no browser/gateway claim as part of this UI acceptance. Handoff after accepted UI: **CTI Engineer** extends `tools/local_integration/gateway.mjs` allowlist specifically for `/api/v1/drafts` paths, validates header/body behavior, then runs same-origin browser integration with API v1. This is a separately evidenced task; fake fetch/unit tests are not a gateway or browser result.

## Handoff/report expected from Frontend

Report exact base/head, tree status, changed files, tests with fresh exit codes and count, plus `UNVERIFIED` gateway/browser/lab/JWKS/Cloudflare/OpenCTI. Do not push, PR, merge or deploy. Explain for a beginner: `savedSelection` is what the server recorded; `editingSelection` is what the analyst is currently changing; the Save button is the deliberate boundary that prevents approving a different snapshot.
