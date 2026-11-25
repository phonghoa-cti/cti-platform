# W04 — hợp đồng công nghệ cục bộ

## Phạm vi

Lát cắt này bổ sung CRUD công nghệ qua API in-process. `TechnologyStore` sở hữu ba đối tượng SQLite
`technology_assets`, `technology_asset_audit`, `w04_technology_migrations` và unique index riêng. Store chỉ
hoạt động khi được inject vào `create_app`; request không tự tạo hoặc migrate database.

Không thay `AssetStore`, `AssetMatcher`, allowlist, W02, dependency, gateway, UI, OpenCTI hoặc W03. Dữ liệu công
nghệ mới chỉ là hồ sơ đầu vào cho lát cắt lỗ hổng sau này, không tự kết luận phiên bản bị ảnh hưởng.

## Wire và API

Response technology có đúng các trường `id`, `vendor`, `product`, `software_version`, `note`, `created_by`,
`created_at`, `updated_at`, `version`. `software_version` là chuỗi phần mềm; `version` là số phiên bản bản ghi.

- `GET /api/assets/technologies`: `{items:[TechnologyView]}`, active theo ID tăng dần, tối đa 1.000.
- `POST /api/assets/technologies`: body exact `{vendor,product,software_version,note}`, trả 201.
- `PUT /api/assets/technologies/{id}`: body POST cộng `expected_version`, trả 200 và tăng `version`.
- `DELETE /api/assets/technologies/{id}?expected_version=N`: soft-delete, trả 204 rỗng.

ID, `version`, `expected_version` là integer strict trong `1..9007199254740991`. IT, analyst, admin và multi-role
có ít nhất một vai trò này được phép; leader-only bị 403. Auth/role chạy trước query/body/database. Mutation kiểm
Origin trước ID/query/body/database, giới hạn body 8.192 byte và chỉ nhận JSON. Mọi response có `no-store` và
`Vary: Cf-Access-Jwt-Assertion`.

Mã lỗi ổn định: `authentication_required` 401, `forbidden` 403, `technology_not_found` 404,
`technology_exists`/`technology_conflict` 409, `request_too_large` 413, `unsupported_media_type` 415,
`invalid_technology` 422 và `assets_unavailable` 503.

## Chuẩn hóa, transaction và audit

`vendor` 1..128, `product` 1..256, `software_version` 1..128 code point sau trim; ba trường từ chối Unicode
Cc/Cf/Cs trước trim. Chỉ `vendor`/`product` dùng `casefold()` cho khóa nội bộ; không NFKC, alias, bỏ dấu hoặc
đổi dấu câu. `software_version` không casefold và không parse range/CPE. Duplicate active là bộ ba khóa nội bộ;
soft-delete cho phép tạo lại bằng ID mới. `note` giữ nguyên, tối đa 500 code point. Actor 1..512 code point và
không rỗng sau strip.

`initialize()` dùng một `BEGIN IMMEDIATE`, DDL tuần tự và một commit. Fresh database tạo đủ table/index/marker;
database có đủ đối tượng phải qua kiểm schema/index/marker; trạng thái partial/sai bị từ chối, không tự repair.
CRUD, validate output, before/after audit và commit nằm trong cùng transaction. Chỉ lỗi unique đúng ba cột
identity active được map duplicate; unique/trigger/audit khác trả unavailable và rollback. Row/key hỏng, version
overflow và hơn 1.000 active đều trả unavailable, không trả dữ liệu một phần.

## Mức kiểm chứng

Test cục bộ dùng SQLite/JWT tổng hợp kiểm migration, CRUD, quyền, validation, audit, rollback, corruption,
giới hạn và regression assets/W02. Chưa kiểm gateway, UI/browser, Cloudflare/JWKS thật, lab, OpenCTI hoặc
production.
