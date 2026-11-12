# X01-C4-EVAL-NEXT — implementation brief

## Scope cố định

Target `root\cti-x01-c4-eval`; branch `feat/x01-c4-eval-20261111`; base `654443e6ede6557f0629fc0886ca56fff782b193`. Một CTI AI Agent/Sol medium làm TDD. Mục tiêu: C4 synthetic/fake_offline, query manifest explicit, artifact 1.2, reporter C4-only hoặc C3-audit+C4. Không benchmark model/RAG/TTP.

Only: `extractor/eval/run.py`, `extractor/eval/report.py`, `extractor/eval/README.md`, `extractor/tests/test_eval_cli.py`, `extractor/tests/test_eval_report.py`, `extractor/tests/test_c4_eval_contract.py`, new `extractor/eval/fixtures/c4/`, `docs/PROGRESS.md`, `docs/adr/0009-c4-evaluator-artifact-and-cohort.md`. Không sửa adapter/retriever/catalog/audit/C2-C3 fixture/API/UI/SQLite/OpenCTI/dependency.

## Exact API/CLI

Add frozen `C4QueryManifest(schema_version: Literal["1.0"], query_policy: Literal["explicit-per-document-v1"], raw_sha256: str, queries: tuple[tuple[str,str],...])`, `load_c4_query_manifest(path: Path) -> C4QueryManifest`, and `evaluate_c4_dataset(dataset: Path, responses_dir: Path, *, tlp: str, attack_catalog: AttackCatalog, query_manifest: C4QueryManifest) -> dict[str, Any]`. Keep C2/C3 API untouched; C4 public API revalidates DTO exactly.

Manifest: raw <=16384 bytes; strict UTF-8/no BOM; reject duplicate/nonfinite; exact root 3 fields; ID 1..128/no NUL; query <=512 codepoints/4096 bytes and existing `_validate_query`; exact IDs equal dataset stems; digest raw bytes. No normalize/derive. C4 requires dataset/responses/TLP(any five)/snapshot/pin/manifest/output; rejects ttp-audit; C1--C3 reject manifest. Fixed top_k 5/budget 4096.

Preflight: safe output → manifest/map → pin/catalog → all reports/metadata/labels (universal-newline; report <=1 MiB codepoint and bytes) → all fixtures/providers → first generate. Construction of ScriptedProvider is allowed before generate. Do not retrieval-preflight. Usage exit 2; runtime only `Lỗi: offline_eval_failed`, exit 1.

## Output/reporter contract

Implement exact C4 `1.2` root/document/context/audit schema from research R3. One C4 adapter invocation + one audit/document; audit no provider call. Preserve real adapter lifecycle: success 1, retry success 2 with empty errors, fallback 2 retryable errors + empty TTP audit, terminal first/second 1/2. Reuse IOC C3 scoring/basis literal. Do not emit raw query/context or claim semantic/model quality.

C4 writer only: temp+fsync+`os.link` no-clobber, no overwrite flag. Protect dataset/responses/manifest/snapshot/pin against lexical/resolved/samefile/hardlink/detectable symlink aliases; output exists/race rejects. Preserve C1-C3 writer. Reporter keeps overwrite; strict C4 validates C4-only/C3.1+C4, compares root and per-ID required metadata, renders digest/catalog/metrics/limitations only.

## RED → GREEN acceptance

1. RED: duplicate/BOM/nonfinite/bounds/whitespace token/ID map and flags; bad last preflight doc has zero generate calls.
2. RED: lifecycle/context/catalog/audit, bool/float substitution, oversize report, output exists/race/aliases/preservation.
3. RED: reporter C4-only/C3+C4, mismatched catalog/per-ID metadata/schema mix, C1 bytes, C2/C3 normalized cross-commit.
4. GREEN: minimal implementation only.

| Criterion | Evidence |
|---|---|
| Contract | Valid manifest; exact 1.2 types/keys; no raw query/context. |
| Preflight | Protected-input malformed fails before generate; terminal response may have earlier calls, no publish. |
| Lifecycle | 1/2/2/1/2 calls as above; audit zero provider calls. |
| Safety | C4 no-clobber; aliases rejected; inputs/old output preserved on failure. |
| Reporter | C4-only+C3.1/C4 deterministic; invalid cohort rejects; no uplift claim. |
| Regression | C1 bytes unchanged; C2/C3 same-checkout bytes; only evaluator git ref ignored cross-commit. |

## Checks/handoff

Use `root\cti-platform-start\.venv\Scripts\python.exe`; `PYTHONPATH=target\core;target\extractor`. Run `test_eval_cli.py`, `test_eval_report.py`, `test_c4_eval_contract.py`, `test_llm_adapter.py`, `test_ttp_audit.py`; then ruff check and `ruff format --check` changed allowlist. Run `git diff --check base..HEAD`, record target/source status + HEAD. Demo C4 JSON and C3.1+C4 reporter at same HEAD; hash manifest/artifacts/report.

Write `root\PHONG-HOA-X01-C4-EVAL-RESULT.md` and evidence references under `root\x01-c4-eval-evidence\`, PASS/FAIL/UNVERIFIED with command/exit/count/ref. Commit local only; no push/PR/merge/deploy/model/network/lab. Synthetic smoke is never model/C4 quality.
