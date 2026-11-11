# Tiến độ (agent cập nhật sau mỗi task)

Cập nhật lần cuối: 11/11/2026

## Mốc
| Mốc | Hạn | Trạng thái |
|---|---|---|
| Đề cương gửi giảng viên | 03/11/2026 | Chưa |
| v0.1 lát cắt end-to-end | 24/11/2026 | Chưa |
| v0.5 MVP F01–F08 | 15/12/2026 | Chưa |
| Extractor + agent chạy trên dataset | 12/01/2027 | Chưa |
| Đóng băng tính năng, bản thảo đủ chương | 31/01/2027 | Chưa |
| Nộp quyển | 27/02/2027 | Chưa |

## Đang làm
- PR #1: bộ khởi động đầy đủ, chờ duyệt và merge
- Việc 2: cài OpenCTI trên máy Ubuntu
- F01/#9: gói demo MITRE + bundle STIX mẫu đã kiểm cấu hình ngoại tuyến; chờ chạy và đo trên lab

## Đã xong gần đây
- Tạo organization phonghoa-cti và repo cti-platform
- Thư viện phonghoa_core (47 test), spec MVP + portal + Hermes, mockup 5 màn, đề cương nháp
- Chi tiết bàn giao: docs/HANDOFF.md
- Baseline PR #46 tại `36259c118f519d3ac9cfc1f7b79e7180c2448a88`: 61 test đạt; Ruff check và format đạt
- Lập ma trận nguồn F01 tại `docs/wiki/Nguon-du-lieu-F01.md`: ưu tiên connector chính thức, gồm CISA KEV;
  `ImportFileStix` là đường nhập mẫu và không tính là feed
- Chuẩn bị `deploy/demo/` với OpenCTI LTS `7.260811.0-lts.2`, 8 image ghim digest và fixture STIX tổng hợp;
  Compose lõi/MITRE/ImportFileStix đã parse, thiếu secret bị từ chối
- Xử lý QA-01–03 cho gói demo: preflight kiểm UUIDv4/Base64/token không lộ input; quy trình ImportFileStix dùng
  bản nháp mặc định và analyst phê duyệt; tiêu chí provenance khớp từng loại object STIX
- X01/C1 ngoại tuyến: CLI dùng lại regex và bộ chấm điểm hiện có, chạy trên 6 mẫu tổng hợp Việt/Anh và xuất
  JSON tái hiện được theo báo cáo, micro và loại IOC; đây chỉ là smoke test, chưa phải đánh giá X01 trên dữ
  liệu thật
- X01 bước 1 bản nháp ngoại tuyến: CLI `.txt` tạo JSON `status=pending`, mỗi IOC có quote/span nguyên văn,
  SHA-256 nguồn, TLP mặc định AMBER, cảnh báo injection và allowlist
- X01 bước 2 kho bản nháp ngoại tuyến: CLI lưu mỗi draft pending thành bản ghi SQLite mới và đọc lại nguyên
  nội dung theo ID qua tiến trình khác; kiểm schema/hash/span, kiểu `language`/`tlp`, và IOC nằm đúng span
  evidence trên nguyên nguồn; có rollback, timeout khóa DB và chế độ đọc không tự tạo DB; chưa có duyệt/từ
  chối, HTTP, xác thực, model hoặc kiểm lab
- X01 bước 3 hợp đồng W05: đã ghi bảng trường schema offline 1.0, quy ước span Unicode, ba fixture `get` SQLite
  và gói handoff UI; đây là tài liệu/mẫu cục bộ, chưa triển khai HTTP, quyền, duyệt/từ chối, UI hay OpenCTI
- X01 hàng đợi ngoại tuyến: API/CLI liệt kê draft pending theo `id DESC` và cursor `before_id`, summary không
  chứa toàn văn; có thể chọn ID từ trang để đọc chi tiết, chưa có HTTP, quyền, duyệt/từ chối hoặc UI
- X01 QA kho/hàng đợi: `get` và `list` dùng chung kiểm payload/metadata khi đọc; `save/get/list` cùng từ chối
  timeout sai trước khi mở SQLite; dữ liệu hỏng không ghi đè output, chưa mở rộng sang HTTP, quyền hoặc UI
- X01 adapter C2/C3 ngoại tuyến: provider giả lập chỉ `fake_offline`/không egress, kiểm schema/TLP/metadata,
  retry một lần rồi fallback C1; C2 chỉ đánh giá, C3 dùng grounding/evidence hiện có. Đây là mock tổng hợp,
  chưa gọi hoặc đo model thật và không ghi SQLite/W05.
- X01 evaluator C2/C3 ngoại tuyến: chạy 6 fixture tổng hợp qua adapter; C2 chấm raw prediction, C3 chấm IOC
  sau grounding và giữ audit, metric tách `model_completed`/`regex_fallback`. C1 giữ nguyên; đây không phải
  benchmark model/corpus thật và không nối W05.
- X01 restricted ATT&CK catalog ngoại tuyến: loader stdlib đọc fixture STIX tổng hợp đã ghim hash, kiểm
  version/lifecycle/parent graph và tra active/inactive/unknown/invalid bằng kết quả bất biến. Semantic luôn
  `unverified`; rework R1/R2 đã phân biệt boolean với number trong exact JSON duplicate và chuyển đường dẫn
  NUL thành lỗi I/O an toàn.
- X01 ATT&CK official v20.1 ngoại tuyến: public `load_catalog` nhận đúng một bộ pin đã review và đọc nguyên
  snapshot local 55.277.605 byte thành 867 record (706 active, 161 inactive; 497 sub-technique), không cần
  provenance Phong Hỏa trong root MITRE. Synthetic giữ nguyên; asset không nằm trong repo và lookup vẫn
  `unverified`/không đủ điều kiện ghi draft. Đây là compatibility loader, không phải xác minh ngữ nghĩa TTP.
- X01 audit technique ngoại tuyến: public API bind SHA-256 UTF-8 của nguyên văn kết quả C2/C3 giả lập, kiểm
  quote literal/offset Unicode và trạng thái ID trên catalog đã nạp; output bất biến, luôn `unverified` và
  không đủ điều kiện ghi draft. Test module mới và regression adapter/catalog/grounding/evaluate/eval CLI
  đã đạt cục bộ; số đếm/lệnh/exit được lưu ở bằng chứng bàn giao của lát cắt này.
- X01 evaluator audit technique ngoại tuyến: C2/C3 có opt-in schema 1.1 để xuất từng quote/span và provenance
  catalog ATT&CK đã pin; mặc định schema 1.0, prediction/score IOC và retry/fallback giữ nguyên. Pin được đọc
  UTF-8 strict có bound 16 KiB, catalog chỉ nạp một lần và output atomic không được alias dataset/fixture/
  snapshot/pin. Đây vẫn là smoke bằng provider giả lập, không phải đánh giá ngữ nghĩa TTP hoặc chất lượng model.
- X01 reporter ngoại tuyến: CLI stdlib đọc cohort C1/C2/C3 schema 1.0 hoặc C2/C3 schema 1.1, kiểm projection,
  aggregate/mode/TTP consistency rồi dựng Markdown bất biến có hash từng input và nhãn synthetic. Publish mặc
  định no-clobber, chỉ overwrite khi có cờ và từ chối alias input; reporter không chấm lại prediction hoặc gọi
  model/mạng/catalog/DB. Đây là bảng smoke tổng hợp, không phải kết quả model/corpus thật.
- X01 component retrieval ATT&CK ngoại tuyến: canonical loader giữ optional description; lexical retriever trả
  raw result bất biến và JSON context có provenance, đo toàn envelope theo budget UTF-8. Ranking/tokenizer được
  kiểm bằng fixture tổng hợp Việt/Anh qua public loader và regression dùng asset Enterprise v20.1 local; chưa nối
  generator/model, chưa phải full C4/RAG hoặc bằng chứng chất lượng semantic.
- X01 adapter C4 context ngoại tuyến: wrapper kiểm báo cáo/TLP, gọi retriever lexical đúng một lần rồi gửi nguyên
  context có hash/provenance trong request bất biến cho provider giả lập; retry/fallback dùng lại C3 và public audit
  chỉ lấy evidence từ báo cáo gốc. Đây là kiểm hợp đồng bằng dữ liệu tổng hợp, chưa phải chất lượng model/RAG.
- X01 evaluator/reporter C4 ngoại tuyến: query manifest explicit, preflight toàn dataset trước generate, artifact
  schema 1.2 no-clobber và reporter nhận C4 đơn hoặc C3-audit+C4 cùng provenance. Demo vẫn dùng response
  fake_offline tổng hợp; không phải benchmark model/RAG/TTP semantic hoặc corpus thật.
- X01 gold-pilot readiness ngoại tuyến: validator/CLI kiểm inventory 5 record, quyền raw khai báo, hai annotation,
  evidence IOC token và TTP active từ catalog đã ghim; report bất biến/no-clobber và agreement chỉ phản ánh nhãn
  tổng hợp. Đây không phải corpus gold, quyền thật, hai người thật hay bằng chứng chất lượng model/RAG.

## Vướng mắc
- Bộ version mới chỉ được kiểm cấu hình; chưa pull image, boot service hoặc chứng minh tương thích/runtime trên lab
- Capability upload/review/approve, work ID, trạng thái draft trước/sau và quyền thực tế chưa kiểm trên lab
- Chưa gọi feed hoặc LLM, chưa có key/điều khoản OTX, chưa đo RAM/queue và chưa xác minh demo MITRE + OTX (#10)
- X01 còn thiếu dataset báo cáo thật được hai người gán nhãn, run model thật và C4/TTP; smoke C1/C2/C3 tổng
  hợp không chứng minh chất lượng extractor hoặc model
- Adapter mới chỉ chứng minh hợp đồng C2/C3 bằng response giả lập; chưa chọn provider/model, chưa có run model
  thật, token/chi phí/độ trễ, corpus hai người gán nhãn hoặc đánh giá TTP/C4
- ATT&CK official mới chỉ kiểm đúng Enterprise v20.1 local; release khác, chữ ký tag/commit, NOTICE riêng,
  C4/RAG, semantics TTP, OpenCTI/lab/production vẫn chưa xác minh
- Audit technique chỉ chứng minh source/quote/catalog consistency trên provider giả lập; semantic truth,
  model/provider thật, corpus/gold/F1 và C4/RAG vẫn chưa xác minh.
- Artifact evaluator schema 1.1 mới chỉ được kiểm ngoại tuyến với snapshot synthetic; semantic truth TTP,
  corpus hai người gán nhãn, model/provider thật, C4/RAG, lab và production vẫn chưa xác minh.
- Reporter chưa được dùng với corpus thật hoặc artifact model thật; semantic TTP, C4/RAG, khả năng chống power
  loss/hostile directory mutation, W05, OpenCTI, lab và production vẫn chưa xác minh.
- Retrieval lexical chưa được nối trước generation, chưa đo semantic/multilingual recall trên corpus hai người
  gán nhãn và chưa gọi model thật; ranking score chỉ là token overlap, không phải confidence hay semantic truth.
- C4 mới chỉ nối request với provider giả lập và query do caller truyền; chưa đo chống prompt injection, model thật,
  semantic/multilingual TTP, corpus hai người gán nhãn, OpenCTI, lab hoặc production. Evaluator/reporter chỉ kiểm
  contract deterministic trên fixture tổng hợp, không nâng mức bằng chứng chất lượng.
- Gold-pilot mới chỉ kiểm cơ chế bằng fixture tổng hợp; quyền raw thật, độc lập hai annotator, adjudication,
  semantic TTP, corpus gold/model quality, hostile mutation, crash/power-loss và production chưa xác minh.
