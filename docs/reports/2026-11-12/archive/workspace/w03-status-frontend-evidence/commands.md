# Lệnh kiểm chứng

## RED quan sát được

- `npm test -- --run tests/cve-status.test.ts` → exit 1: chưa có module status.
- `npm test -- --run tests/cve-status-panel.test.tsx` → exit 1: chưa có component panel.
- Focused invalid mutation bound → exit 1: trước fix trả `unknown-outcome`, chưa chặn trước fetch.
- Focused pending/recovery → exit 1: trước fix pending không sống qua reopen; PUT 503 và 413/415 bị phân loại sai; conflict để pending.

## GREEN cuối

```text
npm test -- --run tests/cve-status.test.ts tests/cve-status-panel.test.tsx tests/cve-app.test.tsx tests/cves-http.test.ts tests/technologies-http.test.ts tests/technology-panel.test.tsx
exit 0
Test Files  6 passed (6)
Tests       143 passed (143)
```

```text
npm run typecheck
exit 0

npm run lint
exit 0

npm run build
exit 0
Compiled successfully
Generating static pages 11/11
```

```text
git diff --check 7ff6eb3af21d8de65836bfbf707396ae5690de0b..HEAD
exit 0

allowlist check
exit 0
CHANGED=15 OUTSIDE_ALLOWLIST=0

git status --porcelain=v1
exit 0
<no output>
```

Một lệnh `rg` tự rà soát đầu tiên sai cú pháp regex (exit 2); lệnh sửa đúng ngay sau đó exit 0 và xác nhận HTTP status chỉ có GET/PUT đã định nghĩa, không có header Authorization/JWT/Origin tự chèn.
