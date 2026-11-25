# W03-READ-BACKEND — kết quả 12/11/2026

## Kết quả

PASS cục bộ cho phạm vi Backend W03-R chỉ đọc. Base `273196e2d23b36172d57cc61b289522786d61b2a`;
HEAD R1 `a49486caf39942019259e41514457bdb85498347`; hai commit `a4ff842` (implementation) và `a49486c`
(`fix: tighten W03 read contracts`); branch `feat/w03-read-backend-20261112`; tree sạch sau commit. Diff
base..HEAD: 13 file, 1.329 dòng thêm, 1 dòng xóa;
`git diff --check base..HEAD` exit 0.

Đã thêm `GET /api/cves`, fixture port bounded 4 MiB, service validate toàn dataset, đối chiếu exact
vendor/product casefold, rank/paging/cursor snapshot, detail/mixed-role và leader summary. Technology snapshot
dùng subclass `TechnologyStore` mở SQLite URI `mode=ro`; request không initialize/migrate/seed. Response có
`no-store`/`Vary`, cap UTF-8 1 MiB và error envelope tĩnh.

R1 khóa affected product ở 128 code point, chỉ nhận KEV source `CISA KEV synthetic sample`, kiểm raw JSON
cursor canonical, xác minh missing-after/cross-role, verifier unavailable trước dependency và SQL bất biến cả
404/409. Năm wire fixture nay được so exact với response API deterministic trong test.

## TDD và kiểm chứng

- RED route: 1 failure, exit 1; GREEN: 1/1, exit 0.
- RED contract: 18 failure, exit 1; GREEN contract: 29/29, exit 0.
- RED fixture adapter/extra-key và rank fractional timestamp đều được ghi riêng; GREEN sau fix exit 0.
- R1 RED: 4 failure/37 pass (product, source, raw cursor, wire exact), exit 1; GREEN: 41/41, exit 0.
- Focused W03 cuối: 41/41 trong 1,96 giây, exit 0.
- W04 technology + W02/W05 auth/API regression: 230/230, exit 0.
- Toàn `portal_api/tests` sau format: 345/345 trong 9,98 giây, exit 0.
- Ruff check: exit 0; Ruff format check: exit 0; 6 JSON fixture parse: exit 0.

SQL proof đọc trước/sau gồm `sqlite_master`, toàn bộ `technology_assets`, `technology_asset_audit` và
`PRAGMA user_version`; kết quả bằng nhau sau GET 200, failure 404 và failure 409. Path DB thiếu trả 503 và không
tạo file. Test cũng bao phủ dataset hỏng, cap candidate/product/response, quyền/query precedence, leader asset
không leak, cursor context, base64 tamper, raw JSON không canonical và stale sau technology edit.

## Wire fixtures và bằng chứng

Response API test thật đã xuất: `w03-wire-detail.json`, `w03-wire-summary.json`, `w03-wire-empty.json`,
`w03-wire-error.json`, `w03-wire-cursor-changed.json`. Hash đầy đủ tại
`w03-backend-evidence/wire-sha256.txt`; dataset fixture hash
`89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73`.

Thư mục bằng chứng: `w03-backend-evidence/` gồm `red-green.log`, `final-tests.log`,
`final-verification.log`, `r1-red-green.log`, `r1-final.log`, `readonly-sql-proof.md`, `wire-sha256.txt`.

## File repo

`portal_api/cves.py`, `portal_api/app.py`, `portal_api/tests/test_cves_api.py`, 7 fixture `w03-*`,
`docs/specs/W03-read-local-contract.md`, `docs/adr/0006-w03-read-only-snapshot-cursor.md`,
`docs/PROGRESS.md`. Không sửa auth, technologies, deps, core, gateway, frontend, ledger hoặc brief.

## UNVERIFIED

Frontend/parser, gateway/runner, browser/viewport, nguồn CVE/CISA thật, OpenCTI/feed, Cloudflare/JWKS/HTTPS
thật, lab và production chưa được kiểm. Fixture tổng hợp không chứng minh độ mới/chất lượng nguồn thật;
matching tên không kết luận phiên bản bị ảnh hưởng hay an toàn.
