# W03-S1 — nghiệm thu bằng chứng chặng A, 12/11/2026

Kết luận: chấp nhận đầu ra chặng A ở phạm vi helper/kiểm hợp đồng/tài liệu; **chưa chấp nhận toàn bộ W03-STATUS-INTEGRATION**. Hai điểm còn mở là phục hồi unknown trên cùng trang và thống nhất giới hạn product giữa W03/W04.

## Phiên bản và bằng chứng

- Tree: $WORKSPACE\cti-w03-status-integration
- HEAD d09929311b4b6447aac8b2ec6adac5999beda25d, branch feat/w03-status-integration-20261112; trạng thái sạch khi kiểm.
- Delta từ a2c4ffa245297a8714b0023bf4e4bb248869dc36: 9 file, +329/-27, helper/tests/docs; không đổi product UI/Backend. Đã đọc cả delta; git diff --check exit 0.
- Report gốc: $THREADS\662556d5-bef1-4bf9-b1f8-ce0ad295308c\PHONG-HOA-W03-STATUS-EVIDENCE-STAGE-A-RESULT.md
- Evidence cùng thư mục cha, w03-status-evidence-stage-a. 45/45 SHA256 khớp. Hash manifest: 466d651c7490c5d386ab9e69577a6fb745c00479a0d306e318e51b214e63b8f8.
- Leader chạy review_stage_a.py trong thư mục báo cáo này, bằng Python của cti-w03-read-backend/.venv: exit 0; kết quả stage-a-review-checks.json. Kiểm hash, biên response, history 100+1, cursor, trace một PUT200 và GET503/503/200, một lần mở /lo-hong, summary một record/một audit.
- Leader chạy tại tree: Python trên với `-m pytest tools/local_integration/tests/test_w04_browser_helper.py -k 'startup_failure or cleanup_state' -o addopts='' -q -p no:cacheprovider`: exit 0, 2 passed, 6 deselected. Kiểm lại rủi ro che lỗi startup và metadata cleanup, không lặp full suite.
- Đọc log worker: 9 focused Python, 6 parser/provider, 10 capture, gate env/file thiếu/JSON hỏng exit1, Ruff/format đạt. Đây là kết quả tái dùng, không phải Leader chạy lại.
- Đã mở hai ảnh known-temporary-error.png và known-recovered-same-page.png: thông báo đã lưu còn hiện khi lỗi đọc, bản ghi v1 còn hiện sau phục hồi. Trace không reload và không ghi lại. Tương tác đóng/mở cụ thể lấy từ báo cáo worker; hai ảnh/trace không tự chứng minh toàn bộ thao tác trung gian. Không mở browser mới trong lượt review.
- PID26176 không tồn tại, cổng59272 không listen, temp-root $USER_HOME\AppData\Local\Temp\w05-local-v8891g1q không còn, được kiểm trực tiếp lượt này. Summary SQLite được đọc, không mở DB gốc lại ở lượt này.

## Lệch giới hạn cần quyết định

Leader tái hiện trực tiếp `_product`: 128 hợp lệ; 256 bị CvesUnavailable('invalid text'). Capture worker ghi technology PUT200 nhưng dataset product256 làm status GET503. Tuy nhiên docs/specs/W03-read-local-contract.md ghi affected vendor/product tối đa128, còn W04-technology-local-contract.md ghi product256; status context cũng256. Vì vậy đây là lệch giữa hợp đồng và tiêu chí tích hợp, chưa đủ kết luận riêng loader vi phạm hợp đồng đã nhận.

Giao Research đọc đúng ref và nghiên cứu đã có, xác định cần mở W03 lên256 hay giới hạn128 có lý do; trả quyết định đề xuất cùng brief sửa tối thiểu nếu cần. Không tự giảm tiêu chí E1 hoặc sửa product để làm test xanh. Thử import riêng đầu tiên thiếu core trên PYTHONPATH; đã sửa môi trường trong review_stage_a.py và tái hiện thành công, không coi lỗi import là lỗi sản phẩm.

## Nối việc

Engineer giữ thread/tree hiện có, chỉ chặng B unknown-outcome browser cùng trang. Research chỉ đọc cùng SHA và ghi báo cáo riêng; không viết source. Một writer/tree, chỉ Engineer dùng browser. Giữ toàn bộ accepted_results cũ; chấp nhận báo cáo chặng A không nâng thành W03-S1 đã xong. Lịch tiếp tục vẫn bật, dự án active; mobile/feed/OpenCTI/lab/production/model thật chưa kiểm.
