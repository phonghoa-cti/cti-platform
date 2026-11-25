# X01-EVAL-REPORT-NEXT — nghiên cứu reporter offline

Ngày 11/11/2026. Đây là research/contract, không phải implementation hay bằng chứng test reporter.

## Kết luận

Giữ phương án A: `extractor/eval/report.py` **stdlib-only**, đọc cohort artifact JSON C1/C2/C3 tương thích và xuất Markdown byte-deterministic. Không sửa evaluator/score/artifact, không gọi model/network/catalog/DB. Header bắt buộc: `SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật`.

Reporter chỉ trình bày IOC metrics đã tồn tại. C3 phải ghi `grounded model candidates + regex; not model-only`; audit TTP chỉ là counts nhất quán source/quote/catalog, không P/R/F1/detection rate/semantic truth/C4.

## Hiện trạng exact base

Đã đọc source read-only `cti-x01-ttp-eval` tại `984bd2136872f4c5fba4118e33cf02b5ca615f2d`, branch `feat/x01-ttp-eval-20261111`: `run.py:229-241,362-494,497-519,522-607`, `evaluate.py:16-32,63-65`, README evaluator. Inventory artifact C1 và demo C2/C3 audit xác nhận mỗi artifact 6 documents; C1 document **không có `config`**.

| Artifact | Root projection exact được dùng | Document envelope exact được dùng | Không render/không chấm lại |
|---|---|---|---|
| C1 1.0 | `schema_version,config,purpose,dataset_sha256,document_count,documents,micro,by_type,ttp` | `id,language,prediction,score,source` | values/payload prediction, source path/hash ngoài hash artifact |
| C2/C3 1.0 | C1-common thay `micro` bằng `fixture_manifest_sha256,provider_policy,mock_only,evaluator,micro_all,micro_by_result_mode,limitations`; không `ttp` | `id,config,language,tlp,source,fixture,adapter_schema_version,provider,attempts,result_mode,error_codes,model_items_used,operational_draft_eligible,prediction_basis,prediction,score` + C2 `raw_audit` / C3 `grounding_audit` | prediction, raw/grounding audit, source/fixture path/value/quote |
| C2/C3 1.1 | exact C2/C3 1.0 + `ttp_audit` | exact 1.0 + `ttp_audit` list | technique evidence/quote/id/name; semantic interpretation |

“Exact” ở đây là envelope/projection mà reporter dùng. Payload lồng không được trình bày (`prediction`, C2 `raw_audit`, C3 `grounding_audit`) chỉ kiểm kiểu, bound và depth để đọc an toàn; reporter không tái kiểm extractor/grounding hay tuyên bố strict semantic cho payload ấy.

`Score` source quy định P/R/F1 = `0.0` khi denominator zero. C1 dùng `micro`; C2/C3 dùng `micro_all`, partition `model_completed`/`regex_fallback` (rỗng = `status=not_available`). 1.1 thêm `ttp_audit` catalog + counts. C4 CLI hiện trả unsupported.

## Reuse và nguồn chính thức

| Nguồn | Dùng lại | Khoảng trống |
|---|---|---|
| Python [`json`](https://docs.python.org/3/library/json.html) | `object_pairs_hook`, `parse_constant`, strict `allow_nan=False`, `sort_keys` | Stdlib không tự bound/depth/duplicate policy; reporter phải làm |
| Python [`os.replace`](https://docs.python.org/3.12/library/os.html#os.replace) và [`os.link`](https://docs.python.org/3.12/library/os.html#os.link) | replace atomic khi overwrite; hard-link publish no-clobber cùng filesystem | không khẳng định chống crash/hostile directory mutation |
| [GFM autolinks](https://github.github.com/gfm/#autolinks-extension-) và [raw HTML](https://github.github.com/gfm/#raw-html) | cho thấy pipe escaping không đủ | dùng vocabulary/grammar, không render text tùy ý |

Không cần tabulate/rich/pandas: thêm dependency/license/format drift nhưng không tăng giá trị cho ba config. Không đưa render vào evaluator vì sẽ đổi producer/baseline.

## Contract quyết định

### Bounds và validation projection

- Tối đa 3 input, mỗi file regular tồn tại, ≤1,048,576 bytes (đọc `MAX_BYTES + 1`), UTF-8 strict không BOM; JSON depth ≤64, object ≤64 key, array ≤512 item, string ≤8,192 Unicode code point, document ≤256. `parse_int` từ chối literal >19 chữ số; int 0..`9_223_372_036_854_775_807`; float finite 0..1 cho metrics.
- Reject duplicate key, `NaN`/`Infinity`, root/keyset sai, schema ngoài `1.0/1.1`, config ngoài C1/C2/C3, purpose khác `synthetic-smoke`, SHA-256 không phải 64 lower-hex. Chỉ fields định danh bắt buộc nonempty; nested payload có thể empty khi contract evaluator cho phép.
- `document_count == len(documents)`; ID string nonempty/unique. C1 document không có `config`; C2/C3 document `config == root.config`. Aggregate TP/FP/FN bằng tổng score documents. `micro`/`micro_all` và mỗi mode score phải khớp TP/FP/FN partition; mode `not_available` **iff** partition rỗng. Validate P/R/F1 theo `Score`, gồm denominator zero = 0.0, tolerance `1e-12`; không “sửa” số artifact. Không suy per-type thành micro.
- 1.1: mọi document audit item chỉ chấp nhận enum quote/catalog đã có, `semantic_status=unverified`, `operational_draft_eligible=false`; `technique_items`, từng quote/catalog count top-level bằng thống kê item document. Đây là consistency check, không semantic TTP.

### Cohort/provenance

Mỗi run 1–3 artifact, one each C1/C2/C3, cùng schema, purpose, dataset SHA, document count. C2/C3 còn phải cùng fixture-manifest SHA, provider policy fake_offline, mock-only, evaluator git ref/Python; 1.1 còn entire catalog projection. C1+C2/C3 chỉ schema 1.0 nếu common fields khớp; report in `không có trong schema C1` cho evaluator/provider/fixture, không suy luận model/prompt. Reject 1.0+1.1, C1 1.1, C4, duplicate config/mismatch.

Provenance Markdown gồm schema/config/count, dataset/fixture/evaluator/catalog khi tồn tại và **SHA-256 bytes của từng input artifact đã đọc**; không filename, path, URL, quote hay IOC. P/R/F1 in fixed 6 decimals, counts decimal integer, hash/ref in validated code literal.

### Markdown grammar và rendering

Mọi field không thuộc vocabulary đóng bị reject hoặc không render. Config `C1/C2/C3`; mode `model_completed/regex_fallback/not_available`; statuses/enums exact evaluator; hash `[0-9a-f]{64}`; git ref `[0-9a-f]{40}`; Python `\d+\.\d+\.\d+`; known limitation mapping literal. Version synthetic chỉ `[A-Za-z0-9._-]{1,64}` và render code literal sau validation. Không render raw label, URL, HTML/entity, quote, IOC, path, ID hay free-text limitation.

Output deterministic: title → warning → provenance → IOC aggregate → mode → by-type → conditional TTP counts → fixed limitations → format footer. Cấu hình C1/C2/C3, mode và statuses theo thứ tự cố định; IOC type lexical. Nếu field admissible cần cell, escape `\\`, `|`, CR/LF/control và HTML-significant `<`, `>`, `&`; backtick không nhận từ input. Test literal/reject `[x](url)`, `![x](url)`, bare URL, `<img>`, entity, backtick, pipe/newline/control.

### Path/publish/error

Input `resolve(strict=True)` rồi require regular file. Output mới được phép; resolve parent existing nearest ancestor + lexical child, sau validation mới `mkdir`. Cấm output directory/samefile/alias resolved hoặc lexical của input; **cho phép sibling tên khác** cạnh JSON input. Không-overwrite: temp same parent, sau fsync/close publish bằng `os.link(temp, output)`; `FileExistsError` là conflict exit 2, không fallback `replace`. `--overwrite` mới dùng `os.replace(temp, output)` sau alias check. Commit point là link/replace thành công; cleanup temp best-effort. Lỗi cleanup sau commit chỉ report I/O, không hứa rollback output đã publish. Scope local filesystem; crash durability/hostile concurrent directory mutation UNVERIFIED.

Validation hoàn tất trước khi tạo parent/temp. Parse/schema/cohort/path/output-exists/race conflict: stderr exact `Lỗi: eval_report_invalid_input`, exit 2. Missing/unreadable input và temp/write/publish I/O: `Lỗi: eval_report_io_failed`, exit 1. Argparse override `error()` để generic stderr/no token/path, exit 2; `--help` exit 0. Thành công stdout JSON one-line và exit 0.

## R1–R4 đã đóng trong tài liệu

| Review | Đóng tại |
|---|---|
| R1 C1 envelope/projection/bounds | Hiện trạng exact base; Contract → Bounds |
| R2 denominator/aggregate/mode/TTP/hash/format | Contract → Bounds; Cohort/provenance |
| R3 grammar literal, link/HTML | Contract → Markdown grammar |
| R4 output/sibling/no-clobber/commit/errors | Contract → Path/publish/error |

## Chưa xác minh

Không có `report.py` hay test mới đã chạy. Synthetic smoke/fake_offline không chứng minh model/corpus thật, TTP semantics, C4/RAG, latency/cost, W05/OpenCTI/lab/production.
