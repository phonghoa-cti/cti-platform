# W04-TECHNOLOGY-NEXT — nghiên cứu tài sản công nghệ để nối W03

**Ngày kiểm:** 11/11/2026 (UTC+07). **Loại công việc:** nghiên cứu và brief; không sửa mã sản phẩm, không chạy test mới, không cài thư viện, không gọi lab/cloud/feed.

## Kết luận ngắn

Nên **điều chỉnh AssetStore hiện hữu bằng một kho `technology_assets` tách riêng**, lưu ba trường bắt buộc `vendor`, `product`, `version` cùng các khóa so sánh nội bộ. Không dùng CPE làm khóa bắt buộc, không import OpenCTI/NVD và không làm so khớp dải phiên bản. Đây là lát cắt nhỏ nhất có thể đưa dữ liệu cho W03, đồng thời không đổi hợp đồng domain/CIDR hoặc W02.

Lý do: CPE 2.3 thực sự có các thành phần vendor/product/version, nhưng CPE Match String Range là một lớp logic áp dụng riêng phức tạp hơn tên CPE. W03 đã chốt chỉ khớp vendor+sản phẩm không phân biệt hoa thường và để con người kiểm phiên bản. Vì vậy ép người dùng nhập CPE, hay tự suy ra/range-match từ chuỗi phiên bản, vừa tăng sai khớp vừa mở rộng quá phạm vi.

## Baseline và ranh giới đã kiểm

| Hạng mục | Bằng chứng đã đọc | Kết luận dùng cho lát cắt |
|---|---|---|
| Ref duy nhất | `cti-w04-local-integration` tại `8a767314b654d39c1ddc2995b7919c44a5b7027a`, working tree sạch và HEAD đúng SHA | Không lấy `main`, PR #1/#46 hay ref khác làm nền triển khai. |
| W04 hiện có | `portal_api/assets.py`; `docs/specs/W04-assets-local-contract.md` | `AssetStore` đã có SQLite per-operation, `BEGIN IMMEDIATE`, optimistic version, audit cùng transaction, quyền server-side và lỗi ổn định; chỉ nhận `domain|ip_range`. |
| W02 | `portal_api/ioc_lookup.py`, schemas, tests cùng ref | Asset snapshot hiện làm `asset_match` và effective allowlist chỉ cho domain/CIDR. Công nghệ **không** tham gia snapshot, allowlist hoặc IOC lookup. |
| W03 | `docs/specs/W03-lo-hong-anh-huong.md` | Đầu vào cần vendor/product/version; đối chiếu chỉ vendor+product case-insensitive; version chỉ hiển thị cho người kiểm. |
| UI | `docs/design/DESIGN.md` | Có thể thêm tab Công nghệ theo tab/bảng/form hiện hữu; research này không thiết kế lại UI. |
| PR đang mở (đọc GitHub 11/11) | [#46](https://github.com/phonghoa-cti/cti-platform/pull/46) `36259c…` và [#1](https://github.com/phonghoa-cti/cti-platform/pull/1) `8d9d7d…` | Không phải baseline W04 này và không chứa bằng chứng để đổi hợp đồng technology. |

`AssetStore` hiện đã bảo vệ đúng các điểm nên tái dùng: canonical/validate khi đọc DB, giới hạn `id`/record `version` ở số JSON an toàn, soft-delete, audit before/after và biến lỗi SQLite thành unavailable. Cần tách rõ **record version** (đồng thời ghi dữ liệu) với **software version** (ví dụ `7.2.1`, chỉ là thông tin phần mềm).

## Ai đã làm, phần dùng lại được và giới hạn

| Tổ chức / nguồn gốc trực tiếp (đã kiểm 11/11) | Phần chứng minh | Phần tái sử dụng | Giới hạn / quyết định |
|---|---|---|---|
| [NIST IR 7695 — CPE Naming 2.3](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7695.pdf), 08/2011; [MITRE CPE specification](https://cpe.mitre.org/specification/) | CPE mô hình hóa tên lớp sản phẩm và nêu rõ vendor/product/version; Naming khác Name Matching. | Mượn **khái niệm tách trường** vendor/product/version, không mượn định dạng CPE làm input v1. | Trang CPE của MITRE ghi archive. Một tên CPE không xác nhận cài đặt thực tế hoặc CVE ảnh hưởng. |
| [CVE Program — CPE Applicability Guide v1.3](https://www.cve.org/Resources/Roles/Cnas/CPEinCVERecordsGuide.pdf), cập nhật 02/07/2026 | CPE match range có ranh giới `versionStart/End` và đòi hỏi CPE Name Matching + logic riêng. | Là bằng chứng để **loại** range matching khỏi W04/W03 hiện tại. | Không phải thư viện thực thi hay chứng minh dữ liệu CVE của dự án đã có/đúng. |
| [NVD Products/CPE API](https://nvd.nist.gov/developers/products), tài liệu hiện hành | Có CPE names, match strings, pagination và metadata/deprecation. | Để ngỏ extension sau này: một CPE do người duyệt chọn có thể được lưu riêng với source/timestamp. | Không gọi API, không lấy Dictionary; không suy một chuỗi vendor/product thành CPE. |
| [OpenCTI CVE connector](https://github.com/OpenCTI-Platform/connectors/blob/master/external-import/cve/README.md), `master` tại ngày kiểm | Connector có thể resolve CPE thành Software gắn Vulnerability, nhưng cảnh báo volume lớn; yêu cầu OpenCTI >=6 và NVD API key. [OpenCTI data model](https://github.com/OpenCTI-Platform/opencti/blob/master/docs/docs/usage/data-model.md) đặt dữ liệu trên STIX 2.1. | Chỉ tái dùng **mô hình khái niệm** Software/Vulnerability cho W03 tương lai. | Không nhúng connector/OpenCTI vào local AssetStore: tăng phụ thuộc, cần key/lab và có rủi ro volume. Chưa chạy mã nguồn hoặc kiểm license/version runtime trong task này. |

Giấy phép: mã nguồn OpenCTI Community Edition hiện công bố Apache-2.0 trong [repository](https://github.com/OpenCTI-Platform/opencti); nghiên cứu này không sao chép mã của nó. Điều khoản/giấy phép dữ liệu NVD và khả năng phân phối lại dữ liệu chưa được xác minh cho triển khai này; v1 không tải hay lưu dữ liệu đó.

## So sánh cách lưu

| Phương án | Phù hợp AssetStore/API | Rủi ro / chi phí | Kết luận |
|---|---|---|---|
| A. Thêm `type=technology` và các cột nullable vào `assets` | Dùng lại một bảng/route, nhưng thay invariant `Asset`/`AssetView`, enum, index unique và mọi consumer domain/CIDR. | Có nguy cơ thay shape W02/W04 đã nghiệm thu; các ràng buộc canonical/asset-match hiện không áp dụng được. | Không chọn. |
| B. **Bảng/route technology tách riêng, cùng pattern `AssetStore`** | Tái dùng transaction, auth, error envelope, audit và frontend provider; giữ domain/CIDR schema/route/matcher nguyên vẹn. | Có một store/DTO/audit mới và migration additive. | **Khuyến nghị.** |
| C. Chỉ lưu CPE URI rồi parse/match | Tương thích tốt khi đã có CPE curated. | CPE có 11 component, escape, deprecation và range/applicability; người dùng dễ chọn nhầm. Nó vượt W03 hiện tại. | Không chọn cho v1; chỉ extension có kiểm duyệt sau này. |

## Hợp đồng dữ liệu đề xuất (v1, chưa triển khai)

### Đối tượng và chuẩn hóa

```json
{
  "id": 41,
  "vendor": "Fortinet",
  "product": "FortiOS",
  "version": "7.2.1",
  "note": "VPN gateway HN",
  "created_by": "it-subject",
  "created_at": "2026-11-11T16:00:00Z",
  "updated_at": "2026-11-11T16:00:00Z",
  "version_id": 1
}
```

`version_id` ở response là version optimistic của **bản ghi**, đặt tên khác `version` để không nhập nhằng với phiên bản phần mềm. Nếu phải giữ quy ước Asset API hiện có, key ngoài có thể là `record_version`; không dùng cùng một key cho hai nghĩa.

| Trường | Quy tắc ghi/lưu | Quy tắc W03 |
|---|---|---|
| `vendor`, `product` | string 1..128/256 Unicode code points sau trim; cấm control chars; lưu display nguyên dạng đã trim và internal key `NFKC().casefold()` (không công khai). | So sánh equality của internal key, không phân biệt hoa thường. Không map alias (`MS` ≠ `Microsoft`). |
| `version` | string 1..128, trim, cấm control chars, giữ nguyên display; **không** parse số, wildcard, comparator hoặc range. | Chỉ trả/hiển thị để analyst tự so với advisory. Không dùng để include/exclude CVE. |
| `note` | string 0..500 như W04 hiện hữu. | Không là dữ liệu đối chiếu. |
| duplicate active | unique `(vendor_key, product_key, version_display)`; soft-deleted row không cấm tạo mới. | Hai dòng khác phiên bản được phép vì là hai khai báo khác nhau; casefold vendor/product chỉ tạo một bản ghi. |

Chọn `NFKC + casefold` chỉ làm khóa so sánh cục bộ, không phải chuẩn CPE và không khẳng định hai hãng/sản phẩm là cùng một thực thể. Không tự bỏ dấu, dịch tên, thay dấu gạch, hoặc sinh alias. Những phép đó cần bảng alias được curated có nguồn, người duyệt và audit riêng.

### API và quyền

Các endpoint mới tách khỏi `/api/assets` hiện có:

| Route | Body / kết quả | Điều kiện |
|---|---|---|
| `GET /api/assets/technologies` | `{ "items": [TechnologyView] }`, ID tăng dần, tối đa 1.000 | JWT hợp lệ + server-side role `it|analyst|admin`; `leader`/thiếu role: 403 trước query/DB. |
| `POST /api/assets/technologies` | exact `{vendor,product,version,note}` → 201 `TechnologyView` | JSON ≤8 KiB, Origin đúng; duplicate active 409 `technology_exists`; malformed/extra key 422 `invalid_technology`. |
| `PUT /api/assets/technologies/{id}` | exact POST + `expected_version` strict JSON-safe positive int → 200 | stale 409 `technology_conflict`; missing 404 `technology_not_found`. |
| `DELETE /api/assets/technologies/{id}?expected_version=N` | 204 | soft delete + audit một transaction. |

Tất cả response/error giữ `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`, error envelope hiện hữu và không echo raw input/SQLite/token. Auth/role/Origin phải chạy trước parse body hoặc DB, giống W04; không tin header/claim role từ client. POST/PUT/DELETE **không tự retry**. Khi gateway/upstream không thể xác nhận outcome, frontend báo `unknown-mutation`, khóa gửi lại và chỉ đề nghị GET đối soát.

### SQLite, migration và audit

Migration additive, chỉ chạy trong explicit `initialize()`/bootstrap opt-in, không ở request và không đổi bảng `assets`/`asset_audit`:

```sql
technology_assets(
  id INTEGER PRIMARY KEY,
  vendor_display TEXT NOT NULL, vendor_key TEXT NOT NULL,
  product_display TEXT NOT NULL, product_key TEXT NOT NULL,
  software_version TEXT NOT NULL, note TEXT NOT NULL,
  record_version INTEGER NOT NULL, created_by TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT NULL
);
CREATE UNIQUE INDEX technology_active_identity
 ON technology_assets(vendor_key, product_key, software_version)
 WHERE deleted_at IS NULL;
technology_asset_audit(
  id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor_subject TEXT NOT NULL,
  action TEXT CHECK(action IN ('technology_created','technology_updated','technology_deleted')),
  technology_id INTEGER NOT NULL, before_json TEXT NULL, after_json TEXT NULL
);
```

`w04_technology_migrations(component, version, applied_at)` đánh dấu migration riêng; không dùng `PRAGMA user_version` global vì DB có thể được các module khác dùng. Trong một `BEGIN IMMEDIATE`, kiểm schema hiện hữu đúng cột/index rồi tạo bảng/index/audit/migration marker; commit một lần. DB cũ chỉ có domain/CIDR được nâng cấp additive và giữ nguyên count/row/audit. DB partial, schema sai, row hỏng, lock hay lỗi I/O: rollback toàn bộ migration/write, map ra lỗi công khai hiện có `assets_unavailable`, **không** tự repair/recreate/drop. Python `sqlite3` yêu cầu commit để bền vững dữ liệu ghi, hỗ trợ quyết định audit cùng transaction ([docs](https://docs.python.org/3/library/sqlite3.html#transaction-control)).

Mỗi create/update/delete là một `BEGIN IMMEDIATE`: mutate row + append-only audit before/after canonical/display + actor `subject` + UTC cùng commit. Test buộc audit lỗi phải chứng minh cả row và audit không đổi. Soft delete không cho phép asset technology cũ tham gia W03 query.

### Extension point W03 và cách diễn đạt an toàn

W03 tương lai chỉ nhận projection read-only:

```json
{
  "technology_id": 41,
  "vendor": "Fortinet",
  "product": "FortiOS",
  "version": "7.2.1",
  "match_basis": "vendor_product_casefold",
  "version_assessment": "not_evaluated"
}
```

Backend W03 có thể trả candidate CVE khi `vendor_key` và `product_key` bằng nhau; phải gắn `match_basis`/`version_assessment` và UI nói: **“Có thể liên quan theo nhà cung cấp và sản phẩm; phiên bản bạn khai báo chưa được đối chiếu tự động. Hãy kiểm tra advisory của hãng trước khi kết luận hoặc vá.”** Không coi chuỗi ghép là kết luận hệ thống có lỗ hổng, không thêm version range matching, quét mạng, feed CVE/KEV/EPSS hoặc tự vá.

Technology không gọi `AssetMatcher`, không tạo allowlist, không đổi `asset_match`, không đổi `/api/ioc`, core `Allowlist`, route/shape W02 hoặc domain/CIDR. Đây là ranh giới bắt buộc để regression W02 không bị ảnh hưởng.

## Brief triển khai nhỏ — Backend (một Sol medium)

**Mục tiêu:** IT/analyst/admin CRUD khai báo vendor/product/software version cục bộ; bản ghi có optimistic version/audit; cung cấp projection read-only cho W03 sau này. Không nối CVE, không thay W03, không UI HTTP thật trong task này.

**Base/tree:** tạo **một working tree Backend mới** từ `cti-w04-local-integration@8a767314b654d39c1ddc2995b7919c44a5b7027a`, branch gợi ý `feat/w04-technology-local-20261111`. Một writer. Không reset/reuse tree đang có thay đổi; không lấy PR #1/#46 làm base.

**Allowlist file:** `portal_api/assets.py` (hoặc `portal_api/technologies.py` mới nếu không đụng model domain/CIDR), `portal_api/schemas.py`, `portal_api/app.py`, tests technology mới, `docs/specs/W04-assets-local-contract.md` bổ sung mục technology, `docs/PROGRESS.md`, evidence/report riêng. Không sửa `portal_api/ioc_lookup.py`, W02 tests/contracts, core, frontend, dependency/lock, deploy, RUNS/plan hay source feed/OpenCTI. Cần file ngoài allowlist: dừng và báo Leader.

**Thiết kế bắt buộc:**

1. Viết pytest RED trước; dùng JWT RSA tổng hợp, SQLite temporary; không network/listener/browser.
2. Implement additive migration rõ ràng, idempotent, transactional và fail-closed như mục trên. Validate read-back để DB hỏng thành unavailable, không output partial.
3. Dùng role resolver server-side của W04. Auth/role/Origin trước body/query/DB; error/header hiện hữu giữ nguyên; không echo raw input.
4. Implement CRUD exact schema, record version separate, active duplicate triple, soft delete và append-only audit. Mọi lỗi sau BEGIN phải rollback technology và audit; mutation outcome không rõ không được retry.
5. Không thêm CPE parser/lookup, alias/brand, scanner, version comparator hoặc bất cứ wiring nào vào W02 matcher/allowlist.

**Kiểm tối thiểu và tiêu chí giao:**

| Nhóm | PASS khi |
|---|---|
| Migration | fresh DB; W04 DB cũ preserve domain/CIDR/audit; rerun idempotent; schema partial/sai và forced failure rollback, không auto-repair. |
| Validation/duplicate | trim+NFKC/casefold vendor/product expected; control/empty/over-bound reject; version giữ display, không parse range; duplicate active 409, soft-delete cho phép tạo lại. |
| CRUD/audit | create/list/update/delete, stale/missing, actor/before/after/UTC; audit fail/constraint fail không để row/audit nửa chừng. |
| Quyền & outcome | missing/bad JWT 401; leader/header-role giả 403; Origin/body/extra key invalid 422; `no-store`/`Vary`; POST/PUT/DELETE unknown không retry trong adapter nếu adapter được chạm. |
| Không ảnh hưởng | Focused W02 regression chạy không đổi; assert technology create/delete không làm `asset_match`/allowlist thay đổi. |

Chạy bằng `.venv\\Scripts\\python.exe` của target (không dùng PATH): focused technology tests, `pytest portal_api/tests/test_assets_api.py -q`, `pytest portal_api/tests/test_w02_ioc_api.py -q`, `ruff check`/`ruff format --check` cho delta, `git diff --check`; ghi command, exit, count, base/HEAD/diff và clean status vào evidence. Commit cục bộ sau khi xanh; không push/PR/merge/deploy/lab.

## Brief Frontend độc lập — có thể làm song song

**Mục tiêu:** thêm provider fixture typed và test cho tab Công nghệ theo DESIGN hiện có; không tự redesign, không gọi API thật. Contract đầu vào là `TechnologyView`, `TechnologyProvider` với list/create/update/delete và cùng semantic `unknown-mutation`/GET-only recovery như W04.

**Phạm vi:** tree Frontend riêng từ cùng baseline; chỉ component/data/test assets và fixture mới. Không sửa Backend, W02, gateway, packages/lock, DESIGN, RUNS hay layout khác. Form có vendor/product/version/note; hiển thị version phần mềm và record revision tách nhãn. State bắt buộc: loading/rỗng/invalid/401/403/409/503/unknown mutation; tab switching không cho callback cũ ghi state mới. Không có test backend dependency nên có thể khởi động trước, nhưng UI HTTP wiring chỉ sau khi Backend contract được nghiệm thu.

**Tiêu chí:** fixture CRUD đúng typed contract; duplicate/stale/forbidden/unknown mutation; context ownership race create/update/delete; typecheck/lint/focused tests/build cho delta xanh; không ảnh hưởng component W02/domain/CIDR. Không chạy browser/lab/deploy.

## Trạng thái bằng chứng

| Trạng thái | Nội dung |
|---|---|
| **ĐÃ KIỂM** | SHA baseline, source/schema/spec W03/W04/DESIGN/AGENTS, tree sạch; hai PR đang mở; nguồn NIST/MITRE/CVE/NVD/OpenCTI/Python ở bảng trên. |
| **KHUYẾN NGHỊ/CHƯA TRIỂN KHAI** | Bảng technology riêng, contract/API/migration/audit/brief và phrasing W03. Chưa có code, commit hoặc test technology. |
| **CHƯA XÁC MINH** | CPE mapping cụ thể, alias quality, NVD/OpenCTI data/license distribution, CVE matching accuracy, migration trên DB người dùng, concurrent writes/lock pressure, gateway/HTTP/frontend/browser, Cloudflare/JWKS/HTTPS, lab/OpenCTI/production. |
