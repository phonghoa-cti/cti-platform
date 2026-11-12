# PHONG HỎA — W03-STATUS-INTEGRATION chặng B rework

Ngày kiểm: 12/11/2026. Kết luận: **PASS** cho điểm rework “khóa ghi sau remount trước GET thành công”. Toàn W03-S1 vẫn **PARTIAL** vì product128/256 được xử lý ở nhánh Backend riêng và chưa ghép.

## Phiên bản và delta

- Tree: `$WORKSPACE\cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Base: `d09929311b4b6447aac8b2ec6adac5999beda25d`
- Commit: `170a38bb92fee09bd2e917faedc8de6342046b54` — `test: add bounded W03 unknown reentry scenario`
- Delta: 5 file, `+50/-0`; chỉ `tools/local_integration/**` và `docs/PROGRESS.md`.
- Git cuối: sạch; `git diff --check` exit 0.

Thay đổi nhỏ: thêm scenario test-only `w03-status-unknown-reentry`. Scenario kết hợp fault response PUT một lần với bộ đếm hai GET 503 đã có, vẫn ràng buộc theo exact status pathname. Không sửa gateway, UI, Backend, contract, dependency hay RUNS.

## TDD và kiểm mã

- RED runner: exit 1 vì scenario mới chưa được phép.
- RED helper: exit 1 vì helper allowlist chưa có scenario.
- GREEN focused: exit 0, `2 passed`; chứng minh `PUT503 → GET503 → GET503 → GET200`, đúng một PUT và SQLite một status/một audit.
- Ruff check: exit 0.
- Ruff format check cuối: exit 0, bốn file đã đúng định dạng.
- Không lặp chặng A hoặc full suite theo brief.

## Browser trực tiếp

Browser OpenMausBot, viewport `1280×720`, DPR 1; chỉ một lần tải `/lo-hong`.

1. Mở CVE-2026-2001 / Fortinet FortiOS, chọn `Đang xử lý`, note `Unknown reentry controlled evidence`, lưu đúng một lần.
2. Quan sát PUT trả 503 sau upstream commit; GET đối soát tự động trả 503.
3. Đóng rồi mở lại chi tiết/status trong cùng trang, không reload. Remount phát GET 503 lần hai.
4. Trước GET thành công, snapshot và DOM trực tiếp cho thấy thông báo unknown + lỗi đọc + nút `Đối soát lại`. Không tồn tại select trạng thái, textarea ghi chú hoặc nút lưu trong status region; do đó UI không có đường mutation sau remount.
5. Bấm `Đối soát lại` một lần; chỉ GET trả 200. UI hiện `Đang xử lý · v1`, note và actor `it-sub`; form bình thường trở lại.

Trace status chính xác:

- counter 11: GET 200 ban đầu.
- counter 12: PUT 503 sau commit.
- counter 13: GET 503 tự động.
- counter 14: GET 503 sau remount.
- counter 15: GET 200 do người dùng đối soát.

Tổng: `PUT=1`, `/lo-hong=1`; không reload và không replay mutation.

## SQLite và cleanup

- Initial: `cve_status_records=0`, `cve_status_audit=0`.
- Final: `cve_status_records=1`, `cve_status_audit=1`.
- Đọc SQLite `mode=ro`: record `patching`, note đúng, `status_version=1`, actor `it-sub`.
- Run ID: `91946e5b7a51492a856a38e55aa0d4d6`.
- PID helper `41064` đã dừng; port `55289` đóng; temp-root `$USER_HOME\AppData\Local\Temp\w05-local-8piecjva` đã xóa.
- Lần startup đầu gọi script path nên thiếu package root và dừng trước listener; log được giữ. Lần hai dùng module command chuẩn, helper exit 0 và stderr rỗng.

## Bằng chứng

- Evidence: `$THREADS\783188b9-409e-47a1-b799-eab58c16854a\w03-status-stage-b-rework`
- Manifest: 27/27 file khớp SHA256 và kích thước.
- SHA256 manifest: `db06cb0e23547a91f8567415ab83c7398a46fba68e8b0892f84572db439cba96`.
- Ảnh chính: `unknown-reentry-locked-after-remount.png`, `unknown-reentry-recovered.png`.
- Bằng chứng máy đọc: accessibility snapshot, DOM JSON, trace JSONL, hai SQLite, summary trước/sau, focused test/Ruff log, session và verification.

## Giới hạn

- Ca browser local dùng fixture tổng hợp; không chứng minh lab, production, Cloudflare/JWKS/HTTPS, OpenCTI, feed hoặc dữ liệu thật.
- Chặng này không ghép hoặc đánh giá sửa product256 từ Backend. Không tuyên bố toàn W03-S1 hoàn tất.
