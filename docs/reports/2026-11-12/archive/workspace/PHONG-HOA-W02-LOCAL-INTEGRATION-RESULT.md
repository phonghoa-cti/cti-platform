# W02-LOCAL-INTEGRATION — kết quả

## Kết luận

**PASS cục bộ tại commit triển khai `50277102bbcfd0c011c1e162569b2c4fe4560189`.** UI `/tra-cuu` → gateway exact `/api/ioc` → API W02 chạy cùng local run với dữ liệu/JWT tổng hợp. `/tra-cuu/mau` vẫn là nguồn mẫu không gọi mạng. Rework tài liệu tại commit `aeff542a20ecc6fe436a0884801fdd69ab0435f6` chỉ sửa README/PROGRESS và provenance báo cáo; không chạy lại hoặc nâng mức bằng chứng chức năng.

Không suy kết quả này thành Cloudflare/JWKS/HTTPS, OpenCTI, lab hay production.

## Git và phạm vi

- Base HTTP: `88e9a9b6e491c0d450640e848043f41c80feb4bd`.
- Source API: `78b026003c86985c7f062986088bfd1f7210a1b1`; delta base `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Branch: `feat/w02-local-integration-20261111`.
- Commit triển khai: `50277102bbcfd0c011c1e162569b2c4fe4560189`; diff 19 file, `+1538/-21`.
- Commit rework docs: `aeff542a20ecc6fe436a0884801fdd69ab0435f6`; diff từ commit triển khai: 2 file, `+11/-1`, chỉ `docs/PROGRESS.md` và `tools/local_integration/README.md`.
- Bốn file API tại commit triển khai có blob hash trùng source API: `app.py e320a39…`, `schemas.py b372719…`, `ioc_lookup.py 19c0b12…`, `test_w02_ioc_api.py ca16dfe…`.

## RED → GREEN của commit triển khai

Chi tiết lịch sử tại `w02-local-integration-evidence/red-green.md`.

- Route/nhãn: RED `1 fail/33 pass`, GREEN `34/34`.
- Gateway: RED `1 fail/9 pass` (404), GREEN `10/10`.
- Runner: RED 7 điểm nối fail, GREEN mục tiêu `8/8`, hồi quy `25/25`.

## Bằng chứng kiểm tra đã lưu

Bảng dưới là kết quả được ghi trong evidence của lượt triển khai, không phải các lệnh được chạy lại trong rework docs này:

| Artifact | Kết quả đã ghi |
|---|---|
| `portal-api-tests.log` | 178 test PASS |
| `runner-tests.log` | 25 test PASS |
| `gateway-tests.log` | 10 test PASS |
| `web-tests.log` | 9 file, 178 test PASS |
| `web-typecheck.log`, `web-lint.log` | PASS |
| `web-build.log` | webpack build PASS; `/tra-cuu` và `/tra-cuu/mau` prerender |
| `ruff-check.log`, `ruff-format.log` | PASS; 21 file formatted |
| `diff-check.log` | PASS |
| `http-matrix.log` | 37 checks, `EXIT=0` theo artifact cũ |

`npm run build` mặc định từng exit 1 vì Turbopack không chấp nhận junction cache `node_modules` nằm ngoài worktree; build được ghi nhận trong artifact là lần chạy webpack, không tải/cài dependency.

## Lệnh tái chạy W02 đã sửa

### Lệnh mẫu có thể tái chạy

Chạy từ root target:

```powershell
Set-Location $WORKSPACE\cti-w02-local-integration
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w02_matrix
```

Target không có `.venv`. Python ở `cti-x01-ingest-browser-prep` là fallback integration environment có `uvicorn` và resolve được module `tools.local_integration.tests.run_w02_matrix`; rework chỉ kiểm tĩnh việc resolve module/dependency, không chạy matrix.

### Lệnh thực tế Leader đã chạy

Leader chạy từ root target đúng lệnh:

```powershell
..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w02_matrix
```

Kết quả thực tế: **37 checks, exit 0**. Raw duy nhất cho lần tái chạy này: `leader-integration-review-20261111/w02-http-matrix-run.log`, SHA-256 `157438825d327bb67cfd730c83deee7f703b4d227ba7f9c2040d6d2231f9557c`.

### Các lỗi tái chạy phải giữ lại

- `.venv\Scripts\python.exe` dưới target không tồn tại; không gán exit cho đường dẫn chưa chạy được này.
- Python của `cti-w02-lookup-api` resolve được interpreter nhưng thiếu `uvicorn`; lần thử cũ kết thúc bằng `ModuleNotFoundError: No module named 'uvicorn'`. Đây không phải lệnh PASS.
- Gọi file `tools\local_integration\tests\run_w02_matrix.py` trực tiếp thiếu package/module path ổn định; README nay dùng `-m tools.local_integration.tests.run_w02_matrix`. Không gán exit 0 của lệnh module cho lệnh direct-script cũ.

## HTTP và provenance browser

- HTTP Leader rerun: route UI + sample route + API, found/allowlist/not-found, IT/analyst/IT+analyst, hidden-data invariant, 401/403/422/503, `no-store`, `Vary`, chống giả header JWT: **PASS 37 checks, exit 0** theo raw riêng nêu trên.
- Evidence browser cũ `w02-local-integration-evidence/browser-observations.md` ghi ba run riêng: `64139` (`w02-it`, found/allowlist/unknown, VI/EN), `54331` (401) và `62630` (503). Ảnh `browser-found.png` thuộc run `64139`; hai run lỗi chỉ có ghi chép trong artifact, không có ảnh riêng.
- Mốc file của evidence cũ nằm trong khoảng 19:14–19:21 ngày 11/11/2026; manifest cũ hash 15 artifact và không chứa bằng chứng cho port `52341`.
- Port `52341` chỉ xuất hiện trong lời trả hậu kiểm sau đó, không có URL/screenshot/summary tương ứng trong evidence cũ. Vì vậy đây là run hậu kiểm riêng; chi tiết browser và cleanup của run `52341` là **UNVERIFIED từ artifact hiện có** và không được nhập vào run `64139/54331/62630`.
- Copy canonical trên browser: **UNVERIFIED** vì clipboard bị từ chối. Unit regression clipboard đã PASS nhưng không thay thế bằng chứng clipboard browser.

## Cleanup và giới hạn

- Artifact browser cũ ghi browser đã đóng, các port owned `64139`, `54331`, `62630` đã đóng và không còn temp `w05-local-*`; đây là cleanup của ba run cũ, không phải bằng chứng cleanup cho `52341`.
- HTTP matrix Leader trả `cleanup=true` trong raw cùng run.
- Rework docs không khởi động listener/browser, không chạy lại matrix/suite/build, không cài dependency và không sửa shared environment.
- Không Internet/feed/model/secret/cloud/OpenCTI/lab; không push/PR/merge/deploy.
- Cloudflare/JWKS/HTTPS thật, OpenCTI, lab, production và clipboard browser: **UNVERIFIED**.

Evidence triển khai cũ giữ nguyên tại `w02-local-integration-evidence/`. Evidence riêng cho rework docs nằm tại `w02-local-integration-evidence/rework-docs/`.
