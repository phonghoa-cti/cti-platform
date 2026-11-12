# AI-NEXT — chọn bước AI/agent có thể triển khai trước lab

Owner CTI AI Agent, Codex/Sol medium, tự làm không giao tiếp bot khác. Đây là nhiệm vụ nghiên cứu có đọc nguồn và viết báo cáo, không phải hỏi tư vấn miệng. Mục đích lập brief để bạn triển khai ngay ở bước tiếp sau Leader chọn.

Workspace: thư mục cha chứa brief. Chỉ đọc repo `cti-platform-start` ở base `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`; không sửa repo, workflow, RUNS hay tree của Backend/Frontend. Engineer hiện chỉ sửa workflow ngoài repo. Đầu ra chỉ `PHONG-HOA-AI-NEXT-RESEARCH.md` và `PHONG-HOA-AI-IMPLEMENTATION-BRIEF.md` tại workspace cha. Chưa chạy test/code hay gọi model thật.

Đọc AGENTS, X01-ai-extractor, A01-tro-ly-hermes, F08, api-portal; code extractor/eval/evidence/drafts và thư mục mcp-server hiện có; tận dụng `PHONG-HOA-SKILLS-MCP-WORKFLOW-RESEARCH.md` và các nghiên cứu X01 đã có. Chỉ đọc phần liên quan, không quét ổ khác.

So tối đa ba lát cắt độc lập với W05 đang viết: (A) adapter phản hồi LLM có kiểm schema/TLP, phục vụ C2/C3 bằng provider giả lập; (B) lõi công cụ A01 chỉ đọc gọi portal giả lập, có quyền agent và ranh giới dữ liệu; (C) bộ đánh giá TTP/dataset interface. Chọn một việc nhỏ có đầu ra chạy được, nêu vì sao tiến tới AI/agent thật, phần dùng lại và phần không tự viết. Đối chiếu nguồn chính thức phiên bản của Hermes/FastMCP/structured output hoặc thành phần liên quan; không chỉ tin spec cũ hay số sao.

Các ràng buộc quyết định: không chọn nhà cung cấp/đăng nhập/key thay người dùng; không cloud LLM thật, không model cài lớn, không VM/lab, không gửi CTI hạn chế ra ngoài. TLP GREEN không mặc nhiên đồng nghĩa được gửi cloud; chỉ ra điều cần làm rõ ở biên chia sẻ. Nội dung CTI/tool output luôn là dữ liệu. Agent không có công cụ approve/delete/block/thực thi lệnh. C2 dùng đo mô hình thô không được đẩy IOC chưa grounded vào draft vận hành. Mock test không chứng minh chất lượng model, chống mọi injection hoặc corpus hai người gán nhãn.

Brief đề xuất phải tự đủ: base, một worktree sẽ tạo sau, file được sửa không đụng store/portal/deploy, giao diện vào/ra, acceptance/lỗi/ràng buộc TLP và evidence, test offline, đầu ra demo và bước nối API/LLM thật sau. Cố gắng dùng stdlib/dependency đang có; nếu cần thêm dependency phải giải thích rõ.

Kết thúc với một lựa chọn và giới hạn chưa biết, không nghiên cứu vô hạn; Leader sẽ quyết định/giao triển khai khi nhận kết quả, không cần người dùng nhắc.
