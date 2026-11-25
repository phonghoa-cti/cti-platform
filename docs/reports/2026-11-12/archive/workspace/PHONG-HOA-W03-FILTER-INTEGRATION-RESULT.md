# W03 filter integration — kết quả cuối cục bộ

## Kết luận

**PASS cục bộ W03-R sau khi ghép R1 và R2.**

- R2 base: `9579d1657145769718fde96c4918fe5cd4d80f63`.
- R1 nguồn đã nghiệm thu: `7ff62711f4304aefda9a6fc640d05039fd0cd9af`.
- Commit ghép R1: `90af6d7a47a9bb9682a6ac7acd6b8ae6729aa986`.
- Final HEAD sạch: `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.
- Từ runtime HEAD đến final HEAD chỉ có `docs/PROGRESS.md`; browser/build chạy trên đúng product code `90af6d7`.
- Source Frontend và Backend vẫn sạch; không push/PR/merge/deploy/lab/feed/secret.

## Kiểm tự động

| Kiểm | Kết quả |
|---|---|
| W03 app + HTTP focused | exit 0, **53/53** PASS |
| Wire portable R2 | exit 0, **10/10** PASS |
| Probe Leader nguyên bản | exit 0, **3/3** PASS; SHA-256 `1756efa9...` giữ nguyên |
| Next production build | exit 0; 10 route, gồm `/lo-hong` và `/lo-hong/mau` |

Đối chiếu cây mã: `portal/web/data/cves-http.ts` và hai test R1 giống commit nguồn `7ff62711`; `portal_api/**`
giống Backend `abcd14d...`. Wire fixtures/preflight/matrix R2 vẫn nằm trên lịch sử `9579d165`.

## Browser desktop tập trung

Một lượt `w03-it` bằng Browser tab, viewport thật **1280×720, DPR 1**:

1. Mặc định `Chỉ KEV` checked: **3 CVE liên quan / 3 KEV**, đúng `2001, 2002, 2003`.
2. Bỏ checked: **16 CVE liên quan / 3 KEV**; ba KEV vẫn đứng đầu.
3. Trang 1 có 10 ID, trang 2 có 6 ID; hợp lại **16 ID duy nhất**, không lặp và không bỏ CVE.
4. Khi unchecked, lọc `q=CVE-2026-2013` còn đúng một ID; xóa filter phục hồi **16**.
5. Bật checked lại: trở về **3/3** với đúng ba KEV ban đầu.

Trace có 7 `GET /api/cves` và không có phương thức ghi. Notice nguồn synthetic/version vẫn hiển thị nguyên văn.
SQLite ban đầu và cuối có cùng SHA-256
`6cca76f8d6afc490303d89f38637370730b39725b46b6c66360037ca1fb4e7b1`; summary/count cũng hoàn toàn giống nhau.
Helper kết thúc `stopped`, port đã đóng và temp root đã xóa.

Ảnh, trace, hai SQLite snapshot và metadata nằm trong `w03-filter-integration-evidence/browser-filter/`.

## Bằng chứng tái sử dụng

Không chạy lại các kiểm không bị ảnh hưởng. Giữ bằng chứng đã được Leader đối chiếu:

- R2 HTTP/SQL **120/120** gồm quyền, wire near-cap, POST/DELETE matches và SQL bất biến.
- Browser Leader summary không gọi Technology API.
- Browser snapshot `409→200` và recovery `503→200`.
- 42 artifact gốc và 14 artifact R2 có manifest riêng đã khớp.

## Giới hạn

**UNVERIFIED:** mobile 360 px, feed/CISA thật, OpenCTI, Cloudflare/JWKS/HTTPS, lab và production. Fixture vẫn là dữ
liệu synthetic; kết quả không chứng minh độ chính xác CVE thật hoặc phạm vi version bị ảnh hưởng.

## Hoàn tác

- Hoàn tác docs cuối: `git revert 7ff6eb3af21d8de65836bfbf707396ae5690de0b`.
- Hoàn tác R1 ghép: `git revert 90af6d7a47a9bb9682a6ac7acd6b8ae6729aa986`.
