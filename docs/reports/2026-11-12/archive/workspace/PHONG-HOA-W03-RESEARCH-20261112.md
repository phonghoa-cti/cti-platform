# W03-NEXT — nghiên cứu lát cắt CVE liên quan công nghệ

**Ngày kiểm:** 12/11/2026 (UTC+07). **Loại:** nghiên cứu/contract/brief, không triển khai.
**Base chỉ đọc:** `cti-w04-technology-integration` tại `273196e2d23b36172d57cc61b289522786d61b2a` (tree sạch khi đọc).
**Câu hỏi quyết định:** có thể tách một luồng cục bộ nhỏ, hữu ích và không khẳng định sai về phiên bản trước khi có OpenCTI/feed/lab hay không?

## Kết luận để Leader chốt

**Khuyến nghị: điều chỉnh, không dùng trực tiếp connector/live feed trong lát cắt đầu.** Thêm một `CveReadPort` chỉ-đọc được inject vào API, dùng **fixture tổng hợp công khai, đã version hóa**. Port trả CVE đã chuẩn hóa và cặp `vendor/product` mà nguồn nói là liên quan; ứng dụng chỉ ghép cặp này với `TechnologyStore` bằng `trim().casefold()` exact. `software_version` được trả về để người dùng tự kiểm tra, kèm câu cảnh báo bắt buộc: **“Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.”**

Đây là lát cắt nhỏ nhất vì W04 đã có TechnologyStore riêng, API/gateway và mẫu provider HTTP; W03 đã định nghĩa cùng luật khớp và thứ tự KEV → EPSS → CVSS → mới hơn. Nó giải phóng Backend và Frontend làm song song mà không giả có feed, OpenCTI, trạng thái vá hay audit chưa tồn tại.

Không được suy từ tên `vendor/product` rằng bản cài đặt chịu ảnh hưởng. “KEV” nghĩa là CVE có trong catalog đã biết bị khai thác, không phải bằng chứng công nghệ cụ thể của SME bị khai thác. EPSS là xác suất quan sát hoạt động khai thác trong 30 ngày, không phải severity hay risk riêng của doanh nghiệp. CVSS truyền đạt severity/đặc tính lỗ hổng; không thay thế ngữ cảnh môi trường.

## Hiện trạng và phần tái sử dụng

| Hạng mục đã có tại base | Bằng chứng đã đọc | Dùng lại | Không được suy rộng |
|---|---|---|---|
| W04 Technology | `docs/specs/W04-technology-local-contract.md`; `TechnologyStore`, `TechnologyView`, `GET /api/assets/technologies` | ID an toàn, vendor/product trim+casefold, `software_version` display-only, JWT role server-side, `no-store`, lỗi `assets_unavailable` | Không có CVE, feed, CPE/range hay kết luận affected-version. |
| API/W03 cũ | `docs/specs/W03-lo-hong-anh-huong.md`, `api-portal.md` | mục tiêu, luật matching và ranking; quyền đọc Leader/IT/analyst/admin | `/api/cves` và PATCH status chỉ là mô tả lịch sử; chưa có implementation/contract được nghiệm thu. |
| Frontend W04 | `portal/web/components/technology-panel.tsx`, `portal/web/data/technologies.ts`, `DESIGN.md` | provider có thể thay, request/context token chống callback cũ, màn loading/empty/unavailable/403, layout SOC console | Không tái dùng CRUD Technology làm UI CVE, không đưa nút đổi status vào lát cắt read-only. |
| F01 | `PHONG-HOA-F01-CONNECTOR-MATRIX.md` | ref candidate connector `7.260811.0-lts.2` / commit connectors `d50686…`, kế hoạch fixture-first | Chưa có connector chạy, OpenCTI, NVD/KEV/EPSS live hay phép đo lab. |

`api-portal.md` còn mô tả `assets(type=technology)` cũ. Contract W04 đã thay nó bằng `technology_assets`; W03 chỉ đọc `TechnologyStore`, không hồi sinh enum/storage cũ.

## Đối chiếu nguồn sơ cấp (mở trực tiếp ngày 12/11/2026)

| Tổ chức / nguồn | Sự thật dùng cho quyết định | Tái sử dụng / giới hạn |
|---|---|---|
| [OpenCTI — Connectors](https://docs.opencti.io/latest/deployment/connectors/) | Import connector lấy dữ liệu ngoài, chuyển thành STIX 2.1 rồi nhập qua worker; mỗi connector cần `OPENCTI_URL` và token riêng. | Không gọi OpenCTI trong W03 đầu; một live adapter là việc sau, cần quyền/token/lab riêng. |
| [OpenCTI CISA KEV connector README, tag `7.260811.0-lts.2`](https://raw.githubusercontent.com/OpenCTI-Platform/connectors/7.260811.0-lts.2/external-import/cisa-known-exploited-vulnerabilities/README.md) | Connector nhập catalog thành Vulnerability, Software và vendor Identity; gắn `x_opencti_cisa_kev: true`; catalog URL, chu kỳ `P1D` mẫu và mode `KEV_FLAG_ONLY` đều có thật. | Đây chứng minh **connector có mapping vendor/product**, không chứng minh graph/phiên bản OpenCTI của Phong Hỏa đã chứa dữ liệu khớp được. TLP:CLEAR là default connector, không phải tự động là policy chia sẻ của dự án. |
| [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Catalog là nguồn authoritative được connector trỏ tới cho CVE đã bị khai thác; record connector giữ CVE, ngày và deadline nguồn. | Trình đọc bị CISA trả 403 với JSON/catalog trong lượt này; chưa xác minh trực tiếp schema hiện hành, terms hay catalog `as_of`. Không gọi `kev_due` là hạn bắt buộc cho SME; đó là thông tin nguồn/chỉ dẫn cần diễn giải. |
| [FIRST EPSS — Get the Data](https://www.first.org/epss/data), [API](https://api.first.org/epss/), [FAQ](https://www.first.org/epss/faq) | EPSS score là xác suất `0..1`, cập nhật hằng ngày; API lookup, CSV phù hợp bulk; API không có CVE trả `200` + mảng rỗng. Ví dụ API đã mở trả `CVE-2021-44228` score/date. | Lưu `epss_as_of`; `null` nghĩa fixture/source không có score, **không** phải `0`. Không đặt nhãn High theo ngưỡng tùy tiện; FIRST nói không có ngưỡng phổ quát. |
| [FIRST CVSS v3.1](https://www.first.org/cvss/v3.1/specification-document), [CVSS v4.0](https://www.first.org/cvss/specification-document) | CVSS là framework mở mô tả đặc tính và severity, có nhiều metric group; v4.0 hiện tại theo FIRST, nhưng dữ liệu feed có thể là v3.1/v4.0. | Port giữ `cvss_base` và `cvss_version`; chỉ rank base score hợp lệ `0..10`, không trộn vector/phiên bản hoặc coi `null=0`. |

Nguồn OpenCTI/CISA/FIRST chỉ chứng minh ý nghĩa/mapping tổng quát. Chúng không chứng minh fixture phù hợp OpenCTI runtime, tính mới của feed, license phân phối lại, hay CVE áp dụng vào một phiên bản đã cài.

## Scope: làm đầu tiên và để sau

| Giai đoạn | Bao gồm | Loại trừ có chủ ý |
|---|---|---|
| **W03-R (khuyến nghị triển khai kế)** | `GET /api/cves` read-only; `CveReadPort`; fixture tổng hợp public; exact name match; filter KEV/technology/search; cursor; ranking xác định; source/as-of; UI danh sách/chi tiết read-only và trạng thái error/empty. | OpenCTI/network/feed, CPE/alias/regex/prefix, version-range, status/audit/PATCH, deadline-overdue KPI, sửa Technology CRUD. |
| **W03-S (sau acceptance W03-R)** | SQLite status theo cặp technology/CVE, optimistic concurrency, append-only audit, note và summary Leader. | Auto-remediation, kết luận patched/not affected tự động. |
| **W03-L (sau lab và policy dữ liệu)** | Adapter OpenCTI/KEV/EPSS có cache, provenance, refresh, tiêu chí stale và phép đo lab. | Không backfill/bật feed production trước khi xác nhận terms, TLP và runtime. |

## Contract đề xuất — W03-R

### 1. Port và fixture

Tạo interface nội bộ, không phụ thuộc OpenCTI:

```text
CveReadPort.list_candidates() -> CveDataset
CveDataset = { dataset_id, source_as_of, retrieved_at, candidates[] }
```

`source_as_of` là instant ISO-8601 của snapshot nguồn, `retrieved_at` là instant fixture được đóng gói/cập nhật; cả hai bắt buộc có timezone và không được thay bằng “now” trong response. `dataset_id` là định danh immutable (ví dụ SHA-256 fixture) để tái hiện kết quả. Fixture chỉ gồm dữ liệu công khai/tổng hợp, có provenance URL cho từng nguồn; không dùng dữ liệu TLP hạn chế.

Mỗi candidate canonical:

```json
{
  "cve_id": "CVE-2026-0001",
  "title": "string, 1..300 code point",
  "published_at": "2026-01-02T00:00:00Z",
  "kev": {"known_exploited": true, "due_date": "2026-02-03", "source": "CISA KEV", "as_of": "2026-01-10T00:00:00Z"},
  "epss": {"score": 0.94, "percentile": 0.99, "as_of": "2026-01-10"},
  "cvss": {"base_score": 9.8, "version": "3.1"},
  "affected_products": [{"vendor": "Fortinet", "product": "FortiOS"}],
  "advisory_url": "https://example.invalid/advisory"
}
```

Validation before any response: canonical `CVE-YYYY-N+` uppercase; title nonblank; finite numeric EPSS `0..1`, percentile `0..1`, CVSS `0..10`; valid RFC3339 date/integer fields; affected `vendor/product` pass the same W04 trim/control-char/key rules. `kev` is mandatory overlay data: `known_exploited:false` means the CVE was absent in the **complete fixture KEV snapshot** at its stated `as_of`; missing/unreadable KEV dataset makes the whole port unavailable (503), never silently false. Optional `due_date`, EPSS, percentile, CVSS and published date serialize `null` when the specific source lacks them. Invalid dataset/row is fail-closed `cves_unavailable`, never a partial list.

### 2. HTTP read contract

`GET /api/cves?kev=true|false&asset_id=<safe-int>&q=<CVE-or-title>&limit=1..100&cursor=<opaque>`.

* Absent `kev` means both values. `asset_id` is a W04 Technology ID, not legacy asset ID. `q` is trimmed 1..128 code point and only case-insensitive substring over canonical CVE ID/title; no regex. `limit` default 25. Cursor is an opaque signed/encoded key of the last stable rank, not an offset. Unknown/duplicate query name, boolean coercion, bad ID/cursor or out-of-bound input → `422 invalid_cve_query` before store/port work.
* **`status` is deliberately absent in W03-R.** Existing `?status=open` is historical design only; accepting it now would imply a persisted triage state that does not exist. Frontend hides the status filter and all mutation controls until W03-S.
* Auth is first, reusing verified server identity/role. `leader|it|analyst|admin` may GET; 401 `authentication_required`, 403 `forbidden`, 503 `cves_unavailable`. All success/error responses carry `Cache-Control: no-store` and `Vary: Cf-Access-Jwt-Assertion`.
* Read active technologies once from `TechnologyStore` in a single read transaction before matching. The response is a **snapshot** of that technology read plus exactly one fixture dataset revision; a concurrent create/update/delete affects a later request, not this page. No stale callback/mutation is attempted by the GET endpoint.
* Payload ceiling: 1 MiB UTF-8 serialized body. Build/page one item beyond the selected limit; if the bounded response exceeds cap, return 503 `cves_unavailable` rather than truncate without a cursor. Fixture itself is small/bounded in W03-R; a later live adapter needs separate paging/cap proof.

Exact normal response for IT/analyst/admin:

```json
{
  "items": [{
    "cve_id": "CVE-2026-0001",
    "title": "Example vulnerability",
    "kev": true,
    "kev_due_date": "2026-02-03",
    "epss_score": 0.94,
    "epss_percentile": 0.99,
    "epss_as_of": "2026-01-10",
    "cvss_base_score": 9.8,
    "cvss_version": "3.1",
    "published_at": "2026-01-02T00:00:00Z",
    "advisory_url": "https://example.invalid/advisory",
    "matches": [{
      "technology_id": 7,
      "vendor": "Fortinet",
      "product": "FortiOS",
      "software_version": "7.2",
      "match_reason": "vendor_product_exact_casefold",
      "version_assessment": "not_performed"
    }],
    "priority": 1
  }],
  "page": {"next_cursor": null, "limit": 25},
  "source": {"dataset_id": "sha256:...", "source_as_of": "2026-01-10T00:00:00Z", "retrieved_at": "2026-01-10T01:00:00Z"},
  "notice": "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá."
}
```

Một CVE xuất hiện **một lần** trên trang, dedupe bằng `cve_id`; `matches` gồm mọi technology active khớp, sắp ID tăng dần và không lặp cặp `(technology_id, vendor-key, product-key)`. Nếu asset filter có Technology tồn tại nhưng không khớp thì `200`, `items:[]`; ID không tồn tại → `404 technology_not_found`; dữ liệu hợp lệ nhưng không match bất kỳ CVE → `200` rỗng. Đây là ba trạng thái UI khác `503` source/port hỏng.

Leader nhận cùng `summary` (`matched_cves`, `kev_cves`, `overdue_from_source_due_dates`) và tối đa danh sách rút gọn `cve_id,title,kev,epss_score,cvss_base_score,priority,match_count`; không trả software version, technology ID/name, advisory URL hoặc raw description. `overdue` dùng clock inject được và chỉ là “quá ngày do nguồn KEV nêu”, không biến thành SLA SME.

### 3. Matching, rank và null

1. W04 `vendor/product` được trim và casefold exact; so với từng `affected_products` chuẩn hóa như trên. Không NFKC, alias, CPE, regex, prefix, punctuation folding hay version/range parse.
2. `software_version` chỉ đi theo match để hiển thị; `version_assessment` luôn `not_performed` trong W03-R. Giao diện không dùng màu “affected”, “safe” hay “patched” từ tên/phiên bản này.
3. Rank tăng dần `priority` theo tuple: `(kev true trước, EPSS có/giảm dần, CVSS có/giảm dần, published_at có/giảm dần, cve_id tăng dần)`. Giá trị `null` luôn đứng sau một số hợp lệ ở từng metric. Tie cuối `cve_id` canonical tạo thứ tự/cursor ổn định.
4. `published_at` null/không hợp lệ: null đứng sau; dữ liệu không hợp lệ trong fixture làm 503 ngay từ validation. Không dùng ngày source refresh thay published date.

## Trạng thái/audit để sau — W03-S

**Khuyến nghị scope:** status thuộc **cặp `(technology_id, cve_id, vendor_key, product_key)`**, không phải chỉ `cve_id` toàn công ty. Một CVE có thể khớp nhiều công nghệ/phiên bản; “đã vá” trên một technology không nói gì về technology khác. Bảng cũ đề xuất `cve_status(cve_id,...)` không đủ granularity.

| Thiết kế sau này | Khuyến nghị |
|---|---|
| Trạng thái | `open|patching|patched|not_affected`; default chỉ khi row tồn tại? Không: UI W03-R ghi “chưa có trạng thái”, không tạo row giả. |
| Identity/lịch sử | `cve_technology_status` có key quan hệ, `status_version`, actor/time/note và snapshot vendor/product/software_version tại lúc ghi; append-only `cve_status_audit` chứa before/after và fixture `dataset_id`. |
| Xóa/sửa technology | Không hard-delete status/audit. Soft-deleted hoặc đổi vendor/product bị ẩn ở list hoạt động nhưng còn truy vết; nếu tên đổi, status cũ không tự áp cho match mới. |
| Concurrency/rollback | `expected_status_version` strict safe integer; update status/audit cùng một transaction; stale 409, unknown/unavailable rollback và 503. Không auto-retry POST. |
| Quyền | IT/analyst/admin ghi; Leader không ghi. Note bound/validate, không tạo kết luận kỹ thuật tự động. |

## Acceptance matrix đề xuất (chưa chạy)

| Nhóm | Fixture/tình huống phải có | Kết quả yêu cầu |
|---|---|---|
| Data quality | CVE có true/false KEV; null EPSS/CVSS/date; số NaN, >range, date hỏng, CVE/match trùng | true khác null/source unavailable; null không thành 0; fixture hỏng 503 không partial; dedupe/matches deterministic. |
| Auth/redaction | missing/bad JWT, leader-only, IT/analyst/admin, role lẫn | 401 trước port; leader chỉ summary/reduced fields; roles còn lại DTO đầy đủ; header no-store/Vary. |
| Matching | case khác nhau, whitespace, version khác nhau, alias/prefix/CPE-looking text, one CVE→two technologies | chỉ vendor/product casefold exact; version display-only/not_performed; không false-positive alias; one CVE/many matches. |
| Ranking/paging | KEV/non-KEV, equal/missing EPSS/CVSS/date, CVE ID tie; page 1→2 | tuple đúng, `priority` liên tục, cursor không bỏ/lặp; clock inject cho summary due-date. |
| Read failure/limits | port missing, dataset invalid, TechnologyStore read fails, oversized response/query invalid | 503 `cves_unavailable`, 422 before dependencies, no partial/silent false/unknown status. |
| Stale context/UI | request A chậm rồi đổi filter/route/provider, 200 rỗng, 404 asset, 503 | callback A không đổi context B; empty/not-found/unavailable tách rõ; không retry GET POST vì không có POST. |

## Brief triển khai độc lập (chờ Leader chọn)

### Backend — Sol medium, tree riêng

**Mục tiêu:** W03-R read-only tại exact base/branch Leader chỉ định, không live adapter và không migration status.

1. Đọc `AGENTS.md`, W03, W04 local contract, contract này và W04 auth/error tests; giữ mọi thay đổi có sẵn.
2. Tạo fixture public/tổng hợp có manifest/provenance + immutable `dataset_id`; implement `CveReadPort`/fixture adapter và schema strict fail-closed.
3. Inject port opt-in vào `create_app`; implement exact `GET /api/cves`, auth-first, TechnologyStore snapshot, exact matching/rank/cursor/redaction/error/header/cap. Không sửa `/api/assets` legacy hay thêm PATCH/status.
4. Viết RED→GREEN tests theo acceptance matrix, nhất là null≠false, name≠version affected, leader redaction, port hỏng và cursor tie. Chỉ fixture/local SQLite/JWT tổng hợp; không network/feed/OpenCTI.
5. Báo SHA, diff, lệnh/exit/test count và giới hạn local. Không merge/push/deploy.

**Tiêu chí giao frontend:** JSON fixture/wire schemas và mã lỗi ổn định đã có test; endpoint không tự tạo/migrate DB; cổng integration chỉ mở sau Backend evidence.

### Frontend — Sol medium, tree riêng

**Mục tiêu:** UI W03-R read-only, có thể bắt đầu với provider fixture khớp DTO trên, không đợi backend runtime.

1. Đọc `DESIGN.md`, W03 và contract này; dùng pattern provider/context ownership của W04, không redesign và không tạo status control.
2. Tạo typed `CveProvider`, strict DTO parser và fixture provider; HTTP provider chỉ route exact `GET /api/cves`, map 401/403/404/422/503 thành trạng thái UX đúng. Không gọi OpenCTI.
3. Dựng `/lo-hong`: panel nguồn/as-of, filter KEV/technology/search, bảng 6–10 row/pagination, detail read-only, tooltip tiếng Việt cho KEV/EPSS/CVSS và disclaimer version. Reuse token SOC/dark table/focus/mobile horizontal scroll.
4. Phân biệt loading, empty valid, technology-not-found, unauthorized, unavailable; stale completion không ghi đè context mới. Leader summary chỉ dùng DTO rút gọn khi server trả role đó.
5. RED→GREEN component/provider tests từ matrix; báo SHA/diff/lệnh/exit/count. Không browser/lab/merge/deploy.

## Integration gate sau hai brief

1. Leader review DTO/codes/query/cursor và quyết định contract trước khi hai tree đổi code.
2. Backend evidence phải chứng minh fixture port + API contract local; Frontend evidence phải chứng minh fixture UI/parser và stale/error states. Chỉ khi hai bên cùng exact DTO, mới giao một integration owner nối gateway/local runner.
3. Integration chỉ kiểm local synthetic end-to-end. Cloudflare/JWKS thật, browser acceptance nếu chưa chạy, OpenCTI, CISA/FIRST feed, license/TLP policy, lab resource, production là cổng riêng — không được suy ra PASS từ integration local.

## Unknowns và giới hạn còn lại

* CISA catalog JSON trả 403 cho công cụ đọc; chưa trực tiếp kiểm schema entry, `dueDate` semantics, license/redistribution terms hoặc freshness tại thời điểm chạy. Không suy ra catalog không tồn tại.
* Chưa dùng OpenCTI schema/GraphQL hay connector runtime; connector README chứng minh mapping thiết kế, không chứng minh data/hành vi của version platform candidate trên lab.
* EPSS/CVSS/KEV freshness, clock/skew, source failures, historical reproducibility và any quota cần được xác minh khi W03-L; fixture W03-R phải tự mang `as_of`.
* Không có implementation/test/runtime/lab/browser mới trong lượt nghiên cứu này. W04 chỉ được dùng làm evidence dependency local đã nghiệm thu, không phải bằng chứng W03.

## Quyết định cần Leader

Chốt **W03-R read-only fixture-first** và contract trên. Sau đó Backend và Frontend có thể làm song song trên tree độc lập; status/audit và live OpenCTI/feed giữ ngoài scope để không tạo “đã vá/không ảnh hưởng” giả.
