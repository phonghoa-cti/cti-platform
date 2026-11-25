# Browser evidence — W05 selection integration

Ngày 11/11/2026, Trình duyệt tích hợp được cấp, viewport thực của ảnh 1285×999; không resize hoặc mở browser khác.

## Happy path

1. Mở `/duyet` trong `selection-admin`: thấy 5 draft, draft selection có 2 IOC đã chọn (`01-happy-initial.png`).
2. Bỏ chọn `evil-one.example`: UI báo thay đổi chưa lưu; mọi nút chuyển draft và decision bị disabled. Thử chọn
   draft 4 không đổi draft hiện hành.
3. Bấm lưu: UI xác nhận 1 IOC đã lưu (`02-happy-saved.png`).
4. Bấm duyệt: hàng đợi 5→4, trạng thái `Đã duyệt`, thông báo rõ chưa nhập OpenCTI
   (`03-happy-approved.png`).
5. Run capture độc lập lặp đúng ba thao tác trên. `browser-happy-audit.json` cho thấy review version 2,
   selection version 1, đúng `[1]` và cùng hash ở selection/final audit; SHA-256 payload trước/sau bằng nhau,
   `items.keep` vẫn `[true,true]`.

## Empty, reject và sample

- `selection-empty`: bỏ chọn cả hai rồi lưu; UI hiện `0 IOC đã lưu`, approve disabled, reject còn khả dụng
  (`04-empty-saved.png`).
- `selection-reject`: nhập `Thiếu bằng chứng trình duyệt`, reject; queue 5→4 và hiện trạng thái từ chối cục bộ
  (`05-rejected.png`).
- `/duyet/mau`: có nhãn `Dữ liệu mẫu`, nguồn fixture ngoại tuyến, decision disabled và nội dung nói rõ không gửi
  request ghi (`06-sample-mode.png`). Test UI verbose xác minh không POST.

## Refresh fault tách run

- `selection-save-refresh-503`: save trả success, hai GET refresh trả 503; UI giữ `1 IOC đã lưu`, hiện nút tải
  lại và khóa decision (`07-save-refresh-503.png`).
- `selection-decision-refresh-503`: fixture bắt đầu từ snapshot v1; decision trả success, hai GET refresh trả
  503; UI giữ `Đã duyệt`, hiện cảnh báo tải lại và không lùi về pending (`08-decision-refresh-503.png`).
- Ma trận HTTP hậu kiểm mỗi fault chỉ có một selection event; fault save có 0 decision, fault decision có đúng
  1 decision. `ui-test-verbose.log` xác minh recovery chỉ GET và không replay POST.

### Retry được quan sát lại trên browser

- Trong run save-fault mới, bấm **Tải lại trạng thái** đúng một lần. Phần trace giữa marker trước/sau retry chỉ
  có hai GET 503; tổng run có đúng một POST selection và không có POST decision. Confirmation `Lựa chọn đã
  được lưu.` và snapshot `1 IOC đã lưu` vẫn còn.
- Trong run decision-fault mới, bấm **Tải lại trạng thái** đúng một lần. Phần trace giữa marker chỉ có hai GET
  503; tổng run có đúng một POST decision và không có POST selection. `Đã duyệt` và confirmation cuối vẫn còn.
- Audit SQLite được đọc trước close trong chính từng run. Raw trace/audit/cleanup và ảnh nằm ở
  `../rework-evidence/`.
- Run `/duyet/mau` riêng có trace chỉ chứa marker tải trang, không có request drafts legacy hay v1.

## Cleanup

`cleanup.log` cũ được giữ nguyên nhưng không còn được dùng để kết luận port đóng: mã Windows `10035` là
`WSAEWOULDBLOCK`, không phải connection refused (`10061`). Ba run rework ghi exact port/PID/temp trước và sau
close; sau close không còn listener trên các port đó, exact child PID không còn, API thread đã dừng và exact
temp path đã bị xóa. Xem `../rework-evidence/cleanup-correction.md` và ba file `*-run.json`.
