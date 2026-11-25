# W03-PRODUCT-BOUNDARY-FIX — kết quả Backend local

## Kết luận

**PASS phạm vi product boundary Backend; FAIL một test wire nền do CRLF/LF; không tuyên bố toàn integration đạt.**

- Worktree: `$WORKSPACE\cti-w03-product-boundary`
- Branch: `fix/w03-product-boundary-20261112`
- Base: `d09929311b4b6447aac8b2ec6adac5999beda25d`
- Commit/HEAD sạch: `1401402122a58baa7dba2b3f1a75abc080baabab`
- Commit message: `fix(w03): align affected product boundary`
- Commit exit: `0`; `git status --short` sau commit rỗng.
- Source integration được giữ nguyên; lúc intake có sửa đổi chưa commit của Engineer tại `tools/local_integration/tests/test_runner.py`, không được đưa vào worktree mới.

## Thay đổi

Diff từ base: 5 file allowlist, `90 insertions, 6 deletions`:

- `portal_api/cves.py`: chỉ nâng affected product `128→256`; vendor vẫn 128.
- `portal_api/tests/test_cves_api.py`: boundary product/vendor, astral/code point, control và 257 fail-closed.
- `portal_api/tests/test_cves_status_api.py`: relation product256 qua GET/PUT/GET/history đúng một audit; dataset257 không ghi.
- `docs/specs/W03-read-local-contract.md`: affected vendor 128, product 256 Unicode code point.
- `docs/PROGRESS.md`: ghi rõ mức kiểm chứng cục bộ và capture integration chưa sửa.

Không đổi trim, Cc/Cf/Cs policy, auth, role, body/response cap, rank, pagination/cursor, status/audit semantics, gateway, UI hay harness.

## RED → GREEN

Interpreter dùng lại, không cài dependency:
`$WORKSPACE\cti-w03-read-backend\.venv\Scripts\python.exe`
— Python `3.13.14`, pytest `9.2.0`.

- RED trước code: selector mới exit `1`, `4 failed, 6 passed`; product129/256/astral và status product256 fail đúng legacy cap128.
- GREEN sau một thay đổi code: cùng selector exit `0`, `10 passed`.
- Focused cuối: exit `0`, `12 passed, 106 deselected`.

Chi tiết: `w03-product-fix-evidence\RED-GREEN.md`.

## Kiểm chứng cuối

- Focused boundary/status: exit `0`, `12 passed`.
- Hai module trừ wire nền: exit `0`, `117 passed, 1 deselected`.
- Hai module chính xác: exit `1`, `117 passed, 1 failed`.
- Ruff check: exit `0`.
- Ruff format check: exit `0`.
- Diff/status/allowlist: 5 file đúng brief; tree sạch.

Test duy nhất còn FAIL là `test_checked_in_wire_fixtures_equal_real_api_responses`. Nguyên nhân đã cô lập là fixture checkout CRLF có SHA-256 `1c44...`, còn wire ghim blob LF `8930...`; tree nguồn cùng base cũng có CRLF. Đây là lỗi portability nền, không do product change; fixture/wire ngoài allowlist nên không sửa.

Evidence: `$WORKSPACE\w03-product-fix-evidence`.

## Trạng thái bằng chứng

- **PASS local/in-process:** product128/129/256; astral256; product257 fail-closed; vendor128/129 giữ nguyên; control bị chặn; GET/PUT/GET/history product256 có đúng một status/audit; dataset257 không mutation.
- **FAIL nền:** một wire fixture hash phụ thuộc line ending như trên.
- **UNVERIFIED:** capture product256 integration, browser, gateway thật, feed/OpenCTI, lab, cloud và production. Capture hiện vẫn cố ý kỳ vọng 256→503, chờ Engineer cập nhật sau khi commit này được review/ghép.
