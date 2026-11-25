# W05 Backend brief — approved final audit → STIX offline bundle (R1–R6)

## Goal, exact base, scope

Read-only converter: approved draft v2 + final approve audit → deterministic STIX 2.1 JSON local. No OpenCTI/outbox/network/UI/F07/TTP/LLM. Base `cti-w05-selection-integration` at `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`, branch `feat/w05-selection-integration-20261111`; confirm clean status/branch/SHA. Proposed, not created: `cti-w05-stix-offline` / `feat/w05-stix-offline-20261111`.

Update required docs in implementation: `docs/PROGRESS.md`, a deterministic-export ADR, and W05 offline contract for new read-only export. Do not change selection/review semantics, old fixtures, API/UI/migrations/OpenCTI compose.

## File scope

| File | Work |
|---|---|
| `extractor/phonghoa_extractor/store.py` | `ApprovedExportSnapshot`, read-only final-audit getter. |
| `extractor/phonghoa_extractor/stix_export.py` new | config/serializer/IDs/publisher. |
| `extractor/draft/stix_export.py` new | thin CLI. |
| `extractor/tests/test_stix_export.py`, `test_stix_export_cli.py` | offline matrix. |
| `extractor/requirements-stix-test.in/.lock` new if validator used | `stix2-validator==3.3.2` + generated hashes; preserve app lock. |

## Contract and transaction

```python
@dataclass(frozen=True)
class ApprovedExportSnapshot:
    draft_id: int; payload: Mapping[str, Any]; approved_audit_id: int
    review_version: int; decided_at: str; final_selection_version: int
    selected_indices: tuple[int, ...]; selected_sha256: str

def get_approved_export_snapshot(db_path: str | Path, draft_id: int, *, timeout: float = 5.0) -> ApprovedExportSnapshot: ...
```

Validate DB/id/finite timeout/config/output aliases first. Open URI `mode=ro`, execute `BEGIN` **before** PRAGMA/schema/rows, require v2 and `_validate_current_schema()`. Same transaction: decode `drafts`; require approved; fetch exactly one final approve audit; compare status/version/actor/time; canonicalize `selected_indices_json` with `_canonical_selection`; compare selection hash; verify subset `_eligible_ioc_indices(payload)` and selection audit event/version. No migration/write/current selection authority.

Reject missing DB/draft/audit; v0/v1/legacy/future; pending/rejected; duplicate/inconsistent final audit; bad payload/source hash; selection corruption; empty/unsupported IOC. `source.sha256` is text hash; payload integrity is complete stored data validation; selection SHA is canonical indices.

## Config, provenance, STIX mapping

CLI requires local trusted `--exporter-config PATH`:

```json
{"schema_version":"1","id_namespace_uuid":"UUID","name":"Phong Hoa offline exporter","identity_class":"organization","created":"2026-01-01T00:00:00Z","tlp":"TLP:GREEN"}
```

Reject extra/missing fields, invalid UUID/time/name/class/TLP, and config TLP different from snapshot TLP (v1 safe rule: equality). Identity is config-hash deterministic and not reviewer author. Sidecar manifest (same atomic rules) contains format version, source text hash, canonical payload SHA, draft/audit/review/selection data, config hash, source/STIX TLP, `reviewer_subject_sha256`; never raw reviewer/text/evidence/reason/secret.

Create marking + exporter Identity + one SCO per deduped final selection + Report. No Indicator/pattern/ObservedData/relationship. Report refs Identity/SCOs. Report time = `decided_at`; Identity created = config; marking fixed. First `(type, normalized value)` wins.

| Input supported | SCO |
|---|---|
| ipv4/ipv6 | `ipv4-addr:value` / `ipv6-addr:value` |
| domain/url/email | `domain-name:value` / `url:value` / `email-addr:value` |
| md5/sha1/sha256 | `file:hashes.'MD5'/'SHA-1'/'SHA-256'` |

SHA512/unknown/empty fail. Apply marking to all generated objects. Literal marking IDs: WHITE `marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9`; GREEN `--34098fce-860f-48ae-8e50-ebd3cc5e41da`; AMBER `--f88d31f6-486f-44da-b317-01333bde0b82`; RED `--5e57c739-391a-4eb3-b6be-7d15ca92d5ed`, with standard created timestamp. CLEAR→WHITE manifest provenance; GREEN/AMBER/RED one-to-one; AMBER+STRICT fail.

## Deterministic ID and validator profile

- SCO: OASIS SCO UUIDv5 namespace + canonical JSON of only ID-contributing properties.
- Identity: project Identity UUIDv5 namespace + full exporter config SHA.
- Report: project Report UUIDv5 namespace + format, payload/source hashes, draft/audit/selection, marking, config SHA.
- Bundle: separate project Bundle UUIDv5 namespace + Report ID + ordered IDs + same provenance.

No shared namespaces, `now()` or UUID4. v5 SDO/Bundle is a SHOULD exception, not MUST violation. Test collision changes: different DB same IDs but differing payload/source/TLP/exporter/selection; identity contents differ.

Before validator tests: verify release artifact `3.3.2`, `--version/--help`, lock hash and exact 103 option. Run all MUST/schema/ref checks; separately label `strict except 103`, only 103 disabled. Independently assert ID version/namespace/SCO canonical properties. Never claim plain strict PASS.

## CLI and publication

```text
python extractor/draft/stix_export.py export-approved --db PATH --id INT --exporter-config PATH --output PATH [--timeout SECONDS]
```

Success prints only draft/bundle/manifest hashes and object count. Error exit 1 one safe line. No actor/selection/TLP/OpenCTI/force/replace.

Build/validate bytes in memory. Bundle and `<output>.manifest.json`: target absent publishes atomic/non-clobber; byte-identical existing succeeds no write; differing existing fails untouched. Reject DB/sidecar/symlink/hardlink/samefile/directory targets. Temp same parent, exclusive create, flush/fsync; retry only own temp collision, delete no unowned temp. Local NTFS supported assumption; network share/reparse alias/crash durability unverified.

## TDD acceptance matrix

| Case | Expected |
|---|---|
| 2 IOC deselect one approve | Only final chosen SCO + Report/Identity/marking; manifest hashes; DB unchanged. |
| Authority/tamper | Client/keep post-approve irrelevant; corrupt payload/audit hash/version/index/actor/time → error, no output/DB change. |
| State | pending/rejected/self approve/creator-null/legacy-v1-future/corrupt/duplicate audit fail. |
| Eight IOC | ipv4,ipv6,domain,url,email,md5,sha1,sha256 each mapping; SHA512/unknown/empty fail. |
| TLP/identity | four literal marking objects incl RED; CLEAR provenance; AMBER+STRICT fail; reviewer not identity. |
| Determinism | same snapshot/config bytes equal; collision vectors change intended ID; SCO ID matches OASIS. |
| Read interleaving | controlled connection changes after `BEGIN`: old consistent snapshot or conflict, never mixed; no sleep. |
| Publisher | new/equal/different targets; DB/sidecars/aliases; injected fail cleans owned temp. |
| Validator | verified pin; MUST/ref profile + strict-except-103; structural pass not OpenCTI/lab pass. |

Run after implementation only: targeted pytest, `git diff --check`, verified validator profiles. Record exact version/lock hash/exit code and limits in ADR/contract/PROGRESS.

## Sources

- <https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html>
- <https://www.first.org/tlp/>
- <https://stix2-validator.readthedocs.io/en/latest/best-practices.html>
- <https://docs.opencti.io/7.260512.0/usage/import-files/>
