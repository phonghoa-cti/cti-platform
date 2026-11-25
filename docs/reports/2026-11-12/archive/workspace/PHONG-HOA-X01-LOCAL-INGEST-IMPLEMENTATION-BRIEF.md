# Brief triển khai — X01 local ingest

Trạng thái: Leader cần nghiệm thu research trước khi giao code. Brief này không xác nhận implementation/test.

## Task packet bất biến

Tree mới: `$WORKSPACE\cti-x01-ingest-local`; branch `feat/x01-ingest-local-20261111`; base `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`. Kiểm HEAD/status sạch trước/sau. Bootstrap target duy nhất: `$WORKSPACE\cti-x01-ingest-local\.venv\Scripts\python.exe`; tạo venv trong tree mới, không PATH/cài source readonly.

Mục tiêu: nạp `.txt` UTF-8 strict hoặc PDF lớp text local, tạo envelope pending bao quanh draft C1 không đổi shape. Không sửa C1–C4/CLI cũ, SQLite/W05, HTTP/UI, URL/network, model, OCR, decrypt, JavaScript/attachment, converter ngoài, corpus thật, RUNS/review. Không commit/push/PR/merge/deploy.

## Allowlist và dependency record

* `extractor/phonghoa_extractor/local_ingest.py`; `extractor/ingest/run.py`; `extractor/ingest/pdf_child.py` (child Python duy nhất, không public API).
* `extractor/requirements-local-ingest.in`: `pypdf==7.0.1`. `extractor/requirements-local-ingest.lock`: cùng pin với hash wheel `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`, sdist `0a78bb99efb41e9088260e9a8e5da134a5cbb9a322014744177bf29b5267ea6d`, comment URL/BSD-3-Clause/`>=3.10`.
* `extractor/tests/test_local_ingest.py`, `extractor/tests/test_ingest_cli.py`.
* `extractor/tests/fixtures/local_ingest/README.md` plus synthetic fixed `text-crlf.txt`, `text-bom.txt`, `text-vi-emoji.txt`, `two-text-pages.pdf`, `blank-middle-page.pdf`, `all-whitespace-pages.pdf`, `encrypted.pdf`, `malformed.pdf`.
* `docs/research/X01-local-ingest-dependency-20261111.md`: URL/version/license/metadata hashes/date; ghi rõ chưa download/install/verify bytes. `docs/PROGRESS.md` chỉ sau test thật.

Ngoài allowlist: dừng, báo Leader compatibility impact. Không sửa `draft/run.py`, `drafts.py`, `evidence.py`, `grounding.py`, C1–C4/gold fixtures. Không ADR; nếu owner cần ADR, xin brief mới.

## API, child và error contract

```python
@dataclass(frozen=True)
class IngestLimits:
    max_raw_bytes: int = 8 * 1024 * 1024
    max_pages: int = 50
    max_page_codepoints: int = 100_000
    max_total_codepoints: int = 1_000_000
    pdf_timeout_seconds: int = 15
    max_child_result_bytes: int = 16 * 1024 * 1024

@dataclass(frozen=True)
class IngestedDocument:
    format: Literal["text", "pdf"]
    display_name: str
    raw_sha256: str
    raw_bytes: int
    canonical_text: str
    canonical_text_sha256: str
    page_count: int | None
    page_text_ranges: tuple[tuple[int, int], ...] | None

class LocalIngestError(ValueError): code: str
def ingest_local_file(path: Path, *, limits: IngestLimits = IngestLimits()) -> IngestedDocument: ...
```

Cap fields must be `type(value) is int` (bool invalid), each `1..default hard maximum`: only smaller caller values legal. `display_name=path.name` after reject NUL/control/slash/backslash; errors only stable code.

Read raw capped/hash raw. Text `decode("utf-8", "strict")`, preserving BOM/CRLF/CR. PDF parent checks extension/magic/dependency then starts exactly one child with paths/fixed limits. Child owns `PdfReader`, `is_encrypted`, page count/extract; no stdin/network/external converter. Parent result file only, no stdout/stderr capture; waits 15 s whole child then terminate→reap <=2 s→kill→reap <=2 s and always cleans up.

Child: 0 page=`pdf_malformed`; encrypted=`pdf_encrypted`; >50=`pdf_page_limit`; page non-exact-str/not UTF-8 encodable=`pdf_malformed`; page >100k=`pdf_page_text_limit`; running page lengths plus 3×separator count >1m=`pdf_total_text_limit`; no page with non-whitespace=`pdf_no_extractable_text`. Do not modify text. Join valid pages exact `"\n\f\n"`; ranges page only, empty `[n,n]`, separators excluded. Text is not complete PDF proof/byte/coordinate.

Error order: `input_missing`, `input_not_regular`, `unsupported_type`, `input_too_large`; then `invalid_utf8` or `pdf_support_unavailable`, `not_pdf`; child `pdf_malformed`, `pdf_encrypted`, `pdf_page_limit`, `pdf_page_text_limit`, `pdf_total_text_limit`, `pdf_no_extractable_text`, `pdf_child_timeout`, `pdf_child_result_too_large`, `pdf_child_invalid_result`, `pdf_child_failed`; then `unsafe_output_path`, `output_parent_invalid`, `output_exists`, `output_publish_unsupported`, `output_write_failed`.

## CLI/envelope/no-clobber

New only: `python extractor/ingest/run.py --input INPUT --output OUTPUT --language {vi,en} [--tlp TLP:AMBER]`. Call ingest then exact existing `build_regex_draft(document.canonical_text, source=document.display_name, ...)`.

```json
{"schema_version":"x01-local-ingest/1.0","input":{"format":"text|pdf","display_name":"report.pdf","raw_sha256":"lowercase-64-hex","raw_bytes":1,"canonical_text_sha256":"lowercase-64-hex","page_count":1,"page_text_ranges":[[0,12]]},"draft":{"existing C1 object":"unchanged shape"}}
```

UTF-8 deterministic JSON `sort_keys=True`, final LF. Text page fields null. `draft.text==canonical_text`; `draft.source.name==display_name`; `draft.source.sha256==canonical_text_sha256`; default AMBER. stdout only `{"schema_version", "format", "output_created"}`, stderr `Lỗi: <code>`, exit 0/1/2. No content/hash/path/IOC logs.

Output parent must exist directory. Reject lexical/resolved and existing samefile/hardlink aliases to input. Serialize private temp same parent, flush+fsync, publish only `os.link(temp, output)`. Never `os.replace`/fallback/overwrite. Existing target=`output_exists` and winner bytes/mtime stay; unsupported link=`output_publish_unsupported`; other=`output_write_failed`; finally unlink temp. Ordinary two-writer race is closed, hostile FS mutation is not.

## TDD, checks, output evidence

Write red tests first; fixture README says synthetic/no real CTI or gold. Required: text CRLF/CR/LF/BOM/vi/emoji hashes/spans and C1 old regression; PDF two pages/blank middle exact join/ranges; 0-page/whitespace/malformed/encrypted/magic/caps; child timeout/oversize-invalid-missing result/reap cleanup; alias/invalid parent/link failure; barrier/hook race one winner/no sleep; injection gives pending/AMBER/no model-network-OCR-decrypt-converter. Do not claim child is RAM/network sandbox.

Proposed, not-run commands:

```powershell
$WORKSPACE\cti-x01-ingest-local\.venv\Scripts\python.exe -m pip install --require-hashes -r extractor\requirements-local-ingest.lock
$WORKSPACE\cti-x01-ingest-local\.venv\Scripts\python.exe -m pytest extractor/tests/test_local_ingest.py extractor/tests/test_ingest_cli.py extractor/tests/test_drafts.py extractor/tests/test_draft_cli.py extractor/tests/test_grounding.py -q
$WORKSPACE\cti-x01-ingest-local\.venv\Scripts\python.exe -m ruff check extractor/phonghoa_extractor/local_ingest.py extractor/ingest/run.py extractor/ingest/pdf_child.py extractor/tests/test_local_ingest.py extractor/tests/test_ingest_cli.py
$WORKSPACE\cti-x01-ingest-local\.venv\Scripts\python.exe -m ruff format --check extractor/phonghoa_extractor/local_ingest.py extractor/ingest/run.py extractor/ingest/pdf_child.py extractor/tests/test_local_ingest.py extractor/tests/test_ingest_cli.py
git diff --check
git status --short
```

Demo synthetic text/PDF twice to fresh outputs, compare JSON bytes and input hashes. Report `PHONG-HOA-X01-LOCAL-INGEST-RESULT.md`; evidence `x01-local-ingest-evidence/`: `commands.md`, `head-status.txt`, `diff-check.txt`, `input-output-sha256.txt`, `txt-output.json`, `pdf-output.json`, `race-result.json`, `timeout-cleanup.json`, `dependency-provenance.md`. Do not claim until real run produces them.

UNVERIFIED: hostile mutation, hard RAM/network isolation Windows, adversarial PDF safety, real PDF/corpus quality, OCR, cloud/model/lab/production.
