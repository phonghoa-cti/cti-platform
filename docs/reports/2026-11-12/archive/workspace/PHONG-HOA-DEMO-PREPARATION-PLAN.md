# Chuẩn bị demo F01 — kế hoạch triển khai

Ngày: 10/11/2026. Leader chọn phạm vi này để tiếp tục yêu cầu bắt đầu của người dùng.

> Người triển khai: CTI Engineer, Sol medium; một người sửa checkout. Không giao việc tiếp. Dùng quy trình triển khai tuần tự và kiểm chứng của team, không mở thêm agent.

**Mục tiêu:** Có gói cấu hình OpenCTI tối thiểu, ghim phiên bản và dữ liệu STIX tổng hợp, đủ để kiểm tra cấu hình trước khi chạy lab.

**Kiến trúc:** Gói độc lập trong `deploy/demo/`, kế thừa cấu hình upstream đã cố định ref. Dùng OpenCTI, một worker, Redis, Elasticsearch, kho S3 và RabbitMQ; MITRE và ImportFileStix được bật riêng sau khi lõi khỏe. Chưa cần OTX, XTM One, XTM Composer hoặc AI cho gói đầu.

**Công nghệ:** Docker Compose; OpenCTI LTS `7.260811.0-lts.2`; STIX 2.1 JSON; công cụ kiểm tra cấu hình và STIX được ghim phiên bản.

**Spec/căn cứ:** `docs/specs/F01-thu-thap-feed.md`, `docs/wiki/Nguon-du-lieu-F01.md`, `PHONG-HOA-INITIAL-RESEARCH.md`, `PHONG-HOA-F01-CONNECTOR-MATRIX.md`. Đây là lát cắt chuẩn bị, không thay tiêu chí đủ 5 feed của F01 hoặc MITRE+OTX của #10.

## Phạm vi và nguồn đã kiểm tra

- Checkout: `$WORKSPACE\cti-platform-start`.
- Base mới: commit tài liệu `7775fee8c456f15dca3e7202b9265f29b0a5f103`; giữ nguyên core/extractor đã có 61 test đạt ở parent.
- Upstream Compose: `OpenCTI-Platform/docker` commit `60285adb360e3823a334333ae4744255d8ac1821`; file `docker-compose.yml` blob `d055f43cdf436c641cd64a9a42a22833c1985a40`. Đây là nguồn cấu trúc, không phải chứng nhận nó tương thích bộ LTS.
- OpenCTI release: `957087377304ea548fcd9f83a4ee2b025c855d9b`; connector release: `d50686be6f64eb2e91ac38b23c45d0460a210435`.
- Leader đã kiểm HEAD manifest registry: platform, worker, MITRE, ImportFileStix, OTX, CISA đều HTTP 200, digest khớp bảng nghiên cứu. Chưa pull/chạy image.
- Image cho gói đầu chỉ lấy bốn thành phần OpenCTI cần dùng; ghim cả các dependency bằng tag/digest đã kiểm, lưu bằng chứng nguồn. Không dùng `latest` trong cấu hình hiệu lực.
- Không cài Docker Engine/Desktop, khởi động container, đổi quyền hệ thống, mở cổng mạng, dùng key thật, gọi feed/LLM, push, PR, merge hoặc deploy ở lượt này.
- Chỉ công bố cổng OpenCTI tại `127.0.0.1`; các dependency ở mạng nội bộ Compose, không publish cổng. Không Docker socket, privileged, host network hay tài khoản connector dùng mặc định token admin.
- Các giá trị bí mật bắt buộc đi qua biến môi trường, mẫu để trống và có kiểm tra thiếu giá trị. Không đọc `.env` thật. Dữ liệu test cấu hình phải được ghi rõ là giả và không dùng để chạy lab.
- Connector giới hạn cấu hình 256 MB theo F01; việc giới hạn này đủ vận hành còn UNVERIFIED. Giữ một worker, ghi phép đo RAM/queue cho lượt lab.

## Điểm cần kiểm tra tập trung

1. Thiếu biến bắt buộc phải làm kiểm tra cấu hình thất bại trước khi chạy.
2. Bộ image phải có digest và kiến trúc linux/amd64, không trôi theo tag hoặc kéo nhầm release.
3. Luồng mặc định chỉ khởi động lõi; connector nạp dữ liệu cần được bật riêng. Không tự bật OTX/AI hoặc dịch vụ quản lý container.
4. Bundle phải hợp chuẩn, mọi tham chiếu nội bộ giải được, nguồn tổng hợp rõ ràng; không gán bằng chứng tấn công thật cho IP/domain minh họa.
5. Kết quả parse/validate không được báo thành boot, import hoặc chống tạo trùng đã đạt.

## Việc 1 — Gói cấu hình có thể kiểm tra độc lập

File: `deploy/demo/compose.yml`, `deploy/demo/compose.mitre.yml`, `deploy/demo/compose.import.yml`, `deploy/demo/.env.example`, `deploy/demo/images.lock.json`, `deploy/demo/README.md`; thêm đúng file upstream phụ thuộc cần thiết, chẳng hạn `rabbitmq.conf`, với nguồn/license rõ. Không chỉnh cấu hình deploy cũ.

- [ ] Đọc schema cấu hình tại đúng release; chọn subset upstream và ghi mọi điều chỉnh trong README. Kiểm nguồn các dependency trước khi ghim; không suy từ HTTP 200 rằng schema đúng.
- [ ] Tạo cấu hình lõi và hai file bổ sung cho connector, biến bắt buộc và token connector riêng. Lõi không yêu cầu token connector chưa bật; chỉ ghép file MITRE/import khi cần. Ghi trong README bước tạo tài khoản/quyền để người vận hành thực hiện sau, không tự đổi quyền.
- [ ] Lưu `images.lock.json`: tên image, tag, digest, nền tảng, ref/URL nguồn, thời điểm kiểm tra. Các image được chạy phải khớp manifest này.
- [ ] Dùng Docker Compose để kiểm tra với giá trị giả: thiếu biến phải thất bại; đủ biến phải `config --quiet` exit 0; kiểm danh sách services/images cho mặc định và từng nhóm.
- [ ] Nếu Docker CLI không có, có thể dùng bản Compose standalone chính thức tải vào thư mục công cụ riêng, xác minh checksum/version; không cài daemon hoặc đổi PATH toàn hệ thống. Nếu không chạy được, ghi đúng lệnh/lỗi và đánh dấu Compose UNVERIFIED; kiểm YAML không thay thế Compose.

## Việc 2 — Dữ liệu mẫu và hướng dẫn nghiệm thu lab

File: `deploy/demo/fixtures/demo-bundle.json`, `deploy/demo/fixtures/README.md`; cập nhật `deploy/demo/README.md`, `docs/wiki/Nguon-du-lieu-F01.md`, `docs/PROGRESS.md`.

- [ ] Tạo bundle STIX 2.1 nhỏ, ID và timestamp cố định: identity của nguồn mẫu, report, observable, indicator và quan hệ hợp chuẩn. Dùng IP dành cho tài liệu và domain `.example`; không cần tải ATT&CK để tạo fixture. Đánh dấu tổng hợp ở tên/mô tả, provenance và marking phù hợp.
- [ ] Đọc chuẩn STIX và định dạng marking được công cụ hỗ trợ; không giả nguồn URL hay quan hệ MITRE. Ghi hash SHA-256, số object/quan hệ và mục đích của fixture trong README.
- [ ] Chạy validator STIX chính thức/được dự án dùng với phiên bản được ghim, kiểm cả tham chiếu và pattern. Xác nhận validator từ chối một bản tạm có tham chiếu/pattern hỏng. Không viết test chỉ so sánh từng hằng số cấu hình với chính nó.
- [ ] Hướng dẫn lab theo thứ tự: người duyệt mẫu → xác minh máy/secret/quyền → lõi khỏe → MITRE → nhập mẫu → đếm và xem nguồn/quan hệ → chạy lặp → đo RAM/queue. Ghi trạng thái chưa chạy của từng tiêu chí; #10 còn cần OTX.
- [ ] Kiểm link tương đối và `git diff --check`; chỉ chạy lại test/lint nếu thêm mã kiểm tra hoặc thay mã liên quan. Commit cục bộ gọn, trả SHA, diff, lệnh, exit và log đã lọc.

## Điều kiện bàn giao

Gói demo được chuẩn bị và kiểm tra ngoại tuyến; các mục không thể kiểm có lỗi/bằng chứng cụ thể. README chỉ rõ đây chưa phải kết quả lab. Báo cáo tại `PHONG-HOA-DEMO-PREPARATION-RESULT.md` trong thư mục công việc của Leader; không giữ secret trong báo cáo hoặc commit.
