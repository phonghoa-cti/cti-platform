# W03 frontend — bằng chứng lệnh

- Worktree: `cti-w03-read-frontend`
- Branch: `feat/w03-read-frontend-20261112`
- Base: `273196e2d23b36172d57cc61b289522786d61b2a`
- HEAD/commit: `5c968c74cc53c5798bcf8adaf8695dacfd86ffd4`

| Lệnh (cwd `portal/web`) | Exit | Kết quả |
|---|---:|---|
| `npm test -- --run tests/cves-http.test.ts tests/cve-app.test.tsx` (RED đầu) | 1 | 2 suite fail vì `@/data/cves-http` và `@/components/cve-app` chưa tồn tại |
| `npm test -- --run tests/cves-http.test.ts tests/cve-app.test.tsx` | 0 | 2 file, 39 test đạt |
| `npm test -- --run tests/technologies-http.test.ts tests/technologies.test.ts tests/technology-panel.test.tsx` | 0 | 3 file, 66 test W04 đạt |
| `npm test` (chạy đồng thời với build/lint/typecheck) | 1 | 342/343 đạt; một test W04 timeout 5 giây do tranh tài nguyên, không có assertion fail |
| `npm test` (chạy riêng ngay sau đó) | 0 | 17 file, 343 test đạt |
| `npm test` (sau regression priority/focus cuối) | 0 | 17 file, 344 test đạt |
| `npm run typecheck` | 0 | Không có lỗi TypeScript |
| `npm run lint` | 0 | Không có lỗi/cảnh báo ESLint |
| `npm run build` | 0 | Next.js build thành công, 11/11 static pages; có `/lo-hong` và `/lo-hong/mau` |
| `git diff --check 273196e2...HEAD` | 0 | Không có whitespace error |
| `git status --short --branch` | 0 | Branch sạch, không có dòng file thay đổi |

Không chạy browser theo brief. Không chạy API/backend/gateway/feed/OpenCTI/lab/production.
