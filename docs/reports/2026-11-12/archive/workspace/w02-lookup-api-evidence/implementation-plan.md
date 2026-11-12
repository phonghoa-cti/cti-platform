# W02 Lookup API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm GET `/api/ioc` chỉ đọc, xác thực JWT/role phía server và không làm lộ dữ liệu ngoài quyền TLP.

**Architecture:** Giữ `app.py` là biên HTTP/auth; `schemas.py` chứa DTO exact; `ioc_lookup.py` chứa immutable fact records, port và service hậu kiểm/filter/score. Adapter thật không có trong lát cắt này; mặc định `lookup_port=None` fail closed 503.

**Tech Stack:** Python 3.12.13, FastAPI, Pydantic v2, PyJWT, phonghoa_core, pytest/TestClient.

**Spec:** `..\PHONG-HOA-W02-API-CONTRACT-BRIEF.md`

## Global Constraints

- Base `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; branch `feat/w02-lookup-api-20261111`.
- Chỉ sửa `portal_api/app.py`, `portal_api/schemas.py`, tạo `portal_api/ioc_lookup.py`, `portal_api/tests/test_w02_ioc_api.py`, và cập nhật W02 trong `docs/PROGRESS.md`.
- Thứ tự: auth → role → query → normalize/private IP → allowlist → lookup/filter TLP → score → serialize.
- Không listener, browser, network/OpenCTI/JWKS thật, secret, dependency mới, push/PR/merge/deploy.
- Mọi response W02 có `Cache-Control: no-store`, `Vary: Cf-Access-Jwt-Assertion`.

## Review Focus

- Record TLP ngoài quyền phải indistinguishable với vắng record.
- Fact ẩn không được đổi score/reason/count/related/assets/TLP output.
- Duplicate source ID giống hệt được dedupe; mâu thuẫn fail closed 503.
- DTO malformed, unknown TLP, timestamp naïve/non-UTC, invalid bounds fail closed 503.
- Query không hợp lệ không được xử lý trước auth/role.

---

### Task 1: W02 DTO và domain service

**Files:**
- Modify: `portal_api/schemas.py`
- Create: `portal_api/ioc_lookup.py`
- Test: `portal_api/tests/test_w02_ioc_api.py`

**Interfaces:**
- Produces: strict success DTO models; `SourceFact`, `RelatedFact`, `AssetFact`, `LookupRecord`, `IocLookupPort`, `LookupService.lookup(raw, roles)`.

- [ ] Viết test failing cho ba fixture, TLP filtering/invariance, dedupe/conflict và malformed records.
- [ ] Chạy test để xác nhận RED do API/domain chưa có.
- [ ] Viết DTO và service nhỏ nhất để GREEN.
- [ ] Chạy test task và refactor khi vẫn xanh.

### Task 2: HTTP route, auth/role và error contract

**Files:**
- Modify: `portal_api/app.py`
- Test: `portal_api/tests/test_w02_ioc_api.py`

**Interfaces:**
- Consumes: `LookupService.lookup(raw, roles)` và W05 `AccessJwtVerifier`/`Principal`.
- Produces: GET `/api/ioc?value=...`, exact errors, no-store/Vary.

- [ ] Viết test failing cho auth/role/order/query/private-IP/None-port/exception/header.
- [ ] Chạy test để xác nhận RED do route chưa có.
- [ ] Thêm optional `lookup_port` và route mà không đổi W05.
- [ ] Chạy W02 test và toàn `portal_api/tests`.

### Task 3: Tài liệu, demo và gate cuối

**Files:**
- Modify: `docs/PROGRESS.md`
- Evidence outside repo: `w02-lookup-api-evidence/`, `PHONG-HOA-W02-LOOKUP-API-RESULT.md`

- [ ] Cập nhật tiến độ với giới hạn offline/in-process.
- [ ] Chạy pytest W02, pytest portal API, Ruff check/format, diff-check và allowlist check.
- [ ] Chạy TestClient demo IT/analyst/multi-role/hidden mutation và lưu raw output/exit.
- [ ] Review diff, commit local, xác nhận tree sạch, ghi manifest SHA256.
