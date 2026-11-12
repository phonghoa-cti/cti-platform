# X01-C4 — retrieval ATT&CK ngoại tuyến: nghiên cứu và quyết định

Ngày đối chiếu: 11/11/2026 (Asia/Saigon). Chỉ research/contract; **không triển khai, không chạy test mới, không phải C4 hoàn thành**.

## Hiện trạng đã kiểm

Source read-only `cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`, HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`, sạch. `attack_catalog.py` đã hash/pin snapshot, canonicalize version/parent/lifecycle và trả catalog immutable; `TechniqueRecord` constructor công khai hiện chưa có description. `ttp_audit.py` chỉ bind quote report và lookup ID *sau* generation; mọi kết quả `semantic_status="unverified"`, `operational_draft_eligible=false`.

Leader inventory read-only asset local Enterprise v20.1: SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`, 55,277,605 bytes; 867 Enterprise record/706 active; description của asset hiện tại đều string không rỗng, lớn nhất 4,680 bytes UTF-8. Đây là inventory JSON, không phải loader/retriever test và không bảo đảm release sau.

Theo Lewis et al., RAG phải đưa bộ nhớ truy hồi vào generation; lookup/audit sau generation không là RAG. MITRE phát hành ATT&CK STIX để dùng machine-readable và ghi bản local versioned giúp workflow không đổi theo catalog.

## Đối chiếu và lựa chọn

| Cách | Nguồn gốc đã đọc | Tái dùng | Giới hạn | Quyết định |
|---|---|---|---|---|
| A. Exact-ID/post-generation audit | `attack_catalog.py`, `ttp_audit.py` | pin/hash, lifecycle/parent, audit quote | không có query/context trước generation | Giữ safety gate, không là C4 |
| B. Lexical local deterministic, name + description | MITRE STIX/USAGE; Lewis et al. | canonical loader, stdlib Unicode, immutable provenance | không hiểu đồng nghĩa Việt–Anh; chưa có quality metric | **Chọn component đầu tiên** |
| C. Embedding/vector semantic | Sentence Transformers semantic-search docs | `encode_query`/`encode_document`, cosine/top-k làm tham khảo | dependency/model weights/nguồn gốc, multilingual benchmark, memory và reproducibility chưa chốt | Hoãn, không cài/tải/gọi mạng |

Nguồn chính đã đọc 11/11/2026: [MITRE Data & Tools](https://attack.mitre.org/resources/attack-data-and-tools/), [MITRE USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md), [Lewis et al.](https://arxiv.org/abs/2005.11401), [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html). Chúng chỉ hỗ trợ khả năng/cách tiếp cận, không chứng minh lexical overlap có chất lượng TTP.

## Contract dữ liệu và trust boundary

Mở rộng đúng canonical parser của `attack_catalog.py`: `TechniqueRecord.description: str | None = None` ở cuối dataclass. Giá trị present hợp lệ lấy từ attack-pattern canonical đã chọn; missing/empty biểu diễn `None`, nên builder/fixture/pin cũ vẫn hợp lệ và record vẫn truy hồi theo ID/name. Present sai type, UTF-8 không encode được (surrogate), hoặc vượt 32 KiB UTF-8 fail-closed bằng finite loader error đã tài liệu hoá. Không có parser STIX thứ hai, không sửa pin/fixture cũ để ép description.

`AttackCatalog` là internal input expected từ `load_catalog()` đã hash/pin; `isinstance`/exact type chỉ là guard API, **không** chứng minh object caller tự dựng có provenance MITRE. Retriever không đọc file, socket, DB, provider, URL hay model. Nó duyệt duy nhất `catalog.records_by_external_id`; chỉ record active (`revoked=False`, `deprecated=False`) được candidate, nên lifecycle/canonical/parent policy của loader không có bypass.

Raw ATT&CK name/description là knowledge, không phải report evidence. URL/citation/prompt-like text trong description chỉ là inert string. Không thực thi/fetch/diễn giải như chỉ thị. Context lexical không thay đổi audit/grounding/TLP/human review; mọi result công khai vẫn unverified/not eligible. C4 CLI tiếp tục reject; component này chưa gắn context vào generation.

## Lexical contract chính xác

Private tokenizer dùng trên query lẫn document search view: đầu tiên `unicodedata.normalize("NFKC", value).casefold()`, sau đó `re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)`. Token giữ nguyên sequence Unicode sau NFKC/casefold, chỉ nhận length 2..64 code points; token 1 hoặc >64 bị bỏ, không cắt. Dấu gạch, `_`, `.` là delimiter: `T1566.002` thành `t1566`, `002`; không dịch, bỏ dấu, stemming hoặc synonym expansion. Vietnamese NFC/NFD được NFKC xử lý; emoji/CRLF không phải token.

Document search view là `external_id + "\n" + name + "\n" + (description or "") + "\n" + " ".join(parent_external_ids)`. Ranking score = `len(unique(query_tokens) ∩ unique(document_tokens)) / len(unique(query_tokens))`; chỉ score > 0 là match. Nó là baseline do dự án chọn, **không** là confidence/probability/semantic truth. Sort `(-score, external_id ASCII)`, top-k exact `int` 1..10 (default 5). Empty/whitespace/tokenless query là `invalid_query`; query max 512 code points và 4 KiB UTF-8.

Parent/sub-technique là record riêng; không tự dedupe theo parent. Duplicate query token không đổi score/result. Zero match thành result rỗng hợp lệ, không network fallback.

## Public context và byte budget

Retriever phải trả raw immutable records *và* context public đã đo. Context is UTF-8 JSON compact (`ensure_ascii=False`, separators `(',', ':')`) của envelope sau, field order cố định và không bao giờ chứa query:

```json
{"schema_version":"1.0","snapshot":{"version":"…","sha256":"…","kind":"official","source_url":"…","release_tag":"…","commit":"…"},"techniques":[{"id":"T…","name":"…","snippet":"…","snippet_truncated":false,"modified":"…","parents":["T…"]}]}
```

Schema order là `schema_version`, `snapshot`, `techniques`; snapshot order `version`, `sha256`, `kind`, `source_url`, `release_tag`, `commit`; item order `id`, `name`, `snippet`, `snippet_truncated`, `modified`, `parents`. JSON escaping mặc định Python `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`, encoded strict UTF-8; length bytes của **whole returned context** là budget measurement. `context_budget_bytes` exact `int` 256..8192 (default 4096). Raw description ở result không bị cắt; chỉ `snippet` context được cắt ở UTF-8 boundary. `snippet_truncated` là generated metadata, không phải ATT&CK.

Xét candidate theo rank. Thêm whole item nếu whole envelope còn vừa. Với candidate đầu tiên, nếu full item không vừa, chỉ được shorten `snippet`; ID/name/modified/parents/snapshot bắt buộc còn nguyên. Nếu empty envelope hoặc mandatory metadata/item không vừa budget, raise `context_budget_exceeded`, không vượt budget và không giả zero-match. Sau item đầu, item kế không vừa thì dừng, không cắt/skip để đảo rank. Zero match trả envelope techniques rỗng nếu vừa; nếu envelope không vừa thì cùng error. Boundary tests bắt buộc: 256 min, exact fit, one-byte short, multibyte, JSON quote/backslash/control escape, name dài/provenance official dài, raw record bất biến.

## Phần giữ nguyên và chưa xác minh

| Dùng lại | Không đổi | Việc sau riêng |
|---|---|---|
| `SnapshotPin`, catalog hash/canonical/parent/lifecycle, pin v20.1 | C1–C3/evaluator/reporter, adapter, `ttp_audit`, CLI C4 reject, fixture/pin cũ | Leader chọn lát tiếp trong phạm vi đã giao: đường C4 context trước generation; model thật/lab/phát hành vẫn ngoài phạm vi |

UNVERIFIED: implementation/test này; license/NOTICE distribution; semantic/multilingual recall-TTP; model/context quality; semantic retriever; performance/memory; corpus/model/network/cloud, W05/OpenCTI/UI/lab/production. Không suy ra không có giải pháp khác chỉ từ ba cách trên.
