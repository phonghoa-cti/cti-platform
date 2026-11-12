# X01-EVAL-REPORT-NEXT — brief nghiên cứu

Ngày 11/11/2026. Owner CTI Research. Chỉ nghiên cứu/hợp đồng, không triển khai/test sản phẩm.

Root `$WORKSPACE`.
Nguồn chỉ đọc `$WORKSPACE\cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`, HEAD `984bd2136872f4c5fba4118e33cf02b5ca615f2d` sạch đã nghiệm thu.
Đọc AGENTS.md, docs/PROGRESS.md và docs/specs/X01-ai-extractor.md (phần Đánh giá yêu cầu extractor/eval/report.py).
Đọc acceptance `PHONG-HOA-X01-TTP-EVAL-ACCEPTANCE-20261111.md`, code evaluator/score và artifact examples trong `x01-ttp-eval-evidence` nếu cần; không lặp research catalog/audit hoặc claim worker report là kiểm chứng của bạn.

## Mục tiêu

Nghiên cứu bước nhỏ tạo **bảng báo cáo đánh giá offline** từ artifact đã có, để người học hiểu và tái lập số liệu C1/C2/C3. Tách synthetic smoke khỏi chất lượng model/corpus thật. Không chờ lab, không mở C4. So tối đa ba phương án, đánh giá tái dùng stdlib/current metrics/formatter trước khi đề xuất dependency. Ưu tiên reporter CLI thuần, artifact JSON → bảng Markdown có nhãn và provenance; quyết định cuối cần giải thích tradeoff từ contract thực.

## Những chỗ phải chốt bằng đọc source + nguồn chính thức

- Inventory chính xác schemas C1/C2/C3 hiện hữu (1.0, opt-in1.1), metric modes/model_completed/regex_fallback, C3 regex-merged, per-type/per-doc/aggregate, empty/unavailable, source/data/response/pin hashes và evaluator refs.
- Bảng nào có ích trước; một hay nhiều input, yêu cầu nào để so sánh được; không âm thầm trộn dataset/hash/config/mode/provider/prompt khác hoặc giả model-only. Trình bày không so được rõ nếu chọn cho phép; quyết định đơn giản, không khung tổng quát.
- Counts TTP là số đếm consistency, không precision/recall/F1/detection rate; semantic unverified/draft false. Không biến active/matched thành TP/gold. C4 unsupported phải rõ.
- Reporter hiển thị metric đã có hay tính lại từ counts; invariant cần validate để không xuất bảng số mâu thuẫn. JSON strict/types/bounds/schema unknown/nonfinite/duplicates, safe error/output preservation. Không cần lộ source/quote/IOC hay đường file riêng tư vào bảng; kiểm Markdown escaping cho nhãn không tin cậy.
- Determinism/provenance, input hashes, Git ref khác do formatter commit, newline/Unicode; output atomic và chống ghi đè/alias input. Không đổi evaluator hoặc artifact baseline chỉ để thuận renderer.
- Tài liệu/thư viện đã có, nguồn chính thức tối thiểu cần cho lựa chọn. Ghi tên/link và phần tái sử dụng; không coi tài liệu là đã chạy test.
- Brief độc lập cho CTI AI Agent Sol medium: exact base, target đề xuất `$WORKSPACE\cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`, file scope nhỏ (report.py/test/README/PROGRESS/ADR nếu cần), public interface/CLI/schema/errors, matrix TDD và regression liên quan, demo từ local artifacts, interpreter tuyệt đối `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`.
- Bàn giao implementation dự kiến `$WORKSPACE\PHONG-HOA-X01-EVAL-REPORT-RESULT.md` và `$WORKSPACE\x01-eval-report-evidence\`. Không mở implementation trước Leader nghiệm thu nghiên cứu.

## Chỉ hai đầu ra được ghi

1. `$WORKSPACE\PHONG-HOA-X01-EVAL-REPORT-RESEARCH.md`
2. `$WORKSPACE\PHONG-HOA-X01-EVAL-REPORT-IMPLEMENTATION-BRIEF.md`

Không sửa repo/RUNS/Leader review/evidence cũ, không tạo worktree/commit, không chạy test hoặc cài dependency, không model/secret/DB/W05/OpenCTI/lab/push/PR/merge/deploy. Không giao bot/helper. Tra nguồn công khai được phép, không gửi dữ liệu CTI lên dịch vụ. Kiểm HEAD/status trước/sau. Trả 2 paths/hash, khuyến nghị, phần còn chưa biết; chỉ gọi PASS nghiên cứu khi hai docs đủ giao người thực hiện độc lập.
