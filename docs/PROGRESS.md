# Tiến độ (agent cập nhật sau mỗi task)

Cập nhật lần cuối: 27/11/2026

## 27/11/2026 — B28: F21 báo cáo lỗ hổng tuần + gửi có duyệt (MVP, spec chờ duyệt)

- Đã làm: [spec F21](specs/F21-bao-cao-va-gui.md) (F18 dòng 10–12); `portal_api` có báo cáo HTML tiếng Việt từ
  read model W03 (CVE khớp tài sản, KEV, phân bố CVSS, nguồn, TLP), mẫu thư tĩnh escape biến, danh sách nhận
  email/Telegram, outbox preview → duyệt (người khác người tạo, khớp `content_hash`) → gửi một lần, audit, SMTP
  chỉ từ env. 16 test offline mới với sender giả; viết mới hoàn toàn, không dùng mã EE.
- Còn lại: giao diện portal, sender Telegram, PDF phía server (hiện in từ trình duyệt), khôi phục lô kẹt
  `sending`, hủy nhận/xác minh địa chỉ, chạy SMTP thật trên lab.
- Vướng mắc: chưa chốt thư viện PDF/license, chính sách hai người duyệt khi gửi ra ngoài, mô hình đa tenant.

## 27/11/2026 — B27: F20 AI tóm tắt + NLQ (MVP ngoại tuyến, spec chờ duyệt)

- [F20](specs/F20-ai-tom-tat-hoi-dap.md): lát cắt F18 #7 và #9; #8 dùng lại extractor X01. Code mới trong
  `extractor/phonghoa_extractor/` (`ai_provider.py`, `ai_insights.py`, `nlq.py`) + 34 test ngoại tuyến.
- Tóm tắt tiếng Việt mỗi claim trích STIX id; NLQ ra bộ lọc whitelist kiểm schema chặt, không SQL/GraphQL tự do.
  Mặc định template/luật offline; LLM cục bộ tùy chọn qua env, chặn TLP:AMBER/RED với provider không cục bộ.
- Còn lại: nối portal API/MCP, marking TLP 2.0, đánh giá model thật. Chưa chạy model/OpenCTI thật.

## 27/11/2026 — B26: F19 playbook MVP ngoại tuyến

- Nhánh `feat/b26-playbook` từ B25; `connectors/playbook/` có nguồn SSE fixture/HTTPS lọc, cấu hình YAML giới hạn cú pháp (không cần dependency mới), hai luật mẫu, dry-run mặc định, SQLite cursor/receipt/version/audit/outbox/pending-label theo scope.
- Dùng CveReadService W03 và W04 read-only để đối chiếu KEV theo sản phẩm, không tự suy phiên bản bị ảnh hưởng. Chỉ CLEAR/GREEN sinh intent; không có LLM, gửi tin, ghi trực tiếp OpenCTI, chặn/xóa hay thực thi đề xuất.
- Projection outbox đọc nội bộ và hàng nháp label riêng chưa nối portal/MCP/Hermes/W05. Fixture giả lập và mock HTTP kiểm schema/score/TLP, replay/xung đột, rollback, scope và 100 event.
- Chưa kiểm runtime CE/tag/permission/marking thực, reconnect/backoff, retention/reconciliation và stale toàn luồng, review/expiry/publish, RBAC API hay notifier. Chỉ nghiệm thu ngoại tuyến; không bật live hoặc cấp DB cho khách.

## 27/11/2026 — B25: F18/F19 (spec chờ duyệt)

- F18: [ma trận 15 tính năng EE](specs/F18-thay-the-tinh-nang-tra-phi.md), thay thế độc lập ngoài OpenCTI CE; P1 7 mục / 116 giờ, tổng 232 giờ ước lượng, chưa triển khai.
- F19: [spec playbook YAML + live stream](specs/F19-playbook-tu-dong.md), fixture-first, cảnh báo portal/Hermes, đề xuất W05, dry-run, audit, không ghi lõi khi chưa được người duyệt, không xóa/chặn tự động. Liên kết F17 (B23) và W03/W04.
- [ADR 0018](adr/0018-khong-dung-ma-enterprise-opencti.md) đề xuất không dùng/đọc mã EE, không bật EE trong bản bán; test dò chuỗi header EE chỉ là cổng phòng ngừa, không thay rà license/SBOM.
- Docs công khai ghi SSO qua config và UI đều EE từ 7.260224.0; portal xác thực riêng, CE local auth. Live stream lọc được tài liệu hóa như chức năng thường, cần smoke test trên CE ghim.
- Nền thực tế origin/main `4d1aeea` (PR #48), khác nền đích PR #56 / 7.261124.0 trong brief. Chưa đồng bộ runtime, chưa xác minh CE stream thật, chưa làm F19/model/feed thật; chủ chốt ưu tiên, tenant, quyền gửi và pháp lý trước code.

Cập nhật lần cuối: 26/11/2026

## 26/11/2026 — B24R1: NVD độc lập, KEV dự phòng chính thức

- Sửa nguyên nhân B24: trước đây lỗi tải KEV phát sinh trước vòng phân trang NVD, khiến toàn bộ import hủy dù NVD có thể trả kết quả. B24R1 dùng User-Agent nhận diện repo và Accept JSON, thử CISA trực tiếp, rồi URL cố định CISAGov/kev-data nhánh main theo brief; nếu không thành công thử default branch develop của cùng repo (đã kiểm metadata GitHub). Không mở rộng tùy ý URL, không theo redirect, giữ TLS, không gửi NVD key sang KEV/mirror.
- Nếu cả các nguồn KEV lỗi, cảnh báo và vẫn nhập NVD; snapshot imported có kev_snapshot_complete=false, trạng thái KEV và as_of của từng CVE là null (chưa xác minh), không phải false. Wire source.kev_catalog là cisa/github/unavailable; giữ contract synthetic cũ. UI ghi rõ nguồn, tự bỏ lọc Chỉ KEV khi unavailable, không hiển thị 0 như kết luận KEV. NVD có ngân sách fetch riêng 420 giây, page size 1.000 và cap 48 MiB/page; giữ pace 6,1 giây. NVD lỗi/phân trang không nhất quán vẫn không ghi snapshot dở.
- Live Windows: CISA HTTP 403; mirror URL main trả dữ liệu hợp lệ. Nạp thành công 1.805 KEV + 3.987 NVD (cửa sổ công bố 7 ngày), 9 trùng giữa nguồn, tổng 5.783 CVE riêng biệt; 3.925 chưa có cặp tên sản phẩm, không tạo match. CLI 21,0 giây; snapshot 5.136.578 byte, thu nhận 2026-11-26T15:23:56Z; không commit file data/cve-feed.json (đã gitignore).
- Kiểm stack loopback với snapshot thật: /lo-hong HTTP 200, /api/cves?kev=true&limit=10 HTTP 200, kind imported, kev_catalog github; 9 CVE khớp tài sản demo. Chromium headless dump DOM xác nhận nhãn CISA KEV (GitHub) + NVD và cả 9 mã trong bảng. Ví dụ thấy trên trang: CVE-2018-13379 (KEV 2021-11-03), CVE-2019-5591 (2021-11-03), CVE-2019-6693 (2025-06-25). Tài sản/role vẫn giả lập; chưa kiểm OpenCTI, dữ liệu doanh nghiệp hoặc production.
- Test offline thêm nhánh KEV mất/NVD vẫn nạp, mirror provenance và UI tự bỏ lọc khi KEV mất; không gọi mạng trong test. Kết quả live này thay cho blocker ở mục B24 lịch sử bên dưới.

## 26/11/2026 — B24: Nguồn CVE thật trực tiếp, không cần OpenCTI

- Nhánh riêng: feat/b24-real-cve-feed. CLI nạp toàn bộ catalog CISA KEV và NVD API 2.0 theo ngày công bố (7–30 ngày), phân trang, giới hạn kích thước/thời gian, pace NVD 6,1 giây giữa các request, retry có backoff, TLS và không redirect. Key NVD tùy chọn từ biến môi trường, không ghi log.
- Kho snapshot JSON chuẩn hóa độc lập, mặc định data/cve-feed.json (data/ đã gitignore). Một dòng logic mỗi CVE ID; ghi nguồn/URL, thời gian bắt đầu lượt thu nhận UTC, ghi công/notice và ngày KEV thêm. Chỉ thay file atomically khi cả hai nguồn hợp lệ; không đánh dấu KEV false nếu thiếu catalog. Snapshot được thay theo cửa sổ ngày, không phải lịch sử tích lũy.
- W03 giữ fixture và giới hạn cũ mặc định; mode imported có giới hạn riêng (20.000 bản ghi, 512 cặp sản phẩm/bản ghi, 64 MiB). Response/cursor/quyền và cap wire 1 MiB giữ nguyên; metadata nguồn kind=imported trên /lo-hong. Không đổi /lo-hong/mau. Ghép exact casefold vendor + product; CPE NVD chỉ lấy vulnerable=true và tên, đổi dấu gạch dưới thành khoảng trắng; không có mapping alias, suy luận AND/OR hoặc kiểm phiên bản. NVD chưa enrich CPE vẫn lưu nhưng không tạo match; EPSS không thu thập, CVSS 3.1/4.0 nếu có. Thiếu điểm hiển thị thiếu, không suy đoán.
- Chạy từ root (PowerShell): đặt $env:PYTHONPATH='core;extractor;.'; dùng .venv/Scripts/python.exe -m portal_api.feeds.import_cves --kev --nvd-days 7. NVD_API_KEY không bắt buộc. Build portal/web, chạy .venv/Scripts/python.exe -m tools.local_integration.runner --scenario w03-it --cve-feed data/cve-feed.json rồi mở URL loopback + /lo-hong. Tài sản/role của harness vẫn tổng hợp. Chế độ API cấu hình W03_CVE_PROVIDER=imported và W03_CVE_FEED_PATH; mặc định synthetic (fixture vẫn opt-in bằng injection, không có fallback âm thầm).
- Kiểm offline: fixture dạng nguồn thật, test phân trang/dedup, nguồn/metadata, lỗi giữa lượt, redirect/domain/key/size, cấu hình; stack loopback HTTP 200 /lo-hong và /api/cves với một CVE fixture khớp. Không gọi mạng trong test.
- **Chưa nghiệm thu LIVE:** lượt nạp trên Windows trả HTTP 403 từ www.cisa.gov (exit 1, không tạo snapshot). NVD kiểm riêng trả HTTP 200, totalResults=4254 cho 7 ngày, 1 bản ghi trả về trong trang kiểm kết nối; KHÔNG phải số nhập. 0 bản ghi thật được nạp; chưa có 3 ví dụ KEV thật hoặc portal CVE thật. Không dùng mirror ngoài danh sách host hoặc bỏ TLS; chờ nguồn CISA truy cập hợp lệ rồi chạy lại CLI và demo lựa chọn 6. Không kết luận doanh nghiệp đã bị tấn công từ CVE trùng tên.

## 26/11/2026 — B13: W01 Tổng quan và W04 xuất CSV

- Thêm `/tong-quan` và `/tong-quan/mau`, nối từ Hàng chờ duyệt; giao diện SOC VI/EN, bốn KPI, ứng viên cần chú ý, CVE ưu tiên, IOC khớp tài sản và tình trạng nguồn. Chỉ đọc GET `/api/cves` theo quyền hiện hành; trang mẫu dùng provider CVE và fixture IOC W04 có sẵn, loại IOC allowlist. Không dùng fixture thay API khi lỗi.
- W01 chưa đủ tiêu chí toàn phần: chưa có API tổng quan/nguồn thống kê IOC theo thời gian, cảnh báo Wazuh, top ATT&CK/mã độc hoặc trạng thái xử lý tổng hợp; hiển thị chưa có nguồn/chưa xác định thay vì số 0, không tự suy ra mức đe dọa hay tạo cảnh báo thật. CVE chỉ khớp tên sản phẩm, chưa đánh giá phiên bản. Không có hành động ghi, không thay API hoặc quyền.
- W04 thêm nút CSV gộp tên miền, dải IP, công nghệ từ ba phép đọc hiện hành; không tải nếu thiếu một nhóm do lỗi. UTF-8 BOM, CRLF, escape dấu nháy kép và tiền tố apostrophe cho ô nguy hiểm (= + - @, kể cả khoảng trắng đầu). Không thêm dependency, không ghi DB, không xuất trường định danh người tạo.
- Cổng cục bộ: Ruff check/format đạt; pytest 1.484 pass, 3 skip sẵn có; Vitest 427/427 pass (14 test mới, 7 wire test cũ được kích hoạt bằng 12 fixture capture), typecheck/lint/build đều đạt. Browser headless qua gateway + API/SQLite giả lập: W01 desktop 1440 và mobile 360 không tràn, mẫu không gọi API; CSV mẫu 3 dòng và CSV API 2 dòng đúng dữ liệu fixture/BOM, chỉ GET, bộ đếm DB/audit không đổi.
- Chờ nghiệm thu độc lập. Chưa có nguồn OpenCTI/Wazuh/feed thật, chưa đo cache <2 giây hoặc kiểm lab/production; còn thiếu các tiêu chí W01 phụ thuộc nguồn nêu trên.


## 26/11/2026 — B14 Connector nguồn tiếng Việt thứ hai (nhánh riêng)

- Thêm VSEC: đọc một trang danh mục HTML, trích tiêu đề/mô tả IOC/CVE qua core; xuất STIX 2.1 dạng ứng viên chưa duyệt, TLP:GREEN. Live mặc định tắt, không có publish trực tiếp.
- Tách kiểu dữ liệu, tải HTTP/robots/cache và bộ dựng STIX dùng chung với MST, giữ profile/ID MST. Kiểm thử fixture/mock và validator STIX; không dùng feed thật trong test.
- Kiểm tra nguồn: robots HTTP 200 rỗng; hai RSS ứng viên HTTP 520; danh mục HTML HTTP 200. [CẦN KIỂM] quyền thu thập/tái sử dụng, quota, độ ổn định layout; chưa chạy CLI live hoặc OpenCTI lab, chưa đo RAM hay chất lượng trích thật.

## 25/11/2026 — Gộp toàn bộ nhánh vào `main` (PR #47)

- Đã gộp đầy đủ nhánh Portal (`3e69340`), AI X01 (`8a16758`), Ingest Queue (`4655d9a`) và hồ sơ bàn giao 12/11 (`9d87622`) về nhánh `main` (`2e74d8d`).
- Đã sửa lỗi tranh chấp đồng thời trong `_validate_v3_schema` (`store.py`), tương thích Linux CI (`gold_pilot.py`, `stix_export.py`, `test_local_ingest.py`) và thêm `.gitleaksignore` cho 9 cảnh báo giả đã xác minh.
- CI GitHub Actions (`python` và `secrets`) đã xanh; kiểm thử cục bộ trên Windows đạt 1,484 pytest passed (3 skipped), 406 Vitest passed (7 skipped), `tsc`/`eslint`/`next build` và `tools/local_integration` đạt.
- Đã cập nhật lại `README.md`, `docs/HANDOFF.md` và `docs/PROGRESS.md` cho khớp trạng thái trên `main`.

## 12/11/2026 11:10 — Người dùng yêu cầu tạm dừng

- Đã tạm dừng hai lịch tiếp tục và ghi user_paused; Frontend đã dừng, chưa có thay đổi W03-S2. Không phát triển thêm.
- [Bàn giao bổ sung](reports/2026-11-12-stop/README.md) ghi delta sau 09:07: W03-S1 docs `4a8f409`, Backend W03-S2 `3e693403`, 13 hồ sơ phát sinh và các việc chưa hoàn tất. Nhánh Frontend hiện chỉ trỏ tới cùng nền Backend.
- W03-S2 Backend có nghiệm thu API cục bộ; Frontend/gateway/browser chưa triển khai/tích hợp. W03-S1 còn vướng cleanup dịch vụ thử cũ theo hồ sơ.

## 12/11/2026 — Chốt kết quả để công bố GitHub

- [Báo cáo quá trình và kết quả hiện tại](reports/2026-11-12/README.md) ghi 52 nhánh kết quả, 133 commit sau nền PR #46, 89 đầu việc và 413 tài liệu nguồn. Có bảng SHA, phạm vi nghiệm thu, vòng sửa lỗi và phần chưa xác minh.
- Nền portal hiện tại là `f5d2315e94b7f83e44360a04b67902cb5b0ba4bd`; các nhánh AI/ingest khác được lưu độc lập, chưa tự coi là đã ghép toàn bộ vào portal.
- W03-R đã nghiệm thu cục bộ. W03-S1 có bằng chứng A/B và delta product256 đã kiểm nhưng toàn task còn chờ đóng báo cáo/cleanup; W03-S2 mới giao nghiên cứu. Các mô tả ở dưới thuộc thời điểm riêng, đọc báo cáo tổng hợp để biết trạng thái mới nhất.
- Lần này chỉ công bố kết quả theo yêu cầu người dùng; chưa merge, deploy, chạy lab, gọi LLM/feed thật hoặc nâng mức nghiệm thu sản phẩm.

## 12/11/2026 — W03-S2 Backend read model trạng thái

- Thêm route opt-in `GET /api/cves/status-view`: detail ghép status theo relation, Leader nhận projection lược;
  filter status trước paging, bộ đếm actionable/quá hạn theo ngày UTC và cursor riêng phát hiện drift.
- R1 siết cursor trước dependency: từ chối type sai, số JSON không hữu hạn, ngày lịch không tồn tại và Unicode
  surrogate bằng 422; test tách riêng drift dataset/Technology/status/ngày UTC để mỗi 409 có nguyên nhân độc lập.
- Technology và status được đọc trong một transaction/một connection SQLite chỉ đọc; GET không migrate/audit/ghi.
  Fixture detail/Leader/error và test writer thật giữa hai phép đọc dùng dữ liệu/JWT/DB tổng hợp cục bộ.
- Giữ nguyên W03-R/W03-S1/technology/auth. Chưa kiểm gateway/frontend/browser, feed/OpenCTI, Cloudflare/JWKS/HTTPS,
  lab hay production; status người dùng ghi nhận không chứng minh đã vá.

## 12/11/2026 — W03-S1 Frontend trạng thái theo quan hệ

- Đã thêm provider/parser HTTP riêng và panel trạng thái/note/history trong chi tiết một CVE/công nghệ; trang tóm tắt không gọi status API, trang mẫu chỉ lưu trong memory.
- Đã khóa double-submit, stale callback, 409 re-entry, phân trang history và pending/unknown recovery bằng GET-only; không tự replay PUT.
- Ở mốc frontend ban đầu chỉ kiểm component/provider cục bộ; browser Backend thật/gateway được bổ sung ở chặng A/B
  bên dưới, còn lab và production vẫn chưa kiểm.
- W03 product boundary Backend: affected product trong dataset/read được nâng riêng từ 128 lên 256 Unicode code
  point để khớp W04; vendor vẫn 128 và trim/control/policy không đổi. Test API cục bộ kiểm 128/129/256,
  257 fail-closed, astral, vendor/control và chuỗi GET/PUT/history product256 có đúng một audit. Candidate tích hợp
  `867bdca` đã kiểm HTTP capture thật và parser production với product256 astral; product257/vendor129 fail-closed,
  fixture LF đạt trên checkout Git mới có `core.autocrlf=true`. Browser A/B dùng lại bằng chứng đã nghiệm thu trước;
feed/OpenCTI/lab/production vẫn chưa được kiểm.

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
- W03-S2 Frontend (B12): đã triển khai trên nhánh `feat/b12-w03-s2-frontend` từ `origin/main`; chờ nghiệm thu độc lập và ghép. `/lo-hong` dùng GET `/api/cves/status-view`, `/lo-hong/mau` dùng fixture và trạng thái trong memory. Lọc trạng thái chỉ cho detail; bộ đếm CVE cần xử lý/KEV quá hạn theo phạm vi lọc cơ sở và ngày UTC, không phải số dòng trang hiện tại. Gateway chỉ mở đúng GET; adapter giữ kiểm schema detail/summary, giới hạn 1 MiB và xử lý lỗi/cursor. Giao diện danh sách VI/EN; nút Làm mới đọc lại snapshot sau khi cập nhật S1. Cổng cục bộ: Python 1484 pass/3 skip có sẵn, gateway 19/19, Vitest 432/432 (2 worker, đủ fixture wire), Ruff/typecheck/lint/build đạt. Chưa kiểm browser/viewport, nguồn CVE thật, OpenCTI, Cloudflare hoặc production.
- Việc 2: cài OpenCTI trên máy Ubuntu và đo RAM thực tế.
- F01/#9: gói demo MITRE + bundle STIX mẫu đã kiểm cấu hình ngoại tuyến; chờ chạy và đo trên lab.

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
  đọc với Unicode, note 1000, actor 512, vendor/version 128, history 100+cursor. Delta `867bdca` bổ sung product256
  astral qua HTTP capture và parser production, đồng thời giữ product257/vendor129 fail-closed. Browser
  desktop 1280×720 đã chứng minh known-commit PUT200, GET `503→503→200`, lỗi tạm thời vẫn giữ notice đã lưu và
  đóng/mở chi tiết trong cùng trang phục hồi với đúng một status/audit. Unknown-outcome reentry cùng trang còn
  PENDING; mobile, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab và production chưa kiểm.
- W03-S1 chặng B rework thêm scenario helper riêng cho unknown-outcome sau commit với đúng hai GET status lỗi trên
  exact relation trước khi phục hồi; regression focused chứng minh `PUT503 → GET503 → GET503 → GET200`, đúng một
  PUT, một status và một audit. Đây là fault tổng hợp có điều khiển phục vụ browser evidence, không đổi UI/Backend,
  hợp đồng product128/256 hoặc phạm vi lab/production.
- X01 adapter C2/C3 ngoại tuyến: provider giả lập chỉ `fake_offline`/không egress, kiểm schema/TLP/metadata,
  retry một lần rồi fallback C1; C2 chỉ đánh giá, C3 dùng grounding/evidence hiện có. Đây là mock tổng hợp,
  chưa gọi hoặc đo model thật và không ghi SQLite/W05.
- X01 evaluator C2/C3 ngoại tuyến: chạy 6 fixture tổng hợp qua adapter; C2 chấm raw prediction, C3 chấm IOC
  sau grounding và giữ audit, metric tách `model_completed`/`regex_fallback`. C1 giữ nguyên; đây không phải
  benchmark model/corpus thật và không nối W05.
- X01 restricted ATT&CK catalog ngoại tuyến: loader stdlib đọc fixture STIX tổng hợp đã ghim hash, kiểm
  version/lifecycle/parent graph và tra active/inactive/unknown/invalid bằng kết quả bất biến. Semantic luôn
  `unverified`; rework R1/R2 đã phân biệt boolean với number trong exact JSON duplicate và chuyển đường dẫn
  NUL thành lỗi I/O an toàn.
- X01 ATT&CK official v20.1 ngoại tuyến: public `load_catalog` nhận đúng một bộ pin đã review và đọc nguyên
  snapshot local 55.277.605 byte thành 867 record (706 active, 161 inactive; 497 sub-technique), không cần
  provenance Phong Hỏa trong root MITRE. Synthetic giữ nguyên; asset không nằm trong repo và lookup vẫn
  `unverified`/không đủ điều kiện ghi draft. Đây là compatibility loader, không phải xác minh ngữ nghĩa TTP.
- X01 audit technique ngoại tuyến: public API bind SHA-256 UTF-8 của nguyên văn kết quả C2/C3 giả lập, kiểm
  quote literal/offset Unicode và trạng thái ID trên catalog đã nạp; output bất biến, luôn `unverified` và
  không đủ điều kiện ghi draft. Test module mới và regression adapter/catalog/grounding/evaluate/eval CLI
  đã đạt cục bộ; số đếm/lệnh/exit được lưu ở bằng chứng bàn giao của lát cắt này.
- X01 evaluator audit technique ngoại tuyến: C2/C3 có opt-in schema 1.1 để xuất từng quote/span và provenance
  catalog ATT&CK đã pin; mặc định schema 1.0, prediction/score IOC và retry/fallback giữ nguyên. Pin được đọc
  UTF-8 strict có bound 16 KiB, catalog chỉ nạp một lần và output atomic không được alias dataset/fixture/
  snapshot/pin. Đây vẫn là smoke bằng provider giả lập, không phải đánh giá ngữ nghĩa TTP hoặc chất lượng model.
- X01 reporter ngoại tuyến: CLI stdlib đọc cohort C1/C2/C3 schema 1.0 hoặc C2/C3 schema 1.1, kiểm projection,
  aggregate/mode/TTP consistency rồi dựng Markdown bất biến có hash từng input và nhãn synthetic. Publish mặc
  định no-clobber, chỉ overwrite khi có cờ và từ chối alias input; reporter không chấm lại prediction hoặc gọi
  model/mạng/catalog/DB. Đây là bảng smoke tổng hợp, không phải kết quả model/corpus thật.
- X01 component retrieval ATT&CK ngoại tuyến: canonical loader giữ optional description; lexical retriever trả
  raw result bất biến và JSON context có provenance, đo toàn envelope theo budget UTF-8. Ranking/tokenizer được
  kiểm bằng fixture tổng hợp Việt/Anh qua public loader và regression dùng asset Enterprise v20.1 local; chưa nối
  generator/model, chưa phải full C4/RAG hoặc bằng chứng chất lượng semantic.
- X01 adapter C4 context ngoại tuyến: wrapper kiểm báo cáo/TLP, gọi retriever lexical đúng một lần rồi gửi nguyên
  context có hash/provenance trong request bất biến cho provider giả lập; retry/fallback dùng lại C3 và public audit
  chỉ lấy evidence từ báo cáo gốc. Đây là kiểm hợp đồng bằng dữ liệu tổng hợp, chưa phải chất lượng model/RAG.
- X01 evaluator/reporter C4 ngoại tuyến: query manifest explicit, preflight toàn dataset trước generate, artifact
  schema 1.2 no-clobber và reporter nhận C4 đơn hoặc C3-audit+C4 cùng provenance. Demo vẫn dùng response
  fake_offline tổng hợp; không phải benchmark model/RAG/TTP semantic hoặc corpus thật.
- X01 gold-pilot readiness ngoại tuyến: validator/CLI kiểm inventory 5 record, quyền raw khai báo, hai annotation,
  evidence IOC token và TTP active từ catalog đã ghim; report bất biến/no-clobber và agreement chỉ phản ánh nhãn
  tổng hợp. Rework R1–R5 đã đóng lỗi kiểu JSON gây traceback, URL/userinfo/control, reparse ancestor, enumeration
  vượt cap, lỗi I/O fingerprint và manifest evidence hai chiều. Đây không phải corpus gold, quyền thật, hai người
  thật hay bằng chứng chất lượng model/RAG.
- X01 local ingest ngoại tuyến: CLI mới nhận UTF-8 TXT hoặc PDF lớp text từ file regular local, bind raw hash với
  snapshot bytes cho child `pypdf` đã pin/hash, kiểm strict/capped result rồi bọc draft C1 pending không đổi shape.
  Output deterministic/no-clobber bằng hard-link; test synthetic có race/alias/timeout/reap/cleanup. Đây không phải
  hard RAM/network sandbox, kiểm PDF đối kháng/thật, OCR hoặc bằng chứng chất lượng extractor/model.
  Rework R1–R3 đã đóng kiểu `code` list/dict trong result, tiếp tục kill/reap khi wait/terminate lỗi, giữ temp owned
  nếu chưa xác nhận child dừng và từ chối symlink/reparse ở mọi ancestor lexical trước khi đọc leaf.
- X01 ingest queue: CLI local/offline kiểm envelope TXT/PDF đã có, migrate SQLite v2→v3 và ghi draft pending cùng
  provenance nguyên tử; retry cùng creator không nhân bản, creator khác conflict, payload/selection/review/STIX cũ
  giữ nguyên. Tên nguồn chặn toàn bộ ký tự điều khiển Unicode `Cc` ở library/CLI trước khi mở database, nhưng vẫn
  nhận tên tiếng Việt, khoảng trắng và emoji. Đây chỉ là importer/core synthetic; chưa kiểm browser, identity HTTP
  thật, OpenCTI, lab hoặc production.
- X01 ingest → browser → STIX cục bộ: TXT hai IOC và PDF một IOC synthetic đi qua producer/importer, W05 UI
  same-origin và exporter trên cùng SQLite; retry importer không nhân bản, tự duyệt bị 403, hai lỗi GET refresh
  sau save/approve không ghi lặp. Hai ca lỗi tạm thời mới còn chứng minh cùng run phục hồi GET 503 → 200:
  lựa chọn đã lưu vẫn chỉ còn IOC thứ hai và quyết định đã duyệt biến khỏi hàng pending; request trace chỉ ghi
  method/path/status, không header/query/body. Verifier đối chiếu source/envelope/provenance, actor,
  selection/final audit, hash bundle, export read-only và cleanup owned resource. Đây chưa kiểm
  Cloudflare/JWKS/HTTPS thật, OpenCTI, dữ liệu báo cáo thật, lab hoặc production.

## Vướng mắc
- Bộ version mới chỉ được kiểm cấu hình; chưa pull image, boot service hoặc chứng minh tương thích/runtime trên lab
- Capability upload/review/approve, work ID, trạng thái draft trước/sau và quyền thực tế chưa kiểm trên lab
- Chưa gọi feed hoặc LLM, chưa có key/điều khoản OTX, chưa đo RAM/queue và chưa xác minh demo MITRE + OTX (#10)
- X01 còn thiếu dataset báo cáo thật được hai người gán nhãn, run model thật và C4/TTP; smoke C1/C2/C3 tổng
  hợp không chứng minh chất lượng extractor hoặc model
- Adapter mới chỉ chứng minh hợp đồng C2/C3 bằng response giả lập; chưa chọn provider/model, chưa có run model
  thật, token/chi phí/độ trễ, corpus hai người gán nhãn hoặc đánh giá TTP/C4
- ATT&CK official mới chỉ kiểm đúng Enterprise v20.1 local; release khác, chữ ký tag/commit, NOTICE riêng,
  C4/RAG, semantics TTP, OpenCTI/lab/production vẫn chưa xác minh
- Audit technique chỉ chứng minh source/quote/catalog consistency trên provider giả lập; semantic truth,
  model/provider thật, corpus/gold/F1 và C4/RAG vẫn chưa xác minh.
- Artifact evaluator schema 1.1 mới chỉ được kiểm ngoại tuyến với snapshot synthetic; semantic truth TTP,
  corpus hai người gán nhãn, model/provider thật, C4/RAG, lab và production vẫn chưa xác minh.
- Reporter chưa được dùng với corpus thật hoặc artifact model thật; semantic TTP, C4/RAG, khả năng chống power
  loss/hostile directory mutation, W05, OpenCTI, lab và production vẫn chưa xác minh.
- Retrieval lexical chưa được nối trước generation, chưa đo semantic/multilingual recall trên corpus hai người
  gán nhãn và chưa gọi model thật; ranking score chỉ là token overlap, không phải confidence hay semantic truth.
- C4 mới chỉ nối request với provider giả lập và query do caller truyền; chưa đo chống prompt injection, model thật,
  semantic/multilingual TTP, corpus hai người gán nhãn, OpenCTI, lab hoặc production. Evaluator/reporter chỉ kiểm
  contract deterministic trên fixture tổng hợp, không nâng mức bằng chứng chất lượng.
- Gold-pilot mới chỉ kiểm cơ chế bằng fixture tổng hợp; quyền raw thật, độc lập hai annotator, adjudication,
  semantic TTP, corpus gold/model quality, hostile mutation, crash/power-loss và production chưa xác minh.
- Local ingest chưa kiểm hostile filesystem mutation, hard RAM/network isolation trên Windows, PDF đối kháng/thật,
  OCR, chất lượng text đa ngôn ngữ, corpus/model, lab hoặc production.

## B10 — Hermes MCP server chỉ đọc (26/11/2026)
- Đã triển khai `mcp-server/` với FastMCP chính thức, transport stdio, 8 công cụ đọc IOC/CVE/bản nháp/báo cáo/tổng quan/sự kiện. Tái dùng logic chuẩn hóa và tính điểm của portal/core; mặc định fixture tổng hợp, không gọi mạng trong test.
- Adapter OpenCTI qua pycti bật bằng env, chỉ list; portal GET tùy chọn để đọc tài sản/CVE và hàng chờ W05. Dữ liệu ngoài được bao trong `tai_lieu`, escape ký tự phân tách; lọc TLP:CLEAR/GREEN; không có tool ghi, duyệt, chặn, chạy lệnh hoặc xóa.
- Còn lại/vướng: chưa kết nối lab/OpenCTI thật, chưa nghiệm thu role agent portal, chưa có stream sự kiện live, chưa tích hợp Hermes/Telegram/cron. Lock MCP tách riêng; CI cần nạp lock ở việc được phép sửa workflow. Lock tạo trên Windows; Ubuntu và tương thích phiên bản OpenCTI chưa kiểm. Fixture/test chỉ chứng minh hợp đồng và ranh giới đọc cục bộ, không chứng minh chất lượng CTI hoặc chống prompt injection của model thật.

## B11 — Bot Telegram Hermes (26/11/2026)
- Đã thêm bot polling python-telegram-bot trong mcp-server/hermes_bot: allowlist chat và user từ env, reviewer riêng; /ioc, /cve, /nhap, /tomtat gọi tool đọc MCP B10 qua stdio, chỉ fixture tổng hợp. Không có LLM hoặc tool ghi thực tế.
- /dexuat chan và /dexuat nhap lưu đề xuất pending trong SQLite; callback Duyệt/Từ chối ghi quyết định và người duyệt đúng chat, chuyển trạng thái nguyên tử đúng một lần, không thực thi. Nội dung nguồn là dữ liệu, có kiểm bao/TLP, defang và giới hạn phản hồi. Thêm test Update Telegram giả lập, SQLite tạm và round-trip MCP fixture; lock dependency dùng chung CI B10.
- Còn lại: nghiệm thu polling Telegram thật, kiểm thành viên chat/quyền chia sẻ, gateway Hermes upstream, MCP live cách ly token, W05, cron 07:00 và trực ca, dữ liệu/model thật. B11 không thực hiện hoặc chứng minh các chức năng này; không thay đổi portal.

## B03 — Connector MST tiếng Việt (26/11/2026)
- Đã làm: lấy RSS qua fetch có robots/timeout/rate limit/retry/cache, parse fixture và dùng core trích IOC/CVE,
  xuất Report + observable/Vulnerability STIX 2.1 (TLP:CLEAR tương thích WHITE), ID ổn định và URL nguồn.
- Chạy ngoại tuyến ra file; pycti chỉ khi live và người vận hành bật publish, đọc secret từ biến môi trường.
- Còn lại/vướng: RSS thật, robots/điều khoản đầy đủ, pycti/OpenCTI thật, quyền review, lịch chạy, RAM và nhập lặp
  trên lab chưa kiểm. Mẫu RSS synthetic và mẫu tái dựng rút gọn, không phải bằng chứng feed thật. Chưa lấy toàn văn.
