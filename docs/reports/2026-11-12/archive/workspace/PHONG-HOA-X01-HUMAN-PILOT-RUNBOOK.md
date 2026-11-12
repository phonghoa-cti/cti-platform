# X01 — runbook pilot hai người gán nhãn độc lập

Áp dụng tại source chỉ-đọc `cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`. Đây là hướng dẫn thao tác sau khi có người thật và quyền dữ liệu; không tạo annotation mẫu, không triển khai scorer/adjudication/UI, và không là phép thử model.

## Điều kiện con người phải hoàn tất trước

1. Người phụ trách xác nhận bằng chứng bằng văn bản cho từng raw report: nguồn, phạm vi lưu (local/repo), và TLP/nhãn chia sẻ. URL công khai không đủ. Chỉ chọn các giá trị schema đúng bằng chứng đó; vì schema không có TLP “unknown”, bài chưa có marking không được tạo record (kể cả `link-only`).
2. Chọn đúng năm bài không phải cùng bản dịch hoặc trùng văn bản đáng kể; ghi quyết định duplicate/translation trong metadata schema, không suy từ tựa đề.
3. Có hai người gán nhãn khác nhau, cùng bản raw đã chuẩn hóa và cùng pin ATT&CK; họ không xem file nhãn, thảo luận hay tỉ lệ của nhau trước khi cả hai nộp bản độc lập. Hai `annotator_id` chỉ là định danh kỹ thuật, không tự chứng minh độc lập.
4. Chỉ người điều phối mở hai nhãn sau khi cả hai đã cố định. Những khác biệt được con người hòa giải (adjudication) trong artefact/quy trình được phê duyệt riêng; không sửa ngược bản độc lập để làm đẹp agreement.

## Chuẩn bị dataset cục bộ hợp lệ

Tạo một thư mục dataset **ngoài repo và ngoài mọi input/output của CLI**. Có đúng `manifest.json`, `records/`, `annotations/`, `raw/`; `adjudications/` và `suggestions/` nếu tạo phải rỗng. Mỗi metadata là `records/<id>.meta.json`, raw là `raw/<id>.txt`, annotation là `annotations/<id>.<annotator_id>.json`. Không tạo file lạ, thư mục con, symlink/junction/hardlink hay file output trong dataset. JSON phải UTF-8 strict, không BOM, duplicate key, `NaN`, `Infinity`, recursion bất thường hay key ngoài bảng dưới đây.

Ký hiệu: `ID64` là ASCII `[a-z0-9][a-z0-9-]{0,63}`; `ID32` giống vậy nhưng dài tối đa 32; `HASH` là 64 hex thường; `DATE` là `YYYY-MM-DD` hợp lệ. Chuỗi không được có NUL/lone surrogate; boolean và integer không được ép kiểu.

| Object / file | Key bắt buộc (kiểu và giá trị) | Optional / ràng buộc parser |
|---|---|---|
| `manifest.json` | `schema_version: "gold-pilot-v1"`; `dataset_id: ID64`; `purpose: "human-annotation-pilot"`; `provenance: "human-supplied"`; `document_count: int = 5` | Không key khác. `synthetic-fixture` chỉ dùng fixture tổng hợp, không dùng cho pilot người thật. |
| `records/<id>.meta.json` | `schema_version: "gold-pilot-v1"`; `id: ID64`; `source`; `language: "vi"\|"en"`; `tlp: "TLP:CLEAR"\|"TLP:GREEN"`; `raw`; `duplicate_group: ID64`; `split: "pilot"`; `attack` | Chỉ `translation_of: ID64` optional. Tên file phải đúng `<id>.meta.json`; bản dịch phải trỏ original khác ID, cùng duplicate group, không chain/cycle. |
| `source` | `url: HTTPS` dài 1–2048 code point, có host, không userinfo/control/whitespace; `publisher: str` 1–256; `published_date: DATE`; `retrieved_at: DATE`; `source_license`; `storage_right` | `published_date <= retrieved_at`. `source_license`: `public-domain\|cc-by-4.0\|cc-by-sa-4.0\|publisher-permission\|unknown`. `storage_right`: `repo-allowed\|local-only\|link-only\|prohibited`. `unknown` chỉ đi với `link-only`; `prohibited` invalid. |
| `raw` | `present: bool`; `sha256: HASH\|null` | `present=true` cần `raw/<id>.txt` và SHA-256 UTF-8 của text LF. `present=false` cần `sha256=null`, không file raw và không annotation. `link-only` không được `present=true`. |
| `attack` | `version: str` đúng `pin.version`; `sha256: HASH` đúng `pin.sha256` | Pin/catalog official phải phù hợp `human-supplied`; current code chỉ hỗ trợ official v20.1. |
| `annotations/<id>.<annotator_id>.json` | `schema_version: "gold-pilot-v1"`; `id: ID64`; `annotator_id: ID32`; `annotated_at: DATE`; `attack_version: str`; `raw_sha256: HASH`; `iocs: list`; `ttps: list` | Chỉ `no_findings: bool` optional. Tên file khớp ID/annotator; `annotated_at >= retrieved_at`; version/hash khớp record; tối đa **2** annotation/record và annotator khác nhau. |
| IOC item | `type`; `value: str` 1–2048; `role`; `evidence` | `type`: `ipv4\|ipv6\|domain\|url\|email\|md5\|sha1\|sha256`; `role`: `attacker\|victim\|benign`. Tối đa **256** IOC; normalizer phải trả đúng `type/value`; không duplicate triple `(type,value,role)`. |
| TTP item | `attack_id: str`; `evidence` | Tối đa **256** TTP; exact `attack_id` không duplicate và phải active trong catalog pin. Parent/sub-technique là ID khác nhau; evidence không xác nhận semantic. |
| Evidence item | `start: int`; `end: int`; `quote_sha256: HASH` | List có 1–16 item; `0 <= start < end <= len(text)` và `end-start <= 2048` code point; không duplicate tuple `(start,end,quote_sha256)` trong cùng item. |

`gold-pilot-v1` thay cho ví dụ `GUIDELINE.md` cũ: không dùng `labels/`, `malware`, `actor` hoặc `ghi_chu`; mọi object có key đóng. `no_findings: true` nghĩa là cả `iocs` và `ttps` rỗng; nó không có nghĩa “chưa làm”. Hợp đồng đầy đủ nằm tại `PHONG-HOA-X01-GOLD-PILOT-LEADER-PLAN.md`; parser được đối chiếu là `cti-x01-gold-pilot/extractor/phonghoa_extractor/gold_pilot.py` (manifest dòng 287–301, record/source/raw 327–420, annotation/evidence 424–520).

Tất cả raw phải UTF-8 strict; chuyển CRLF và CR thành LF, không trim hay NFC/NFKC. `raw.sha256`, `raw_sha256`, `quote_sha256` và `start/end` dùng chính văn bản LF đó; span là chỉ số **code point Unicode**, không phải byte/UTF-16. Quote hash là SHA-256 UTF-8 của substring `text[start:end]`. IOC evidence phải là token đúng (có thể defang) và khi normalizer chuẩn hóa phải khớp `type/value`; TTP evidence chỉ chứng minh quote/span/hash, không chứng minh ngữ nghĩa TTP.

Ví dụ giả cực ngắn, chỉ kiểm cách tính trong bộ nhớ (không phải raw corpus hay annotation file): input `Cảnh báo 😀\r\nhxxp://evil[.]example\r` canonical thành `Cảnh báo 😀\nhxxp://evil[.]example\n`. Với `quote = "hxxp://evil[.]example"`, normalizer thực trả `type=url`, `value=http://evil.example/`; `start=11`, `end=32`, `quote_sha256=461bcfb45c988ca4ccaa9c72f3a84e7ba588b01a24c9e429f4af216f06d174a7`, còn SHA-256 UTF-8 của toàn text canonical là `2cbda6ed9b762a5647a98b31db053c7986cc69aea3c9ee70149526b6be831f2b`. Emoji được tính là một code point và defang vẫn nằm nguyên trong quote; không thay đổi emoji/defang trước cắt span.

## Thứ tự thực hiện

1. Người phụ trách xác nhận quyền/TLP và local storage trước khi tải/lưu raw. Nếu chưa rõ, giữ bài ở shortlist ngoài dataset; không tạo record hay annotation.
2. Lưu năm raw hợp lệ cục bộ; chuẩn hóa LF, tính SHA-256 và ghi metadata khớp schema. Chỉ `human-supplied` dùng official ATT&CK pin; không dùng synthetic fixture/pin để giả dữ liệu thật.
3. Giao cùng snapshot raw-hash/pin cho hai người trong hai thư mục làm việc tách biệt. Mỗi người tự xác định IOC role (attacker/victim/benign) và TTP chỉ khi văn bản mô tả rõ; không suy diễn parent/sub-technique.
4. Mỗi người tự kiểm annotation: id/tên file/sha/ngày, 1–16 evidence mỗi item, span code point và quote hash; tối đa 256 IOC/TTP, không duplicate canonical IOC hoặc exact TTP ID. Người điều phối chỉ nhận file đã hoàn tất.
5. Khi đủ hai nhãn, chạy validator/readiness. Sau đó mới xem agreement IOC attacker triple và exact TTP ID. Tỷ lệ này là Jaccard giữa hai nhãn khai báo, không phải precision/recall, model F1 hay semantic truth.
6. Hòa giải chỉ sau bước 5: lưu cả hai bản độc lập; con người nêu lý do và quyết định nhãn cuối theo cơ chế được duyệt riêng. Validator hiện không thực hiện adjudication.

Mốc 80% trong `GUIDELINE.md` cũ chỉ là ngưỡng để đội thảo luận quy tắc. `gold-pilot-v1` **không có cổng 80%**; report agreement không tự cho phép tiếp tục, không xác nhận gold corpus và không đánh giá AI.

## Lệnh kiểm tra (PowerShell)

Đặt biến rõ ràng; thay `D:\PHONGHOA-HUMAN-PILOT\dataset` bằng thư mục local đã được cấp quyền và một thư mục report trống, ngoài dataset.

```powershell
$root = '$WORKSPACE'
$repo = "$root\cti-x01-gold-pilot"
$py = "$root\cti-platform-start\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$repo\core;$repo\extractor"
$env:PYTHONDONTWRITEBYTECODE = '1'
$dataset = 'D:\PHONGHOA-HUMAN-PILOT\dataset'
$snapshot = "$root\x01-attack-real-research-evidence\enterprise-attack-20.1.json"
$pin = "$repo\extractor\tests\fixtures\attack_official\official-pin.json"
$report = 'D:\PHONGHOA-HUMAN-PILOT\reports\readiness.json'
& $py "$repo\extractor\dataset\check_gold_pilot.py" --dataset $dataset --attack-snapshot $snapshot --attack-pin $pin --report $report
$LASTEXITCODE
```

Lệnh đặt `PYTHONPATH` để CLI dùng đúng core/extractor ở HEAD đã nêu, dùng pin official v20.1 đang được code hỗ trợ, và ghi report no-clobber vào đường dẫn mới. Không chạy lại cùng `--report` nếu file đã tồn tại: chọn một tên mới sau khi xem kết quả, vì writer cố ý không ghi đè. Không đặt report trong dataset hay trùng/alias raw, pin, snapshot.

- Exit `0`: `READY_FOR_ADJUDICATION` đã publish structurally; **vẫn chưa** chứng minh quyền thật, hai người độc lập hay semantic quality.
- Exit `2` với stdout `NOT_READY`: report đã publish nhưng còn thiếu quyền/raw/nhãn thứ hai; xem `reasons`, không coi là lỗi model. Exit `2` với stderr `{"error":"..."}`: input/schema/argument không hợp lệ, không tin report mới.
- Exit `1`: I/O failure; không suy report đã được publish. Nếu stderr có `{"warning":"cleanup_incomplete"}` cùng stdout status, report đã publish nhưng file tạm không dọn được; người phụ trách kiểm tra đúng thư mục output và xử lý file tạm thuộc sở hữu công cụ.

## Diễn giải trạng thái đúng mức

Validator kiểm schema, UTF-8/LF, span/hash, IOC normalizer, TTP active trong catalog pin và inventory. `READY_FOR_ADJUDICATION` là structural readiness của dữ liệu đã khai báo. Nó **không** xác minh giấy phép/TLP thật, nguồn không trùng, danh tính/độc lập annotator, nhãn semantic TTP, corpus gold, hay bất kỳ F1/chất lượng model/RAG nào. Research/shortlist và fixture tổng hợp cũng không phải corpus/model test.
