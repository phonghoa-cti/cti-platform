# W03-FILTER-FIX — sửa checkbox Chỉ KEV
ROOT = $WORKSPACE
Một CTI Frontend Sol medium trực tiếp; không workercon/botkhác. Cùng thread a977848b-e1c7-4934-8649-6d33a10bb5e3, tree ROOT/cti-w03-read-frontend, base f650f04de8f08238e13e2630f974e9f30ef838b5. Giữ edits cótrước, khôngreset. Engineer đang sửa tests độc lập ở integrationtree, không chạm.
Đọc ROOT/leader-w03-integration-review-20261112/REVIEW.md và hợpđồng W03-r1/AGENTS/PROGRESS đúngtree. Đây là lỗi parity có bằng chứng, tái dùng nghiên cứu, không mở kiến trúc mới.

R1: checkbox Chỉ KEV unchecked nghĩa tất cả, Sample provider đúng; HTTPprovider luôn gửi kev=false làm Backend loại KEV. Browser cho13nonKEV thay16tất cả. Probe Leader1FAIL2PASS với validContent-Type; không cần chạy lại phần B1/B2 hay F1–F3 đã đóng.
Sửa tối thiểu: createCvesHttpProvider chỉ setkev=true khi query.kev=true, false thì bỏ parameter. Giữ Backend contract GETkev=false cho APIclient riêng; không đổi samplealgorithm hoặc đổi label.
Allowed: portal/web/data/cves-http.ts, tests/cves-http.test.ts, tests/cve-app.test.tsx, docs/PROGRESS.md; cves.ts chỉ comment vềsemantics boolean nếu cần. Không Backend/gateway/deps/style/ledger/Engineer tree.
RED→GREEN test false→parameterabsent, true→true; component bỏchọn/đổifilter/paging/retry vẫn giữall; sample và HTTP semantics thống nhất. Giữ 51focused và probes cũ. Typecheck/lint; build nếu chạm componentruntime. Không full356 vì chỉadapter nhỏ.
Leader probe ROOT/leader-w03-integration-review-20261112/kev-checkbox-probe.test.ts phải giữhash; configgốc trỏ integrationtree nên **không dùng configgốc làmGREENcho treeFrontend**. Tạo config riêng trong evidence trỏsourceFrontend/giữprobe, ghi source chính xác. Có thể chạy unitregression mới thay configurationvòng nếu pathkhó, Leader sẽchạyprobe saucherry-pick.
Output ROOT/PHONG-HOA-W03-FILTER-FIX-RESULT.md và ROOT/w03-filter-fix-evidence/: SHA sạch, diff/commands/exit/count/REDGREEN. Không push/PR/merge/deploy/browser/lab/feed. Trả kết quả, Leader kiểm rồi mới chuyển commit choEngineer.
