# W03 filter fix evidence

- Base: `f650f04de8f08238e13e2630f974e9f30ef838b5`
- HEAD: `7ff62711f4304aefda9a6fc640d05039fd0cd9af`
- Commit: `fix(portal): align unchecked KEV filter`
- Diff: 4 files, +39/-1.
- RED: exit 1, 1 fail + 52 pass / 53; `kev=false` còn xuất hiện trong URL.
- GREEN focused: exit 0, 53/53.
- Probe Leader nguyên bản: exit 0, 3/3 với config alias sang frontend tree.
- Typecheck/lint: exit 0/0.
- Probe SHA-256 không đổi: `1756efa94d8e2fa77f8108f1c6f309e20a584aaa32cb9c130663b38fd085a797`.
- Browser/backend/gateway/feed/OpenCTI/lab/production: UNVERIFIED.

## Final files

```text
docs/PROGRESS.md
portal/web/data/cves-http.ts
portal/web/tests/cve-app.test.tsx
portal/web/tests/cves-http.test.ts
```

## Probe command

Chạy từ `ROOT/leader-w03-integration-review-20261112`:

```powershell
& .\node_modules\.bin\vitest.cmd run --config '..\w03-filter-fix-evidence\vitest.frontend.config.ts'
```

Config evidence alias `@` sang `ROOT/cti-w03-read-frontend/portal/web`; không dùng config gốc trỏ integration tree và không sửa probe.
