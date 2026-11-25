# X01-LOCAL-INGEST-NEXT — nghiên cứu nạp file cục bộ

Root: `$WORKSPACE`.

## Mục tiêu, hiện trạng

Chuẩn bị lát sản phẩm nhỏ nhất để người dùng đưa file văn bản/PDF có lớp text vào X01 ngoại tuyến, có nguồn gốc và giới hạn rõ ràng. Đây là bước 1 đã có trong `docs/specs/X01-ai-extractor.md`, không phải công cụ đánh giá mới. Corpus người thật đang thiếu quyền/nhân sự; dùng fixture tổng hợp cho đề xuất kiểm thử, không chờ hoặc giả lập nhãn người thật.

Source chỉ đọc `<root>\cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`. Đọc AGENTS.md, docs/PROGRESS.md, spec X01; `extractor/draft/run.py`, `extractor/llm/run.py`, `phonghoa_extractor/{drafts,evidence,injection,llm_adapter}.py`, dependency manifests liên quan. CLI draft hiện chỉ nhận `.txt`, mặc định AMBER, chưa có loader PDF trong thư viện. Source giữ nguyên; không lấy branch main thay cho trạng thái này.

## Hai đầu ra duy nhất

1. `<root>\PHONG-HOA-X01-LOCAL-INGEST-RESEARCH.md`: so tối đa ba phương án thực tế (text trước; text + thư viện PDF có sẵn; tái sử dụng converter khác nếu hợp lý). Mở tài liệu chính thức, kiểm licence/dependency/giới hạn, ghi phần tái sử dụng và khuyến nghị nhỏ nhất. Chưa chọn thư viện thay Leader. Có thể đề xuất hoãn PDF nếu chưa đủ cơ sở, nhưng phải giải thích phần nào giúp người dùng ngay.
2. `<root>\PHONG-HOA-X01-LOCAL-INGEST-IMPLEMENTATION-BRIEF.md`: hợp đồng đủ giao CTI AI Agent/Sol medium, tree mới đề xuất `cti-x01-ingest-local`, branch `feat/x01-ingest-local-20261111`, exact base như trên; allowlist file, API/CLI/DTO/lỗi hữu hạn, phạm vi compatibility, acceptance/TDD, lệnh kiểm và bằng chứng/cleanup.

## Các quyết định cần nghiên cứu/chốt trong đề xuất

- Giữ raw-byte hash riêng với canonical-text hash; LF/Unicode/evidence offset áp dụng trên văn bản nào; provenance PDF page/text không được giả là vị trí byte trong PDF. Không trim/chuẩn hóa làm sai evidence nếu chưa có contract rõ.
- Input không tin cậy: giới hạn byte/page/text, lỗi malformed/encrypted/image-only/empty, timeout hoặc memory exhaustion của parser và cách kiểm offline. Không chạy JavaScript, attachment, liên kết ngoài hay OCR. Nêu ranh giới không thể chứng minh chống mọi PDF độc hại.
- TLP mặc định AMBER phù hợp spec; metadata local không tự mở quyền gửi cloud. Không suy licence/TLP từ nội dung file hoặc URL công khai.
- Chọn đường nối nhỏ tới regex draft/evidence hiện có; cân nhắc API library/CLI riêng so với sửa CLI cũ, tránh phá C1–C4 artifacts. Output atomic/no-clobber, alias/input preservation, không log raw/path nhạy cảm; các yêu cầu chỉ áp dụng nơi thực sự cần ghi.
- Dependency mới nếu cần: phiên bản/licence/support chính thức, lock/hash và kiểm offline đề xuất; không cài trong nhiệm vụ này. Tận dụng thư viện/writer có sẵn khi phù hợp, không refactor ngoài mục tiêu.
- Fixtures tổng hợp có nguồn gốc rõ; test Việt/Anh, emoji/newline, bounds, malformed, không mạng, lỗi giữ nguyên input/output. Giữ riêng chất lượng text PDF thật chưa kiểm khỏi contract fixtures.

## Giới hạn và bàn giao

Một CTI Research làm trực tiếp, không giao bot khác. Chỉ viết hai tài liệu nêu trên. Không sửa repo/RUNS/review; không tạo worktree/commit, cài dependency, chạy implementation hoặc mở/tải corpus/PDF không tin cậy. Nghiên cứu web chính thức được phép; không đăng nhập, secret, model/cloud, listener, lab, push/PR/merge/deploy. Kiểm HEAD/status trước/sau, hash hai output; tự đối chiếu brief với chữ ký mã hiện có. Nếu thiếu bằng chứng, ghi UNVERIFIED, không bịa kết quả test. Leader sẽ chọn phương án và nghiệm thu trước khi giao code.
