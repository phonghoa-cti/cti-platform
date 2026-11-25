# X01-C4-EVAL-NEXT — research/contract C4 evaluator + reporter

Ngày đối chiếu: 11/11/2026. Source chỉ đọc `root\cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`, HEAD `654443e6ede6557f0629fc0886ca56fff782b193`, status sạch. Đây là contract, không phải kết quả chạy C4 hay chất lượng model/RAG/TTP.

## Quyết định và nguồn

**Chọn A: evaluator C4 và reporter C4 trong cùng lát offline.** Tái dùng `run_c4_extraction`, `load_catalog`, `audit_techniques`, scorer IOC, fixture provider, writer và reporter strict; không thêm parser STIX, dependency, egress, DB hay model thật. C4 có JSON tái lập + Markdown đọc được; C1--C3 không đổi hành vi/output.

| Cách | Kết luận |
|---|---|
| A. Evaluator + reporter C4 | **Chọn:** có artifact và cohort C3/C4 cùng provenance. |
| B. Chỉ evaluator C4 | Không chọn: phải vá reporter ngay lượt sau. |
| C. Chờ corpus/gold TTP | Để sau: cần cho quality, không cần để test contract synthetic. |

[RAGAS bản gốc](https://aclanthology.org/2024.eacl-demo.16.pdf) tách nhiều chiều RAG và đối chiếu human judgments; Phong Hỏa **áp dụng chính sách** không coi fixture/reference-free là gold. [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) hỗ trợ ghi assumptions/limitations/provenance, không chứng minh pipeline. [MITRE ATT&CK STIX Data](https://github.com/mitre-attack/attack-stix-data) là asset versioned, không là nhãn semantic report.

## R1 — compatibility đã chốt

- C4 nhận đủ năm TLP hiện có: CLEAR, GREEN, AMBER, AMBER+STRICT, RED; tất cả chỉ tới `fake_offline`, `egress=false`, fixture tổng hợp.
- `prediction_basis` literal: `adapter_grounded_model_plus_regex` cho `model_completed`; `regex_fallback` cho fallback.
- Cohort mới: C4 schema `1.2` đơn lẻ, hoặc C3 audit schema `1.1` + C4 `1.2`. Cấm C1/C2/C3-1.0/C3-1.2 trộn C4. Cohort C1--C3 cũ giữ nguyên.
- C3+C4 cùng dataset hash/count, fixture manifest, provider policy/mock_only, evaluator, catalog projection. Ghép doc bằng ID duy nhất; cùng source hash, fixture hash, language, TLP; không so query hash/prediction/mode.
- C1 baseline byte-identical. C2/C3 cross-commit chỉ bỏ `evaluator.git_ref`; rerun cùng HEAD/input byte-identical. Markdown cũ với artifact cố định byte-identical.

## R2 — preflight, DTO, API, errors

Trong `extractor/eval/run.py` thêm:

```text
@dataclass(frozen=True)
class C4QueryManifest:
  schema_version: Literal["1.0"]
  query_policy: Literal["explicit-per-document-v1"]
  raw_sha256: str
  queries: tuple[tuple[str, str], ...]

def load_c4_query_manifest(path: Path) -> C4QueryManifest
def evaluate_c4_dataset(dataset: Path, responses_dir: Path, *, tlp: str,
  attack_catalog: AttackCatalog, query_manifest: C4QueryManifest) -> dict[str, Any]
```

`queries` tuple là immutable DTO. Public evaluator revalidate exact class/fields/literals/lowercase SHA-256 64 hex, nonempty tuple pair `(str,str)`, unique IDs; không tin dataclass tự runtime-check. Map dựng sau validate, không đổi query.

Manifest đọc tối đa 16385 bytes, nhận <=16384; UTF-8 strict/no BOM; `object_pairs_hook` từ chối duplicate và `parse_constant` từ chối NaN/Infinity. Root exact `schema_version`, `query_policy`, `queries`; literals exact. ID 1..128 code points, strict UTF-8, no NUL. Query <=512 code points/4096 UTF-8 bytes và qua **chính** `_validate_query` retrieval (whitespace/`!!!`/`a` không hợp lệ); không copy tokenizer/retrieval. Digest là raw bytes, không reserialize JSON.

C4 requires dataset/responses/TLP/snapshot/pin/manifest/output; nhận 5 TLP; từ chối `--ttp-audit`. C1--C3 từ chối manifest C4. C4 fixed `top_k=5`, budget 4096, không tuning flag.

Order: (1) argparse/combination exit 2; (2) output/protected-path; (3) manifest+exact dataset ID map; (4) pin/catalog; (5) đọc hết report/metadata/labels universal-newline, report <=1 MiB code point **và** bytes; (6) load/validate fixture và dựng ScriptedProvider; (7) generate đầu tiên. Provider construction được phép preflight, `generate` không. Preflight lỗi doc cuối có total generate=0. Không preflight retrieval; wrapper đúng một retrieval/doc. Terminal response sau start có thể đã có calls doc trước; output chưa publish.

Runtime failure in đúng `Lỗi: offline_eval_failed`, exit 1, không CTI/query/context/traceback. Source hash/span/audit dùng `str` universal-newline gửi adapter; raw hash chỉ dataset/fixture/manifest.

## R3 — schema, publish, reporter

Root C4 exact schema `1.2` keys: `schema_version`, `config`, `purpose`, `dataset_sha256`, `fixture_manifest_sha256`, `query_manifest_sha256`, `provider_policy`, `mock_only`, `evaluator`, `document_count`, `documents`, `micro_all`, `micro_by_result_mode`, `by_type`, `ttp_audit`, `limitations`; literals `1.2`, C4, synthetic-smoke; policy exact fake_offline/false; mock_only true. count int (not bool/float) 0..256, strings <=8192 where reporter accepts, hashes lowercase 64 hex.

Document exact keys: `id`, `config`, `language`, `tlp`, `source`, `fixture`, `adapter_schema_version`, `provider`, `attempts`, `result_mode`, `error_codes`, `model_items_used`, `operational_draft_eligible`, `prediction_basis`, `prediction`, `score`, `grounding_audit`, `attack_context`, `ttp_audit`. Source/fixture exact path/hash; provider exact name/model_id/destination/egress; bool is bool; existing strict score applies.

model_completed: attempts 1|2, errors empty, model_items true, basis adapter literal. fallback: attempts 2, two retryable errors, model_items false, fallback basis, empty TTP audit. Document eligible true; each TTP audit semantic unverified/eligible false.

`attack_context` exact 10 keys `requested`, `retrieval_completed`, `provider_context_sent`, `c4_adapter_completed`, `schema_version`, `sha256`, `byte_length`, `top_k`, `budget_bytes`, `snapshot`. First 3 true; schema 1.0; sha hex; length int >0 <=4096; top_k 5; budget 4096; completed iff model mode. Snapshot exact six `version`, `sha256`, `kind`, `source_url`, `release_tag`, `commit`, matching root catalog projection (extra provenance only root). Context/source/query hashes differ and do not prove hits/model use.

Root audit is exact existing 1.1 enabled/catalog/note/counts; audit config/source hash/pin match doc/root; counts equal docs; never TTP P/R/F1/rate. Limitations exact: synthetic fake provider/no real quality; C4 merges candidates+regex/not model-only; semantic TTP/malware/actor not evaluated; context retrieval/transmission not proof knowledge use/quality; audit only source/quote/catalog, semantic TTP unverified.

C4 has **new no-clobber writer only**: target exists always refuses; no overwrite flag. temp+fsync same parent, `os.link(temp, output)` is commit point; pre-link failure preserves old output, post-link cleanup failure returns I/O while output remains; clean only own temp. Protected: dataset/responses/manifest/snapshot/pin; reject lexical/resolved containment in dataset/responses and samefile/hardlink/detectable symlink/reparse aliases. Do not claim hostile-directory/crash safety. C1--C3 writer unchanged; reporter retains overwrite.

Reporter adds strict C4 validator/order after C3 and a C4 cohort branch; retains old C1--C3 order/validation/render. Accept C4-only and C3.1+C4 only. Render aggregate/modes/query digest/catalog, never query/context/evidence/path/URL. Fixed header limits: synthetic, not model-only, transmission not proof knowledge use.

## R4 — scope/checks/limits

Target `root\cti-x01-c4-eval`, branch `feat/x01-c4-eval-20261111`, one CTI AI Agent/Sol medium. Allowlist: `extractor/eval/run.py`, `extractor/eval/report.py`, `extractor/eval/README.md`, `extractor/tests/test_eval_cli.py`, `extractor/tests/test_eval_report.py`, `extractor/tests/test_c4_eval_contract.py`, new `extractor/eval/fixtures/c4/`, `docs/PROGRESS.md`, `docs/adr/0009-c4-evaluator-artifact-and-cohort.md`. No adapter/retriever/catalog/audit/old fixture edits.

Use `root\cti-platform-start\.venv\Scripts\python.exe`, `PYTHONPATH=target\core;target\extractor`. Evidence: target HEAD/status, base..HEAD diff, targeted pytest, ruff check/format-check changed files, C4 JSON and C3+C4 reporter demos same HEAD, command/exit/count + SHA manifest/artifacts/report. Result `root\PHONG-HOA-X01-C4-EVAL-RESULT.md`; evidence `root\x01-c4-eval-evidence\`. No push/PR/merge/deploy/network/model/lab. Unverified: implementation/tests, real model/provider, semantic/multilingual retrieval, injection, human gold/corpus, cost/latency, W05/OpenCTI/lab/production.
