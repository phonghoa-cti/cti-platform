# W05-NEXT-RESEARCH — chọn việc kế sau mốc SQLite

Owner CTI Research, Terra medium; chỉ nghiên cứu và viết hai đầu ra, không sửa mã, không giao tiếp bot khác. Người dùng đã yêu cầu tiếp tục dự án trước lab; kết thúc mốc offline không kết thúc mục tiêu.

## Hiện trạng

Workspace là thư mục chứa brief; repo `cti-platform-start`, branch `feat/x01-draft-queue-20261110`, HEAD `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`. Kiểm HEAD/status đầu và cuối, không checkout/reset. Nền đã nghiệm thu: text→IOC evidence→pending→SQLite save/list/get; log236 Engineer,44 Leader,24 CLI QA. Không chạy lại các test này.

Đọc đúng file: repo AGENTS.md, docs/specs/W05-duyet.md, docs/specs/W05-draft-offline-contract.md, docs/specs/api-portal.md (drafts/quyền), docs/specs/X01-ai-extractor.md, docs/PROGRESS.md; `PHONG-HOA-INITIAL-RESEARCH.md` và `PHONG-HOA-ORCHESTRATION-RESEARCH-20261110.md`. Đọc chọn lọc code store/drafts để biết phần có sẵn.

## Câu hỏi phải chốt thành đề xuất

So tối đa ba lát cắt kế tiếp: schema đầu vào chặt, lõi quyết định duyệt/từ chối+audi­t ngoại tuyến, hoặc API đọc có quyền. Chọn một có ích và nhỏ nhất để nối W05, nêu lý do và phần phụ thuộc. Đối chiếu OpenCTI draft/workbench và thư viện chuẩn trước khi tự xây để tránh nhân bản; nguồn chính thức còn hiện hành, đường dẫn và ngày truy cập. Nghiên cứu cũ phù hợp được dùng lại, không tìm để đủ số nguồn.

Làm rõ: dữ liệu người tạo/người duyệt; không tin email client; TLP không là quyền gửi cloud; transaction/chuyển trạng thái/audit/version/migration nếu lát cắt cần; old pending1.0 xử lý ra sao. Phân biệt hàm policy được test với xác thực production thật. Không giả lập auth hoặc ghi OpenCTI rồi báo đã tích hợp. UI của Antigravity chỉ nhận handoff, không tự thiết kế.

## Đầu ra và giới hạn

Chỉ ghi `PHONG-HOA-W05-NEXT-RESEARCH.md` và `PHONG-HOA-W05-NEXT-IMPLEMENTATION-BRIEF.md` trong workspace. Đầu ra1: so lựa chọn, nguồn, reuse/gap, quyết định đề xuất và rủi ro còn lại. Đầu ra2: brief tự đủ gồm mục tiêu, base/path, file có thể sửa, giao diện, tiêu chí đo được và kiểm lỗi, giới hạn, đầu ra/evidence, bước sau nghiệm thu. Nếu có câu hỏi sản phẩm mà hiện trạng chưa trả lời, đề xuất mặc định đảo ngược được và phân biệt phần cần chủ; không dừng nghiên cứu ở câu hỏi đó.

Không sửa sổ PHONG-HOA-RUNS.json (Leader đang quản lý), không viết vào repo/ổ E, không test sản phẩm, không bot/model khác, lab/cloud/LLM thật, secret, push/PR/merge/deploy. Không đọc *_PRIVATE hoặc .env. Dùng nguồn web chính thức phù hợp, không gửi nội dung CTI thật ra ngoài. Báo đúng đây là nghiên cứu/brief, chưa triển khai. Sau kết quả Leader quyết định, giao Engineer khi rảnh; không cần người dùng nhắc tiếp.
