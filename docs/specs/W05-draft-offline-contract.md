# Hợp đồng bản nháp ngoại tuyến X01 → W05

Trạng thái: hợp đồng cho dữ liệu **đã chạy cục bộ**, chưa phải API HTTP đang hoạt động. Phiên bản payload hiện
tại là `1.0`; schema kho SQLite hiện tại là `PRAGMA user_version=3`. `drafts.py` tạo payload bất biến, còn
`store.py` kiểm/lưu payload và ghi quyết định review tách riêng.

## Import envelope X01 và provenance schema v3

Lệnh `extractor/ingest_queue/run.py import` nhận đúng một envelope `x01-local-ingest/1.0` đã có, yêu cầu
`--created-by-subject` do người vận hành cung cấp và lưu draft pending không thay đổi cùng một dòng provenance.
Identity này là subject opaque tại biên CLI, chưa phải xác thực HTTP; policy hiện hữu vẫn cấm người tạo tự approve.

Schema v3 thêm bảng `draft_ingest_provenance` quan hệ 1:1 với draft. Khóa idempotency là SHA-256 của JSON envelope
canonical đã kiểm: retry cùng creator trả `duplicate`, còn creator khác trả conflict và không đổi owner/payload.
Migration v2→v3 là transaction riêng; transaction sau đó mới ghi draft+provenance nguyên tử. Reader v2/v3 không
tự migrate. Draft cũ hoặc draft tạo qua CLI legacy có thể không có provenance và vẫn hợp lệ.

Với PDF, `raw_sha256` chỉ là provenance do envelope tự khai vì importer không mở lại byte PDF. Các kiểm tra hash,
range và separator chỉ phát hiện bất nhất nội bộ; ai sửa envelope rồi tính lại mọi hash nhất quán đã tạo một input
mới, không chứng minh được nguồn gốc hay tính xác thực. Importer không gọi model, mạng, OpenCTI hoặc tự approve.

Mục tiêu của tài liệu này là để người làm W05 đọc đúng dữ liệu hiện có mà không làm mất bằng chứng, cảnh báo
hoặc nguồn. Ba mẫu kết quả `get` thật nằm tại [`extractor/draft/examples/`](../../extractor/draft/examples/README.md).

## Hai hình dạng dữ liệu

- **Draft mới tạo:** đúng các trường của schema 1.0, chưa có `id` và `created_at`; đây là đầu vào của `save`.
- **Draft đã lưu:** toàn bộ payload ban đầu không đổi, cộng `id`, `created_at` và object `review` do store quản
  lý; đây là dữ liệu W05 cần đọc. Không đưa các metadata này trở lại lệnh `save`.

### Trường cấp draft

| Trường | Kiểu / nullable | Có ở draft mới | Có ở draft đã lưu | Ai tạo | Ý nghĩa hiện tại |
|---|---|---:|---:|---|---|
| `id` | integer dương, không null | — | ✓ | Store | Khóa bản ghi cục bộ; mỗi lần lưu tạo ID mới. |
| `created_at` | string ISO 8601 có múi giờ, không null | — | ✓ | Store | Thời điểm lưu UTC, ví dụ `...+00:00`. |
| `review` | object, không null | — | ✓ | Store | Metadata quyết định cục bộ, tách khỏi payload; xem phần dưới. |
| `schema_version` | string, không null | ✓ | ✓ | Builder | Hiện chỉ nhận `"1.0"`. |
| `status` | string, không null | ✓ | ✓ | Builder | Hiện chỉ nhận `"pending"`; đây là trạng thái **draft**. |
| `source` | object, không null | ✓ | ✓ | Builder | Tên nguồn và hash của text được lưu; xem bảng dưới. |
| `language` | `"vi" \| "en"`, không null | ✓ | ✓ | Builder/người gọi | Ngôn ngữ khai báo của text. Store không tự nhận diện. |
| `tlp` | string, không null | ✓ | ✓ | Builder/người gọi | `TLP:CLEAR`, `TLP:GREEN`, `TLP:AMBER`, `TLP:AMBER+STRICT` hoặc `TLP:RED`; là metadata, không cấp quyền gửi cloud. |
| `text` | string, không null | ✓ | ✓ | Người gọi/builder | Nguyên văn dùng để tạo hash và tính span; có thể rỗng. |
| `items` | array, không null | ✓ | ✓ | Builder | Danh sách mục trích; hiện builder C1 chỉ tạo IOC. |
| `injection_warning` | boolean, không null | ✓ | ✓ | Bộ quét | Có phát hiện dấu hiệu chèn lệnh; `false` không chứng minh text an toàn. |
| `findings` | array, không null | ✓ | ✓ | Bộ quét | Chi tiết quy tắc cảnh báo; có thể rỗng. |
| `model` | string không rỗng | ✓ | ✓ | Builder | Hiện là `regex-C1`; tên này không chứng minh có LLM. |
| `cost_tokens` | integer ≥ 0 | ✓ | ✓ | Builder | C1 hiện là `0`. |

### Metadata `review`

| Trường | Kiểu / nullable | Ý nghĩa |
|---|---|---|
| `status` | `pending \| approved \| rejected` | Trạng thái review cục bộ; `approved` **không** có nghĩa đã nhập OpenCTI. |
| `version` | integer ≥ 0 | Phiên bản optimistic concurrency; pending ban đầu là 0, quyết định cuối là 1. |
| `created_by_subject` | string không rỗng hoặc null | Subject opaque do caller tin cậy cung cấp khi lưu; null là legacy/không rõ tác giả. |
| `decided_by_subject` | string không rỗng hoặc null | Subject đã quyết định; chỉ có sau approve/reject. |
| `decided_at` | ISO 8601 có múi giờ hoặc null | Thời điểm quyết định UTC. |
| `reason` | string hoặc null | Bắt buộc, được trim khi reject; approve luôn null. |

### `source`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa |
|---|---|---|---|
| `source.name` | string không rỗng | Người gọi/builder | Nhãn/tên nguồn để hiển thị; chưa phải URL hay định danh tin cậy. |
| `source.sha256` | 64 ký tự hex thường | Builder | SHA-256 của `text.encode("utf-8")` thực sự lưu. Không hứa là hash byte file gốc trước khi giải mã/trích text. |

### Mỗi phần tử `items`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa hiện tại |
|---|---|---|---|
| `kind` | string, không null | Grounding/builder | Builder hiện tạo `"ioc"`. Store chưa giới hạn mọi giá trị string khác. |
| `type` | string, không null | Grounding/builder | Với IOC kept, phải khớp loại của `value` sau chuẩn hóa. |
| `value` | string, không null | Grounding/builder | Giá trị IOC chuẩn hóa; không dùng thay cho quote nguyên văn. |
| `span` | `[start, end]` hoặc `null` | Grounding/builder | Khoảng code point Python `[start,end)` trên đúng `text`. `null` nghĩa không có liên kết tô sáng. |
| `evidence` | string, không null | Grounding/builder | Phải bằng `text[start:end]` khi `span` khác null; có thể rỗng cho item rejected. |
| `keep` | boolean, không null | Grounding/builder | Gợi ý chọn ban đầu. `true` **không** có nghĩa con người đã duyệt. |
| `warning` | string hoặc `null` | Grounding/builder/fixture | Lý do/cảnh báo để người duyệt hiểu trạng thái. |
| `status` | string, không null | Grounding/builder | Trạng thái **item** như `ok`, `allowlist`, `bia`; khác `draft.status`. |

### Mỗi phần tử `findings`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa |
|---|---|---|---|
| `paragraph` | integer ≥ 1 | Bộ quét | Đoạn chứa dấu hiệu theo quy ước hiện tại của scanner. |
| `rule` | string, không null | Bộ quét | Mã quy tắc phát hiện. |
| `excerpt` | string, không null | Bộ quét | Trích đoạn để giải thích; luôn render dạng text. |

## Bất biến và giới hạn schema hiện tại

1. `source.sha256` phải đúng SHA-256 UTF-8 của `text`; store từ chối payload không khớp.
2. Khi `span` khác null, `text[start:end] == evidence`. IOC `keep=true` còn phải nằm nguyên token trong chính
   span đó sau chuẩn hóa và đúng `type`.
3. Item rejected có thể có `span=null`, `evidence=""`, `keep=false`; W05 không tạo liên kết tô sáng cho item này.
4. Store chỉ nhận payload `pending`; quyết định không sửa `payload_json` mà đổi metadata review trong cùng
   transaction với một audit metadata.
5. Builder C1 hiện chỉ tạo IOC. Ví dụ API cũ có `ttp|malware|actor` là hướng tương lai, không phải dữ liệu đã chạy.
6. Ngoài kiểm tra quan hệ type/value/span cho `kind=ioc` được giữ, store chưa giới hạn đầy đủ tập
   `kind`/`item.status` của dữ liệu tự khai. Biên API tương lai phải có allowlist schema và từ chối loại/trạng
   thái chưa hỗ trợ trước khi đưa dữ liệu cho W05.
7. `tlp` và `injection_warning` chỉ là dữ liệu hiển thị/kiểm soát; chúng không phải phép gửi cloud và cũng không
   chứng minh nội dung an toàn.
8. `get` và mỗi hàng `list` được trả phải kiểm lại payload, schema/status/hash ở cột SQLite, ID, thời gian và
   metadata review. Hàng `list` đã bị lọc ngoài trang hoặc không còn review pending không nằm trong lần kiểm này.
9. `save`, `get` và `list` chỉ nhận timeout kiểu `int`/`float` hữu hạn, không âm và không nhận boolean; giá trị
   sai phải bị từ chối trước khi mở SQLite.

## Unicode và span

Python 3.12 đếm `str` theo Unicode code point. Span không phải offset byte và cũng không phải vị trí ký tự hiển
thị (grapheme): một chữ ghép có thể gồm nhiều code point. Không normalize, refang hoặc trim `text` trước khi cắt.

Mẫu `01-regular.json` có emoji đứng trước IOC và evidence `[0,58)`. Python lấy quote bằng:

```python
quote = text[start:end]
```

JavaScript dùng chỉ số UTF-16 cho `slice`, nên với span code point phải dùng:

```js
const quote = Array.from(text).slice(start, end).join("");
```

Nếu API/frontend sau này chọn offset UTF-16, cần một bước chuyển đổi được đặc tả và test riêng; không được đổi
ngầm ý nghĩa span 1.0.

## Hàng đợi pending ngoại tuyến

API Python dự kiến cho lát cắt này:

```python
list_drafts(db_path, *, limit=20, before_id=None, timeout=5.0)
```

Hàm chỉ đọc các draft có trạng thái cột SQLite là `pending`, sắp xếp `id DESC` và trả:

```json
{
  "items": [
    {
      "id": 5,
      "created_at": "2026-11-10T15:18:49.564135+00:00",
      "status": "pending",
      "source": {"name": "synthetic.txt", "sha256": "..."},
      "language": "vi",
      "tlp": "TLP:AMBER",
      "item_count": 1,
      "injection_warning": false
    }
  ],
  "next_before_id": 5
}
```

Mỗi summary còn có `review_status: "pending"` và `review_version: 0`; `status` trong cùng summary vẫn là trạng
thái payload `pending` để hai lớp trạng thái không bị nhập nhằng.

- Summary không chứa `text`, `items`, `evidence`, `findings` hoặc excerpt nguồn.
- `limit` là integer thật trong `[1,100]`; `before_id` là null hoặc integer dương trong miền SQLite.
- Trang sau dùng `id < before_id`, không dùng OFFSET. Cursor không cần trùng một ID đang tồn tại.
- `next_before_id` là ID cuối trang khi còn ít nhất một dòng phía sau; hết dữ liệu hoặc trang rỗng trả null.
- Insert mới giữa hai lần đọc không làm lặp/mất ID cũ ở các trang tiếp theo; tải lại trang đầu mới thấy ID mới.
  Đây không phải snapshot chung qua nhiều lần đọc.
- Lệnh list dùng SQLite `mode=ro`, timeout hữu hạn, không tạo DB/table, không migration và không chuyển trạng thái.

## Migration và quyết định review cục bộ

- `migrate_store()` nâng database legacy user version 0 trong một transaction, backfill creator null,
  `review_status=pending`, `review_version=0`, rồi mới đặt user version 1. Chạy lại không đổi row/audit.
- `get_draft()` và `list_drafts()` nhận cả schema legacy hợp lệ nhưng chỉ đọc và trả review mặc định pending/0;
  schema tương lai hoặc hỏng bị từ chối. `decide_draft()` yêu cầu database đã migrate và không tự tạo file.
- `save_draft(..., created_by_subject=...)` giữ tương thích caller cũ; draft mới cần subject để có thể approve.
  Subject là định danh opaque do caller tin cậy cung cấp, không phải email/header đã được core xác thực.
- `Actor(subject, roles)` chỉ thực thi policy offline: chỉ `analyst`/`admin`, không tự approve, creator null không
  approve, reject bắt buộc lý do. Admin không được bypass tự duyệt; creator được reject draft của mình.
- Update state/version và insert `draft_audit` metadata cùng `BEGIN IMMEDIATE`; stale/lặp trả conflict, không thêm
  audit. Audit SQLite là trace vận hành, không chống người có quyền sửa file database.
- Approve chỉ nhận các item kept có `kind=ioc`; không gọi mạng, LLM, OpenCTI và không tạo Report/STIX/outbox.
- CLI ghi JSON summary ra file riêng; output trùng/equivalent/samefile với DB phải bị từ chối.

## Lựa chọn IOC hiệu lực (schema store v2)

- `get_effective_selection()` trả tập index eligible hiện tại, version selection/review, hash JSON canonical,
  người/thời điểm save gần nhất và bốn count tách biệt.
- `save_selection()` chỉ nhận `Actor` trusted và list/tuple index; chỉ Analyst/Admin, subset của IOC
  `kind=ioc, keep=true, status=ok`. Tập rỗng hợp lệ nhưng không thể approve.
- Save có thay đổi tăng đồng thời `selection_version` và `review_version`; no-op không ghi event. Pending có hai
  version bằng nhau, terminal có `review_version = selection_version + 1`.
- Approve và reject v2 đều copy selection version, JSON và SHA-256 vào `draft_audit`. Audit migrate từ v1 giữ ba
  trường này null vì không được bịa lịch sử.
- Payload, evidence, source hash và `items.keep` ban đầu không đổi. API/UI hiện tại chưa đọc selection object và
  chưa chấp nhận review version lớn hơn 1 nên chưa được nối vào DB đã edit.

## Khoảng trống trước khi W05 chạy thật

| Phần | Hiện tại | Cần có trước tích hợp |
|---|---|---|
| Liệt kê/lọc/phân trang | Có API/CLI ngoại tuyến theo cursor ID; chưa có HTTP | Endpoint pending có quyền, giới hạn và metadata phân trang. |
| Đọc chi tiết | Chỉ có CLI/API Python `get_draft` | Endpoint đọc một draft, lỗi 404/422 rõ và payload giữ đủ trường. |
| Xác thực/quyền | Chưa có | Danh tính phải do backend xác minh; chỉ Analyst/Admin, không tin header email do client tự gửi. |
| Schema ở biên API | Store chưa siết mọi `kind/status` | Từ chối loại/trạng thái chưa hỗ trợ và trường thừa/thiếu trước khi render. |
| Sửa/lưu nháp | Chưa có chỉnh item | Cần contract sửa item và số liệu bỏ/thêm/sửa riêng. |
| Duyệt/từ chối | Có lõi Python offline + atomic audit | Cần adapter HTTP/auth thật trước khi portal gọi. |
| Người đề xuất/người duyệt | Có subject opaque do caller cung cấp | Cần xác thực danh tính và lookup role server-side. |
| Đo sửa đổi | Chưa có | Số mục gốc/bỏ/thêm/sửa để đánh giá extractor. |
| OpenCTI | Chưa nối | Chỉ ghi sau quyết định hợp lệ; lưu ID/kết quả/lỗi và cho phép retry an toàn. |
| Offset frontend | Chỉ code point Python | Dùng `Array.from` hoặc chuyển đổi có test với emoji/chữ ghép. |

Ba endpoint `/api/drafts` legacy và bốn endpoint selection v1 trong [`api-portal.md`](api-portal.md) đã có test
in-process. Các endpoint portal khác vẫn là đề xuất; tài liệu này không chứng minh browser/lab/OpenCTI hoạt động.

## Adapter HTTP selection v1

Core hiện có hai read helper v2-only: detail đọc draft/review/selection trong một read transaction và list chỉ
thêm `selection_version` vào summary. `decide_draft_with_selection()` dùng chung transaction routine với
`decide_draft()` nhưng trả thêm snapshot selection đã ghi final audit; wrapper cũ vẫn giữ sáu field legacy.
Mutation nhận `max_version` để adapter v1 chặn trước khi ghi khi version mới vượt miền số an toàn JavaScript;
no-op hợp lệ tại cap vẫn không ghi event/version.

Contract HTTP chính xác nằm tại [`api-portal.md`](api-portal.md). `/api/drafts` legacy không đổi;
`/api/v1/drafts` mới là lát cắt in-process và chưa chứng minh listener, browser, Cloudflare/JWKS thật, lab,
OpenCTI hoặc production.

## Export STIX 2.1 ngoại tuyến từ final approve audit

Lệnh export chỉ nhận SQLite schema v2 đã tồn tại và đọc bằng URI `mode=ro`. Transaction `BEGIN` được mở trước
mọi lần đọc schema/data để payload, review, selection event và final audit thuộc cùng một snapshot. Nguồn quyền
duy nhất là đúng một `draft_audit.action=approve` khớp review terminal; selection client, `items.keep` sau duyệt
hoặc pointer hiện tại không thay thế final audit. Pending, rejected, legacy/future schema, self-review, creator
null, reason khác null, selection rỗng/hỏng hoặc metadata không nhất quán đều bị từ chối; không migration/ghi DB.

```powershell
.\.venv\Scripts\python.exe extractor\draft\stix_export.py export-approved `
  --db .\drafts.sqlite `
  --id 1 `
  --exporter-config .\extractor\draft\examples\stix\exporter-config.example.json `
  --output .\approved-bundle.json
```

Config JSON exact gồm `schema_version=1`, UUID namespace riêng, tên exporter, `identity_class=organization`,
timestamp UTC và TLP bằng TLP snapshot. Đây là cấu hình tổng hợp minh họa, không phải danh tính tổ chức thật.
TLP:CLEAR ánh xạ TLP:WHITE; GREEN/AMBER/RED giữ nguyên; AMBER+STRICT bị từ chối trong profile v1.

Artifact duy nhất là bundle JSON canonical UTF-8 có newline cuối, không có manifest sidecar. Thứ tự object là
marking literal chuẩn, exporter Identity, các SCO theo final index sau khử trùng lặp, rồi Report. Chỉ hỗ trợ
IPv4, IPv6, domain, URL, email, MD5, SHA-1 và SHA-256; không tạo Indicator, Pattern, Observed Data, Relationship
hoặc TTP. `Report.external_references` chứa JSON canonical provenance v1 và SHA-256 của chính JSON đó; không có
subject/hash subject người duyệt, source name, raw text, evidence, findings hoặc reason.

SCO dùng namespace UUIDv5 chuẩn OASIS và đúng ID-contributing properties. Identity, Report và Bundle dùng ba
child namespace UUIDv5 riêng sinh từ config. Vì SDO/Bundle UUIDv5 là ngoại lệ khuyến nghị UUIDv4, profile
validator được gọi là **strict except 103**, không gọi là strict nguyên vẹn. Dependency kiểm test là
`stix2-validator==3.3.2` trong `requirements-stix-test.lock`; runtime exporter không phụ thuộc SDK STIX.

Publisher ghi đủ bytes vào temp độc quyền cùng thư mục, flush/fsync, đóng file rồi `os.link()` tạo output mới.
Output đã tồn tại và byte-identical là thành công không ghi; nội dung khác bị từ chối, không replace/truncate.
DB, `-wal/-shm/-journal`, config và alias/symlink/reparse của chúng được bảo vệ. Hỗ trợ đã kiểm trên local NTFS;
không cam kết chống người có quyền đổi directory đồng thời, mất điện/crash hoặc network share.

Thành công stdout đúng một dòng `{"draft_id":N,"bundle_sha256":"...","object_count":N}` và exit 0. Lỗi
nghiệp vụ là một dòng an toàn trên stderr, exit 1; lỗi cú pháp/`--help` theo argparse dùng exit 2/0. Export không
gọi mạng, không retry gửi/import, không cấp quyền chia sẻ TLP và không chứng minh OpenCTI nhận artifact.
