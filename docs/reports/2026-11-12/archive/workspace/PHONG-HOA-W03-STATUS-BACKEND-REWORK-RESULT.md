# W03-S1 Backend — kết quả rework B1/B2

## Kết luận

PASS rework cục bộ/in-process; chờ Leader review lại, chưa tự nhận tích hợp W03-S1.

- Base chung: `7ff6eb3af21d8de65836bfbf707396ae5690de0b`
- Candidate trước rework: `b8957e63acc7497ba835e06c05e52f4b16ef136c`
- Final commit sạch: `4f7100cf83e57b1cb30a12472ed71a0cd985a413`
- Branch: `feat/w03-status-backend-20261112`
- Delta rework: 3 file allowlist, `+229/-24`
- Probe Leader giữ nguyên SHA-256: `d633a3f5b82c88f7ec57d97a2238f812d7965ea207bf3a27cac307777300a152`
- Không sửa probe/log RED/brief/RUNS/Frontend/shared; không push/PR/merge/deploy/browser/feed/lab

## Sửa B1

PUT validate đủ năm trường ngay sau auth/role → Origin → media → path/query/body parse, trước configured
dependency/dataset/DB. Integer dùng kiểu `int` chính xác và JS-safe range, không nhận bool/float/string/null.
Status, note và dataset ID cũng được kiểm trước dependency. Request sai trả 422, không gọi port/store và SQL snapshot
không đổi. Context 409 vẫn được kiểm trước status-version conflict sau khi request hợp lệ.

## Sửa B2

- Timestamp persisted phải khớp wire rồi parse thành ngày UTC có thật; hỗ trợ không fraction hoặc 1..6 chữ số.
- Sai status/note/context/time trong row/audit được đổi thành `status_unavailable` 503, không lẫn lỗi client 422.
- Context persisted phải bind đúng technology/CVE/vendor/product của relation đang đọc; technology version/dataset cũ
  hợp lệ vẫn được giữ để báo `review_required`.
- History kiểm relation, created/changed, version tăng đúng một và trước/sau liên tục. PUT validate toàn audit chain
  hiện có khớp status trước DML; corruption rollback và giữ nguyên status/audit/W04.

## Kiểm chứng sau commit

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `pytest test_cves_status_api.py test_backend_probes.py --tb=short` | 0 | 57 passed: 49 source + 8 probe Leader |
| `pytest test_cves_api.py test_technologies_store.py test_technologies_api.py test_w02_ioc_api.py --tb=short` | 0 | 174 passed |
| `ruff check app.py cves_status.py test_cves_status_api.py` | 0 | All checks passed |
| `ruff format --check app.py cves_status.py test_cves_status_api.py` | 0 | 3 files already formatted |
| `git diff b8957e6..HEAD --check` | 0 | sạch |

Regression bổ sung numeric/string/null bounds, malformed body trước dependency, persisted status/note/time/context,
audit relation/event/version/chain, non-mutation cho GET/PUT/history và valid controls ngày nhuận UTC với fraction
0/1/6 chữ số. Wire fixture/provenance cũ vẫn khớp test, không đổi byte.

## Bằng chứng và giới hạn

Raw GREEN và manifest: `ROOT/w03-status-backend-rework-evidence/`.

Chưa kiểm frontend/backend integration qua gateway, browser, Cloudflare/JWKS/HTTPS thật, feed/CISA/OpenCTI, lab,
deploy hoặc production. W03-S2 không thuộc rework này.
