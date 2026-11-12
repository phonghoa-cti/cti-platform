# WEB-W05-PREVIEW — giao diện Codex làm được trước lab/API

Owner CTI Frontend, Codex/Sol medium. Người dùng đã yêu cầu Codex làm giao diện thay Antigravity. Tự làm, không giao tiếp bot khác.

## Mục tiêu

Một người mở portal cục bộ, xem hàng đợi bản nháp tổng hợp, chọn draft, đọc văn bản gốc và IOC gắn đúng bằng chứng; thấy rõ cảnh báo, allowlist và mục bị loại. Đây là lát cắt giao diện đầu tiên để nối API thật sau, không phải hoàn thành W00–W05. Không triển khai quyết định duyệt giả hay OpenCTI.

## Nơi làm và nguồn

- Workspace cha chứa brief: `$WORKSPACE`.
- Chỉ sửa repo con `cti-portal-web`, branch đã tạo `feat/portal-w05-preview-20261110`, base `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`. Không tạo worktree khác, không sửa `cti-platform-start`/`cti-w05-backend`.
- Đọc AGENTS.md, docs/PROGRESS.md, docs/design/DESIGN.md, docs/adr/0002-chon-cong-nghe-web.md, docs/specs/W00-portal-tong-the.md, W05-duyet.md, W05-draft-offline-contract.md, docs/design/W05-draft-handoff.md; ba JSON trong extractor/draft/examples.
- Trước code: ghi ngắn nguồn chính thức cho phiên bản Next.js/React/Tailwind đang chọn và khả năng dùng lại component; không nghiên cứu lại toàn sản phẩm. Giữ lựa chọn stack A (Next.js + TypeScript + Tailwind; shadcn khi có component thực sự cần), thiết kế SOC console tối đã có. Chọn phiên bản ổn định từ nguồn chính thức và lockfile, không beta/ép --force để vượt conflict. Không cài thư viện biểu đồ hoặc auth không dùng ở lát cắt này.

## Phạm vi file

Được tạo/sửa `portal/web/**` (kể cả package manifest/lock, app/components/data/messages/tests/README và gitignore cục bộ). Chỉ sửa docs/PROGRESS.md đoạn của task, tạo docs/ai-log/web-w05-preview.md để ghi lựa chọn/nguồn/kiểm; không đổi spec/API contract chung hoặc file Python. Giữ node_modules/build/artifact test khỏi Git. Local commit được phép, không push/PR/merge/deploy. Không secret/VM/lab/cloud LLM.

## Hành vi cụ thể

1. Route `/duyet` là màn chính; `/` điều hướng tới màn này. Sidebar/topbar theo DESIGN chỉ có điều hướng đang dùng được, không bày link giả. Có nhãn dễ hiểu `Dữ liệu mẫu` và trạng thái nguồn để người dùng biết chưa lấy dữ liệu thật.
2. Adapter dữ liệu riêng tải ba fixture tổng hợp sẵn có. Validate tối thiểu đúng hình dạng và ID; lỗi phải hiển thị, không tự chuyển thành hàng đợi trống. Không hardcode tất cả vào component. Có empty/loading/error bằng adapter và test; không cần bảng điều khiển test lộ trong sản phẩm.
3. Hàng đợi, phân trang hoặc chọn hàng; chi tiết gồm tên nguồn/TLP/ngôn ngữ/model, văn bản text-only, item loại/value/keep/status, lý do cảnh báo. Mục rejected vẫn thấy được cùng lý do. Default keep đúng fixture; nếu có checkbox chỉ là bản xem thử tại chỗ, không giả lưu lên server.
4. Chọn IOC làm nổi đúng span trong nguồn và chuyển focus hợp lý. Span là code point, dùng Array.from hoặc cách tương đương; test nguồn có emoji đứng trước IOC. Không render HTML từ text/evidence/source. IOC/URL hiển thị defang, không tạo link mở địa chỉ nguy hiểm; copy chỉ khi người dùng bấm.
5. Quyết định approve/reject chưa có API xác thực: không gửi request ghi, không hiển thị đã nhập OpenCTI. Có thể ẩn hoặc vô hiệu nút kèm lời rõ `Chức năng duyệt đang được hoàn thiện`. Không tạo đăng nhập giả để tuyên bố có bảo vệ quyền.
6. Tiếng Việt mặc định, text tách messages/vi.json và en.json; có chọn ngôn ngữ đơn giản hoạt động. Mobile 360 px và desktop 1440 px, focus/bàn phím, label bảng và trạng thái dùng cả chữ lẫn màu. Dùng font có sẵn/fallback phù hợp; build không phụ thuộc tải font lúc chạy.

## Kiểm và bàn giao

- Kiểm trạng thái Git trước sửa; dependency chỉ trong portal/web. Chạy typecheck, lint theo cấu hình và production build. Kiểm import dùng đúng tree.
- Test hành vi adapter malformed/empty; evidence highlight emoji; payload có chuỗi HTML hiển thị text; không có thao tác ghi/approval từ bản preview. Dùng công cụ test phù hợp, không viết test chỉ lặp markup.
- Kiểm luồng trình duyệt thật: mở `/duyet`, chọn ít nhất 2 draft, bấm evidence, đổi ngôn ngữ, kích thước 360/1440. Dùng bề mặt trình duyệt/máy được OpenMausBot cấp; nếu không truy cập được localhost, ghi đúng điều chưa kiểm, không dùng ảnh giả hoặc trang đăng nhập làm bằng chứng. Mã build/unit không thay kiểm hiển thị.
- Cổng dự kiến 3002, không chiếm cổng task khác. Không để process không rõ chủ sở hữu. Server cần chạy bằng cơ chế công cụ hỗ trợ; nếu không giữ được, cung cấp lệnh chạy kiểm được và không báo server đang mở.
- Đầu ra ngoài repo trong workspace cha: `PHONG-HOA-FRONTEND-RESULT.md`, `frontend-evidence/` (log, ảnh khi có). Báo SHA, diff, nguồn phiên bản, lệnh/exit, ca pass/fail/unverified, cách chạy và phần chưa nối backend.
- Bước sau: Leader nghiệm thu rồi giao adapter API/luồng tiếp. Không chờ lab để tự hoàn thành phần preview đã đủ brief.
