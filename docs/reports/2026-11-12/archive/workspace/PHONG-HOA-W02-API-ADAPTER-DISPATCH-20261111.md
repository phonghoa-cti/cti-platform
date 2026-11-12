# W02 API + adapter và QA harness — gói việc song song

Ngày 11/11/2026. Root: `$WORKSPACE`.

Mục tiêu: Backend và Frontend xây hai đầu kết nối tra cứu IOC theo một hợp đồng, trong khi QA kiểm bộ demo nạp tài liệu. Mỗi người một tree/phạm vi; Sol medium trực tiếp, không giao worker khác. Không push/PR/merge/deploy, cloud/model/secret/OpenCTI/lab hay dữ liệu thật.

## Nguồn/hợp đồng chung đã chốt

- `PHONG-HOA-W02-API-CONTRACT-BRIEF.md`, SHA256 `93dab3d51d5e62e63711f6dc7fbd6b05a5c039c38f62e6e667b3ac2b34da84df`: schema HTTP, ba fixture JSON, lỗi/quyền/bounds/checks.
- `PHONG-HOA-PARALLEL-EXECUTION-20261111.md`, SHA256 `c444100fb49b5ebc5c1201e9c245966739de328091344995c0695035bc09245f`, mục W02 bổ sung là quyết định cuối khi brief viết tắt. Không thay HTTP contract theo view model cũ.
- Tái dùng W02/api-portal/DESIGN và `portal/web/data/api-client.ts` cho kiểu parser chặt + fetch dependency injection; không sửa transport W05. Nguồn API Fetch chính thức đã mở: https://fetch.spec.whatwg.org/ (11/11/2026). Dùng platform Fetch, không thêm thư viện mạng.
- Ba JSON fixture trong brief là mẫu chung cho test hai phía; worker ghi literal vào test của mình để test chạy độc lập, không phụ thuộc file ngoài repo. Không tự sửa fixture để che contract mismatch; báo đúng khác biệt.

## Backend — W02-LOOKUP-API-IMPLEMENT

1. Source chỉ đọc `cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`. Tạo target `cti-w02-lookup-api`, branch `feat/w02-lookup-api-20261111` từ exact SHA này. Không lấy importer fc08897 làm base; hai phần không phụ thuộc mã.
2. Theo brief API cùng chốt Leader: GET `/api/ioc`, xác minh JWT rồi role server-side, filter TLP trước scoring, missing adapter 503 chỉ W02, W05 giữ contract. Role IT không nhận dữ liệu AMBER/RED, kể cả qua score/reason/count/related/assets.
3. Chốt rõ nhãn output: với record được phép, response TLP là mức hạn chế nhất trong **record_tlp và facts còn visible**, không hạ nhãn record. Record ngoài quyền trả not_found; malformed DTO/unknown TLP trả 503. Source visible tối thiểu 1 cho found; source duplicate giống hệt thì dedupe, mâu thuẫn thì 503. as_of độc lập dữ liệu ẩn theo plan.
4. Allowlist nguyên brief: `portal_api/app.py`, `schemas.py`, mới `ioc_lookup.py`, mới `portal_api/tests/test_w02_ioc_api.py`, tùy chọn `docs/specs/W02-lookup-offline-contract.md`, `docs/PROGRESS.md`. Không sửa core/auth/settings/W05/frontend/dependency/lock. Nếu cần ADR, chỉ thêm một `docs/adr/0012-w02-offline-lookup.md` khi số chưa được dùng trong target; nếu trùng báo Leader.
5. Dùng Python 3.12.13 sẵn ở source `.venv` với cwd/PYTHONPATH target; có thể tạo target venv từ cache đã có, không sửa môi trường chung hay tải dependency mới. Kiểm exact interpreter/dependency trước chạy.
6. TDD + toàn `portal_api/tests` (gồm W05 regression), Ruff check/format/diff, demo TestClient IT/analyst/multi-role/hidden-data mutation, JSON closed/no-store/Vary. Không listener/browser/network adapter thật. Default không dùng fixture hoặc synthetic identity trong production.
7. Report `PHONG-HOA-W02-LOOKUP-API-RESULT.md`, evidence `w02-lookup-api-evidence/`: raw command/output/exit/count, base/HEAD/diff, fixture demo, manifest, commit local sạch và giới hạn. Không chỉ bảng tóm tắt thay log.

## Frontend — W02-LOOKUP-HTTP-ADAPTER

1. Source chỉ đọc `cti-w02-lookup-ui@a949081bf302801e11d69a8ee70c1232d68955cc`. Tạo `cti-w02-lookup-http`, branch `feat/w02-lookup-http-20261111` từ exact SHA này. Giữ nguyên thiết kế và mẫu W02/W05; không đợi Backend để viết parser/transport theo contract đã chốt.
2. Đầu ra nhỏ nhất: `createIocHttpDataSource({fetcher?})` đáp ứng `LookupDataSource`; parser HTTP strict được export để test. Chỉ request tới đường dẫn cố định `/api/ioc` cùng origin, GET với URLSearchParams có đúng `value`; `credentials:same-origin`, `cache:no-store`, `redirect:error`, Accept JSON. Không tự tạo header JWT/email/role, không localStorage/analytics/log query hoặc đưa query lên URL trang.
3. Timeout hữu hạn 10 giây bằng AbortController bao trùm fetch + đọc body, cleanup timer/reader mọi nhánh; không retry. Body UTF-8 tối đa 1 MiB, đọc có giới hạn rồi parse JSON; không nhận HTML/login-page như kết quả. Thiếu/malformed/mismatch schema/status trả unavailable, không raw error/message ra giao diện. Không fallback fixture khi HTTP lỗi.
4. Parse exact object keys, loại array/null sai, numbers hữu hạn/integer strict, Unicode code-point caps, 8 IOC types, 5 TLP, bounds và invariant của found/allowlisted/not_found như brief. Source timestamp UTC có ý nghĩa và first_seen<=last_seen; không tự chuẩn hóa/chấm điểm/đoán allowlist. Header success phải JSON; thông báo lỗi chỉ map từ status/code cho phép, không render server message.
5. Mapping: found→view result; allowlisted→view result với found=false/allowlisted=true; not_found→not-found, không hiển thị là an toàn. `sources.first_seen`→firstSeen; enrichment `{}` vì contract chưa có dữ liệu này. Parser giữ đầy đủ last_seen/TLP/asset_match/parts; view hiện chỉ tiêu thụ phần đã có, không dựng số liệu còn thiếu. `input` nội bộ lấy đúng query caller, không yêu cầu API echo.
6. Hỗ trợ đầy đủ 8 nhãn type trong view (ipv4/ipv6/domain/url/email/md5/sha1/sha256); có thể giữ legacy `hash` chỉ cho fixture cũ, HTTP không nhận type hash chung. Thêm trạng thái authentication-required cho 401 authentication_required; 403 forbidden, 422 invalid_ioc/private_ip, 503 lookup_unavailable tương ứng các trạng thái hiện có. Lỗi/status không khớp phải unavailable. Copy vẫn dùng canonical value từ response, display dùng trường defang, render text.
7. Allowlist: mới `portal/web/data/ioc-lookup-http.ts`, mới `portal/web/tests/ioc-lookup-http.test.ts`, sửa `portal/web/data/ioc-lookup.ts` chỉ types/state; `portal/web/tests/ioc-lookup.test.tsx` chỉ kiểm adapter injection/types/state/regression; `portal/web/messages/vi.json`, `en.json` chỉ W02; `portal/web/components/ioc-lookup.tsx` chỉ hỗ trợ trạng thái/type cần thiết, không đổi bố cục; `portal/web/README.md`, `docs/PROGRESS.md` mục task. Không route mới, không đổi trang mẫu sang HTTP, không gateway/backend/W05/config/package/lock/DESIGN/RUNS.
8. Tests không mạng: fetch mock trả Response chuẩn cho ba fixture chung; 8 type/5 TLP; query encoding (URL có &/#/Unicode), không thêm identity header; unknown≠safe; lỗi HTTP/HTML/invalid JSON/extra fields/nonfinite/out-of-bound/empty sources found; 10s timeout/body cap/cancel; A→B response cũ và clipboard R1/R2 không hồi quy; render text an toàn. Toàn web test/typecheck/lint/build/diff một lượt cuối, raw logs.
9. Report `PHONG-HOA-W02-LOOKUP-HTTP-RESULT.md`, evidence `w02-lookup-http-evidence/`, local commit sạch. Đây là parser/adapter + component test với HTTP giả; chưa chứng minh kết nối Backend/browser/JWT/OpenCTI. Không mở browser/listener; không cài dependency mới (dùng cache hiện có trong target nếu cần, không đổi lock).

## QA — X01-INGEST-BROWSER-HARNESS-QA

Source chỉ đọc `cti-x01-ingest-browser-prep@970a130452eb69bae3cd3793eab5a527b3d382d5`, base `db36ec01b765dfd515c1d0ef13642a693b777172`. Không cần đọc tree Backend/Frontend đang viết. Đọc brief harness, execution plan và kết quả Engineer; F1 đã sửa ở tree khác nhưng chưa ghép vào source này, không báo F1 cũ thành finding mới.

- Rà đúng 5-file diff, trọng tâm helper seed và `verify_browser_outcome`, stdin deadline/EOF và ownership cleanup. Unit 22/22 + TXT/PDF positive của Engineer có evidence; không lặp full suite/backend/web.
- Chạy tối đa vài probe độc lập có giá trị: sửa envelope sau seed nhưng giữ source hash; sửa payload/provenance hoặc final-audit count/version/actor trong DB tổng hợp; kiểm expected selection và thiếu/bất nhất bundle; deadline/EOF cleanup nếu có khoảng trống. Chỉ thao tác DB/temp/evidence của QA; kết quả FAIL cần minimal repro cụ thể, không sửa mã sản phẩm.
- Leader thấy candidate gap cần xác minh: hậu kiểm chỉ so `envelope.draft.source.sha256` với seed, không thấy so lại hash toàn envelope; `database_state` fetchone audit mà không count decision. Kiểm có thể false PASS không trước kết luận; không suy static suspicion thành exploit.
- Phân loại rõ coverage: browser-session hiện chỉ TXT, chưa có PDF/self-approve/save-refresh/decision-refresh trong cùng ingest scenario. So với giai đoạn chuẩn bị thì ghi gap cho bước tích hợp; xác định phần nào phải sửa trước khi dùng harness chứng minh ma trận cuối.
- Dùng Python target `.venv` 3.12.13, `-B`, cache tắt, basetemp riêng. Không browser/listener demo; test loopback riêng chỉ khi cần kiểm lifecycle và phải cleanup owned. Không chạy batch chờ dài, mạng ngoài máy, secret/model/OpenCTI/lab.
- Chỉ ghi `PHONG-HOA-X01-INGEST-BROWSER-HARNESS-QA-RESULT.md`, `x01-ingest-browser-harness-qa-evidence/`; không source/index/branch/RUNS/plan/evidence Engineer. Report severity/file:line/repro/expected/actual/command/exit/log/minimal fix, source before-after, manifest. Không tự ghi source đã đạt.

## Cổng nối

W02 API và HTTP adapter dùng contract cố định nên triển khai song song, chỉ nối runtime sau khi cả hai đạt. QA kết luận harness sẽ mở việc Engineer sửa hoặc ghép vào importer `fc08897a...` trên tree tích hợp riêng; không tự merge/cherry-pick. Leader cập nhật RUNS bằng receipt thật, giữ ID lịch sử và chỉ nghiệm thu theo bằng chứng.
