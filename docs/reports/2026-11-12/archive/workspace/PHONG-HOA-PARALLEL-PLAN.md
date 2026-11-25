## Cập nhật 12/11 — Backend S1 đạt; sửa Frontend và chuẩn bị HTTP song song

Backend accepted tại4f7100cf: Leader chạy57test và1case API thật đều đạt; RECHECK.md trong leader-w03-status-review-20261112. Frontend13b80252 đạt7probe cũ nhưng còn F5/F6: parser từ chối case-only rename hợp lệ và pending bị kẹt sau reopen409. Frontend nhận rework2 trong thread/tree cũ. Engineer nhận W03-STATUS-INTEGRATION-PREP ở tree cti-w03-status-integration từ Backend accepted, chỉ tools/harness/HTTP; chưa ghép UI hoặc chạy browser. Receipt hiện hành trong RUNS và recheck-receipts.json. Cả hai independent, không đọc/sửa tree đang làm của nhau. Ghép toàn luồng chờ Frontend và prep đều accepted. Giữ lịch tiếp tục, project active.

Các mục dưới là lịch sử.

## Cập nhật 12/11 — W03-S1 cần sửa trước tích hợp

Leader review Backend b8957e63 và Frontend e31f0b40: baseline Backend14PASS nhưng8probe độc lập FAIL; Frontend7probe FAIL assertion. Chi tiết tại leader-w03-status-review-20261112/REVIEW.md. Backend sửa B1/B2 (strict request + dữ liệu lưu hỏng); Frontend sửa F1–F4 (khóa unknown, ownership callback, history409, wire). Hai bên tiếp tục đúng tree/thread cũ, một Sol medium mỗi tree; receipt mới trong RUNS và rework-receipts.json. Chưa giao Engineer tích hợp, không nhận các số full suite của worker là nghiệm thu. W03-R đã accepted vẫn giữ nguyên. Giữ callback và lịch tiếp tục; người dùng chưa cần thao tác.

Các mục dưới là lịch sử.

## Cập nhật 12/11 — W03-S1 giao Backend và Frontend song song

Nghiên cứu W03-STATUS-NEXT accepted có sửa tại PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md: stale context phải409/no write; migration ngoài request; status/history theo relation qua route riêng, giữ W03-R nguyên. List status filter/KPI Leader là S2 để sau, không coi W03 hoàn tất.

Backend: cti-w03-status-backend, request f24818b7-412a-48de-b17c-d2d26aa42489, thread93a366c6-3c4c-4bb7-8b6c-9c7801aa0c3a. Frontend: cti-w03-status-frontend, request b38b9494-2d10-4d08-87f6-50a485f21ad7, threada7b74dcb-d309-4b2b-a34e-19b13d145482. Cùng base7ff6eb3, một Sol medium trực tiếp mỗi tree; hai receipt queued không phải chứng cứ implementation. Chỉ giao tích hợp sau hai kết quả đạt review/wire parity. Giữ callback, không giao thêm writer hoặc poll.

Các mục dưới là lịch sử.

## Cập nhật 12/11 — W03-R đã nghiệm thu, nối nghiên cứu trạng thái

W03-READ-INTEGRATION accepted tại 7ff6eb3af21d8de65836bfbf707396ae5690de0b. Leader đối chiếu bộ lọc 3 → 16 → 3, đủ 16 CVE duy nhất, chỉ GET, SQLite không đổi và 69 mục manifest khớp; biên bản leader-w03-final-acceptance-20261112/ACCEPTANCE.md. Chỉ dữ liệu tổng hợp/desktop cục bộ, chưa có status/audit W03-S; mobile/feed thật/OpenCTI/lab/production vẫn chưa kiểm.

W03-STATUS-NEXT đã giao CTI Research theo PHONG-HOA-W03-STATUS-NEXT-BRIEF-20261112.md; request ab91a48c-9fff-4aa3-9337-7a9b69a3abfc, thread d1ec42a3-3552-4ba9-980d-fe73c1ba1bb2. Nghiên cứu bổ sung trên base đã đạt, chỉ ghi báo cáo, không source/ledger. Receipt queued không phải bằng chứng đã chạy hoặc hoàn thành. Leader chốt contract khi có kết quả rồi mới giao implementation. Các mục dưới là lịch sử.

## Cập nhật 12/11 03:10 — R1/R2 đạt riêng, đang ghép bộ lọc cuối

Frontend7ff62711 và R2 Engineer9579d165 đã được Leader kiểm tại leader-w03-rework-acceptance-20261112/ACCEPTANCE.md. W03-FILTER-FIX accepted; toàn W03-READ-INTEGRATION chưa accepted. Engineer giữ cùng tree/thread, nhận cherry-pick7ff62711 và kiểm browser3KEV→16tất cả→3KEV theo PHONG-HOA-W03-FILTER-INTEGRATION-BRIEF-20261112.md. Receipt ea0642c1-7fb0-43aa-87ac-ddf62a6a3cee, thread024d0127-8ec0-48ac-bd81-cbe0d65ff053. Không thêm writer, không lặp recovery/summary đã kiểm. Các mục dưới là lịch sử.

## Cập nhật 12/11 02:55 — W03 cần sửa bộ lọc và kiểm wire

Candidate tích hợp 93962d9 chưa accepted: bỏ chọn Chỉ KEV đang loại KEV; wire tests thiếu file ngoài cho false PASS ở hai case503. Frontend nhận W03-FILTER-FIX trong tree riêng f650f04d; Engineer sửa wire/coverage trong integration tree, không sửa UI. Receipt trong RUNS và leader-w03-integration-review-20261112/rework-receipts.json. Khi hai kết quả đạt, Leader mới chuyển commit filter để Engineer ghép và kiểm browser 3KEV → 16tất cả. Giữ evidence recovery/summary/SQL đã đối chiếu; không giao trùng. Các mục dưới là lịch sử.

## Cập nhật 12/11 — W03 đã nghiệm thu hai đầu vào, giao tích hợp

Backend abcd14dacca361791b17719632d2ce38557d6baf và Frontend f650f04de8f08238e13e2630f974e9f30ef838b5 accepted cục bộ. Engineer nhận W03-READ-INTEGRATION theo PHONG-HOA-W03-INTEGRATION-BRIEF-20261112.md, tree cti-w03-read-integration riêng. Request d9f78c6b-39ef-4a0b-979d-ff53045995d9, thread 024d0127-8ec0-48ac-bd81-cbe0d65ff053 đã queued; chưa chứng minh đang chạy hoặc tích hợp hoàn thành. Giữ hai source trees, không giao writer khác. Browser/feed/lab/production vẫn chưa nghiệm thu. RUNS là sổ trạng thái hiện hành; các mục dưới là lịch sử.

## Cập nhật 11/11 — technology được giao song song sau nghiên cứu

Research W04-TECHNOLOGY-NEXT accepted có điều chỉnh tại PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md: software_version chuỗi/version số bản ghi; trim+casefold, không NFKC; đúng403/413/415; migration/audit rollback và không ảnh hưởng W02.

- Backend: tree cti-w04-technology-backend, request d39e26a6-05a4-480a-b6a7-1051a415e18c, thread9b474792-9eaf-40d1-9e71-d38af6006f59.
- Frontend: tree cti-w04-technology-frontend, request aa2d3c84-c646-4f8f-8abd-07cd84c6cb68, thread e41d79fa-1aed-471d-96b4-54494ffc0949.

Cùng base8a767314; mỗi người Sol medium trực tiếp, không worker lồng. Hai receipt queued, chưa phải đang chạy/hoàn tất. Frontend làm tab mẫu/provider/HTTP mock độc lập. W04-TECHNOLOGY-INTEGRATION chỉ planned, chờ Leader nghiệm thu cả hai head và lập brief. Không ghi technology đã đạt hoặc nối W03 CVE thật. Lịch nối việc giữ enabled.

## Cập nhật 11/11 23:07 — nghiệm thu domain/CIDR và nối công nghệ

W04-LOCAL-INTEGRATION đã accepted tại 8a767314b654d39c1ddc2995b7919c44a5b7027a: 53/53 artifact khớp, 6 DB/trace và 6 ảnh đối chiếu; Leader chạy mới 71 kiểm HTTP exit 0. Lượt stalled đã phục hồi và trả kết quả, không suy thành bảo đảm phục hồi mọi sự cố. Phạm vi domain/CIDR local desktop, chưa phải toàn bộ W04/Phong Hỏa. Mobile và runtime ngoài máy vẫn chưa kiểm.

Đã giao W04-TECHNOLOGY-NEXT cho CTI Research, receipt 4fa536de-ba5c-4e2d-a6b6-8bcc5a574a9d, thread 9f4697d2-4f80-41aa-a1c6-c26743a71040 (queued). Chỉ nghiên cứu vendor/product/version theo W04 và ranh giới W03, không implementation/source edit. Báo cáo dự kiến PHONG-HOA-W04-TECHNOLOGY-RESEARCH-20261111.md. Phiên bản chỉ hiển thị; không tự ghép version-range. Lịch tiếp tục dự án giữ enabled.

## Cập nhật 11/11 22:50 — phục hồi lượt tích hợp bị dừng

Request a8d902c0 bị stalled; Leader thấy mã đã lưu tại 59d679e0949fea5ece953645cd6b80303546b43a, tree sạch, chưa có nghiệm thu tích hợp. Đã giao lần phục hồi thứ nhất trên cùng thread Engineer 5262b550-6793-407c-b9fc-bc10820a712f, receipt 391c163e-4cb7-44ca-bb93-0b58afdfc2e4 (queued). Không tạo writer thứ hai hoặc làm lại các đầu vào đã đạt. Brief bổ sung: PHONG-HOA-W04-INTEGRATION-RECOVERY-20261111.md. Engineer thu kết quả đã có, hoàn tất kiểm còn thiếu và bàn giao browser/helper theo khả năng thực tế. Không coi queued là đang chạy hoặc hoàn tất.

# Phong Hỏa — phân công song song từ 10/11/2026

## Cập nhật 11/11 22:25 — đã giao nối W04 sau nghiệm thu hai đầu vào

Frontend `fd04f95e` accepted component/adapter sau 6 probe độc lập PASS; prep `65254568` accepted HTTP cục bộ sau 64 assertions mới, recovery503→200 và DB/cleanup đúng. SHA/tree sạch và 4/4 hash evidence prep khớp. Acceptance `leader-w04-inputs-acceptance-20261111/ACCEPTANCE.md`; không đồng nghĩa UI/browser đã đạt.

Engineer nhận việc bổ sung `W04-LOCAL-INTEGRATION`, tree mới `cti-w04-local-integration` từ prep và ba commit Frontend đã chốt. Request `a8d902c0-9c10-4c57-be79-7d61d1a83fbf`, thread `5262b550-6793-407c-b9fc-bc10820a712f`, outcome queued. Brief `PHONG-HOA-W04-LOCAL-INTEGRATION-BRIEF-20261111.md` yêu cầu route thật/cùng DB, quyền, browser recovery/no replay/unknown outcome; thiếu browser ở worker thì bàn giao helper để Leader kiểm tiếp. Không có writer mới trong hai source trees.

## Cập nhật 11/11 22:07 — Frontend rework và HTTP prep song song

Frontend `be131133` chưa nghiệm thu: Leader tái hiện 3 finding bằng 6 test độc lập (5 FAIL/1 PASS): created_by bound sai; gateway failure khi mutation phân loại sai unknown outcome; refresh cũ set notice sau đổi tab. Rework cùng thread `957c7dec-fe60-4717-acf1-8531e349e4aa`, request `8bad0526-df81-46df-8484-3d306c606575`; brief `PHONG-HOA-W04-FRONTEND-REWORK-20261111.md`. Source tree không bị Leader sửa.

Backend `90b26287` vẫn accepted. CTI Engineer nhận `W04-INTEGRATION-PREP` từ đúng SHA đó trong tree mới `cti-w04-integration-prep`, chỉ local gateway/runner/HTTP tests, không chạm hoặc lấy mã Frontend. Request `2f89df42-a919-4ad9-a4ee-949b342ee13f`, thread `54ea127f-33f4-40fa-9e8b-56095c9b1d79`; brief `PHONG-HOA-W04-INTEGRATION-PREP-BRIEF-20261111.md`. Cả hai receipt queued là đã giao, chưa phải đã chạy/xong. Chỉ nối UI khi Frontend và prep được nghiệm thu; browser/lab chưa xác minh.

## Cập nhật 11/11 21:57 — Backend W04 đã nghiệm thu cục bộ

Leader chấp nhận `90b26287eccc416fd7e7e736b0ad37632e0c34b1`: delta F4 đúng 3 file, kiểm mới 55 tests và 2 probe độc lập PASS/exit 0, tree sạch; dùng lại kiểm F1–F3/W02 99 tests + 7 probe từ lượt trước. Bằng chứng `leader-w04-backend-acceptance-20261111/ACCEPTANCE.md`. Các kết luận FAIL bên dưới là lịch sử đã được sửa; không chạy lại/giao lại Backend.

Frontend giữ nguyên request `659a5f35-1227-4205-a8dd-7cafc677f9bb`, thread `957c7dec-fe60-4717-acf1-8531e349e4aa`, quan sát running. Sau khi Frontend được nghiệm thu, giao Engineer tích hợp hai SHA đã đạt trong tree riêng, kiểm cùng DB và browser. Backend đạt không chứng minh luồng W04 đã tích hợp; chưa push/merge/deploy/lab.

## Cập nhật 11/11 — sửa QA F1–F4, Frontend tiếp tục

QA report đã được Leader kiểm manifest23/23, đọc source và tái chạy nguyên7probe với output riêng `leader-w04-qa-confirm-20261111/probe-results.json`:4findings đúng,3control đạt, exit0 chỉ là probe hoàn tất. Backend candidate `bfd3272d` FAIL; không tích hợp. Chấp nhận báo cáo QA không phải chấp nhận Backend.

Backend cùng thread/tree nhận rework theo `PHONG-HOA-W04-BACKEND-REWORK-20261111.md`: request mới `eb4fafd2-1722-43ec-955e-83bc536d7848`, thread `12614171-9e62-4c0d-a75b-b7f852c15b02`, queued. Receipt cũ giữ trong history. F1 dữ liệu hỏng mở allowlist; F2 commit rồi lỗi response; F3 bound asset name; F4 audit lỗi bị báo duplicate. Frontend giữ nguyên nhiệm vụ đang chạy, chưa nối runtime candidate. QA không còn thao tác target. Hai lịch Phong Hỏa vẫn enabled, không tạo lịch/worker trùng.

## Cập nhật 11/11 — Backend trả candidate, QA song song Frontend

Backend `bfd3272d` đã reported, chưa accepted. Leader kiểm đúng ref/tree sạch/diff-check và3 response fixture+1error, exit0; `leader-w04-backend-intake-20261111.json` giữ SHA256/module path. Số197 suite/26targeted là evidence worker, không tự nhận Leader chạy lại.

CTI QA Security nhận `W04-ASSETS-BACKEND-QA` đọc đúng candidate, kiểm auth/transaction/snapshot/TLP theo `PHONG-HOA-W04-BACKEND-QA-BRIEF-20261111.md`; request `cd1d0878-6e79-43dc-80dd-15a94a670942`, thread `e430cea6-2476-477c-9548-d11aab8ebd10`, queued. Guard REVIEW của Backend đã có người xử lý này; không giao review trùng.

Frontend vẫn giữ request `659a5f35-1227-4205-a8dd-7cafc677f9bb`, thread `957c7dec-fe60-4717-acf1-8531e349e4aa`. Cập nhật đối chiếu bốn fixture Backend được injected vào lượt đang chạy, không tạo worker/request mới. Không phải đợi QA để làm parser/view, nhưng chưa nối runtime Backend chưa nghiệm thu. Research callback cũ đã accepted, không review lại.

## Cập nhật 11/11 21:15 — tăng tốc W04

Người dùng yêu cầu tăng tốc. Backend được quan sát đang chạy, giữ nguyên tree và receipt `9d5f3b39-1394-443d-a3d5-2b7d2ca0b20c`. Bỏ phụ thuộc chờ Backend không cần thiết đối với phần view/adapter/fixture: CTI Frontend nhận `W04-ASSETS-FRONTEND` trên tree riêng `cti-w04-assets-frontend`, cùng base W02 `aeff542a`, theo `PHONG-HOA-W04-FRONTEND-PARALLEL-BRIEF-20261111.md`. Request `659a5f35-1227-4205-a8dd-7cafc677f9bb`, thread `957c7dec-fe60-4717-acf1-8531e349e4aa`, outcome queued. Chưa suy receipt thành đang chạy.

Hợp đồng nghiên cứu/hiệu chỉnh đã đủ cho UI mẫu, HTTP adapter và parser W02 làm trước; Frontend không đọc/sửa tree Backend đang hoạt động. Chỉ phần tích hợp API runtime/browser phải chờ hai SHA đạt. Bổ sung này thay thứ tự làm tuần tự ở brief cũ, không đổi ranh giới ghi/kiểm Backend. Leader review phần mới/rủi ro, không lặp suite mốc cũ hoặc thêm người cùng tree. Giữ các lịch hiện có; dự án chưa hoàn tất.

## Cập nhật 11/11 — W04 chuyển nghiên cứu sang Backend

Leader chấp nhận nghiên cứu W04 kèm hiệu chỉnh bắt buộc trong `PHONG-HOA-W04-IMPLEMENT-BRIEF-20261111.md`: schema/client W02 chưa nhận asset-match ở allowlisted/not_found; SQLite cần partial unique index riêng; core dùng IDNA theo RFC3490; W04 bật tường minh qua asset_store, không đổi mặc định W02 trước bước client. Đã đối chiếu source/nguồn chính thức và chạy probe hợp đồng/DDL, chưa có runtime W04.

CTI Backend nhận `W04-ASSETS-IMPLEMENT`, một Sol medium/tree mới `cti-w04-assets-local`, base W02 `aeff542a`. Request `9d5f3b39-1394-443d-a3d5-2b7d2ca0b20c`, thread `12614171-9e62-4c0d-a75b-b7f852c15b02`, outcome queued. Sau nghiệm thu API/audit/fixture, Leader giao Frontend nối parser/view và màn W04 theo thiết kế hiện có; chưa giao song song khi hợp đồng còn đang triển khai. Giữ dự án active và các giới hạn lab/model/OpenCTI. Các mục dưới là lịch sử.

## Cập nhật 11/11 lúc nối việc sau nghiệm thu X01

X01 `4655d9ae` đã nghiệm thu cục bộ theo `leader-x01-recovery-acceptance-20261111/ACCEPTANCE.md`; R1 phục hồi 503 đóng. Đối chiếu khi các cuộc liên quan đều idle, Leader cập nhật RUNS từ receipt cũ thành accepted, giữ lịch sử và không chạy lại test. W02 `aeff542a` giữ accepted. Dự án vẫn active.

CTI Research nhận `W04-ASSETS-NEXT`, brief `PHONG-HOA-W04-NEXT-BRIEF-20261111.md`, chỉ nghiên cứu quản lý tài sản cục bộ và liên kết W02; chỉ ghi `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md`. Request `b40473ce-68a7-4932-9487-4a2f1415a116`, thread `42e76174-2c37-44f3-b6eb-849737a512dd`, outcome queued; chưa chứng minh đang chạy hoặc hoàn thành. Chưa giao triển khai W04. Lab/OpenCTI, model thật, pilot người gán nhãn, mobile viewport và clipboard vẫn chưa được nghiệm thu. Các mục dưới là lịch sử.

## Cập nhật 11/11 sau kiểm năm lượt browser X01

Áp dụng `PHONG-HOA-X01-BROWSER-REVIEW-20261111.md`. W02 docs `aeff542a` đã nghiệm thu, không giao lại. X01 `5fd527fc` có bằng chứng TXT/PDF, tự duyệt 403 và chống ghi lặp trong lỗi kéo dài; Leader kiểm 14 artifact, 28 test tươi và hai mutation payload đều bị chặn. Còn R1 tải lại thành công sau 503: Engineer nhận rework cùng thread/tree, chỉ hai browser run mới, giữ mã sản phẩm và evidence cũ. Chỉ Engineer dùng browser; không thêm người cho một cổng kiểm còn thiếu. Receipt mới ở RUNS và `leader-x01-browser-review-20261111/dispatch-receipt.json`. Các mục dưới là lịch sử.

## Cập nhật 11/11 sau nghiệm thu hậu kiểm và W02 HTTP

Ưu tiên hiện hành: `PHONG-HOA-INTEGRATION-ACCEPTANCE-NEXT-20261111.md`. Harness `16e6f889` đã được Leader nghiệm thu ngoại tuyến sau baseline và sáu mutation; W02 `50277102` đạt chức năng cục bộ/37 kiểm HTTP tươi, còn rework hướng dẫn tái chạy. Frontend chỉ sửa README/report ở tree W02; Engineer nhận X01-INGEST-BROWSER-INTEGRATION tại tree mới từ importer `fc08897a` và harness đã nghiệm thu. Chỉ Engineer dùng browser, không thêm người. Hai giao việc đã có receipt queued trong RUNS và `leader-integration-review-20261111/dispatch-receipts.json`; chưa coi queued là đang chạy hay hoàn thành. Các cập nhật dưới là lịch sử.

## Cập nhật 11/11 sau kết quả API và sửa harness

Ưu tiên hiện hành: `PHONG-HOA-API-ACCEPTANCE-NEXT-20261111.md`. API `78b02600` được Leader nghiệm thu cục bộ (178 tests tươi); HTTP adapter `88e9a9b6` đã đạt từ trước. Frontend nhận W02-LOCAL-INTEGRATION trên tree mới `cti-w02-local-integration`. Engineer sửa hai false PASS F3 semantic tại tree `cti-x01-ingest-browser-prep`; F1/F2 đã kiểm đạt, toàn harness chưa được chấp nhận. Hai phạm vi riêng, chỉ Frontend được mở browser demo; không thêm người. Receipt thật trong RUNS và `leader-api-harness-acceptance-20261111/dispatch-receipts.json`. Các cập nhật dưới là lịch sử.

## Cập nhật sau nghiệm thu hai bản sửa, 11/11 khoảng 18:10

Ưu tiên hiện hành: `PHONG-HOA-W02-API-ADAPTER-DISPATCH-20261111.md`. Backend triển khai W02 API từ W05 cf9e609; Frontend triển khai HTTP adapter ở tree riêng từ UI a949081; QA kiểm harness 970a130 chỉ đọc. Importer fc08897 và UI a949081 đã được Leader nghiệm thu theo `PHONG-HOA-PARALLEL-ACCEPTANCE-20261111.md`. Engineer nhận bước nối/sửa sau QA, không tạo worker trùng; browser chưa được nghiệm thu. Receipt thật trong RUNS và `PHONG-HOA-W02-API-ADAPTER-RECEIPTS-20261111.json`.

## Cập nhật thực thi 11/11 sau kiểm trạng thái

Áp dụng `PHONG-HOA-PARALLEL-EXECUTION-20261111.md`: Backend sửa F1 importer; Frontend nối lại R1/R2 bị cancelled trên tree có sửa dở; Engineer viết phần điều khiển demo trong tree riêng từ commit cố định, chỉ nghiệm thu browser sau importer đạt. W02 API đã có brief cùng bổ sung Leader, chờ Backend trả F1. Không tạo thêm người hoặc bản sao việc đang có. Receipt và trạng thái thực tế ghi tại RUNS.

## Phân công hiện hành 11/11 lúc 17:03

Theo yêu cầu mới tăng tốc nhưng tránh trùng việc, áp dụng `PHONG-HOA-PARALLEL-W02-PLAN-20261111.md` cho đợt hiện tại: Backend tiếp tục nhập envelope vào W05; Engineer giữ chuẩn bị demo cùng luồng; Frontend làm view tra cứu W02 ở tree riêng; Research chốt API tra cứu chỉ đọc bằng một brief ngắn. Receipt trong RUNS mới là bằng chứng đã giao. QA kiểm commit ổn định, không thêm writer vào tree đang chạy. Chưa cần thêm thành viên; không thay các request/thread đang hoạt động. Các bảng dưới là lịch sử.

Người dùng yêu cầu tăng tiến độ, máy ảo để sau, và chỉ định Codex làm giao diện thay Antigravity. Đã áp dụng cấu hình Backend, AI Agent, Frontend bằng Codex/Sol medium. Leader giữ định hướng/nghiệm thu/nối việc. Việc giao thực tế và request/thread chỉ lấy từ PHONG-HOA-RUNS.json, không suy diễn từ bảng này.

| Người phụ trách | Việc đầu tiên | Phạm vi riêng | Bước tiếp |
|---|---|---|---|
| CTI Engineer `a26c5706-a922-4648-8ede-7e04f7faec5d` | Sửa R1/R2 WORKFLOW-GUARD | workflow/*.py, tests/README/evidence, ngoài repo sản phẩm | Sau nghiệm thu: hạ tầng/cấu hình tích hợp offline có brief; chưa boot VM |
| CTI Backend `047f6b81-8c94-49e4-b3aa-d07cf8918448` | W05 quyết định cục bộ + audit | cti-w05-backend, branch feat/w05-local-review-20261110 | QA theo rủi ro, rồi API/auth qua nghiên cứu phù hợp |
| CTI Frontend `9d42e445-4b1a-4851-bf0a-bd4a8c87141c` | Portal W05 đọc bản nháp mẫu + evidence | cti-portal-web, branch feat/portal-w05-preview-20261110 | Kiểm trình duyệt, nối adapter API thật |
| CTI AI Agent `8ef51811-1fe3-4887-a60f-ae2b3ca51fbd` | Chọn adapter AI/agent offline + brief | Chỉ hai báo cáo AI ở workspace cha; repo đọc | Leader chọn rồi giao code trong tree AI riêng |
| CTI Research | Nghiên cứu W05 đã trả, hướng B được chấp nhận | Hai báo cáo W05 | Hỗ trợ khi xuất hiện câu hỏi mới, không giao lại nghiên cứu cũ |
| CTI QA Security | Chưa giao kiểm phần đang viết | Chỉ đọc đúng SHA, DB test riêng khi nhận brief | Migration/audit/policy, UI text safety và AI trust boundary |

Hai worktree sản phẩm cùng base e83bb3f; original cti-platform-start giữ sạch. Baseline mới tree backend: Python 3.12, pytest đầy đủ exit 0. Python dùng interpreter sẵn ở cti-platform-start/.venv nhưng pytest cwd/PYTHONPATH của tree backend, không pip cài sửa môi trường chung. Frontend cài dependency chỉ trong portal/web của tree riêng và dùng port 3002 nếu cần.

W05 không phụ thuộc mã guard điều phối; tách được owner/tree thì chạy đồng thời. Frontend dựa hợp đồng offline 1.0/fixtures đã có, chưa chạm metadata review mới; adapter integration là việc tiếp sau khi backend được nghiệm thu. AI nghiên cứu chưa sửa file dùng chung. Mỗi người được brief rõ file và output; không giao tiếp bot khác hoặc sửa RUNS.

Sửa docs/PROGRESS.md trong từng branch được phép; Leader đối chiếu khi tích hợp để không ghi đè trạng thái của nhau. Chưa push/PR/merge/deploy và chưa tuyên bố các branch đã tích hợp. Dữ liệu mẫu/adapter giả lập phải được ghi rõ, không chứng minh production/auth/LLM/OpenCTI/lab.

Lịch dự phòng `79621896-f322-47a8-80d7-072739a2314b` đã được cập nhật theo các owner mới, giữ chu kỳ 30 phút. Callback đồng đội vẫn nối ngay. Lần chạy thử manual 23:27 có trạng thái completed và output NOTHING NEW; chưa đủ bằng chứng đã phục hồi một việc bỏ dở, không tính là nghiệm thu toàn cơ chế.

## Nối việc ngày 11/11/2026

Guard và lõi W05 đã nghiệm thu đúng phạm vi cục bộ; AI-NEXT đã được chọn. Sổ tổng là nguồn trạng thái mới: CTI AI Agent nhận AI-IMPLEMENT trên tree mới từ e83bb3f; CTI Frontend nhận rework clipboard trên tree hiện có; CTI Research nhận W05-API-NEXT dựa trên backend f87b7f và frontend be364bd. Ba nhiệm vụ đã có receipt queued, chưa gọi là running. Backend/Engineer không nhận việc trùng. Chi tiết: PHONG-HOA-LEADER-ACCEPTANCE-20261111.md. UI 360/1440, model thật, HTTP/auth/OpenCTI/lab vẫn chưa nghiệm thu.
