# Hướng dẫn 03 (Việc 3) — Giảm tải OpenCTI và bật connector đầu tiên

**Làm sau khi:** Việc 2 xong (đăng nhập được OpenCTI). Ai làm: vai Hạ tầng & Dữ liệu, cả nhóm nên xem.

**Mục tiêu:** OpenCTI chạy nhẹ trên máy i3; có dữ liệu MITRE ATT&CK; tự động nhận tin từ AlienVault OTX mỗi 30 phút.

**Vì sao:** đây là issue đầu tiên của F01 (thu thập feed). Làm xong là Phong Hỏa có "nguồn sống" đầu tiên.

## Điều cần biết trước
File `docker-compose.yml` chính thức của OpenCTI chạy khoảng **25 dịch vụ**: nền tảng, 3 worker, khoảng 10 connector
xuất/nhập file, connector MITRE, và **XTM One** (một nền tảng phụ kèm cơ sở dữ liệu riêng). Như vậy là nhiều cho máy i3 16 GB.

## Phương án giảm tải

| Cách | Ưu | Nhược |
|---|---|---|
| Sửa thẳng `docker-compose.yml` | Dễ hiểu | Lần sau cập nhật OpenCTI (`git pull`) sẽ bị xung đột, mất chỗ đã sửa |
| **Tạo file `docker-compose.override.yml` (khuyến nghị)** | Không đụng file gốc; Docker Compose tự gộp hai file | Phải học thêm khái niệm override |

## Bước 1 — Đo trước khi sửa
```bash
cd ~/phonghoa/opencti
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"   # RAM từng dịch vụ
free -h                                                               # RAM còn trống của cả máy
```
Chụp lại kết quả cho devlog. Nếu cột "available" của `free -h` còn **trên 3 GB** thì có thể bỏ qua bước 2.

## Bước 2 — Giảm tải bằng file override
```bash
nano docker-compose.override.yml   # tạo file mới cạnh docker-compose.yml
```
Dán nội dung sau:
```yaml
services:
  worker:
    deploy:
      replicas: 1          # 3 worker -> 1; tăng lên 2 nếu dữ liệu nhập chậm
  # Tạm tắt XTM One (bật lại ở tháng 1 khi làm MCP). "profiles" khiến dịch vụ chỉ chạy khi được gọi tên.
  xtm-one:
    profiles: ["tat"]
  xtm-one-worker:
    profiles: ["tat"]
  pgsql-xtm-one:
    profiles: ["tat"]
```
Áp dụng:
```bash
docker compose up -d --remove-orphans   # khởi động lại theo cấu hình mới
docker compose ps                       # kiểm tra các dịch vụ còn lại đều "running"/"healthy"
```
Nếu báo lỗi kiểu *"depends on ... which is disabled"* (một dịch vụ khác cần XTM One), xóa đoạn XTM One khỏi override,
chỉ giữ phần `worker`, rồi chạy lại. Ghi lỗi gặp phải vào devlog.

## Bước 3 — Kiểm tra connector MITRE (đã có sẵn)
Trên giao diện OpenCTI: vào **Data → Ingestion → Connectors**, tìm *MITRE ATT&CK*: trạng thái phải là đang chạy.
Sau 10–30 phút, vào mục **Techniques** sẽ thấy hàng trăm kỹ thuật (ví dụ T1566 Phishing).

## Bước 4 — Tạo tài khoản riêng cho connector
Tài liệu OpenCTI khuyến nghị mỗi connector dùng một tài khoản và token riêng, để biết dữ liệu do ai tạo và dễ thu hồi quyền.
1. **Settings → Security → Users → Create**: tên `[C] AlienVault`, email giả như `alienvault@connector.local`.
2. Thêm user vào nhóm **Connectors**.
3. Mở user vừa tạo, tạo **API token**, copy lại.

## Bước 5 — Lấy API key OTX
Đăng ký miễn phí tại otx.alienvault.com, vào trang cá nhân (Settings) để copy **OTX Key**.

## Bước 6 — Thêm connector AlienVault
Mở `.env`, thêm 3 dòng (giá trị thật, không đưa lên GitHub):
```bash
CONNECTOR_ALIENVAULT_ID=<một UUID mới: cat /proc/sys/kernel/random/uuid>
CONNECTOR_ALIENVAULT_TOKEN=<token của user [C] AlienVault ở bước 4>
OTX_API_KEY=<key ở bước 5>
```
Thêm vào **cuối** `docker-compose.override.yml` (thụt lề đúng 2 dấu cách, ngang hàng với `worker:`):
```yaml
  connector-alienvault:
    image: opencti/connector-alienvault:latest
    environment:
      - OPENCTI_URL=http://opencti:8080
      - OPENCTI_TOKEN=${CONNECTOR_ALIENVAULT_TOKEN}
      - CONNECTOR_ID=${CONNECTOR_ALIENVAULT_ID}
      - CONNECTOR_NAME=AlienVault OTX
      - CONNECTOR_SCOPE=alienvault
      - CONNECTOR_LOG_LEVEL=info
      - CONNECTOR_DURATION_PERIOD=PT30M
      - ALIENVAULT_API_KEY=${OTX_API_KEY}
      # Mặc định lấy từ năm 2020 -> rất nhiều dữ liệu, máy i3 sẽ quá tải. Chỉ lấy từ đầu tháng 10/2026:
      - ALIENVAULT_PULSE_START_TIMESTAMP=2026-10-01T00:00:00
    restart: always
    mem_limit: 256m
```
**Đối chiếu tên biến** với file mẫu chính thức trước khi chạy (tên biến có thể đổi theo phiên bản):
`https://raw.githubusercontent.com/OpenCTI-Platform/connectors/master/external-import/alienvault/docker-compose.yml`

Chạy:
```bash
docker compose up -d connector-alienvault       # chỉ khởi động connector mới
docker compose logs -f --tail 30 connector-alienvault   # xem log trực tiếp; Ctrl+C để thoát xem
```

## Kiểm tra là xong
- Log không có dòng `ERROR`; thấy dòng báo đang xử lý pulse.
- Trên giao diện: **Data → Ingestion → Connectors** có *AlienVault OTX*; mục **Analyses → Reports** có báo cáo mới từ OTX.
- `free -h` vẫn còn trên 2 GB "available" sau 1 giờ chạy.

## Đưa cấu hình vào repo (bằng Pull Request)
Copy `docker-compose.override.yml` vào `deploy/` trong repo (file chỉ chứa `${TEN_BIEN}`, không có giá trị thật nên an toàn),
thêm 3 tên biến mới vào `deploy/.env.example`, rồi mở PR theo hướng dẫn 02. Đóng issue *"F01: bật connector MITRE và OTX"*.

## Học thêm
- **docker-compose.override.yml:** file "vá" được Docker Compose tự gộp vào file chính. Bạn tùy biến mà không sửa file gốc.
- **Profiles:** gắn nhãn cho dịch vụ; dịch vụ có profile chỉ chạy khi gọi đích danh profile đó. Đây là cách "tắt mà không xóa".
- **Service account:** tài khoản dành cho máy (connector, bot) chứ không cho người. Mỗi máy một tài khoản nên dễ kiểm soát và thu hồi.
- **PT30M:** cách viết khoảng thời gian theo chuẩn ISO 8601. P = khoảng, T = phần giờ, 30M = 30 phút; PT1H = 1 giờ, P1D = 1 ngày.
