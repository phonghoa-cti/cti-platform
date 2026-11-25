# X01 ATT&CK thật — manifest bằng chứng

Thời điểm quan sát: 2026-11-11T08:38:27+07:00. Đây là inventory chỉ đọc, không phải test tương thích sản phẩm.

## Snapshot chính xác

- Tổ chức/nguồn: MITRE ATT&CK `mitre-attack/attack-stix-data`.
- Tag có chú thích: `v20.1`, object tag `fe094cfc533102f8eed3acefd89bb38a96fdf2c1`.
- Tag trỏ commit bất biến: `f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7` (`chore(release): prepare ATT&CK 20.1`); tagger 2026-11-05T16:32:16Z.
- Tệp: `enterprise-attack/enterprise-attack-20.1.json`; Git blob SHA-1 `4acfc94abd56693ca590ccab493c087deaa7cfb5`; GitHub API khai báo 55,277,605 bytes.
- URL tải bất biến: <https://raw.githubusercontent.com/mitre-attack/attack-stix-data/f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7/enterprise-attack/enterprise-attack-20.1.json>.
- Bản bytes đã tải: `enterprise-attack-20.1.json`, 55,277,605 bytes, SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`.
- Tải đúng một JSON qua HTTP GET timeout 60 giây; kiểm `Content-Length` và tổng stream không quá 64 MiB. Kết quả: 55,277,605 < 67,108,864 bytes.

## License / notice

- License tại cùng commit: `LICENSE.txt`, Git blob SHA-1 `7d8dc97542672cc9ec78de1b643b5b39ca7e2fba`, 1,354 bytes: <https://github.com/mitre-attack/attack-stix-data/blob/f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7/LICENSE.txt>.
- License MITRE cho phép dùng ATT&CK cho nghiên cứu, phát triển và thương mại nhưng yêu cầu mọi bản sao tái tạo copyright designation và license. Artifact phân phối phải giữ `LICENSE.txt` nguyên văn cùng chỉ dẫn bản quyền MITRE. Không có tệp `NOTICE` tên đúng như vậy trong root được xác minh ở lượt này; README có mục Notice, nhưng **NOTICE file riêng: UNVERIFIED/không giả định tồn tại**.

## Tệp local và hash

| Tệp | SHA-256 |
|---|---|
| `enterprise-attack-20.1.json` | `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5` |
| `download_snapshot.ps1` | `2293751a5ebc7a08142365f27156ef96a67e646322e10afa9cf7332f4129d4d1` |
| `inventory_snapshot.py` | `2a928f62cc4d51a7640c32f1a91235a74a0ca3c278b8c955115759d737ed0915` |
| `inventory.json` | `0c66a886c3f721e9d4c9161d7bbecf467daa81fe2008384316619fca8470507b` |
| `MITRE-LICENSE.txt` | `738144f7fb054722a4ef9d3367c51710341dc12fc574c6ac3a41daaaecd8bf5e` |

`inventory_snapshot.py` chỉ dùng Python stdlib để đọc JSON và xuất đếm; nó không import loader sản phẩm, không gọi mạng và không ghi vào repo.
