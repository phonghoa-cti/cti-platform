# X01-EVAL-REPORT-NEXT — implementation brief

## Task packet

Owner CTI AI Agent, Sol medium. Implement reporter stdlib offline only. Base read-only `$WORKSPACE\cti-x01-ttp-eval`, exact HEAD `984bd2136872f4c5fba4118e33cf02b5ca615f2d`; new isolated tree `...\cti-x01-eval-report`, branch `feat/x01-eval-report-20261111`. Interpreter: `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`.

Read AGENTS, PROGRESS, X01 spec and eval README. TDD required. No evaluator/score/dataset/artifact change, model/network/DB/OpenCTI/W05/lab/cloud. Local commit is permitted after verification; no push/PR/merge/deploy.

## File scope and CLI

Change only `extractor/eval/report.py`, `extractor/tests/test_eval_report.py`, `extractor/eval/README.md`, `docs/PROGRESS.md`; tests fixtures may live `extractor/tests/fixtures/eval_report/`. ADR only for a genuinely new decision.

```text
python extractor/eval/report.py --input ARTIFACT [--input ARTIFACT ...] --output REPORT.md [--overwrite]
```

One to three inputs; C1/C2/C3 each at most once. Success stdout one-line JSON and exit 0. Generic parse/schema/cohort/path/conflict exit 2 stderr exactly `Lỗi: eval_report_invalid_input`; missing/unreadable/write/publish I/O exit 1 stderr exactly `Lỗi: eval_report_io_failed`; `--help` exit 0. Override argparse error so neither offending token nor path leaks.

## Artifact projection to implement

Implement exactly the three projections/bounds/metric and cohort rules in research section “Contract quyết định”. Important C1 exception: C1 1.0 document exact envelope is `id,language,prediction,score,source`; it has no `config`. C2/C3 documents do have root-equal `config`. For non-rendered prediction/raw/grounding nested payloads, validate safe shape/bounds/depth only; do not reject valid evaluator semantics or re-run grounding.

Bounds: 1 MiB + one-byte probe/input; depth 64; map 64; array 512; string 8,192 code points; 256 documents; JSON integer literal ≤19 digits then 0..`2^63-1`; finite [0,1] metrics. Reject duplicate keys/nonfinite/BOM/keyset mismatch. P/R/F1 use evaluator `Score` denominator-zero=0 and tolerance `1e-12`. Aggregate/mode/TTP-document consistency is mandatory; never recompute to repair artifact and never derive micro from `by_type`.

## Output and safety

Emit synthetic warning, cohort provenance including SHA-256 bytes for each input (no filename/path), aggregate IOC, C2/C3 modes, per-type, conditional 1.1 TTP consistency counts, fixed limitations/footer. P/R/F1 fixed six decimals; counts decimal. C3 exact label says merged model candidates+regex, not model-only. No raw CTI/path/URL/quote/ID/provider free-text.

Use closed vocabulary and grammar from research, rendering only validated renderer-owned literals/code spans. Reject or literal-safe test all Markdown link/image/autolink/HTML/entity/backtick/pipe/newline/control attempts. Deterministic ordering C1/C2/C3 then fixed mode/status then lexical types; UTF-8 LF; no timestamp/host/cwd.

Inputs strict-resolve regular files. Output can be new and a sibling different name; prohibit directory/samefile/resolved or lexical alias. Finish all validation before parent creation. Create temp in output parent. Default no-clobber publishes using `os.link(temp, output)`: race/existing is exit 2, never replace fallback. Only `--overwrite` uses `os.replace`. Temp cleanup best effort; link/replace success is commit point and cleanup failure cannot claim rollback.

## TDD acceptance and commands

Write failing tests then implementation. Cover positive C1 1.0, C2/C3 1.0, C2/C3 1.1 including valid fallback/audit; malformed fixtures must start valid then change one property. Cover C1 no-document-config, exact keysets/projection bounds, zero denominator, aggregate mismatch, empty/nonempty mode and not_available, top TTP mismatch, duplicate/nonfinite/huge/deep JSON, input hash repeatability, grammar attacks, aliases/sibling/new output/race no-clobber, overwrite, write failure/old-output preservation and byte-identical rerun.

Run (from new tree):

```powershell
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest extractor/tests/test_eval_report.py -q -p no:cacheprovider
$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest extractor/tests/test_eval_cli.py -q -p no:cacheprovider
ruff check extractor/eval/report.py extractor/tests/test_eval_report.py
ruff format --check extractor/eval/report.py extractor/tests/test_eval_report.py
git diff --check
```

## Demo, evidence, handoff

Worker may create **new synthetic** C1 1.0 and compatible C2+C3 1.1 inputs outside source at `$WORKSPACE\x01-eval-report-evidence\inputs\`; use local evaluator only, never modify historical evidence. Render outputs/logs/manifests under `...\x01-eval-report-evidence\`. Record SHA-256 before/after input, report SHA-256, rerun byte equality, exact commands/exit/test count, branch/HEAD/status/diff files. Result: `...\PHONG-HOA-X01-EVAL-REPORT-RESULT.md`.

State PASS only for fresh local reporter/test evidence. Model quality/corpus, semantic TTP, C4/RAG, lab/production remain UNVERIFIED.
