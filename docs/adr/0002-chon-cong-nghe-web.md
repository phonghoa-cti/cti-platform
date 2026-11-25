# ADR 0002 — Công nghệ cho portal

- Ngày: 22/10/2026
- Trạng thái: **Đề xuất** (chờ nhóm duyệt)

## Bối cảnh
Portal cần: nhiều màn hình, biểu đồ, hai ngôn ngữ, chạy tốt trên điện thoại, phân quyền; nhóm code chủ yếu nhờ AI agent,
có một bạn quen web. Logic CTI (chuẩn hóa, chấm điểm) đã viết bằng Python trong `phonghoa_core`.

## Các phương án
| Phương án | Ưu | Nhược |
|---|---|---|
| A. **Next.js + Tailwind + shadcn/ui** (giao diện) + **FastAPI** (API) | Agent viết React/Next.js rất tốt; giao diện đẹp, chuyên nghiệp; i18n và responsive có sẵn công cụ; API Python dùng lại `phonghoa_core` | Hai ngôn ngữ (TypeScript + Python); thêm một container |
| B. Streamlit | Rất nhanh, chỉ Python | Giao diện "đồ án", khó tùy biến, phân quyền và i18n yếu, khó làm tốt trên điện thoại |
| C. FastAPI + Jinja + HTMX | Một ngôn ngữ, nhẹ | Ít mẫu sẵn; agent ít kinh nghiệm hơn; biểu đồ và tương tác phức tạp tốn công |

## Quyết định (đề xuất)
Phương án A. Thư viện phụ: `next-intl` (đa ngôn ngữ), `recharts` (biểu đồ), `lucide-react` (icon), `@tanstack/react-query` (gọi API),
Playwright (test giao diện). Backend: FastAPI, `pycti`, SQLModel + SQLite, pytest.

## Hệ quả
- Tốt: sản phẩm trông chuyên nghiệp khi demo; frontend/backend làm song song nhờ `api-portal.md`.
- Xấu: thành viên phải đọc được cả TypeScript và Python → mỗi PR bắt buộc có mục "Giải thích cho người mới".
- Giảm thiểu: frontend dùng dữ liệu giả (mock) theo đúng hợp đồng API cho tới khi backend xong.
