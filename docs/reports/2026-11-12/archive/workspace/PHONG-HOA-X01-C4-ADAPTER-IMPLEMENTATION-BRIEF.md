# X01-C4-ADAPTER-NEXT — brief request seam ngoại tuyến (R1–R3)

## Base/target/scope

- Root: `$WORKSPACE`.
- Base: `root\cti-x01-c4-retrieval`, `feat/x01-c4-retrieval-20261111`, `d97f96362edcd92e87fc69cfa20a563109cec550`, clean.
- Target đề xuất: `root\cti-x01-c4-adapter`, `feat/x01-c4-adapter-20261111`; tạo nếu chưa có, không reset/xóa tree lạ.
- Làm request seam C4 fake-offline; không model/network/DB/API/UI/evaluator/reporter/CLI C4/query derivation/asset/dependency mới.

## Allowlist triển khai (7 file)

```text
extractor/phonghoa_extractor/llm_adapter.py
extractor/phonghoa_extractor/ttp_audit.py
extractor/tests/test_llm_adapter.py
extractor/tests/test_ttp_audit.py
docs/prompts/extractor-v1-c4-context.md
docs/adr/0008-x01-c4-offline-request-context.md
docs/PROGRESS.md
```

Không sửa retriever/catalog/grounding/evaluator/reporter/CLI/fixture/pin.

## Contract

1. Giữ `run_extraction` C2/C3. Thêm `run_c4_extraction(*, text, language, tlp, provider, catalog, attack_query, top_k=5, context_budget_bytes=4096)`.
2. C4 report exact str/nonempty/strict UTF-8 ≤1 MiB code point+bytes: invalid `invalid_input`, oversize `input_too_large`; không cắt. Base/language/config → TLP → one `retrieve_techniques` (retriever owns bounds→query→catalog/record→budget errors) → provider safety → generate.
3. Append ProviderRequest C4 + knowledge context/SHA/schema fields default None. Wrapper derives from RetrievalResult context; C2/C3 all None. ScriptedProvider records frozen requests before response. Unsafe provider yields `egress_not_configured`, calls 0.
4. C4 result exact research `attack_context`; C4 success flags all true, fallback last false; iocs/C3 behavior and no raw_iocs. Terminal exception has no fabricated result.
5. `unverified_semantic_items` exact four keys, eligible false. Extend `ttp_audit.py` C4 projection/dataclass only; retain exact key validator, source/quote/catalog/mode/bounds. Wrapper audit 0; composition call exact `audit_techniques(adapter_result=c4_result, source_text=report, catalog=catalog)`.
6. Prompt new version separates untrusted report/knowledge; evidence only report; delimiters are not full injection protection.

## TDD/checks

Write RED then GREEN: C4 request/hash/result shape; C2/C3 compatibility; all error-order/count cases; retry success/exhausted/terminal-attempt-2; zero-match/provenance; separation and public audit composition (knowledge-only not-found/span None, Unicode report matched); no mutation/no egress.

Use `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe` from target, PYTHONPATH target/core+target/extractor. Run scoped `test_llm_adapter.py`, `test_ttp_audit.py`, `test_attack_retrieval.py`, `test_attack_catalog.py`, `test_grounding.py`, Ruff check/format-check and `git diff --check`; direct scripted smoke proves request/calls only. Record commands/exit/count/base/HEAD/status/diff/hash in `root\PHONG-HOA-X01-C4-ADAPTER-RESULT.md` and `root\x01-c4-adapter-evidence\`; local commit only.

ADR 0008 records wrapper/separation/query/deferred scope; PROGRESS only actual checks. UNVERIFIED: model quality/injection resilience, semantic/multilingual TTP, real corpus/evaluator-reporter C4, OpenCTI/lab/production.
