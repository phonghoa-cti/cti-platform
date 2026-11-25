# X01 → W05 → STIX E2E evidence

Ngày chạy: 11/11/2026, Windows local. Evidence này chỉ giữ command, exit, count, Git ref và SHA-256 đã lược
dữ liệu. Không lưu raw source, draft JSON, SQLite, bundle STIX, JWT, private key hoặc subject.

Kết luận: PASS local cho extractor CLI → store CLI → HTTP gateway/API v1 selection/approve → STIX CLI trên
cùng draft và DB, rồi cleanup owned process/thread/listener/temp.

- Base: `ed829a0344b2d3d4392fae933e41a9c44fdcd853`
- HEAD: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`
- Branch: `feat/x01-w05-stix-e2e-20261111`
- Source readonly vẫn đúng base và sạch; implementation tree sạch.
- Diff: 7 file, `+588/-1`.
- Final targeted pytest: 54 passed, exit 0.
- New E2E matrix: 59 checks, exit 0.
- Selection regression: 113 checks / 10 scenarios, exit 0.
- Ruff check/format và `git diff --check`: exit 0.

Command seed nội bộ có metadata creator synthetic; evidence thay giá trị đó bằng
`--created-by-subject <REDACTED_SYNTHETIC_SUBJECT>`. Không xem metadata CLI này là bằng chứng xác thực danh tính.

Giới hạn: chưa kiểm browser cùng draft, OpenCTI import/workbench, identity thật, Cloudflare/JWKS/HTTPS, chất
lượng X01 C2–C4/dataset thật, network share/crash, lab, deploy hay production.
