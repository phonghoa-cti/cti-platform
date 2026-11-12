# W03-READ-BACKEND-QA — kiểm độc lập Backend

Ngày kiểm: 12/11/2026
Verdict: **FAIL — chưa đủ điều kiện accepted hoặc nối tích hợp**.

## Phạm vi và định danh

- Candidate: `a49486caf39942019259e41514457bdb85498347`
- Base: `273196e2d23b36172d57cc61b289522786d61b2a`
- Branch: `feat/w03-read-backend-20261112`
- Module thực chạy: `$WORKSPACE\cti-w03-read-backend\portal_api\cves.py`
- Source chỉ đọc. Không sửa sản phẩm, dependency, ledger, Frontend hoặc Git.
- Trạng thái trước và sau: HEAD/branch đúng; `git status --short`, `git diff --check`, diff index/worktree đều rỗng, exit 0.

## Bằng chứng chạy

1. Baseline tập trung:
   `.\.venv\Scripts\python.exe -m pytest -o addopts='' -o cache_dir=<OUT>\pytest-cache-baseline portal_api/tests/test_cves_api.py -q`
   → **41 passed**, 3.25 giây, exit 0.
2. Probe QA độc lập:
   `.\.venv\Scripts\python.exe -m pytest -c <REPO>\pytest.ini --rootdir <REPO> -o addopts='' -o cache_dir=<OUT>\pytest-cache-probes <OUT>\test_w03_backend_qa_probes.py -q`
   → **3 failed**, 1.40 giây, exit 1. Cả ba là lỗi sản phẩm được tái hiện bên dưới.
3. Năm SHA-256 wire fixture tính lại khớp chính xác manifest của Backend. Baseline 41 test cũng lấy response API thật và so exact với các fixture.
4. Không chạy lại `portal_api/tests` 345 test, build, browser hoặc lab theo brief.

Ghi chú minh bạch: lần đầu gọi probe dùng sai pytest root nên collection lỗi `phonghoa_core`; đã sửa đúng một lần bằng cách ghim config/root/PYTHONPATH về candidate. Lần đó không chạy assertion sản phẩm và không được tính vào kết quả 3 probe.

## Findings

### F1 — HIGH — DB thiếu schema bắt buộc vẫn được tin và trả 200

- Vị trí: `portal_api/cves.py:154-162`; `portal_api/technologies.py:194-207`.
- Input tái hiện: tạo DB W04 hợp lệ có một technology, sau đó xóa index `technology_assets_active_identity`, bảng `technology_asset_audit` và `w04_technology_migrations`; giữ bảng/row `technology_assets` đủ để câu SELECT hiện tại chạy; gọi `GET /api/cves`.
- Expected: fail-closed `503 cves_unavailable` vì schema SQLite hỏng/thiếu.
- Actual: `200`, không có error code.
- Probe: `test_partial_sqlite_schema_fails_closed_without_mutation`; exit chung 1, 1 failure. Assert byte DB trước/sau được chạy trước assert status và **PASS**, nên request không sửa DB nhưng vẫn chấp nhận schema không tương thích.
- Nguyên nhân: `CveReadService` đổi sang `ReadOnlyTechnologyStore` nhưng gọi `TechnologyStore.list()`; hàm này chỉ SELECT rows, không gọi `_validate_schema()`.
- Tác động: dữ liệu technology từ DB đã mất audit/migration/index vẫn được dùng để sinh kết quả CVE, phá yêu cầu fail-closed và bằng chứng toàn vẹn.
- Sửa tối thiểu: override đường đọc trong `ReadOnlyTechnologyStore` để trên **cùng kết nối mode=ro/cùng read transaction** kiểm `TechnologyStore._validate_schema(connection)`, rồi SELECT/fetchall bounded và validate toàn bộ row. Không gọi initialize/migrate/seed và không tách schema-check với data-read sang hai kết nối.

### F2 — MEDIUM — `advisory_url` nhận HTTPS authority không hợp lệ

- Vị trí: `portal_api/cves.py:539-552`.
- Inputs tái hiện:
  - `https://:443/advisory` (không có hostname)
  - `https:// example.invalid/advisory` (hostname có khoảng trắng)
- Expected: toàn dataset fail-closed `503 cves_unavailable`.
- Actual: cả hai trả `200` và URL không hợp lệ đi vào response.
- Probe: hai case của `test_invalid_https_authority_fails_closed`; exit chung 1, **2 failures**. SQL snapshot trước/sau được assert trước status và **PASS**.
- Nguyên nhân: validator chỉ kiểm `scheme == "https"`, `netloc` khác rỗng và không có username/password; `:443` và authority có khoảng trắng vẫn vượt qua.
- Tác động: dữ liệu CTI không tin cậy có thể tạo link advisory hỏng/khác cách diễn giải giữa parser và browser; contract “HTTPS tuyệt đối” không được giữ.
- Sửa tối thiểu: sau `urlsplit`, truy cập `hostname` trong `try/except ValueError`; bắt buộc hostname khác rỗng, không whitespace/control/backslash, port hợp lệ và authority canonical. Thêm hai case trên cùng các biến thể malformed authority vào regression.

## PASS giới hạn

| Kiểm tra | Kết quả | Bằng chứng/giới hạn |
|---|---|---|
| Auth trước query/dependency; role detail/mixed/leader summary; leader asset bị chặn | PASS | Source review `portal_api/app.py:298-312,377-400` và baseline 41/41. Chỉ JWT/JWKS tổng hợp in-process. |
| Query strict, cursor context/snapshot/after, rank/null-vs-0, response/query caps | PASS | Source review `portal_api/cves.py:122-150,158-209,398-471` và baseline 41/41. |
| Dataset strict cho bool/NaN/null/date/duplicate/bounds và validate toàn dataset | PASS ngoại trừ F2 | Source review `portal_api/cves.py:213-340,505-536`; baseline 41/41. URL authority là gap riêng ở F2. |
| SQLite mở `mode=ro`, path thiếu không tạo file, row/time hỏng fail; request probe không mutation | PASS giới hạn | `portal_api/cves.py:107-119`; baseline và ba assert non-mutation mới. **Schema fail-closed FAIL theo F1**. |
| Năm wire fixtures detail/summary/empty/error/cursor-changed | PASS | Hash QA khớp manifest; baseline so exact với API response thật. |
| Header `no-store` / `Vary` trên route và error | PASS | `portal_api/app.py:201-212,214-242`; baseline 41/41. |
| Source/Git không bị thay đổi | PASS | HEAD vẫn `a49486c...`; status/diff/index rỗng; `git diff --check` exit 0. |

## UNVERIFIED

Gateway/runner, Frontend/parser, browser/viewport, JWT/Cloudflare/HTTPS thật, nguồn CVE/CISA thật, OpenCTI/feed, lab và production. Fixture tổng hợp không chứng minh freshness/chất lượng nguồn hoặc phiên bản thực sự bị ảnh hưởng.

## Artifact

- `w03-backend-qa-evidence/test_w03_backend_qa_probes.py`
- `w03-backend-qa-evidence/baseline.log`
- `w03-backend-qa-evidence/probe-final.log`
- `w03-backend-qa-evidence/wire-hashes-qa.txt`
