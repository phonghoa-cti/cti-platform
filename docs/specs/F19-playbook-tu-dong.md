# F19 — Playbook tự động ngoài lõi OpenCTI CE

- Người phụ trách: [NHÓM ĐIỀN] (Hạ tầng + Web, AI/Agent review an toàn)
- Issue: [NHÓM ĐIỀN]
- Trạng thái: Nháp — spec chờ duyệt (27/11/2026)
- Phụ thuộc: F18/ADR 0018, F01/F02/F04/F08, W03/W04/W05, A01, B23/F17.

## Mục tiêu (1–2 câu)

Playbook là bộ quy tắc “nếu có sự kiện phù hợp thì tạo đề xuất/cảnh báo” do quản trị viên Phong Hỏa khai báo bằng YAML (định dạng văn bản cấu hình dễ đọc). Khi OpenCTI có dữ liệu mới hoặc đổi, một connector độc lập đọc luồng, so với tài sản SME, ghi cảnh báo/bản nháp có bằng chứng và chờ người có quyền duyệt mọi thay đổi OpenCTI; không tự chặn hay xóa.

## Người dùng và tình huống

- IT của SME: nhận cảnh báo mã CVE (mã định danh lỗ hổng) mới trùng sản phẩm đang dùng; mở W03 để xem nguồn, kiểm phiên bản bị ảnh hưởng, ưu tiên cập nhật.
- Analyst: kiểm bản nháp gắn nhãn, lý do, phiên bản dữ liệu và tác động; duyệt hoặc từ chối có lý do ở W05. Không coi duyệt là đã ghi lõi/đã vá.
- Admin Phong Hỏa: quản lý phiên bản rule, chạy thử không ghi (dry-run), bật/tắt từng rule sau review. Hermes là trợ lý đọc thông báo qua MCP, không giữ credential ghi, không tự duyệt.
- Ví dụ giả lập: công ty dùng ExampleCorp / ExampleApp 1.2, bản tin mới nói ứng dụng này có lỗ hổng. Máy đối chiếu tên sản phẩm và báo “cần xác minh phiên bản”, không khẳng định công ty đã bị tấn công.

## Đầu vào / Đầu ra

| | Mô tả | Ví dụ |
|---|---|---|
| Đầu vào | SSE (Server-Sent Events — máy chủ gửi sự kiện qua HTTP), sự kiện STIX 2.1 có ID, loại, phiên bản, nguồn, TLP, score/label nếu có | create/update/merge/delete; `vulnerability`, `indicator` |
| Đầu vào | Rule YAML cục bộ được duyệt, snapshot W04 công nghệ/tài sản theo tenant, chính sách F08, provenance/quyền nguồn | rule `cve-product-review` v1; vendor/product |
| Đầu ra | Kết quả match, alert cục bộ, nháp action trong hàng chờ W05, metadata audit/cursor; dữ liệu dẫn nguồn | alert ID, tenant, rule/version, event ID, asset ID, CVE, trạng thái cần xác minh |
| Đầu ra | MCP đọc alert, portal projection theo quyền; dry-run chỉ trả dự kiến, không ghi nghiệp vụ | “có cảnh báo mới cần kiểm tra”; không chứa IOC thô ngoài phạm vi |

## Xác minh giao diện CE, thiết kế thành phần

Tài liệu Data Streaming [S1] công khai API SSE cho connector, endpoint lọc `/stream/{STREAM_ID}`, sự kiện create/update/merge/delete và resume từ ID. Tài liệu Streams [S2] mô tả live stream thông thường, không gắn nhãn EE; danh sách EE [S3] có Playbooks nhưng không có live stream. Theo docs, dùng live stream lọc là hướng CE, **không dùng EE Playbooks**. Đây là xác minh tài liệu (bằng chứng gián tiếp về edition), không phải xác minh runtime; không có tuyên bố đã chạy ở 7.261124.0. Nền B25 chưa thấy PR #56 ở origin/main (xem F18). [CẦN KIỂM] trên CE đúng image/tag: tạo stream lọc bằng admin hợp lệ, kết nối reader, kiểm quyền/marking/heartbeat/resume và không kích hoạt EE. Nếu không đạt, dừng tích hợp; chỉ đề xuất polling GraphQL CE đọc-only theo B23, không tự sửa license.

- Connector dự kiến `connectors/playbook/`: reader SSE HTTPS, service account quyền đọc tối thiểu, không dùng raw `/stream` (docs yêu cầu Bypass all capabilities) hoặc Redis trực tiếp; stream riêng cho scope được phép. Secret từ env, không in log; TLS kiểm chứng, timeout, reconnect backoff có jitter. Chỉ URL đã cấu hình bởi admin, không dùng URL trong event.
- Normalize và validate envelope/ID/loại/marking, dùng core IOC/F04 nếu phù hợp; mapper score/label/marking/CVE được kiểm bằng fixture của schema phiên bản ghim. Không tự tạo điểm khi thiếu; phân biệt score 0 với null. Read model W03/W04 cung cấp match và snapshot; nếu mất quyền, nguồn stale hoặc dữ liệu hỏng thì không suy là an toàn.
- Engine độc lập, không LLM: cấu hình rule declarative → so điều kiện → sinh intent typed; không có GraphQL/SQL tự do, shell, eval, webhook, truy cập URL hoặc plug-in code do nguồn cung cấp. Rule chỉ đọc từ tệp admin đã duyệt, schema version/hash, atomically activate phiên bản hợp lệ; lỗi config không chạy rule mới.
- Portal API: lưu alert và outbox cục bộ trong một transaction, ghi audit, trạng thái/cursor; tách kho action intent W05 khỏi schema bản nháp IOC đang có (cần spec/migration riêng). Không sửa trực tiếp W05 hiện hành để giả rằng đã có action queue/publish. Hermes/MCP chỉ đọc projection được phép hoặc tạo đề xuất theo A01; không có công cụ execute/approve.
- Executor tương lai riêng (ngoài B25): chỉ service được ủy quyền mới có token ghi tối thiểu, đọc quyết định W05 hợp lệ, kiểm lại tenant/TLP/version/allowlist và phạm vi action đã duyệt, thực hiện đúng một action idempotent. Không có credential ghi trong connector/Hermes. Chưa có executor thì giữ pending/approved_not_executed; không hiển thị “đã gắn nhãn”. F19 MVP có mock publisher để kiểm luồng, chưa ghi live.

### Rule YAML (ví dụ cấu hình giả lập, chưa có parser)

    schema_version: 1
    rules:
      - id: cve-product-review
        version: 1
        enabled: true
        when:
          event_types: [create, update]
          entity_types: [vulnerability]
          labels_any: [kev]
          min_score: 60
          tlp_in: ["TLP:CLEAR", "TLP:GREEN"]
          cve_matches_customer_product: true
        actions:
          - type: propose_label
            label: phonghoa-review
          - type: create_alert
            audience: [portal, hermes]
            template_id: cve-review-v1
          - type: queue_review
            reason_code: cve_product_match

Đây là schema riêng dự kiến, không phải YAML của OpenCTI EE. Tất cả điều kiện có mặt kết hợp AND; danh sách trong một điều kiện là OR. `entity_types` là allowlist schema đã chuẩn hóa; `labels_any` so exact token; `min_score` số nguyên 0–100 (bao gồm biên), thiếu score/label khi rule yêu cầu thì no-match kèm lý do; CVE không nhất thiết có score/label KEV, nên rule CVE thường có thể bỏ hai điều kiện này, không bịa. `tlp_in` chỉ thu hẹp chính sách F08, không thể nới; thiếu/không rõ marking hoặc permission là hold/quarantine, không match ngoại tuyến gửi ra ngoài. Rule CVE kiểm ID định dạng, vendor+product exact casefold theo W03, dữ liệu nguồn đủ và snapshot W04 của đúng tenant; version hiển thị để IT kiểm thủ công. Không fuzzy match hay tuyên bố tự xác định affected khi chưa có kiểm CPE/version riêng. Không lấy tenant từ payload: ánh xạ scope cấu hình server.

Parser YAML an toàn (safe loader), từ chối duplicate keys, unknown key/tag, alias/anchor, giá trị kiểu sai, đường dẫn/include, ID/version trùng, action ngoài allowlist, YAML vượt 64 KiB, >100 rule hoặc >10 actions/rule (ngưỡng đề xuất); cap event 1 MiB, timeout đọc heartbeat 30s (cần đo). Rule không chứa secret, network destination hoặc template tùy ý. Không ép boolean/string thành số. Action `propose_label` **chỉ** tạo đề xuất typed trong hàng W05, `queue_review` ghi intent hợp nhất, không nhân đôi mỗi rule; `create_alert` chỉ lưu alert cục bộ. Nút phê duyệt phải hiển thị chính xác target ID, label, event hash/version, actor đề xuất, lý do, TLP và tenant. Quyền Analyst/Admin phía server, không người đề xuất/agent tự duyệt; reject/expiry 72 giờ theo W05; sửa dữ liệu sau duyệt làm mất hiệu lực và yêu cầu duyệt lại. Hành động ghi vào OpenCTI kể cả label/Note/Report phải qua hàng chờ người duyệt; không có action delete/block/patch/execute hay giảm TLP.

### Vòng đời sự kiện, chống trùng và stale

1. Reader kiểm schema/timestamp/source/TLP/tenant, reject dữ liệu không hợp lệ trước đánh giá. Event/message/label không đáng tin, luôn coi là dữ liệu, không thực thi chỉ thị nhúng. Technical heartbeat/connected/metrics chỉ cập nhật sức khỏe, không tạo alert; error/no-recover/mất cursor làm stale và yêu cầu reconciliation.
2. Tạo khóa chống lặp `(tenant, stream_id, event_id, rule_id, rule_version, asset_id, action_type)`, cùng khóa nghiệp vụ `(tenant, normalized_object_id, object_version, rule_id, rule_version, asset_id, action_type)` để replay từ hai event không tạo lặp. Event out-of-order cũ không ghi đè phiên bản mới; cập nhật có ý nghĩa tạo phiên bản/alert đính chính; merge/delete/revoke/expiry chỉ đánh dấu bản ghi cục bộ stale/thu hồi, không xóa kho hay tự chặn. Không chạy vòng lặp do chính label đã duyệt sinh event; đối chiếu effective state và version/idempotency.
3. Ghi record xử lý/alert/proposal/audit/outbox và cursor sau commit bền vững; crash trước commit replay, sau commit không nhân bản. Resume từ ID cuối đã xử lý bằng `Last-Event-ID` hoặc `from` theo docs [S1], không giả cursor nếu retention gap. Khi gap: dừng phát cảnh báo live, quản trị duyệt snapshot/recover có giới hạn và đối chiếu read-only; ghi khoảng thiếu. Event lỗi schema lưu metadata/hash đã lược trong quarantine theo chính sách (không log payload nhạy cảm), có quyết định skip minh bạch, không silently drop.
4. Notifier riêng chỉ đọc outbox và chính sách người nhận đã được phê duyệt, retry hữu hạn/backoff, dead-letter/uncertain (timeout sau gửi không replay mù). Telegram chỉ khi CLEAR/GREEN và quyền nguồn/tenant/người nhận cho phép, tin tối thiểu “Có cảnh báo cần xem. Mã hồ sơ …”; không gửi IOC thô/inventory/PII/evidence, không mở URL ngoài. Alert trong portal luôn lọc role/TLP, kể cả tổng số không tiết lộ bản ghi bị cấm.
5. Nhật ký kiểm toán append-only về nghiệp vụ (không tuyên bố chống sửa DB): UTC, actor/service, tenant, rule ID/version/hash, event ID/object/version, decision và lý do, alert/proposal ID, before/after hash, reviewer, retry/outcome, cursor/correlation ID. Không ghi secret/payload hạn chế; quyền đọc audit theo tenant; thời hạn lưu [NHÓM ĐIỀN].
6. Dry-run mặc định cho rule mới: dùng reader fixture/replay hoặc snapshot read-only, xuất bảng intent dự kiến/lý do ra màn hình hoặc tệp được phép riêng; không thay cursor production, không ghi alert/proposal/outbox/audit nghiệp vụ, không gửi tin hay gọi writer, không cấp token ghi. Có log phiên thử tách biệt, chỉ metadata. Live evaluation phải được admin bật sau phê duyệt và cổng kiểm.

### Liên hệ F17 và W03

W03 đang so exact vendor+product với dữ liệu tổng hợp, phiên bản chỉ là thông tin để IT đối chiếu, thứ tự KEV → EPSS → CVSS → mới hơn. Không thay đổi trạng thái W03 tự động. F19 tái sử dụng kết quả match W03/W04, tạo cảnh báo kèm nguồn/as-of và yêu cầu xác minh; F17 (B23 mục 7) có thể nhận cùng event để đề xuất tóm tắt khuyến cáo/rule phát hiện thụ động có bằng chứng đã công bố, không sinh exploit, không tự triển khai rule. F17 và F19 chia sẻ alert/outbox/cursor, không làm hai hệ thống gửi trùng; chỉ chuyển nháp rule khi đủ bằng chứng và đã qua quy trình kiểm ngoại tuyến của F17. Nếu thiếu dữ liệu thì tạo cảnh báo kiểm tra, không bịa rule.

Đo t_store → t_match → t_portal/Hermes theo B23, phân biệt thời gian công bố nguồn với thời gian kho nhận. Mục tiêu đề xuất offline p95 store→portal ≤60 giây với 100 event fixture; báo n, p50/p95/max, lỗi/gap/duplicates và môi trường. Không phải SLA thời gian tấn công hay kết quả đã đo.

## Tiêu chí chấp nhận (kiểm tra được)

- [ ] Runtime CE đúng phiên bản không bật EE: stream lọc được tạo hợp lệ, reader không bypass, nhận sự kiện và resume; kiểm quyền/marking bằng hai service account. Không có cổng này chỉ được nghiệm thu offline.
- [ ] Fixture 100 event vô hại, ca create/update/merge/delete/heartbeat; so khớp từng loại/label/score/TLP/CVE exact, inclusive biên 60, thiếu/null, tên sản phẩm sai/khác tenant, W03 version chưa rõ. Alert đúng n theo oracle cố định, không coi CVE trùng là bị tấn công.
- [ ] Config lỗi/duplicate key/tag/alias/action tùy ý/size/type/unknown field bị từ chối trước khi đọc hoặc tạo action; text chèn lệnh chỉ là dữ liệu. Không có command/shell/URL động.
- [ ] Dry-run so snapshot SQLite/cursor/outbox trước-sau: không đổi; fake writer/notifier ghi nhận 0 call; chỉ có kết quả mô phỏng.
- [ ] Fake writer chứng minh pending/rejected/expired/changed hash/cross-tenant/agent tự duyệt đều 0 call; approve đúng quyền + đúng snapshot cho phép đúng 1 lần trong mock. Không có xóa, tự chặn hay tự vá. W05 migration/action queue cần nghiệm thu riêng trước bật publisher.
- [ ] Crash ở trước/sau commit, reconnect/backoff/duplicate/out-of-order, retention gap và revoke; đúng một alert/proposal hợp lệ, cursor không vượt event chưa xử lý, đính chính không xóa lịch sử. Lỗi notifier không biến alert thành đã gửi, unknown outcome không retry mù.
- [ ] TLP:AMBER/AMBER+STRICT/RED, thiếu marking/quyền hoặc tenant khác: 0 call LLM cloud/Telegram, không lộ thông tin qua list/detail/export/log/counter; test với transport spy. CLEAR/GREEN vẫn cần quyền nguồn và người nhận đúng.
- [ ] Audit đủ actor/time/source/hash/rule/decision/reviewer/cursor/correlation, không secret; log replay có thể đối chiếu. Chạy toàn bộ fixture ngoại tuyến, report kết quả tách live.
- [ ] Portal IT xem đúng alert, Leader chỉ summary theo quyền; Hermes/MCP đọc theo tenant và không có tool ghi OpenCTI. Thử HTTP/browser/Telegram mock sau khi A01 và W05 có implementation; kiểm live riêng.
- [ ] Đo độ trễ giả lập n≥100, 0 cảnh báo chéo tenant/0 tác vụ không duyệt, p95 ≤60 giây là mục tiêu, ghi số đo thực, chưa đạt thì nêu rõ.

## Không làm trong phạm vi này

B25 chỉ viết spec, ADR và test dò license; không cài core, gọi OpenCTI/feed thật, làm engine/parser/queue/publisher/UI/bot thật, không bật EE. F19 MVP không xây kéo-thả workflow như EE, không có vòng lặp tùy ý, không phân tích ngược/exploit, không tự chặn, xóa, vá hoặc trực tiếp thực thi rule phòng thủ, không dùng LLM để đánh giá YAML. Không triển khai SaaS đa tenant trước khi F18 #3 đạt cổng cô lập; fixture hai tenant vẫn bắt buộc để ngăn lỗi scope.

## Rủi ro và câu hỏi còn mở

- CE/docs latest có thể khác tag ghim: kiểm smoke CE, log phiên bản và schema SSE; nếu live stream không dùng được thì báo lại, không thay license.
- Stream retention/host ngủ/đứt mạng: heartbeat, cursor, stale, bounded recovery; không hứa không mất dữ liệu ngoài retention.
- Giả dương do product alias, thiếu version/score, event bị sửa: exact match + evidence + reviewer, không tự hạ TLP, không tự gắn nhãn.
- SQLite hiện là single-tenant: không cho khách dùng kho chung; cần chốt partition/instance trước bán. [NHÓM ĐIỀN] retention audit, cap, rule đầu tiên và policy người duyệt/gửi.
- Nhóm cần duyệt scope P1, cổng CE và publisher riêng, quyền feed/model; mọi giá trị thời gian/giới hạn ở đây là đề xuất.

## Chia task (mỗi task ≤ 2 giờ cho agent)

1. Đối chiếu CE pin/stream docs, tạo fixture envelope + oracle (2h).
2. Schema YAML strict và test parser lỗi (2h).
3. Chuẩn hóa event/mapping core (2h).
4. Matcher condition và edge cases TLP/score/labels (2h).
5. Adapter W03/W04 snapshot tenant, CVE fixture (2h).
6. Reader SSE mock, retry/heartbeat/cursor (2h).
7. SQLite alert/receipt + idempotency/replay (2h).
8. W05 action intent contract + mock review/publisher gate (2h).
9. Audit/transaction/outbox và dry-run invariant (2h).
10. API alert read/role + Hermes MCP contract mock (2h).
11. Notifier mock, egress/unknown/revoke tests (2h).
12. Test offline xuyên luồng, đo độ trễ, biên bản; nếu CE lab chưa sẵn sàng chỉ ghi offline (2h).

Tổng 24 giờ công ước lượng cho lát cắt nhỏ F19, không gồm setup OpenCTI/live feeds/production publisher và rollout; chia việc mới, chờ chủ duyệt trước code.

## Nguồn công khai (27/11/2026)

- [S1] https://docs.opencti.io/latest/reference/streaming/ — SSE, event types, filtered stream, resume/recover.
- [S2] https://docs.opencti.io/latest/usage/import/internal-streams/ — live streams và cấu hình.
- [S3] https://docs.opencti.io/latest/administration/enterprise/ — Playbooks thuộc EE, live stream không nằm trong danh sách EE.
- Nội bộ: F18, F01/F02/F04/F08, W00/W03/W04/W05, A01, X01; VAN_HANH/ket_qua/B23.md mục 3.2, 4, 7.
