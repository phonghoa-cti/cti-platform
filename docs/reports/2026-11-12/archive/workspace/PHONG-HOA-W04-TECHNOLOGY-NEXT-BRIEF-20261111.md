# W04-TECHNOLOGY-NEXT — nghiên cứu tài sản công nghệ để nối W03

CTI Research làm trực tiếp, chỉ nghiên cứu/đối chiếu; không triển khai, không giao thêm bot. Root `$WORKSPACE`.

## Mục tiêu và nền đã đạt

Chốt lát cắt nhỏ nhất để người dùng khai báo nhà cung cấp, sản phẩm và phiên bản phần mềm trong W04, làm đầu vào cho W03 Lỗ hổng ảnh hưởng. Nền chỉ đọc: `cti-w04-local-integration`, SHA `8a767314b654d39c1ddc2995b7919c44a5b7027a`. Domain/CIDR và browser local đã nghiệm thu tại `leader-w04-integration-acceptance-20261111/ACCEPTANCE.md`; không nghiệm thu lại các suite cũ.

Đọc AGENTS/PROGRESS, `docs/specs/W04-tai-san.md`, `W04-assets-local-contract.md`, `W03-lo-hong-anh-huong.md`, `api-portal.md`, `docs/backlog.json` trên đúng ref; tái dùng `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md` và brief Backend/Frontend đã có. Không chọn main/PR chưa nghiệm thu làm baseline. Đối chiếu PR đang mở nếu liên quan; ghi rõ ngày/ref và phần chưa kiểm.

## Câu hỏi cần chốt bằng nguồn và mã hiện có

1. Ai đã làm và thành phần nào dùng lại được: ít nhất hai nguồn gốc trực tiếp liên quan (ví dụ mô hình Software/OpenCTI, CPE hoặc tài sản công nghệ trong dự án hiện có), kèm link chính xác, ngày kiểm, mức tái sử dụng và giới hạn. Nêu khi chỉ đọc tài liệu, chưa chạy mã. Không cài thư viện hoặc gọi lab/cloud dịch vụ thật.
2. So sánh ngắn 2–3 cách lưu công nghệ tương thích AssetStore/API hiện hữu; khuyến nghị một cách đơn giản. Chốt cấu trúc vendor/product/version, bound/chuẩn hóa/duplicate, ghi chú, phiên bản optimistic và audit, phân biệt version phần mềm với version bản ghi.
3. Giữ domain/CIDR và W02 không đổi; technology không tạo allowlist, không làm IOC có asset-match. Quyền server-side, lỗi/unknown outcome và không replay mutation giữ nguyên. Nêu migration SQLite và dữ liệu cũ/hỏng, giao dịch asset+audit và cách kiểm lỗi không commit.
4. Hợp đồng trả/ghi dữ liệu và extension point cho Frontend: có thể thêm tab công nghệ theo DESIGN sẵn có; provider fixture trước/HTTP sau. Không tự thiết kế lại giao diện. Giữ một người sửa một tree.
5. W03 spec khớp nhà cung cấp+sản phẩm không phân biệt hoa thường; phiên bản chỉ hiển thị cho người kiểm. Nêu rủi ro alias/khớp sai, cách diễn đạt chưa chắc chắn và chỗ cần dữ liệu tương thích. Không biến ghép chuỗi thành kết luận chắc chắn hệ thống có lỗ hổng; không tự thêm version-range matching, quét mạng hoặc tự vá.
6. Đề xuất một brief Sol medium có goal, base/tree riêng, allowlist, test có ý nghĩa (dữ liệu cũ, quyền, duplicate, cập nhật/xóa, audit rollback, không ảnh hưởng W02), kiểm tối thiểu và tiêu chí bàn giao. Tách việc đủ độc lập để Frontend không chờ toàn bộ Backend; chưa tự giao triển khai.

## Phạm vi chưa làm

Không làm mã sản phẩm, không commit/push/PR/merge/deploy, không sửa source tree/RUNS/plan, không cài dependency, không đọc secret/dữ liệu doanh nghiệp. Không làm CSV, thương hiệu, scanner, feed CVE thật, EPSS/KEV sync hoặc toàn bộ W03 trong nghiên cứu này. Nếu cần quyết định ngoài spec, ghi lựa chọn và khuyến nghị để Leader chốt trong phạm vi, không tự hỏi bot khác.

## Kết quả

Ghi duy nhất báo cáo root `PHONG-HOA-W04-TECHNOLOGY-RESEARCH-20261111.md`; artifact hỗ trợ nếu cần ở `w04-technology-research-evidence/`. Trả nguồn đã kiểm, ref, phần dùng lại, phương án, hợp đồng/brief đề xuất và UNVERIFIED. Bằng chứng tài liệu không đồng nghĩa đã triển khai hoặc test.
