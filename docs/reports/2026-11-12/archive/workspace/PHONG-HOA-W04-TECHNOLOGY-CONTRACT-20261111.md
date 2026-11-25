# W04 Technology — hợp đồng Leader chốt để triển khai song song

Ngày 11/11/2026. Base `8a767314b654d39c1ddc2995b7919c44a5b7027a` tại `cti-w04-local-integration`. Đây là quyết định triển khai sau nghiên cứu, chưa phải bằng chứng mã/test đạt. Văn bản này ưu tiên hơn các lựa chọn còn mở trong `PHONG-HOA-W04-TECHNOLOGY-RESEARCH-20261111.md`.

## Phương án và các điều chỉnh sau review

Chọn `TechnologyStore` mới trong `portal_api/technologies.py`, bảng/audit tách riêng, cùng SQLite nếu được inject. Tái dùng cách xử lý quyền/giao dịch/audit của W04, không mở enum `AssetType` và không sửa `AssetStore`, matcher, core hay hợp đồng W02.

- Tên trường ngoài: `software_version` là chuỗi phần mềm; `version` là số phiên bản bản ghi như W04 hiện có. Bỏ lựa chọn `version_id`/`record_version` trong JSON để hai nhóm không tự chọn khác nhau.
- Chỉ trim và Unicode `casefold()` vendor/product làm khóa nội bộ. **Không NFKC**, alias, bỏ dấu hoặc đổi dấu câu: spec W03 chỉ chốt không phân biệt hoa thường; không tự mở rộng phép tương đương tên.
- Origin sai = 403, body quá lớn = 413, media type sai = 415; không gộp thành 422 như hàng kiểm trong báo cáo nghiên cứu.
- Migration dùng một giao dịch tường minh với DDL tuần tự, không sao chép `BEGIN` rồi `executescript()` từ một pattern có thể commit sớm. Mọi record/response phải validate trước commit.
- Frontend có thể làm cả adapter HTTP với fetch giả lập ngay; chỉ nối tab mẫu trước. Không chờ Backend để viết UI/test, không nối API/gateway thật khi chưa nghiệm thu.

## Wire DTO duy nhất

```json
{
  "id": 41,
  "vendor": "Fortinet",
  "product": "FortiOS",
  "software_version": "7.2.1",
  "note": "VPN gateway mẫu",
  "created_by": "synthetic-it",
  "created_at": "2026-11-11T16:00:00Z",
  "updated_at": "2026-11-11T16:00:00Z",
  "version": 1
}
```

Exact keys, không field ẩn thêm vào response. `id`, `version`, `expected_version` là strict integer 1..9007199254740991 (không bool/float/string). Timestamp UTC ISO dạng `Z`, có thể có phần thập phân; parser giống W04. `created_by` string 1..512 code points, không rỗng sau strip; subject quá 512 phải bị từ chối trước ghi/audit.

`vendor` 1..128, `product` 1..256, `software_version` 1..128 Unicode code points sau trim. Reject ký tự thuộc Unicode Cc/Cf/Cs trong ba input này trước trim (control/format/surrogate); không parse phiên bản, wildcard, comparator, range hoặc CPE. `note` exact string 0..500, giữ quy tắc W04. JS đếm code points (`Array.from`), không dùng số UTF-16 code units làm bound.

Khóa duplicate active = `(vendor.strip().casefold(), product.strip().casefold(), software_version.strip())`. Lưu display sau trim; không casefold software_version, không gộp nhiều khoảng trắng bên trong. Hai phiên bản phần mềm khác nhau là hai khai báo. Soft-deleted cho phép tạo lại bằng ID mới. Ví dụ `Fortinet/FortiOS/7.2.1` và ` FORTINET /fortios/7.2.1` trùng; `7.2.2` không trùng. Casefold là thẩm quyền Backend; frontend không tự kết luận duplicate bằng lowercase gần đúng.

## API tách biệt, opt-in

| Request | Kết quả |
|---|---|
| GET `/api/assets/technologies` | 200 exact `{items:[TechnologyView]}`, chỉ active, ID tăng dần, tối đa 1000; query không hỗ trợ bị 422 |
| POST `/api/assets/technologies` | Exact `{vendor,product,software_version,note}`, 201 TechnologyView |
| PUT `/api/assets/technologies/{id}` | Exact POST + `expected_version`, 200 TechnologyView; version bản ghi tăng 1 |
| DELETE `/api/assets/technologies/{id}?expected_version=N` | Exact một expected_version, soft-delete + audit, 204 rỗng |

`create_app(..., technology_store=None)` không tự tạo/migrate DB; thiếu store → 503 `assets_unavailable` sau auth/quyền. Request không khởi tạo schema. Static technology routes được đặt rõ trước route asset ID nếu cần để không nuốt route mới. Giữ nguyên hành vi domain/CIDR. Không thay public config/auth hoặc thêm quyền.

Auth JWT và role theo mapping server hiện có (`it|analyst|admin`; multi-role có một role được phép thì được). Missing/bad JWT401; chỉ leader hoặc role không được phép403. Không đọc body/query/DB trước auth/role. Với mutation đã có quyền: kiểm Origin trước parse ID/query/body; body cap8192 bytes, content-type đúng như helper W04. Không echo SQL, input hay JWT. Cache-Control no-store và Vary Cf-Access-Jwt-Assertion cho cả thành công/lỗi.

| HTTP/code | Ý nghĩa |
|---|---|
| 401 `authentication_required` | Thiếu/sai danh tính |
| 403 `forbidden` | Thiếu quyền hoặc Origin sai |
| 404 `technology_not_found` | ID không tồn tại/đã xóa |
| 409 `technology_exists` | Trùng identity active thật |
| 409 `technology_conflict` | expected_version cũ |
| 413 `request_too_large` | Body vượt cap |
| 415 `unsupported_media_type` | Không đúng JSON content-type |
| 422 `invalid_technology` | Kiểu/extra key/query/id/nội dung không hợp lệ |
| 503 `assets_unavailable` | Store/auth tạm lỗi, schema/row hỏng, quá giới hạn; không trả dữ liệu một phần |

Error exact `{error:{code,message}}` như W04. Adapter chỉ map các cặp code/status nêu trên; với mutation, timeout/network/abort/response sai/mã gateway bất định → `unknown-mutation`, không retry. GET lỗi bất định → unavailable. Sau mutation thành công nhưng refresh lỗi: giữ thông báo đã lưu, chỉ GET retry. Sau unknown: thông báo chưa rõ, chỉ GET đối soát, không tự gửi lại; chặn double submit trong khi đang ghi/chưa đối soát.

## Lưu và migration

Sở hữu `technology_assets`, `technology_asset_audit`, marker `w04_technology_migrations` theo nghiên cứu; cột bản ghi có thể dùng `record_version` nội bộ nhưng wire luôn `version`. Không sửa schema/count/nội dung `assets`, `asset_audit` hoặc bảng module khác; không dùng PRAGMA user_version toàn DB.

`initialize()` explicit: nếu chưa có cả ba đối tượng thì tạo bảng/index/marker version1 trong cùng BEGIN IMMEDIATE và commit một lần. Nếu có đủ thì kiểm schema/cột/unique index partial/marker tương thích và idempotent; nếu chỉ có một phần/sai schema/marker/version lạ, từ chối và giữ nguyên, không repair/drop tự động. Lỗi giữa DDL rollback cả ba; khóa/lỗi I/O chuyển unavailable. Close connection sau mỗi thao tác, kể cả lỗi.

CRUD: validation input + actor trước ghi; mutate row, validate chính đối tượng sẽ trả (mọi bound và record version), audit before/after cùng actor/UTC trong một BEGIN IMMEDIATE. Không commit rồi mới phát hiện response invalid. Duplicate chỉ được map409 khi đúng index identity của technology; lỗi UNIQUE/CHECK/trigger ở bảng audit/khác →503 và rollback, kể cả khi dòng identity đã tồn tại. Version overflow không commit. Từ chối thêm khi đã đủ1000 active; dữ liệu có >1000 hoặc row/key sai khi đọc trả503, không truncate.

Technology tuyệt đối không gọi AssetMatcher, không tạo allowlist, không đổi asset_match/lookup. W03 chưa triển khai; vendor/product có thể là đầu vào đọc sau này, nhưng chỉ là gợi ý liên quan và không kết luận phiên bản bị ảnh hưởng. Không CSV/brand/CPE parser/feed/scan/alias/version-range.

## Nguồn và mức đã kiểm

Leader đối chiếu baseline sạch, app/schema/store/adapter/UI và W03/W04 specs. Nghiên cứu được chấp nhận với điều chỉnh trên; không xác nhận đã có technology code/test.

Nguồn Leader mở trực tiếp: [NIST IR7695](https://csrc.nist.gov/pubs/ir/7695/final) xác định CPE Naming là mô hình tên lớp sản phẩm; [Python3.12 sqlite3](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Cursor.executescript) ghi executescript có thể commit transaction đang mở trong legacy mode, nên migration phải kiểm rollback thực. Đọc ngày11/11/2026. PDF NIST timeout và trang NVD không trả văn bản trong lần kiểm Leader; không dùng các lần đó làm bằng chứng nội dung. Các nguồn CVE/OpenCTI còn lại là evidence Research, không chứng minh runtime/license/data matching.
