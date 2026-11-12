# W03-STATUS-INTEGRATION-PREP — recovery result

Ngày 12/11/2026. Kết luận: **PASS rework R1 cục bộ**. Đây chưa phải nghiệm thu UI/browser hoặc toàn W03-S1.

## Git và phạm vi

- Tree: `$WORKSPACE/cti-w03-status-integration`
- Branch: `feat/w03-status-integration-20261112`
- Base R1: `32b5c068c4d6da5a0abb00906c619f92f13b9177`
- Final HEAD: `65e31980ac01910b825951676bae428ca3bf1742`
- Commit: `fix(integration): scope W03 status recovery faults`
- Delta: 5 file, `+71/-7`; đúng allowlist: `tools/local_integration/**`, `docs/PROGRESS.md`.
- `git status --porcelain=v1`: rỗng; tree sạch.
- Không sửa probe Leader, Backend, Frontend, dependency hoặc RUNS; không cherry-pick UI; không push/PR/merge/deploy.

## Sửa R1

Fault GET được lưu theo exact pathname status vừa PUT thay vì một bộ đếm dùng chung. GET relation khác và
`status-history` không nhận hoặc tiêu thụ fault. Dùng map theo pathname nên hai relation được PUT xen kẽ giữ
bộ đếm độc lập.

## Bằng chứng đã đối chiếu

Evidence rework gốc, không bị ghi đè:

`$THREADS/cf98b168-ecfc-4799-bd0f-0a78c1ed38ff/w03-status-integration-prep-rework-evidence/`

| Kiểm tra | Command/nguồn | Exit | Kết quả |
|---|---|---:|---|
| 2 probe Leader | `node --test .../fault-scope-probe.mjs` | 0 | 2 PASS, 0 FAIL; probe SHA-256 giữ `4d0b52f3...e4e8f` |
| Gateway targeted | `node --test tools/local_integration/tests/test_gateway.mjs` | 0 | 17 PASS, 0 FAIL |
| HTTP/SQL status matrix | `python -X utf8 -B -m tools.local_integration.tests.run_w03_status_matrix ...` | 0 | 150 assertion PASS |
| Ruff | `python -m ruff check tools/local_integration` | 0 | 0 diagnostic (`ruff.json=[]`) |
| Format, chạy mới lúc recovery | `python -m ruff format --check tools/local_integration` | 0 | 19 file đã định dạng |
| Diff check, chạy mới lúc recovery | `git diff --check` | 0 | không lỗi whitespace |

Probe known: PUT A 200; GET relation B 200; GET A history 200; GET A `503→503→200`.
Probe unknown: PUT A 503 sau upstream commit; GET relation B 200; GET A history 200; GET A `503→200`.

Ma trận API/SQLite thật dùng relation B hợp lệ `CVE-2026-2013/technologies/2`. Mỗi scenario có đúng một PUT,
một `cve_status_records` và một `cve_status_audit`; snapshot SQL không đổi qua hai GET xen kẽ. Trace chỉ có
counter/method/path/status, không chứa JWT hoặc body.

## Cleanup và manifest

- Ma trận PASS bao gồm assertion xóa temp root sở hữu và đóng primary gateway port.
- Kiểm mới sau recovery: `owned_runtime_processes=0` cho Node/Python gắn tree; không có thư mục `w05-local-*`
  nào được tạo từ 04:26 trở đi.
- Evidence recovery mới: `$THREADS/484d57b0-1cb9-4264-b24a-54cecff6e454/w03-status-prep-recovery-evidence/`
- `RECOVERY-CHECKS.json` ghi SHA/delta/count/cleanup; `SHA256SUMS.txt` khóa 13 mục mới, cũ và input Leader.

## PASS / UNVERIFIED

PASS: fault scope exact relation/status, hai probe Leader, gateway targeted, HTTP/SQL/trace, phục hồi hữu hạn,
format/diff-check, manifest và cleanup.

UNVERIFIED: ghép Frontend `2448b860`, UI/browser desktop/mobile, toàn W03-S1, feed/OpenCTI,
Cloudflare/JWKS/HTTPS thật, lab và production.

## Hoàn tác

Nếu Leader không nhận R1, chạy `git revert 65e31980ac01910b825951676bae428ca3bf1742` trong đúng tree để tạo
commit hoàn tác có lịch sử; không dùng reset vì có thể làm mất thay đổi kế tiếp.
