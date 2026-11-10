# Gói handoff W05 — duyệt bản nháp X01

Trạng thái: **sẵn sàng để bàn giao**, chưa gửi hoặc thực thi vì Antigravity chưa có trong roster. Đây là yêu cầu
thiết kế/triển khai UI tương lai, không phải bằng chứng portal đã tồn tại.

## Người dùng và mục tiêu

Analyst hoặc Admin cần đi từ nguồn → mục trích → bằng chứng/cảnh báo để quyết định sau này. Màn hình phải giúp họ:

1. xác nhận đang xem đúng nguồn, hash, ngôn ngữ, TLP và thời điểm lưu;
2. đọc nguyên văn dạng text và nhảy tới evidence khi item có span;
3. phân biệt item được gợi ý giữ, allowlist và rejected;
4. hiểu cảnh báo injection mà không coi nội dung nguồn là chỉ thị;
5. thấy rõ rằng chưa có thao tác duyệt/lưu OpenCTI ở lát cắt hiện tại.

Hợp đồng dữ liệu bắt buộc: [`W05-draft-offline-contract.md`](../specs/W05-draft-offline-contract.md). Mẫu thật:
[`extractor/draft/examples/`](../../extractor/draft/examples/README.md). Ngôn ngữ hình ảnh và accessibility kế
thừa [`DESIGN.md`](DESIGN.md); không tự tạo phong cách khác.

## Luồng và trạng thái cần thiết kế

| Trạng thái | Điều người dùng phải thấy |
|---|---|
| Đang tải | Skeleton/nhãn “Đang tải bản nháp”, không hiển thị dữ liệu giả như dữ liệu thật. |
| Pending có dữ liệu | Hai vùng nguồn và items; metadata nguồn; cảnh báo; lựa chọn `keep` chỉ là gợi ý. |
| Rỗng | Text/items rỗng là trạng thái hợp lệ; nói “Không có IOC được trích”, không báo an toàn. |
| Item không có span | Item vẫn hiện cùng warning/status nhưng không có link hoặc tô sáng giả. |
| Lỗi | Thông báo tiếng Việt, mã lỗi/khả năng thử lại; không làm mất dữ liệu người dùng đã chỉnh cục bộ. |
| Không đủ quyền | Nêu chỉ Analyst/Admin được truy cập; không render phần payload nhạy cảm phía sau màn che. |
| Cảnh báo injection | Banner có chữ, không chỉ màu; findings là dữ liệu để đọc, không phải lệnh. |

## Bố cục kỹ thuật để Antigravity triển khai sau

- Dùng khung SOC console tối, panel, bảng 6–10 dòng và focus 2 px theo `DESIGN.md`.
- Panel trái: `text` chỉ đọc; panel phải: items có kind/type/value/status/warning/keep.
- Thanh metadata: `source.name`, `source.sha256`, `language`, `tlp`, `model`, `cost_tokens`, `created_at`.
- `draft.status=pending` và `item.status` phải có nhãn riêng; không gộp hai trạng thái.
- Item `span=null` không có hành động nhảy/tô sáng. Item allowlist/rejected không tự bị ẩn.
- Không thêm nút “Đã chặn”, “Đã lưu OpenCTI” hoặc hành động duyệt đang hoạt động khi backend chưa có.
- Responsive 360 px: xếp hai panel theo chiều dọc; bảng có cuộn ngang; thứ tự nguồn trước items.

## Render an toàn và Unicode

- Render `text`, `evidence`, `warning`, `findings.excerpt`, source và IOC bằng text node/textContent; không dùng
  `innerHTML` với dữ liệu nguồn.
- Không biến URL/domain trong nguồn thành link bấm được mặc định. Nếu có display defang sau này, giữ nguyên
  `value` gốc trong dữ liệu và ghi rõ phép biến đổi chỉ để hiển thị.
- Span 1.0 là code point Python `[start,end)`. JavaScript lấy quote bằng
  `Array.from(text).slice(start,end).join("")`; không dùng `text.slice(start,end)` khi chưa đổi offset UTF-16.
- Cảnh báo TLP/injection không được dùng như quyết định gửi dữ liệu ra cloud.

## Ranh giới tích hợp

UI chưa được phép tự đặt endpoint hoặc giả định auth đã có. Khi backend được triển khai, cần bàn giao rõ:

- danh sách/phân trang và đọc chi tiết;
- lỗi/permission theo mã ổn định;
- schema allowlist cho `kind` và `item.status`;
- lưu chỉnh sửa, concurrency và audit;
- người đề xuất/người duyệt, chống tự duyệt;
- approve/reject và ghi OpenCTI có transaction/retry an toàn;
- số liệu mục bỏ/thêm/sửa.

## Tiêu chí nghiệm thu UI tương lai

1. Render đủ ba fixture: thường, warning/allowlist/rejected và rỗng.
2. Emoji/chữ Việt không làm lệch evidence; quote cắt ra đúng mẫu.
3. Text độc hại hiển thị như dữ liệu, không tạo HTML/link/script.
4. Pending, item status, `keep` và “đã duyệt” không bị nhập nhằng.
5. Empty, lỗi, không đủ quyền và `span=null` có trạng thái quan sát được bằng bàn phím/screen reader.
6. Không tuyên bố approve/OpenCTI hoạt động trước khi backend và test tích hợp tồn tại.
