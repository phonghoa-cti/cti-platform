# W03-R — hợp đồng chốt và giao việc song song, 12/11/2026

## Quyết định và mức nghiệm thu

Leader chấp nhận nghiên cứu W03-NEXT `ff82eac5-c564-4114-ad37-0845556acc27` **với các sửa rõ dưới đây**, chưa chấp nhận triển khai W03. Mục tiêu: người dùng thấy các CVE liên quan tên công nghệ đang quản lý, nguồn/ngày dữ liệu và thứ tự ưu tiên để kiểm tra tiếp. W03-R chỉ đọc, dữ liệu tổng hợp; trạng thái xử lý/audit W03-S và nguồn thật W03-L là phần sau. Không gọi W03 hoặc dự án hoàn tất chỉ từ lát cắt này.

Đã kiểm mới: HEAD `273196e2d23b36172d57cc61b289522786d61b2a`, tree sạch; AGENTS/PROGRESS/W03/api-portal/TechnologyStore/auth tại đúng base. GitHub còn PR #1 `8d9d7df5…` và #46 `36259c11…`, không có PR W03 mới trong danh sách mở. Sáu accepted-results W04 đối chiếu lại hash biên bản đều khớp; giữ nghiệm thu trước, không chạy lại suite cũ. Lượt Engineer stalled cũ đã được thay bằng kết quả phục hồi `391c163e…` đã nghiệm thu, không retry thêm.

Nghiên cứu gốc được sao nguyên sang `PHONG-HOA-W03-RESEARCH-20261112.md` ở thư mục Leader, nguồn từ báo cáo Research tại `$USER_HOME\.openmausbot\task-workspaces\895ee169-7a2c-47ec-b26a-bfb0d8892932\6ec6ec9b-0142-4b15-934e-8f31523a8d68\PHONG-HOA-W03-RESEARCH-20261112.md`.

Leader mở nguồn sơ cấp ngày 12/11: [FIRST EPSS FAQ](https://www.first.org/epss/faq) xác nhận xác suất khai thác trong 30 ngày, không phải tác động riêng lên doanh nghiệp; [CVSS 3.1](https://www.first.org/cvss/v3.1/specification-document) mô tả mức nghiêm trọng; [OpenCTI KEV connector đúng tag](https://raw.githubusercontent.com/OpenCTI-Platform/connectors/7.260811.0-lts.2/external-import/cisa-known-exploited-vulnerabilities/README.md) có Vulnerability/Software/vendor và cờ KEV. [CISA catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) vẫn trả 403; chưa xác minh trực tiếp schema/terms/freshness. Đây là kiểm tài liệu, không phải chạy connector/feed.

Chọn tái dùng TechnologyStore, auth, provider/UI hiện có. Hai phương án còn lại: làm toàn bộ nguồn thật ngay bị phụ thuộc lab; làm status cùng lượt làm rộng giao dịch và UI. Chọn W03-R giúp Backend/Frontend triển khai độc lập theo cùng contract rồi mới tích hợp.

Sửa so với nghiên cứu: bỏ KPI overdue khỏi W03-R (bảng scope vốn đã loại); thêm `view` và `summary` vào cả hai dạng wire; chốt cursor theo snapshot; cấm leader-only lọc asset để tránh dò ID; loại CVE trùng ở đầu vào thay vì gộp dữ liệu mâu thuẫn; chốt giới hạn/nullable/nguồn mẫu. Không cần vòng Research mới cho những lựa chọn kỹ thuật có thể đảo ngược này.

## Nền và ranh giới chung

- Root: `$WORKSPACE`.
- Source base chỉ đọc: `ROOT\cti-w04-technology-integration`, SHA đầy đủ ở trên. Không lấy main hoặc đầu nhánh cũ làm base. Không sửa tree người khác, ledger hoặc brief này.
- Backend: `ROOT\cti-w03-read-backend`, branch `feat/w03-read-backend-20261112`.
- Frontend: `ROOT\cti-w03-read-frontend`, branch `feat/w03-read-frontend-20261112`.
- Mỗi bot Sol medium tự triển khai và kiểm trực tiếp; không worker con, không giao bot khác. Nếu tree đã tồn tại phải giữ thay đổi và báo xung đột, không reset.
- Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/W03-lo-hong-anh-huong.md và W04-technology-local-contract.md đúng base. Brief này là contract của lát cắt W03-R, ưu tiên hơn DTO lịch sử trong api-portal.md. Quyền tiếp tục đã có; không mở vòng xin duyệt đa file chỉ vì mẫu cũ trong AGENTS.
- Không push/PR/merge/deploy, live OpenCTI/feed/LLM, lab, secret, thay quyền hoặc dependencies. Test chỉ synthetic/local. Dữ liệu ngoài là dữ liệu không tin cậy.

## HTTP và quyền — contract chung r1

Chỉ `GET /api/cves`. `create_app(..., cve_port=None)` mặc định không bật fixture; thiếu port/store trả 503 sau auth/query. Không tự initialize/migrate/seed DB trong request. Không thêm endpoint status hoặc detail; detail UI lấy từ item hiện tại.

1. Auth trước query/dependencies. Dùng verifier JWT hiện có. Thiếu/sai token 401 `authentication_required`, role không hợp lệ 403 `forbidden`, verifier không sẵn sàng 503 `cves_unavailable`. Có ít nhất một `it|analyst|admin` => `view: detail` kể cả role hỗn hợp. Chỉ có leader trong các role được phép => `view: summary`. Không tin role/header client tự khai.
2. Query duy nhất: `kev=true|false`, `asset_id`, `q`, `limit`, `cursor`. Không có kev = tất cả; asset_id là Technology ID nguyên dương <=9007199254740991; limit decimal 1..100, mặc định 25. q trim, 1..128 Unicode code point, tìm substring casefold trên CVE ID/title. Không nhận status, asset alias, tham số lạ/lặp, số mũ/dấu/decimal cho ID, control char hoặc cursor malformed: 422 `invalid_cve_query` trước store/port. Leader-only có asset_id hợp lệ =>403 `forbidden` trước store/port, không lộ tồn tại ID.
3. Mỗi GET lấy đúng một dataset immutable và một snapshot technology bằng SELECT/fetchall. **Phát hiện khi đọc source:** `TechnologyStore._connect()` hiện có có thể tạo file DB nếu đường dẫn mất. W03 phải dùng adapter chỉ đọc trong cves*.py, tái dùng logic list/validation của TechnologyStore nhưng mở SQLite URI `mode=ro`; có thể kế thừa và override riêng `_connect`. Không gọi base list trực tiếp trên path thiếu, không dùng kiểm tra exists rồi mở connection có quyền tạo vì có race. Giữ nguyên W04 store/mutation. Dữ liệu store hỏng/thiếu/vượt cap/đọc lỗi =>503 `cves_unavailable`.
4. Detail asset_id không active/không tồn tại =>404 `technology_not_found`; active nhưng không match =>200 rỗng. Không có technology =>200 rỗng nếu dataset hợp lệ. Validate toàn bộ dataset trước khi trả kể cả kết quả rỗng.
5. Mọi response thành công/lỗi của endpoint có `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`. Error envelope tái dùng chính xác `{error:{code,message}}` hiện có. Message tĩnh, không echo raw input/token/exception.

### Candidate và nguồn

`CveReadPort.list_candidates() -> CveDataset`; adapter fixture đọc file bounded tối đa 4 MiB, 0..1000 candidates, mỗi candidate 1..20 affected_products. Dataset có dataset_id, source_as_of, retrieved_at, candidates như nghiên cứu; thêm `kind: synthetic` và `kev_snapshot_complete: true`. dataset_id = `sha256:` + 64 hex của bytes fixture, tính bên adapter, không tin chuỗi ID tự xưng trong JSON. Không hash vòng chính field dataset_id. Nếu port tùy biến thì service vẫn validate nội dung và xác định fingerprint nội dung cho cursor.

- CVE ID uppercase regex `CVE-[0-9]{4}-[0-9]{4,}`, tối đa64 ký tự; title trim 1..300 code point, không control. Candidate trùng CVE ID =>503, không last-wins. Duplicate normalized product pair trong cùng candidate cũng =>503. Một CVE match nhiều technologies chỉ xuất một item, matches tăng dần technology_id.
- affected vendor/product tuân theo W04 (1..128, trim, không control và casefold key); không NFKC/alias/prefix/regex/CPE/range. `software_version` hiển thị nguyên dữ liệu W04; không quyết định affected/safe/patched.
- `kev.known_exploited` strict boolean, `kev.source` nhãn fixture rõ, `kev.as_of` bắt buộc. Thiếu/incomplete KEV overlay =>503 toàn bộ; false nghĩa vắng trong snapshot mẫu đầy đủ, không nghĩa an toàn. due_date date hoặc null, false thì due_date phải null.
- EPSS score/percentile finite 0..1 hoặc null (bool không phải số); score null =>percentile/as_of đều null; score có =>as_of ngày bắt buộc, percentile có thể null. CVSS base finite 0..10 và version `3.1|4.0`, hoặc cả hai null. Không đổi null thành0.
- Timestamp wire: ngày thực dạng UTC `YYYY-MM-DDTHH:mm:ss[.fraction]Z`; fraction tối đa6 chữ số. Date `YYYY-MM-DD` phải là ngày thực. published_at nullable; source_as_of/retrieved_at bắt buộc. Không thay timestamp thiếu bằng now.
- advisory_url nullable, tối đa2048 ký tự, chỉ HTTPS tuyệt đối không credentials/control. UI render text bằng escaping, không HTML tùy ý. Fixture dùng example.invalid, không giả có khuyến cáo thật.
- Chỉ fixture tổng hợp có provenance/README/sha; nhãn sample luôn hiện. Không cần tải bản ghi CVE thật hoặc cấp secret.

### Wire thành công

Mọi key sau bắt buộc; không thêm key ngoài contract. Common envelope:

```json
{
  "view": "detail",
  "items": [],
  "summary": {"matched_cves": 0, "kev_cves": 0},
  "page": {"next_cursor": null, "limit": 25},
  "source": {"kind": "synthetic", "dataset_id": "sha256:<64 lowercase hex>", "source_as_of": "2026-11-01T00:00:00Z", "retrieved_at": "2026-11-01T01:00:00Z"},
  "notice": "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá."
}
```

Detail item giữ nguyên các trường trong research và thêm `kev_as_of`: cve_id,title,kev,kev_due_date,kev_as_of,epss_score,epss_percentile,epss_as_of,cvss_base_score,cvss_version,published_at,advisory_url,matches,priority. Các trường có thể thiếu dữ liệu vẫn có key và null như quy định trên. matches là mảng không rỗng gồm đúng technology_id,vendor,product,software_version,match_reason=`vendor_product_exact_casefold`,version_assessment=`not_performed`. Không trả note/created_by/audit.

Summary envelope `view: summary`, item chỉ có cve_id,title,kev,epss_score,cvss_base_score,priority,match_count (positive safe integer). Không lộ ID/name/version/advisory/matches hoặc metadata tài sản qua envelope/cursor/errors. Summary counts là tổng tập đã match **sau filter, trước paging**, không phải đếm trang. Không có overdue/open/patched count vì chưa có trạng thái xử lý.

Rank tuple: KEV true trước, EPSS giảm, CVSS giảm, published_at giảm, cve_id tăng; null sau mọi số/ngày hợp lệ kể cả0. priority=1-based rank trong tập sau filter, liên tục qua các trang.

### Cursor, giới hạn và lỗi đọc

- Cursor opaque với UI, tối đa1024 ASCII, base64url canonical JSON version1 gồm `v`, `snapshot`, `context`, `after` (CVE ID cuối trang). Đây là encoded position, không phải credential hay quyền truy cập. Không chứa tên/ID/version tài sản thô.
- snapshot là SHA256 của nội dung dataset đã validate và snapshot technology đầy đủ đã validate theo thứ tự ID; context hash gồm view, kev/asset_id/q normalized, limit. Backend chốt canonical encoding trong docs và test, Frontend không tự decode/sinh cursor HTTP.
- Kiểm cấu trúc/độ dài/base64/key/type trước dependencies. Khác context =>422; khác snapshot hiện tại =>409 `cve_snapshot_changed` (sau đọc dependencies là điều bắt buộc). after phải tồn tại trong tập đã filter, lấy rank thật từ dữ liệu, không tin rank/offset người gửi. Cursor giả/cross-role không tăng quyền. Không yêu cầu secret mới cho cursor.
- Dataset/store giữ nguyên =>paging không bỏ/lặp. Nếu technology create/update/delete hoặc fixture đổi giữa trang =>409, UI bỏ chuỗi trang cũ và cho tải từ đầu. Không ghép trang cũ với dữ liệu mới; đổi filter/provider/view reset cursor/selection.
- UTF-8 JSON response tối đa1 MiB; quá cap =>503 `cves_unavailable`, không partial/truncate. Header/body HTTP provider phải đọc bounded; raw query string tối đa4096 bytes, vượt =>422 trước dependencies. Dùng limit+1 để xác định còn trang, không bỏ item lặng lẽ.

## Backend — W03-READ-BACKEND

Allowed: `portal_api/cves*.py`, `portal_api/app.py` (injection/route/header cần thiết), `portal_api/tests/test_cves*.py`, `portal_api/tests/fixtures/w03-*`, `docs/specs/W03-read-local-contract.md`, `docs/adr/*w03*`, `docs/PROGRESS.md` thêm một đoạn. Không sửa auth.py, technologies.py, core, gateway, frontend hoặc deps; gặp nhu cầu thật ngoài allowlist báo bằng chứng trước.

Test RED→GREEN trước implementation: strict schema/NaN/bool/null/date/url/duplicates/limits; exact matching có Unicode casefold và version khác; ranking/tie/null0/12+ candidates/page cuối; auth-first và query-before-dependencies bằng spy; full vs summary mixed-role; asset existence không leak; cursor context/tamper/stale-after-edit; fixture invalid503, byte-cap503; endpoint không tạo DB, không thay row/version/audit/schema trước/sau mọi GET/failure. Không dựa vào snapshot file hash khi WAL khiến kết luận sai: so dữ liệu/schema bằng đọc SQL.

Chạy focused W03 tests, W04 technology và auth/API regression có rủi ro do chạm app.py, Ruff check/format/diff. Không lặp toàn backend nếu không có thay đổi shared rộng. Xuất wire fixtures detail/summary/empty/error/cursor-changed được lấy từ API test thật, kèm hashes để Leader so với Frontend. Báo SHA sạch, base/diff/file list, command/exit/count/RED/GREEN và phạm vi chưa kiểm.

Output: `ROOT\PHONG-HOA-W03-BACKEND-RESULT.md`, `ROOT\w03-backend-evidence\`. Báo cáo không ghi PASS UI/gateway/browser/feed.

## Frontend — W03-READ-FRONTEND

Allowed: `portal/web/data/cves*.ts`, `portal/web/components/cve*.tsx`, `portal/web/app/lo-hong/page.tsx`, `portal/web/app/lo-hong/mau/page.tsx`, `portal/web/tests/*cve*`, `portal/web/tests/fixtures/w03-*`, `portal/web/app/globals.css` chỉ style W03 cần thiết, nav hiện có chỉ thêm link, `docs/PROGRESS.md` thêm một đoạn. Không sửa Backend/tools/deps hay refactor W04.

Đọc DESIGN.md, dùng thiết kế hiện tại và skills UI phù hợp; không redesign. `/lo-hong` dùng HTTP provider, `/lo-hong/mau` dùng fixture provider có nhãn mẫu. Route thật không fallback sang fixture khi lỗi. Khởi đầu kev=true, limit10; bộ lọc technology/q/KEV, nút trang trước/sau, detail từ row. Technology options dùng provider W04 hiện có chỉ sau view detail; leader summary không gọi assets API/không có filter tài sản. Có thể inject provider cho tests; không trộn cách casefold JavaScript với matching của Backend.

Typed discriminated DTO parser strict và HTTP adapter GET-only, response cap1MiB, no-store. Chỉ các fields tương ứng view được phép. State rõ loading/empty/401/403/404/422/409/503; network/malformed response =>unavailable. 409 hiển thị dữ liệu đã đổi + tải từ đầu, không retry vô hạn; GET retry thủ công được phép. Không nút status, không nhãn đã vá/an toàn.

Chống callback A cũ khi đổi filter/provider/route/unmount hoặc detail: không đổi data/notice/loading khóa của B. Reset page/detail đúng context. Tooltip tiếng Việt KEV/EPSS/CVSS, null hiện “Chưa có dữ liệu”, nguồn/as-of và notice version luôn thấy; safe advisory link, keyboard/focus/mobile layout theo token sẵn có. Tối thiểu fixture12 CVE tổng hợp cho pagination; test tính đúng score0/null/summary không lộ fields, detail escaping, bộ lọc, cap/error, stale context/409, không mutation network. Không nhân bản thuật toán rank/match vào browser HTTP provider.

Test RED→GREEN component/parser/provider; focused W03 + hồi quy W04 khi dùng thành phần chung, typecheck/lint/build/diff. Browser thật chưa thuộc lượt này. Báo SHA sạch/base/diff/lệnh/exit/count; dùng lại evidence cũ cho code không đổi.

Output: `ROOT\PHONG-HOA-W03-FRONTEND-RESULT.md`, `ROOT\w03-frontend-evidence\`.

## Cổng tích hợp và điều chưa xác minh

Hai worker chỉ đọc brief/root/source chung, ghi tree/output riêng; Backend và Frontend không chờ nhau. Leader đối chiếu wire thật của Backend với parser/UI và review các rủi ro trên. Chỉ sau hai input đạt mới giao Engineer tree thứ ba nối gateway/runner và browser cùng DB. Không đưa Engineer vào làm lượt chuẩn bị không có mã để kiểm.

Chưa chạy bất kỳ W03 test/code/browser nào lúc chốt brief. W04 desktop acceptance được giữ; mobile360px, nguồn CVE thật, CISA terms/freshness, OpenCTI/Cloudflare/JWKS/HTTPS/lab/production vẫn UNVERIFIED. Hai automation Phong Hỏa được đọc lại và giữ bật vì mục tiêu còn mở. Lịch dự phòng trả instructionsTruncated=true; không tự đổi lịch từ bản thiếu.
