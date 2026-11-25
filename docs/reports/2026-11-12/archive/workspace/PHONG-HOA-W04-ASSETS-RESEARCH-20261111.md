# W04-ASSETS-NEXT — nghiên cứu và brief lát cắt tài sản cục bộ

**Ngày kiểm:** 11/11/2026. **Loại việc:** chỉ đọc + báo cáo; không sửa repo, sổ điều phối, cloud, dữ liệu thật, feed, secret hay lab.

## Kết luận cho Leader

**Khuyến nghị: điều chỉnh và tái sử dụng lõi hiện có, triển khai trước lát cắt cục bộ “Tên miền + dải IP” trên nền W02 đã nghiệm thu.**

Lát cắt này cho IT/Analyst khai báo, sửa, xóa tên miền hoặc CIDR của doanh nghiệp; cùng dữ liệu đó tạo allowlist có **nguồn gốc `asset`**, và W02 trả `asset_match` cho domain/IP phù hợp. Không có hành động chặn, không coi IOC là an toàn, không gọi dịch vụ ngoài. Nó đáp ứng luồng nhỏ nhất trong W04: thêm `congty.vn` rồi tra `mail.congty.vn` thấy thuộc tài sản.

Chưa làm trong lát cắt: công nghệ/phiên bản để W03 đối chiếu CVE, từ khóa/thương hiệu, CSV, quét crt.sh/Shodan, UI mới, OpenCTI, Cloudflare/JWKS/HTTPS thật, lab và production. W03 không là phụ thuộc kỹ thuật của lát cắt này; ngược lại, W03 cần lát cắt công nghệ sau W04.

## Hiện trạng đã đối chiếu

| Mục | Bằng chứng đọc được | Ý nghĩa |
|---|---|---|
| Nền triển khai W02 | `cti-w02-local-integration`, `feat/w02-local-integration-20261111`, HEAD `aeff542a20ecc6fe436a0884801fdd69ab0435f6` | Commit này chỉ rework tài liệu. Chức năng W02 đã nghiệm thu cục bộ ở `50277102bbcfd0c011c1e162569b2c4fe4560189`; không chạy lại theo brief. |
| W02 | `portal_api/ioc_lookup.py`, `portal_api/app.py`, `portal_api/tests/test_w02_ioc_api.py` ở SHA trên | W02 đã có JWT/role server-side và response `asset_match:{matched,assets}`; nhưng hiện tạo `Allowlist.default()` trong bộ nhớ, `asset_match` chỉ đến từ lookup fixture, không có AssetStore/API. |
| Lõi có thể dùng lại | `core/phonghoa_core/ioc.py`, `allowlist.py` | `normalize()` refang/canonical/IDNA; `Allowlist` dùng `ipaddress.ip_network`, kiểm IP thuộc mạng và khớp domain bằng `domain == d or domain.endswith('.' + d)`. Vì thế `mail.congty.vn` khớp `congty.vn`, còn `evilcongty.vn` không khớp. |
| Khoảng trống | `allowlist.py` | Chỉ có `add_domain`, không có lưu SQLite, CRUD/audit, nguồn gốc asset/manual, xóa/sửa theo nguồn, hoặc `add_network`; `from_file()` còn diễn giải chuỗi không phải CIDR là domain. Không thể dùng trực tiếp làm AssetStore. |
| Spec | `docs/specs/W04-tai-san.md`, `W03-lo-hong-anh-huong.md`, `W01-tong-quan.md`, `api-portal.md` tại W02 SHA | W04 nêu 4 loại, allowlist tự động, audit, 403 cho Lãnh đạo và CSV; W03 cần technology. API tài liệu hiện là hợp đồng lịch sử cho `/api/assets`, chưa phải endpoint được triển khai/xác minh. |
| Thiết kế | `docs/design/DESIGN.md` tại W02 SHA | Có mục “Tài sản” trong nhóm Rủi ro; không tạo thiết kế/UI mới trong task này. |
| PR gốc | GitHub kiểm ngày 11/11: [PR #1](https://github.com/phonghoa-cti/cti-platform/pull/1), [PR #46](https://github.com/phonghoa-cti/cti-platform/pull/46) | Cả hai vẫn mở. #46 nói rõ nó xếp trên #1; không dùng chúng làm nền W04 vì chưa merge và không mang W02 local integration đã nghiệm thu. |

`AGENTS.md` trên ref W02 yêu cầu dùng `phonghoa_core` thay vì viết lại chuẩn hóa/allowlist trong connector, test trước, và không cho agent tự chặn. Đề xuất tuân theo: W04 gọi lõi đó nhưng thêm adapter lưu trữ portal, không nhân bản thuật toán.

## Đối chiếu giải pháp đã có và khả năng tái sử dụng

| Ai/nguồn | Điều đã có | Dùng cho W04 | Giới hạn / giấy phép |
|---|---|---|---|
| Phong Hỏa core, SHA `aeff542…` | Chuẩn hóa IOC, IDNA qua codec `idna`, `Allowlist.contains()`; domain có ranh giới nhãn; membership IP network | **Dùng lại trực tiếp** `normalize`, `Ioc`, `IocType`, và quy tắc `contains`; trích helper tối thiểu nếu cần để AssetMatcher dùng cùng canonical form | Chưa có API/storage/audit/provenance; `Allowlist` mutable và in-memory nên không là nguồn dữ liệu đa request. Repo không có tệp LICENSE ở ref này: giấy phép tái sử dụng ngoài repo **chưa xác minh**. |
| Python Software Foundation, [`ipaddress`](https://docs.python.org/3/library/ipaddress.html) | Thư viện chuẩn Python cho IPv4/IPv6/network; `ip_network(..., strict=True)` từ chối host bits và `ip_address`/network ném `ValueError` khi sai | **Dùng sẵn**, không thêm dependency: parse canonical IPv4 và IPv6 CIDR; membership cùng phiên bản IP | Cần map lỗi sang tiếng Việt cố định, không trả `ValueError` nội bộ; quyết định UX phải nói rõ chỉ nhận network-address CIDR (ví dụ từ chối `113.160.0.1/24`). Đây là thư viện chuẩn; điều khoản phân phối Python cần được kiểm khi phát hành, không được suy ra từ báo cáo này. |
| IETF, [RFC 5891 IDNA2008](https://www.rfc-editor.org/rfc/rfc5891) | IDNA dành cho xử lý tên miền quốc tế, không dành cho free text | **Dùng lại chính sách lõi**: canonical lưu ASCII/punycode lowercase, input/display tiếng Việt không làm khóa so sánh | Codec Python có hành vi IDNA cần test với mẫu đã chọn; không mở rộng thành kiểm tra đăng ký domain/PSL. |
| IETF, [RFC 3986 §3.2.2](https://datatracker.ietf.org/doc/html/rfc3986#section-3.2.2) | Host là một phần authority của URI, không phải phép so sánh chuỗi URL tùy ý | Giới hạn rõ: asset domain chỉ khớp hostname của IOC domain/email/URL, không khớp substring/path/query | URL trong allowlist lõi hiện chỉ coi trang chủ là allowlisted; W04 không đổi luật URL này trong lát cắt đầu. |

Nguồn web đã kiểm ngày 11/11/2026; không có nguồn nào ở trên là ủy quyền cloud/chặn tự động.

## Quyết định dữ liệu và vòng đời allowlist

### Phân biệt ba khái niệm

| Khái niệm | Ý nghĩa trong W04 | Tác động W02 |
|---|---|---|
| Asset | Bản ghi doanh nghiệp quản lý: `domain` hoặc `ip_range` trong lát cắt đầu | `asset_match=true` và trả tên tài sản khi canonical IOC thuộc asset. |
| Allowlist nguồn `asset` | Quy tắc hiệu lực được suy ra **từ asset đang hoạt động**, không phải bản copy bị mồ côi | Có thể ra state `allowlisted`, nhưng không đồng nghĩa IOC an toàn hay đã chặn/bỏ cảnh báo. |
| Allowlist `manual` (tương lai) | Quy tắc do người có quyền tạo độc lập | Không bị xóa/sửa khi asset bị xóa/sửa. Không triển khai endpoint manual trong lát cắt này, nhưng schema phải phân biệt origin để không khóa đường này. |

Không nhân bản asset thành một hàng allowlist độc lập. `effective_allowlist` được tính trong transaction đọc từ `(manual active rules) ∪ (active domain/ip_range assets)` và mang `origin`/`asset_id`. Khi sửa asset, canonical cũ mất hiệu lực và canonical mới có hiệu lực trong cùng commit; khi xóa asset, chỉ rule `origin=asset` của asset đó mất hiệu lực. Bản ghi manual cùng value vẫn còn. Mọi create/update/delete ghi audit bất biến gồm actor `sub`, thời điểm UTC, action, asset id và before/after JSON đã canonical; audit không chứa JWT hay raw input không hợp lệ.

### Chuẩn hóa và khớp phải test

| Input / trường hợp | Quy tắc đề xuất |
|---|---|
| Domain | Nhận hostname/domain, không nhận scheme, path, port, wildcard hay dấu `@`; bỏ dot cuối, `idna` + lowercase rồi kiểm lại là `IocType.DOMAIN`. Lưu canonical ASCII. |
| Subdomain | `mail.congty.vn` khớp `congty.vn`; `evilcongty.vn`, `congty.vn.evil.example` không khớp. Quy tắc đúng là equality hoặc hậu tố `.` + canonical-domain. |
| IPv4 CIDR | `ipaddress.ip_network(value, strict=True)`; lưu `str(network)`. Mọi IPv4 IOC thuộc network khớp. |
| IPv6 CIDR | Cùng cơ chế; IPv6 IOC chỉ khớp IPv6 network, không ép/chuyển giữa hai family. |
| IP ngoài CIDR, host-bits, malformed | Không khớp hoặc HTTP 422 `invalid_asset`; không dùng fallback thành domain. |
| URL/email/hash | Lát cắt domain asset có thể nhận hostname URL và domain email để tính `asset_match`; hash không bao giờ asset-match. **Không thay đổi** luật W02 allowlist URL: chỉ root URL được allowlisted. |

## Hợp đồng W04 đề xuất (v1 cục bộ, nối W02 mà không đổi shape W02)

Tất cả `/api/assets` yêu cầu JWT đã xác minh qua cơ chế W02/W05; role chỉ lấy từ `Settings.roles_by_subject[principal.subject]`, không tin claim/header role/email. `leader` hoặc subject không có `it|analyst|admin` nhận `403 forbidden` trước body/query/DB. Response/error `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`; lỗi là `{ "error": {"code":"…","message":"…"} }`, không echo raw input/SQL/path.

### Asset API

| Route | Request / response tối thiểu | Điều kiện |
|---|---|---|
| `GET /api/assets?type=domain|ip_range` | `{"items":[{"id":1,"type":"domain","value":"congty.vn","note":"","created_by":"…","created_at":"…","updated_at":"…","version":1}]}` | `type` optional; chỉ hai enum; thứ tự `id` tăng dần; không trả audit. |
| `POST /api/assets` | body exact `{"type":"domain","value":"congty.vn","note":""}` hoặc `{"type":"ip_range","value":"113.160.0.0/24","note":""}` → `201` item | body JSON ≤ 8 KiB, note 0..500; canonical duplicate active cùng type → `409 asset_exists`; sai/extra key → `422 invalid_asset`. |
| `PUT /api/assets/{id}` | body exact như POST + `expected_version` strict int → `200` item | atomic compare-and-update; missing → `404 asset_not_found`, stale → `409 asset_conflict`. |
| `DELETE /api/assets/{id}?expected_version=N` | `204` | soft delete hoặc delete + audit trong một write transaction; stale/không tồn tại như trên. Không tự retry POST/PUT/DELETE. |

W02 giữ route/shape đã nghiệm thu. Thay đổi nội bộ đúng một điểm: sau auth/role và `normalize`, gọi `AssetMatcher` trên snapshot đọc để dựng `asset_match`, sau đó tính effective allowlist. Vì vậy thêm `congty.vn` khiến `GET /api/ioc?value=mail.congty.vn` vẫn trả schema W02 hiện hữu, `asset_match={"matched":true,"assets":["congty.vn"]}` và state `allowlisted`. Asset không có nghĩa `found=false` là không nguy hiểm; UI phải giữ thông điệp “thuộc tài sản của bạn / không tự chặn”, không nói “an toàn”. Nếu không có asset/manual rule, hành vi W02 fixture hiện tại không đổi.

**Mẫu schema SQLite tối thiểu**

```sql
assets(id INTEGER PRIMARY KEY, type TEXT CHECK(type IN ('domain','ip_range')),
       canonical_value TEXT NOT NULL, note TEXT NOT NULL, version INTEGER NOT NULL,
       created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
       deleted_at TEXT NULL, UNIQUE(type, canonical_value) WHERE deleted_at IS NULL);
allowlist_rules(id INTEGER PRIMARY KEY, origin TEXT CHECK(origin IN ('manual')),
       type TEXT CHECK(type IN ('domain','ip_range')), canonical_value TEXT NOT NULL,
       created_by TEXT NOT NULL, created_at TEXT NOT NULL, deleted_at TEXT NULL);
asset_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor_subject TEXT NOT NULL,
            action TEXT CHECK(action IN ('asset_created','asset_updated','asset_deleted')),
            asset_id INTEGER NOT NULL, before_json TEXT NULL, after_json TEXT NULL);
```

Asset-origin rules được suy ra từ `assets`, nên không tạo row `allowlist_rules(origin='asset')`; enum `origin` và bảng vẫn bảo vệ được vòng đời manual sau này.

## Brief giao một Sol medium

**Mục tiêu và người dùng:** IT/Analyst khai báo asset domain/CIDR cục bộ; W02 cho biết IOC có thuộc asset và không tự chặn nó. Không dựng màn `/tai-san` mới trong lượt này.

**Working tree/baseline:** tạo working tree mới từ đúng `cti-w02-local-integration@aeff542a20ecc6fe436a0884801fdd69ab0435f6`, branch gợi ý `feat/w04-assets-local-20261111`. Đây là nền chứa W02 integration và W05 auth contract đã được dùng cục bộ; không lấy PR #1/#46 hoặc X01 SHA `4655d9ae…` làm base chỉ vì chúng mới hơn/đã nghiệm thu phạm vi khác. Một writer duy nhất.

**Được sửa (allowlist):**

- `portal_api/assets.py` (mới): DTO, validation, `AssetStore` SQLite, `AssetMatcher`, audit.
- `portal_api/app.py`, `portal_api/schemas.py`, `portal_api/ioc_lookup.py`: chỉ wiring route/schema và AssetMatcher cho W02.
- `portal_api/tests/test_assets_api.py` (mới), `portal_api/tests/test_w02_ioc_api.py` (bổ sung hồi quy nối W02).
- `docs/specs/W04-assets-local-contract.md` (mới) và mục W04 trong `docs/PROGRESS.md`.

Không sửa `core/phonghoa_core`, frontend, `docs/specs/W04-tai-san.md`, auth/settings/service W05, requirements/lock, RUNS/plan, deploy, OpenCTI connector. Nếu cần file ngoài allowlist: dừng và báo Leader với lý do.

**Thiết kế bắt buộc:**

1. Viết test RED trước; dùng cùng factory/JWT RSA tổng hợp hiện có của W02, SQLite temporary và fixture giả; không listener/browser/network.
2. Dùng `phonghoa_core.normalize`/`Ioc` để canonical domain; dùng `ipaddress.ip_network(..., strict=True)` cho CIDR, không parse tự viết. Không chấp nhận URL/email như asset input.
3. AssetStore mở SQLite theo từng request/op; migration/idempotent schema cục bộ rõ ràng. Mỗi write là một transaction: asset mutation + audit cùng commit; lỗi thì rollback cả hai. Không ghi manual rule cho asset.
4. AssetMatcher đọc snapshot transaction nhất quán; matching domain dùng equality hoặc `'.'+domain`; network chỉ match cùng IP version. Kết quả asset sắp theo `id`, dedupe name, giới hạn 100; vượt/hỏng DB → `503 assets_unavailable`, không trả partial hoặc nới allowlist.
5. Route auth/role trước validation/body/DB. Chỉ `it|analyst|admin`; Lãnh đạo 403, kể cả khi gắn client header/claim giả. Do W02 không cho Lãnh đạo tra IOC, không làm ngoại lệ role.
6. W02 dùng AssetMatcher snapshot trước effective allowlist và gắn `asset_match` vào cả `found/not_found/allowlisted`; preserve exact error/header/shape W02. Cơ chế W02 default allowlist vẫn hoạt động; asset chỉ bổ sung effective rules theo transaction, không mutate singleton `Allowlist.default()`.

**Tiêu chí kiểm thử/ nghiệm thu:**

| Nhóm | PASS khi |
|---|---|
| Validation | Domain lowercase/trailing-dot/IDN canonical; reject URL/wildcard/single-label/malformed; IPv4 và IPv6 CIDR hợp lệ; reject host bits, malformed, cross-family. |
| Ranh giới | `mail.congty.vn` match `congty.vn`; `evilcongty.vn` và `congty.vn.evil.test` không match; IPv4/IPv6 in/out CIDR. |
| CRUD/audit | Create/list/update/delete với optimistic version; duplicate/stale/not-found; audit chứa before/after canonical và actor; failure không để asset/audit dở dang. |
| Vòng đời | Edit/xóa asset bỏ đúng effective rule nguồn asset; rule manual fixture cùng canonical (nếu store hỗ trợ fixture nội bộ) còn hiệu lực; không stale cache. |
| Quyền/API | Missing/bad JWT 401; leader/role/header giả 403; 422/404/409 ổn định; no-store/Vary và không echo input. |
| Nối W02 | Domain/IP asset trả `asset_match`; asset-origin allowlisted không gọi lookup port; unknown behavior/response existing W02 không đổi khi không có asset; test W02 hiện có vẫn xanh. |

**Lệnh yêu cầu và evidence:** dùng interpreter `.venv\\Scripts\\python.exe` của target (Python 3.12), không dùng PATH; chạy `pytest portal_api/tests/test_assets_api.py -q`, `pytest portal_api/tests/test_w02_ioc_api.py -q`, `pytest portal_api/tests -q`, `ruff check portal_api`, `ruff format --check portal_api`, `git diff --check`; ghi exit code, test count, base/HEAD/diff và `git status --short` vào `w04-assets-evidence/` cùng `PHONG-HOA-W04-ASSETS-RESULT.md`. Không push/PR/merge/deploy hay chạy browser/lab. Nếu môi trường target chưa có `.venv`, báo **UNVERIFIED**, không dùng Python khác để tuyên bố PASS.

## Trạng thái bằng chứng và điều chưa xác minh

| Trạng thái | Nội dung |
|---|---|
| ĐÃ ĐỌC / kiểm tĩnh | Ref W02, source core/API/test, specs/design/AGENTS/PROGRESS; PR #1/#46 và tài liệu chuẩn nguồn gốc; không phát hiện AssetStore/API W04 ở ref W02. Đây không chứng minh lịch sử repo không có ở ref khác. |
| ĐÃ KẾ THỪA | Kết quả W02 cục bộ đã được Leader nghiệm thu theo `PHONG-HOA-W02-LOCAL-INTEGRATION-RESULT.md`: 37 HTTP checks exit 0 và các evidence lịch sử nêu trong đó. Không chạy lại theo brief. |
| SUY LUẬN/đề xuất | Schema, `AssetMatcher`, thứ tự integration W02, code/error/API v1 và phạm vi 2 loại asset. Cần Leader duyệt trước khi giao code. |
| CHƯA XÁC MINH | Không có runtime W04/test mới; không Cloudflare/JWKS/HTTPS thật, OpenCTI, data thật, W03 CVE matching, CSV, crt.sh/Shodan, browser/UI, lab hoặc production. Chưa xác minh giấy phép repo vì ref không có LICENSE; chưa xác minh khả năng migrate/độ trễ/concurrency trên DB thật. |
