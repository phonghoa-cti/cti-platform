# X01-C4 — adapter context ATT&CK ngoại tuyến: research/contract R1–R3

Ngày đối chiếu: 11/11/2026. Chỉ research/brief; không triển khai/test C4 hay claim model quality.

## Hiện trạng và nguồn

Source read-only `cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, HEAD `d97f96362edcd92e87fc69cfa20a563109cec550`, sạch trước rework. `retrieve_techniques()` đã trả `RetrievalResult.context` có budget/provenance. `llm_adapter.py` có C2/C3, retry hai lần và fallback regex; `grounding.py` chỉ dùng report. `audit_techniques(*, adapter_result, source_text, catalog)` audit quote/span report và catalog hậu generation.

| Nguồn | Dùng được | Giới hạn |
|---|---|---|
| [MITRE ATT&CK STIX USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md) | STIX local/versioned, không drift và không Internet sau asset ban đầu. | Không chứng minh RAG/semantic TTP. |
| [Lewis et al., RAG](https://arxiv.org/abs/2005.11401) | Retrieval phải condition generation; provenance cần explicit. | Không chứng minh lexical/multilingual của dự án. |
| [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) | Governance provenance, testing rủi ro GAI. | Không giải quyết prompt injection/model quality. |

Chọn wrapper C4 + request seam: giữ C2/C3 nguyên vẹn, tách knowledge/report và dùng retry/fallback chung. Loại ghép knowledge vào source vì hỏng source hash/evidence; hoãn derive query và evaluator/CLI C4.

## Contract C4 chính xác

Thêm `run_c4_extraction(*, text, language, tlp, provider, catalog, attack_query, top_k=5, context_budget_bytes=4096)`. `run_extraction` C2/C3 không đổi signature/artifact/behavior.

Report C4: exact `str`, non-empty, UTF-8 strict, tối đa 1 MiB cả code point và byte; sai type/empty/surrogate → `AdapterError("invalid_input")`, quá lớn → `AdapterError("input_too_large")`; không cắt. Sau base input/language/config và TLP, gọi `retrieve_techniques` đúng một lần. Retriever giữ thứ tự **bounds → query → catalog/record → budget**, với `invalid_bounds`, `invalid_query`, `invalid_catalog`, `invalid_record`, `context_budget_exceeded`; không copy tokenizer/STIX parser. Query explicit, không derive report: valid token, ≤512 code point/4096 UTF-8 bytes; bounds exact int, không bool, top-k 1..10/budget 256..8192. Zero match hợp lệ nếu envelope vừa budget.

Nới cuối `ProviderRequest`:

```text
config: Literal["C2", "C3", "C4"]
knowledge_context: str | None = None
knowledge_context_sha256: str | None = None
knowledge_schema_version: str | None = None
```

Wrapper tự build ba field từ `RetrievalResult.context`; C2/C3 cả ba None. Không `__post_init__`, không caller context/hash. `ScriptedProvider` append frozen request vào `requests` trước response và giữ `calls`. Provider safety sau retrieval/trước generate: thiếu/sai attribute/name UTF-8/destination/egress → `egress_not_configured`, calls 0. Base/TLP error: retrieval 0/provider 0; retrieval error: 1/0; provider safety: 1/0.

Knowledge ATT&CK là prompt-untrusted, không phải evidence. Prompt `extractor-v1-c4-context-v1` tách report/knowledge; chỉ report tạo evidence. Không đưa context vào grounding, quote/span, source hash hoặc audit source. Wrapper audit 0 lần; caller/demo gọi public `audit_techniques(adapter_result=c4_result, source_text=report, catalog=catalog)` sau wrapper.

Mở tối thiểu C4 trong audit projection/dataclass để nhận C4, giữ source hash, exact four item keys, quote/catalog/bounds/mode. `unverified_semantic_items` luôn exact: `kind`, `value`, `evidence`, `operational_draft_eligible=False`; không thêm `semantic_status`. `TechniqueAudit` vẫn `semantic_status="unverified"`, eligible false.

## Result/lifecycle

C4 root giữ shape library: schema 1.0, config C4, prompt version mới, purpose grounded-candidate, source SHA report UTF-8, provider/attempts/mode/mock/errors. C4 dùng `iocs` theo C3; không `raw_iocs`. Top-level eligible chỉ cho IOC candidate, không semantic/DB/publish.

Chỉ C4 thêm `attack_context` exact keys/types:

```text
requested: bool; retrieval_completed: bool; provider_context_sent: bool;
c4_adapter_completed: bool; schema_version: str; sha256: str;
byte_length: int; top_k: int; budget_bytes: int;
snapshot: {version: str, sha256: str, kind: "synthetic"|"official",
           source_url: str|None, release_tag: str|None, commit: str|None}
```

No query/raw context in result. Any returned result had retrieval + generate: first three flags true; `c4_adapter_completed` true only `model_completed`, false `regex_fallback`. It proves fake pipeline completion, not model understanding. Terminal refusal/incomplete/nonretryable error raises, no success result.

One retrieval/frozen request, max two generate calls: first success 1; retry-success 2; two retryable → fallback 2; terminal first 1; retry then terminal second 2/no fallback. No re-retrieval/audit. Fallback has mode regex_fallback, model items false/empty, last completion flag false.

## Test matrix

| Nhóm | Bằng chứng |
|---|---|
| Compatibility | C2/C3 fields None/artifacts unchanged; C4 exact fields. |
| Error order | invalid/oversize report, TLP, bounds/query/catalog/record/budget, unsafe provider; count retrieval/provider đúng. |
| Separation/audit | recorded context only; report-only source/grounding/audit; knowledge-only quote not found/span None; Unicode report quote matched; C2/C3 audit and extra-key rejection giữ nguyên. |
| Lifecycle | Success/retry/fallback/terminal-attempt-2 counts; no re-retrieval/audit; exact metadata. |
| Safety | no mutation/egress/DB/listener; fake proves request/calls only. |

UNVERIFIED: semantic/multilingual recall, model/injection resilience, corpus/evaluator-reporter C4, OpenCTI/lab/production.
