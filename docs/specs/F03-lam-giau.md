# F03 — Làm giàu IOC (enrichment)

- Vai: Hạ tầng & Dữ liệu · Mốc: v0.5 (15/12/2026) · Trạng thái: Nháp

## Mục tiêu
Khi analyst mở một IOC, thấy thêm: quốc gia/ASN của IP, chủ tên miền, kết quả VirusTotal/AbuseIPDB.

## Cách làm
Ưu tiên connector enrichment chính thức của OpenCTI (thư mục `internal-enrichment`): VirusTotal, AbuseIPDB,
và các connector tra cứu IP/tên miền khác nếu có. Bật chế độ chạy khi analyst bấm (không tự động hàng loạt)
để không vượt giới hạn miễn phí.

## Tiêu chí chấp nhận
- [ ] ≥ 3 nguồn enrichment hoạt động trên IP, domain, hash.
- [ ] Không vượt giới hạn miễn phí trong 7 ngày chạy (ghi số request vào devlog).
- [ ] Key API nằm trong `.env`, không có trong repo.

## Không làm
Không tự động enrich toàn bộ IOC từ feed (quá giới hạn API).
