# Portal web — W05 review selection

## W02 — Tra cứu IOC mẫu

`/tra-cuu/mau` là view tra cứu một IOC bằng dữ liệu tổng hợp có nhãn rõ. Route không gọi mạng; nguồn dữ liệu
fixture triển khai qua `LookupDataSource` để bước sau thay bằng adapter HTTP đã được chốt hợp đồng. Giá trị không
khớp fixture luôn trả “không tìm thấy”, không được coi là an toàn và không được frontend tự chấm điểm hay
chuẩn hóa. Fixture có sẵn: `hxxp://Evil[.]COM/a` và `allowlisted.example`.

View này chưa có API, xác thực, OpenCTI, enrichment thật, lịch sử, batch, đề xuất chặn hoặc dữ liệu vận hành.

`/tra-cuu` gắn adapter HTTP qua client wrapper ổn định và gửi đúng một `GET /api/ioc?value=...`
cùng origin, không tự thêm danh tính, giới hạn phản hồi 1 MiB và timeout 10 giây cho cả fetch lẫn đọc body.
Parser chỉ nhận schema W02 exact; lỗi mạng, HTML, JSON sai hoặc contract không khớp đều thành trạng thái nguồn không
khả dụng, không fallback sang fixture. Nhãn route nói rõ dữ liệu tổng hợp cục bộ và chưa kết nối OpenCTI;
`/tra-cuu/mau` vẫn giữ nguồn mẫu không gọi mạng.

`/duyet` đọc hàng đợi API v1, cho analyst chỉnh tập IOC đủ điều kiện, bấm **Lưu lựa chọn**, rồi duyệt hoặc từ
chối đúng snapshot đã lưu. `savedSelection` là tập server đã ghi; `editingSelection` là tập analyst đang sửa.
Nút lưu là ranh giới rõ ràng để quyết định không vô tình dùng một tập khác với tập đang hiển thị.

`/duyet/mau` vẫn là ba bản nháp tổng hợp X01 có nhãn dữ liệu mẫu. Route mẫu không gọi API ghi, không xác thực
và không nối OpenCTI. Gateway v1 và luồng trình duyệt same-origin được kiểm ở bước tích hợp riêng.

## W04 — Tài sản mẫu

`/tai-san/mau` quản lý hai loại tài sản tổng hợp là tên miền và dải IP trong bộ nhớ của phiên xem thử. Màn hình
có thêm/sửa/xóa, xác nhận trước khi xóa, kiểm tra nhập liệu tiện dụng, trạng thái tải/rỗng/lỗi/quyền/xung đột và
khóa gửi lặp. Nhãn trên trang nói rõ thay đổi không phải dữ liệu vận hành và không tồn tại sau khi tải lại ứng dụng.

`AssetsDataSource` tách view khỏi nguồn dữ liệu. Provider mẫu không gọi mạng; adapter HTTP gọi cùng origin
`/api/assets`, không tự thêm JWT/role, không retry mutation và dùng `expected_version` khi sửa/xóa. Nếu mutation
thành công nhưng GET làm mới thất bại, giao diện chỉ cho tải lại danh sách; nếu mất kết nối trong mutation, giao
diện coi kết quả chưa rõ và không gửi lại. Route API thật, gateway, xác thực và database sẽ được nối ở bước tích
hợp sau khi Backend được nghiệm thu.

Parser W02 nhận `asset_match` ở cả `found`, `allowlisted` và `not_found`. Ba fixture phản hồi tổng hợp cùng một
fixture lỗi được sao chép nguyên byte từ gói Backend candidate đã được Leader đối chiếu SHA-256; đây là regression
schema, chưa phải bằng chứng API/backend hoặc browser toàn luồng đã chạy.

## Chạy cục bộ

Yêu cầu Node.js 22.12 trở lên (đã kiểm với Node.js 24.22.1).

```powershell
npm ci
npm run dev -- --port 3002
```

Mở `http://localhost:3002/duyet`; `/` tự chuyển tới route này. Dùng `/duyet/mau` khi chỉ cần xem fixture duyệt,
hoặc `/tai-san/mau` để thử quản lý tài sản tổng hợp.

## Kiểm tra

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Dữ liệu trong `data/fixtures/` là bản sao có chủ đích của ba fixture tổng hợp tại
`extractor/draft/examples/`. Adapter `data/draft-adapter.ts` chỉ phục vụ route mẫu; API mode dùng parser v1 exact,
không fallback sang fixture khi lỗi.
