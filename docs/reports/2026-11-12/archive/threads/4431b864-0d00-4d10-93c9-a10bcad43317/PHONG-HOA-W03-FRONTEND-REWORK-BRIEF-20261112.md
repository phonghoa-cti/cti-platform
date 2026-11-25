# W03-READ-FRONTEND — rework F1–F3

ROOT = $WORKSPACE
OUT = $THREADS\4431b864-0d00-4d10-93c9-a10bcad43317
Source writer duy nhất: CTI Frontend, Sol medium trực tiếp, không worker con.
Tree ROOT\cti-w03-read-frontend, branch feat/w03-read-frontend-20261112.
Candidate cần sửa: 5c968c74cc53c5798bcf8adaf8695dacfd86ffd4.
Giữ nguyên các thay đổi hiện có nếu HEAD/status khác; báo khác biệt trước khi sửa, không reset/cherry-pick Backend.

Đọc ROOT\PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md, OUT\PHONG-HOA-W03-FRONTEND-QA-RESULT.md và OUT\leader-w03-qa-review-20261112\ACCEPTANCE.md. Tái dùng nghiên cứu/hợp đồng r1, không nghiên cứu lại hoặc redesign.
Leader đã tái hiện 3/3 probe thất bại, exit1, SHA sạch; artifact OUT\leader-w03-qa-review-20261112\probe-results.json. Các probe gốc OUT\w03-frontend-qa-evidence\w03-qa-probe.test.tsx phải giữ nguyên.

## Sửa tối thiểu và kiểm bắt buộc
1. F1: notice phải là copy r1 cố định: “Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.” So literal trong parser hoặc dùng copy cục bộ không render notice wire tùy ý; cách chọn phải làm cả detail/summary đúng hợp đồng và có regression. Không tự tuyên bố đã sửa lỗi vượt quyền server.
2. F2: parser từ chối cveId trùng trong cùng response ở cả view, matches technologyId phải duy nhất và tăng nghiêm ngặt. Tách test duplicate CVE, duplicate match và ID giảm, mỗi test payload còn lại hợp lệ. Không chỉ làm probe ghép xanh. Không sort/dedupe im lặng dữ liệu sai.
3. F3: dữ liệu response/options/detail phải có chủ sở hữu context/provider rõ. Chỉ gọi Technology sau response detail của context hiện tại; đổi provider không được dùng view detail cũ. Kiểm detail→pending summary (0 calls), summary→detail (gọi hợp lệ), detail→detail, provider A/B và Technology A/B đổi riêng/cùng lúc; callback cũ không set data/error/loading/options/notice và không bỏ kẹt loading. Đổi filter/409 không hồi sinh chuỗi trang/detail cũ. Giữ cách triển khai nhỏ nhất có ích.
4. RED→GREEN regressions mới trước sửa; chạy nguyên ba probe QA ngoài source và focused W03; typecheck/lint. Build chỉ khi code thay đổi hoặc typecheck chưa chứng minh cần kiểm route/framework; không cần lặp full344 nếu không có ảnh hưởng mới ngoài W03. Không sửa tests W04 hoặc nới contract cho tests xanh.

Allowed: portal/web/data/cves*.ts, portal/web/components/cve*.tsx, portal/web/tests/*cve*, docs/PROGRESS.md một đoạn; cần ngoài phạm vi thì báo cụ thể. Không sửa QA probes gốc, deps, Backend/gateway, ledger, hợp đồng, browser, live feeds, secret/lab, push/PR/merge/deploy.
Báo cáo mới: OUT\PHONG-HOA-W03-FRONTEND-REWORK-RESULT.md; logs/hash trong OUT\w03-frontend-rework-evidence. Giữ evidence cũ.
Done: SHA commit mới/tree sạch, diff so candidate, từng finding đóng bằng kiểm riêng và nguyên 3 QA probes đạt; command/exit/count, module/source path, giới hạn browser/tích hợp vẫn UNVERIFIED. Hai nguồn chưa accepted thì chưa tích hợp.
