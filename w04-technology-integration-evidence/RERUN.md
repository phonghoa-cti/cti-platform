# Lệnh tái chạy W04 Technology Integration

CWD repo: `cti-w04-technology-integration`.

```powershell
$py = '..\cti-x01-ingest-browser-prep\.venv\Scripts\python.exe'
& $py -X utf8 -B -m tools.local_integration.tests.run_w04_technology_matrix --output .\w04-technology-integration-evidence\http-assertions.json --evidence-dir .\w04-technology-integration-evidence\db
& $py -X utf8 -B -m pytest tools/local_integration/tests/test_runner.py tools/local_integration/tests/test_w04_browser_helper.py -o addopts='' -q
node tools/local_integration/tests/test_gateway.mjs
Set-Location portal\web
node node_modules/vitest/vitest.mjs run tests/assets-http-client.test.tsx tests/assets-http.test.ts tests/assets-app.test.tsx tests/technologies.test.ts tests/technologies-http.test.ts tests/technology-panel.test.tsx --reporter=dot
node node_modules/typescript/bin/tsc --noEmit
node node_modules/eslint/bin/eslint.js . --max-warnings=0
node node_modules/next/dist/bin/next build
```

`node_modules` dùng bản dependency vật lý sao chép nguyên trạng từ source Frontend đã nghiệm thu; không cài hay
nâng cấp package. Browser helper và giới hạn của nó nằm trong `tools/local_integration/README.md`.
