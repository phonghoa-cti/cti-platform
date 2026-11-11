# ADR 0011 — Nạp TXT/PDF cục bộ bằng snapshot và child hữu hạn

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh

C1 hiện nhận text nhưng X01 cần lát nhỏ nhận file TXT/PDF mà không đổi shape
draft, không gọi model/mạng và không ghi thẳng OpenCTI. PDF là dữ liệu không
tin cậy; parser có thể treo hoặc dùng nhiều tài nguyên.

## Các phương án

1. Chỉ TXT bằng thư viện chuẩn: ít dependency nhưng chưa đáp ứng PDF.
2. `pypdf` pin/hash trong một Python child: hỗ trợ lớp text, giữ runtime nhỏ.
3. Poppler/Tika: thêm binary/JVM và contract subprocess lớn hơn lát cắt.

## Quyết định

Chọn phương án 2. Parent đọc một bản bytes có cap để băm, ghi snapshot private
và chỉ truyền snapshot cho đúng một child. Child sở hữu toàn bộ `pypdf`; parent
áp timeout, reap, cap kết quả, strict JSON/schema rồi tự kiểm lại page/text
limits và dựng canonical text/range.

TXT giữ nguyên UTF-8 BOM/newline. PDF giữ nguyên text từng trang do parser trả
về, nối bằng `"\n\f\n"`; range là chỉ số Unicode trong canonical text, không
phải byte hay tọa độ PDF. Envelope bọc draft C1 `pending` không đổi shape.

Output được ghi vào temp cùng thư mục, flush+fsync rồi publish đúng một lần bằng
`os.link`; không overwrite/fallback. Nếu dọn temp lỗi sau publish, output hợp lệ
được giữ và CLI trả `output_cleanup_failed`.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: hash/parser cùng một snapshot; output deterministic/no-clobber; lỗi đóng.
- Tốt: không import parser PDF ở parent, không OCR/decrypt/converter/model/mạng.
- Xấu: timeout không phải hard RAM limit hay network sandbox; child vẫn cùng host.
- Xấu: text PDF không chứng minh đầy đủ nội dung, layout hoặc chất lượng PDF thật.
- Giảm thiểu: cap raw/page/text/result, terminate→reap→kill→reap, fixture tổng
  hợp và người duyệt trước mọi hành động ghi tiếp theo.
