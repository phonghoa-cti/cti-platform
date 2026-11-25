# W04 Backend — sửa F1–F4 đã được Leader tái hiện

Task giữ `W04-ASSETS-IMPLEMENT`. Owner CTI Backend, Sol medium trực tiếp; cùng thread `12614171-9e62-4c0d-a75b-b7f852c15b02`, cùng tree `cti-w04-assets-local`, branch `feat/w04-assets-local-20261111`. Bắt đầu tại `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`, không reset/xóa/recreate tree, không giao người khác.

Root: `$WORKSPACE`.

## Bằng chứng và quyết định

Đọc `PHONG-HOA-W04-BACKEND-QA-RESULT.md` cùng script `w04-assets-qa-evidence/targeted_probes.py`. Leader đã đối chiếu code với cả4 findings, xác minh manifest23/23 và chạy nguyên script vào evidence mới `leader-w04-qa-confirm-20261111/`, exit0. Kết quả `probe-results.json` tái hiện đúng4 lỗi;3 probe concurrency/Origin-private-IP/overflow đạt. Exit0 của probe là script chạy xong, không phải sản phẩm PASS. Target vẫn sạch/đúng SHA. QA đã xong, không còn writer khác trong target; Frontend đang làm tree riêng.

QA report được chấp nhận là đầu ra kiểm thử FAIL; Backend chưa được nghiệm thu. Không thay schema/fixture đã gửi Frontend nếu không thật sự cần; bốn sửa này nhằm đạt hợp đồng đã chốt, không tạo phiên bản hợp đồng khác.

## Sửa cụ thể và tiêu chí

### F1 HIGH — domain hỏng trong snapshot làm allowlist quá rộng

Row synthetic `type=domain, canonical_value=com` khiến GET IOC `attacker.com` trả200 allowlisted/score0/assets[com]. Snapshot hiện dùng row không kiểm invariant.

Phải kiểm toàn bộ dữ liệu sử dụng từ DB (type, canonical value, ID/bounds và các trường cần cho response) theo hợp đồng. Dữ liệu lưu phải đúng canonical, không tự chuẩn hóa/loại row hỏng rồi trả partial. Row hỏng bất kỳ trong snapshot làm cả lookup trả503 `lookup_unavailable`, adapter không bị gọi. Đường list/đọc mutation cần fail-closed tương ứng thay vì trả row hỏng như dữ liệu hợp lệ. Thêm test single-label, invalid type/CIDR, noncanonical/malformed và bound; domain/IP hợp lệ cùng default rules vẫn giữ hành vi.

### F2 HIGH — đã commit nhưng API trả422

Subject đã xác minh dài513 có role hợp lệ POST domain: API trả422 `invalid_asset`, nhưng asset và audit đều đã commit (mỗi bảng1 row). Ràng buộc actor trước transaction theo schema1..512. Kiểm cả create/update/delete; reject actor sai không tạo/sửa/xóa/audit gì, không echo subject.

Quan trọng hơn: đảm bảo output DTO chắc chắn hợp lệ **trước commit**, không chỉ vá subject cụ thể. Xem bound ID/version, before-row được lưu và version tăng vượt2^53-1; lỗi input/DTO/storage phải rollback hoặc bị chặn trước mutation, không để response-validation422 sau commit. Thêm test biên512/513 và output/version boundary cùng kiểm DB/audit không đổi. Giữ unknown transport outcome là vấn đề client riêng; không dùng client retry để che lỗi server này.

### F3 MEDIUM — tên asset129 bị từ chối

`_validate_asset()` còn dùng bound128 chung dù AssetName riêng cho phép253. Áp bound1..253 đúng cho AssetFact.name; giữ source/related128. Kiểm128/129/253 accepted,254 rejected với error tương ứng, malformed type/blank vẫn bị chặn. Không nới các invariant TLP/source/score.

### F4 MEDIUM — mọi integrity error bị coi là asset trùng

Synthetic trigger làm INSERT audit abort: rollback đúng0asset/0audit nhưng trả409 `asset_exists`, cần503 `assets_unavailable`. Chỉ unique active canonical của asset mới map thành asset_exists; audit/constraint/storage lỗi khác unavailable. Không map rộng mọi SQLITE_CONSTRAINT_UNIQUE nếu constraint không thuộc active asset canonical; có thể thu hẹp khối bắt lỗi quanh đúng câu INSERT/UPDATE asset và giữ lỗi audit ngoài đường duplicate. Kiểm cả create và update, đồng thời chứng minh duplicate thật vẫn409 và audit không sinh thêm.

## Phạm vi và kiểm

Allowlist cũ `PHONG-HOA-W04-IMPLEMENT-BRIEF-20261111.md` giữ nguyên; chỉ sửa tối thiểu assets.py/ioc_lookup.py/app.py/schemas.py nếu cần, test tương ứng, contract/PROGRESS khi giải thích error. Không sửa auth/settings/core/frontend; không sửa hay ghi đè evidence QA/Leader lịch sử. Nếu cần file ngoài allowlist, báo lý do cụ thể.

1. Thêm regression F1–F4 và chạy RED trên candidate trước sửa; ghi count/cause đúng, không cần lặp full baseline suite.
2. Sửa và chạy cùng regression GREEN. Chạy các test assets + W02 bị ảnh hưởng một lần trên HEAD cuối (không toàn repo). Các thay đổi chạm validator W02 nên nhóm W02 cần chạy lại lần này.
3. Chạy lại **nguyên bản** QA `targeted_probes.py` với output-dir mới dưới `w04-assets-evidence/rework-qa/`, không chỉnh probe cho xanh; kiểm actual expected7/7, không chỉ exit0. Giữ cả lần RED và GREEN, dùng UTF8, Python/module target như brief cũ. Không ghi thêm vào evidence QA/Leader gốc.
4. Ruff check/format portal_api, diff-check, commit cục bộ, tree sạch. Báo rõ base/head và delta từ bfd3272d. Không push/PR/merge/deploy/browser/lab/network/secret.

Lưu phần rework vào `PHONG-HOA-W04-ASSETS-RESULT.md`, raw dưới `w04-assets-evidence/rework-qa/`. Bảo toàn báo cáo/evidence cũ và nêu supersedes candidate FAIL. Trả kết quả tự quay về Leader; Leader kiểm targeted và quyết định có cần QA tái kiểm rủi ro còn lại trước nối Frontend.
