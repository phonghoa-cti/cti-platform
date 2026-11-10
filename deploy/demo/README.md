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

Cấu hình bộ nhớ ứng viên dành 4 GB cho container Elasticsearch nhưng chỉ đặt heap JVM 2 GB, theo khuyến nghị
[heap không vượt quá 50% RAM khả dụng](https://www.elastic.co/guide/en/elasticsearch/reference/8.19/advanced-configuration.html).
Container OpenCTI có giới hạn 3 GB và Node.js `--max-old-space-size=2048` MiB để chừa bộ nhớ ngoài V8 heap.
Đây là giá trị chuẩn bị để thử, chưa phải bằng chứng mức RAM phù hợp hoặc runtime ổn định trên lab.

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

`OPENCTI_ADMIN_TOKEN` phải là UUIDv4 hợp lệ. `OPENCTI_ENCRYPTION_KEY` phải là Base64 giải mã được ít nhất
32 byte. Mỗi `CONNECTOR_*_ID` là một UUIDv4 riêng. `CONNECTOR_*_TOKEN` là API token do OpenCTI cấp cho user
connector, khác ID và admin token; OpenCTI 7 không yêu cầu token API này có dạng UUID.

Sinh giá trị mới **trên lab**, rồi đưa vào kho secret/kênh an toàn; không ghi output vào repo hoặc log:

```bash
# Python 3.12: chạy từng lệnh và chép trực tiếp kết quả vào nơi lưu secret an toàn.
python3.12 -c "import uuid; print(uuid.uuid4())"  # admin token hoặc từng connector ID
python3.12 -c "import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

```powershell
# PowerShell: UUIDv4 và khóa Base64 32 byte.
[guid]::NewGuid().ToString()
$bytes = [byte[]]::new(32); $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes); [Convert]::ToBase64String($bytes); $rng.Dispose()
```

Nguồn định dạng: [OpenCTI installation](https://docs.opencti.io/latest/deployment/installation/) và
[OpenCTI 7 breaking changes](https://docs.opencti.io/latest/deployment/breaking-changes/).

## Kiểm cấu hình, không cần daemon

Các lệnh dưới đây chỉ parse và render Compose; chúng không pull image hoặc chạy container:

```bash
# Lõi: chỉ 6 service, không yêu cầu token connector.
docker compose --env-file .env -f compose.yml config --quiet
docker compose --env-file .env -f compose.yml config --services
docker compose --env-file .env -f compose.yml config --format json | python3.12 validate_compose_config.py

# MITRE: chỉ ghép sau khi có ID/token riêng.
docker compose --env-file .env -f compose.yml -f compose.mitre.yml config --quiet
docker compose --env-file .env -f compose.yml -f compose.mitre.yml config --format json | python3.12 validate_compose_config.py

# ImportFileStix: chỉ ghép sau khi có ID/token riêng.
docker compose --env-file .env -f compose.yml -f compose.import.yml config --quiet
docker compose --env-file .env -f compose.yml -f compose.import.yml config --format json | python3.12 validate_compose_config.py
```

Pipe truyền JSON trực tiếp qua bộ nhớ; không lưu cấu hình render chứa secret ra file/log. Preflight chỉ in tên
trường và quy tắc khi lỗi. Nó kiểm định dạng và tách token, không chứng minh entropy, quyền hay token sử dụng được.

Trước mỗi thay đổi version, so sánh các image render từ Compose với `images.lock.json`; không chấp nhận
`latest`, image không có digest hoặc platform khác `linux/amd64`.

## Kiểm fixture STIX

Cài đúng validator vào `.venv` riêng của checkout, không cài toàn hệ thống:

```powershell
uv pip install --python .venv\Scripts\python.exe stix2-validator==3.3.2
.venv\Scripts\stix2_validator.exe --version 2.1 --strict --enforce-refs deploy/demo/fixtures/demo-bundle.json
```

Lệnh chỉ parse file cục bộ. Kết quả và negative case được mô tả trong [`fixtures/README.md`](fixtures/README.md).

## Trình tự nghiệm thu trên lab (chưa chạy)

1. Analyst duyệt fixture: xác nhận nội dung tổng hợp, provenance, marking/TLP và SHA-256 trong
   [`fixtures/README.md`](fixtures/README.md).
2. Kiểm máy lab, `vm.max_map_count`, dung lượng, secret và quyền; chạy `config --quiet` trước khi pull.
3. Khởi động **lõi**, chờ Redis/Elasticsearch/S3/RabbitMQ/OpenCTI khỏe; ghi RAM và queue nền.
4. Tạo tài khoản connector MITRE riêng, ghép `compose.mitre.yml`, rồi kiểm số entity/relationship và
   external references sau import; chạy lặp để phát hiện trùng.
5. Tạo tài khoản ImportFileStix riêng, kiểm capability **Upload knowledge files**, ghép `compose.import.yml`,
   rồi analyst tải fixture đã duyệt tại vùng nhập file chung. Vì `CONNECTOR_AUTO=false`, nếu chưa xuất hiện work,
   chọn và chạy ImportFileStix thủ công; chờ work xử lý xong, không dùng bypass validation.
6. OpenCTI ref `957087377304ea548fcd9f83a4ee2b025c855d9b` tại
   `opencti-platform/opencti-graphql/config/default.json` mặc định `app.validation_mode="draft"`: analyst có
   quyền phù hợp mở bản nháp, kiểm object/relationship/marking/provenance rồi phê duyệt; chỉ gọi là workbench
   khi lab chọn mode workbench. Quyền review/approve theo mode phải kiểm trên lab, không tự cấp. Ghi người duyệt,
   work ID, trạng thái trước/sau.
7. Sau phê duyệt mới kiểm kho dữ liệu chính: mọi object hỗ trợ marking có marking phù hợp;
   indicator/relationship/report có `created_by_ref`; report có external reference nguồn tổng hợp; IPv4/domain
   truy nguyên qua `report.object_refs` và relationship. Nhập lặp và ghi số object trước/sau; parse không chứng
   minh chống trùng.
8. Theo dõi RSS/CPU peak, RAM còn trống, queue, work thành công/thất bại, timeout/retry. Dừng trước connector
   kế tiếp nếu RAM trống dưới 2 GB hoặc queue/error tăng dần.
9. OTX là lượt riêng sau khi có key và chấp nhận điều khoản. #10 chỉ đạt khi MITRE + OTX chạy thật và dữ liệu
   quan sát được; gói này chưa đạt điều kiện đó.

Luồng draft/import dựa trên [OpenCTI import files](https://docs.opencti.io/latest/usage/import-files/) và
[connector tại ref đã chọn](https://github.com/OpenCTI-Platform/connectors/blob/d50686be6f64eb2e91ac38b23c45d0460a210435/internal-import-file/import-file-stix/src/connector/connector.py).
Cấu hình ngoại tuyến chưa chứng minh capability, work, phê duyệt hay object xuất hiện đúng trên lab.

## Hoàn tác

Khi mới dừng ở bước chuẩn bị, hoàn tác bằng commit Git. Trên lab tương lai, dừng Compose trước; không xóa
volume nếu chưa có phê duyệt và bản sao lưu vì thao tác đó phá hủy dữ liệu.
