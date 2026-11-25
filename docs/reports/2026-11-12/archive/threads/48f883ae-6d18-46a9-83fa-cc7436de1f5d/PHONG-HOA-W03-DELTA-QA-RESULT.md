# PHONG HỎA — W03-STATUS-DELTA-QA

Ngày kiểm: 12/11/2026. Phạm vi: chỉ đọc hai candidate từ cùng base; không chạy lại chặng A/full suite, không khởi động browser/helper, không sửa/ghép nhánh nguồn.

## Kết luận

| Kiểm tra | Kết luận | Bằng chứng chính |
|---|---|---|
| Delta Backend product256/vendor128 | **PASS cục bộ** | `12 passed, 106 deselected`, exit `0`; diff đúng 5 file `+90/-6`; HEAD/status không đổi |
| Nguyên nhân test wire | **FAIL tái lập sạch trên Windows; nguyên nhân đã xác minh** | test riêng `1 failed`, exit `1`; checkout CRLF hash `1c44...`, blob base/candidate LF hash `8930...`; chỉ ba `body.source.dataset_id` lệch; bản sao LF khớp 5/5 wire |
| Chặng B khóa ghi sau remount | **PASS bằng chứng cục bộ** | manifest 27/27; trace `GET200→PUT503→GET503→GET503→GET200`, đúng 1 PUT và 1 `/lo-hong`; ảnh/DOM/accessibility khóa mutation trước GET200; SQLite `0/0→1/1` |
| Toàn W03-S1 sau ghép | **UNVERIFIED** | Hai candidate chưa ghép; capture/parser gate product256 chưa cập nhật/kiểm lại; không kiểm lab/cloud/feed/OpenCTI/production |

Không chấp nhận toàn W03-S1 từ kết quả này và không thay đổi trạng thái chặng A/`accepted_results`.

## Ref và bất biến nguồn

- Base chung: `d09929311b4b6447aac8b2ec6adac5999beda25d`.
- Backend: branch `fix/w03-product-boundary-20261112`, HEAD trước/sau `1401402122a58baa7dba2b3f1a75abc080baabab`, `git status --short` trước/sau rỗng.
- Engineer: branch `feat/w03-status-integration-20261112`, HEAD trước/sau `170a38bb92fee09bd2e917faedc8de6342046b54`, `git status --short` trước/sau rỗng.
- Không commit, push, PR, merge, deploy, sửa RUNS, cài dependency hoặc dùng dữ liệu thật.

## A. Delta Backend — PASS cục bộ

### Review diff

`git diff --stat <base> HEAD`, `git diff --name-status <base> HEAD` và `git diff --check <base> HEAD` xác nhận 5 file, `90 insertions, 6 deletions`, diff-check exit `0`:

- `portal_api/cves.py:326`: duy nhất policy runtime đổi affected product từ 128 lên 256 Unicode code point.
- `portal_api/tests/test_cves_api.py:518`: product 128/129/256 và 256 ký tự astral.
- `portal_api/tests/test_cves_api.py:536`: vendor 128 đạt, 129 fail-closed.
- `portal_api/tests/test_cves_api.py:553`: Cc/Cf vẫn bị từ chối.
- `portal_api/tests/test_cves_status_api.py:143`: GET/PUT/history product256 có đúng một record/audit.
- `portal_api/tests/test_cves_status_api.py:161`: dataset product257 trả 503, không mutation.
- Hai file tài liệu chỉ cập nhật contract/giới hạn bằng chứng; không đổi auth, role, audit, trim, control, rank, cursor, gateway hay UI.

### Chạy focused mới

Interpreter dùng lại, không cài dependency:

`$WORKSPACE\cti-w03-read-backend\.venv\Scripts\python.exe`

Lệnh:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py portal_api/tests/test_cves_status_api.py -k 'affected_product_boundary or affected_vendor_boundary or affected_product_controls or product_256_get_put_history or product_257_dataset or w03_synthetic_product_and_source_contract'
```

Kết quả mới: exit `0`; `12 passed, 106 deselected` trong `5.76s`. Probe import sau khi áp dụng đúng `pythonpath = . core extractor` của `pytest.ini` xác nhận `portal_api.cves` đến từ chính candidate Backend. Lần probe standalone đầu thiếu các pythonpath này nên exit `1` với `ModuleNotFoundError: phonghoa_core`; đây là lỗi cách gọi probe, không phải kết quả test, và đã sửa bằng đúng cấu hình repo.

Raw: `w03-delta-qa-evidence/01-backend-focused.log`.

## B. Lỗi wire — FAIL, nguyên nhân CRLF/LF đã xác minh

Test riêng tại `portal_api/tests/test_cves_api.py:780`:

```powershell
& $python -m pytest -o addopts='' portal_api/tests/test_cves_api.py::test_checked_in_wire_fixtures_equal_real_api_responses
```

Kết quả mới: exit `1`; `1 failed` trong `1.12s`.

Đối chiếu bytes `portal_api/tests/fixtures/w03-cves-synthetic.json`:

| Nguồn | Size | CRLF/LF | SHA-256 |
|---|---:|---:|---|
| checkout Windows candidate | 1362 | 1 CRLF, 0 LF đứng riêng | `1c44a50597b702259dc89b242f4e16cfd37f7a574efda48743e61a440c51a872` |
| Git blob base `d099293...` | 1361 | 0 CRLF, 1 LF | `89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73` |
| Git blob candidate `1401402...` | 1361 | 0 CRLF, 1 LF | `89304e284654d5558014365b919c84ecc17346998ff12ebf22869066f1fa6b73` |

Probe field-level cho checkout hiện tại chỉ tìm thấy đúng ba chênh lệch:

- `detail.body.source.dataset_id`;
- `summary.body.source.dataset_id`;
- `empty.body.source.dataset_id`.

Các response `error` và `cursor-changed` khớp; ngoài ba `dataset_id` trên không có field nào khác lệch. Bản sao tạm chỉ đổi CRLF cuối file thành LF làm cả 5 wire fixture khớp; probe exit `0`, và `SOURCE_UNCHANGED=True`.

**Finding WIRE-01 — MEDIUM, lỗi khả năng tái lập đa nền tảng.** API đúng khi băm bytes thực; wire fixture ghim hash của blob LF nhưng checkout Windows chuyển dòng kết thúc thành CRLF. Vì vậy đây không phải regression product256, nhưng làm clean-checkout gate đỏ và làm `dataset_id` phụ thuộc checkout.

**Sửa nhỏ nhất đề xuất, chưa triển khai:** thêm rule đường dẫn hẹp trong `.gitattributes`, ví dụ `portal_api/tests/fixtures/w03-cves-synthetic.json text eol=lf`, re-checkout/renormalize đúng fixture này, rồi chạy lại test wire riêng. Không nới assertion và không đổi logic băm.

Raw: `w03-delta-qa-evidence/02-wire-failure.log`, `03-wire-byte-and-field-probe.log`, probe tái lập `probe_wire.py`.

## C. Chặng B — PASS bằng chứng cục bộ

### Delta harness

Từ base đến `170a38b...`: 5 file, `+50/-0`, diff-check exit `0`; chỉ `tools/local_integration/**` và `docs/PROGRESS.md`. Runtime product/gateway semantics không đổi. Scenario mới tại `tools/local_integration/runner.py:113,276,565`, regression tại `tools/local_integration/tests/test_runner.py:208`, helper allowlist tại `tools/local_integration/w04_browser_helper.py:34`.

### Tính toàn vẹn và cùng run

- Manifest schema `phong-hoa-evidence-manifest-v1`: 27/27 entry khớp tên, size, SHA-256; không có file ngoài manifest; manifest SHA-256 `db06cb0e23547a91f8567415ab83c7398a46fba68e8b0892f84572db439cba96`.
- Run ID `91946e5b7a51492a856a38e55aa0d4d6`; session UTC `00:32:46.205031` đến `00:34:40.066319`.
- Record SQLite UTC `00:33:24.217181`, nằm trong session. Mtime initial DB, trace, ảnh khóa, ảnh phục hồi và final DB đều nằm theo thứ tự trong cùng cửa sổ; helper stdout dùng cùng run ID/temp-root/port.

### Chuỗi hành vi

Trace gốc:

1. counter 11: GET status `200`;
2. counter 12: PUT status `503` sau commit;
3. counter 13: GET tự đối soát `503`;
4. counter 14: GET sau đóng/mở lại cùng trang `503`;
5. counter 15: GET khi bấm `Đối soát lại` `200`.

Đếm toàn trace: PUT status đúng `1`; GET `/lo-hong` đúng `1`; không có PUT thứ hai.

Trước GET200, ảnh `unknown-reentry-locked-after-remount.png`, DOM và accessibility đều cho thấy cảnh báo unknown + lỗi đọc + nút GET-only `Đối soát lại`; không có status select, note textarea hay save button. Sau GET200, ảnh phục hồi hiện `Đang xử lý · v1`, note `Unknown reentry controlled evidence`, actor `it-sub`.

Hai SQLite được mở `mode=ro`, `PRAGMA quick_check=ok`:

- initial: `cve_status_records=0`, `cve_status_audit=0`;
- final: một record `patching`, version `1`, note và actor đúng; một audit `created` có cùng context/note/status/version/actor.

Cleanup kiểm mới: PID `41064` absent, listener port `55289` absent, temp-root `$USER_HOME\AppData\Local\Temp\w05-local-8piecjva` absent. Không dừng tiến trình nào.

Raw/tổng hợp QA: `w03-delta-qa-evidence/04-stage-b-artifact-review.log`. Artifact nguồn: `...\783188b9-409e-47a1-b799-eab58c16854a\w03-status-stage-b-rework`.

## Việc tối thiểu cho Engineer khi tích hợp

1. Sửa WIRE-01 bằng rule LF đường dẫn hẹp và chứng minh test wire riêng xanh trên clean checkout Windows.
2. Sau khi review/chọn cách ghép commit Backend `1401402...` vào integration, cập nhật capture/parsing gate đang kỳ vọng product256→503 thành product256 hợp lệ và product257 fail-closed; giữ vendor128.
3. Chạy focused product/vendor/status và capture tích hợp liên quan sau ghép; không cần lặp toàn chặng A nếu không có delta ảnh hưởng.

## Chưa xác minh

- Không xác minh nhánh sau ghép vì chưa có ref tích hợp product256 + chặng B.
- Không chạy lại test chặng B vì artifact đủ và brief cấm khởi động helper/browser không cần thiết; `focused-tests.log` gốc ghi `2 passed`, nhưng không được nâng thành test mới của QA.
- Không kiểm mobile, Cloudflare/JWKS/HTTPS thật, feed/OpenCTI, lab, cloud, production hoặc dữ liệu thật.

## Evidence QA

- `w03-delta-qa-evidence/01-backend-focused.log`
- `w03-delta-qa-evidence/02-wire-failure.log`
- `w03-delta-qa-evidence/03-wire-byte-and-field-probe.log`
- `w03-delta-qa-evidence/04-stage-b-artifact-review.log`
- `w03-delta-qa-evidence/05-git-and-diff.log`
- `w03-delta-qa-evidence/probe_wire.py`
