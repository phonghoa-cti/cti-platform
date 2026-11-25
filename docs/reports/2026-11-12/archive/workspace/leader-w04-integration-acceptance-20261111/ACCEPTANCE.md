# W04 domain/CIDR — nghiệm thu tích hợp cục bộ

Ngày 11/11/2026. Leader kiểm callback `391c163e-4cb7-44ca-bb93-0b58afdfc2e4` sau lần phục hồi lượt bị dừng. Kết luận: **PASS lát cắt domain/CIDR cục bộ**, gồm bằng chứng browser desktop. Không phải hoàn thành toàn bộ W04 hoặc Phong Hỏa.

## Mã và phạm vi

- Tree `cti-w04-local-integration`, HEAD `8a767314b654d39c1ddc2995b7919c44a5b7027a`, sạch khi kiểm sau chạy lại.
- Base prep `652545688fb5dd7bb4fe974c597fed370e9ad0f0`. Ba cherry-pick Frontend giữ đúng thứ tự; cây `portal/web` tại `1aeedc4` trùng nguồn đã nghiệm thu `fd04f95e`.
- Commit tích hợp `59d679e0949fea5ece953645cd6b80303546b43a`: 12 file +388/-4. Tính thêm báo cáo cuối: 13 file +446/-4, đúng phạm vi wrapper/route/harness/tests/docs. `core` và `portal_api` không đổi so với prep. `git diff --check` exit 0.
- `/tai-san` dùng adapter HTTP hiện có; quản lý tài sản và tra cứu dùng chung SQLite/AssetStore. Giữ nguồn mẫu riêng, không thêm JWT/role ở client.

## Leader kiểm độc lập trong lượt này

- Chạy lại ma trận HTTP trên đúng HEAD: **71 assertion PASS, exit 0**, gồm quyền, CRUD, tra cứu cùng DB, refresh 503→200 và mất phản hồi sau commit. Raw: `fresh-http-matrix.json`, `fresh-http-matrix.log`, `fresh-http-exit.json`.
- Kiểm SHA-256 **53/53 artifact**, không thiếu/khác nội dung. Manifest gốc SHA-256 `5da03a25fca8ae9f754abe71184217208065d760de2f5a53ac10ff95e997889b`; bao gồm 52 file evidence và báo cáo trong tree.
- Đọc trực tiếp sáu SQLite backup bằng chế độ chỉ đọc, đối chiếu summary và trace. CRUD: 2 row, 1 active, 4 audit; POST×2, PUT×1, DELETE×1. Forbidden: POST403, 0 asset/0 audit. Các run lỗi: 1 asset/1 audit và đúng một POST.
- Hai run bấm tải lại có trace chính xác: refresh `GET200, POST201, GET503, GET200`; unknown outcome `GET200, POST503, GET200`. Trace chỉ có counter/method/path/status; không suy số request từ screenshot.
- Xem trực tiếp sáu ảnh: không có quyền; lookup sau xóa mất nhãn tài sản; refresh lỗi và thành công; chưa rõ kết quả và đối soát thành công. Ảnh 1280×720, phù hợp trace/SQLite và quan sát browser của Engineer. Leader không chạy lại toàn bộ browser; nghiệm thu dựa trên bằng chứng browser đã trả, kiểm ảnh/dữ liệu độc lập và chạy mới HTTP.
- Sáu state đều stopped, port đóng và temp root đã xóa theo trạng thái cleanup; kiểm hiện tại không còn Python helper W04. Phép HTTP mới cũng dọn sạch temp/port.
- `artifact-verification.json` ghi chi tiết kiểm hash/cây mã/trace/SQLite. Lần đầu checker của Leader giới hạn đường dẫn manifest trong evidence; đã sửa để chấp nhận đúng báo cáo được khai báo ở tree bên cạnh, không sửa artifact sản phẩm.

## Bằng chứng worker được đối chiếu, không chạy lặp

Log và exit artifact mới của Engineer: frontend 150/150; typecheck/lint/build exit 0 (có `/tai-san`); gateway 13/13; harness/helper 34/34; Ruff exit 0. Các file nằm trong manifest đã kiểm. Không lặp Backend55/99, full portal hoặc frontend222 đã nghiệm thu trước.

## Giới hạn và bước nối

Mobile 360px chưa kiểm do bề mặt browser chưa có resize; giữ task responsive đang blocked. Công nghệ, thương hiệu/từ khóa, CSV của W04 còn thiếu. W03 CVE, OpenCTI, Cloudflare/JWKS/HTTPS thật, lab, feed/LLM và production chưa được chứng minh bởi lát cắt này. Không push/PR/merge/deploy.

Bước tiếp theo đủ điều kiện: nghiên cứu lát cắt công nghệ của W04 (nhà cung cấp/sản phẩm/phiên bản) để mở đầu vào cho W03 theo spec. Phiên bản chỉ hiển thị cho người kiểm; không mở rộng sang đối chiếu phiên bản tự động. Dùng nghiên cứu W04 hiện có, nghiên cứu phần mới trước khi giao triển khai.
