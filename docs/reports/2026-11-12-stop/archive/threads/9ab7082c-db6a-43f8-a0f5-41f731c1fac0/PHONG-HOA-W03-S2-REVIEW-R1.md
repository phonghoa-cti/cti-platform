# W03-S2 Backend — review và yêu cầu sửa R1

Ngày 12/11/2026. Candidate **82f8a6acc8f357645f7105a2cc84b46bf58f4e4f chưa được nghiệm thu**.

## Bằng chứng mới

Leader đọc diff 9 file (+1026/-1), source/app/contract/tests tại đúng candidate; status sạch tại đầu review. SHA256 báo cáo Backend F75EA13FFDF70CF89DCA0BB2E4D75EF50824DF0A4938A05A15472EEC8DB8B5FE khớp báo cáo.

Leader chạy mới từ tree cti-w03-status-s2-backend:
- ..\cti-w03-read-backend\.venv\Scripts\python.exe -m pytest portal_api/tests/test_cves_status_view_api.py -q -p no:cacheprovider: exit 0, 9 test qua.
- ..\cti-w03-read-backend\.venv\Scripts\python.exe $THREADS/9ab7082c-db6a-43f8-a0f5-41f731c1fac0/probe_w03_s2_cursor.py $WORKSPACE/cti-w03-status-s2-backend: exit 1, control qua / 7 ca hợp đồng không đạt, schema/technology/status/audit không đổi.

Kết quả máy đọc: w03-s2-cursor-probe-results.json cùng thư mục; raw stdout/exit: w03-s2-cursor-probe-command.json. Probe chỉ dùng dữ liệu tổng hợp, JWT sinh cục bộ và DB tạm, không gọi mạng. Lần đầu probe thiếu đường dẫn extractor; đã sửa riêng script Leader. Lần kế tiếp vướng dọn DB Windows do connection chưa thu hồi; đã thêm gc.collect(), lần kết quả nêu trên hoàn tất. Hai lỗi harness này không được tính là lỗi sản phẩm.

127 test hồi quy xanh và full suite 819 pass/4 fail là bằng chứng Backend đã cung cấp, Leader không chạy lại cả suite. Bốn lỗi STIX thiếu stix2-validator vẫn là giới hạn môi trường riêng, không sửa dependency trong R1. Log 03-full-suite.txt đang ghi 126 ở phần diễn giải trong khi log mới là 127: sửa cách mô tả, giữ kết quả cũ theo lần chạy.

## R1 — cursor không kiểm kiểu/giá trị đầy đủ

Ghi chú cleanup: thư mục DB thử từ lần probe lỗi cleanup, $USER_HOME\AppData\Local\Temp\leader-w03-s2-yvi2r26j, chưa được dọn. Lệnh xóa có kiểm đúng đường dẫn bị cơ chế kiểm duyệt tự động từ chối với thông báo blocked by policy. Leader không thử đường xóa khác. Không tác động DB sản phẩm; không tính cleanup là PASS.

Bắt đầu bằng GET hợp lệ ?kev=true&limit=1, giải mã next_cursor rồi chỉ thay trường được nêu, encode canonical base64url và gọi lại cùng query:

| Dữ liệu cursor không hợp lệ | Thực tế | Mong đợi |
|---|---|---|
| context.view=[] | 503 cves_unavailable | 422 invalid_cve_status_query |
| context.kev={} | 503 cves_unavailable | 422 invalid_cve_status_query |
| context.status=[] | 503 cves_unavailable | 422 invalid_cve_status_query |
| context.kev=1 (number, không phải boolean) | 200 và đọc dataset | 422, không đọc dependency |
| snapshot.as_of_date=2026-99-99 | 409 và đọc dataset | 422, không đọc dependency |
| context.kev=NaN | 503 cves_unavailable | 422 invalid_cve_status_query |
| context.q=unpaired surrogate U+D800 | 503 cves_unavailable | 422 invalid_cve_status_query |

Control cursor nguyên gốc trả 200. Cả bảy ca lỗi phải bị từ chối trước dependency, giữ no-store/Vary và không thay DB.

Nguyên nhân đọc từ portal_api/cves_status_view.py::_decode_cursor:
- Kiểm membership trong set trước kiểm kiểu cho view/kev/status gây TypeError với list/dict.
- Membership/equality Python cho phép 1 bằng True; kev chưa kiểm đúng bool hoặc None.
- as_of_date chỉ kiểm hình thức regex, chưa kiểm ngày tồn tại.
- _canonical_bytes(parsed) nằm ngoài đoạn bắt lỗi và có thể ném ValueError/UnicodeEncodeError cho JSON có NaN/surrogate. Không biến lỗi đầu vào thành dependency 503.

Sửa tại ranh giới giải mã/validation; kiểm rõ type và miền giá trị của mọi field, từ chối nonfinite JSON/Unicode không encode được bằng lỗi query có chủ đích. Không chữa bằng đổi toàn bộ generic exception handler và không đổi 503 của lỗi dependency thật. Giữ cursor hợp lệ, ngày đổi thật 409, route auth/role và hợp đồng hiện hành.

## Bằng chứng drift cần tách độc lập

test_cursor_context_cross_route_and_snapshot_changes hiện thêm status rồi thêm dataset rồi sửa technology mà không đưa DB/port về baseline; hai case sau có thể 409 chỉ vì status đã đổi. Bổ sung ca độc lập (fresh fixture hoặc khôi phục đúng baseline) cho dataset-only, technology-only, status-only, UTC-date-only; query/context giữ nguyên. Đây là khoảng trống chứng minh, chưa kết luận implementation drift sai.

## Giao CTI Backend

Tiếp tục đúng thread ec2f0709-b0f2-46ed-823d-9a461e1f1912, tree $WORKSPACE/cti-w03-status-s2-backend, một Sol medium trực tiếp. Đây là vòng sửa chức năng R1 đầu tiên sau kết quả trả về, khác hai lần nối lượt bị ngắt trước đó. Không reset, không worker lồng.

Phạm vi sửa: portal_api/cves_status_view.py, portal_api/tests/test_cves_status_view_api.py, docs/PROGRESS.md và cập nhật báo cáo/raw evidence. Chỉ sửa contract nếu cần làm rõ validation đã thống nhất, không mở rộng API. Không UI/gateway/dependency/route W03-R/S1/push/PR/merge/deploy/lab/LLM.

Chứng minh RED bằng ca mới trước sửa, GREEN sau sửa; chạy lại probe Leader (lưu output mới sang thư mục evidence riêng, không ghi đè evidence R1 Leader), nhóm S2 + W03-R + S1 phù hợp, Ruff/format/diff-check. Không cần chạy full suite đã biết thiếu validator. Đối chiếu fixture; schema không đổi thì không tạo lại vì hình thức.

Commit cục bộ, tree sạch, trả SHA, diff, lệnh/exit/test count và raw output nguyên vẹn. Báo cáo mới tại $THREADS/9ab7082c-db6a-43f8-a0f5-41f731c1fac0/PHONG-HOA-W03-S2-BACKEND-R1-RESULT.md, raw evidence tại $THREADS/9ab7082c-db6a-43f8-a0f5-41f731c1fac0/w03-s2-backend-r1-evidence. Giữ báo cáo candidate cũ làm lịch sử. Không sửa RUNS. Chưa giải phụ thuộc Frontend.
