# W05-STIX — review Leader, 11/11/2026

Trạng thái: **NEEDS_FIX nghiên cứu/brief**, chưa giao triển khai. Phạm vi review: hai tài liệu do CTI Research trả trong request `6b944460-af35-4d1a-b5b9-fc2499d43871`; không audit lại các phần đã accepted.

## Bằng chứng đã đối chiếu

- Source `cti-w05-selection-integration`, branch `feat/w05-selection-integration-20261111`, HEAD `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`, status sạch khi đọc.
- Research SHA256 `81A56EDF638BEEAFFE08D274499FCE51052DDA23DE037DCB9D79E5378E38129F`.
- Brief SHA256 `E07C517D7955A3BBB2E8D26E6CCBCF028D0A8478C2A88B5AE8CB9588299BC10F`.
- Đã đọc helper/schema store, `core/phonghoa_core/ioc.py`, spec W05 và brief nghiên cứu gốc.
- Đã mở nguồn OASIS và tài liệu validator ngày 11/11/2026. Chưa chạy validator hoặc test implementation; trang validator là tài liệu 3.2.0, chưa xác minh mã release 3.3.2 (đường dẫn GitHub được thử không tải được).

## Findings và quyết định để sửa

### R1 — Major: mã TLP:RED không đúng chuẩn
Brief dòng 77 ghi `5e57c739-391a-4eb3-b6f9-3f0a3c7ce4e6`. OASIS §7.2.1.4 quy định `marking-definition--5e57c739-391a-4eb3-b6be-7d15ca92d5ed`; created của các marking chuẩn là `2017-01-20T00:00:00.000Z`. Sửa cả hai tài liệu, ghi đầy đủ object marking chuẩn và test đối chiếu literal độc lập. Không áp dụng decided_at cho marking chuẩn. Giữ CLEAR→WHITE có provenance rõ và từ chối AMBER+STRICT trong lát cắt này.

Nguồn: https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html (mục 7.2.1.4).

### R2 — Major: hợp đồng UUID deterministic xung đột với lệnh strict
Brief dòng 66,79,86 yêu cầu UUIDv5 cho mọi loại, nhưng dòng validator yêu cầu strict không ngoại lệ. OASIS §2.9 cho phép dùng v5 cho SDO/Bundle ngoài khuyến nghị v4 với namespace riêng; SCO có thuật toán namespace + ID-contributing properties riêng. Tài liệu validator nêu check 103 kiểm v5 cho SCO/v4 cho phần còn lại và strict chuyển warning thành lỗi. Không được nói v5 SDO vi phạm MUST hoặc lệnh strict hiện tại chắc chắn PASS.

Leader chọn giữ deterministic: SCO theo thuật toán chuẩn OASIS (canonical JSON đúng quy định); SDO/Bundle UUIDv5 namespace riêng, nêu rõ ngoại lệ SHOULD. Brief phải chốt namespace/lược đồ name đầu vào, tránh collision khi hai DB dùng cùng draft/audit ID và selection indices nhưng khác payload/nguồn/TLP/exporter; không dùng namespace SCO cho SDO. Identity phải có nội dung/timestamp ổn định, không thay timestamp/marking theo từng draft dưới cùng ID. Chốt kiểm validator MUST đầy đủ và strict chỉ bỏ check 103 nếu release ghim xác nhận đúng code; có kiểm riêng mọi ID/SCO namespace/properties, không tắt nhóm kiểm khác. Ghi rõ đây là profile có ngoại lệ 103, không gọi là strict nguyên vẹn. Xác minh source release/CLI trước khi hứa lệnh.

Nguồn: OASIS §2.9,3.4; https://stix2-validator.readthedocs.io/en/latest/best-practices.html .

### R3 — Major: mapping không khớp loại IOC hiện hữu
`core/phonghoa_core/ioc.py:17` có tám loại: ipv4, ipv6, domain, url, email, md5, sha1, sha256. Không có sha512; email bị bỏ sót trong brief dòng 73,100. Sửa mapping/ma trận cho đúng tám loại, email→email-addr. SHA-512 và loại lạ là ca không hỗ trợ; không mở rộng core trong task export.

### R4 — Major: tự thêm ý nghĩa phát hiện bất thường và mất đường truy nguồn người duyệt
Research dòng 54–56 vẫn chọn Indicator và để worker chọn anomalous-activity hoặc bỏ field, trong khi input chỉ chứng minh trích xuất grounded và được duyệt. OASIS §4.7 định nghĩa Indicator phục vụ phát hiện hoạt động đáng ngờ/độc hại; không có bằng chứng đánh giá đó trong schema hiện tại.

Leader chọn lát cắt **Report + SCO + identity/marking**, chưa tạo Indicator, pattern, Observed Data hay relationship suy diễn. Chỉnh toàn bộ interface/ma trận/count cho nhất quán, bỏ test pattern không còn thuộc scope. Giữ provenance chuẩn và liên kết về final audit; tách danh tính exporter khỏi người duyệt. Snapshot phải giữ thông tin người duyệt nội bộ để handoff sau, không xuất raw subject/email hoặc giả danh tổ chức/người. Chốt identity config bằng schema/đường dẫn/cách CLI nhận cấu hình tin cậy cụ thể, không để 'config local' chung chung. Tác giả reviewer trên OpenCTI vẫn là acceptance tương lai, không gọi exporter identity là hoàn thành yêu cầu đó.

Nguồn: OASIS §4.7; repo `docs/specs/W05-duyet.md`.

### R5 — Major: publication output không có một contract thống nhất
Research dòng 85 cấm clobber nhưng brief dòng 62,88 yêu cầu os.replace đè đích. Leader chọn **không ghi đè output khác nội dung**: output chưa có thì publish nguyên tử không clobber; output đã có byte-identical thì thành công idempotent và không sửa; nội dung khác thì lỗi giữ nguyên. Không có --force/--replace. Chốt cách publish an toàn khi hai lần chạy cạnh tranh trên Windows; preflight exists rồi replace không đủ. Bảo vệ DB và sidecar -wal/-shm/journal, samefile/hardlink/symlink alias; temp cùng parent và cleanup khi lỗi. Ghi rõ giới hạn filesystem; không hứa crash-durability nếu chưa chứng minh.

### R6 — Medium: brief chưa tự đủ để triển khai
Đóng các chỗ 'hoặc/chốt trong code': config exporter, provenance trường cụ thể, phụ thuộc validator/test lock chính xác và scope docs/PROGRESS.md + ADR/contract phù hợp AGENTS. Đặt BEGIN trước các lần đọc schema/data cần cùng snapshot, thêm deterministic read-interleaving test theo cách đã có, không sleep. Phân biệt SHA nguồn text với hash payload đầy đủ và final selection hash; không coi hash tự lưu trong DB là chống quản trị viên sửa DB. Không cài package, không tạo tree, không sửa repo trong lượt Research sửa tài liệu.

## Phạm vi rework

CTI Research chỉ sửa hai file đã được giao, trên exact source chỉ đọc như trên; không sửa review này, RUNS, evidence cũ hoặc repo. Trả đủ sáu mục đã đóng, nguồn/file:line, hai hash mới, HEAD/status trước/sau và giới hạn chưa chạy. Không nghiên cứu lại UI/auth/lab hoặc mở rộng sang outbox/import. Leader kiểm bản sửa rồi mới giao Backend/Sol medium.

Dự án còn active. Tự động tiếp tục vẫn enabled; lượt lịch 05:56 ghi NOTHING NEW trong khi Leader đang làm, không chứng minh phục hồi việc bỏ dở. Không pause automation.
