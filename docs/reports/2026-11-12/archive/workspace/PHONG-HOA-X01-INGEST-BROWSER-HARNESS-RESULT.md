# PHONG HỎA — X01 ingest browser harness result

## Kết luận

**PASS F1–F3 và baseline TXT/PDF offline; browser/end-to-end thật vẫn `UNVERIFIED`.** Hai false PASS F3 mới đã có RED→GREEN: marker Unicode escape trong `report.description` và IOC đã bỏ xuất hiện ngoài SCO đều bị từ chối bằng `RuntimeError` đúng lý do. Đây là sửa verifier, không phải bằng chứng exporter hiện tại từng lộ dữ liệu.

## Ref, diff và phạm vi

- Tree/branch: `cti-x01-ingest-browser-prep` / `feat/x01-ingest-browser-prep-20261111`.
- Base lượt này: `cba5b39c4e95449aa152dae5c2a1099c2e75c515`.
- HEAD/commit sạch: `16e6f889b4e8cd2e3bd1fa7147c81106cf6a328c`, `fix(integration): reject semantic bundle leaks`.
- Diff: 4 file, `+83/-9`; chỉ `docs/PROGRESS.md`, `tools/local_integration/README.md`, verifier và test runner đúng allowlist.
- Producer chỉ đọc `8a16758601647fb3dbf935abecc2435f3b7a3fb6`; W05 source `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; target và hai source đều status count `0`.

## RED→GREEN và regression

- RED: 2/2 mutation `DID NOT RAISE RuntimeError`, exit 1 (`01-red-semantic-description.log`).
- GREEN unit: 2/2 passed, exit 0. Verifier duyệt chuỗi semantic sau JSON parse nên không phụ thuộc escape/whitespace; IOC đã bỏ được tính theo tập `deselected - selected` để không chặn giá trị duplicate vẫn được chọn.
- Script Leader nguyên trạng: baseline `ACCEPTED`; F1 canonical envelope, F2 hai actor/audit mutation và F3 cũ đều `REJECTED`; hai F3 mới trả `RuntimeError` lần lượt `STIX lộ privacy marker` và `STIX chứa IOC đã bỏ ngoài SCO`; `false_passes=[]`, exit 0 (`04-leader-verify-green-utf8.log`).
- `test_runner.py`: `40 passed`, exit 0; giữ lifecycle/cleanup và toàn bộ F1/F2/F3 (`08-runner-postformat.xml/log`).
- TXT offline: PASS, duplicate=true, final `[1]`, 1 selection audit, 4 STIX object, export read-only, exit 0.
- PDF offline: PASS, duplicate=true, final `[0]`, 2 selection audit, 4 STIX object, export read-only, exit 0.
- Ruff check/format và `git diff --check`: exit 0 (`09-static-final.log`).

## Evidence

- Exact commands: `x01-ingest-browser-harness-evidence/rework-f3-semantic/COMMANDS.md`.
- Raw RED/GREEN/final/ref: `x01-ingest-browser-harness-evidence/rework-f3-semantic/`.
- Manifest: `21` raw artifact, SHA-256 `418868a844e702ddf4e6c4add508f136c5ac7200fc5132139d8049760302620d`; hash report nằm riêng ở `RESULT.sha256`.
- Ref/diff/status sạch: `10-refs-diff-status.log`.

## Giới hạn

- Chưa ghép importer vào tree tích hợp; không cherry-pick/merge/push/PR.
- Chưa chạy `browser-session`, browser tích hợp hoặc listener demo; browser/end-to-end vẫn `UNVERIFIED`.
- Không chứng minh OpenCTI, lab, cloud, model, feed, Cloudflare/JWKS/HTTPS thật, deploy hoặc production.
