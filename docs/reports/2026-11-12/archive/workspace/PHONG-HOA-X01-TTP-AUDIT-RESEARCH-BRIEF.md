# X01-TTP-AUDIT-NEXT — nối catalog và bằng chứng kỹ thuật

Ngày 11/11/2026. CTI Research, chỉ nghiên cứu/brief. Không triển khai hoặc giao bot khác.

## Mục tiêu

Chọn lát cắt offline nhỏ nhất có ích để dùng catalog đã nghiệm thu kiểm mã kỹ thuật trong kết quả AI giả lập và đối chiếu vị trí câu trích trong văn bản. Phân biệt ba khái niệm: mã tồn tại/còn hoạt động; câu trích thật sự có trong nguồn; hành vi thật sự phù hợp kỹ thuật. Hai kiểm tra đầu **không chứng minh kiểm tra thứ ba**, và lookup đơn thuần không phải RAG/C4.

Root: `$WORKSPACE`.

Source chỉ đọc `<root>\cti-x01-attack-official`, exact HEAD `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`, branch `feat/x01-attack-official-20261111`. Không dựa main hoặc tree W05. Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, ADR0004 và các file liên quan:

- `extractor/phonghoa_extractor/attack_catalog.py`, `llm_adapter.py`, `grounding.py`, `evidence.py`, `evaluate.py`, `llm_fixture.py`.
- `extractor/eval/run.py`, test catalog/official/adapter/eval và dataset GUIDELINE khi liên quan.
- Trong root: PHONG-HOA-AI-NEXT-RESEARCH.md, PHONG-HOA-AI-IMPLEMENTATION-BRIEF.md, PHONG-HOA-X01-ATTACK-RESEARCH.md, PHONG-HOA-X01-ATTACK-REAL-LEADER-PLAN.md và ACCEPTANCE-20261111.md.

## Quan sát đã có để tránh nghiên cứu lặp

- Catalog nhận synthetic hoặc đúng một official pin v20.1; lookup immutable luôn semantic unverified/eligible false. Real asset ngoài repo đã có/hash kiểm, không cần tải nữa.
- `llm_adapter._semantic_items` giữ techniques/malware/actors trong `unverified_semantic_items`, từng item eligible false. `C3` top-level eligible true dành cho IOC grounded, **không được dùng để nâng quyền semantic item**.
- Adapter hiện kiểm strict shape kỹ thuật; C1/C2/C3 đã có output/evaluation regression. C4 vẫn bị từ chối. Không âm thầm thay contract mặc định hoặc gọi một audit là hoàn tất C4.
- Helper cũ `ground_techniques(raw_items, known_ids)` ép str/strip/uppercase và giữ item mặc định; không kiểm trích dẫn/active state. Đánh giá khả năng tái dùng có giới hạn, không bọc lại rồi nhận là an toàn.
- `find_evidence_span` hiện yêu cầu IOC và token IOC. Kỹ thuật không bắt buộc có chuỗi `Txxxx` trong quote; không ép quote chứa ID để tạo false negative.

## Nghiên cứu và quyết định phải trả

1. Tái dùng nguồn chính đã đọc, chỉ bổ sung tài liệu chính thức cần cho mapping ATT&CK/bằng chứng và định nghĩa RAG; tối đa 2–3 cách trực tiếp hữu ích. So helper/audit tách khỏi output hiện tại, opt-in adapter integration, hoặc bước C4 đầy đủ; chọn cách nhỏ nhất đạt mục tiêu mà chưa cần model/dataset thật. Ghi phần tái dùng và tradeoff, không làm khảo sát framework rộng.
2. Chốt input/output/API, provenance/source SHA/catalog pin, immutable/non-mutation, schema/error taxonomy và bounds. Phải có đường demo sử dụng **kết quả thật của ScriptedProvider/adapter đã có** với catalog; không chỉ demo helper bằng dict tự dựng rồi gọi là đã nối adapter.
3. Chốt policy active/inactive/unknown/invalid ID, no catalog/error, missing/empty quote, quote không tồn tại, quote lặp/Unicode emoji/NFC-NFD/CRLF, vị trí theo code point, duplicate item/order. Policy do Phong Hỏa chọn phải ghi rõ, không gán cho MITRE. Không echo raw input trong lỗi; report cần bằng chứng thì giữ có giới hạn, không toàn văn/mạng.
4. Semantic status vẫn unverified, từng technique không eligible/không tự keep/approve; actor/malware chưa triển khai. IOC và legacy C1/C2/C3 không đổi theo mặc định; C4/RAG không được quảng cáo nếu không có retrieval-context-generation thật. TLP không được suy từ spec cũ rằng GREEN tự động được gửi cloud; toàn lát cắt offline fake only.
5. Test matrix gồm success và failures, strict kiểu list/dict/bool/number, input/adapter result không bị sửa, source mismatch, parent/inactive, deterministic/duplicate, dữ liệu chèn lệnh không gây tác động, no provider extra call/network/DB và C1–C3 regression. Không dùng tổng hợp làm F1 hay chất lượng model/TTP thật.
6. Brief tự đủ để giao **một CTI AI Agent/Sol medium**: exact base, đề xuất tree `<root>\cti-x01-ttp-audit`, branch `feat/x01-ttp-audit-20261111`, file scope tối thiểu, interface, TDD, lệnh kiểm, artifact/evidence/result. Interpreter absolute `<root>\cti-platform-start\.venv\Scripts\python.exe`. Không tự mở thêm CLI/API/UI nếu chưa cần cho demo library.

## Đầu ra được phép

Chỉ ghi hai file tại root:

- `PHONG-HOA-X01-TTP-AUDIT-RESEARCH.md`
- `PHONG-HOA-X01-TTP-AUDIT-IMPLEMENTATION-BRIEF.md`

Không sửa source/RUNS/tài liệu cũ; không tạo worktree/commit, không cài package, không tải thêm snapshot, không chạy implementation/model/lab, không secret/DB/listener/push/PR/merge/deploy. Dùng web chỉ để đọc nguồn công khai cần thiết; không gửi dữ liệu CTI riêng ra ngoài.

Trả SHA-256 hai tài liệu, Git HEAD/status trước-sau, nguồn đã đọc và phần chưa xác minh. Sau review Leader mới giao code. Đây là tiến bước trong X01, không kết luận dự án đã hoàn thành.
