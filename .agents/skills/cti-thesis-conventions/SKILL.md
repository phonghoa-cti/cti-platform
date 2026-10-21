---
name: cti-thesis-conventions
description: Quy ước dữ liệu CTI của dự án Phong Hỏa — cách đặt nhãn TLP, công thức chấm điểm IOC, decay, allowlist, chuẩn hóa IOC và cách ghi devlog. Dùng khi viết hoặc sửa code xử lý IOC, điểm tin cậy, hoặc khi viết tài liệu đồ án.
---

# Quy ước CTI của dự án Phong Hỏa

## Chuẩn hóa IOC (trước khi lưu hoặc so sánh)
- Refang trước: `hxxp` → `http`, `[.]` → `.`, `(.)` → `.`, `[@]` → `@`.
- Domain: chữ thường, bỏ dấu chấm cuối, chuyển IDN sang punycode.
- URL: chữ thường phần scheme + host; giữ nguyên path/query.
- IP: dùng `ipaddress` của Python; loại IP private, loopback, multicast, reserved.
- Hash: chữ thường; nhận diện theo độ dài (MD5 = 32, SHA1 = 40, SHA256 = 64).
- Khi hiển thị trong báo cáo hoặc Telegram: luôn defang (`example[.]com`).

## Ánh xạ sang STIX 2.1
| IOC | STIX Cyber Observable | Pattern của Indicator |
|---|---|---|
| IPv4 | `ipv4-addr` | `[ipv4-addr:value = '1.2.3.4']` |
| Domain | `domain-name` | `[domain-name:value = 'evil.com']` |
| URL | `url` | `[url:value = 'http://evil.com/a']` |
| SHA256 | `file` | `[file:hashes.'SHA-256' = '...']` |
| Email | `email-addr` | `[email-addr:value = 'a@evil.com']` |

Mọi object phải có: `created_by_ref` (identity của nguồn), `object_marking_refs` (TLP), `confidence` (0–100), `external_references` (link nguồn).

## TLP 2.0
- CLEAR, GREEN: được gửi tới LLM cloud.
- AMBER, AMBER+STRICT, RED: KHÔNG gửi tới LLM cloud; chỉ xử lý bằng regex hoặc model local.
- Không rõ TLP thì mặc định GREEN cho feed công khai, AMBER cho tài liệu analyst tải lên.

## Công thức điểm IOC (0–100)
```
score = 100 × R × (1 − e^(−0.7 × n)) × e^(−λ × d) × (1 + 0.3 × asset_match)
```
- `R`: độ tin cậy nguồn (0–1), khởi tạo theo Admiralty: A=0.95, B=0.8, C=0.6, D=0.4, E=0.2, F=0.5.
- `n`: số nguồn độc lập xác nhận IOC.
- `d`: số ngày kể từ `last_seen`.
- `λ` theo loại: IP 0.05, URL 0.04, domain 0.02, hash 0.002.
- `asset_match` = 1 nếu IOC liên quan tài sản trong hồ sơ doanh nghiệp, ngược lại 0.
- Cắt trần 100. IOC nằm trong allowlist → 0, không xuất ra blocklist.
- Mỗi lần analyst đánh dấu false positive: `R_nguon = max(0.1, R_nguon − 0.02)`.
- Luôn lưu "lý do điểm" (từng thành phần) để hiển thị thẻ giải thích.

## Allowlist mặc định
Dải IP và domain của: Google, Cloudflare, Microsoft, Amazon CDN, các resolver DNS công cộng, top 10k domain Tranco.
Tên miền và dải IP của chính doanh nghiệp mẫu.

## Ghi chép
- Devlog tuần: `docs/devlog/YYYY-Www.md` theo TEMPLATE.md.
- Prompt LLM quan trọng: lưu vào `docs/prompts/` kèm model và ngày.
- Kết quả thí nghiệm: `extractor/eval/results/<ngay>-<cau-hinh>.json` để dựng bảng chương 4.
