# W03 — review QA và bước nối tiếp 12/11/2026

Leader đã kiểm các cuộc mở: chỉ Leader tại cuộc này chạy; QA/Engineer/Backend idle. Đã đọc báo cáo QA, raw focused test, raw probe, diff harness và kiểm SHA/status hiện tại: Backend 1401402122a58baa7dba2b3f1a75abc080baabab; Engineer 170a38bb92fee09bd2e917faedc8de6342046b54, hai tree sạch.

## Phần chấp nhận và phần còn chặn

- Chấp nhận đầu ra QA request 17e8f806-387b-4ff6-9203-b6091ea3afd7. QA chạy focused 12 PASS/106 deselected exit0; không coi đó là suite Leader chạy lại.
- Leader tự chạy lại probe_wire.py từ đúng candidate Backend: exit0, checkout lệch đúng 3 dataset_id, bản sao LF khớp cả 5 wire, SOURCE_UNCHANGED=True. Log: leader-wire-reproduction.log. WIRE-01 được xác nhận; candidate Backend còn gate clean-checkout FAIL, chưa chấp nhận toàn candidate hoặc toàn W03-S1.
- Chấp nhận riêng bằng chứng chặng B rework tại 170a38b: Leader kiểm 27/27 artifact hash/size, đọc trace GET200 -> PUT503 -> GET503 -> GET503 -> GET200 với đúng một PUT, DOM khóa, và xem ảnh khóa sau remount. QA đã đối chiếu hai SQLite mode=ro (0/0 -> 1/1), ảnh phục hồi, provenance và cleanup; Leader tái dùng phần kiểm QA đó, không khởi động lại browser/helper.
- Chặng A và các accepted_results cũ không thay đổi. Bằng chứng B không chứng minh product256 đã tích hợp.

## Quyết định kỹ thuật nhỏ nhất

Chọn rule đúng một file fixture `portal_api/tests/fixtures/w03-cves-synthetic.json text eol=lf` trong .gitattributes; không nới assert, không đổi hash dữ liệu thật, không renormalize cả repo. Nguồn chính thức đã đọc ngày 12/11: https://git-scm.com/docs/gitattributes — mục text/eol xác nhận eol=lf giữ kiểu xuống dòng LF khi checkout. Giới hạn: phải chứng minh bằng Git checkout thực và test wire, không chỉ rewrite file đang làm.

## Giao Engineer: hoàn tất phần còn thiếu trong W03-STATUS-INTEGRATION

Một Sol medium, cùng thread b05471df-3a0c-49c0-b02b-4019e1cf15d4 và tree `$WORKSPACE\cti-w03-status-integration`, bắt đầu từ 170a38bb92fee09bd2e917faedc8de6342046b54. Không tạo worker thay thế hoặc sửa tree Backend.

1. Đọc AGENTS/docs progress/contract đúng nhánh, báo cáo QA tại thư mục chứa brief này. Giữ toàn bộ chặng A/B cũ. Ghi test wire RED hiện tại; đây là lỗi đã tái hiện, không tìm lỗi mới ngoài phạm vi.
2. Đưa đúng commit Backend 1401402122a58baa7dba2b3f1a75abc080baabab vào nhánh tích hợp cục bộ bằng cherry-pick; chỉ giải xung đột docs/PROGRESS theo nội dung hai bên. Không merge main, push, PR hoặc phát hành. Đây là candidate tích hợp, chưa baseline accepted.
3. Sửa WIRE-01 bằng rule .gitattributes hẹp như trên và LF fixture đúng bytes; chứng minh rule áp dụng bằng git check-attr và checkout mới trong thư mục evidence riêng với core.autocrlf=true ở phạm vi lệnh. Không đổi global/local shared Git config, không reset/clean tree, không normalize file ngoài allowlist.
4. Cập nhật `tools/local_integration/tests/capture_w03_status_wire.py` và gate/tests/fixtures W03 status liên quan: product256 (gồm Unicode astral nếu contract đếm code point) hợp lệ; product257 fail-closed; vendor128 hợp lệ và129 bị chặn. Bỏ kỳ vọng cũ product256->503. Wire thực phải qua parser Frontend, không sửa response mẫu thủ công để ép đạt.
5. Chạy test wire trước đây FAIL trên candidate và checkout mới; focused product/vendor/status; capture wire và parser gate liên quan; Ruff/diff-check. Giữ raw lệnh/exit/count, SHA256 fixtures và hash raw bytes. Không lặp full suite hoặc browser chặng A/B khi không có delta ảnh hưởng. Nếu thay đổi vượt scope hoặc làm bằng chứng cũ không còn áp dụng, báo rõ trước khi mở rộng.
6. Commit cục bộ, tree sạch. Báo kết quả vào `PHONG-HOA-W03-INTEGRATION-PRODUCT256-RESULT.md` và evidence trong `w03-product256-integration-evidence` ở thư mục chứa brief này. Trả SHA, diff, test thực chạy, lỗi/cảnh báo và phần chưa xác minh. Không tự nghiệm thu toàn dự án.

Allowlist: 5 file của commit Backend; .gitattributes (chỉ rule fixture nêu trên); portal_api/tests/fixtures/w03-cves-synthetic.json (chỉ LF, không đổi dữ liệu); tools/local_integration/tests/capture_w03_status_wire.py; tools/local_integration/tests/test_runner.py nếu cần cập nhật expectation liên quan; portal/web/tests/*cve-status* và fixtures/w03-status-* liên quan capture/parser; tools/local_integration/README.md; docs/PROGRESS.md; output riêng nêu trên. Không sửa UI runtime/auth/audit/gateway policy/RUNS. Nếu tên file thực khác, báo đúng tên trước khi mở rộng, không dò/sửa mảng khác.

Tối đa hai lần thử cùng lỗi; không lab/cloud/LLM thật/secret/dữ liệu thật. Bước tiếp: Leader nghiệm thu candidate tích hợp mới, rồi chọn lát cắt tiếp từ mục tiêu tổng; S2 phải nghiên cứu trước.
