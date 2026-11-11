# Tiến độ (agent cập nhật sau mỗi task)

Cập nhật lần cuối: 11/11/2026

## 12/11/2026 — W03-S1 Frontend trạng thái theo quan hệ

- Đã thêm provider/parser HTTP riêng và panel trạng thái/note/history trong chi tiết một CVE/công nghệ; trang tóm tắt không gọi status API, trang mẫu chỉ lưu trong memory.
- Đã khóa double-submit, stale callback, 409 re-entry, phân trang history và pending/unknown recovery bằng GET-only; không tự replay PUT.
- Giới hạn: mới kiểm thử component/provider cục bộ; chưa kiểm browser với Backend thật, gateway, lab hoặc production.

## Mốc
| Mốc | Hạn | Trạng thái |
|---|---|---|
| Đề cương gửi giảng viên | 03/11/2026 | Chưa |
| v0.1 lát cắt end-to-end | 24/11/2026 | Chưa |
| v0.5 MVP F01–F08 | 15/12/2026 | Chưa |
| Extractor + agent chạy trên dataset | 12/01/2027 | Chưa |
| Đóng băng tính năng, bản thảo đủ chương | 31/01/2027 | Chưa |
| Nộp quyển | 27/02/2027 | Chưa |

## Đang làm
- PR #1: bộ khởi động đầy đủ, chờ duyệt và merge
- Việc 2: cài OpenCTI trên máy Ubuntu
- F01/#9: gói demo MITRE + bundle STIX mẫu đã kiểm cấu hình ngoại tuyến; chờ chạy và đo trên lab

## Đã xong gần đây
- W03-S1 Backend cục bộ: ba route status/history opt-in dùng cùng SQLite W04, migration explicit, GET read-only,
  PUT `BEGIN IMMEDIATE` với optimistic version và audit nguyên tử; cursor history gắn context/snapshot. Đã kiểm
  bằng JWT/dataset/SQLite tổng hợp in-process; chưa nối frontend/gateway/browser, feed/OpenCTI, lab hay production.
- Tạo organization phonghoa-cti và repo cti-platform
- Thư viện phonghoa_core (47 test), spec MVP + portal + Hermes, mockup 5 màn, đề cương nháp
- Chi tiết bàn giao: docs/HANDOFF.md
- Baseline PR #46 tại `36259c118f519d3ac9cfc1f7b79e7180c2448a88`: 61 test đạt; Ruff check và format đạt
- Lập ma trận nguồn F01 tại `docs/wiki/Nguon-du-lieu-F01.md`: ưu tiên connector chính thức, gồm CISA KEV;
  `ImportFileStix` là đường nhập mẫu và không tính là feed
- Chuẩn bị `deploy/demo/` với OpenCTI LTS `7.260811.0-lts.2`, 8 image ghim digest và fixture STIX tổng hợp;
  Compose lõi/MITRE/ImportFileStix đã parse, thiếu secret bị từ chối
- Xử lý QA-01–03 cho gói demo: preflight kiểm UUIDv4/Base64/token không lộ input; quy trình ImportFileStix dùng
  bản nháp mặc định và analyst phê duyệt; tiêu chí provenance khớp từng loại object STIX
- X01/C1 ngoại tuyến: CLI dùng lại regex và bộ chấm điểm hiện có, chạy trên 6 mẫu tổng hợp Việt/Anh và xuất
  JSON tái hiện được theo báo cáo, micro và loại IOC; đây chỉ là smoke test, chưa phải đánh giá X01 trên dữ
  liệu thật
- X01 bước 1 bản nháp ngoại tuyến: CLI `.txt` tạo JSON `status=pending`, mỗi IOC có quote/span nguyên văn,
  SHA-256 nguồn, TLP mặc định AMBER, cảnh báo injection và allowlist
- X01 bước 2 kho bản nháp ngoại tuyến: CLI lưu mỗi draft pending thành bản ghi SQLite mới và đọc lại nguyên
  nội dung theo ID qua tiến trình khác; kiểm schema/hash/span, kiểu `language`/`tlp`, và IOC nằm đúng span
  evidence trên nguyên nguồn; có rollback, timeout khóa DB và chế độ đọc không tự tạo DB; chưa có duyệt/từ
  chối, HTTP, xác thực, model hoặc kiểm lab
- X01 bước 3 hợp đồng W05: đã ghi bảng trường schema offline 1.0, quy ước span Unicode, ba fixture `get` SQLite
  và gói handoff UI; đây là tài liệu/mẫu cục bộ, chưa triển khai HTTP, quyền, duyệt/từ chối, UI hay OpenCTI
- X01 hàng đợi ngoại tuyến: API/CLI liệt kê draft pending theo `id DESC` và cursor `before_id`, summary không
  chứa toàn văn; có thể chọn ID từ trang để đọc chi tiết, chưa có HTTP, quyền, duyệt/từ chối hoặc UI
- X01 QA kho/hàng đợi: `get` và `list` dùng chung kiểm payload/metadata khi đọc; `save/get/list` cùng từ chối
  timeout sai trước khi mở SQLite; dữ liệu hỏng không ghi đè output, chưa mở rộng sang HTTP, quyền hoặc UI
- W05-B review ngoại tuyến: schema SQLite migration version 1 giữ nguyên payload 1.0, tác giả subject cho draft
  mới, policy Actor analyst/admin, approve/reject đúng một lần với optimistic concurrency và atomic audit;
  get/list vẫn chỉ đọc kể cả schema legacy, approve không gọi OpenCTI. Đây chưa phải xác thực HTTP/JWT, UI,
  chỉnh item, ingestion OpenCTI hoặc audit chống sửa file database.
- W05 API cục bộ: FastAPI có ba route list/detail/decision, xác minh JWT RS256/issuer/audience/claims bằng khóa
  RSA tổng hợp, role lookup phía server và POST bắt buộc Origin + JSON; lỗi/no-store/schema response đã có test
  in-process. Audience chuỗi/mảng exact membership, lỗi bất ngờ no-store và số quá dài 422 đã có regression.
  Chưa kiểm Cloudflare/JWKS thật, listener, browser frontend, lab hoặc OpenCTI.
- W05 tích hợp browser cục bộ: harness test-only nối nguyên snapshot UI với FastAPI qua gateway same-origin loopback,
  JWT RSA tổng hợp được xác minh thật, role phía server và SQLite tạm; ma trận HTTP kiểm auth/Origin/decision/audit,
  cleanup và lỗi POST thành công nhưng refresh 503 không retry. Đây không phải integration lab, HTTPS/JWKS thật,
  OpenCTI, deployment hoặc thay thế quy tắc HTTPS của cấu hình production.
- W05 selection core: schema SQLite v2 lưu snapshot IOC đủ điều kiện bằng audit riêng, migrate v0/v1 nguyên tử,
  version đồng thời và quyết định cuối tham chiếu snapshot/hash; payload/evidence không đổi. Đây là core-only,
  chưa tương thích API/UI hiện giới hạn version 0/1 và chưa nhập OpenCTI.
- W05 selection API v1: thêm list/detail/save selection/decision dưới `/api/v1/drafts`; detail dùng một read
  snapshot, mutation trả committed selection không reread, giới hạn số/body strict và giữ nguyên `/api/drafts`
  legacy. Đã kiểm in-process với SQLite/JWT/JWKS tổng hợp; chưa nối UI, listener, Cloudflare/JWKS thật, lab,
  OpenCTI hoặc production.
- W05 selection UI: `/duyet` dùng API v1 và tách tập lựa chọn đã lưu với tập analyst đang sửa; lưu/decision là
  hai thao tác riêng, POST chưa rõ kết quả bị khóa đến khi tải lại có chủ ý, response/refresh được xử lý độc lập.
  `/duyet/mau` vẫn chỉ dùng fixture có nhãn và không gọi API. Đã kiểm Vitest/typecheck/lint/build cục bộ; chưa
  kiểm gateway v1, browser same-origin, Cloudflare/JWKS thật, lab, OpenCTI hoặc production.
- W05 selection tích hợp cục bộ: gateway allowlist đúng bốn route API v1, giữ cap legacy 8.192 byte và cap v1
  65.536 byte; fixture hai IOC chỉ có trong scenario selection. Ma trận HTTP thật kiểm save/no-op/empty,
  approve/reject, auth/Origin/conflict, payload bất biến và snapshot/hash audit; trình duyệt same-origin đã kiểm
  bỏ chọn → lưu → duyệt, empty/reject, dirty lock, trang mẫu và hai lỗi refresh 503 riêng. Chưa kiểm
  Cloudflare/JWKS/HTTPS thật, lab, OpenCTI hoặc production.
- W05 export STIX ngoại tuyến: CLI chỉ đọc SQLite v2, lấy final approve audit làm nguồn quyền và xuất đúng một
  bundle STIX 2.1 gồm marking, exporter Identity, tám loại SCO hỗ trợ và Report có provenance dạng hash/metadata.
  Output deterministic, không ghi đè và publish bằng hardlink temp hoàn chỉnh trên NTFS; validator 3.3.2 đạt
  MUST/schema/ref và profile `strict except 103`. Đây chưa chứng minh import OpenCTI, mapping reviewer thật,
  network share/crash durability, lab, Cloudflare hoặc production.
- X01 → W05 → STIX E2E ngoại tuyến: một fixture UTF-8/Unicode đi qua extractor CLI, store CLI, HTTP gateway/API
  selection `[1]` + approve và STIX CLI trên cùng draft/DB; ma trận kiểm source/TLP/audit/provenance, export
  read-only/idempotent/non-clobber và cleanup owned resource. Đây chỉ là CLI + HTTP synthetic cục bộ; browser
  cùng draft, OpenCTI, Cloudflare/JWKS/HTTPS thật, chất lượng dataset/model, lab và production chưa được kiểm.
- W02 view tra cứu IOC mẫu: `/tra-cuu/mau` tra một giá trị qua nguồn fixture thay được, có VI/EN, trạng thái
  idle/loading/result/not-found/invalid/private-IP/unavailable/forbidden, chống response cũ ghi đè và copy giá trị
  gốc theo kết quả Promise. Fixture chỉ nhận own key exact-match; completion clipboard cũ bị vô hiệu khi có submit
  mới, unmount hoặc lượt copy mới hơn. Regression deterministic cho năm key kế thừa và race resolve/reject đã đạt.
  Dữ liệu tổng hợp không gọi mạng; desktop loopback `/tra-cuu/mau` đã được kiểm ở lượt bàn giao trước, không chạy
  lại browser cho rework này; mobile viewport thật và API/auth/OpenCTI/enrichment/lab/production chưa kiểm.
- W02 HTTP adapter frontend: parser strict giữ đủ score parts, source timestamp/TLP và asset match; nguồn dữ liệu
  HTTP gửi một GET cùng origin, giới hạn body UTF-8 1 MiB, timeout 10 giây cho fetch + body và map lỗi W02 sang
  trạng thái UI không lộ message server. Đã kiểm bằng Response giả, gồm ba fixture hợp đồng, 8 loại IOC, 5 TLP,
  lỗi schema/body/timeout và regression race/clipboard; chưa gắn route, nối backend/JWT, chạy browser, OpenCTI,
  lab hoặc production.
- W02 tích hợp cục bộ: `/tra-cuu` dùng adapter HTTP qua client wrapper, gateway chỉ mở `/api/ioc`, và LocalRun
  inject JWT cùng lookup fixture tổng hợp deterministic theo scenario. Ma trận HTTP cùng UI/gateway/API kiểm IT,
  analyst, multi-role, hidden-data invariant, found/allowlist/unknown, 401/403/422/503, no-store/Vary và chống
  header JWT giả; browser tích hợp kiểm found/allowlist/unknown, VI/EN, 401 và 503. Đây vẫn chưa phải
  Cloudflare/JWKS/HTTPS thật, OpenCTI, lab hoặc production.
- W02 rework tài liệu tái chạy: README dùng module command từ đúng cwd với Python integration có `uvicorn`;
  report tách log HTTP Leader khỏi artifact browser cũ và giữ clipboard UNVERIFIED. Không chạy lại matrix,
  test/build hay browser trong rework này; mức bằng chứng tích hợp cục bộ không đổi.
- W04 tài sản cục bộ: API in-process opt-in quản lý domain/CIDR bằng SQLite, optimistic version và audit
  nguyên tử; W02 dùng snapshot để gắn `asset_match` và effective allowlist mà không đổi mặc định khi store
  chưa inject. Đã kiểm bằng dữ liệu/JWT/SQLite tổng hợp cục bộ; chưa có UI/CSV, OpenCTI, browser, lab,
  network thật hoặc production.
- W04 Backend rework F1–F4: mọi row active dùng cho list/snapshot/mutation được kiểm lại canonical và bound;
  actor/version/output bị chặn trước commit; tên `AssetFact` dùng bound 253 riêng; chỉ lỗi unique active asset
  `assets(type, canonical_value)` thật trả `asset_exists`, còn UNIQUE ở bảng/cột khác cùng lỗi
  audit/constraint/storage trả unavailable và rollback. Regression F4 RED 2/2 rồi GREEN 2/2, nhóm assets đạt
  55/55 và probe F4 độc lập đạt 2/2 cục bộ; các phạm vi browser/lab/production vẫn chưa được kiểm.
- W04 chuẩn bị tích hợp cục bộ: gateway mở đúng collection/positive-id assets với cap 8 KiB và thay JWT client;
  LocalRun chỉ inject AssetStore trong scenario W04, dùng cùng SQLite cho CRUD/audit và W02 lookup. Ma trận HTTP
  loopback kiểm quyền, Origin/body/version, domain/subdomain/CIDR/URL-path, xóa cập nhật snapshot và một chuỗi
  refresh 503→200 không replay mutation; UI/browser, Cloudflare/JWKS/HTTPS thật, lab/production chưa được kiểm.
- W04 frontend tài sản mẫu: `/tai-san/mau` quản lý tên miền/dải IP tổng hợp qua provider thay được, có form
  thêm/sửa/xóa, expected version, xác nhận xóa, trạng thái tải/rỗng/invalid/401/403/503/409/kết quả mutation chưa
  rõ, chống gửi lặp, response cũ và mutation cũ hoàn tất sau khi đổi tab bằng context ownership token. Adapter
  `/api/assets` cùng origin giữ strict schema/body/timeout và không tự
  thêm danh tính hay retry mutation. Parser/view W02 giữ `asset_match` cho found/allowlisted/not_found bằng bốn
  fixture candidate đã đối chiếu SHA-256. Đây là component/schema cục bộ; route API thật, gateway, database,
  browser, Cloudflare/JWKS/HTTPS, lab, OpenCTI và production chưa được kiểm.
- W04 nối cục bộ frontend/backend: `/tai-san` dùng adapter HTTP với cùng gateway/API/SQLite như `/tra-cuu`;
  harness có fault refresh 503 rồi phục hồi và fault mutation đã commit nhưng mất success response, không replay.
  Có helper bounded start/status/stop, trace lược dữ liệu và snapshot DB trước cleanup; browser OpenMausBot chưa
  được chạy trong lượt tích hợp này nên browser acceptance và viewport vẫn UNVERIFIED.
- W04 frontend rework F1–F3: đồng bộ `created_by` tối đa 512; mutation chỉ map các cặp status/code đã xác nhận,
  còn lỗi gateway/không rõ của POST/PUT/DELETE là `unknown-mutation` và không replay; context token được kiểm lại
  sau refresh để notice domain cũ không lọt sang tab IP. TDD ghi nhận 4/6/3 failure RED, sau GREEN focused assets
  đạt 53/53 và probe Leader độc lập đạt 6/6; typecheck/lint/build/diff-check đều exit 0. API thật và browser vẫn
  chưa được kiểm trong rework này.
- W04 technology backend cục bộ: `TechnologyStore` và API opt-in quản lý vendor/product/software version bằng
  SQLite riêng, optimistic version và before/after audit nguyên tử; migration additive kiểm schema/index/marker,
  duplicate chỉ map đúng identity active. Đã kiểm JWT/role, Origin/body, bound Unicode/actor/safe integer,
  rollback/corruption/giới hạn và regression assets/W02 bằng fixture tổng hợp. Chưa nối gateway, UI/browser,
  Cloudflare/JWKS thật, W03/OpenCTI, lab hoặc production.
- W04 frontend công nghệ mẫu: `/tai-san/mau` được inject provider công nghệ tách riêng với CRUD và tab/bảng/form
  theo DESIGN; `/tai-san` thật vẫn chỉ dùng domain/CIDR. Adapter technology giữ wire `software_version` chuỗi và
  `version` số bản ghi, parser strict/code-point/UTC, mutation bất định không retry và chỉ GET đối soát; callback
  cũ bị vô hiệu khi đổi tab/provider hoặc unmount. Bằng chứng chỉ dùng fixture/fetch giả cục bộ; API/gateway thật,
  browser, Cloudflare/JWKS/HTTPS, lab, OpenCTI và production chưa được kiểm.
- W04 frontend công nghệ rework F1–F3: cap GET list được tính hữu hạn cho 1.000 DTO tối đa kể cả JSON Unicode
  escape/UTF-8, trong khi mutation/error giữ cap 1 MiB; notice committed sống qua mọi GET retry lỗi và chỉ clear
  khi GET thành công; trạng thái mutation pending/unknown thuộc provider và sống qua đổi tab, không mở khóa bởi
  GET sớm. Probe Leader 4/4, regression focused 120/120, typecheck, lint và build đều đạt ở evidence bàn giao
  rework; API/gateway/browser/lab/production vẫn chưa được kiểm.
- W04 Technology tích hợp cục bộ: `/tai-san` dùng provider HTTP Technology thật; gateway allowlist chính xác hai
  route Technology và runner inject `TechnologyStore` cùng SQLite với `AssetStore`, schema setup trước request.
  Ma trận HTTP loopback 51 assertion kiểm CRUD/duplicate/stale/xóa-tạo lại, IT/analyst/multi-role, 401/403,
  timestamp hỏng không ghi, danh sách đủ 1.000 và từ chối 1.001, non-impact assets/W02, domain/CIDR lookup và
  hai chuỗi fault không replay. Frontend focused 120/120, Python harness 42/42, gateway 14/14, typecheck/lint/
  build 9/9 route đều đạt; browser OpenMausBot và viewport desktop/mobile vẫn UNVERIFIED trong lượt này.
- W03-R backend chỉ đọc: `GET /api/cves` fixture-first đối chiếu exact casefold với snapshot Technology SQLite
  mở `mode=ro`, tách detail/leader summary, rank KEV/EPSS/CVSS/thời gian, cursor theo snapshot/context và cap
  response 1 MiB. R1 khóa product 128, nhãn KEV synthetic exact và raw JSON cursor canonical. Test cục bộ kiểm
  auth/query precedence, schema strict, paging/stale cursor, bất biến SQL cả success/failure và wire fixture exact
  với API thật. B1/B2 khóa schema/index/marker và bounded SELECT trong cùng transaction đọc `mode=ro`, đồng thời
  từ chối authority advisory mơ hồ/sai port mà không DNS; SQL snapshot trước/sau chứng minh success/failure không
  đổi schema/row/audit/user_version. Chưa nối frontend/gateway/browser, feed/OpenCTI, lab/production.
- W03 frontend đọc lỗ hổng: `/lo-hong` dùng provider HTTP GET-only và `/lo-hong/mau` dùng 12 CVE tổng hợp có
  nhãn mẫu; parser phân biệt strict detail/summary, giữ null khác điểm 0, giới hạn response 1 MiB và map lỗi
  401/403/404/422/409/503 an toàn. Giao diện lọc KEV/công nghệ/từ khóa, phân trang, detail từ dòng hiện tại,
  nguồn/as-of/notice, tooltip Việt và bỏ chuỗi trang khi snapshot đổi; leader summary không gọi API tài sản.
  Ownership token chặn callback cũ khi đổi filter/provider/route/unmount. Đây là frontend/test cục bộ; chưa nối
  API/gateway thật, chưa chạy browser, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab hoặc production.
- W03 frontend rework F1–F3: parser chỉ nhận đúng notice hợp đồng, từ chối CVE trùng ở detail/summary và match
  công nghệ trùng hoặc không tăng nghiêm ngặt; response cùng options công nghệ chỉ thuộc provider/context hiện
  hành nên detail cũ không kích hoạt provider mới trong lúc summary/detail kế tiếp còn chờ. Regression mới RED
  7/49 rồi GREEN 51/51, probe QA độc lập 3/3 và toàn bộ portal 356/356; typecheck/lint/build đều đạt sau khi chạy
  độc lập. API/gateway/browser/feed/OpenCTI/lab/production vẫn chưa được kiểm trong rework này.
- W03 sửa parity bộ lọc KEV: adapter HTTP chỉ gửi `kev=true` khi bật “Chỉ KEV”; khi bỏ chọn thì bỏ hẳn tham số
  để Backend trả cả KEV và non-KEV, đồng nhất với sample provider. Regression adapter RED 1/53 rồi GREEN 53/53;
  kiểm thêm component giữ all-CVE qua phân trang/retry và probe Leader nguyên bản đạt 3/3 với alias sang frontend
  tree. Đây chỉ là kiểm cục bộ; không chạy browser/backend/gateway/feed/OpenCTI/lab/production trong lượt sửa này.

- W03 tích hợp cục bộ: gateway chỉ mở `GET /api/cves`; runner inject fixture 16 CVE tổng hợp
  và TechnologyStore cùng SQLite W04. HTTP/wire kiểm detail/summary/quyền/paging/rank, W04 update làm
  cursor 409, tải lại 200, 503→200, response gần/vượt cap và SQL bất biến. Browser desktop 1280×720
  kiểm detail 0/null, filter, paging 409, leader summary không gọi Technology API và retry thủ công;
  mobile 360 px, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab và production chưa kiểm.
- W03 tích hợp rework R2: wire fixtures API thật đã capture được lưu portable trong repo với provenance/hash;
  test mặc định và override hợp lệ đều qua HTTP provider, còn thư mục/file thiếu hoặc JSON hỏng dừng ở preflight
  trước assertions. Near-cap chạy với cả có/không `Content-Length`; quá 1 MiB bị từ chối. Ma trận cùng SQLite
  kiểm thêm W04 POST tạo match và DELETE bỏ match, cursor cũ trả 409, mọi W03 GET giữ SQL bất biến. **Toàn luồng
  vẫn CHƯA ĐẠT:** R1 checkbox KEV thuộc frontend đang chờ commit riêng được review và ghép; rework này không sửa
  component/provider sản phẩm, không tự coi R1 đã xong.
- W03 filter tích hợp cuối: đã ghép R1 để checkbox bỏ chọn không gửi `kev=false`; focused frontend 53/53, wire
  10/10 và probe độc lập 3/3 đạt. Browser desktop 1280×720 trên runtime SHA `90af6d7` chứng minh checked 3 KEV,
  unchecked 16 tổng/3 KEV, hai trang đủ 16 CVE duy nhất và checked lại còn 3; lọc `q` rồi bỏ lọc phục hồi 16.
  Trace chỉ có GET, hai SQLite snapshot trùng SHA-256 và cleanup đóng port/xóa temp. Commit sau browser chỉ cập nhật
  dòng PROGRESS này; mobile/feed/OpenCTI/Cloudflare/JWKS/lab/production vẫn chưa kiểm.
- W03-S1 chuẩn bị tích hợp status cục bộ: gateway mở đúng GET/PUT status và GET history với cap PUT 16 KiB;
  runner opt-in inject `CveStatusStore` cùng SQLite W04 và fixture CVE tổng hợp sau bootstrap explicit. Ma trận
  socket HTTP kiểm quyền/JWT giả, strict body, status/history/cursor, cạnh tranh ghi, drift W04/dataset/identity,
  SQL non-mutation và hai chuỗi PUT một lần + GET phục hồi; cleanup đóng port/xóa temp. Chưa ghép frontend, chưa
  chạy browser, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab và production chưa kiểm.
- W03-S1 prep rework R1: fault phục hồi được ràng buộc theo exact pathname status vừa PUT; GET relation khác và
  status-history không nhận hoặc tiêu thụ bộ đếm. Probe gateway và ma trận HTTP/SQLite có request xen kẽ chứng minh
  từng scenario vẫn chỉ một PUT, một status, một audit và phục hồi hữu hạn; phạm vi chưa ghép UI/browser không đổi.
- W03-S1 tích hợp status chặng A: frontend đã ghép cục bộ và wire capture API thật được parser/provider production
  đọc với Unicode, note 1000, actor 512, vendor/version 128, history 100+cursor; product context mới chứng minh 128,
  còn 256 không biểu diễn được qua dataset CVE đang giới hạn 128 và được giữ là blocker thay vì sửa contract. Browser
  desktop 1280×720 đã chứng minh known-commit PUT200, GET `503→503→200`, lỗi tạm thời vẫn giữ notice đã lưu và
  đóng/mở chi tiết trong cùng trang phục hồi với đúng một status/audit. Unknown-outcome reentry cùng trang còn
  PENDING; mobile, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab và production chưa kiểm.

## Vướng mắc
- Bộ version mới chỉ được kiểm cấu hình; chưa pull image, boot service hoặc chứng minh tương thích/runtime trên lab
- Capability upload/review/approve, work ID, trạng thái draft trước/sau và quyền thực tế chưa kiểm trên lab
- Chưa gọi feed hoặc LLM, chưa có key/điều khoản OTX, chưa đo RAM/queue và chưa xác minh demo MITRE + OTX (#10)
- X01 còn thiếu dataset báo cáo thật được hai người gán nhãn và các cấu hình C2–C4; smoke C1 không chứng minh
  chất lượng extractor hoặc TTP
