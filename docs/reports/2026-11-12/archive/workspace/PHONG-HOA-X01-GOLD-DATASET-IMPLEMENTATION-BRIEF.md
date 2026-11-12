# X01-GOLD-DATASET-NEXT — brief `gold-pilot-v1`

## Target and scope

One CTI AI Agent/Sol medium worker, no delegation. Root `$WORKSPACE`; read-only base `<root>\cti-x01-c4-eval` at `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`; new target `<root>\cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111` (both not created). Verify base/status, then read AGENTS/PROGRESS/GUIDELINE/catalog/C4 docs and write RED tests.

Only create/change:

```text
extractor/phonghoa_extractor/gold_pilot.py
extractor/dataset/check_gold_pilot.py
extractor/tests/test_gold_pilot.py
extractor/tests/fixtures/gold_pilot/**
docs/specs/X01-gold-pilot-v1.md
docs/adr/0010-x01-gold-pilot-readiness.md
docs/PROGRESS.md
```

No raw corpus/model/network/dependency/config/C1–C4/UI/DB/API/push/PR/merge/deploy. Fixtures synthetic only.

## API, CLI and statuses

```python
def validate_gold_pilot(dataset: Path, snapshot: Path, pin_path: Path) -> GoldPilotReadiness: ...
def write_readiness(report: GoldPilotReadiness, output: Path, *, protected_inputs: tuple[Path, ...]) -> None: ...
```

`GoldPilotError(code)` closed codes: invalid_inventory, invalid_manifest, invalid_record, invalid_annotation, invalid_raw, invalid_pin, invalid_catalog, invalid_technique, unsafe_output, io_failure. Validator returns READY_FOR_ADJUDICATION|NOT_READY; invalid/I/O raise. API and CLI share validators/writer.

```powershell
<root>\cti-platform-start\.venv\Scripts\python.exe extractor\dataset\check_gold_pilot.py --dataset <local> --attack-snapshot <snapshot> --attack-pin <pin> --report <new.json>
```

All args required; 0 READY, 2 INVALID/NOT_READY, 1 I/O. INVALID writes no report; NOT_READY writes valid report. Never emit raw/path/exception. Pin parser strict <=16 KiB exact SnapshotPin seven fields; build existing DTO, call `load_catalog` once and `validate_technique` for every TTP; no new STIX parser/network/default. Full exact data contract is Research above.

## Writer/report

Use lstat/reparse checks before resolve; report parent existing/safe, report outside dataset and not lexical/resolved/samefile alias of dataset/pin/snapshot. Refuse existing output. Same-parent temp, flush/fsync, `os.link` no-clobber commit point. Pre-commit failure creates no report/keeps old output; cleanup failure after link preserves completed report and returns bounded I/O diagnostic. No swallow.

Report canonical JSON sorted keys/compact/LF only: status, dataset_input_sha256, pin-byte/snapshot hashes, provenance, document id/status/reasons, eligible agreement counts, cohort evaluated_record_count, limitations. No sensitive fields. Include active catalog membership only, `semantic_status=unverified` for TTP.

## Test matrix

Tests live under `extractor/tests` (pytest.ini testpath). Synthetic loader/pin for unit tests; official compatibility only reads existing `extractor/tests/fixtures/attack_official/official-pin.json`, never copies/downloads 55 MiB asset.

| Case | Expected |
|---|---|
| valid 5-record synthetic dataset, token IOC evidence, two annotation IDs | READY/0, API/CLI parity, no sensitive output. |
| 0/1 annotations, permitted missing raw, all no-findings | NOT_READY/2 deterministic reasons. |
| malformed inventory/schema/UTF-8/BOM/duplicate key/type/date/hash/rights/TLP/filename/orphan | INVALID/2, no report. |
| bad span/quote/token normalization; malformed/unknown/inactive TTP | INVALID/2. |
| mutate raw/annotation bytes with same counts | fingerprint changes. |
| parent/sub active | distinct accepted labels, semantic unverified. |
| translation/group violation, aliases/path escape/size caps | INVALID and input hashes unchanged. |
| output alias/existing, before/post-link failures | no-clobber and completed post-link preserved. |
| two fresh output paths | byte-identical reports. |
| named C1–C4/catalog tests | existing contracts green. |

```powershell
$py='<root>\cti-platform-start\.venv\Scripts\python.exe'
& $py -m pytest extractor/tests/test_gold_pilot.py -q
& $py -m pytest extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_evaluate.py extractor/tests/test_eval_cli.py extractor/tests/test_eval_report.py extractor/tests/test_c4_eval_contract.py -q
& $py -m ruff check extractor/phonghoa_extractor/gold_pilot.py extractor/dataset/check_gold_pilot.py extractor/tests/test_gold_pilot.py
& $py -m ruff format --check extractor/phonghoa_extractor/gold_pilot.py extractor/dataset/check_gold_pilot.py extractor/tests/test_gold_pilot.py
git diff --check 5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35..HEAD
```

Result `<root>\PHONG-HOA-X01-GOLD-PILOT-RESULT.md`; evidence `<root>\x01-gold-pilot-evidence\` with commands/exit/JUnit, ready/not-ready/invalid demos, non-mutation hashes, manifest/base/HEAD/diff/status. Do not claim full-suite/product proof unless run. Return PASS/FAIL/UNVERIFIED; never call it gold/model quality.
