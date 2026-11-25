# W05 Selection UI — nghiên cứu nối giao diện

Ngày kiểm: 11/11/2026 (ICT). Mục tiêu là chốt lát cắt UI nhỏ nhất để analyst thay đổi tập IOC đủ điều kiện, **lưu rõ ràng**, rồi mới duyệt/từ chối snapshot đã lưu. Đây là nghiên cứu/brief; không có thay đổi sản phẩm hay bằng chứng browser/lab.

## Hiện trạng đã đối chiếu

| Nguồn | Ref / trạng thái đã đọc | Bằng chứng cần tái dùng |
|---|---|---|
| Tree API | `cti-w05-selection-api`, branch `feat/w05-selection-api-20261111`, HEAD `812dae1ffbdc8e8866342cc075d925fdc99ef12d`; `git status --short --branch` chỉ trả branch, tức sạch | API selection v1 đã được Leader nghiệm thu local/in-process; không suy ra gateway/browser/lab đã tích hợp. |
| Nghiệm thu API | `PHONG-HOA-W05-SELECTION-API-REVIEW-20261111.md` | 56 passed (nhóm Leader) tại ref trên; giới hạn browser/gateway/JWKS thật/lab/OpenCTI vẫn UNVERIFIED. |
| Contract thật | `portal_api/schemas.py`, `portal_api/app.py`, `portal_api/service.py`, `docs/specs/api-portal.md` tại ref trên | Four route `/api/v1/drafts`; strict JSON; safe integer; selection/review snapshot từ cùng read transaction. |
| UI hiện có | `portal/web/data/api-client.ts`, `components/draft-review-app.tsx`, `components/draft-review.tsx`, adapter, fixtures, messages và Vitest tests | UI hiện gọi legacy `/api/drafts`, parser khóa `review.version <= 1`; checkbox chưa có; có AbortController cho detail, decision lock, refresh-after-decision và sample không POST. |
| Harness | `tools/local_integration/gateway.mjs` tại ref trên | Regex chỉ cho `/api/drafts...`, **không** `/api/v1/drafts`; browser v1 là việc Engineer sau khi UI được nghiệm thu. |

Đã đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-draft-offline-contract.md`, `docs/specs/api-portal.md`, `docs/design/DESIGN.md`. Thiết kế SOC console tối, VI mặc định/EN, hiển thị CTI không tin cậy dạng text, font/clipboard/defang hiện có phải giữ nguyên.

## Hợp đồng v1 cần UI dùng đúng

`GET /api/v1/drafts` thay thế riêng cho màn API (không phải fallback legacy): mỗi summary có thêm `selection_version`. `GET /api/v1/drafts/{id}` trả payload bất biến, `review` và:

```json
{
  "selection": {
    "review_version": 0,
    "selection_version": 0,
    "selected_indices": [0, 3],
    "selected_sha256": "<64 lowercase hex>",
    "saved_by_subject": null,
    "saved_at": null,
    "changed": false,
    "ai_extracted_count": 4,
    "ai_eligible_count": 2,
    "human_deselected_count": 0,
    "selection_save_count": 0
  }
}
```

Chỉ item `kind === "ioc" && keep === true && status === "ok"` là eligible. `items.keep` là gợi ý extractor bất biến: không sửa, không dùng làm state checkbox sau tải. `selected_indices` là index của `items` và là snapshot con người đã lưu. `draft_id` nằm trên URL; selection không chứa draft ID nên client phải ghép response với request ID đang còn hiệu lực.

Lưu: `POST /api/v1/drafts/{id}/selection` body exact `{"expected_version": 0, "selected_indices": [0,3]}`. Array sorted tăng dần, unique, toàn số nguyên JavaScript-safe `0..9007199254740991`, tối đa 1.024; `[]` hợp lệ. Backend vẫn xác thực subset eligible. Thành công trả full `selection`; no-op có thể trả `changed:false` và không tạo event/version. Không được suy ra `changed:true` chỉ từ checkbox đã đổi.

Quyết định: `POST /api/v1/drafts/{id}/decision` body exact `{"decision":"approve","expected_version":1}` hoặc `{"decision":"reject","expected_version":1,"reason":"..."}`. `expected_version` là version trong **selection đã lưu** (`selection.review_version`), không là version của UI đang sửa. Thành công trả `draft_id`, `status`, `version`, actor/time/reason cùng `selection_version`, `selected_indices`, `selected_sha256` đã copy vào audit cuối. UI chỉ chấp nhận response khi ID, terminal status và snapshot phù hợp request/current committed selection; response sai shape/ID/version/hash là lỗi service, không là thành công.

Tất cả v1 public integers là safe, strict (không boolean/coercion). POST có Origin exact, JSON và giới hạn raw body 65.536 byte. API trả `Cache-Control: no-store` và `Vary: Cf-Access-Jwt-Assertion`; frontend chỉ dùng `credentials:"same-origin"`, không dựng JWT/role/subject từ client.

## Hai cách thao tác lưu

| Cách | Đánh giá |
|---|---|
| Autosave sau mỗi checkbox | Giảm một lần bấm nhưng tạo nhiều mutation/race, khó nói rõ thay đổi nào đã được duyệt; mất kết nối cho trạng thái POST chưa rõ và đổi draft phức tạp hơn. Không chọn. |
| **Nút “Lưu lựa chọn” rõ ràng (chọn)** | Giữ `savedSelection` và `editingSelection` riêng; user thấy `Đã có thay đổi chưa lưu`, quyết định chỉ mở khi hai tập bằng nhau. Một POST có snapshot/version rõ, phù hợp API optimistic concurrency và UI hiện có lock. |

Quyết định là cách hai. Không tự xâu `save → approve`: sau save hợp lệ, UI chỉ mở nút quyết định để người dùng bấm riêng; không có contract/test cho chuỗi tự gửi đó.

## State và luồng quyết định

Một state gọn theo draft đang chọn gồm: `detail` (payload read-only), `savedSelection` (tập + selection/review version/hash từ server), `editingSelection` (tập checkbox), `selectionPhase` (`clean|dirty|saving|save-unknown|save-refresh-failed|stale|terminal`) và action lock. `dirty` là so set indices, không giữ cờ dễ lệch. Counts hiển thị lấy từ `selection` server: `ai_extracted_count`, `ai_eligible_count`, `human_deselected_count`, `selection_save_count`; số đang chọn có thể tính từ `editingSelection.size` và phải gắn nhãn “chưa lưu” khi dirty.

1. Tải queue/detail v1; exact-parse detail+selection. Clone `selected_indices` sang cả saved/editing. Tính eligible từ payload và reject client response chứa index không eligible, duplicate, không sorted, quá 1.024 hoặc version/hash sai format.
2. Checkbox chỉ đổi `editingSelection` cho eligible. Empty selection được phép lưu; approve bị disabled khi saved selection rỗng (backend cũng từ chối). `items.keep`/allowlist/bị loại/non-IOC luôn read-only; vẫn render warning/evidence/defang/clipboard cũ.
3. Dirty: hiện status và hai nút `Lưu lựa chọn` / `Hủy thay đổi`. Hủy clone saved sang editing. Disable approve/reject; khi save đang gửi, khóa checkbox, lưu/hủy, queue, phân trang, đổi draft và mọi decision.
4. Save success: exact-parse response, kiểm đúng draft còn selected và response `review_version/selection_version/selected_indices/hash` hợp lệ; thay saved+editing bằng response, báo saved/no-op. Sau đó có thể refresh detail/queue để đồng bộ display, nhưng refresh fail **không đảo** kết quả save: phase `save-refresh-failed`, giữ committed response, khóa quyết định và chỉ có “Tải lại trạng thái”.
5. Detail reload thành công thay cả saved/editing chỉ khi không dirty/saving. Khi dirty, không tự overwrite: hiện lựa chọn “Lưu lựa chọn”, “Hủy thay đổi rồi tải lại”, hoặc “Ở lại”; trong lát cắt nhỏ, nút reload/đổi draft/pagination bị chặn và dùng thông báo dẫn rõ hai hành động đầu, không modal thiết kế mới.
6. Chỉ gửi decision từ `clean`, pending, saved selection nonempty. Body dùng `selection.review_version`. Thành công phải khớp draft và committed snapshot; set terminal then refresh. Nếu refresh sau decision lỗi, giữ success như UI cũ, khóa double-decision, cho “Tải lại trạng thái”.

### Lỗi và race được chốt

| Tình huống | Hành vi UI |
|---|---|
| `401` / `403` | Giữ edits cục bộ, dừng action; báo session/quyền. Không tạo identity/role ở browser. |
| `413` / `422` | Không retry tự động; giữ edits. 422 yêu cầu tải lại detail nếu server có thể đã thay đổi eligibility/version; 413 báo payload quá lớn (không thể xảy ra từ UI tối đa 1.024 bình thường nhưng vẫn xử lý). |
| `503`, service/shape lỗi | Không retry tự động; giữ edits và mở lại Lưu khi outcome xác định là failure. Không fallback sang sample/legacy. |
| `409` stale/terminal/version ceiling | Đặt `stale`, khóa save/decision, giữ edits nhìn thấy; chỉ “Tải lại” (và hủy edits trước khi áp response). Không ghi đè server. |
| Mạng lỗi/abort sau POST (outcome chưa rõ) | `save-unknown`; giữ checkbox và khóa save/decision, ghi “Chưa xác định lựa chọn đã được lưu. Không gửi lại; tải lại trạng thái.” Chỉ reload detail có thể phân giải; không suy luận DB chưa ghi. Với decision, giữ khóa POST theo `submittedVersionRef` như hiện có, nói kết quả chưa xác định và chỉ cho refresh. |
| Save success, refresh fail | Saved response là committed local evidence; hiện “Đã lưu nhưng chưa tải lại được trạng thái”, không tự POST lại, khóa decision đến khi reload thành công. |
| Double click | Ref lock trước await, disable controls; một request ID/version trong flight. |
| Draft A response đến sau đổi draft B | Abort/active generation cho GET; mutation pins draft A và response chỉ được apply khi selected ID + generation còn khớp. Tuy nhiên navigation bị khóa khi mutation/dirty nên không âm thầm lẫn A/B. |

Response POST `2xx` nhưng không parse/không khớp draft/version/hash là **không rõ/unsafe**, không phải success và không được gửi lại tự động. `AbortController` chỉ hủy fetch/response; không chứng minh POST chưa đến server.

## Nguồn ngoài, khả năng tái dùng

| Ai / nguồn | Đọc 11/11/2026 | Phần tái dùng | Giới hạn |
|---|---|---|---|
| React, [Choosing the State Structure](https://react.dev/learn/choosing-the-state-structure) | React docs v19.3 | Tránh duplicated/contradictory state: set dirty derived từ `savedSelection`/`editingSelection`; phase hữu hạn thay nhiều boolean xung đột. | Là hướng dẫn state, không thay hợp đồng API. |
| React, [useEffect](https://react.dev/reference/react/useEffect) | React docs v19.3 | Cleanup effect khi ID đổi; reuse pattern active/AbortController hiện có để bỏ stale GET. | Không xử lý được mutation đã tới server. |
| MDN, [AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) | baseline browser từ 03/2019, trang sửa 17/09/2025 | Có thể abort fetch/body; phù hợp race tải detail. | Không dùng abort làm bằng chứng POST chưa commit. |

## Phần dùng lại và khoảng trống

- Dùng lại `DraftReviewApp`, `DraftReview`, layout/style/locale message, `draft-adapter` item rendering, exact parser pattern, safe `ApiClientError`, detail abort, locks, rejection reason, decision refresh-error state, tests về XSS text/Unicode span/defang/clipboard/sample.
- Cần điều chỉnh `api-client.ts` sang type/parser **v1 riêng**; không sửa parser legacy để "rộng" ra hay fallback vì v1 thêm trường/versions lớn. Sample vẫn dùng `mode="sample"`, không POST và checkbox giữ trạng thái preview/disabled như hiện tại.
- Cần checkbox/component selection và state transition mới trong app; fixture v1 only cho test client/component (không làm sample route giả POST). Cập nhật VI/EN strings và `docs/PROGRESS.md` theo AGENTS khi implementation.
- Gateway regex chưa v1; sau UI accepted, Engineer phải mở rộng/kiểm gateway và browser same-origin với API v1. In-process API hay fake fetch UI không chứng minh tích hợp gateway/browser.

## Chưa kiểm chứng

Không chạy test, cài dependency, listener, browser, cloud/lab/OpenCTI. Không khẳng định contract tương thích deployment/JWKS/Cloudflare thật. `POST` transport mơ hồ không có idempotency key hay endpoint trạng thái chuyên biệt; thiết kế trên chọn không gửi lại và yêu cầu detail refresh để giảm nguy cơ double write.
