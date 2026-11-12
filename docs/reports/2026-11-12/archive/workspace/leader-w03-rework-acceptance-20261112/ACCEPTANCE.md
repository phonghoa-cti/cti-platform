# W03 — nghiệm thu hai bản sửa, 12/11/2026

**PASS cục bộ cho R1 và R2 riêng; toàn tích hợp vẫn chờ ghép R1 và kiểm browser.**

## R1 — Frontend 7ff62711f4304aefda9a6fc640d05039fd0cd9af
Base f650f04de8f08238e13e2630f974e9f30ef838b5; đọc diff4file +39/-1. Runtime chỉ một dòng: unchecked bỏ query kev, checked vẫn kev=true. Không đổi Backend contract, sample hoặc label.
Leader chạy mới53focused tests, exit0; nguyên3probe kiểm parity, exit0. SHA probe1756efa94d8e2fa77f8108f1c6f309e20a584aaa32cb9c130663b38fd085a797 giữ nguyên.
Config w03-filter-fix-evidence/vitest.frontend.config.ts alias đúng Frontend. Cwd chạy probe là leader-w03-integration-review-20261112; thử từ portal/web bị lỗi module /@fs trước test, không phải lỗi sản phẩm.
Green log filter-probe-green.log; focused53 stdout lưu frontend-focused.log. Worker typecheck/lint được tái dùng, không chạy lặp. Tree sạch.

## R2 — Engineer 9579d1657145769718fde96c4918fe5cd4d80f63
Base93962d9; diff14file +189/-17 chỉ tests/fixtures/matrix/docs. Product frontend/backend không đổi. Đã đọc fixture preflight ngoài catch HTTP, default portable và override, near-cap qua provider, POST/DELETE matches và SQL assertions.
Leader chạy mới:
- Default không W03_WIRE_DIR:10/10 PASS exit0 (wire-default-green.log).
- Hai fixture lỗi: thiếu summary và detail JSON hỏng đều exit1 **0 test chạy**, thông báo preflight đúng; missing-preflight.log và invalid-preflight.log. Đây là kết quả lỗi mong đợi, không tính là tests PASS.
- Ma trận120/120 HTTP+SQL PASS exit0; http-matrix.json/http-run.log và capture mới dưới http/.
- Wire override tới capture mới của Leader:10/10 PASS exit0; wire-fresh-override.log.
42artifact gốc và14artifact R2 đều khớp manifest; hash9b17ed1f... vàa489de03... đầy đủ trong báo cáo gốc. Tree sạch.

Lệnh matrix cwd cti-w03-read-integration:
`..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w03_matrix --output ..\leader-w03-rework-acceptance-20261112\http-matrix.json --evidence-dir ..\leader-w03-rework-acceptance-20261112\http`.
Frontend cwd portal/web: vitest.cmd run tests/cves-http.test.ts tests/cve-app.test.tsx; wire command vitest.cmd run tests/cves-wire-integration.test.ts.

## Cổng còn lại
Engineer giữ cùng tree/thread, cherry-pick7ff62711 rồi kiểm browser3KEV→16tất cả→3KEV; phân trang không mất3KEV và không lặp CVE. Reuse summary/SQL/recovery đã đối chiếu, không làm lại toàn browser/historical suites.
Chưa nghiệm thu toàn W03-R, mobile360, nguồn thật/OpenCTI/Cloudflare/lab/production. Dự án active, hai automation giữ bật.
