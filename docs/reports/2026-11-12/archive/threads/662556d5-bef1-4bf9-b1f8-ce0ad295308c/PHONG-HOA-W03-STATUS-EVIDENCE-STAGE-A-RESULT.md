# W03-S1 status evidence — kết quả chặng A

Ngày 12/11/2026. Kết quả tổng: **PARTIAL đúng phạm vi chặng A**. Mã/harness/docs đã commit sạch; E1 đạt các biên có thể biểu diễn nhưng product 256 chưa đạt; browser known được tái dùng và kiểm hash/cleanup; browser unknown reentry cùng trang còn **PENDING chặng B**. Không tuyên bố W03-S1 hoàn tất.

## Git và phạm vi

- Tree: `$WORKSPACE\cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Base: `a2c4ffa245297a8714b0023bf4e4bb248869dc36`
- Final HEAD: `d09929311b4b6447aac8b2ec6adac5999beda25d`
- Commit: `test(w03): capture status evidence boundaries`
- Delta: 9 file, `+329/-27`; chỉ helper/tests/docs trong allowlist.
- Final `git status --short --branch`: chỉ dòng branch, không có file sửa/untracked.
- Hoàn tác: `git revert d09929311b4b6447aac8b2ec6adac5999beda25d`.

## Kết quả E1 — PARTIAL

Capture chạy qua gateway/API/store thật và production parser/provider của UI:

- 10 response được thu; capture exit 0.
- Unicode thật: `Nhà cung cấp`, `Sản phẩm`, `Phiên bản`, `Đã xác minh trạng thái` nằm trong response API và được parser production đọc.
- Đạt: note 1000 ký tự, actor JWT 512, vendor 128, software version 128, product 128.
- History: 101 audit thật; trang đầu `limit=100` có 100 item và `next_cursor`, trang sau có 1 item và cursor null.
- Parser/provider production: 6/6 PASS.
- Gate required: env thiếu, thư mục tồn tại nhưng thiếu fixture, JSON hỏng đều thoát 1 như yêu cầu.

Product 256 **chưa đạt/không biểu diễn được qua dataset hiện tại**:

- PUT technology với product dài 256 trả 200, version 2.
- Loader CVE trả `invalid text` vì `portal_api/cves.py::_product` giới hạn product 128.
- GET status relation trả 503 `status_unavailable`; `cves_status.py`/UI context vẫn cho phép tối đa 256.
- Không sửa product/contract để lách gate. Bằng chứng: `wire-fixtures/product-256-repro.json`; manifest capture ghi `status=PARTIAL`.

## Helper startup và cleanup — PASS

- RED tái hiện: lỗi `RuntimeError("startup failed")` trong `LocalRun.__enter__` bị che bởi `UnboundLocalError` do `running` chưa gán.
- GREEN: ownership state được khởi tạo trước `with`; lỗi gốc tiếp tục nổi lên, state cuối vẫn ghi PID/port/temp-root và hai cờ cleanup.
- Focused Python: 9/9 PASS, gồm actor 512, startup fault injection, cleanup metadata và snapshot DB.

## Browser known — REUSED/VERIFIED; unknown — PENDING

Chặng A không mở browser mới. Tái dùng artifact đã thu trước khi chia chặng từ:
`$THREADS\7720a19d-5db9-427d-9e14-e5ce81e15744\w03-status-evidence-rework\browser-known`.

- Viewport thực: 1280×720, DPR 1.
- Trace: PUT 200 đúng một lần, sau đó GET status `503→503→200`; không reload trang.
- Ảnh `known-temporary-error.png`: notice đã lưu vẫn hiện cùng lỗi đối soát tạm thời.
- Đóng/mở chi tiết trong cùng trang rồi mở status lại; ảnh `known-recovered-same-page.png` cho thấy record v1 phục hồi và notice vẫn còn.
- SQLite cuối: 1 status record, 1 audit; initial là 0/0.
- Session `run_id=7fbd1465149a445da582c0e762a181d9`; PID 26176 đã dừng, port 59272 đóng, temp-root `w05-local-v8891g1q` đã xóa. Chặng A kiểm lại ba điều kiện đều true.
- Unknown-outcome PUT503 + khóa form + đóng/mở trong cùng trang + GET-only reconciliation: **PENDING chặng B**, chưa dùng ảnh cũ/page reload để thay thế.
- History 409 trên browser vẫn UNVERIFIED; đã có HTTP/component evidence nhưng không nâng thành browser PASS.

## Lệnh kiểm mới

CWD cho Python: tree ở phần Git. Interpreter tuyệt đối:
`$WORKSPACE\cti-w03-read-backend\.venv\Scripts\python.exe`.

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `python.exe -m tools.local_integration.tests.capture_w03_status_wire --output <Evidence>\wire-fixtures` | 0 | 10 response; capture PASS, E1 PARTIAL |
| `python.exe -m pytest tools/local_integration/tests/test_runner.py::test_w03_status_runner_can_capture_actor_at_validator_boundary tools/local_integration/tests/test_w04_browser_helper.py -q` | 0 | 9 passed |
| CWD `portal/web`: `npm test -- --run tests/cve-status-wire-capture.test.ts` với required env + fixture dir | 0 | 6 passed |
| Cùng test, required env nhưng thiếu fixture dir | 1 mong đợi | Gate PASS |
| Cùng test, directory có thật nhưng thiếu `boundary-status.json` | 1 mong đợi | Gate PASS; 1 fail/5 pass |
| Cùng test, `boundary-status.json` malformed | 1 mong đợi | Gate PASS; 1 fail/5 pass |
| `python.exe -m ruff check tools/local_integration` | 0 | không diagnostic |
| `python.exe -m ruff format --check tools/local_integration` | 0 | 20 file formatted |
| `git diff --check` | 0 | chỉ cảnh báo LF/CRLF, không lỗi whitespace |

Không lặp full HTTP matrix, build hoặc 58 component tests vì product source/build không đổi và brief cấm lặp kiểm đã đạt.

## Artifact và giới hạn

- Evidence mới: `$THREADS\662556d5-bef1-4bf9-b1f8-ce0ad295308c\w03-status-evidence-stage-a`
- `manifest.json`: 45 artifact, SHA-256 `466d651c7490c5d386ab9e69577a6fb745c00479a0d306e318e51b214e63b8f8`.
- Manifest phân biệt kiểm mới và known artifact tái dùng; report/evidence cũ không bị ghi đè.
- Chưa kiểm mobile, unknown browser reentry, Cloudflare/JWKS/HTTPS thật, feed/OpenCTI, lab, production hoặc LLM thật.

## Chặng B còn đúng một việc

Chạy browser scenario `w03-status-unknown-outcome`: PUT503 + GET503, chụp trạng thái form bị khóa và accessibility disabled/read-only; đóng/mở chi tiết trong cùng trang (không reload), chỉ GET đối soát đến 200; chứng minh trace/SQLite đúng một PUT, một status, một audit và cleanup PID/port/temp-root.
