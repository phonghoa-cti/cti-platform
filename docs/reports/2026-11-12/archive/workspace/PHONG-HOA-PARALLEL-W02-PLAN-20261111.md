# Phân công song song — 11/11/2026

Mục tiêu: hoàn thiện luồng nạp → duyệt → xuất đang làm, đồng thời xây phần tra cứu IOC (IP/domain/URL/hash đáng ngờ) của portal theo W02. Không coi giao việc, bản mẫu hoặc test cục bộ là sản phẩm chạy thật.

## Chủ sở hữu và phụ thuộc

| Task | Owner | Phạm vi ghi | Điều kiện bước tiếp |
|---|---|---|---|
| X01-INGEST-QUEUE-IMPLEMENT | Backend | `cti-x01-ingest-queue` và report/evidence đã giao | Leader nghiệm thu commit + migration/creator/demo |
| X01-INGEST-BROWSER-PREP | Engineer | Một brief đã giao | Chỉ triển khai tích hợp sau khi importer được nghiệm thu |
| W02-LOOKUP-VIEW | Frontend, Sol medium | `cti-w02-lookup-ui`, UI và tests dưới đây | Nối API sau khi contract/backend được nghiệm thu |
| W02-LOOKUP-API-RESEARCH | Research | `PHONG-HOA-W02-API-CONTRACT-BRIEF.md` | Leader chốt contract rồi giao triển khai API riêng |

QA nhận commit ổn định để kiểm rủi ro cụ thể; không sửa cùng tree với tác giả. AI Agent giữ phần AI, chưa gọi model thật hoặc thay người gán nhãn. Chưa cần thêm người: các vai trò hiện có đủ cho bốn nhánh này.

Root: `$WORKSPACE`.
Source chỉ đọc chung: `cti-x01-w05-stix-e2e` tại `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; Leader đã đối chiếu HEAD và status sạch. Không đọc/sửa tree Backend đang viết.

## Hướng đã chọn và nghiên cứu tái sử dụng

W00 xếp W02 là luồng có ích cho IT: xem thông tin đã biết, nguồn và lý do đánh giá. Tái dùng `docs/specs/W02-tra-cuu-ioc.md`, `api-portal.md`, `docs/design/DESIGN.md`, UI W05 và nghiên cứu ban đầu `PHONG-HOA-INITIAL-RESEARCH.md`. Các hợp đồng ngoài W05 trong source còn là đề xuất, không tự coi đã triển khai.

Chọn tách phần hiển thị W02 khỏi API để làm song song. Chờ toàn backend sẽ làm Frontend bị nhàn; tự đoán thêm API/auth sẽ làm lệch hướng. Frontend làm view/interaction và nguồn dữ liệu mẫu thay được; Research chốt contract API dựa trên core hiện có. Không nghiên cứu lại toàn kiến trúc; câu hỏi mới kiểm nguồn chính thức trước quyết định, ghi gọn vào đầu report/brief.

## W02-LOOKUP-VIEW — gói triển khai Frontend

- Tạo tree riêng `cti-w02-lookup-ui`, branch `feat/w02-lookup-view-20261111` từ source exact SHA trên. Nếu tồn tại có thay đổi/owner khác thì báo; không reset. Một worker Sol medium, không giao tiếp bot khác.
- Đọc AGENTS, PROGRESS, W00/W02/api-portal/DESIGN và skill UI/TDD phù hợp. Phạm vi đã được giao; không xin lại quyền lựa chọn kỹ thuật có thể đảo ngược. Giữ thiết kế Phong Hỏa, thư viện/lock hiện có; không thêm dependency, font tải ngoài hoặc thiết kế lại W05.
- Đầu ra: component tra một IOC, trạng thái idle/loading/result/not-found/invalid/private-IP/unavailable/forbidden và trang `/tra-cuu/mau` ghi rõ dữ liệu tổng hợp. Form dùng nhãn, bàn phím và VI/EN. Mọi lần tìm không khớp fixture trả trạng thái mẫu không tìm thấy, không gọi mạng.
- Tách interface nguồn dữ liệu khỏi component: kết quả hiển thị có IOC đã chuẩn hóa/display, trạng thái có nguồn/allowlist, score/level/reason tùy trạng thái, sources, related/enrichment/TLP. Đây là view model nội bộ, không tuyên bố là contract HTTP cuối; adapter HTTP là task sau. Mẫu sử dụng đúng các trường đã có trong spec, không phát minh điểm hoặc quan hệ cho dữ liệu nhập bất kỳ.
- Chỉ một IOC mỗi lần; batch, enrichment thật, đề xuất chặn, false-positive, đăng nhập, OpenCTI links và URL chứa truy vấn thật chưa triển khai. Không dựng nút báo thành công cho hành động chưa có. Không làm thêm W01/W03/W04.
- Không tự chuẩn hóa/chấm điểm trong frontend. Mọi IOC hiển thị defang, không liên kết bấm được; copy giá trị nguyên từ kết quả và báo lỗi/thành công đúng Promise. Văn bản từ dữ liệu render text, không HTML; chưa bật link ra nguồn ngoài. Không có secret, lưu lịch sử truy vấn hay analytics.
- Có case tìm A rồi B, response A đến muộn không ghi đè B; lỗi xóa kết quả cũ đang dễ bị hiểu nhầm; rỗng/không tìm thấy không hiện là an toàn. Dữ liệu allowlist chỉ hiện theo kết quả mẫu đã định nghĩa, không suy từ tên miền.
- Allowlist: `portal/web/app/tra-cuu/mau/page.tsx`; component mới `portal/web/components/ioc-lookup*.tsx`; `portal/web/data/ioc-lookup*.ts`; `portal/web/tests/ioc-lookup*.test.ts*`; `portal/web/messages/vi.json`, `en.json` chỉ thêm nhóm W02; `portal/web/app/globals.css` chỉ selector mới có phạm vi; `portal/web/README.md`; `docs/PROGRESS.md`. Không sửa `/`, W05, API, store, extractor, DESIGN, config, package/lock hoặc RUNS. Liệt kê file mới chính xác trong report.
- Kiểm: RED→GREEN cho tương tác/nhánh lỗi/race và copy; toàn test web, typecheck, lint, build, diff-check một lần cuối. Không chạy Python/full backend. So diff bảo toàn W05/config/lock.
- Browser nếu cần dùng trình duyệt tích hợp duy nhất; port riêng `3012`, xác minh trống trước mở, listener loopback và cleanup đúng process thuộc mình. Không đụng port của Engineer. Browser bận/không sẵn thì báo UNVERIFIED, không đổi sang tự động hóa khác. Không giả viewport bằng zoom/CSS.
- Report `PHONG-HOA-W02-LOOKUP-UI-RESULT.md`, evidence `w02-lookup-ui-evidence/`: SHA/base/diff, command/exit/count, demo thao tác và giới hạn. Commit local sạch trong target. Không push/PR/merge/deploy, dữ liệu thật, model, lab hoặc OpenCTI. Trả kết quả để Leader nghiệm thu; không coi W02 hoàn thành toàn bộ.

## W02-LOOKUP-API-RESEARCH — gói nghiên cứu ngắn

- Chỉ đọc source exact SHA, AGENTS/spec W02/F05/F08/api-portal, core normalize/score/allowlist và auth W05 hiện có. Kiểm HEAD/status trước-sau. Không đọc tree Frontend/Backend đang làm.
- Đầu ra duy nhất `PHONG-HOA-W02-API-CONTRACT-BRIEF.md`, tối đa 160 dòng, đủ giao Sol medium. Tái dùng tài liệu chính thức/research có sẵn; tối đa ba nguồn mới có ích về OpenCTI lookup/marking/auth. Không viết lại lịch sử hay dựng kế hoạch toàn dự án.
- Chốt một endpoint GET `/api/ioc?value=` chỉ đọc; không batch, enrichment POST, đề xuất chặn hay sửa W05/store. Định nghĩa exact schema/types/bounds/nulls/enums cho found/absent/allowlist và lỗi invalid/private-IP/auth/unavailable; cung cấp fixture JSON nhỏ hợp lệ. Chốt `unknown` khác `safe`; không có nguồn không đồng nghĩa score nguy hiểm bằng 0.
- JWT đã xác minh + role server-side theo sub như W05; không dùng email/header tự khai hoặc DEV_USER_EMAIL trong spec cũ. Quyền/TLP kiểm trước trả kết quả, kể cả related/sources/count/reason/cache; IT không thấy AMBER/RED. Không tự coi GREEN được gửi cloud.
- Tái dùng core chuẩn hóa/chấm điểm, giới hạn input, timeout/lỗi đóng, no-store, không echo dữ liệu/token thô. Chốt backend lookup abstraction hẹp với fixture offline trước; real OpenCTI/JWKS chưa kiểm và cần bước riêng, không đưa mock vào production mặc định.
- Đưa source/base, target/branch mới không đè tree đang chạy, allowlist, interface, acceptance matrix, tests in-process không mạng, demo, report/evidence và điều kiện nối UI. Bất đồng với spec cũ ghi delta rõ để Leader quyết, không tự sửa contract trong source.
- Không tạo worktree/code/test/listener, cài dependency, sửa repo/RUNS/plan, dùng secret/cloud/model/lab hoặc gửi thông tin. Nghiên cứu là chuẩn bị, không phải API đã hoạt động.

## Cổng tích hợp và nghiệm thu

Mỗi task có receipt riêng trong RUNS; một writer một tree. Kết quả về Leader kiểm đúng SHA và phần rủi ro, không chạy lại kiểm đã đủ. Đổi hợp đồng hoặc mở thêm file phải báo cụ thể. Frontend không đợi Research để làm view; việc nối HTTP phải đợi contract và backend được chấp nhận. Engineer không lấy UI W02 đang viết để ghép vào demo W05. Chỉ Leader chọn bước ghép sau khi các phần ổn định; không ai tự merge/phát hành.
