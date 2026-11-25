# Leader review Frontend W04 — 11/11/2026

**FAIL, chưa nghiệm thu Frontend `be131133da7b63a3054da032ed1ab8a85af48bc6`.** Backend `90b26287` vẫn giữ nghiệm thu cục bộ trước đó.

Đúng base `aeff542a20ecc6fe436a0884801fdd69ab0435f6`, HEAD/tree sạch. Đã đọc component AssetsApp, adapter, các test hành vi, diff parser/view W02 và schema Backend. Delta 39 file +2720/-5 gồm 20 file sản phẩm/tài liệu và log/evidence; không sửa Backend. Báo cáo worker thực tế nằm trong `cti-w04-assets-frontend/`, không phải root như brief ban đầu; giữ nguyên đường dẫn thực tế, không di chuyển.

Worker báo 222 tests, lint/typecheck/build đạt; Leader không lặp toàn suite khi đã có finding cần sửa. Kiểm độc lập bằng Vitest có sẵn, cấu hình/probe ở thư mục bằng chứng này, import source target không chỉnh sản phẩm: **5 failed / 1 passed (6), exit 1**. `verification.json` ghi đúng HEAD và tree sạch sau kiểm. Lần khởi tạo probe đầu lỗi setup path, không có test chạy; giữ `runner-setup-error.txt/xml`, đã sửa cấu hình runner ngoài sản phẩm rồi mới chạy RED thật ở `leader-regressions-red.txt/xml`.

| Finding | Bằng chứng | Hệ quả / sửa |
|---|---|---|
| F1 created_by bound 253 thay vì 512 | 254/512 FAIL, 513 reject PASS; schema Backend max512 | Response hợp lệ bị từ chối; nới riêng created_by đúng hợp đồng |
| F2 gateway 503 khi mutation thành unavailable | POST upstream_unavailable expected unknown-mutation, actual unavailable | Chưa biết đã ghi hay chưa nhưng UI báo lỗi lưu thông thường; phân biệt lỗi Backend chắc chắn rollback với lỗi gateway/không rõ |
| F3 stale refresh ghi notice lên tab mới | Create/delete thành công, refresh chờ, đổi tab IP, refresh cũ reject; hai FAIL | Bảng IP giữ đúng nhưng notice cũ xuất hiện; kiểm context sau await refresh |

Không có bằng chứng tự gửi lặp mutation ở candidate. F2 là sai phân loại unknown outcome; không khẳng định dữ liệu đã bị ghi lặp. Chưa chạy browser/real HTTP cho Frontend, nên không coi component tests là bằng chứng toàn luồng.

Sửa theo `PHONG-HOA-W04-FRONTEND-REWORK-20261111.md`, cùng owner/thread/tree. Để tăng tốc, Engineer chuẩn bị gateway/runner/HTTP trên tree riêng từ Backend đã nghiệm thu theo `PHONG-HOA-W04-INTEGRATION-PREP-BRIEF-20261111.md`. Chưa tích hợp UI candidate lỗi; chỉ giao bước nối sau khi cả Frontend và prep đạt.

Đã đọc hai lịch nối việc: enabled, dự án active, giữ nguyên. Không push/merge/deploy/lab/secret hoặc thêm reviewer trùng.
