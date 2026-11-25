# W05 selection integration — R1/R2 rework evidence

Ngày 11/11/2026. Repo source không đổi; HEAD vẫn là
`d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`. Không chạy lại suite/build vì source không đổi.

## R2 — browser retry GET-only

Mỗi fault chạy trong một `LocalRun` mới và được thao tác bằng Trình duyệt tích hợp:

- `selection-save-refresh-503`: browser gửi đúng 1 `POST /api/v1/drafts/5/selection` (200). Hai GET refresh tự
  động trả 503. Giữa marker `before-retry` và `after-retry`, một lần bấm **Tải lại trạng thái** chỉ tạo
  `GET /api/v1/drafts/5` và `GET /api/v1/drafts` (đều 503), không thêm POST. UI vẫn hiện `1 IOC đã lưu` và
  confirmation `Lựa chọn đã được lưu.`. Audit cùng run: pending, review version 1, selection version 1,
  đúng một selection event `[1]`, không có decision.
- `selection-decision-refresh-503`: browser gửi đúng 1 `POST /api/v1/drafts/5/decision` (200), không có POST
  selection. Giữa hai marker, một lần retry chỉ tạo hai GET 503, không thêm POST. Sau retry UI vẫn hiện
  `Đã duyệt` và `Bản nháp đã được duyệt cục bộ; chưa nhập OpenCTI.`. Audit cùng run: approved, review version
  2, selection version 1, đúng một final decision; indices `[1]` và SHA-256 khớp selection snapshot.
- `/duyet/mau`: trang hiện `Dữ liệu mẫu`; trace riêng chỉ có marker `GET /__evidence_marker/after-load`, không
  có request legacy `/api/drafts...` hay v1 `/api/v1/drafts...`.

Raw trace: `save-refresh-retry-trace.jsonl`, `decision-refresh-retry-trace.jsonl`,
`sample-no-api-trace.jsonl`. Ảnh sau retry/load: ba PNG cùng thư mục.
Ba browser run cuối đều đóng bằng tín hiệu input bình thường và exit `0`; xem `exit-codes.json`.

## R1 — owned cleanup

Ba file `*-run.json` ghi trạng thái trước/sau close bằng OS listener table, exact PID và exact temp path. Cả ba
run đều có ba listener khớp owner trước close; sau close: `listeners=[]`, gateway/UI PID không còn, API thread
dừng, temp path không còn. Xem `cleanup-correction.md` cho correction của raw `cleanup.log` cũ.

## Kết luận

**PASS R1/R2 tại local browser/harness.** Không thay đổi repo, không tạo commit rỗng, không push/merge/deploy.
