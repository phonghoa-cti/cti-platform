# X01-C4-EVAL-NEXT — nghiên cứu bước đánh giá C4 ngoại tuyến

Ngày 11/11/2026. Owner CTI Research. Chỉ nghiên cứu và viết hai tài liệu, không implementation hoặc giao tiếp bot khác.

## Điểm xuất phát

Root tuyệt đối: `$WORKSPACE`.

Source chỉ đọc `root\cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`, HEAD `654443e6ede6557f0629fc0886ca56fff782b193`, vừa được Leader nghiệm thu. Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, ADR 0008 và `root\PHONG-HOA-X01-C4-ADAPTER-ACCEPTANCE-20261111.md`.

Tái dùng research/brief ở root: `PHONG-HOA-X01-C4-ADAPTER-RESEARCH.md`, `PHONG-HOA-X01-TTP-EVAL-RESEARCH.md`, `PHONG-HOA-X01-TTP-EVAL-IMPLEMENTATION-BRIEF.md`, `PHONG-HOA-X01-EVAL-REPORT-RESEARCH.md`, `PHONG-HOA-X01-EVAL-REPORT-IMPLEMENTATION-BRIEF.md`. Chỉ đọc đoạn cần; không nghiên cứu lại catalog hoặc workflow.

Đối chiếu source thực: `extractor/eval/run.py`, `extractor/eval/report.py`, `extractor/phonghoa_extractor/{llm_adapter,llm_fixture,ttp_audit,attack_catalog,attack_retrieval}.py`, tests liên quan, dataset synthetic hiện có. CLI evaluator vẫn từ chối C4; reporter chỉ có C1–C3. Adapter C4 đã nhận query explicit và tách knowledge/report; retry tối đa 2 lần và fallback cùng C3.

## Câu hỏi phải chốt

Mục tiêu dùng được: chạy C4 bằng provider giả lập trên bộ mẫu tổng hợp, xuất kết quả truy nguyên được và đọc/so sánh đúng giới hạn. Không biến smoke thành chất lượng mô hình.

1. So tối đa ba cách nối C4 vào evaluator/reporter, đánh giá phần tái dùng và giới hạn, khuyến nghị phạm vi nhỏ nhất dùng được. Xác định có nên làm reporter cùng lát hay giao ngay sau; nếu hoãn phải nêu đầu ra evaluator dùng/đọc thế nào và hợp đồng tương thích.
2. Query theo từng document: explicit manifest hay derive deterministic từ source; so tradeoff và chốt một hợp đồng. Không lấy gold labels, phản hồi provider hoặc đáp án ATT&CK để tạo query; không gọi provider thêm. Bounds, Unicode/newline, document-ID mapping, missing/extra/duplicate, provenance/hash và input-error order phải rõ; không thêm dịch vụ/dependency.
3. Public API + CLI flags, schema artifact chính xác và mẫu cấu trúc. C4 scoring IOC theo keep=true/C3, thuật ngữ model+regex rõ; TTP chỉ source/quote/catalog consistency, không F1/semantic quality. Retrieval hoàn thành không đồng nghĩa model sử dụng knowledge hay tăng chất lượng.
4. Tái dùng loader/pin/retriever/adapter/audit/scorer, không parser STIX thứ hai. Context/query không ghép vào nguồn evidence; hash nguồn báo cáo và hash context khác nhau; zero-match/fallback/terminal/error/call-count và provenance phải biểu diễn trung thực. Không lưu raw context/query không cần thiết trong bảng báo cáo.
5. C1–C3 defaults/artifacts không đổi; reporter validation/schema/cohort cần cập nhật đúng mức hoặc tiếp tục từ chối C4 rõ ràng. C3/C4 comparison phải cùng dataset/pin/query policy thích hợp, không ngụy tạo metric mô hình. Chính sách input bounded, safe errors, atomic output/no-clobber/alias và không ghi đè input kế thừa hiện có.
6. Brief triển khai tự đủ cho CTI AI Agent/Sol medium: exact base/tree/branch đề xuất mới, allowlist, signatures/DTO/flags/error taxonomy, invariants, acceptance matrix, RED→GREEN, regression cần chạy, demo và evidence/output. Không mở rộng sang API/UI/W05/STIX/model thật.

Nguồn: ưu tiên nghiên cứu còn phù hợp, kiểm mã ở exact SHA và trích tài liệu chính thức/nghiên cứu gốc cho câu hỏi mới (RAG evaluation, tránh dùng đáp án trong đầu vào, provenance/reproducibility). Ghi cái đã đọc và cái chưa kiểm chứng; tài liệu không phải bằng chứng implementation. Đối chiếu PR đang mở nếu cần quyết định base; không đổi base/pull/merge trong nhiệm vụ nghiên cứu.

## Quyền ghi và tiêu chí trả

Chỉ tạo/cập nhật hai file mới tại root:

- `PHONG-HOA-X01-C4-EVAL-RESEARCH.md`
- `PHONG-HOA-X01-C4-EVAL-IMPLEMENTATION-BRIEF.md`

Nếu file đã có nội dung lạ, không ghi đè; báo rõ. Source/RUNS/acceptance/brief này không sửa; không tạo worktree/commit, cài package, chạy implementation/test, listener/model/cloud/secret/lab, push/PR/merge/deploy. Không tải lại snapshot 55 MB; dùng đường dẫn/provenance sẵn có nếu cần.

Trả một khuyến nghị có lý do, hai đường dẫn tuyệt đối/SHA-256, source HEAD/status trước/sau, phần chưa biết. Thành công khi không còn quyết định kỹ thuật cốt lõi bỏ ngỏ trong brief và Leader có thể giao một worker triển khai mà không phải dựng lại contract.
