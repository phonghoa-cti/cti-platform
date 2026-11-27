# F18 — Kế hoạch thay thế tính năng trả phí của OpenCTI

- Người phụ trách: [NHÓM ĐIỀN] (Hạ tầng, Web, AI phối hợp)
- Issue: [NHÓM ĐIỀN]
- Trạng thái: Nháp — spec chờ duyệt, 27/11/2026.
- Mục tiêu: Phong Hỏa cung cấp các kết quả nghiệp vụ tương đương ở lớp riêng cho SME (doanh nghiệp vừa và nhỏ), không nhân bản toàn bộ giao diện hay sửa lõi OpenCTI.

## Nền và phạm vi

B25 được yêu cầu dựa trên CE 7.261124.0 (PR #56 theo brief). Nhánh thực tế được tạo từ origin/main `4d1aeea` (PR #48); PROGRESS trên nền này còn ghi gói demo LTS 7.260811.0-lts.2. B25 không đổi image, không xác nhận PR #56 đã gộp và chưa chạy OpenCTI bản mới. [CẦN KIỂM] đồng bộ nền và smoke test CE ghim trước code F19. Các mô tả tính năng bên dưới dựa trên tài liệu công khai [S1], không phải đọc mã EE.

Đã có thư viện `core/phonghoa_core`, API FastAPI `portal_api/`, portal Next.js, W03/W04/W05 và extractor chạy cục bộ trên fixture tổng hợp. Có W05 snapshot, quyết định/audit SQLite, xuất STIX ngoại tuyến; X01 có ingest PDF/text, regex, grounding (đối chiếu bằng chứng), adapter LLM giả lập. Chưa chứng minh chất lượng model/feed thật, import OpenCTI, Telegram thật hay isolation nhiều khách hàng. `connectors/` và `mcp-server/` trên nền B25 chưa có code nghiệp vụ (chỉ .gitkeep); A01 là thiết kế; B23/F17 là đề xuất. Không nhận công của nhánh khác thành tính năng đã gộp.

## Ma trận 15 tính năng EE

Tên và mục đích EE đối chiếu danh mục [S1] ngày 27/11/2026. Các phương án bên phải là thiết kế độc lập của Phong Hỏa; giờ công ước lượng có AI hỗ trợ, tính cả kiểm thử fixture, không phải số đo hay giá bán. P1 = lát cắt ưu tiên; P2 = mở rộng sau MVP; P3 = sau khi đủ nguồn lực; Bỏ = không làm. Các cổng quyền, TLP (quy tắc giới hạn chia sẻ dữ liệu) và audit tối thiểu phải có ngay trong P1.

| # / Tính năng EE | Làm gì theo docs [S1] | Phong Hỏa thay bằng gì / thành phần | Tái sử dụng tại nền repo | Ưu tiên | Giờ | Phụ thuộc |
|---|---|---|---|---|---:|---|
| 1 Activity monitoring | Theo dõi ai thao tác gì và lúc nào. | Portal API: nhật ký có actor, tenant, action, object, UTC, before/after hash, correlation; màn lọc/xuất audit theo quyền. Không hứa log nội bộ toàn bộ OpenCTI. | W03 status audit, W04 audit, W05 decision audit | P2 (audit tối thiểu P1) | 12 | F08, W05, lưu giữ log |
| 2 Playbooks & automation | Quy trình xử lý tự động khi dữ liệu thay đổi. | Connector nhận live stream; YAML có điều kiện/hành động allowlist; portal alert và hàng duyệt, Hermes/MCP đọc. F19, không có ghi trực tiếp. | Core chuẩn hóa/chấm điểm, W03/W04 match, W05 review, F17 đề xuất | P1 | 24 | F01 CE live stream, W05 action queue, F08 |
| 3 Organizations segregation | Tách quyền truy cập dữ liệu theo tổ chức. | Portal API và kho riêng từng SME; CE instance riêng mỗi khách nếu có dữ liệu riêng, không cho khách vào kho chung; chỉ chia sẻ intelligence công khai qua hợp đồng dữ liệu. Chưa làm SaaS nhiều khách. | W00 single-tenant, auth JWT/role, SQLite W04/W05 | P2 (cổng trước bán nhiều khách) | 28 | kiến trúc tenant, backup, F08, test chéo khách |
| 4 Authorized members | Giới hạn người được đọc/sửa/quản lý đối tượng cụ thể. | Portal ACL (danh sách cấp quyền) deny-by-default theo tenant, object, subject và action, giao quyền quản trị có audit; áp dụng cả list/search/export. | portal_api/auth.py, projection Leader, W05 roles | P3 | 16 | #3, F08, kiểm tra IDOR |
| 5 Draft capability control | Cho làm việc trên bản nháp nhưng hạn chế quyền xuất bản kho chính. | Portal W05 tách propose/review/publish; hash phiên bản, người duyệt khác người đề xuất; service xuất bản riêng chỉ thực hiện quyết định hợp lệ. | extractor drafts/store/selection, W05 review, STIX export offline | P2 (baseline W05 bắt buộc P1) | 12 | F08, W05 action queue, kiểm ghi CE |
| 6 Full text indexing | Tìm kiếm cả nội dung tài liệu thay vì chỉ metadata. | Portal API/extractor: SQLite FTS5 trên bản văn đã được phép lưu, index theo tenant/TLP; lọc trước tìm, không để snippet lộ dữ liệu. | extractor local_ingest/evidence, SQLite; W02 tra cứu | P2 | 16 | quyền lưu nguồn, #3, retention |
| 7 AI Insights | Tóm tắt báo cáo và hoạt động đe dọa, có khả năng dự báo. | Extractor/Hermes: tóm tắt Việt/Anh có dẫn nguồn và khoảng thời gian; thống kê xu hướng mô tả, không dự báo chắc chắn. | X01 adapter/grounding/eval, W01 spec, A01 weekly_brief (spec) | P1 | 16 | X01 model/quyền nguồn, TLP, MCP |
| 8 NLP (Natural Language Processing) | Trích thực thể và quan hệ từ PDF/văn bản. | Extractor X01: PDF/text → regex + LLM có schema, evidence, ATT&CK, nháp STIX; quan hệ chỉ khi có chứng cứ và hỗ trợ schema, nếu không abstain (từ chối kết luận). | local_ingest, injection, grounding, attack catalog, STIX export, W05 | P1 | 24 | dataset được phép, model thật, đánh giá P/R/F1, W05 |
| 9 Natural Language Query (NLQ) | Chuyển câu hỏi tự nhiên thành bộ lọc tìm thực thể. | Hermes/MCP/portal API: intent và tham số schema giới hạn cho IOC, CVE, tổng quan; hỏi lại khi mơ hồ, quyền ở API. Không sinh GraphQL/SQL tự do. | W02/W03 APIs, auth, A01 tool contracts (spec) | P1 | 16 | MCP implementation, F08, X01 adapter nếu dùng LLM |
| 10 Fintel templates | Dùng mẫu tạo báo cáo hoàn chỉnh có văn bản, biểu đồ và xuất PDF. | Portal report service: mẫu riêng tiếng Việt, số liệu theo snapshot, nguồn và TLP, render PDF nội bộ, không render HTML không tin cậy. | W01/F06 spec, W03 read model, W05 provenance | P1 | 16 | quyền nguồn, PDF renderer/license, #7 tùy chọn |
| 11 Dissemination list | Gửi tài liệu tới danh sách người nhận phù hợp. | Portal/Hermes: danh bạ tenant, xác minh người nhận, preview, hàng duyệt, outbox gửi email/link có xác thực; Telegram chỉ thông báo tối thiểu. | W05 audit/review, A01 thông báo (spec), B23 outbox đề xuất | P1 | 12 | #10, #12, F08, SMTP/quyền chia sẻ |
| 12 Email template | Tạo mẫu thư gửi cho người dùng, kể cả thông báo quản trị. | Portal: mẫu text/HTML tĩnh có biến allowlist, escape dữ liệu, preview và phê duyệt; SMTP credentials từ env. | W00 VI/EN, W05 mô hình duyệt | P1 | 8 | #11, SMTP, chính sách nhận/hủy nhận |
| 13 PIR (Priority Intelligence Requirements) | Gom và ưu tiên tình báo theo nhu cầu quyết định của người dùng. | Portal/Hermes: hồ sơ nhu cầu theo tài sản, ngành và chủ đề, bộ lọc và bản tin ưu tiên; dùng F19 và W03 thay việc tạo PIR trong OpenCTI. | W04 Technology, W03 rank, F04 core, A01 spec | P2 | 12 | #2, #7, F08 |
| 14 SSO (single sign-on) definition & usage | Cấu hình và dùng đăng nhập một lần qua các nhà cung cấp danh tính. | Portal độc lập dùng Cloudflare Access/OIDC đã thiết kế; API xác minh JWT thật; lõi CE giữ local auth và mạng nội bộ. Không mô phỏng đăng nhập trực tiếp lõi CE, bỏ phần UI quản lý SSO cho OpenCTI. | portal_api/auth.py, test JWT RSA tổng hợp, W00 | P3 | 8 | IdP thật, HTTPS/JWKS, F08 |
| 15 Custom fields | Thêm trường riêng cho loại thực thể theo nghiệp vụ. | Portal API: metadata phụ có schema, type/version/validation; lưu bên ngoài lõi theo ID STIX + tenant, không sửa model OpenCTI; export có mapping rõ. | W04 TechnologyStore, W05 payload/version, STIX export | P3 | 12 | #3, schema registry, F08 |

P1: 7 mục, 116 giờ; P2: 5 mục, 80 giờ; P3: 3 mục, 36 giờ; tổng 232 giờ công đề xuất, chưa cộng dự phòng 20–30% (khoảng 46–70 giờ) và setup lab/feed thật, pháp lý nguồn, vận hành, kiểm định bảo mật. #11/#12 dùng chung outbox/template, không tính lại trong F19; F17 dùng chung adapter/matcher/outbox, chỉ tính thêm phần riêng khi lập kế hoạch. Không bảo đảm hoàn tất trước 27/02/2027. Chốt lát cắt P1 nhỏ (một rule CVE, một tóm tắt có nguồn, một truy vấn, một mẫu PDF và gửi giả lập) trước; mở rộng nếu còn sức. P2/P3 không phải điều kiện đồ án, trừ các cổng an toàn/pháp lý trước bán.

## Ranh giới pháp lý

- CE = Community Edition, Apache License 2.0; EE = Enterprise Edition, giấy phép thương mại riêng. LICENSE [S2] phân biệt theo header từng file và cho ví dụ marker chính xác `OpenCTI Enterprise Edition License`. Không được mở, chép, phân tích hay diễn giải mã EE; chỉ dùng tài liệu công khai mô tả chức năng, API CE được phép và tự thiết kế ngoài lõi. Không trích logic, assets, UI hay test EE, không bỏ kiểm license, không bật thử EE để xây bản bán. Không coi mã thấy trên GitHub là được phép phân phối thương mại.
- Chỉ dùng core CE không bật EE/trial/Filigran license/XTM One kích hoạt EE; không fork sửa lõi. Lõi là dịch vụ riêng, giao tiếp qua API/stream công khai. Kiểm các image/digest, trạng thái CE và quyền phân phối trước phát hành; upstream có mã EE chung repo, nên kiểm gói triển khai và điều khoản riêng, không đồng nhất "không kích hoạt" với quyền tái phân phối toàn bộ image. Nếu chưa rõ, khách tự triển khai CE theo điều khoản đã duyệt và Phong Hỏa kết nối; không bán gói chứa phần chưa xác minh.
- Giữ LICENSE/NOTICE, attribution và nghĩa vụ Apache 2.0 nếu phân phối CE; rà từng dependency, connector, feed, dataset, model, PDF renderer, nhãn TLP và quyền thương mại/lưu/biến đổi/chia sẻ. TLP không thay giấy phép. Không dùng tên/logo gây hiểu nhầm sản phẩm chính thức Filigran. Chủ/nhóm rà pháp lý trước hợp đồng; đây không phải ý kiến pháp lý.
- Cổng kiểm tra `core/tests/test_no_opencti_ee_code.py` chỉ dò marker byte trong cây repo ngoài thư mục bỏ qua và các tài liệu giải thích chỉ định; không in nội dung. Đây là chỉ báo phòng ngừa, không phát hiện mã bị bỏ header, mã nhị phân nén, encoding khác hoặc dependency ngoài cây. Review nguồn gốc/SBOM, license, gói deploy vẫn bắt buộc.
- SSO: [S3] và [S4] nói từ 7.260224.0, định nghĩa **và sử dụng** chiến lược SSO thuộc EE, CE chỉ đăng nhập local. Vì vậy giả định brief "SSO file config vẫn CE" không đúng ở dòng 7.x đã nêu; không dùng env/config để lách. Portal SSO là xác thực độc lập, không cấp SSO vào lõi. [CẦN KIỂM] runtime đúng tag ghim, không bật thử EE.

## Tiêu chí chấp nhận của kế hoạch

- [ ] Chủ duyệt thứ tự, lát cắt P1, giờ công và những phần không làm; mỗi hạng mục mới có spec/test riêng.
- [ ] Dò marker EE đạt, review giấy phép và provenance từng thành phần; smoke test CE đúng tag, không kích hoạt EE.
- [ ] Chỉ dùng dữ liệu giả lập cho test; cổng quyền/tenant, TLP, audit và phê duyệt được kiểm trước nối live; không gửi AMBER/RED, nhãn không rõ hay dữ liệu khách lên LLM cloud.
- [ ] Báo cáo tách phạm vi đã làm/chưa làm và kết quả thật/giả lập; không tuyên bố parity OpenCTI EE, SLA phát hiện, hay thương mại sẵn sàng khi chưa nghiệm thu.

## Giải thích cho người mới

OpenCTI CE giống một kho hồ sơ an ninh có thể dùng theo giấy phép mở, còn EE cung cấp thêm những tiện ích thương mại. Phong Hỏa giữ kho đó và tự xây dịch vụ bên ngoài, ví dụ khi có mã CVE (mã lỗ hổng phần mềm) mới liên quan phần mềm của công ty thì hiện cảnh báo để IT kiểm tra. IOC là dấu hiệu như tên miền đáng ngờ; TTP là cách thức tấn công, được phân loại bằng MITRE ATT&CK; STIX là chuẩn lưu thông tin tình báo. Trợ lý giúp đọc, tìm và tóm tắt, nhưng không tự sửa hồ sơ, chặn mạng hay gửi dữ liệu hạn chế. Kế hoạch này giúp doanh nghiệp nhỏ nhận thông tin tiếng Việt, có nguồn và có người kiểm tra, không phải lời hứa đã xây đủ 15 tính năng.

## Câu hỏi cho nhóm

1. Chốt lát cắt P1 7 mục hay chỉ F19 + X01/NLQ + một mẫu PDF gửi thử trước mốc đồ án?
2. Bán theo mỗi khách một CE/portal riêng hay phát triển SaaS sau khi có cổng cô lập tenant và rà pháp lý?
3. Model local hay cloud chỉ với CLEAR/GREEN được phép; ngân sách, bộ dữ liệu và ngưỡng chất lượng?
4. Ai duyệt hành động/địa chỉ nhận, chọn email hay thông báo Hermes trước, và có cần hai người duyệt khi gửi ngoài?
5. Ai chịu trách nhiệm hồ sơ license/SBOM/nguồn feed và cổng nghiệm thu CE đúng phiên bản trước bán?

## Nguồn công khai (truy cập 27/11/2026)

- [S1] https://docs.opencti.io/latest/administration/enterprise/ — đủ 15 mục chức năng.
- [S2] https://github.com/OpenCTI-Platform/opencti/blob/master/LICENSE — LICENSE công khai, mục Examples of License Headers in File; bản tag 7.261124.0 chưa truy xuất được qua web, cần đối chiếu trước phát hành.
- [S3] https://docs.opencti.io/latest/deployment/authentication/ — cảnh báo Authentication Strategies – Enterprise Edition Starting v7.260224.0.
- [S4] https://docs.opencti.io/latest/deployment/breaking-changes/7.260224.0-SSO-authentication-migration/ — Migrating as a Community Edition.
- [S5] https://github.com/OpenCTI-Platform/opencti — README, Editions & License; không đọc file nguồn EE.
- [S6] https://docs.opencti.io/latest/reference/streaming/ — API stream; đối chiếu F19.
