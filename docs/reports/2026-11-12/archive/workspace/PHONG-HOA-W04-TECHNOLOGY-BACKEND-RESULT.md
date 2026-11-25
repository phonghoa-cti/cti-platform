# Kết quả W04-TECHNOLOGY-BACKEND

**PASS cục bộ/in-process.** CRUD/quyền/migration/audit/rollback theo hợp đồng đã có test mới; regression
technology/assets/W02 đạt và tree commit sạch đúng allowlist.

## Git

- Tree: `cti-w04-technology-backend`
- Branch: `feat/w04-technology-backend-20261111`
- Base: `8a767314b654d39c1ddc2995b7919c44a5b7027a`
- HEAD: `f4c19d44a33fe588046e0e974af9c18cbf8a1a12`
- Commit triển khai: `b32fbfe8bb5e72230424ab23d27f8949238dd2a9` — `feat: add local technology asset API`
- Commit rework B1: `f4c19d44a33fe588046e0e974af9c18cbf8a1a12` — `fix: enforce technology timestamp wire format`
- Diff triển khai base..HEAD: 8 file, `+1483/-0`.
- Delta rework `b32fbfe..f4c19d4`: 2 file, `+75/-4`.

Allowlist thực tế:

- `portal_api/technologies.py`
- `portal_api/app.py`
- `portal_api/schemas.py`
- `portal_api/tests/test_technologies_store.py`
- `portal_api/tests/test_technologies_api.py`
- `portal_api/tests/fixtures/technology-wire.json`
- `docs/specs/W04-technology-local-contract.md`
- `docs/PROGRESS.md`

Không sửa `assets.py`, `ioc_lookup.py`, auth/settings/core/dependency/gateway/UI/RUNS.

## Chức năng và an toàn đã kiểm

- `TechnologyStore` riêng với migration additive, transaction DDL tuần tự, marker/index/schema strict và
  rollback khi fault giữa migration.
- CRUD active + soft-delete/recreate, optimistic version, before/after audit cùng transaction.
- `vendor`/`product` chỉ trim + casefold key; `software_version` giữ chuỗi, không NFKC/range/CPE.
- Bound Unicode Cc/Cf/Cs, actor 512/513, safe integer strict, overflow, 1.000/1.001, row/key corruption.
- Phân biệt true identity duplicate với unique/trigger/audit khác; lỗi khác rollback và trả unavailable.
- Hai writer cùng expected version không lost update; failure path đóng kết nối và nhả lock.
- API opt-in `/api/assets/technologies`; IT/analyst/admin/multi-role được phép, leader-only/thiếu JWT bị chặn.
- Auth/role/Origin/body/query/DB precedence; 401/403/404/409/413/415/422/503; no-store/Vary.
- Mutation technology không mở `AssetStore`; regression assets/W02 giữ nguyên.

## RED → GREEN và kiểm cuối

- RED: exit `1`, 2 collection errors vì module/store chưa tồn tại.
- GREEN focused: exit `0`, `47/47` technology.
- Final focused + regression: exit `0`, `148/148` = technology 47 + assets 55 + W02 46.
- Ruff check exit `0`; Ruff format-check exit `0`; diff-check exit `0`.
- Interpreter/CWD và output chi tiết: `w04-technology-backend-evidence/verification.md`.

## Fixture bàn giao Frontend

- Repo: `cti-w04-technology-backend/portal_api/tests/fixtures/technology-wire.json`
- Handoff: `w04-technology-backend-evidence/technology-wire.json`
- Bao gồm created/list/duplicate/conflict/unavailable; timestamp và danh tính đều tổng hợp.
- SHA-256: `f98df16abb8f92d441b56b718f0436f8bfd1b2c10bc1919c588eda156f816cb5`.
- Hai bản đã được đối chiếu byte-identical: `True`.

## Chưa kiểm

Không tự nhận đã tích hợp UI/browser/gateway. Cloudflare/JWKS thật, lab, OpenCTI, W03 version matching và
production đều **UNVERIFIED**. Không push/PR/merge/deploy, không gọi dịch vụ ngoài hoặc đọc secret.

## Rework B1 — timestamp wire

Leader probe SHA-256 `3a022eb79f3ca1b1c08bc62ed51d09cb89217bca5629471101f0535d13cf5dcf`
được chạy nguyên bản. RED trước fix: exit `1`, 6 fail/2 pass; GET chấp nhận ba dạng timestamp trái wire và
PUT đã ghi `note=edited`, `version=2`, audit=2.

Fix khóa cú pháp `YYYY-MM-DDTHH:mm:ss[.fraction]Z` bằng regex ASCII trước khi parse giá trị lịch. Validation
áp dụng chung cho `created_at` và `updated_at`; GET/PUT/DELETE gặp row sai đều trả 503. Mutation không sửa row,
không tăng version và không thêm audit.

- Regression mới RED: 18 fail/4 pass, exit `1`.
- Regression mới GREEN: 22/22, exit `0`.
- Final: 69 focused technology + 8 probe Leader = 77/77, exit `0`.
- Probe valid: `2026-11-11T16:00:00Z` và `2026-11-11T16:00:00.123456Z` vẫn hoạt động.
- Ruff check, Ruff format-check và diff-check: exit `0`; tree sạch.
- Raw evidence: `w04-technology-backend-evidence/rework-b1-raw.log`.

Không chạy lại assets/W02 vì delta chỉ chạm `technologies.py` và test technology; không đổi app/schema/shared
code. UI/browser/gateway/integration vẫn **UNVERIFIED**.
