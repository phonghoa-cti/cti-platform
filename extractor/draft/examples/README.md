# Mẫu hợp đồng draft đã lưu

Ba file JSON trong thư mục này là kết quả `get` thật từ store SQLite hiện tại trên Python 3.12.13. Dữ liệu đều
tổng hợp, không lấy từ feed/báo cáo thật và không chứa secret.

| File | Tình huống | Ghi chú |
|---|---|---|
| `01-regular.json` | Draft thường | Có emoji/chữ Việt trước IOC, một item kept và span code point. |
| `02-warning-allowlist-rejected.json` | Cảnh báo + allowlist + rejected | Hai findings từ scanner; `google.com` bị bỏ chọn theo allowlist. Item `missing.example` được **thêm thủ công vào fixture đầu vào** để kiểm hợp đồng rejected, không phải kết quả regex tự trích. |
| `03-empty.json` | Draft rỗng | `text=""`, `items=[]`; không có IOC không có nghĩa nội dung an toàn. |

Đây là hình dạng **đã lưu**, nên mỗi file có `id` và `created_at` do store tạo. Không đưa nguyên file trở lại
lệnh `save`: đầu vào save phải bỏ hai trường store quản lý này. UI/mock có thể đọc trực tiếp các file để kiểm
render, nhưng không được suy ra endpoint HTTP đang tồn tại.

Mỗi mẫu đã được kiểm:

- JSON parse thành công;
- `source.sha256 == sha256(text.encode("utf-8"))`;
- mọi span khác null cắt đúng `evidence` theo code point Python;
- payload sau `get`, bỏ `id/created_at`, bằng đúng payload trước `save`;
- fixture warning bảo toàn item kept, allowlist, rejected và findings;
- không có `kind` ngoài `ioc` trong dữ liệu đã chạy.

Hợp đồng đầy đủ và giới hạn tích hợp: [`docs/specs/W05-draft-offline-contract.md`](../../../docs/specs/W05-draft-offline-contract.md).
