# X01-ATTACK — brief restricted catalog offline cho CTI AI Agent (Sol medium)

## Mục tiêu và tree chính xác

Triển khai **library + fixture STIX hoàn toàn synthetic** để kiểm syntax/catalog status ATT&CK Enterprise. Không snapshot MITRE thật, RAG/C4/model/network, semantic TTP hay ghi draft. Đây là contract testable, không phải chứng minh tương thích MITRE thật.

- Base: `8694fa7244d181f421bb2733ded7bf9ae218ea93`, tree mới `$WORKSPACE/cti-x01-attack-offline`.
- Branch: `feat/x01-attack-offline-20261111`. Không sửa tree AI nguồn.
- Dùng, không sửa/cài: `$WORKSPACE/cti-platform-start/.venv/Scripts/python.exe` và `.../.venv/Scripts/ruff.exe`.

## File scope

```text
extractor/phonghoa_extractor/attack_catalog.py
extractor/tests/test_attack_catalog.py
extractor/attack/fixtures/*.json
extractor/attack/fixtures/README.md
extractor/attack/README.md
docs/adr/<next-free>-x01-restricted-attack-catalog.md
docs/PROGRESS.md
```

Không thêm `data/<version>`, snapshot MITRE hay dependency. Không sửa adapter/grounding/evaluator/draft/store/SQLite/W05/API/UI/exporter/deploy/RUNS. ADR ghi fixture-only/restricted policy; PROGRESS nói synthetic offline, không phải C4/MITRE runtime.

## Interface bắt buộc

```python
@dataclass(frozen=True)
class SnapshotPin:
    kind: Literal["synthetic", "official"]
    version: str
    sha256: str
    source_url: str | None
    release_tag: str | None
    commit: str | None
    provenance: Literal["hand-authored-test-fixture", "mitre-attack-stix-data"]

@dataclass(frozen=True)
class TechniqueRecord:
    stix_id: str; external_id: str; name: str; modified: datetime
    revoked: bool; deprecated: bool; is_subtechnique: bool
    parent_external_ids: tuple[str, ...]

@dataclass(frozen=True)
class AttackCatalog:
    pin: SnapshotPin
    records_by_external_id: Mapping[str, TechniqueRecord]

@dataclass(frozen=True)
class TechniqueLookup:
    normalized_id: str | None
    syntax_valid: bool
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"]
    reason_code: str
    pin_kind: Literal["synthetic", "official"]
    snapshot_version: str; snapshot_sha256: str
    external_id: str | None; name: str | None; is_subtechnique: bool | None
    parent_external_ids: tuple[str, ...]
    semantic_status: Literal["unverified"] = "unverified"
    operational_draft_eligible: bool = False

class AttackCatalogError(ValueError): code: str
def load_catalog(snapshot: Path, pin: SnapshotPin, *, max_bytes: int=64*1024*1024) -> AttackCatalog: ...
def validate_technique(catalog: AttackCatalog, supplied_id: object) -> TechniqueLookup: ...
```

Lookup never `str()`/trims/raw-echoes. Only ASCII fullmatch; invalid yields `None,false,"not_checked","invalid_technique_id"`. All results semantic-unverified/not eligible. Pin pre-I/O: exact types/enums/ASCII bounds, lowercase 64-hex SHA; synthetic requires hand-authored provenance + all MITRE fields None, official requires non-empty metadata but is unsupported in this slice. `max_bytes`: int-not-bool, 1..64 MiB.

## Loader/graph rules

Read `max_bytes+1`; hash → UTF-8 → strict JSON duplicate/NaN/Infinity reject → bundle/member → patterns/relationships → canonical conflicts → graph. Codes: `invalid_pin`, `snapshot_not_found`, `snapshot_io_error`, `snapshot_too_large`, `snapshot_hash_mismatch`, `invalid_utf8`, `invalid_json`, `invalid_bundle`, `invalid_member`, `invalid_attack_pattern`, `invalid_relationship`, `duplicate_conflict`, `parent_conflict`; str/repr code only.

Patterns need strict STIX fields/domain/external ref/lifecycle/sub-technique consistency as research. Canonicalize patterns+edges by id, newest UTC modification including fractional time, exact duplicate dedupe, collision/equal-time differing payload conflict/no resurrection. Apply only current non-inactive `subtechnique-of`. Active child must exactly one active non-child parent source→target/prefix match; reject all dangling/self/wrong/multi/orphan/inactive-parent cases; inactive child may omit edge.

## TDD/acceptance

Write RED `test_attack_catalog.py`, preserve RED evidence, then GREEN. Tiny fixtures state synthetic provenance/purpose and cover active parent/child, revoked/deprecated inactive, unknown—no MITRE bytes/names/tags.

Tests: pin types/enums/hash/metadata, size/read/hash-before-parse, I/O/UTF-8/strict JSON, root/member/list-dict-null-bool-number attacks, external refs/domains/lifecycle, no coercion/marker leak, all version/collision/graph cases, immutable catalog, socket guard/no egress, active/inactive/unknown/invalid results. Regression: evaluator/adapter CLI four files plus grounding if reused; demonstrate C4 still exit 2. Do not run full/UI/browser suite.

From new tree, prove import origin then execute/report fresh exit/count:

```powershell
$py='$WORKSPACE/cti-platform-start/.venv/Scripts/python.exe'
$ruff='$WORKSPACE/cti-platform-start/.venv/Scripts/ruff.exe'
& $py -c "import phonghoa_extractor.attack_catalog as m; print(m.__file__)"
& $py -m pytest extractor/tests/test_attack_catalog.py -q
& $py -m pytest extractor/tests/test_evaluate.py extractor/tests/test_eval_cli.py extractor/tests/test_llm_adapter.py extractor/tests/test_llm_cli.py extractor/tests/test_grounding.py -q
& $ruff check extractor/phonghoa_extractor/attack_catalog.py extractor/tests/test_attack_catalog.py
& $ruff format --check extractor/phonghoa_extractor/attack_catalog.py extractor/tests/test_attack_catalog.py
git diff --check; git status --short; git rev-parse HEAD; git diff --stat
```

If missing executable/test, UNVERIFIED; never install. Result: `$WORKSPACE/PHONG-HOA-X01-ATTACK-RESULT.md`; logs/fixture manifest: `.../x01-attack-evidence`. Report base/head/diff/status, command/exit/count, fixture SHA/provenance, demo statuses, local clean commit; never push/merge. Test only proves fixture contract, not real MITRE snapshot, TTP semantics, RAG/C4/model/W05/OpenCTI/lab.
