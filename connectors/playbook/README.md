# F19 — Playbook độc lập (B26, MVP ngoại tuyến)

Playbook là tập luật “nếu… thì…” để phát hiện sự kiện đáng kiểm tra. Ví dụ: mã CVE (lỗ hổng phần mềm)
có trong KEV (danh sách lỗ hổng đã bị khai thác) trùng tên phần mềm doanh nghiệp đang dùng → cảnh báo
mức cao và đề xuất nhãn chờ người duyệt. Trùng tên không chứng minh phiên bản bị ảnh hưởng hay đã bị tấn công.

## Chạy thử trên fixture

Từ gốc repo, trong môi trường Python 3.12 đã có dependency của API:

    $env:PYTHONPATH='.;core;extractor'
    .\.venv\Scripts\python.exe -m connectors.playbook

Linux: `PYTHONPATH=.:core:extractor python -m connectors.playbook`.
Mặc định dry-run (chạy thử), SQLite chỉ ở RAM, không ghi cursor/alert/audit vào đĩa.
Fixture tổng hợp `tests/fixtures/demo.sse`: indicator score 80 CLEAR → alert và log;
RED → không tạo intent; CVE cần snapshot W03/W04 tương ứng mới tạo alert.
Có thể thử với `--fixture <file.sse> --rules <file.yaml>`.
Để kiểm CVE, truyền đồng thời `--technology-db <W04 SQLite>` và
`--cve-fixture portal_api/tests/fixtures/w03-cves-synthetic.json` (chỉ dữ liệu mẫu;
W04 có công nghệ Fortinet/FortiOS). W03 dùng read-only, báo phiên bản chưa xác minh.
`--persist --db <playbook.sqlite>` mới lưu kết quả mẫu; chọn DB riêng, không dùng DB W04/W05.
Chạy lại cùng fixture không nhân bản. Không có nút/API thực thi nhãn.

## Hợp đồng và an toàn

- `source.py`: SSE (Server-Sent Events) tách nguồn fixture và lớp LiveSource GET HTTPS
  `/stream/<id>` đã cấu hình, token đọc từ env, Last-Event-ID, timeout, không redirect.
  Profile envelope giả lập `{"data":{STIX object}}`; marking map cấp bởi admin, không lấy tenant từ event.
  Chỉ create/update indicator/vulnerability, ID luồng kiểu Redis; technical heartbeat bỏ qua.
  Merge/delete/error/unknown schema/marking, cursor gap hoặc xung đột làm dừng; không tự nhảy cursor.
- `rules.py`: safe parser YAML 1.2 dạng giới hạn (mapping/sequence thụt 2 dấu cách, inline list,
  token đơn giản, chuỗi ngoặc kép JSON, boolean và số nguyên; JSON cũng hợp lệ).
  Không hỗ trợ tag, anchor, alias, include, multiline, single quote, comment cuối dòng hay YAML tổng quát.
  Giới hạn 64 KiB/100 luật/10 action; schema nghiêm ngặt, điều kiện AND, list OR, score inclusive.
- `engine.py`: dùng CveReadService W03 và TechnologyStore read-only, không viết lại match vendor/product.
  SQLite transaction từng event lưu receipt, version, audit (UTC, rule/hash/version, entity/hash, action),
  outbox, pending_labels và cursor; bản mới làm intent cũ stale, không xóa lịch sử. Scope tenant/stream
  do vận hành cấp, không tự tin payload. Không lưu nguyên văn báo cáo/IOC vào outbox.
- `read_outbox` là projection đọc cục bộ cho adapter portal/Hermes tương lai, chưa gắn API/MCP/Telegram.
  Chỉ CLEAR/GREEN, đúng scope/audience. AMBER/RED/AMBER+STRICT không sinh alert/đề xuất;
  không có LLM, gửi tin, webhook hay OpenCTI writer. `pending_labels` là hàng nháp riêng, không phải W05
  IOC schema; không có chức năng approve/publish.
- Chưa kiểm CE runtime, phiên bản/marking/permission của luồng thật, reconnect tự động/backoff,
  retention reconciliation, revoke/delete, RBAC/auth API, expiry/reviewer hay thông báo thật.
  LiveSource chỉ được kiểm bằng mock; không bật live/publish trước khi nghiệm thu các cổng F19/F08.
  DB mẫu là kho nội bộ của người vận hành, không cấp trực tiếp cho khách. Không coi trạng thái active
  trong DB là đảm bảo nguồn còn mới sau khi luồng dừng; cần cổng stale/reconciliation trước tích hợp.
