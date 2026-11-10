# Tiến độ (agent cập nhật sau mỗi task)

Cập nhật lần cuối: 10/11/2026

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

## Vướng mắc
- Bộ version mới chỉ được kiểm cấu hình; chưa pull image, boot service hoặc chứng minh tương thích/runtime trên lab
- Capability upload/review/approve, work ID, trạng thái draft trước/sau và quyền thực tế chưa kiểm trên lab
- Chưa gọi feed hoặc LLM, chưa có key/điều khoản OTX, chưa đo RAM/queue và chưa xác minh demo MITRE + OTX (#10)
