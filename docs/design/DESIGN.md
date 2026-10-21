# DESIGN.md — Ngôn ngữ thiết kế của Phong Hỏa (SOC console)

Agent viết giao diện (portal-web) PHẢI đọc file này trước. Nhóm đã chọn hướng **SOC console tối** (22/10/2026).
Mockup tham chiếu: canvas "Phong Hỏa — Mockup portal" — W01 Tổng quan, W02 Điều tra IOC.

## Nguyên tắc
1. **Là công cụ làm việc, không phải trang giới thiệu:** dày thông tin, mọi khối đều trả lời một câu hỏi vận hành.
2. **Mỗi khối là một panel** có thanh tiêu đề: tên + ngữ cảnh (khoảng thời gian, độ mới) + hành động phụ ("Xem tất cả").
3. **Biết dữ liệu có đủ không:** luôn có panel "Tình trạng nguồn dữ liệu"; nguồn hỏng phải hiện rõ, không để màn hình yên ắng trông như an toàn.
4. **Mức độ luôn có chữ** (Cao / Trung bình / Thấp) kèm màu; không chỉ dùng màu.
5. **Số liệu và IOC dùng font mono**, căn phải trong bảng.
6. Không trang trí vô nghĩa: không bản đồ thế giới để cho đẹp, không gradient, không hiệu ứng chuyển động khi tải.

## Màu (lớp nền tối dần lên sáng)
| Token | Hex | Dùng cho |
|---|---|---|
| background | `#0D141D` | Nền trang |
| sidebar | `#0A1017` | Thanh điều hướng trái |
| layer-01 | `#131C27` | Nền panel |
| layer-02 | `#1A2533` | Hàng tiêu đề bảng, ô nhập |
| border-subtle | `#1F2B3A` | Viền panel, đường kẻ hàng |
| border-strong | `#3A4A5E` | Gạch chân ô nhập, viền nút phụ |
| text-primary / secondary / helper | `#E6EDF4` / `#A3B1C2` / `#8193A8` | Chữ |
| interactive | `#0F62FE` (nút chính), liên kết `#78A9FF` | Hành động |
| brand | `#F26B3A` | Chỉ logo lửa, ô nhiệt ATT&CK cao nhất |
| Cao | nền `#4D1216`, chữ `#FFB3B8`, nét `#FA4D56` | |
| Trung bình | nền `#3A2E06`, chữ `#F1C21B` | |
| Thấp / trung tính | nền `#26354A`, chữ `#C3CFDC` | |
| Tốt | nền `#0E3B22`, chữ `#6FDC8C`, chấm `#42BE65` | Nguồn hoạt động, TLP:GREEN |
| Chuỗi dữ liệu | URL `#4589FF`, Tên miền `#A56EFF`, IP `#08BDBA`, Hash `#6F7F92`, Mã độc `#EE5396` | Thống nhất mọi biểu đồ |

## Chữ — thang "productive" (theo IBM Carbon)
**IBM Plex Sans** (có tiếng Việt) cho giao diện, **IBM Plex Mono** cho IOC, thời gian, mã kỹ thuật. Bật `font-variant-numeric: tabular-nums`.
| Vai trò | Cỡ / dòng | Đậm | Giãn chữ |
|---|---|---|---|
| Nhãn, chú thích, tag | 12 / 16 | 400 | 0.32px |
| Thân, ô bảng | 14 / 18 | 400 | 0.16px |
| Tiêu đề panel, tiêu đề cột | 14 / 18 | 600 | 0.16px |
| Giá trị trong ô tóm tắt | 16 / 22 | 400 | 0 |
| Tiêu đề trang | 28 / 36 | 400 | 0 |
| Số KPI | 32 / 40 | 300 | 0 |

## Khoảng cách — lưới 8 (2, 4, 8, 12, 16, 24, 32, 48)
Lề trang 24 · giữa các panel 16 · đệm trong panel 16 · giữa nhãn và giá trị 4–8.

## Kích thước component
| Component | Quy cách |
|---|---|
| Thanh trên cùng | cao 48 |
| Mục sidebar | cao 32, mục đang chọn có vạch xanh 3 px bên trái |
| Header panel | cao 48: tiêu đề + chú thích + hành động bên phải (nút ⋮ 32×32) |
| Hàng bảng | 40 (thường), 32 (gọn); hàng tiêu đề nền layer-02; chân bảng phân trang cao 40 |
| Nút | 40 (chính, phụ), 32 (trong thanh công cụ); góc vuông |
| Ô nhập | cao 32–40, nền layer-02, gạch chân border-strong |
| Tag mức độ | cao 24, bo tròn 12, chữ 12 |
| Tab | cao 48, gạch dưới 2 px xanh cho tab đang chọn |

## Mật độ
Mỗi màn tối đa 6–8 khối. Các panel cùng hàng phải cao bằng nhau (flex `align-items: stretch`) để không có khoảng trống thừa.
Bảng hiển thị 6–10 dòng kèm phân trang thay vì kéo dài vô tận.

## Khung trang
- Sidebar trái 224–240 px, nhóm: Giám sát (Tổng quan, Cảnh báo, Điều tra IOC) · Tri thức (Báo cáo, Ma trận ATT&CK) · Rủi ro (Lỗ hổng, Tài sản) · Vận hành (Hàng chờ duyệt, Nguồn dữ liệu). Huy hiệu số đếm cho mục có việc chờ.
- Thanh trên 48 px: đường dẫn trang, ô tìm kiếm toàn cục (Ctrl K), chọn khoảng thời gian, trạng thái tự làm mới, mức đe dọa.
- Nội dung: khoảng cách giữa panel 16 px; hàng bảng 40 px.

## Thành phần chuẩn
KPI có sparkline · biểu đồ cột chồng theo giờ · hàng đợi xử lý có người phụ trách và hạn (SLA) · ma trận ATT&CK dạng nhiệt ·
bảng IOC trực tiếp (thanh điểm + màu) · bảng tình trạng nguồn · màn điều tra: đầu trang thực thể + tab + thành phần điểm + đồ thị quan hệ + dòng thời gian + làm giàu + ghi chú + STIX thô.

## Chất lượng tối thiểu
Tương phản đạt WCAG AA trên nền tối; focus nhìn thấy (viền `#78A9FF` 2 px); dùng được ở 360 px (sidebar xếp lên trên, bảng cuộn ngang);
`prefers-reduced-motion`; mọi bảng có tiêu đề cột; mọi biểu đồ có `aria-label` mô tả nội dung.
