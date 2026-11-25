# X01-LOCAL-INGEST-NEXT — nghiên cứu nạp file cục bộ

Ngày đối chiếu: 11/11/2026. Đây là quyết định/brief nghiên cứu, **không phải implementation hay test**.

## Hiện trạng và quyết định

Source chỉ đọc: `cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`; `git status --short` rỗng trước rework. Spec X01 nói bước 1 nhận URL/PDF/text và upload mặc định TLP:AMBER. C1 thực tế chỉ nhận `.txt` trong `extractor/draft/run.py`; `build_regex_draft()` băm `text.encode("utf-8")`; `evidence.py`/`grounding.py` đo span trên chuỗi C1. `core/pyproject.toml` không có dependency; chưa có loader PDF.

Chọn **B**: CLI local mới cho `.txt` và PDF có lớp text, tái dùng nguyên `build_regex_draft(canonical_text, ...)`; envelope mới chứa provenance, không sửa CLI C1 hay artifact C1–C4. A (chỉ text stdlib) là fallback không dependency nhưng không đáp ứng PDF. C (Poppler/Tika) thêm binary/JVM/licence/subprocess contract nên không phải lát nhỏ nhất.

| Phần sẵn có | Tái sử dụng | Không suy diễn |
|---|---|---|
| `build_regex_draft`, `extract_iocs`, `ground_iocs` | tạo draft `pending` từ canonical text | raw PDF/provenance PDF |
| `evidence.py` | quote/span literal Unicode | span là byte/coordinate PDF |
| `injection.scan` | coi input là dữ liệu không tin cậy | chặn mọi prompt injection |
| `os.link` đã dùng ở `extractor/eval/report.py:933`, `gold_pilot.py:741` | publish no-clobber | `os.replace` an toàn với race |

## Nguồn và dependency đã đối chiếu

| Nguồn chính thức, kiểm 11/11 | Bằng chứng dùng | Kết luận dùng lại |
|---|---|---|
| [PyPI JSON pypdf 7.0.1](https://pypi.org/pypi/pypdf/7.0.1/json) | release `7.0.1`, `requires-python >=3.10`, BSD-3-Clause; wheel SHA-256 `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`; sdist SHA-256 `0a78bb99efb41e9088260e9a8e5da134a5cbb9a322014744177bf29b5267ea6d` | pin đúng release cho Python 3.12; không extras/crypto. |
| [pypdf extract text](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | `PdfReader`/`extract_text`; parser có thể cần nhiều RAM, text/image/layout không chắc | dùng PDF text-only, không OCR/không khẳng định completeness. |
| [pypdf PdfReader](https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html) | `is_encrypted` | phát hiện rồi từ chối; không decrypt. |
| [Python 3.12 `os.link`](https://docs.python.org/3.12/library/os.html#os.link) | hard link tới target; target tồn tại gây lỗi OS | publish temp cùng parent không thay winner. |
| [Python 3.12 `os.replace`](https://docs.python.org/3.12/library/os.html#os.replace) | thay file đích nếu tồn tại | không dùng để publish lát này. |

Hai SHA distribution là metadata upstream đã đối chiếu, **không phải** bằng chứng wheel/sdist đã tải, cài hoặc byte local đã kiểm. CVE review tại lúc cài và dependency install vẫn UNVERIFIED.

## Contract canonical/provenance và compatibility

`raw_sha256` là SHA-256 bytes đọc capped, trước decode/parse. `canonical_text_sha256` là SHA-256 UTF-8 strict chuỗi canonical. Không NFC/NFKC, trim, refang hoặc đổi newline. Hash lowercase hex 64 ký tự.

| Input | Canonical text | Evidence/range |
|---|---|---|
| `.txt` | `raw_bytes.decode("utf-8", "strict")`, giữ BOM, CRLF, CR literal | span `[start,end)` là Python Unicode code-point index; quote là literal slice. |
| `.pdf` | page text nguyên trả về, đúng thứ tự; sau validate nối `"\n\f\n"` | range mỗi page half-open chỉ canonical text; separator ngoài range; không là byte/coordinate PDF. |

Đây là contract mới. CLI cũ dùng `Path.read_text()` (universal-newline), cùng bytes CRLF/CR có thể khác canonical/hash mới. Chỉ yêu cầu C1 cũ không đổi, **không** parity cùng-input. `draft.text`, `draft.source.name`, `draft.source.sha256` giữ shape C1: canonical text, basename sạch, canonical hash. Raw metadata nằm ngoài `draft`.

PDF: trước join, page text phải `type(text) is str`, UTF-8 strict encodable, <=100.000 code point; page rỗng giữ range 0. PDF 0 page=`pdf_malformed`; tất cả page whitespace=`pdf_no_extractable_text`. `.strip()` chỉ kiểm điều kiện, không sửa output. Trang rỗng giữa hai trang text vẫn giữ thứ tự/range/separator. Text trích được không chứng minh PDF complete.

## Bounds, child và error contract

Hard default/max: raw 8 MiB, 50 pages, 100.000 code point/page, 1.000.000 code point canonical tổng **kể separator**, child PDF wall timeout 15 s, result serialized tối đa 16 MiB. `IngestLimits` chỉ cho caller giảm: exact `int` (bool bị từ chối), `1..hard_max`; timeout `1..15`. Không config cap từ input, không nâng hard max.

TXT xử lý parent. Toàn bộ `pypdf` import, `PdfReader`, encrypted check, page count/extract chạy đúng một Python child do project gọi; không converter/subprocess khác. Parent dùng result file private, không capture stdout/stderr; child chỉ ghi JSON bounded `{ok, code|pages}`, không raw path/content trong log/error. Parent chờ 15 s; quá hạn `terminate`, reap <=2 s, còn sống `kill`, reap <=2 s; cleanup mọi nhánh. Result >16 MiB, JSON/schema sai, child exit thiếu result là `pdf_child_result_too_large`, `pdf_child_invalid_result`, `pdf_child_failed`.

Error order: (1) `input_missing`, `input_not_regular`, `unsupported_type`, `input_too_large`; (2) text `invalid_utf8`, PDF `pdf_support_unavailable`, `not_pdf`; (3) child `pdf_malformed`, `pdf_encrypted`, `pdf_page_limit`, `pdf_page_text_limit`, `pdf_total_text_limit`, `pdf_no_extractable_text`, `pdf_child_timeout`, ba child-result code; (4) publish `unsafe_output_path`, `output_parent_invalid`, `output_exists`, `output_publish_unsupported`, `output_write_failed`. Không exception thô/success rỗng.

Child timeout/cap **không** là hard RAM limit, OS network sandbox hay parser-safety proof. Hard-memory isolation Windows, hostile mutation ngoài race publish, PDF đối kháng và chất lượng text thật là UNVERIFIED; không tạo bomb PDF/corpus thật để thử.

## Publish no-clobber

Serialize deterministic JSON vào temp unique cùng parent; flush+fsync; kiểm alias lexical (`output == input`), resolved (`resolve(strict=False)` equal) và nếu output tồn tại `samefile`/hardlink trước publish. Không tạo parent tự động. Dùng `os.link(temp, output)` đúng một lần; `FileExistsError`=`output_exists`, giữ bytes/mtime winner; hardlink unsupported=`output_publish_unsupported`; lỗi khác=`output_write_failed`; finally unlink temp. Không fallback `os.replace`, không overwrite. Race test barrier/hook, không sleep: đúng một winner, loser không đổi bytes/mtime winner/input.

## Giới hạn còn lại

Không cài/tải dependency, parse PDF, test sản phẩm hay mở corpus trong research. Fixture synthetic chỉ chứng minh contract; không chứng minh safety, OCR, completeness, multilingual/model quality, lab/production hoặc quyền dữ liệu thật.
