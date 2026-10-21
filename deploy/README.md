# Triển khai lab trên máy Ubuntu (i3, 16 GB RAM)

Dùng docker-compose chính thức của OpenCTI (repo `OpenCTI-Platform/docker`), rồi áp các giới hạn dưới đây.
Mọi secret đặt trong `.env` (sao chép từ `.env.example`, KHÔNG commit).

## Chuẩn bị hệ điều hành
```bash
sudo sysctl -w vm.max_map_count=1048575
echo "vm.max_map_count=1048575" | sudo tee -a /etc/sysctl.conf
```

## Ngân sách RAM dự kiến (điều chỉnh theo `docker stats` thực tế)
| Thành phần | Giới hạn |
|---|---|
| Elasticsearch/OpenSearch | 4 GB heap (`ELASTIC_MEMORY_SIZE=4G`) |
| OpenCTI platform (Node) | 3 GB |
| Redis | 1 GB (giảm độ dài stream) |
| RabbitMQ | 512 MB |
| S3 (MinIO/Silo) | 256 MB |
| 2 worker | 2 × 512 MB |
| Connector (mỗi cái) | 256 MB, bật tối đa 4–5 cái |
| Hermes + MCP server | 1 GB |
| Hệ điều hành + dư phòng | khoảng 3 GB |

Wazuh KHÔNG chạy trên máy này: dùng máy ảo trên laptop 32 GB (Wazuh 8 GB, Windows nạn nhân 4 GB, Kali 4 GB).

## Mở ra Internet cho demo
Dùng Cloudflare Tunnel (`cloudflared`) trỏ tên miền của nhóm vào portal; bật Cloudflare Access để chỉ email
của nhóm và giảng viên vào được. Không mở port trên router.

## Sao lưu
Chụp volume Elasticsearch + MinIO mỗi tuần trước khi thử nghiệm lớn.
