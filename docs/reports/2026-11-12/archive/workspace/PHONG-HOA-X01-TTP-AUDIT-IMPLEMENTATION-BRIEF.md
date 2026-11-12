# X01-TTP-AUDIT — implementation brief offline

## Scope chốt

Owner một CTI AI Agent, Sol medium, không giao bot khác. Implement audit opt-in sau adapter fake: source binding + exact quote/span + catalog lookup. Không phải C4/RAG/semantic proof hay quyền draft technique.

Base source chỉ đọc: <root>\cti-x01-attack-official, exact 4001441edcf5414df0f06c34352f6c5d3e2a2bd5, branch feat/x01-attack-official-20261111. Tạo worktree <root>\cti-x01-ttp-audit, branch feat/x01-ttp-audit-20261111 từ exact base. Nếu tồn tại: chỉ inspect owner/HEAD/status, báo Leader, không reset/xóa/chiếm. <root> = $WORKSPACE.

Interpreter: <root>\cti-platform-start\.venv\Scripts\python.exe. Không cài package/mạng/model/asset download/secret/DB/listener/API/UI/OpenCTI/lab/push/PR/merge/deploy. Không sửa RUNS, source tree, evidence Leader, attack_catalog.py, llm_adapter.py, grounding.py, evidence.py, evaluate.py, C1–C3/eval behavior, dependencies hay docs/spec cũ.

Đọc AGENTS.md, PROGRESS, X01 spec, ADR0004, hai TTP documents và adapter/catalog tests. AGENTS yêu cầu TDD; phạm vi đã được Leader giao.

## File scope

1. Add extractor/phonghoa_extractor/ttp_audit.py.
2. Add extractor/tests/test_ttp_audit.py.
3. Chỉ khi cần export public: extractor/phonghoa_extractor/__init__.py.
4. docs/PROGRESS.md chỉ ghi evidence thực chạy/giới hạn.

Không CLI mới. Demo là test library dùng public ScriptedProvider và run_extraction thực.

## Exact contract

    def audit_techniques(
        *, adapter_result: dict[str, object], source_text: str, catalog: AttackCatalog
    ) -> tuple[TechniqueAudit, ...]: ...

Audit validates projection, không xác thực full result/provenance object RAM. Allow but ignore top-level iocs/purpose/language/tlp/attempts/warnings/error_codes và provider metadata ngoài destination/egress.

Validate trước mọi result:

1. source_text exact str, nonempty; character bound trước strict UTF-8 encode. Type/rỗng/Unicode encoding => invalid_source_text; >1 MiB => input_too_large.
2. catalog type exact AttackCatalog else invalid_catalog. Catalog là trusted-loader boundary; không reload/verify object RAM; loader error outside seam không catch/remap.
3. adapter_result dict projection: schema_version exact "1.0"; config exact "C2"|"C3"; mock_only is True; source exact dict only sha256 with lowercase ASCII 64 hex; provider dict destination == "fake_offline", egress is False; result_mode/model_items_used pair is model_completed/True or regex_fallback/False; unverified_semantic_items list <=500.
4. Encode source strict UTF-8, SHA-256 and compare declared hash before empty list/fallback/output. Bad hash shape => invalid_adapter_result; different exact-shape hash => source_mismatch.
5. Validate every semantic element before filtering: exact dict keys kind/value/evidence/operational_draft_eligible; kind exact technique|malware|actor; value/evidence exact str each 0..8192 UTF-8 bytes; eligibility is False. Structural/type/unknown/encoding failure => whole call invalid_adapter_result. Bound => input_too_large. No str/trim/upper/normalization/bool coercion.
6. regex_fallback requires semantic list empty; model_completed requires True flag but list can empty. Malware/actor validly validate then are omitted. Technique retains list order, duplicate and original item_index.

TechniqueAudit is frozen dataclass with immutable fields only:

    item_index: int; kind: Literal["technique"]; value: str; evidence: str
    evidence_span: tuple[int, int] | None
    source_sha256: str; config: Literal["C2", "C3"]
    quote_status: Literal["matched", "missing", "not_found", "ambiguous"]
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"]
    reason_code: str
    pin_kind: Literal["synthetic", "official"]; snapshot_version: str; snapshot_sha256: str
    semantic_status: Literal["unverified"]; operational_draft_eligible: Literal[False]

Return outer tuple. No mutable catalog dict/list span/keep. Copy pin scalar values from validate_technique lookup. Every record unverified/False even if C3 top-level eligibility true.

Quote exact literal, no regex/NFC/NFD/case/CRLF/whitespace normalization. Empty evidence => missing/span None. Nonempty: source_text.find evidence; second find starts first+1 so overlapping occurrences count; second found => ambiguous/span None, no full scan. One found => matched/[start,end) tuple Python code point; none => not_found. Quote need not contain ID.

Always validate quote and catalog independently. Reason order: missing_evidence > evidence_not_in_source > evidence_ambiguous > invalid_technique_id > unknown_technique_id > catalog_inactive > catalog_active_and_quote_matched. Preserve both statuses. No keep/approval. TtpAuditError codes only: invalid_source_text, input_too_large, invalid_adapter_result, source_mismatch, invalid_catalog; str/repr cannot include raw data/path/marker. No input/catalog mutation and no provider/socket/filesystem/SQLite/logger/network/retry.

## TDD acceptance

1. RED integration path for **both C2 and C3**: ScriptedProvider valid response -> run_extraction -> audit public API with synthetic catalog. Semantic list includes valid technique/malware/actor. Assert provider calls stays one after audit; only techniques emitted with original indexes; source_sha256/config/pin scalars correct; all technique false/unverified even C3 top-level true.
2. RED source-binding: sources A/B share quote but adapter result A; source B raises source_mismatch. Cover mismatch model_completed, regex_fallback and empty list before output. Cover emoji/CRLF/NFC/NFD hash and spans.
3. RED projection: malformed hash/type, extra/missing source or semantic keys, provider/mode/flag pairs wrong; errors exact code/no RAW_MARKER.
4. RED bounds before filtering: 501 mixed valid items, >8192 malware value, oversize source; fail input_too_large. Structural malware/actor failure invalidates whole call.
5. RED content result: empty evidence missing, empty/malformed/lowercase/space/look-alike ID not_checked; missing/wrong type stays structural error distinction.
6. RED quote occurrence: no/one/overlap aaa in aaaa, Unicode code-point span, repeated CRLF and NFC-vs-NFD mismatch.
7. RED catalog: active/inactive/unknown/subtechnique via existing small fixtures; do not claim parent-inactive as accepted catalog state.
8. RED immutability/determinism: deepcopy adapter input/catalog mapping before-after; attempt mutate frozen record/tuple/scalar provenance fails; duplicate technique returns two ordered stable records.
9. RED side effect: fault-injection marker evidence is data; guard socket/SQLite and provider calls; audit causes no extra call/IO.
10. Implement minimal module after RED. Never reuse ground_techniques or mutate adapter/catalog. Do not label mutation tests as adapter integration.

## Commands, report and evidence

Run from worktree with project Python:

    & '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider extractor/tests/test_ttp_audit.py -q
    & '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider extractor/tests/test_llm_adapter.py extractor/tests/test_attack_catalog.py extractor/tests/test_grounding.py extractor/tests/test_evaluate.py extractor/tests/test_eval_cli.py -q
    & '..\cti-platform-start\.venv\Scripts\ruff.exe' check extractor/phonghoa_extractor/ttp_audit.py extractor/tests/test_ttp_audit.py
    & '..\cti-platform-start\.venv\Scripts\ruff.exe' format --check extractor/phonghoa_extractor/ttp_audit.py extractor/tests/test_ttp_audit.py
    git diff --check

Do not rerun official 166 suite only because this seam is documented; official compatibility has separate accepted evidence. If optionally used, asset/hash must be supplied and reported; skip is not PASS. C1/C2/C3/C4 claim requires test_eval_cli; expected C4 remains rejected/documented, unchanged.

After tests: local Conventional Commit, clean tree, no push. Write <root>\PHONG-HOA-X01-TTP-AUDIT-RESULT.md and <root>\x01-ttp-audit-evidence\ with RED/GREEN logs, commands/cwd/interpreter/exit/count, import path, source/base/HEAD/diffstat and SHA-256 manifest; do not copy MITRE snapshot. Report PASS/FAIL/UNVERIFIED, not project completion.

UNVERIFIED: technique semantic truth, C4/RAG, real model/provider, corpus/gold/F1, W05/SQLite/API/UI/OpenCTI, TLP cloud authorization, lab/production.
