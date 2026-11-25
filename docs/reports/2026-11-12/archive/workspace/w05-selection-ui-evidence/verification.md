# W05 Selection UI verification evidence

- Base: `812dae1ffbdc8e8866342cc075d925fdc99ef12d`
- Head: `2276f49399ae2cd5ae40963622a3d9b70bcf1d3c`
- Branch: `feat/w05-selection-ui-20261111`
- Tree status: clean
- Diff: 12 files, 812 insertions, 486 deletions

Fresh final commands:

```text
npm test
Test Files  7 passed (7)
Tests       73 passed (73)
Duration    5.80s
exit        0

npm run typecheck
exit        0

npm run lint
0 errors, 0 warnings
exit        0

npm run build
Compiled successfully
Routes: /, /duyet, /duyet/mau (static)
exit        0

git diff --check
exit        0

git commit -m "feat(portal): add saved IOC selection workflow"
exit        0
```

TDD observations:

```text
RED selection-api-client.test.ts: 13 failed, exit 1
GREEN selection-api-client.test.ts: 13 passed, exit 0
RED selection-review-app.test.tsx: 6 failed, exit 1
GREEN selection-review-app.test.tsx: 6 passed, exit 0
Boundary selection-review-app.test.tsx: 7 passed, exit 0
```

No browser/listener/gateway/lab run was performed by this assignment. These remain UNVERIFIED.
