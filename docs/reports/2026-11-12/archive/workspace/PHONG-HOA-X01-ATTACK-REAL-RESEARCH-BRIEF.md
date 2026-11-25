# X01-ATTACK-REAL-NEXT — dữ liệu MITRE thật và brief compatibility

Ngày 11/11/2026. Owner CTI Research. Nghiên cứu + đọc dữ liệu công khai, **chưa triển khai code sản phẩm**. Dự án còn active; đây là bước phụ thuộc sau catalog synthetic đã nghiệm thu.

## Mục tiêu và nền có sẵn

Chọn cách nhỏ nhất kiểm catalog với một snapshot Enterprise ATT&CK STIX2.1 chính thức, ghim nguồn/phiên bản/SHA256; trả brief triển khai tự đủ cho CTI AI Agent/Sol medium. Lý do: test fixture không chứng minh loader tương thích dữ liệu MITRE thật. Tái dùng stdlib loader trước; chỉ đề xuất dependency khác khi có khoảng trống cụ thể.

Source chỉ đọc `$WORKSPACE\cti-x01-attack-offline`, branch feat/x01-attack-offline-20261111, exact HEAD **4e894c37df3ad53c16022909ae6df113dd89aa04**. Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, docs/adr/0004-x01-restricted-attack-catalog.md, extractor/phonghoa_extractor/attack_catalog.py. Dùng PHONG-HOA-X01-ATTACK-RESEARCH.md, LEADER-PLAN.md, CODE-REVIEW-20261111.md, ACCEPTANCE-20261111.md ở workspace này. Không nghiên cứu lại toàn bộ AI, không giao bot khác.

## Công việc

1. Xác minh nguồn chính thức: https://github.com/mitre-attack/attack-stix-data , USAGE.md/index.md, release/tag/commit, ATT&CK schema và điều khoản/NOTICE liên quan của chính nguồn. Chọn bản Enterprise versioned đang khả dụng (v20.1 là ứng viên từ nghiên cứu trước, phải kiểm lại); không dựa mutable master/latest làm pin. Tối đa so hai cách trực tiếp hữu ích: tái dùng loader so với thành phần MITRE/STIX có sẵn khi thật sự cần.
2. Được tải **một** JSON snapshot công khai từ nguồn MITRE chính thức để đọc/kiểm metadata, kèm thông tin bản quyền/NOTICE chính thức. Lưu dưới thư mục evidence được phép, giữ nguyên bytes, giới hạn đọc/download64 MiB với timeout hữu hạn; nếu lớn hơn báo kích thước và đề xuất, không tự bỏ giới hạn. Không tải/chạy code hay package, không gọi TAXII/LLM/OpenCTI/lab. Dữ liệu chỉ là danh mục tham chiếu công khai, không dùng báo cáo CTI riêng.
3. Ghi provenance từ quan sát thật: exact immutable commit/filepath/download URL, tên phiên bản, byte count, SHA256 exact bytes, thời điểm, nguồn LICENSE/NOTICE. Không bịa commit/hash hay suy version từ tên file. Nếu không tải/xác minh được, ghi UNVERIFIED chính xác và vẫn hoàn thành brief.
4. So dữ liệu thực với policy restricted hiện có: trường/schema/domain, nhiều version/lifecycle, active/inactive, parent graph, refs, precision/duplicate, root provenance, size. Được viết script inventory chỉ đọc trong evidence (stdlib; không sửa/vượt rào loader); báo số lượng và ví dụ STIX id cho mỗi khác biệt. Không thêm synthetic provenance vào bytes MITRE, không đổi kind thành synthetic để lách official-pin rejection. Không gọi inventory là test compatibility sản phẩm.
5. Brief chốt pin official/provenance verification, licensing/NOTICE cần giữ trong artifact, cách cung cấp snapshot ngoại tuyến, trust boundary không tự tải lúc lookup, backward compatibility synthetic, lỗi/bounds/invariants, fixtures và ma trận test. Quyết định policy phải có lý do nguồn hoặc ghi là policy Phong Hỏa; không âm thầm bỏ record khó để tạo PASS. Chốt exact base, tree mới đề xuất, file scope, interpreter và lệnh kiểm phù hợp, output/evidence, điều còn chưa biết. Không mở adapter/C4/RAG/semantic/model trong lát cắt này.

## Đầu ra và giới hạn

Chỉ ghi:
- `$WORKSPACE\PHONG-HOA-X01-ATTACK-REAL-RESEARCH.md`
- `$WORKSPACE\PHONG-HOA-X01-ATTACK-REAL-IMPLEMENTATION-BRIEF.md`
- `$WORKSPACE\x01-attack-real-research-evidence\` (snapshot nguyên bản, metadata/inventory/script đọc dữ liệu và manifest cần thiết).

Không sửa repo, RUNS, tài liệu cũ hoặc probe Leader; không tạo worktree/commit/push/PR/merge/deploy, không package/secret/cloud/model/DB/UI. Kiểm Git HEAD/status trước và sau source, SHA của hai tài liệu và manifest, tất cả lệnh đọc dữ liệu có exit. Nêu rõ đọc tài liệu, inventory thực chạy và code sản phẩm chưa triển khai. Việc tên mã tồn tại trong catalog không chứng minh đúng ngữ nghĩa TTP.

Sau khi trả hai tài liệu đủ dùng, Leader review rồi giao implementation riêng; không tự triển khai hoặc giao bot khác.
