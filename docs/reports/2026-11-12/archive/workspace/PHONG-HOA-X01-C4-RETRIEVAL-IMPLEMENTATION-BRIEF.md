# X01-C4 — brief triển khai `attack_retrieval` offline

Ngày 11/11/2026. Contract cho một CTI AI Agent/Sol medium, chỉ dùng sau Leader nghiệm thu. Không phải yêu cầu chạy ngay, không phải full C4/RAG.

## Base, target và ranh giới

- Base: `$WORKSPACE\cti-x01-eval-report`, HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`, branch `feat/x01-eval-report-20261111`.
- Target: `$WORKSPACE\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`.
- Interpreter: `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe` with `-X utf8 -B`.
- Mục tiêu: component lexical offline trả provenance-preserving ATT&CK context trước *một generation tương lai*. Không nối generator, adapter/evaluator/reporter, C4 CLI, database, network/model/package/snapshot download, API/UI/OpenCTI/lab. C1–C3 và C4 CLI reject giữ nguyên.

## File scope

Được sửa/thêm: `extractor/phonghoa_extractor/attack_catalog.py`; mới `extractor/phonghoa_extractor/attack_retrieval.py`; `extractor/tests/test_attack_catalog.py`; mới `extractor/tests/test_attack_retrieval.py`; `extractor/tests/test_attack_catalog_official.py`; một ADR tại `docs/adr/`; `docs/PROGRESS.md`. Không sửa adapter/evaluator/reporter/CLI/grounding/audit hay pinned fixture/pin/hash cũ. Fixture tổng hợp mới chỉ được thêm trong test retrieval nếu thực sự cần, không đổi fixture hiện có.

## Public API bắt buộc

```python
@dataclass(frozen=True)
class RetrievedTechnique:
    external_id: str
    name: str
    description: str | None
    modified: str
    parent_external_ids: tuple[str, ...]
    ranking_score: float
    snapshot_version: str
    snapshot_sha256: str
    pin_kind: Literal["synthetic", "official"]
    source_url: str | None
    release_tag: str | None
    commit: str | None
    semantic_status: Literal["unverified"] = "unverified"
    operational_draft_eligible: Literal[False] = False

@dataclass(frozen=True)
class RetrievalResult:
    query: str
    top_k: int
    context_budget_bytes: int
    context: str
    snapshot_version: str
    snapshot_sha256: str
    results: tuple[RetrievedTechnique, ...]

class AttackRetrievalError(ValueError):
    # code-only str/repr: invalid_catalog | invalid_query | invalid_bounds |
    # invalid_record | context_budget_exceeded

def retrieve_techniques(catalog: AttackCatalog, query: str, *, top_k: int = 5,
                        context_budget_bytes: int = 4096) -> RetrievalResult: ...
```

`TechniqueRecord.description: str | None = None` ở cuối record dataclass. Canonical parser converts missing/empty description to `None`; present non-string/unencodable/over-32KiB fields fail finite loader error. Existing manual builders/fixtures remain valid. `AttackCatalog` type guard is not a claim of provenance: only `load_catalog()` validates snapshot hash/pin; caller-built object may only be an internal test/input.

Use exact tokenizer/search-view/ranking and public JSON context schema in Research sections “Lexical contract chính xác” and “Public context và byte budget”. Context must encode strict UTF-8 and `len(result.context.encode("utf-8")) <= context_budget_bytes`; fixed serializer is part of API, no hidden implementation choice. Results copy scalars/tuples only; no mutable map/raw STIX is returned. `description` is raw knowledge, never report evidence; fixed semantics/eligibility fields are required on every result.

## TDD acceptance matrix

Write focused RED tests before implementation, then GREEN minimum code. No test may network/download.

| Group | Required proof |
|---|---|
| Compatibility seam | Old `TechniqueRecord` builder without description works; missing/empty -> `None`; malformed/surrogate/>32KiB present description finite fail; canonical newest/duplicate/lifecycle/parent behavior unchanged |
| Official regression | `test_attack_catalog_official.py` requires env `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT` pointing local `enterprise-attack-20.1.json`; verify bytes/hash then public `load_catalog()` and a known active lookup/description. Missing env is explicit test failure, not skip/PASS. Asset and pin unchanged |
| Token/ranking | NFKC/casefold, Vietnamese composed/decomposed, English; `T1566.002`, hyphen/underscore delimiters; 1/65-character tokens omitted; duplicate token neutral; exact score, stable ASCII-ID tie; parent/child separate; zero-match success |
| Input/errors | non-str/empty/whitespace/tokenless/surrogate/>512 codepoints/>4KiB query -> `invalid_query`; bool/float/outside top-k 1..10 or budget 256..8192 -> `invalid_bounds`; exact error str/repr exposes only code |
| Context budget | Public JSON parsed/field order tested byte-exact; escape quote/backslash/control; min 256, exact-fit, one-byte-short; official long URL/hash/commit and long name; multibyte snippet boundary; mandatory envelope/item impossible -> `context_budget_exceeded`; later unfit item stops rank; raw description unchanged |
| Trust/safety | inactive excluded; no secondary STIX reader; inert prompt/URL description; socket/open/DB/provider guards no calls; input/catalog public fields unchanged; no claim caller-built catalog is provenance verified |
| Regression | `test_attack_catalog.py`, `test_ttp_audit.py`, `test_llm_adapter.py`, `test_evaluate.py`, `test_eval_cli.py`, `test_eval_report.py`; C4 existing reject test remains green |

## Checks, demo và deliverables

Use the exact interpreter and record commands, exit codes, counts and fresh log files. The worker must set `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT` to the existing verified local asset, never download it. From target root, the required scoped commands are:

```powershell
$env:PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT = '<Leader root>\\x01-attack-real-research-evidence\\enterprise-attack-20.1.json'
& '<Leader root>\\cti-platform-start\\.venv\\Scripts\\python.exe' -X utf8 -B -m pytest extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_attack_retrieval.py extractor/tests/test_ttp_audit.py extractor/tests/test_llm_adapter.py extractor/tests/test_evaluate.py extractor/tests/test_eval_cli.py extractor/tests/test_eval_report.py -q -p no:cacheprovider
& '<Leader root>\\cti-platform-start\\.venv\\Scripts\\python.exe' -X utf8 -B -m ruff check extractor/phonghoa_extractor/attack_catalog.py extractor/phonghoa_extractor/attack_retrieval.py extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_attack_retrieval.py
& '<Leader root>\\cti-platform-start\\.venv\\Scripts\\python.exe' -X utf8 -B -m ruff format --check extractor/phonghoa_extractor/attack_catalog.py extractor/phonghoa_extractor/attack_retrieval.py extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_attack_retrieval.py
git diff --check
```

Replace `<Leader root>` with `$WORKSPACE`. If a named regression path differs, report mismatch rather than widen scope.

Demo must use public `load_catalog()` → `retrieve_techniques()` → `result.context` with the official asset: verify source hash before/after, show one Vietnamese/English lexical match, deterministic repeat hash, zero-match, parsed context provenance and measured byte bound. It must state that no model/C4 generation/semantic quality was tested.

Write future output at Leader root only:

- `PHONG-HOA-X01-C4-RETRIEVAL-RESULT.md` with base/target SHA, status before/after, diff/file list, command/exit/count table, PASS/FAIL/UNVERIFIED and limitation.
- `x01-c4-retrieval-evidence/` with RED/GREEN/regression/lint-format/diff-check/demo logs and manifest SHA-256.

Do TDD, scoped self-review against this brief, commit locally once with Conventional Commit, leave target clean/branch intact for Leader review. No push/PR/merge/deploy. The worker does not re-ask the user for this approved bounded implementation; only later model, semantic evaluation, lab or release needs a new decision.

## Handoff boundary

Stop after component/evidence. Later separately approved work may call retrieval before `run_extraction()`, delimit `attack_context` from report evidence and retain provenance. It must not make ATT&CK knowledge report evidence, change `unverified`/`false`, or bypass grounding/audit/TLP/human review.
