# X01-TTP-EVAL-NEXT — nghiên cứu nối audit vào evaluator

Ngày 11/11/2026. Đây là nghiên cứu/brief, **không phải implementation hay nghiệm thu mới**.

## Câu hỏi và hiện trạng đã kiểm

Có nên đưa kết quả audit TTP ngoại tuyến vào artifact đánh giá C2/C3 để tái lập liên kết document → source/quote/catalog, mà không gọi provider thêm hoặc đổi điểm IOC? Có.

Source chỉ đọc: `cti-x01-ttp-audit`, branch `feat/x01-ttp-audit-20261111`, HEAD `b896ad343a2e9876559649b1182c0a4feeecaaa5`. Tại lúc nghiên cứu, `git status --short` rỗng. `extractor/eval/run.py` gọi `run_extraction` một lần/document và chỉ serialize `raw_audit` (C2) hoặc `grounding_audit` (C3); semantic item bị bỏ khỏi artifact. Một invocation adapter có thể gọi provider 1 lần (completed), 2 lần (retry rồi completed), hoặc 2 lần rồi `regex_fallback`; audit không được thêm provider call. Audit đã được Leader kiểm trực tiếp PASS với 281 checks, nhưng chỉ chứng minh source hash/quote/catalog consistency, không chứng minh ngữ nghĩa TTP, precision/recall/F1 TTP hoặc C4/RAG.

`audit_techniques(adapter_result, source_text, catalog)` là seam đã có: nhận đúng projection `unverified_semantic_items`, dùng SHA-256 UTF-8 của nguyên văn `str`, quote literal với span theo Unicode code point, và `AttackCatalog` đã nạp. Nó trả tuple immutable `TechniqueAudit`; mọi item có `semantic_status="unverified"` và `operational_draft_eligible=false`. `load_catalog(snapshot, SnapshotPin)` đã kiểm pin/hash/provenance và không cần mạng.

## Nguồn và phần tái sử dụng

| Ai/nguồn | Bằng chứng kiểm 11/11/2026 | Dùng lại được | Giới hạn |
|---|---|---|---|
| Phong Hỏa, `ttp_audit.py` + ADR 0005 | API audit/public catalog trên exact HEAD; nghiệm thu Leader 281 checks | Audit fail-closed, quote/span, source hash, output immutable và error-code taxonomy | Không suy luận semantics; không nạp snapshot từ CLI; audit lỗi nếu projection/nguồn lệch |
| Phong Hỏa, `eval/run.py` | C2/C3 có fixture manifest, provider policy, atomic output và alias/hardlink guard | Luồng CLI, deterministic JSON, output-preservation và một adapter invocation/document | Adapter retry có thể gọi provider 2 lần; chưa serialize TTP, pin hoặc catalog provenance |
| MITRE ATT&CK STIX Data v20.1 | Release official v20.1, commit `f59b03e`; pin local hiện có trỏ đúng asset/hash | Pin version, commit, URL, SHA-256 vào artifact để tái lập lookup | Release/catalog hợp lệ không phải nhãn hành vi của document; asset official không được tải trong lát cắt |
| Python standard library `argparse`, `json`, `open`, `dataclasses`, `os.replace` | Tài liệu Python: parser xử lý required/choices; JSON là input không tin cậy cần bound; `open` universal-newline; dataclass không runtime type-check; `os.replace` dùng cho thay thế file | Giữ stdlib, parse cờ rõ ràng, pin strict bounded, hash text đúng reader, JSON atomic hiện hữu | `argparse` tự in usage cho sai syntax; không dùng nó để lộ nội dung CTI |

Nguồn chính thức: [MITRE ATT&CK STIX Data v20.1](https://github.com/mitre-attack/attack-stix-data/releases/tag/v20.1), [Python argparse](https://docs.python.org/3/library/argparse.html), [Python json](https://docs.python.org/3.12/library/json.html), [Python open/newline](https://docs.python.org/3.12/library/functions.html#open), [Python dataclasses](https://docs.python.org/3.12/library/dataclasses.html), [Python os.replace](https://docs.python.org/3/library/os.html#os.replace).

## So sánh phương án

| Phương án | Phần dùng lại | Lợi ích | Khoảng trống/rủi ro | Kết luận |
|---|---|---|---|---|
| A. Opt-in trong evaluator C2/C3 | `run_extraction`, `load_catalog`, `audit_techniques`, atomic writer | Một artifact gắn IOC score hiện có với audit/provenance; không gọi model thêm; C1 mặc định bất biến | Cần contract CLI/pin/output và test guard chặt | **Chọn** |
| B. CLI audit riêng | audit/catalog API | Cô lập, ít sửa evaluator | Hai artifact phải join theo document/hash; người dùng dễ chạy thiếu/lệch input; không đạt mục tiêu quan sát cùng evaluation | Không chọn cho lát cắt này |
| C. Chờ corpus semantic/C4 | spec dataset + tương lai RAG | Có thể tính metric TTP thực | Chưa có gold hai người gán nhãn, C4/RAG; trì hoãn mất traceability vốn đã có | Chỉ làm sau, không phải điều kiện A |

## Khuyến nghị: lát cắt A, điều chỉnh tối thiểu

Tạo tree mới từ exact HEAD: `cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`. Một CTI AI Agent Sol medium thực hiện TDD, không mở rộng provider/model/SQLite/W05/lab. Thay đổi chỉ opt-in C2/C3 bằng bộ cờ cùng xuất hiện:

```text
--ttp-audit --attack-snapshot PATH --attack-pin PATH
```

Không có `--ttp-audit`: root `schema_version="1.0"` và C2/C3 artifact cũ giữ nguyên (khi so checkout khác chỉ loại `evaluator.git_ref`, vì nó phải đổi theo HEAD). C1 tiếp tục không nhận cờ audit; C4 tiếp tục exit 2. Có `--ttp-audit` mà thiếu/thừa/bị dùng với C1/C4 là usage error exit 2, không tạo output. C2/C3 cùng đủ cờ sẽ nạp catalog **một lần** trước vòng document, rồi audit projection của đúng kết quả adapter; không tự fallback qua audit failure. Audit thêm **zero** provider calls: invocation adapter hiện hữu vẫn là 1 call normal, 2 calls retry-completed, hoặc 2 calls retryable-fallback.

### Contract artifact v1.1 (chỉ khi opt-in)

Khi enabled, root `schema_version` là `"1.1"` và top level thêm `ttp_audit`; khi disabled không thêm field mới. `attack_catalog` chỉ là keyword-only optional library parameter `AttackCatalog | None = None` của evaluator: `None` disabled; kiểu sai fail trước provider. Library không đọc file/nạp pin; CLI parse pin và nạp đúng một lần.

```json
{
  "enabled": true,
  "catalog": {
    "kind": "official|synthetic", "version": "...", "sha256": "...",
    "source_url": "string-or-null", "release_tag": "string-or-null",
    "commit": "string-or-null", "provenance": "..."
  },
  "metric_note": "counts only; not TTP precision, recall, F1, or detection rate",
  "counts": {
    "technique_items": 1,
    "quote_status": {"matched": 1, "missing": 0, "not_found": 0, "ambiguous": 0},
    "catalog_status": {"active": 1, "inactive": 0, "unknown": 0, "not_checked": 0}
  }
}
```

Mỗi `documents[]` thêm `ttp_audit` là list giữ đúng thứ tự adapter/index, mỗi item là JSON projection đầy đủ của `TechniqueAudit`: `item_index`, `kind`, `value`, `evidence`, `evidence_span` (array hoặc null), `source_sha256`, `config`, `quote_status`, `catalog_status`, `reason_code`, `pin_kind`, `snapshot_version`, `snapshot_sha256`, `semantic_status`, `operational_draft_eligible`. Không copy toàn source hay thiết lập `keep`; luôn giữ `semantic_status=unverified`, `operational_draft_eligible=false`. `counts` có **chính xác** `technique_items`, `quote_status` (matched/missing/not_found/ambiguous) và `catalog_status` (active/inactive/unknown/not_checked); mọi key là integer >=0 kể cả zero, mỗi map tổng bằng `technique_items`, duplicate tính theo item/index, không dedupe/denominator/rate. Fallback/empty dùng đủ key zero, ví dụ `{"technique_items":0,"quote_status":{"matched":0,"missing":0,"not_found":0,"ambiguous":0},"catalog_status":{"active":0,"inactive":0,"unknown":0,"not_checked":0}}`.

Ví dụ document enabled (rút gọn chỉ ở chỗ không liên quan IOC):

```json
{"schema_version":"1.1","documents":[{"id":"case-01","ttp_audit":[{"item_index":0,"kind":"technique","value":"T1000","evidence":"Đoạn mô tả","evidence_span":[0,12],"source_sha256":"<64-hex>","config":"C2","quote_status":"matched","catalog_status":"active","reason_code":"catalog_active_and_quote_matched","pin_kind":"synthetic","snapshot_version":"synthetic-1","snapshot_sha256":"<64-hex>","semantic_status":"unverified","operational_draft_eligible":false}]}]}
```

Pin được CLI đọc binary tối đa 16 KiB + 1 (vượt bound từ chối trước parse), UTF-8 strict không BOM; JSON root exact dict với đúng **tám** field `kind`, `version`, `sha256`, `source_url`, `release_tag`, `commit`, `provenance`, không duplicate key ở bất kỳ object nào, không NaN/Infinity/-Infinity, không deep/numeric parse failure. Dataclass không tự runtime type-check, nên parser phải xác minh native type: trường base exact `str`; source_url/release_tag/commit chỉ `str|None` tùy loại pin; không bool/number/list/dict, không coerce/trim/default. Public loader mới kiểm enum/shape/hash/provenance/official exact pin. Pin file bytes SHA không thay thế `SnapshotPin.sha256`: trường latter là hash snapshot. Artifact ghi pin/provenance từ `catalog.pin` đã validate. Snapshot/pin là input protected: output không được nằm trong/alias/hardlink/symlink tới dataset, responses, snapshot hoặc pin.

### Tính tương thích và lỗi

- Source audit là **đúng `str` từ `Path.read_text(encoding="utf-8")` đã đưa vào `run_extraction`**. Giữ universal-newline reader hiện tại: CRLF và CR được dịch sang LF trước adapter/audit; không đổi sang `newline=''` và không thêm NFC/NFD/defang normalize. `source.sha256`/audit hash là SHA-256 của `text.encode("utf-8", errors="strict")`, span là index code point của `str` sau đọc. Đây không phải raw-file hash; `dataset_sha256` hiện hữu vẫn hash raw bytes/path dataset.
- Asset/pin thiếu, JSON sai, pin/provenance/hash/snapshot lỗi, `TtpAuditError`, NUL/path I/O hay source mismatch đều là `offline_eval_failed`, exit 1; stderr không được echo text CTI, contents pin/snapshot hoặc traceback. Output cũ giữ nguyên vì toàn bộ work hoàn tất trước `_write_json_atomic`.
- `result_mode=regex_fallback` hợp lệ và có `ttp_audit=[]`; adapter fallback vốn phải không có semantic items. Empty semantic list cũng hợp lệ. Mixed malware/actor chỉ bị audit bỏ qua theo API (không phải lỗi hoặc success của technique); duplicate technique giữ nguyên index/order, không dedupe thêm. Nonretryable/refusal theo policy adapter cũ phải abort/no output; comparison audit on/off giữ attempts/error_codes/result_mode/prediction/IOC score.
- Không có network, dependency, database, provider/model attempt hay write nào ngoài output atomic. `--attack-snapshot`/`--attack-pin` là path option đầy đủ, không có default asset hay download.

## Giới hạn còn lại

Chưa chạy implementation/test trong research này. Artifact mới không là bằng chứng semantic truth, gold TTP, F1/precision/recall TTP, model thật, C4/RAG, chống injection hay quyền ghi draft. Official ATT&CK v20.1 asset được Leader kiểm ở lát cắt trước nhưng không nằm trong repo; implementation phải dùng fixture local/public loader để test và chỉ demo official khi asset pin đã có sẵn.
