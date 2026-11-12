# X01-C4-RETRIEVAL-NEXT — nghiên cứu lát cắt C4 ngoại tuyến

Ngày 11/11/2026. Owner CTI Research; **chỉ nghiên cứu và brief, không triển khai**. Không giao bot/helper khác.

## Đích và căn cứ

Sau reporter C1–C3 được nghiệm thu, chọn phần C4 nhỏ nhất hữu ích theo `docs/specs/X01-ai-extractor.md` (pipeline bước 6, cấu hình C4, đánh giá). Cần phân biệt tra ID sau generation với retrieval kiến thức liên quan trước generation. Mục tiêu lượt này là hợp đồng đủ rõ để một CTI AI Agent / Sol medium triển khai độc lập một thành phần offline; không mở toàn bộ C4, không đo hoặc hứa chất lượng model.

Root tuyệt đối: `$WORKSPACE`.

- Source chỉ đọc: `root\cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`, exact HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`.
- Đọc AGENTS, spec X01, PROGRESS, `extractor/phonghoa_extractor/attack_catalog.py`, `ttp_audit.py` nếu tên đúng trong tree, adapter/provider/schema và prompt hiện có; kiểm tên thực bằng rg.
- Tái dùng nghiên cứu tại root: `PHONG-HOA-AI-NEXT-RESEARCH.md`, `PHONG-HOA-X01-ATTACK-RESEARCH.md`, `PHONG-HOA-X01-ATTACK-REAL-RESEARCH.md`, `PHONG-HOA-X01-TTP-AUDIT-RESEARCH.md`, cùng `PHONG-HOA-X01-EVAL-REPORT-ACCEPTANCE-20261111.md`. Không nghiên cứu lại toàn bộ lịch sử workflow hay reporter.
- Hiện `TechniqueRecord` có name/ID/lifecycle/parents nhưng chưa có description. Snapshot Enterprise v20.1 đã ghim commit/hash, loader strict/canonical/parent policy đã có. Phải giải quyết thiếu dữ liệu retrieval bằng một seam nhỏ có test, không tạo parser STIX thứ hai bỏ qua validation hiện tại.

## Câu hỏi phải chốt

1. Đối chiếu tối đa ba cách đã có người làm: tra từ khóa/lexical local, truy hồi ngữ nghĩa cần embedding, hoặc cách tối thiểu khác phù hợp. Dùng nguồn gốc MITRE STIX/ATT&CK và nghiên cứu retrieval/RAG chính thức. Nêu phần tái dùng, dependency/chi phí, giới hạn Việt–Anh, lý do chọn. Dẫn nguồn đã đọc và ngày; không coi nguồn nghiên cứu là bằng chứng sản phẩm chạy.
2. Chọn thành phần đầu tiên đủ nhỏ: ưu tiên thư viện retrieval + context bất biến có provenance, chạy hoàn toàn cục bộ. Xác định rõ dữ liệu từ name/description, source snapshot pin, canonical version, lifecycle/parent; không cho metadata bị sửa hoặc record inactive lọt do đường đọc phụ. Nếu chỉ dùng tên/ID, nói giới hạn và không gọi semantic retrieval.
3. Hợp đồng query/result: kiểu và bounds, Unicode/tiếng Việt, thứ tự/tie-break deterministic, top-k/context budget, zero match/empty/invalid input, duplicate/parent-child, hash/version/provenance, lỗi an toàn và no mutation/no egress. Nếu ranking có score, định nghĩa đó là ranking score, không confidence hay semantic truth. Nếu đọc description/citation markup, coi đó là dữ liệu không tin cậy; không thực thi URL/lệnh hoặc cho nó tự nâng quyền.
4. Phân biệt evidence trích từ báo cáo gốc với mô tả kiến thức ATT&CK. Context không được làm bằng chứng giả rằng báo cáo có kỹ thuật đó. Kết quả vẫn semantic `unverified`, không operational draft eligible; audit/grounding/quyền duyệt hiện có không được bỏ qua.
5. Chốt ranh giới thành phần đầu tiên và bước nối tiếp: C1–C3/evaluator/reporter giữ tương thích, C4 CLI tiếp tục từ chối cho đến khi đường đầy đủ được thiết kế/kiểm. Chưa gọi model, chưa chọn dịch vụ trả phí, không embeddings mạng, UI/W05/OpenCTI hoặc lab.

## Đầu ra và giới hạn

Chỉ tạo đúng hai file tại root:

- `PHONG-HOA-X01-C4-RETRIEVAL-RESEARCH.md`.
- `PHONG-HOA-X01-C4-RETRIEVAL-IMPLEMENTATION-BRIEF.md`.

Brief tự đủ exact source/base, target mới đề xuất `root\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, file scope hữu hạn, public interface/types/errors, fixture contract, TDD matrix, regression cần thiết, demo/evidence/report output và docs/ADR. Interpreter tuyệt đối `root\cti-platform-start\.venv\Scripts\python.exe`; không dùng PATH tùy ý. Không tạo target/branch/commit hoặc chạy test implementation trong lượt research.

Được đọc nguồn web công khai chính thống và file source liên quan; không gửi dữ liệu riêng lên dịch vụ, không tải lại snapshot 55 MB hoặc cài package. Kiểm Git source trước/sau; nếu ref/bẩn khác đã nêu, báo rõ và không ghi đè. Không sửa repo/RUNS/Leader review/evidence cũ. Không push/PR/merge/deploy, secret, model thật, DB/listener/browser app/lab.

Trả đúng đường dẫn, SHA-256 hai file, source HEAD/status trước/sau, kết luận phương án và mọi phần UNVERIFIED. Không tính research là test hoặc C4 hoàn thành. Leader nghiệm thu contract rồi mới giao implementation.
