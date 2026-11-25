# X01-C4-ADAPTER-NEXT — nghiên cứu nối context trước generation ngoại tuyến

Ngày 11/11/2026. Owner CTI Research. Chỉ nghiên cứu và viết hợp đồng triển khai; không sửa source hoặc chạy implementation.

## Mục tiêu và nguồn

Chọn lát cắt nhỏ nhất để nối retrieval ATT&CK đã nghiệm thu vào đầu vào provider giả lập, rồi tái dùng đối chiếu IOC/audit technique hiện có. Có thể kiểm việc đưa đúng context vào request bằng provider ghi nhận request trong bộ nhớ; không tuyên bố model hiểu context hoặc đạt chất lượng TTP.

Root tuyệt đối: `$WORKSPACE`.
Source chỉ đọc: `root\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, exact HEAD `d97f96362edcd92e87fc69cfa20a563109cec550`, trạng thái sạch. Kiểm trước/sau; không checkout/reset/commit/create worktree.

Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, docs/adr/0007-x01-offline-attack-retrieval.md và docs/prompts/extractor-v1.md nếu có. Tái dùng nghiên cứu trong root: PHONG-HOA-X01-C4-RETRIEVAL-RESEARCH.md, PHONG-HOA-X01-C4-RETRIEVAL-LEADER-PLAN.md, PHONG-HOA-X01-C4-RETRIEVAL-ACCEPTANCE-20261111.md; AI adapter/TTP audit/evaluator briefs khi cần. Code cần đối chiếu: extractor/phonghoa_extractor/{attack_catalog,attack_retrieval,llm_adapter,ttp_audit,grounding}.py, CLI/fixtures và các test liên quan. ProviderRequest/LLMProvider/ScriptedProvider nằm trong llm_adapter.py; không có llm_provider.py.

## Câu hỏi phải chốt

1. So tối đa 2–3 phương án nối context, ưu tiên tái sử dụng adapter/retry/grounding thay vì copy pipeline. Phân biệt lựa chọn kỹ thuật từ code với claim từ tài liệu; đối chiếu nguồn chính thức hoặc bài nghiên cứu gốc còn phù hợp. Không nghiên cứu lại toàn bộ C4/retrieval.
2. Hợp đồng public API nhỏ nhất: C4 qua wrapper hay mở rộng adapter; cách truyền catalog/query/top_k/budget/context vào request; tương thích constructor/API và C2/C3 artifacts. Chốt exact fields/types/bounds, cấu trúc result/provenance và error taxonomy cho worker Sol medium.
3. Source report phải tách khỏi ATT&CK knowledge: không ghép catalog vào source_text để grounding/audit; quote/span chỉ đối chiếu báo cáo gốc, source hash giữ cùng quy tắc UTF-8. Mọi technique vẫn semantic unverified/eligible=false; không coi catalog match là bằng chứng TTP đúng ngữ cảnh hoặc đủ điều kiện draft.
4. Query retrieval hiện có tối đa 512 code point/4 KiB UTF-8, trong khi report có thể dài: chốt chính sách explicit bounded query hay xây query deterministic, hành vi empty/tokenless/zero-match, tiếng Việt/Anh, overflow. Không cắt ngầm báo cáo dùng để grounding, không dựa query do model sinh thêm.
5. Context trước generate: JSON/delimiter/instruction version và nguồn dữ liệu không tin cậy; chống nhầm knowledge với instruction khi chứa thẻ đóng, URL hoặc chuỗi chèn lệnh. Prompt containment bằng cấu trúc chỉ là cơ chế; không tuyên bố chống mọi prompt injection khi chưa chạy model.
6. Retry/fallback giữ hữu hạn, không thêm lần gọi provider vì retrieval/audit; thất bại validation/pin/query/budget phải có thứ tự và provider call count rõ. Metadata C4 completed/fallback phải phản ánh thật, không đổi nhãn C3 thành C4 mà chưa truyền context. Provider vẫn fake_offline, egress=false; không mở cloud kể cả TLP:GREEN, không nới TLP/quyền.
7. Tách phạm vi: khuyến nghị library/request seam trước; evaluator/reporter/CLI C4 chỉ mở nếu chứng minh cần cho lát nhỏ này và ghi rõ chi phí. Không thay evaluator schema 1.0/1.1 hoặc mở W05/DB/API/UI để hoàn thành task này. Đề xuất bước tiếp riêng cho evaluation sau khi adapter được nghiệm thu.
8. Acceptance matrix: source/knowledge separation, provider nhận context, Unicode, zero-match, deterministic provenance/hash, bounds, invalid types/pins, inactive lifecycle, call counts/retry/refusal/incomplete/fallback, no mutation/no egress, C1–C3 regressions. Không biến fake provider thành evidence model quality.

## Hai đầu ra duy nhất

- `root\PHONG-HOA-X01-C4-ADAPTER-RESEARCH.md`: mục tiêu, nguồn có link/ngày, đối chiếu cách có sẵn và phần tái dùng, lựa chọn/đánh đổi, phần chưa biết.
- `root\PHONG-HOA-X01-C4-ADAPTER-IMPLEMENTATION-BRIEF.md`: tự đủ cho CTI AI Agent Sol medium, exact base/source, đề xuất target `root\cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`; file allowlist chính xác, interface/errors, fixtures mới không đổi pinned cũ, TDD, scoped regression/lint/demo, ADR/PROGRESS và đường report/evidence. Đây là đề xuất, chưa tạo tree hay giao code.

Trả hash hai tài liệu và source HEAD/status trước/sau. Chỉ viết hai tài liệu trên; không RUNS/review/code/tests/dependencies, không tải asset mới, không model/network integration/secret/DB/listener/lab/push/PR/merge/deploy. Tra cứu tài liệu công khai qua công cụ nghiên cứu được phép; không đọc folder riêng của bot khác. Không giao tiếp bot khác. Nếu hợp đồng còn lựa chọn có thể đảo ngược, chọn và giải thích, không hỏi người dùng giữa chừng.
