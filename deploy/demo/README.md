# Gói chuẩn bị demo F01

Gói này chuẩn bị cấu hình ngoại tuyến cho demo **MITRE ATT&CK + bundle STIX tổng hợp**. Nó chưa chứng minh
OpenCTI boot được trên lab, chưa nhập dữ liệu và chưa đạt #10 (MITRE + OTX chạy thật).

## Phạm vi

- `compose.yml`: lõi OpenCTI, một worker, Redis, Elasticsearch, kho S3 và RabbitMQ.
- `compose.mitre.yml`: connector MITRE bật riêng sau khi lõi khỏe.
- `compose.import.yml`: connector ImportFileStix bật riêng để analyst tải bundle đã duyệt.
- `images.lock.json`: tag, digest index và manifest `linux/amd64` của mọi image được dùng.
- `fixtures/`: dữ liệu STIX 2.1 tổng hợp, không phải báo cáo tấn công thật.

Không có OTX, XTM One, XTM Composer, Docker socket, AI, host network hoặc privileged container. Chỉ OpenCTI
được publish tại `127.0.0.1`; các dependency chỉ ở mạng Compose. Connector có giới hạn cấu hình 256 MB,
nhưng khả năng chạy đủ trong giới hạn này vẫn **UNVERIFIED** cho tới khi đo trên lab.

## Nguồn cấu hình và phiên bản

- OpenCTI/worker: LTS `7.260811.0-lts.2`, source commit
  `957087377304ea548fcd9f83a4ee2b025c855d9b`.
- Connector: cùng tag LTS, source commit `d50686be6f64eb2e91ac38b23c45d0460a210435`.
- Cấu trúc lõi tham khảo từ `OpenCTI-Platform/docker` commit
  `60285adb360e3823a334333ae4744255d8ac1821`, nhưng bỏ các service không thuộc demo và thay mọi image
  bằng tag + digest trong lock file.
- `rabbitmq.conf` lấy hai giá trị từ file upstream cùng commit. Repo upstream không có file LICENSE tại ref
  này; provenance và SHA-256 được ghi ngay trong file, cần rà điều khoản trước khi phân phối ra ngoài dự án.

Giấy phép image là của từng dự án, không phải của Compose này: OpenCTI Community Edition nêu Apache-2.0;
Redis, Elasticsearch, Silo và RabbitMQ có điều khoản riêng tại source/image link trong `images.lock.json`.
Kiểm lại điều khoản đúng version trước triển khai ngoài lab.

## Secret và tài khoản

Sao chép `.env.example` thành `.env` **trên máy lab**, rồi nhập secret bằng kênh an toàn. Không commit `.env`.
Các biến bắt buộc dùng cú pháp `${VAR:?message}`, vì vậy kiểm cấu hình sẽ thất bại nếu thiếu hoặc để trống.

Worker dùng token quản trị của platform theo cấu trúc upstream. MITRE và ImportFileStix phải dùng hai tài khoản
connector riêng: sau khi lõi khỏe, người vận hành tạo tài khoản/quyền phù hợp trong OpenCTI, lấy token và điền
`CONNECTOR_MITRE_TOKEN` / `CONNECTOR_IMPORT_FILE_STIX_TOKEN`. Không dùng admin token cho connector.

## Kiểm cấu hình, không cần daemon

Các lệnh dưới đây chỉ parse và render Compose; chúng không pull image hoặc chạy container:

```bash
# Lõi: chỉ 6 service, không yêu cầu token connector.
docker compose --env-file .env -f compose.yml config --quiet
docker compose --env-file .env -f compose.yml config --services

# MITRE: chỉ ghép sau khi có ID/token riêng.
docker compose --env-file .env -f compose.yml -f compose.mitre.yml config --quiet

# ImportFileStix: chỉ ghép sau khi có ID/token riêng.
docker compose --env-file .env -f compose.yml -f compose.import.yml config --quiet
```

Trước mỗi thay đổi version, so sánh các image render từ Compose với `images.lock.json`; không chấp nhận
`latest`, image không có digest hoặc platform khác `linux/amd64`.

## Trình tự nghiệm thu trên lab (chưa chạy)

1. Analyst duyệt fixture: xác nhận nội dung tổng hợp, provenance, marking/TLP và SHA-256 trong
   [`fixtures/README.md`](fixtures/README.md).
2. Kiểm máy lab, `vm.max_map_count`, dung lượng, secret và quyền; chạy `config --quiet` trước khi pull.
3. Khởi động **lõi**, chờ Redis/Elasticsearch/S3/RabbitMQ/OpenCTI khỏe; ghi RAM và queue nền.
4. Tạo tài khoản connector MITRE riêng, ghép `compose.mitre.yml`, rồi kiểm số entity/relationship và
   external references sau import; chạy lặp để phát hiện trùng.
5. Tạo tài khoản ImportFileStix riêng, ghép `compose.import.yml`; analyst tải fixture đã duyệt qua giao diện.
6. Kiểm object mẫu có `created_by`, marking/TLP, observable, indicator, report và relationship; nhập lặp và
   ghi số object trước/sau, không gọi kết quả parse là bằng chứng chống trùng.
7. Theo dõi RSS/CPU peak, RAM còn trống, queue, work thành công/thất bại, timeout/retry. Dừng trước connector
   kế tiếp nếu RAM trống dưới 2 GB hoặc queue/error tăng dần.
8. OTX là lượt riêng sau khi có key và chấp nhận điều khoản. #10 chỉ đạt khi MITRE + OTX chạy thật và dữ liệu
   quan sát được; gói này chưa đạt điều kiện đó.

## Hoàn tác

Khi mới dừng ở bước chuẩn bị, hoàn tác bằng commit Git. Trên lab tương lai, dừng Compose trước; không xóa
volume nếu chưa có phê duyệt và bản sao lưu vì thao tác đó phá hủy dữ liệu.
