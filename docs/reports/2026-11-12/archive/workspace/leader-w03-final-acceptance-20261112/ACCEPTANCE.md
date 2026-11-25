# Nghiệm thu W03-R cục bộ — 12/11/2026

**PASS LOCAL** tại `7ff6eb3af21d8de65836bfbf707396ae5690de0b`, tree `cti-w03-read-integration`, branch `feat/w03-read-integration-20261112`. Request cuối `ea0642c1-7fb0-43aa-87ac-ddf62a6a3cee` đã trả kết quả. Chỉ nghiệm thu tra cứu CVE với dữ liệu tổng hợp và trình duyệt desktop; chưa hoàn thành toàn W03 hoặc dự án.

## Leader đã đối chiếu

- HEAD đúng và status sạch. Từ R2 `9579d165` đến final: 4 file, +44/-1. Runtime đã chạy browser là `90af6d7a47a9bb9682a6ac7acd6b8ae6729aa986`; final chỉ bổ sung `docs/PROGRESS.md`.
- Backend `portal_api` bằng bản đã nghiệm thu `abcd14da`. Frontend runtime bằng `7ff62711`; khác biệt trong `portal/web` chỉ wire test R2 và fixture đi kèm. Không suy browser chạy trên commit tài liệu được tạo sau đó.
- Mở trực tiếp bốn ảnh: checked 3 CVE/3 KEV; unchecked 16 CVE/3 KEV; trang 1 có 10 mã, trang 2 có 6 mã; checked lại 3/3. Ba KEV đứng đầu. 16 mã duy nhất, đúng tập CVE-2026-2001 đến 2016; thứ tự trong metadata khớp ảnh. Metadata ghi tìm CVE-2026-2013 rồi bỏ lọc phục hồi 16; trace có bảy GET CVE tương ứng. Bằng chứng tìm kiếm không có ảnh riêng, không gộp thành kiểm ảnh độc lập.
- Đọc trace: 22 yêu cầu đều GET và 200, gồm 7 GET `/api/cves`; không có mutation.
- Mở hai SQLite bằng URI `mode=ro`, so schema và tất cả bảng/row: giống nhau. Hai file cùng SHA-256 `6cca76f8d6afc490303d89f38637370730b39725b46b6c66360037ca1fb4e7b1`. Có 2 technology và 2 technology audit trước/sau; không phát sinh audit khi lọc.
- Tính lại manifest mới: 13/13 khớp; SHA-256 `b3e9ddb8046f76e4f2f2d507a4b999d0828891e21bca5f14a9456e5dc441e165`. Bằng chứng gốc 42/42 và R2 14/14 vẫn nguyên hash, tổng 69 mục được kiểm.
- Trạng thái helper lưu tại `w03-filter-integration-evidence/browser-filter.json`: stopped, gateway port closed và temp root removed. Đây là bằng chứng cleanup của lượt chạy; không khởi động lại helper để kiểm lại luồng đã đạt.

## Tái sử dụng kiểm đã nghiệm thu

`leader-w03-rework-acceptance-20261112/ACCEPTANCE.md`: Leader đã chạy mới 53 focused frontend + 3 probe bộ lọc; 10 wire mặc định + 10 wire từ API capture mới; 120 HTTP/SQL assertions. Fixture thiếu/hỏng đều dừng trước test, không còn false PASS. Các file thực thi tương ứng không đổi sau đó, nên không lặp full suite.

Engineer báo chạy final tree: 53 focused + 10 wire + 3 probe, build exit 0 với 10 route. Leader không nhận các số này là một lượt chạy mới của mình. Bằng chứng browser summary/quyền, 409 tải lại, 503 phục hồi từ lượt tích hợp đầu đã được đối chiếu tại `leader-w03-integration-review-20261112/REVIEW.md`; mã liên quan không đổi.

R1 (bỏ Chỉ KEV vẫn phải chứa KEV) và R2 (fixture portable/preflight, coverage tạo/xóa match) đã đóng trên cùng tree. Nghiệm thu này thay trạng thái toàn luồng còn chờ trong các biên bản trước, không sửa lại lịch sử.

## Giới hạn và bước tiếp

Mobile 360 px, nguồn CVE/CISA/EPSS thật, OpenCTI, Cloudflare/JWKS/HTTPS, lab và production vẫn UNVERIFIED. Không push/PR/merge/deploy. Tên sản phẩm liên quan không chứng minh phiên bản cài đặt bị ảnh hưởng. Trạng thái xử lý/audit W03-S chưa triển khai.

Chọn W03-STATUS-NEXT: nghiên cứu bổ sung contract trạng thái theo từng cặp công nghệ/CVE, tái sử dụng phần W03-S của báo cáo cũ và các mẫu transaction/audit đã có. Chỉ ghi báo cáo; Leader chốt contract trước giao lập trình. Xem `PHONG-HOA-W03-STATUS-NEXT-BRIEF-20261112.md`.
