# Kết quả W02-LOOKUP-API-IMPLEMENT

Ngày 11/11/2026. Kết luận: **PASS cục bộ/in-process**.

## Git và phạm vi

- Tree: `cti-w02-lookup-api`
- Branch: `feat/w02-lookup-api-20261111`
- Base: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`
- HEAD/commit local: `78b026003c86985c7f062986088bfd1f7210a1b1`
- Commit: `feat: add read-only W02 IOC lookup API`
- Diff: 5 file, `+1183/-4`; đúng allowlist; working tree sạch.

File đổi:

1. `portal_api/app.py`: route `GET /api/ioc`, auth JWT, role server-side, exact query/error/header.
2. `portal_api/schemas.py`: DTO W02 strict/exact và invariant ba state.
3. `portal_api/ioc_lookup.py`: immutable facts/port/service, normalize/allowlist, TLP filter/postcheck, score visible-only.
4. `portal_api/tests/test_w02_ioc_api.py`: 44 test W02 in-process.
5. `docs/PROGRESS.md`: ghi trạng thái và giới hạn.

## Hành vi đã kiểm

- Thứ tự `auth → role → query → normalize/private IP → allowlist → lookup/TLP → score`.
- Role chỉ lấy từ `roles_by_subject` sau JWT; không tin role/email/header/query client.
- IT chỉ thấy CLEAR/GREEN; analyst/admin và multi-role dùng quyền cao nhất.
- Record ngoài quyền không khác record vắng; nested fact bị ẩn không đổi score/reason/count/related/assets/TLP output.
- Nguồn trùng `source_id` giống hệt được dedupe; mâu thuẫn fail closed 503.
- DTO/schema/timestamp/TLP sai fail closed; 8 loại IOC và 5 marking TLP được phủ.
- Found/allowlisted/not_found đúng fixture; output TLP không hạ `record_tlp` và là marking hạn chế nhất của facts visible.
- W05 giữ nguyên qua toàn bộ `portal_api/tests`.

## Lệnh và kết quả tươi trên HEAD

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `.\.venv\Scripts\python.exe -B -m pytest portal_api/tests/test_w02_ioc_api.py -o addopts='' -q` | 0 | 44 passed |
| `.\.venv\Scripts\python.exe -B -m pytest portal_api/tests -o addopts='' -q` | 0 | 178 passed |
| `.\.venv\Scripts\ruff.exe check portal_api` | 0 | All checks passed |
| `.\.venv\Scripts\ruff.exe format --check portal_api` | 0 | 11 files already formatted |
| `git diff --check HEAD^ HEAD` | 0 | không lỗi |
| TestClient demo IT/analyst/multi-role/hidden mutation | 0 | invariant true; no-store/Vary đúng |

TDD RED đã quan sát trước code: thiếu `portal_api.ioc_lookup`; `create_app` chưa có `lookup_port`; và hidden nested lỗi từng làm lộ qua 503. Cả ba đã GREEN trong bộ 44 test.

## Review và quyết định

- Tự review toàn diff theo contract và năm failure mode; không có finding Critical/Important/Minor.
- Không gọi reviewer khác vì brief yêu cầu một Sol medium trực tiếp, không giao worker.
- Literal score analyst là 69 cho fixture hai nguồn + asset, theo công thức core; 46 trong test nháp ban đầu là tính nhầm và đã sửa trước gate cuối.

## Chưa xác minh

**UNVERIFIED:** adapter/query OpenCTI, Cloudflare/JWKS/JWT thật, listener/HTTPS, frontend↔backend runtime, browser, latency/quy mô, lab, production. Không có push/PR/merge/deploy hay mạng thật.

## Bằng chứng

- `w02-lookup-api-evidence/00-environment.txt`
- `w02-lookup-api-evidence/01-tdd-red.txt`
- `w02-lookup-api-evidence/10-final-checks.txt`
- `w02-lookup-api-evidence/11-demo.json`
- `w02-lookup-api-evidence/demo.py`
- `w02-lookup-api-evidence/implementation-plan.md`
- `w02-lookup-api-evidence/manifest.sha256`
