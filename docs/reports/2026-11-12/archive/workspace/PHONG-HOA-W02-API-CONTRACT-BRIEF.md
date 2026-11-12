# W02 — brief API IOC chỉ đọc (R1–R4)

**Trạng thái:** giao Sol medium; chưa có API/listener/OpenCTI/JWKS thật.
**Base bất biến:** source `cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`, branch đang đọc `feat/x01-w05-stix-e2e-20261111`, sạch trước/sau research.
**Đã chốt:** JWT W05, một GET chỉ đọc, `not_found.score=null`; không batch/enrichment/false-positive/block/recommendation/OpenCTI link.

## 1. Tái dùng, phạm vi và delta

| Có sẵn | Dùng lại | Không suy ra |
|---|---|---|
| `phonghoa_core.normalize`, `Ioc.display()` | refang/canonical/defang và từ chối IP non-global | `ValueError` nội bộ hoặc chuỗi raw ra HTTP |
| `Allowlist.contains`, `score(ScoreInput)` | allowlist trước lookup; score/reason phía server | score 0/allowlist/unknown là “an toàn” |
| W05 `AccessJwtVerifier`, `Principal`, `Settings`, app factory | RS256/JWKS/issuer/audience/`sub`; role do server map | JWT/JWKS Cloudflare thật đã kiểm |
| W02/F05/F08/api-portal | mục tiêu IOC/TLP | API-key, OpenCTI, batch và action từ nháp cũ còn hiệu lực |

Chọn `FixtureLookupPort` offline, deterministic, in-process; adapter OpenCTI là công việc riêng sau. Delta đã được Leader chốt: W02 dùng JWT W05 thay API-key nháp; IT chỉ CLEAR/GREEN là policy portal, không là quyền chia sẻ ngoài hệ thống; unknown không có score.

## 2. HTTP, quyền và thứ tự xử lý

Route duy nhất: `GET /api/ioc?value=<raw>`; không body, pagination, CORS wildcard hay ghi dữ liệu. Query chỉ có `value` đúng một lần. Tất cả response success/lỗi W02 có `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`; không echo raw value, JWT/claim, exception/path/SQL.

Thứ tự bất biến: **auth → role → query → normalize/private-IP → allowlist → lookup/filter TLP → score → serialize**. Thiếu/sai/hết hạn token hoặc sai RS256/issuer/audience/`sub` => `401 authentication_required`; JWKS tạm lỗi => `503 lookup_unavailable`; không role hợp lệ => `403 forbidden`. Không kiểm query hay IOC trước auth/role.

Role chỉ từ `Settings.roles_by_subject[principal.subject]`: tập role có `analyst` hoặc `admin` thấy mọi TLP; nếu không, có `it` thì chỉ CLEAR/GREEN; nhiều role dùng quyền cao nhất. Tập không chứa cả ba => 403. Không nhận role/email/header/query tự khai.

Sau auth/role: thiếu/rỗng/trùng `value`, key query lạ, raw >4096 code point => `422 invalid_ioc`; `normalize` lỗi thường => cùng lỗi, lỗi non-global IP => `422 private_ip`. Sau normalize, bắt buộc `1..2048` code point cho canonical `ioc.value` và `1..4096` cho `Ioc.display()` (defang/IDNA có thể dài hơn raw); vượt bound => `422 invalid_ioc`. `allowlist` trả ngay, không gọi adapter. GET không cần Origin/Content-Type.

Mọi error exact là `{"error":{"code":"...","message":"<câu Việt cố định>"}}`; message `1..160`, không dữ liệu thô. `503 lookup_unavailable` cho `lookup_port is None`, fixture adapter ném lỗi, DTO/schema/TLP hậu kiểm lỗi; không 404, retry hay network fallback. “Timeout” fixture chỉ là exception giả, **không** chứng minh timeout mạng tương lai.

## 3. DTO response exact

Mọi DTO HTTP `extra=forbid`; integer strict (bool không là integer); number finite. Enums: `ioc.type=ipv4|ipv6|domain|url|email|md5|sha1|sha256`; `state=found|not_found|allowlisted`; `tlp=TLP:CLEAR|TLP:GREEN|TLP:AMBER|TLP:AMBER+STRICT|TLP:RED`; `score.level=low|medium|high`.

Success luôn có: `ioc:{type,value,display}` (strings canonical/display như §2); `state`; `found:boolean`; `allowlisted:boolean`; `score:Score|null`; `sources:Source[]`; `related:{techniques:string[],malware:string[],actors:string[]}`; `asset_match:{matched:boolean,assets:string[]}`; `tlp:Tlp|null`. Mỗi list `0..100`; name/value `1..128`; timestamps RFC3339 UTC; `Score={value:strict int 0..100,level,reason:string 1..512,parts:{reliability,confirmation,freshness,asset}}`, bốn number finite: first three `0..1`, asset `1|1.3`.

`state=found`: found true, allowlisted false, score/sources/tlp non-null. `allowlisted`: found false, allowlisted true, score `{value:0,level:"low",reason:<core allowlist reason>,parts:null}`, empty list, `tlp:"TLP:CLEAR"`. `not_found`: both false, score/tlp null, empty list. Không trạng thái nào là khẳng định IOC an toàn.

Request (không phải response): `GET /api/ioc?value=evil.example`. Response found fixture hợp lệ (score do core tính từ đúng một source visible reliability `.8`, ngày 0):

```json
{"ioc":{"type":"domain","value":"evil.example","display":"evil[.]example"},"state":"found","found":true,"allowlisted":false,"score":{"value":40,"level":"medium","reason":"Nguồn tin cậy 0.80 × 1 nguồn xác nhận (0.50) × thấy lần cuối 0 ngày trước (1.00) = 40 điểm","parts":{"reliability":0.8,"confirmation":0.5,"freshness":1.0,"asset":1.0}},"sources":[{"name":"Synthetic Alpha","first_seen":"2026-11-11T00:00:00Z","last_seen":"2026-11-11T00:00:00Z","tlp":"TLP:GREEN"}],"related":{"techniques":[],"malware":[],"actors":[]},"asset_match":{"matched":false,"assets":[]},"tlp":"TLP:GREEN"}
```

```json
{"ioc":{"type":"ipv4","value":"8.8.8.8","display":"8[.]8[.]8[.]8"},"state":"allowlisted","found":false,"allowlisted":true,"score":{"value":0,"level":"low","reason":"IOC nằm trong allowlist (hạ tầng hợp pháp) nên điểm = 0.","parts":null},"sources":[],"related":{"techniques":[],"malware":[],"actors":[]},"asset_match":{"matched":false,"assets":[]},"tlp":"TLP:CLEAR"}
```

```json
{"ioc":{"type":"domain","value":"unknown.example","display":"unknown[.]example"},"state":"not_found","found":false,"allowlisted":false,"score":null,"sources":[],"related":{"techniques":[],"malware":[],"actors":[]},"asset_match":{"matched":false,"assets":[]},"tlp":null}
```

Level là projection W02: `0..39=low`, `40..69=medium`, `70..100=high`; không đổi hàm score core.

## 4. DTO nội bộ, TLP và adapter

Trong `portal_api/ioc_lookup.py`: `SourceFact(source_id/name 1..128, reliability finite 0..1, first_seen/last_seen UTC, tlp)`, `RelatedFact(kind=technique|malware|actor,value 1..128,tlp)`, `AssetFact(name 1..128,tlp)`, immutable `LookupRecord(ioc,record_tlp,sources,related,assets,as_of UTC)`; `first_seen<=last_seen<=as_of`; không duplicate `source_id` sau lọc. `IocLookupPort.lookup(ioc, allowed_tlps)->LookupRecord|None`.

`LookupService` xác định allowed TLP, yêu cầu adapter lọc đệ quy, rồi **tự hậu kiểm** record/nested item. Vi phạm/invalid => 503, không serialize partial. Với bản ghi mixed: lọc source/related/asset không được phép; nếu không còn source visible thì `not_found`. `record_tlp` không được trả/làm rò; `tlp` response là marking hạn chế nhất của dữ liệu còn visible.

Chỉ facts visible tạo `ScoreInput`: dedupe `source_id`; `confirmations=len(visible sources)`; `reliability` là trung bình số học reliability visible; `days_since_last_seen=(as_of-max(last_seen visible))/86400`; `asset_match=bool(visible assets)`. Dữ liệu ẩn không được tham gia score/reason/count/marking. `related` và asset chỉ serialize sau lọc. Fixture có record GREEN gồm `Synthetic Alpha` GREEN và `Synthetic Amber` AMBER; IT nhận đúng JSON found trên (không đổi nếu Amber reliability/time/asset/related bị sửa), analyst thấy cả hai và score được tính lại từ hai fact visible. Đây là test chống leak nested-TLP.

`FixtureLookupPort` dictionary trong test, không file/network/clock; thiếu `lookup_port` mặc định `None`. `create_app(..., lookup_port=None, ...)` phải tạo/giữ mọi W05 route; W02 hợp lệ đến lookup mới 503. Adapter OpenCTI tương lai phải cùng interface/lọc tại truy vấn và vẫn qua hậu kiểm; không làm fallback mặc định hay chứng minh OpenCTI thật.

## 5. Gói triển khai và kiểm chứng

Target: `<root>\\cti-w02-lookup-api`, branch `feat/w02-lookup-api-20261111`, tạo từ exact base SHA trên; một writer, không đụng tree Frontend/W05. Interpreter: `<target>\\.venv\\Scripts\\python.exe` Python 3.12.13; không dùng Python PATH khác. Allowlist source: `portal_api/app.py`, `portal_api/schemas.py`, **mới** `portal_api/ioc_lookup.py`, **mới** `portal_api/tests/test_w02_ioc_api.py`, tùy chọn **mới** `docs/specs/W02-lookup-offline-contract.md`, `docs/PROGRESS.md` (mục W02). Không sửa core/auth/settings/service W05, frontend, spec cũ, requirements/lock, RUNS/plan/config; file ngoài allowlist phải báo Leader.

Hook `lookup_port` chỉ thêm optional keyword vào `create_app`; middleware/error handler áp dụng W02 không làm đổi headers/mã/shape W05. Test RED→GREEN in-process TestClient/JWT RSA tổng hợp: three JSON fixtures parse stdlib; core xác nhận sample score/display; found/unknown/allowlist; auth/role/multi-role; query/error order; normalized/defang bound; `None` port 503 và W05 vẫn pass; mixed-TLP mutation invariance; adapter exception/schema failure 503/no-store/Vary. Sau đó chạy `pytest portal_api/tests/test_w02_ioc_api.py -q`, `pytest portal_api/tests -q`, `ruff check portal_api`, `ruff format --check portal_api`, `git diff --check`, allowlist diff, HEAD/status.

Evidence/report: `<root>\\PHONG-HOA-W02-LOOKUP-API-RESULT.md`, `<root>\\w02-lookup-api-evidence\\` (lệnh, exit/count, base/HEAD/diff, TestClient demo IT/analyst); không listener/browser/OpenCTI/cloud/lab/push/merge/deploy. Demo là fixture + JWT tổng hợp, không phải auth/OpenCTI thật.

## 6. Nguồn và chưa xác minh

Đã đọc/reuse exact SHA: W02/F05/F08/api-portal, core normalize/allowlist/score và W05 auth/factory. FIRST TLP 2.0 từ nghiên cứu ban đầu xác nhận TLP là ranh giới chia sẻ, không là quyền cloud. Chưa xác minh Cloudflare/JWKS/OpenCTI thật, GraphQL/schema, latency/100k IOC, cache, production configuration hay UI/browser.
