# X01-INGEST-QUEUE-NEXT — nghiên cứu cầu nối envelope vào hàng chờ W05

Ngày 11/11/2026. Đây là nghiên cứu và brief thiết kế, **không phải** triển khai hay kết quả test mới.

## Câu hỏi và bằng chứng đã đọc

Mục tiêu mẹ là đưa bản nháp IOC từ TXT/PDF cục bộ vào hàng chờ người duyệt, giữ được bằng chứng nguồn và tuyệt đối không tự ghi OpenCTI. Hai checkout chỉ đọc đã được đối chiếu:

| Checkout | Ref đã đọc | Quan sát liên quan |
|---|---|---|
| `cti-x01-ingest-local` | `8a16758601647fb3dbf935abecc2435f3b7a3fb6` | `extractor/ingest/run.py` xuất JSON `x01-local-ingest/1.0`: `input` (raw/canonical metadata) và `draft` schema 1.0. `local_ingest.py` tạo raw SHA-256 và canonical text SHA-256; span nằm trên canonical text. |
| `cti-x01-w05-stix-e2e` | `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b` | `store.py` schema SQLite v2 đã lưu payload pending bất biến, metadata review/selection/audit riêng; `save_draft()` dùng `BEGIN IMMEDIATE`, `get/list` mở `mode=ro`, và STIX chỉ đọc final approve audit. |

`draft.source.sha256` hiện là SHA-256 của `draft.text` UTF-8, không phải byte của file PDF/TXT. Store W05 kiểm strict exact keys payload, hash text, language/TLP, span/evidence và kept IOC; vì thế nên gọi lại validator này, không tạo schema draft thứ hai.

Nguồn nền tảng đã kiểm ngày 11/11/2026:

| Ai / nguồn | Điều dùng lại được | Giới hạn |
|---|---|---|
| [SQLite — Transactions](https://www.sqlite.org/lang_transaction.html) | `BEGIN IMMEDIATE` lấy write transaction từ đầu; `COMMIT`/`ROLLBACK` tạo đơn vị ghi nguyên tử. SQLite chỉ có một writer cùng lúc; reader giữ snapshot. | Không tự tạo exactly-once qua crash hoặc response mất. |
| [SQLite — PRAGMA](https://www.sqlite.org/pragma.html#pragma_user_version) | `user_version` là marker version schema, có thể kiểm trước khi dùng DB. | PRAGMA là riêng SQLite; phải kiểm hình dạng bảng/index, không chỉ tin version. |
| [Python sqlite3](https://docs.python.org/3/library/sqlite3.html) | Placeholder `?` cho query và `commit()` rõ ràng; `sqlite3.connect(path)` có thể tạo DB nếu path chưa có. | Reader phải tiếp tục dùng URI `mode=ro`; writer cần kiểm path/policy trước. |
| [Python json](https://docs.python.org/3/library/json.html) | `object_pairs_hook` cho phép từ chối key trùng; `allow_nan=False` dùng cho serialize canonical. | JSON không tin cậy có thể ngốn CPU/RAM, nên cần cap byte và độ sâu trước khi lưu. |

## So sánh cách làm

| Cách | Tái dùng | Chi phí/rủi ro | Kết luận |
|---|---|---|---|
| A. Lệnh import envelope độc lập trong tree W05 (**chọn**) | Validator/store W05 v2, contract payload 1.0, CLI style hiện có; chỉ bổ sung validator envelope + provenance + migration v3. | Có migration nhỏ và test mới. | Ít thay đổi nhất mà vẫn nối được hai nhánh không merge. |
| B. Thêm `--db` vào `extractor/ingest/run.py` | Tái dùng output mới tạo ngay trong ingest. | Kéo dependency và schema W05 vào tree ingest; failure sau publish envelope tạo hai hành vi, làm parser/CLI hiện có phức tạp hơn. | Không chọn. |
| C. Service/outbox/worker mới | Có thể chuẩn bị async sau này. | Thêm listener, retry protocol, dependency và bề mặt quyền; vượt scope local/offline. | Không chọn. |

Khuyến nghị: **A — điều chỉnh store W05 bằng importer một lần**. Importer chỉ nhận file envelope đã xuất; không mở lại file PDF/TXT, không gọi model/mạng/OpenCTI, không suy diễn parser, và không dùng path nguồn trong envelope.

## Base, target và phạm vi chính xác

- Base nguồn W05 chỉ đọc: `$WORKSPACE\cti-x01-w05-stix-e2e` tại `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Target tuyệt đối (chưa được tạo trong nhiệm vụ nghiên cứu): `$WORKSPACE\cti-x01-ingest-queue`, branch `feat/x01-ingest-queue-20261111`, base đúng SHA trên.
- Producer chỉ đọc: `$WORKSPACE\cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`; không cherry-pick/merge toàn bộ producer.
- Chỉ dùng `cti-x01-ingest-local@8a167586` làm nguồn contract. Nếu cần chép ý tưởng `object_pairs_hook`, strict JSON hoặc local-path guard, ghi provenance comment/test nêu SHA; không import từ path checkout khác ở runtime.
- Sửa tối thiểu dự kiến: `extractor/phonghoa_extractor/store.py`; mới `extractor/phonghoa_extractor/ingest_queue.py`, `extractor/ingest_queue/run.py`; tests mới cho module/CLI; `docs/specs/W05-draft-offline-contract.md`, `docs/PROGRESS.md`, README CLI liên quan. Không sửa parser PDF/TXT, `drafts.py`, selection/review/STIX public contract hay API HTTP.

## Hợp đồng envelope và DTO được chốt

CLI đề xuất:

```text
python extractor/ingest_queue/run.py import --envelope <path.json> --db <path.sqlite> --created-by-subject <opaque-subject> [--timeout <seconds>]
```

Nó nhận **một** JSON UTF-8 file regular cục bộ, không symlink/reparse point/UNC/network path; tối đa 16 MiB. Đọc một lần, không dùng bất kỳ path nào nằm trong JSON. `--created-by-subject` là bắt buộc, là subject opaque do người vận hành khai báo và được `_validate_subject` W05 kiểm; nó không đến từ envelope và chưa phải xác thực HTTP. Parse từ chối UTF-8 lỗi, surrogate Unicode không encode UTF-8 strict, duplicate key mọi cấp, `NaN`/`Infinity`, root không object hoặc độ sâu quá 64. Độ sâu tính root object là 1; mỗi dict/list lồng tăng 1; scalar không tăng. Không log raw text, evidence, full path hay payload khi lỗi.

Top-level envelope exact `{"schema_version","input","draft"}`; schema đúng `x01-local-ingest/1.0`. `draft` phải đi nguyên vẹn qua `_validate_draft()` W05 và có exact keys schema 1.0 — importer không thêm/bớt/sửa `items`, `items.keep`, text, findings hoặc evidence.

DTO library tối thiểu là `IngestProvenance` (draft_id, envelope schema/hash, format, display_name, raw hash/bytes, canonical hash, page metadata) và `IngestQueueResult(draft_id, result)`; `get_ingest_provenance(db_path, draft_id, *, timeout=5.0)` chỉ đọc `mode=ro`, không migrate và trả DTO sau khi kiểm row. Parser/validator ném `IngestEnvelopeError(code)` cho tám lỗi envelope; store giữ `DraftInputError` (creator/timeout), `DraftConflictError` (creator khác), `DraftNotFoundError` và `DraftSQLiteError`. CLI là adapter duy nhất map các class thành bộ mã stderr đã chốt; không lộ exception/SQL/payload.

`input` exact keys:

| Key | Quy tắc strict |
|---|---|
| `format` | đúng `"text"` hoặc `"pdf"`. |
| `display_name` | string UTF-8 không rỗng, không control, `/` hoặc `\\`; phải bằng `draft.source.name`. |
| `raw_sha256` | đúng 64 hex thường; chỉ là digest do envelope khai báo. |
| `raw_bytes` | `int` thật (không bool), 0..8,388,608. Với TXT phải đúng `len(draft.text.encode("utf-8", "strict"))`. |
| `canonical_text_sha256` | đúng 64 hex thường, phải bằng `draft.source.sha256` và SHA-256 UTF-8 của `draft.text` qua validator W05. |
| `page_count`, `page_text_ranges` | Với text: cả hai `null`, `raw_sha256 == canonical_text_sha256`; không normalize newline/BOM. Với PDF: count `int` thật 1..50 và list đúng count của `[start,end]`, số nguyên thật, 0 ≤ start ≤ end ≤ `len(text)`, từng page ≤100.000 code point, ít nhất một page `strip()` không rỗng; range đầu bắt đầu 0, range cuối kết thúc ở `len(text)`, range kề nhau cách đúng `"\n\f\n"`. |

`draft.text` phải là string UTF-8 strict, tối đa 1.000.000 code point trước mọi hash/range. Thứ tự validation/error public phải ổn định: (1) CLI argument/timeout/creator; (2) boundary đọc file/cap; (3) decode JSON; (4) root type/exact keys/schema; (5) input type/exact keys/bounds; (6) shape draft trước mọi nested access; (7) cross-invariants input↔draft; (8) `_validate_draft`; (9) DB exists/path/schema/lock; (10) duplicate/write. Bộ mã đóng: `invalid_arguments`, `invalid_created_by_subject`, `envelope_read_failed`, `envelope_too_large`, `invalid_utf8`, `invalid_json`, `duplicate_json_key`, `json_too_deep`, `invalid_envelope`, `invalid_input_metadata`, `invalid_provenance`, `invalid_draft`, `database_invalid`, `database_locked`, `duplicate_creator_conflict`, `write_failed`. stderr chỉ `Lỗi: <code>`, exit 2 cho argparse, exit 1 cho các mã còn lại; stdout chỉ một JSON summary khi commit hoặc duplicate thành công.

## Provenance, schema và giao dịch

Giữ `drafts.payload_json` không đổi. Nâng `STORE_SCHEMA_VERSION` từ 2 lên **3**, thêm đúng một bảng 1:1:

```sql
CREATE TABLE draft_ingest_provenance (
  draft_id INTEGER PRIMARY KEY REFERENCES drafts(id),
  envelope_schema_version TEXT NOT NULL,
  envelope_sha256 TEXT NOT NULL UNIQUE,
  input_format TEXT NOT NULL CHECK (input_format IN ('text','pdf')),
  display_name TEXT NOT NULL,
  raw_sha256 TEXT NOT NULL,
  raw_bytes INTEGER NOT NULL,
  canonical_text_sha256 TEXT NOT NULL,
  page_count INTEGER,
  page_text_ranges_json TEXT
);
```

Validator schema v3 phải kiểm chính xác columns, PK/FK, UNIQUE `envelope_sha256` và hàng provenance canonical trước khi coi DB hợp lệ. `page_text_ranges_json` là JSON canonical compact (`separators=(',', ':')`), `null` cho text. Có thể bổ sung CHECK đơn giản, nhưng validator Python là nơi thực thi liên hệ cross-field/range đầy đủ.

Migration hiện có 0/1→2 là **một** transaction đã tồn tại, không giả định ba transaction 0→1→2. Bổ sung 2→3 trong cùng transaction migration riêng: dưới `BEGIN IMMEDIATE`, validate v2, tạo bảng, validate v3, set `PRAGMA user_version=3`, commit; lỗi rollback DDL/version. Rerun v3 chỉ validate. Importer không được lồng `BEGIN`: gọi migration xong rồi mới mở transaction ghi riêng. Nếu migration thành công nhưng insert sau đó lỗi, schema v3 được giữ lại nhưng không có draft/provenance mồ côi.

| DB mở bằng binary mới | get/list legacy | selection/review/export | importer writer |
|---|---|---|---|
| 0 legacy / 1 | đọc theo mode legacy/v1 hiện có, không migrate | giữ yêu cầu migrate hiện có, từ chối khi cần v2 | migration current rồi import v3 |
| 2 | đọc/selection/review/export theo semantics v2, không ghi/migrate | được phép như v2 | transaction migration 2→3 riêng, rồi import |
| 3 | đọc theo validator v3, không migrate | giữ behavior v2 trên schema v3 | validate v3 rồi import |
| >3/hỏng | từ chối fail closed | từ chối | từ chối |

`save_ingested_envelope()` phải validate toàn bộ envelope **và creator** trước khi mở DB. Sau đó mở writer, chạy migration transaction riêng nếu cần, rồi `BEGIN IMMEDIATE`, đọc lại `PRAGMA user_version` và validate chính xác v3 dưới khóa trước khi query `envelope_sha256`:

1. Có row provenance liên kết đúng một `drafts` row và mọi hash/canonical fields hợp lệ: creator giống nhau → trả `duplicate`, ID cũ; creator khác → `duplicate_creator_conflict`; không update payload/provenance/review/audit.
2. Không có row → insert `drafts` như `save_draft` với `created_by_subject` bắt buộc, rồi insert provenance cùng transaction, commit một lần, trả `imported` + ID.
3. Bất kỳ insert/commit lỗi → rollback. Nếu commit đã thành công nhưng process/response hỏng, retry cùng canonical envelope sẽ trả `duplicate`; đây là idempotent-at-least-once, **không** là exactly-once end-to-end.

Writer serialization của `BEGIN IMMEDIATE`, UNIQUE identity và transaction tránh hai importer đồng thời tạo hai row cùng envelope. Lock/timeout trả lỗi rõ; không retry nền. `raw_sha256` **không** tự nó là khóa hoặc bằng chứng byte PDF: importer không đọc PDF/TXT nên chỉ lưu nó là tuyên bố provenance. `envelope_sha256` là hash của canonical strict serialization envelope đã validate, dùng cho idempotency chứ không xác thực tác giả/nguồn.

## Compatibility, an toàn và giới hạn

| Chủ đề | Quyết định |
|---|---|
| W05 payload/review/selection/STIX | Giữ `payload_json`, `source_sha256`, audit và API hiện có. Import tạo pending draft với creator CLI bắt buộc; policy hiện hữu tiếp tục cấm self-approve và cần reviewer khác. |
| Migration/read | Chỉ writer import/migrate được nâng; get/list/export read không tự migrate/ghi. Không mở DB thiếu bằng read API. |
| Duplicate | Chỉ exact canonical envelope duplicate. Cùng raw hash nhưng draft/provenance khác không bị gộp; không sửa draft cũ. |
| Path/output | Không output file/sidecar; stdout summary. `--db` phải là local existing regular DB, không là envelope/samefile; reject alias/reparse/UNC theo policy test. |
| Dữ liệu CTI | Envelope là không tin cậy; không cho nó điều khiển lệnh/model/network. Không log content, evidence hoặc path tuyệt đối. TLP không cấp quyền gửi cloud. |
| Không thuộc scope | Parser/re-extract PDF, raw-byte verification, source signature, HTTP/browser, auth, listener, OpenCTI, network share, crash/power-loss semantics, cloud/lab. |

## Ma trận nghiệm thu đề xuất

| Nhóm | Ca phải có | Bằng chứng mong đợi |
|---|---|---|
| Contract | TXT Unicode và PDF synthetic envelope hợp lệ; exact output payload + provenance query/get helper | `imported`, ID; hash/ranges/source giữ nguyên. |
| Strict input | Thiếu/thừa key, bool-as-int, 64-hex sai, SHA canonical mismatch, name mismatch, format/page mismatch, deep JSON, duplicate keys, nonfinite, >16 MiB | fail closed, DB bytes/row count không đổi. |
| Integrity limit | TXT raw/canonical exact, PDF ranges/page caps/whitespace, surrogate và Unicode emoji; raw hash khác canonical | phát hiện bất nhất nội bộ; envelope bị sửa rồi tính lại hash nhất quán là input mới, không thể tự chứng minh bản gốc. |
| Atomic | inject lỗi insert provenance và commit; DB không còn draft mồ côi/audit/provenance nửa vời | rollback quan sát được. |
| Retry/race | import cùng creator hai lần; creator khác; hai process cùng envelope; timeout lock | 1 row + 1 provenance, duplicate/creator conflict stable hoặc lock error; không hứa mọi process thành công. |
| Migration | v2→v3, rerun, 0/1 chain, future/hỏng schema; insert lỗi sau migration | version/table đúng; rollback đúng transaction; schema có thể còn v3 sau lỗi insert; read không migrate. |
| Regression | save/get/list, selection/review v2, approval creator≠reviewer, STIX exporter và legacy CLI | behavior đã có còn PASS trên v3 DB; list chỉ pending. |
| Process demo | subprocess import envelope→list/get/provenance assertion trên temp DB | local/offline only; không mạng/listener/browser. |

Lệnh thực hiện sau này phải dùng Python 3.12.13 của checkout, TDD RED→GREEN cho module/CLI, targeted tests rồi regression phù hợp, `ruff check`, `ruff format --check`, `git diff --check`. Chỉ sau khi có code mới có thể báo số test/exit; nghiên cứu này chưa chạy chúng.

## Kết luận

Chọn importer envelope độc lập + provenance table schema v3. Nó tái dùng đúng validator/store/transaction W05, giữ ranh giới giữa hai branch và đem raw/canonical/range vào queue một cách có thể kiểm tra. Phần chưa chứng minh: tính đúng của implementation tương lai, race/crash trên hệ file thật, migration dữ liệu thật, PDF provenance byte gốc, API/UI/OpenCTI/lab/production.
