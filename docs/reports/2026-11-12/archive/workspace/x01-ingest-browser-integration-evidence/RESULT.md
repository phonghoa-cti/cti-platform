# X01 ingest → browser → STIX — kết quả tích hợp cục bộ

Ngày chạy: 11/11/2026 (Asia/Saigon).

## Kết quả

**PASS cục bộ** tại `cti-x01-ingest-browser-integration@5fd527fc5d9b113ac2725a855f3ac75c9b106762`.

- TXT synthetic: producer → importer → W05 browser bỏ IOC đầu/lưu/duyệt → STIX trên cùng SQLite; một selection audit, một decision audit, bundle 4 object.
- PDF synthetic: đúng một IOC eligible; browser lưu rỗng, chọn lại IOC đó, lưu, duyệt → STIX; đúng hai selection audit, một decision audit, bundle 4 object.
- Retry importer cùng envelope/creator trả duplicate cùng draft ID; verifier xác nhận source/envelope/provenance/hash không đổi.
- Subject tạo draft tự duyệt nhận HTTP 403; decision audit = 0.
- Save-refresh 503: một POST save đã ghi, hai GET refresh (detail/list) lỗi; một lần “Tải lại trạng thái” chỉ GET và vẫn lỗi; hậu kiểm đúng một selection audit, không decision audit.
- Decision-refresh 503: selection đã seed đúng một event, một POST approve đã ghi, hai GET refresh lỗi; một lần “Tải lại trạng thái” chỉ GET và vẫn lỗi; hậu kiểm đúng một selection audit và một decision audit.
- Exporter được chạy sau approve, DB inventory trước/sau bằng nhau; bundle không chứa IOC bỏ chọn, raw source, evidence hoặc subject.
- Năm listener loopback và process/thread/temp do từng `LocalRun` sở hữu đã được cleanup.

## Ref và nguồn

- Base importer: `fc08897a240d9e55198b1a8166b21e8e7caf7213`.
- Harness source: `16e6f889b4e8cd2e3bd1fa7147c81106cf6a328c`; delta 5 file `db36ec0..16e6f88` được mang nguyên vẹn trước phần TDD mới.
- Producer source: `8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- W05/STIX source tham chiếu: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Bốn source tree trên sạch và đúng SHA khi hậu kiểm.
- Build UI được tái sử dụng từ `cti-w05-selection-integration` sau khi đối chiếu 33/33 tracked blob `portal/web` giống target; hai junction tạm `node_modules` và `.next` đã xóa.

## Browser run và raw evidence

| Run | Port | Thao tác quan sát | Terminal hậu kiểm | Evidence |
|---|---:|---|---|---|
| TXT happy | 56857 | bỏ `evil-one.example`, lưu, duyệt | PASS; selected `[1]`; selection audit 1; decision audit ID 1; bundle `d7c839f6811647a5fb615374855a30b3834d74ea2549c0c472bd658a4f792fbd` | `browser-txt-happy.log/png` |
| PDF happy | 59480 | bỏ `example.test`, lưu rỗng; chọn lại, lưu, duyệt | PASS; selected `[0]`; selection audit 2; decision audit ID 1; bundle `a7b2bc79df92ecf545bca8e8f0858a83f074fcef6070329aa3d822b5c4eb5837` | `browser-pdf-happy.log/png` |
| Self approve | 57352 | click duyệt, UI báo không đủ quyền; Browser ghi POST decision → 403 | PASS; outcome denied; selection audit 0; decision audit 0 | `browser-self-approve.log`, `browser-self-approve-403.png` |
| Save refresh 503 | 63957 | bỏ IOC đầu, save; Browser ghi GET detail/list → 503; click tải lại một lần | PASS; pending; selection audit 1; decision audit 0 | `browser-save-refresh-503.log/png` |
| Decision refresh 503 | 50179 | selection `[1]` đã lưu; duyệt; Browser ghi GET detail/list → 503; click tải lại một lần | PASS; approved; selection audit 1; decision audit ID 1; bundle `e233e0519ac117ba44876106967897bb484f07461e78865902d1cffe8b35448f` | `browser-decision-refresh-503.log/png` |

Browser không trả mã step ổn định trong lượt này; bảng ghi theo đúng port/run, raw log và ảnh tương ứng.

## TDD và lệnh kiểm

- RED case plan/scenario: 6 failure đúng do thiếu `browser_case_plan` và scenario chưa được phép, exit 1; GREEN 6 pass, exit 0.
- RED nonterminal verifier: 2 failure đúng do thiếu verifier, exit 1; GREEN 2 pass, exit 0.
- RED PDF browser orchestration: 1 failure do thiếu tham số `case`, exit 1; GREEN 1 pass, exit 0.
- `<queue .venv python> -m pytest tools/local_integration/tests/test_runner.py -q` → 49/49 pass, exit 0.
- `<queue .venv python> -m pytest -q` → 561/561 pass, exit 0.
- TXT/PDF `offline-check` → mỗi lệnh PASS, exit 0; duplicate verified, export read-only.
- `<queue .venv python> -m ruff check tools/local_integration` → exit 0.
- `<queue .venv python> -m ruff format --check tools/local_integration` → 9 files formatted, exit 0.
- `git diff --check` → exit 0.
- Cleanup: ports 56857/59480/57352/63957/50179 đều listener_count=0; không còn Python/Node command line của các run; junction môi trường đã xóa.

Python thực chạy: `cti-x01-ingest-queue\.venv\Scripts\python.exe` 3.12.13; producer dùng `cti-x01-ingest-local\.venv\Scripts\python.exe` 3.12.13. Không cài/sửa dependency dùng chung.

## Diff và hoàn tác

- Commit: `5fd527fc5d9b113ac2725a855f3ac75c9b106762`.
- Diff: 6 file, `+1517/-10`, đúng allowlist.
- Hoàn tác: `git revert 5fd527fc5d9b113ac2725a855f3ac75c9b106762` trên branch này; không reset source tree.

## UNVERIFIED

Cloudflare Access/JWKS/HTTPS thật, OpenCTI import, dữ liệu báo cáo thật, feed/LLM, lab, production, network share và crash/power-loss vẫn **UNVERIFIED**. Gateway fault cố ý tiếp tục trả 503, nên lượt này chứng minh không POST lặp và DB đúng, không chứng minh upstream tự phục hồi.
