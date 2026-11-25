# X01-GOLD-DATASET-NEXT — nghiên cứu bước dữ liệu đánh giá

Root: `$WORKSPACE`.

## Mục tiêu

Chọn bước ngoại tuyến nhỏ nhất để chuyển từ kiểm contract bằng sáu mẫu tổng hợp sang chuẩn bị dữ liệu đánh giá có nguồn và nhãn đáng tin. Kết quả là research và brief triển khai độc lập; không triển khai, không chạy model, không tuyên bố đã có corpus gold.

Owner CTI Research, làm trực tiếp, không giao bot/worker khác. Source chỉ đọc `root\cti-x01-c4-eval`, branch `feat/x01-c4-eval-20261111`, exact HEAD `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`.

## Đọc và tái dùng

- AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, extractor/dataset/GUIDELINE.md trên source.
- extractor/eval/README.md, run.py, report.py, evaluate.py và schema dataset hiện có; đọc theo câu hỏi, không khảo sát lại toàn repo.
- `root\PHONG-HOA-X01-C4-EVAL-ACCEPTANCE-20261111.md`, `PHONG-HOA-AI-EVAL-NEXT-RESEARCH.md`, `PHONG-HOA-X01-TTP-EVAL-RESEARCH.md`, `PHONG-HOA-X01-C4-EVAL-RESEARCH.md` để tránh nghiên cứu trùng.
- Hiện CLI chỉ nhận synthetic-smoke; GUIDELINE dữ liệu thật dùng metadata tên trường khác và TTP chưa được chấm semantic. Hãy xác nhận gap bằng file:line, không suy từ tên file.

## Câu hỏi cần giải và lựa chọn

1. Đối chiếu tối đa ba cách chuẩn bị: tái dùng dataset CTI công khai đã có nhãn; nhóm tự gán nhãn một pilot nhỏ; công cụ kiểm schema/nguồn/gán nhãn trước khi thu thập. Có thể khảo sát MITRE TRAM/CTI-Bench nếu phù hợp, phải dùng nguồn gốc, giấy phép và schema thật; không mặc định dữ liệu hợp mục tiêu hoặc được phép sao chép.
2. Phân biệt báo cáo gốc, bản dịch, mẫu tổng hợp, bản chèn lệnh, nhãn đề xuất bởi máy và nhãn do con người xác nhận. Không xem metadata tự khai là chứng minh hai người đã gán nhãn.
3. Chốt đơn vị đo IOC/TTP và evidence quote/span; parent/sub-technique, revoked/deprecated và version ATT&CK; cách giải bất đồng; nguồn, thời điểm, hash và quyền lưu dữ liệu. Chỉ tìm nguồn/metadata cần thiết, không tải bộ raw có bản quyền hoặc dữ liệu hạn chế vào repo/cloud.
4. Nêu cách giữ bộ đánh giá chưa nhìn trước khi tuning query/prompt; xử lý nguồn trùng/bản dịch/trùng campaign nếu có chứng cứ, không hứa chống leakage hoàn toàn. Phân biệt kiểm schema, kiểm độ đồng thuận và chứng minh đúng semantic.
5. Đề xuất một lát có thể triển khai ngay, ưu tiên hợp đồng dữ liệu + validator/read-only readiness report nếu đó là điểm thiếu nhỏ nhất. Giữ C1–C4 synthetic compatibility; không mở model thật/HTTP/DB/UI hoặc sửa schema artifact 1.0–1.2 chỉ để làm bước này. Nếu scorer TTP hay corpus download là bước sau, ghi dependency cụ thể.

## Đầu ra duy nhất được ghi

- `root\PHONG-HOA-X01-GOLD-DATASET-RESEARCH.md`: vấn đề thực tế, phương án/nguồn/ngày kiểm, phần tái dùng, quyết định khuyến nghị và chưa biết.
- `root\PHONG-HOA-X01-GOLD-DATASET-IMPLEMENTATION-BRIEF.md`: tự đủ cho CTI AI Agent/Sol medium; exact base/tree/branch đề xuất (chưa tạo), allowlist, schema/API/CLI nếu cần, bounds/type/Unicode/error/privacy contracts, test matrix, regression, output/evidence và done_when. Chốt các lựa chọn kỹ thuật nhỏ hợp lý, không để worker đoán.

Không sửa source/RUNS/acceptance, không cài dependency/tạo worktree/commit, không thực thi dữ liệu tải về, không model/secret/lab/push/PR/merge/deploy. Web chỉ dùng nguồn công khai phục vụ nghiên cứu; không upload tài liệu dự án hoặc dữ liệu CTI hạn chế.

Done: hai tài liệu có quyết định và brief khả thi, kiểm hash, source HEAD/status trước–sau không đổi; ghi rõ chưa triển khai/chưa có gold thật. Leader nghiệm thu rồi giao bước đã chọn, không cần người dùng nhắc tiếp.
