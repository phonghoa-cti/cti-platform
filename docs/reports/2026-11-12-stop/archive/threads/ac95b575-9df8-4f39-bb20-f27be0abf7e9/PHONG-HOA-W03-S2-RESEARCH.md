# W03-S2 — lọc trạng thái toàn danh sách và tổng hợp Leader

**Ngày kiểm:** 12/11/2026 (UTC+07) · **Loại:** nghiên cứu/brief, không triển khai.
**Ref chỉ đọc:** `867bdcaeffded177ee119fe5e05015c4700979db` tại `ROOT/cti-w03-status-integration`; tree sạch lúc đọc.

## Kết luận

**Đề xuất: thêm read-model/route riêng `GET /api/cves/status-view`, không thay wire/cursor của `GET /api/cves` W03-R.** Route mới tái dùng dataset, Technology snapshot, rank và status store S1 để ghép trạng thái hiện hành theo *quan hệ CVE–technology*. Đây là lát cắt nhỏ nhất tránh làm hỏng parser/cursor strict đã nghiệm thu, vẫn cho lọc trước phân trang và summary đã lược dữ liệu cho Leader.

`patched` và `not_affected` chỉ là ghi nhận của người dùng, không chứng minh vá, đánh giá phiên bản, remediation hay hết hạn KEV.

## Hiện trạng, nguồn và tái dùng

| Nguồn / ai đã làm | Đã kiểm ở ref | Tái dùng | Giới hạn |
|---|---|---|---|
| W03-R: `portal_api/cves.py`, `W03-read-local-contract.md` | rank KEV→EPSS→CVSS→published→CVE, cursor canonical snapshot/context, summary detail/leader, cap 1 MiB, read-only Technology | validator dataset, snapshot/rank/query/cursor/error/header | Wire summary không có status; không sửa nó trong S2. |
| W03-S1: `portal_api/cves_status.py`, `W03-status-local-contract.md` | status/audit theo `(technology_id,cve_id,vendor_key,product_key)`, review_required, history cursor | Context, status taxonomy, record validation, ro SQLite | Không có list filter/KPI; Leader không gọi status/history. |
| Specs W03/W01 | cần lọc trạng thái, Leader chỉ xem tóm tắt và có “quá hạn” | mục tiêu/ngôn ngữ UI | chưa định nghĩa multi-technology/timezone/mẫu đếm. |
| SQLite chính thức, kiểm 12/11 | một writer; read transaction là snapshot; BEGIN IMMEDIATE có thể busy | S2 GET lấy Technology/status cùng read transaction; cursor bind snapshot status | chưa chứng minh runtime/filesystem dự án. [Isolation](https://www.sqlite.org/isolation.html), [Transactions](https://www.sqlite.org/lang_transaction.html) |
| OWASP Authorization, kiểm 12/11 | least privilege và kiểm quyền mỗi request | projection Leader tách cấu trúc, chặn trước dependency | guidance, không phải policy. [Nguồn](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| PR mở, kiểm đọc 12/11 | #1 `feat/cap-nhat-bo-khoi-dong`, #46 `feat/x01-nen-tang`, cùng base main, cập nhật 21/10 | không có PR làm base S2 | chỉ metadata đọc, chưa review/merge. [#1](https://github.com/phonghoa-cti/cti-platform/pull/1), [#46](https://github.com/phonghoa-cti/cti-platform/pull/46) |

## Semantics đề xuất

Status thuộc **quan hệ**, không thuộc CVE chung. Một CVE có nhiều technology active tạo nhiều relation.

| Bucket | Điều kiện relation active | Quy tắc |
|---|---|---|
| `unset` | không có StatusRecord đúng key hiện hành | không tạo row `open` giả |
| `open`, `patching`, `patched`, `not_affected` | `record.status` hiện hành | record context cũ vẫn giữ status, có thêm overlay review |
| `review_required` | có record và saved `technology_record_version` **hoặc** `dataset_id` khác context hiện hành | không phải status thứ năm, không tự đổi record |
| inactive/deleted/no-match | không là relation list | không kế thừa/không lộ; audit S1 vẫn giữ |

`status=<bucket>` chọn **CVE có ít nhất một relation active** thuộc bucket. Một CVE có thể có ở nhiều filter. Detail luôn trả mọi relation active, với `{status,status_version,review_required,updated_at}`; Leader không bao giờ nhận technology/version/note/actor/history/status của relation.

`summary.status_relations` đếm relation theo năm trạng thái persisted; `review_required_relations` đếm overlay. `actionable_cves` đếm CVE một lần nếu có ít nhất một `unset|open|patching|review_required`. Không cộng relation thành CVE và không tự đặt “status xấu nhất”.

Giữ ranking W03-R nguyên vẹn; status không đổi priority/KEV. `kev_due_date` là ngày không timezone: route sinh `summary.as_of_date` theo UTC server, `overdue_kev_cves` đếm CVE KEV có due date khác null, `< as_of_date`, và actionable. Ngày bằng `as_of_date` là due today; null không overdue. `as_of_date` phải nằm trong context/cursor, nên qua nửa đêm UTC trả 409 thay vì trộn định nghĩa quá hạn.

## Ba phương án

| Phương án | Lợi | Rủi ro | Kết luận |
|---|---|---|---|
| A. Thêm status vào `GET /api/cves` | ít route | đổi wire/query/cursor W03-R, có thể phá parser strict | Không chọn |
| B. `GET /api/cves/status-view` **(khuyến nghị)** | giữ W03-R, tái dùng logic, projection/cursor riêng, handoff tách được | thêm adapter read-model/gateway route | Chọn |
| C. Frontend tải hết list rồi gọi status từng relation | ít backend ban đầu | N+1, snapshot lệch, lộ dữ liệu, không có paging/summary tin cậy | Loại |

## Contract S2 đề xuất (chờ Leader chốt)

`GET /api/cves/status-view?kev=true|false&asset_id=<id>&q=<text>&status=unset|open|patching|patched|not_affected|review_required&limit=1..100&cursor=<opaque>`.

Auth trước parse/dependency; role trước dataset/SQLite. `it|analyst|admin` (kể cả mixed role) nhận detail; leader-only nhận summary; role khác 403, JWT lỗi 401. Leader dùng `asset_id` là 403 trước dependency như W03-R; status filter được phép vì projection vẫn aggregate. Query lạ/lặp/control/cursor sai là 422 `invalid_cve_status_query`; dependency/schema/cap hỏng là 503; all responses `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`.

Detail kế thừa item W03-R và thêm trên mỗi match `status` nullable, `status_version` nullable, `review_required`, `status_updated_at` nullable. Summary giữ nguyên `{cve_id,title,kev,epss_score,cvss_base_score,priority,match_count}`; không có matches, technology, version, note, actor, audit hoặc status. Envelope chung:

```json
{
  "summary":{
    "matched_cves":0,"kev_cves":0,
    "status_relations":{"unset":0,"open":0,"patching":0,"patched":0,"not_affected":0},
    "review_required_relations":0,"actionable_cves":0,
    "overdue_kev_cves":0,"as_of_date":"YYYY-MM-DD"
  },
  "page":{"limit":25,"next_cursor":null}
}
```

Counts áp sau base filter `kev/asset/q` nhưng trước status/paging; cards vì vậy mô tả toàn scope đã chọn. Count sau status filter là quyết định khác, không tự thêm.

Một request validate immutable dataset đúng một lần, dùng **một** ro SQLite transaction để validate schema W04/S1 và đọc active Technology/status. Không initialize/migrate/audit/write. Snapshot hash gồm dataset, technology, status version/context relation, `as_of_date`, view; context hash gồm `view,kev,asset_id,q,status,limit,as_of_date`. Cursor canonical `{v:1,snapshot,context,after}`, phiên bản tách W03-R: mismatch context=422; status/technology/dataset/UTC-date đổi=409 `status_snapshot_changed`. Response cap 1 MiB; status schema/row lỗi fail-closed 503, không coi là unset.

## Brief sau quyết định

### Backend

- Read service/DTO/parser riêng, inject opt-in; không đổi `/api/cves`, S1 routes, auth hay W04 CRUD.
- Tái dùng W03-R validation/rank và S1 Context/record validation; derive UTC date một lần/request; projection Leader dựng riêng ngay từ service.
- Gateway chỉ exact GET route. Tests: một CVE nhiều relation/many buckets; unset/review; inactive/delete/key/dataset drift; null due; due yesterday/today; role/redaction/asset denial; rank invariant; aggregate equations; status mutation/UTC rollover cursor 409; SQL hash/schema/audit trước-sau GET/failure; caps/errors.

### Frontend

- Provider/parser status-list tách `CveProvider`; strict detail/summary DTO, cap/error/opaque cursor.
- Detail có filter + marker từng match, không redesign; Leader chỉ cards/list aggregate và không gọi status/history/technology API.
- Reset page khi đổi base/status filter; 409 chỉ explicit reload; callback cũ không cập nhật context mới. Sample memory-only.
- Tests parser redaction, multi-bucket, null, cards, paging/conflict, role switch, 401/403/422/503/cap. Unit test không là browser/API thật.

### Cổng tích hợp

Pin Backend/Frontend SHA; đối chiếu route/query/DTO/error/notice/cursor và gateway allowlist. Với fixture + cùng SQLite kiểm filter trước paging, equations, leader không lộ field nhạy cảm/không gọi API ngoài, 409 sau status/Technology/dataset change, GET không đổi SQL. Browser chỉ sau HTTP gate. Không suy từ local sang CISA/OpenCTI/feed, Cloudflare/JWKS/HTTPS, mobile, lab hay production.

## Điều cần Leader chốt / chưa xác minh

1. Chọn route B và `actionable_cves` OR-based thay vì bịa một status CVE duy nhất.
2. Chấp nhận UTC/date-only cho overdue hoặc bỏ KPI nếu nghiệp vụ cần timezone doanh nghiệp.
3. Leader chỉ xem aggregate theo selected base scope, không status/technology/note/actor/audit.

Không chạy test, không sửa source/tree/ledger, không live feed/LLM/OpenCTI/lab/cloud/browser. CISA catalog trực tiếp trả HTTP 403 khi kiểm nên không suy định nghĩa due-date từ nguồn đó; semantics due-date là đề xuất. Chưa kiểm SQLite runtime/concurrency thật, mobile, license/source freshness dữ liệu thật.
