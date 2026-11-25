# W04 Frontend — sửa ba finding trước tích hợp

CTI Frontend, một Sol medium trực tiếp, không giao người khác. Giữ thread `957c7dec-fe60-4717-acf1-8531e349e4aa`, tree `cti-w04-assets-frontend`, branch hiện tại. Base `be131133da7b63a3054da032ed1ab8a85af48bc6`. Không reset/recreate hoặc chạm tree Backend/Engineer.

Root: `$WORKSPACE`.

Leader xác nhận HEAD/tree sạch, đọc component/adapter/contract. Probe ngoài sản phẩm tại `leader-w04-frontend-review-20261111/leader-regressions.test.tsx`, config cùng thư mục: **5 FAIL / 1 PASS / 6 test**, exit 1. `leader-regressions-red.txt/xml` là RED sản phẩm; `runner-setup-error.*` chỉ là lỗi đường dẫn lần đầu, không tính finding. `verification.json` xác nhận không sửa tree. Backend `90b26287eccc416fd7e7e736b0ad37632e0c34b1` đã được nghiệm thu; không chạy lại/sửa Backend.

## F1 — created_by sai bound

`parseAssetItem` giới hạn `created_by` 253, nhưng `portal_api/schemas.py:AssetView` và actor đã nghiệm thu cho phép 1..512. Probe 254 và 512 bị throw; 513 reject đúng. Hệ quả: GET hợp lệ thành unavailable, POST đã commit có response hợp lệ lại thành unknown.

Sửa bound riêng 512, giữ các bound value/note/tên asset khác. Test 253/254/512 pass, 513 reject; thêm kiểm adapter list/create bằng response thật từ schema hoặc fixture tương ứng, không chỉ unit parser. Không nới trường khác.

## F2 — lỗi gateway khi ghi bị coi là lỗi đã biết

Gateway hiện có thể trả 503 `{error:{code:'upstream_unavailable',message:...}}` sau khi upstream đã nhận/ghi request nhưng response không về. Adapter hiện parse envelope rồi `errorKind` fallback unavailable; probe POST expected unknown-mutation thực tế unavailable. Không có bằng chứng tự replay, lỗi là phân loại kết quả khiến form vẫn là lỗi lưu thông thường.

Chỉ các cặp status/code được hợp đồng xác nhận là reject trước commit/rollback mới là lỗi mutation đã biết (ví dụ auth, forbidden, invalid_asset, asset_conflict/asset_exists, asset_not_found, 503 assets_unavailable). Với gateway/upstream hoặc status/code không xác nhận được kết quả POST/PUT/DELETE, giữ unknown-mutation, không replay và hướng GET để đối soát. GET vẫn unavailable như cũ. Không dựa vào message hay echo message server. Kiểm POST/PUT/DELETE upstream_unavailable và unknown envelope; giữ known errors, request count và GET-only recovery.

## F3 — refresh cũ vẫn ghi notice sau đổi context

Mutation thành công, gọi `await load(type,true)`; trong lúc GET refresh chờ, người dùng chuyển từ domain sang IP và tải IP thành công. GET domain cũ reject; `load` trả false do request ownership, nhưng submit/remove sau await vẫn set committed-refresh notice lên tab IP. Cả create và delete tái hiện FAIL; bảng IP không bị đổi, thông báo cũ vẫn xuất hiện.

Kiểm context ownership sau await refresh và trước mọi state write tương ứng. Chặn cả success/error/finally cũ; giữ loading/saving context mới, không tăng request/mutation. Regression cho create/update/delete theo cùng race và giữ recovery trong context hiện tại 503→200. Không sửa bằng delay hoặc vô hiệu hóa kiểm cũ.

## Phạm vi và nghiệm thu

- Chỉ `portal/web/data/assets-http.ts`, `components/assets-app.tsx`, test assets tương ứng; PROGRESS/report khi cần. Giữ UI/thiết kế/API contract/W02/fixtures/package-lock.
- Thêm regression RED→GREEN tại source; chạy focused assets UI/HTTP và typecheck/lint/build đúng delta. Không lặp full 222 test nếu không thay phần ngoài assets. Lưu exit/count chuẩn và log.
- Probe Leader giữ nguyên. Có thể chạy từ root bằng `node cti-w04-assets-frontend/portal/web/node_modules/vitest/vitest.mjs run --config leader-w04-frontend-review-20261111/vitest.config.mjs --reporter=verbose`; ghi stdout/XML mới dưới `w04-assets-frontend-evidence/rework-leader/` trong tree, không ghi đè RED/verification Leader. Phải 6/6 PASS.
- Commit cục bộ/tree sạch, trả base/head/diff/bằng chứng; bổ sung báo cáo hiện hữu `cti-w04-assets-frontend/PHONG-HOA-W04-ASSETS-FRONTEND-RESULT.md` (ghi rõ đường dẫn thực tế). Không push/merge/deploy/browser/lab/secret.
- Engineer được giao riêng phần gateway/runner từ Backend đã đạt; không lấy/cherry-pick mã đó hoặc giao tiếp bot khác. Leader nối sau khi hai đầu vào được nghiệm thu.
