# Nghiệm thu API W02 và bước nối tiếp

Ngày 11/11/2026. Root: `$WORKSPACE`.

## Kết luận có bằng chứng

**W02 API: ACCEPTED_LOCAL** tại `78b026003c86985c7f062986088bfd1f7210a1b1`, base `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`, branch `feat/w02-lookup-api-20261111`. Leader đọc toàn bộ implementation/service/schema/route và tests rủi ro, đối chiếu contract đã chốt; diff đúng 5 file +1183/-4, tree sạch. Chạy tươi toàn `portal_api/tests`: **178 passed**, exit 0, bao gồm 44 W02 và W05 regression. Diff-check base..HEAD exit 0. Manifest 7/7 khớp `cff4b4feeaa0eeaddc1be08140a6548a8f737bc50ee18f0c1921702fa91ebf87`. Giữ giới hạn fixture adapter/JWT tổng hợp/in-process; chưa chứng minh OpenCTI hoặc HTTP/browser thật.

**X01 harness: PARTIAL, chưa chấp nhận toàn bộ** tại `cba5b39c4e95449aa152dae5c2a1099c2e75c515`. Diff đúng 6 file +441/-35, tree sạch, diff-check exit 0. Manifest rework 23/23 khớp `03af0d8a12887f18151a3003eb0fb9ef322b7a64caaca991771e0fdbdf16a063`.

- F1 canonical envelope và F2 actor/audit: chấp nhận bản sửa trong phạm vi hậu kiểm. Leader chạy tươi 8 tests chọn theo `canonical_digest_changed or actor_or_selection`: 8 passed, exit 0. Wrapper QA cũ: baseline nhận, bốn mutation bị từ chối và không TypeError.
- F3 vẫn FAIL qua hai probe mới của Leader. Đây là lỗi năng lực phát hiện của verifier, **không phải bằng chứng exporter hiện tại làm lộ dữ liệu**.
- Regression 38 tests/59 STIX checks/TXT/PDF offline của Engineer đã có log và hash; không lặp các suite đó khi đã xác định lỗi cần sửa.

Raw bằng chứng: `leader-api-harness-acceptance-20261111/api-regression.log`, `harness-f1-f2.log`, `harness-review.log`, `verified-state.json`, `verify.py`. Script `verify.py` exit **1** có chủ đích vì hai mutation sau vẫn trả PASS.

## Engineer — sửa F3 bổ sung, cùng thread/tree

Một Sol medium trực tiếp, không giao worker khác. Tree `<root>\cti-x01-ingest-browser-prep`, branch `feat/x01-ingest-browser-prep-20261111`, base rework `cba5b39c4e95449aa152dae5c2a1099c2e75c515`. Dùng lại brief, spec, nghiên cứu và phạm vi cũ; không tạo tree thay thế.

1. `escaped_evidence_in_description`: chèn `ghi nhận` vào `report.description`, serialize JSON với `ensure_ascii=True`, cập nhật bundle SHA trong stdout. JSON parse ra vẫn chứa đúng marker, nhưng kiểm `marker in serialized_bytes.decode()` không thấy chuỗi nên PASS. Expected REJECTED. Sửa kiểm theo nội dung JSON đã parse (bao gồm nested strings/keys phù hợp), không phụ thuộc cách escape hoặc whitespace. Với description chứa JSON provenance, kiểm lớp JSON có cấu trúc đúng khi cần; không decode escape tùy tiện trên toàn file.
2. `deselected_ioc_in_description`: giữ SCO selected đúng, thêm IOC index 0 đã bỏ vào `report.description`; summary/hash/count vẫn khớp. Hiện chỉ so `sco_values == selected_values`, làm mất điều kiện âm IOC đã bỏ ở bản cũ. Expected REJECTED. Phải kiểm IOC bị bỏ vắng trong toàn bundle semantic; đồng thời giữ điều kiện IOC được chọn ở đúng SCO. Tránh nhầm nếu một giá trị đồng thời được chọn do duplicate; dùng tập deselected trừ tập selected theo contract.

Minimal repro đã có tại script Leader ở trên; không sửa script hoặc QA evidence để làm xanh. Được thêm test regression trong target. Allowlist lần này: `tools/local_integration/tests/run_ingest_browser_stix.py`, `tools/local_integration/tests/test_runner.py` (hoặc file test riêng trong cùng thư mục), `tools/local_integration/README.md`, `docs/PROGRESS.md`; không cần sửa runner/importer/exporter/store/API/UI.

Kiểm RED→GREEN hai ca và biến thể nested/escaped marker; baseline hợp lệ được nhận, F1/F2 và probe cũ vẫn bị chặn đúng lý do. Chạy test_runner, TXT/PDF offline, Ruff/format file đổi, diff-check; không lặp W05 59 checks nếu không đổi helper/runner và không có lỗi mới liên quan. Lưu evidence mới `x01-ingest-browser-harness-evidence/rework-f3-semantic/`, cập nhật report harness, local commit sạch và exact command/exit/count/hash. Chưa ghép importer/chạy browser; không push/PR/merge/cherry-pick/deploy/secret/cloud/OpenCTI/lab.

## Frontend — W02-LOCAL-INTEGRATION

Mục tiêu: người dùng mở trang tra cứu, nhập IOC và xem kết quả từ **API W02 thật chạy cục bộ với nguồn tổng hợp**, thay vì chỉ component/mock HTTP. Một CTI Frontend Sol medium trực tiếp trên tree riêng, giữ thiết kế hiện có; không giao worker khác.

### Nghiên cứu tái sử dụng và ref

- Đã có: W02 HTTP adapter `88e9a9b6e491c0d450640e848043f41c80feb4bd`, API `78b026003c86985c7f062986088bfd1f7210a1b1`, spec `docs/specs/W02-tra-cuu-ioc.md`, `PHONG-HOA-W02-API-CONTRACT-BRIEF.md`, bổ sung `PHONG-HOA-W02-API-ADAPTER-DISPATCH-20261111.md`.
- Tái dùng `tools/local_integration/runner.py::LocalRun`, `local_settings.py::make_local_settings`, `gateway.mjs` và tests HTTP/lifecycle của W05. Hiện gateway chỉ nhận drafts/v1, runner chưa inject lookup_port, trang mẫu chưa inject HTTP source: đó là ba điểm nối cần làm. Không dựng runner/gateway thứ hai, không thêm thư viện.
- Source READONLY `<root>\cti-w02-lookup-http@88e9a9b6e491c0d450640e848043f41c80feb4bd` và `<root>\cti-w02-lookup-api@78b026003c86985c7f062986088bfd1f7210a1b1`; kiểm clean/exact trước/sau.
- Tạo target `<root>\cti-w02-local-integration`, branch `feat/w02-local-integration-20261111` từ HTTP SHA 88e9a9b6. Chuyển chính xác API delta base cf9e6094..78b02600 của bốn file `portal_api/app.py`, `schemas.py`, `ioc_lookup.py`, `tests/test_w02_ioc_api.py` bằng patch cục bộ đã kiểm; không sửa logic API đã nghiệm thu. Không git merge/cherry-pick. `docs/PROGRESS.md` tổng hợp riêng. Nếu target tồn tại hoặc patch có conflict ngoài dự kiến: giữ nguyên và báo Leader, không reset.

### Hành vi và phạm vi ghi

- Thêm `/tra-cuu` dùng client wrapper khởi tạo `createIocHttpDataSource` ổn định; không truyền object chứa hàm qua ranh giới server/client. `/tra-cuu/mau` vẫn dùng mẫu. Không thay thiết kế/bố cục/CSS/DESIGN.
- Tách nội dung nhãn theo nguồn: trang HTTP không được nói “Không gọi mạng”; dùng nhãn rõ “Bản thử kết nối API · Dữ liệu tổng hợp cục bộ · Chưa kết nối OpenCTI” cho lát cắt này. State rỗng không nói fixture một cách sai; unknown không được diễn đạt an toàn. Giữ Việt/Anh. Phần thử local là trạng thái sản phẩm hiện tại, không bật synthetic adapter trong default production API factory.
- Mở đúng `/api/ioc` ở gateway, giữ toàn bộ giới hạn/header sanitation/timeout/route allowlist và behavior W05. Không wildcard `/api/*`. Inject JWT tổng hợp chỉ phía gateway cục bộ, không đưa vào JS/UI/URL/log/screenshot; client header giả không được thay actor.
- LocalRun có scenario W02 rõ ràng, lookup_port fixture deterministic chỉ trong `tools/local_integration`, as_of cố định độc lập dữ liệu ẩn. Có mixed-TLP cho IT vs analyst, found/allowlist/unknown và scenario 401/403/503. Default API thiếu port vẫn fail closed như đã nghiệm thu. Không fixture fallback khi HTTP lỗi.
- Được sửa: `portal/web/app/tra-cuu/page.tsx` mới; client wrapper mới trong `portal/web/components`; `ioc-lookup.tsx` chỉ injection/nhãn/source mode; W02 tests/messages/README; `tools/local_integration/runner.py`, `gateway.mjs`, tests/README và file fixture W02 riêng dưới cùng thư mục; `docs/PROGRESS.md`; bốn file API chỉ nhận exact patch. Không API semantics/auth/settings/core/W05 UI/package/lock/DESIGN, source tree khác, RUNS hoặc evidence cũ.

### Kiểm và đầu ra

1. TDD điểm nối mới: gateway route/header spoof, fixture inject/default missing, route HTTP dùng một GET và không fallback; giữ lỗi/race/clipboard cũ.
2. Chạy portal_api/tests tại target, web test/typecheck/lint/build, node gateway tests, pytest runner; Ruff/diff-check/phạm vi. Dùng dependency cache/venv sẵn với đúng cwd/PYTHONPATH, không sửa môi trường nguồn, không tải/cài dependency mới.
3. HTTP loopback ma trận IT/analyst/multi-role, hidden-data invariant, found/allowlisted/not_found, 401/403/422/503; xác minh no-store/Vary và không header client giả chi phối. Không đổi nội dung báo cáo theo dữ liệu ẩn.
4. Chỉ một bộ listener local do run sở hữu, TTL tối đa 300s mỗi lần, cleanup port/PID/temp khi xong hoặc lỗi. Browser **tích hợp của OpenMausBot** là nơi kiểm; không Playwright/CDP/shell-launched browser/host browser thay thế. Xem trang trước thao tác, giữ snapshot/screenshot cần thiết. Nếu browser tích hợp không truy cập loopback thì báo đúng blocker; không đổi bề mặt trái phép.
5. Browser ít nhất found `evil.example`, allowlist `8.8.8.8`, unknown; thêm state 401 và 503 khi scenario có. Nhập/tra cứu/copy giá trị canonical nếu quyền cho phép, đổi VI/EN, xác minh không hiện raw error. HTTP matrix là bằng chứng riêng, không thay bằng chứng thao tác browser. Không cần làm lại mobile audit rộng ở lát cắt này.
6. Report `<root>\PHONG-HOA-W02-LOCAL-INTEGRATION-RESULT.md`, evidence `<root>\w02-local-integration-evidence/`: exact base/source/HEAD, diff/allowlist, commands/exit/count, route+API evidence cùng run, screenshots/step refs, cleanup, manifest và local commit sạch. Ghi rõ dữ liệu tổng hợp, JWT local; Cloudflare/OpenCTI/lab/production vẫn UNVERIFIED. Không push/PR/merge/deploy hoặc gọi Internet/feed/model/secret.

## Điều phối và cổng tiếp

Frontend làm W02 integration trên tree mới; Engineer chỉ sửa hậu kiểm X01 trên tree cũ. Hai phạm vi độc lập, chỉ Frontend dùng browser/listener demo. Backend đã xong phạm vi API và không sửa song song integration; QA nhận kiểm độc lập khi có commit ổn định cần review. Không cần thêm thành viên.

Khi bắt đầu lượt có một lịch Leader đang chạy đồng thời; chỉ đọc/kiểm source trước. Kiểm lại đã idle, không giao hoặc ghi sổ chồng. Hai lịch tiếp tục đã đọc lại và còn bật; dự án active nên giữ nguyên. Lịch 30 phút còn cắt phần cuối instructions; không tự thay cấu hình. Việc cũ đã accepted không được nghiệm thu lặp.
