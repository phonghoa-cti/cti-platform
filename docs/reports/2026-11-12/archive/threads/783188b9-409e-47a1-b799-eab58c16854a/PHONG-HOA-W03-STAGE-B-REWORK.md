# Chặng B — đóng điểm chưa quan sát

CTI Engineer Sol medium giữ thread/tree integration d099293; không worker con. Giữ evidence B cũ. B chưa đạt hết vì thiếu khóa ghi sau đóng/mở khi GET200 chưa đến; không lặp cùng cách chụp đua tốc độ.

Thay đổi nhỏ được phép trong tools/local_integration/**: thêm scenario riêng hoặc override test-only dùng W03_FAIL_STATUS_GET_COUNT=2 cho unknown-outcome (giữ scenario cũ nếu cần tránh đổi matrix cũ). Một PUT503 sau commit → GET503 tự động → đóng/mở panel → GET503 lần2, chụp snapshot/ảnh khóa select/textarea/nút ghi còn giữ sau mở lại → chỉ bấm GET đối soát → GET200. Không dùng sleep/delay tùy ý hoặc sửa UI/product. Counter phải gắn exact relation, GET history/relation khác không tiêu thụ.

Focused tests cho scenario mới/count/trace, không lặp full suites. Một browser run bằng Browser OpenMausBot; trace đúng1PUT, DB1record/1audit, không reload. Ảnh/snapshot trước-sau và trạng thái trung gian quan sát được; không suy từ component. Cleanup PID/port/temp-root. Giữ base product128 hiện hành; Backend đang sửa product tree riêng, chưa ghép.

Allowlist tools/local_integration/**, docs/PROGRESS.md ghi phạm vi evidence; không Backend/UI/deps/lockfile hoặc RUNS. Commit local sạch nếu sửa; report $THREADS\783188b9-409e-47a1-b799-eab58c16854a\PHONG-HOA-W03-STAGE-B-REWORK-RESULT.md, evidence mới w03-status-stage-b-rework. Chỉ làm ca này rồi trả; không push/PR/merge/deploy/lab/cloud/thật. Đây là cách kiểm có điều khiển thay cho đua tốc độ lần trước, không lặp retry cũ.
