# X01 ATT&CK offline — brief nghiên cứu tiếp theo

Trạng thái: nghiên cứu mới, **chưa cho phép implementation**. Owner CTI Research. Mục tiêu là chốt phần kiểm mã ATT&CK (bộ mã kỹ thuật tấn công) làm được ngoại tuyến để chuẩn bị C4 trong X01.

## Nguồn và ranh giới
Workspace Leader: `$WORKSPACE`.
Source AI readonly: `$WORKSPACE/cti-platform-ai-llm-adapter`, HEAD `8694fa7244d181f421bb2733ded7bf9ae218ea93`, đang sạch. Không lấy main thay nhánh này, không gộp nhánh hay sửa tree.
Đọc AGENTS/PROGRESS, `docs/specs/X01-ai-extractor.md`, `extractor/dataset/GUIDELINE.md`, adapter/eval hiện có. Tái dùng `PHONG-HOA-AI-NEXT-RESEARCH.md`, `PHONG-HOA-AI-IMPLEMENTATION-BRIEF.md`, `PHONG-HOA-AI-EVAL-RESULT.md`. Không nghiên cứu lại toàn bộ provider/agent/STIX.
Luồng C1→W05→STIX vừa nghiệm thu ở nhánh độc lập cf9e609; việc này không yêu cầu nhập code AI vào nhánh đó.

## Câu hỏi phải trả lời
1. So tối đa ba cách nhỏ: parser/index JSON STIX trực tiếp, thư viện ATT&CK có sẵn, hoặc tái dùng thành phần repo. Chọn một phương án theo độ phức tạp, dependency/version/license/provenance; tra nguồn MITRE/OASIS và tài liệu chính thức, link đúng mục và ngày kiểm. Không khẳng định release/package đã chạy chỉ từ tài liệu.
2. Chốt nguồn snapshot Enterprise ATT&CK, phiên bản/hash/bản quyền, cách pin và cập nhật thủ công. Xem file/snapshot hiện có trước khi đề xuất tải thêm. Không tải bulk corpus, cài package hoặc gọi TAXII trực tiếp ở lượt này.
3. Chốt xử lý attack-pattern, external_references/external_id, domain, technique/sub-technique, revoked/deprecated, duplicate/conflicting/versioned IDs, bundle lỗi và giới hạn kích thước. Mã có tồn tại không chứng minh hành vi đúng; quoted evidence khớp văn bản cũng không chứng minh quan hệ ngữ nghĩa.
4. Tách rõ ba mức: cú pháp mã hợp lệ, mã tồn tại/active trong snapshot đã pin, và ngữ nghĩa TTP chưa xác minh. Không tự chuyển semantic item thành operational_draft_eligible chỉ vì lookup/quote khớp. Không gọi lookup là RAG hoặc C4 hoàn tất.
5. Đề xuất lát cắt triển khai nhỏ nhất: loader/index/validator thuần offline với fixture nhỏ tổng hợp hoặc trích có license/provenance; hợp đồng input/output/errors; chỗ tích hợp adapter/evaluator nếu thật sự cần. Giữ C1/C2/C3 tương thích và dữ liệu semantic chưa xác minh. Không sửa SQLite/W05/API/UI/STIX exporter.
6. Ma trận kiểm: ID tồn tại/không tồn tại, revoked/deprecated, technique cha/con, external_ref sai, malformed JSON/kiểu dữ liệu/Unicode, duplicate/version conflict, pin/hash mismatch, evidence lệch, giới hạn tài nguyên, mạng/provider 0 call, không ghi đè output khi lỗi, C1/C2/C3 regression cần thiết. Không yêu cầu test chỉ để tăng số lượng.

## Đầu ra duy nhất được ghi
- `PHONG-HOA-X01-ATTACK-RESEARCH.md`: đối chiếu nguồn, phương án chọn, phần tái dùng, phần chưa biết.
- `PHONG-HOA-X01-ATTACK-IMPLEMENTATION-BRIEF.md`: tự đủ để CTI AI Agent/Sol medium triển khai sau Leader chọn; exact base, tree/branch mới đề xuất, scope file, interface, test/acceptance, lệnh và bằng chứng cần trả.

Chỉ ghi hai file tại workspace Leader; repo đọc, không tạo tree/commit/listener, không sửa RUNS hoặc báo cáo khác. Không giao bot khác, không model/cloud LLM/lab/OpenCTI/secret/dữ liệu hạn chế. Có thể đọc nguồn công khai chính thức cho nghiên cứu. Không tuyên bố đã chạy test/validator hoặc model; báo SHA256 hai tài liệu và Git trước/sau. Nếu có quyết định sản phẩm chưa đủ căn cứ, nêu lựa chọn và tradeoff cho Leader, không hỏi người dùng thay Leader.
