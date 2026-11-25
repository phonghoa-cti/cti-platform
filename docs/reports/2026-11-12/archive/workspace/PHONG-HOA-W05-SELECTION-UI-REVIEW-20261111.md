# W05 Selection UI — Leader review

Ngày 11/11/2026. **NEEDS_FIX — chưa nghiệm thu UI**, chưa giao gateway/browser.

## Bằng chứng đã kiểm

- Task `W05-SELECTION-UI-IMPLEMENT`, request `f330be29-87e2-4b2d-a28d-1429a44ec351`.
- Tree `$WORKSPACE\cti-w05-selection-ui`.
- Base `812dae1ffbdc8e8866342cc075d925fdc99ef12d`; HEAD `2276f49399ae2cd5ae40963622a3d9b70bcf1d3c`, branch `feat/w05-selection-ui-20261111`, status sạch, diff 12 file +812/-486.
- Manifest worker: **12/12 hash khớp** file thực tế. Đây chứng minh đúng nội dung, không chứng minh hành vi.
- Leader đọc code client/two components, test mới, diff tests cũ và contract core; chạy targeted hai file mới: **20 passed, 0 failures/errors, exit 0**, JUnit `w05-selection-ui-evidence/leader-targeted.xml`, log cùng tên.
- Leader probe riêng: **15 failed, 0 errors, exit 1**, JUnit `w05-selection-ui-evidence/leader-review.xml`, log cùng tên. Lỗi đều là assertion của hành vi cần bảo vệ, không phải lỗi import/setup.
- Probe `w05-selection-ui-evidence/leader-review.test.tsx`, SHA256 `10E2C8589B5935428F3E4D4DEC1AB018AD3C969BD6308E3D62EB97619150F93A`; config `leader-review.config.mjs` cùng thư mục. Chỉ thêm evidence ngoài repo, không sửa code/test repo.
- Worker báo full73/typecheck/lint/build xanh; evidence bàn giao hiện chỉ có `verification.md` tổng hợp và manifest source, không có raw log/JUnit full73. Không nâng phần tường thuật này thành bằng chứng Leader đã chạy full/build. Không cần lặp trước khi sửa vì đã có lỗi xác nhận.

## Findings bắt buộc sửa

### R1 — Cao: retry hàng đợi bỏ qua khóa dirty/POST

`portal/web/components/draft-review-app.tsx:116` và `:202`: retryQueue không kiểm `navigationLocked` hoặc `operationLock`, nút retry luôn enabled. Tải thêm thất bại → sửa checkbox hoặc bắt đầu save → click Thử lại làm reset detail/selection/phase và gọi lại list. Hai probe thấy **list gọi 3 thay vì 2 lần**. Khi POST đang chờ, reset còn cho chọn draft khác; response/catch/finally của thao tác cũ có thể tác động trạng thái mới.

Sửa cả handler và disabled UI theo cùng ràng buộc navigation. Giữ khóa đồng bộ trước await; mọi response queue/load-more/detail/save/decision/recovery phải gắn đúng generation/ID và bỏ qua response lỗi/success cũ sau đổi draft/unmount. Tránh thông báo/thành công của A làm thay B. Thêm regression dirty, POST đang chờ và deferred response sau chuyển ngữ cảnh hợp lệ.

### R2 — Cao: refresh/recovery làm lùi dữ liệu đã ghi

`draft-review-app.tsx:138-142`, `:178`, `:186-194`: refresh chỉ so selection_version; recovery không so version nào. (a) Save empty v1 thành công → refresh network error → retry GET trả v0: UI tick lại IOC cũ, mở khóa. (b) Approve review v1/selection v0 thành công → GET pending review v0/selection v0 vẫn được nhận: checkbox mở lại, trạng thái hiển thị Chờ duyệt dù có xác nhận approve. Hai probe tái hiện trực tiếp.

Giữ mức version và snapshot đã xác nhận cho cả automatic refresh và manual recovery. So **review version + selection version + status/snapshot liên quan**, không chỉ selection version. Với decision đã xác nhận, không chấp nhận pending/lùi quyết định; với cùng version, không chấp nhận indices/hash khác. Không apply dữ liệu stale rồi mới báo lỗi. Giữ success/snapshot và mutation lock, chỉ cung cấp GET retry. Snapshot mới hơn hợp lệ do writer khác vẫn có thể hiển thị theo contract; không khẳng định đó là tác động của mình. Bổ sung test cả save và decision, automatic/manual refresh, và không tăng số POST.

### R3 — Vừa: draft 404 bị kẹt không quay về hàng đợi

`draft-review-app.tsx:160`, `:182`, `:186-194`: 404 đưa vào reload-required và khóa navigation; nút Bỏ thay đổi cục bộ và tải lại trạng thái lại chờ `Promise.all(detail của draft đã mất, list)`. Detail luôn 404 nên list mới không được áp dụng, draft khác luôn disabled. Probe có draft 2 còn trong queue nhưng không chọn được sau thao tác bỏ thay đổi.

Tạo lối thoát thực sự cho 404: sau hành động bỏ thay đổi rõ ràng, tải hàng đợi và cho chọn draft còn lại/hiện queue rỗng mà không phụ thuộc detail của ID đã mất thành công. Không dùng đường này để tự bỏ dirty ở lỗi khác. Mọi 404 vẫn giữ thông báo an toàn, không fallback sample.

### R4 — Cao: nhận detail của ID khác yêu cầu

`portal/web/data/api-client.ts:202` chỉ parse shape, không so id với URL; `draft-review-app.tsx:106-107` so selectedId của request nhưng không so `result.id`. Probe request detail(1) trả payload id2 được client chấp nhận; injected API cũng làm UI hiển thị second.txt dưới hàng đợi đang chọn draft1. Các nút mutation sau đó lấy detail.id, nên người dùng có thể thao tác bản khác với dòng đang chọn.

Client detail phải bắt ID request cố định và từ chối payload ID khác. Component phải bảo vệ association ở mọi đường áp detail, bao gồm injected API, initial load, refresh/recovery; không mở mutation trên mismatch. Không tự chuyển selectedId theo response sai. Hai lớp đều có regression.

### R5 — Vừa: parser legacy mất validation đã có

`portal/web/data/api-client.ts:218-229`: rewrite parser cũ làm mất kiểm created_at, status, language, TLP, item_count, review_status, duplicate IDs và empty actor/time của decision. Tám probe cho thấy dữ liệu sai trước đây bị từ chối nay được nhận. Đây trái yêu cầu giữ legacy strict, dù API mode hiện gọi v1.

Khôi phục đầy đủ validation legacy từ base, tái sử dụng helper nếu giữ nguyên hành vi; không xóa export/test hoặc làm parser nhận v1 để né lỗi. Giữ v1 riêng, không nới contract. Chạy cả legacy parser và v1 regression.

## Gói rework CTI Frontend — R1–R5

- Tiếp tục đúng tree/branch tại HEAD `2276f49399ae2cd5ae40963622a3d9b70bcf1d3c`, Sol medium, không agent/bot con; không reset/ghi đè tree khác.
- Scope chỉ file UI/client/tests/messages/docs cần cho năm finding, theo plan trước. Không backend/gateway/dependency/lock/config/refactor ngoài phạm vi, không browser/listener/push/PR/merge/deploy.
- **Không sửa probe/config/log/JUnit/plan/review của Leader.** Dùng probe hiện có làm RED; thêm test regression trong repo rồi sửa GREEN. Chỉ báo đã khắc phục khi probe nguyên trạng đạt, có giải thích nếu test phải được Leader xem lại.
- Lệnh probe từ root: `node .\cti-w05-selection-ui\portal\web\node_modules\vitest\vitest.mjs run --config w05-selection-ui-evidence/leader-review.config.mjs`. Ghi output mới vào thư mục rework riêng, không đè RED Leader.
- Sau targeted/probe xanh: full Vitest một lần, typecheck, lint, build, diff-check vì có thay đổi hành vi UI/client. Lưu raw stdout/stderr, fresh exit và JUnit/JSON reporter có count; không chỉ viết tóm tắt thủ công. Không lặp suite khi không có thêm thay đổi/lỗi.
- Bổ sung vào report chính ma trận acceptance: PASS cần trỏ test/bằng chứng cụ thể; phần chưa kiểm ghi UNVERIFIED. Không suy rộng 20 test xanh thành đã phủ hết matrix. Kết quả 404, stale refresh, association, queue retry và compatibility cần có regression riêng.
- Output chỉ cập nhật `PHONG-HOA-W05-SELECTION-UI-RESULT.md` và thêm `w05-selection-ui-evidence/rework-r1-r5/`; manifest mới trong đó, giữ manifest/bằng chứng trước. Commit cục bộ sau checks, báo HEAD/diff/status/hash probe không đổi.

## Trạng thái điều phối

Lượt này đã kiểm các cuộc mở: chỉ Leader hiện tại đang xử lý Phong Hỏa; Frontend đã trả kết quả. Không nghiệm thu lại các task accepted. Automation tiếp tục mỗi 30 phút vẫn enabled=true lúc 04:54 giờ Việt Nam; dự án active, chưa đạt điều kiện tạm dừng.

Chưa nghiệm thu UI selection; gateway/browser v1, Cloudflare/JWKS thật, lab, OpenCTI và production vẫn UNVERIFIED. Gửi lại đúng assignment/thread để sửa R1–R5, nhận kết quả tự động, không hỏi trạng thái liên tục.
