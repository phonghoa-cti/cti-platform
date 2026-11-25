# W03-S1 — chặng B: phục hồi unknown trong cùng trang

Một CTI Engineer, Sol medium trực tiếp, không worker con. Tiếp tục thread b05471df-3a0c-49c0-b02b-4019e1cf15d4; không tạo tree khác hoặc sửa RUNS.

TREE=$WORKSPACE\cti-w03-status-integration
HEAD=d09929311b4b6447aac8b2ec6adac5999beda25d
BRANCH=feat/w03-status-integration-20261112
OUT=$THREADS\783188b9-409e-47a1-b799-eab58c16854a

Đọc AGENTS, docs/PROGRESS, docs/specs/W03-status-local-contract.md và OUT/PHONG-HOA-W03-STAGE-A-REVIEW.md. Kế thừa nghiên cứu S1 và helper đã kiểm; không chạy lại chặng A/capture/build/full suite mặc định. Product128/256 do Research đọc riêng; không sửa hoặc đợi nghiên cứu đó để kiểm scenario synthetic FortiOS hiện hành.

## Một ca cần làm

1. Dùng Browser tab OpenMausBot được cấp và helper scenario w03-status-unknown-outcome. Kiểm trạng thái/công cụ trước; không chuyển sang host browser hoặc automation khác. Chỉ helper loopback dữ liệu tổng hợp hiện có.
2. Ghi một thay đổi trạng thái; helper trả PUT503 sau upstream commit, rồi GET503. Lưu ảnh và snapshot thể hiện thông báo chưa rõ kết quả, form/nút ghi bị khóa trước đối soát. Ghi nguyên văn trạng thái disabled/read-only và số bước nếu bề mặt cung cấp.
3. Đóng/mở panel hoặc A→B→A trong cùng trang. Lưu bằng chứng khóa ghi còn giữ qua việc chuyển này trước GET200; không reload cả trang. Nếu quá nhanh để lấy trạng thái trung gian, ghi chính xác điểm chưa quan sát, không suy từ ảnh cuối.
4. Chỉ GET đối soát tới200; chụp record v1 và thông báo tương ứng. Không suy PUT thành công từ GET, không tự gửi PUT lại. Trace cuối đúng một PUT, SQLite đúng một status/một audit. Ghi initial/final DB, trace và cách tái chạy.
5. Dừng helper thuộc lượt mình; lưu PID/cổng/temp-root trước và xác nhận sau cleanup. Giữ command exit code thật, không đợi vô hạn; tối đa hai lần cùng lỗi, báo blocker cụ thể nếu không làm được.

Đầu ra OUT/PHONG-HOA-W03-STAGE-B-RESULT.md và OUT/w03-status-stage-b-evidence/ gồm manifest SHA256, ảnh, snapshot, trace, DB và cleanup; báo PASS/FAIL/UNVERIFIED từng tiêu chí. Trả ngay sau ca này, không chờ hoặc tự nhận việc khác.

Mặc định không sửa source, HEAD phải sạch/không đổi. Nếu helper bắt buộc sửa, chỉ tools/local_integration/** với focused test và commit nhỏ; không product Backend/Frontend, deps/lockfile, S2, push/PR/merge/deploy, lab, feed/cloud/LLM thật, secret, quyền hay chi tiền. Không ghi đè evidence cũ. Chặng B đạt vẫn chưa làm toàn tích hợp đạt nếu quyết định product128/256 chưa đóng.
