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
- W05-B review ngoại tuyến: schema SQLite migration version 1 giữ nguyên payload 1.0, tác giả subject cho draft
  mới, policy Actor analyst/admin, approve/reject đúng một lần với optimistic concurrency và atomic audit;
  get/list vẫn chỉ đọc kể cả schema legacy, approve không gọi OpenCTI. Đây chưa phải xác thực HTTP/JWT, UI,
  chỉnh item, ingestion OpenCTI hoặc audit chống sửa file database.
- W05 API cục bộ: FastAPI có ba route list/detail/decision, xác minh JWT RS256/issuer/audience/claims bằng khóa
  RSA tổng hợp, role lookup phía server và POST bắt buộc Origin + JSON; lỗi/no-store/schema response đã có test
  in-process. Audience chuỗi/mảng exact membership, lỗi bất ngờ no-store và số quá dài 422 đã có regression.
  Chưa kiểm Cloudflare/JWKS thật, listener, browser frontend, lab hoặc OpenCTI.
- W05 tích hợp browser cục bộ: harness test-only nối nguyên snapshot UI với FastAPI qua gateway same-origin loopback,
  JWT RSA tổng hợp được xác minh thật, role phía server và SQLite tạm; ma trận HTTP kiểm auth/Origin/decision/audit,
  cleanup và lỗi POST thành công nhưng refresh 503 không retry. Đây không phải integration lab, HTTPS/JWKS thật,
  OpenCTI, deployment hoặc thay thế quy tắc HTTPS của cấu hình production.
- W05 selection core: schema SQLite v2 lưu snapshot IOC đủ điều kiện bằng audit riêng, migrate v0/v1 nguyên tử,
  version đồng thời và quyết định cuối tham chiếu snapshot/hash; payload/evidence không đổi. Đây là core-only,
  chưa tương thích API/UI hiện giới hạn version 0/1 và chưa nhập OpenCTI.

## Vướng mắc
- Bộ version mới chỉ được kiểm cấu hình; chưa pull image, boot service hoặc chứng minh tương thích/runtime trên lab
- Capability upload/review/approve, work ID, trạng thái draft trước/sau và quyền thực tế chưa kiểm trên lab
- Chưa gọi feed hoặc LLM, chưa có key/điều khoản OTX, chưa đo RAM/queue và chưa xác minh demo MITRE + OTX (#10)
- X01 còn thiếu dataset báo cáo thật được hai người gán nhãn và các cấu hình C2–C4; smoke C1 không chứng minh
  chất lượng extractor hoặc TTP
