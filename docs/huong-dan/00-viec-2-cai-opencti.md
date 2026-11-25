# Hướng dẫn 00 (Việc 2) — Cài Docker và OpenCTI trên máy Ubuntu

**Mục tiêu:** mở trình duyệt trên laptop, vào được giao diện OpenCTI chạy trên máy Ubuntu.

**Vì sao:** OpenCTI là "kho trí nhớ" của Phong Hỏa; connector, AI extractor và bot đều đọc/ghi vào đây.

## Phương án gõ lệnh
Dùng **SSH từ laptop** (khuyến nghị): copy–dán lệnh được, agent sau này cũng điều khiển máy chủ được.

## 2A — SSH và Docker
Trên máy Ubuntu (Terminal):
```bash
sudo apt update && sudo apt upgrade -y   # cập nhật phần mềm
sudo apt install -y openssh-server       # cho phép đăng nhập từ xa
hostname -I                              # ghi lại IP, ví dụ 192.168.1.50
whoami                                   # ghi lại tên đăng nhập
```
Trên laptop (PowerShell): `ssh tendangnhap@192.168.1.50`

Trong cửa sổ SSH:
```bash
free -h && df -h /                                     # RAM ~16Gi, ổ trống > 60G
curl -fsSL https://get.docker.com -o get-docker.sh     # tải script cài Docker chính thức
sudo sh get-docker.sh                                  # cài Docker + Compose
sudo usermod -aG docker $USER                          # dùng docker không cần sudo
exit                                                   # thoát rồi ssh lại
docker run hello-world && docker compose version       # kiểm tra
```

## 2B — OpenCTI
```bash
sudo sysctl -w vm.max_map_count=1048575
echo "vm.max_map_count=1048575" | sudo tee -a /etc/sysctl.conf
mkdir -p ~/phonghoa && cd ~/phonghoa
git clone https://github.com/OpenCTI-Platform/docker.git opencti
cd opencti && cp .env.sample .env
cat /proc/sys/kernel/random/uuid      # tạo UUID
openssl rand -base64 32               # tạo khóa ngẫu nhiên
nano .env                             # điền giá trị (bảng dưới)
```
| Biến | Điền |
|---|---|
| OPENCTI_ADMIN_EMAIL / OPENCTI_ADMIN_PASSWORD | Email và mật khẩu mạnh |
| OPENCTI_ADMIN_TOKEN | **Bắt buộc UUID** |
| OPENCTI_HEALTHCHECK_ACCESS_KEY, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, mọi CONNECTOR_..._ID, XTM_COMPOSER_ID | Mỗi cái một UUID |
| OPENCTI_ENCRYPTION_KEY, RABBITMQ_DEFAULT_PASS | Chuỗi từ openssl |
| OPENCTI_HOST | IP máy Ubuntu |
| ELASTIC_MEMORY_SIZE | 4G |

```bash
docker compose up -d          # lần đầu tải vài GB, 10–20 phút
docker compose ps             # chờ opencti "healthy"
docker stats --no-stream      # chụp RAM cho devlog
```
Mở `http://<IP>:8080` trên laptop và đăng nhập. Kẹt: `docker compose logs --tail 50 <dịch vụ>`. **Không gửi file .env cho ai.**

Tiếp theo: hướng dẫn 03 (giảm tải + connector đầu tiên).
