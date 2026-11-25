# X01 TTP audit offline — catalog, quote và source binding

Ngày đối chiếu: 11/11/2026 (Asia/Saigon). Đây là research/brief, không phải C4/RAG hay đánh giá chất lượng TTP.

## Kết luận

**Giữ phương án B:** hàm audit opt-in, thuần offline, nhận projection đã định nghĩa của kết quả thực run_extraction() cùng AttackCatalog đã nạp; không sửa adapter/C1–C3. Nó tách ba mệnh đề:

| Điều kiểm | Evidence | Kết luận được phép |
|---|---|---|
| ID ATT&CK tồn tại/còn active | validate_technique(catalog, id) | Chỉ trạng thái catalog pin |
| Quote thuộc đúng source adapter đã xử lý | source SHA-256 UTF-8 khớp, rồi source[span[0]:span[1]] == evidence | Chỉ consistency + khớp câu chữ |
| Hành vi là technique đó | corpus gán nhãn/evaluation TTP | **Chưa kiểm**, không suy từ hai dòng trên |

Mỗi output technique luôn semantic_status="unverified" và operational_draft_eligible=false. Audit sau generation không có retriever/context đi vào generation; không gọi là RAG/C4, không auto keep/approve.

## Hiện trạng và tái sử dụng

Source chỉ đọc: cti-x01-attack-official, branch feat/x01-attack-official-20261111, HEAD 4001441edcf5414df0f06c34352f6c5d3e2a2bd5; status sạch.

- attack_catalog.py: validate_technique() strict ASCII Tdddd/Tdddd.ddd và trả active/inactive/unknown/not_checked kèm pin; catalog/records immutable; semantic unverified, eligible false.
- llm_adapter.py: run_extraction() tạo source.sha256 bằng UTF-8 tại _base_result(), dùng ScriptedProvider deterministic/no-egress, và đưa technique/malware/actor vào unverified_semantic_items. C3 top-level eligibility là cờ IOC grounded, không áp cho technique.
- evidence.py là evidence IOC vì bắt quote chứa IOC normalized, không dùng cho technique.
- grounding.py: ground_techniques() str/strip/upper ID, không kiểm quote/active và có keep mặc định; không tái dùng.
- Catalog official v20.1 đã được nghiệm thu riêng: SHA-256 539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5; 867 record, 706 active, 161 inactive, 497 sub-technique. Đây không là semantic proof.

MITRE mô tả ATT&CK STIX là machine-readable knowledge base và local versioned copy tránh catalog thay đổi ảnh hưởng workflow. [Data & Tools](https://attack.mitre.org/resources/attack-data-and-tools/), [STIX usage](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md). stix2/MemoryStore phù hợp query phức tạp nhưng thêm dependency không cần trong seam exact-ID này. Lewis et al. định nghĩa RAG là retrieval trên non-parametric memory kết hợp generation; post-hoc lookup không đáp ứng điều đó. [Lewis et al.](https://arxiv.org/abs/2005.11401).

| Cách | Dùng lại | Trade-off | Quyết định |
|---|---|---|---|
| A. Helper dict | ground_techniques() | Không chứng minh adapter binding; coercion/keep nguy hiểm | Không chọn |
| B. Audit opt-in sau adapter | adapter public + catalog lookup | Deterministic, bounded, demo đường thật, no dependency | Không semantic/RAG | **Chọn** |
| C. C4/RAG đầy đủ | STIX + retriever/context/generator/corpus | Có giá trị benchmark sau | Cần thiết kế/evidence lớn hơn | Hoãn |

## Contract và projection input

Module mới: extractor/phonghoa_extractor/ttp_audit.py.

    def audit_techniques(
        *, adapter_result: dict[str, object], source_text: str, catalog: AttackCatalog
    ) -> tuple[TechniqueAudit, ...]: ...

Đây là **validation của projection audit**, không xác thực toàn adapter result hay provenance mật mã object trong RAM. Các top-level khác như iocs, purpose, language, tlp, attempts, warnings, error_codes và provider metadata ngoài hai field bên dưới được phép tồn tại nhưng audit không đọc/diễn giải.

| Field | Quy tắc |
|---|---|
| schema_version | exact str "1.0" |
| config | exact str "C2" hoặc "C3"; copy vào mỗi output |
| mock_only | is True |
| source | exact dict chỉ key sha256; hash exact str ASCII lowercase 64 hex |
| provider | dict, destination == "fake_offline", egress is False |
| result_mode/model_items_used | model_completed đi với is True; regex_fallback đi với is False và semantic list rỗng; cặp khác invalid_adapter_result |
| unverified_semantic_items | list <=500 trước lọc; validate tất cả item trước tạo output |

source_text phải exact str, non-empty. Kiểm length character bound trước encode, rồi encode UTF-8 strict; lỗi type/rỗng/Unicode encoding là invalid_source_text; mọi bound quá 1 MiB source hoặc 8192 UTF-8 bytes semantic field là input_too_large. Tính SHA-256 bytes UTF-8 và so với source.sha256 **trước mọi return**, gồm semantic list rỗng/fallback. Hash sai dạng là invalid_adapter_result; hash đúng dạng nhưng khác là source_mismatch. Hash là consistency check, không xác thực provider hay trust của text.

Mỗi semantic item phải là exact dict có đúng bốn keys kind, value, evidence, operational_draft_eligible. kind exact one of technique/malware/actor; value/evidence exact str 0..8192 UTF-8 bytes; eligibility is False. Thiếu/extra key, sai type, unknown kind, eligibility sai hoặc semantic encoding lỗi: toàn call raise invalid_adapter_result. Không coercion str/trim/uppercase/NFC-NFD. Malware/actor qua validation rồi bị lọc không tạo audit record. Technique giữ original list order, duplicate và item_index vị trí gốc.

catalog là boundary trusted-loader: kiểm type AttackCatalog, nếu sai invalid_catalog; không xây lại loader/không hứa xác thực catalog tự dựng/đã bị can thiệp trong RAM. AttackCatalogError khi load nằm ngoài seam và không bị đổi.

## Output, quote và policy

TechniqueAudit phải dataclass(frozen=True), chỉ scalar immutable hoặc tuple:

    item_index: int
    kind: Literal["technique"]
    value: str
    evidence: str
    evidence_span: tuple[int, int] | None
    source_sha256: str
    config: Literal["C2", "C3"]
    quote_status: Literal["matched", "missing", "not_found", "ambiguous"]
    catalog_status: Literal["active", "inactive", "unknown", "not_checked"]
    reason_code: str
    pin_kind: Literal["synthetic", "official"]
    snapshot_version: str
    snapshot_sha256: str
    semantic_status: Literal["unverified"]
    operational_draft_eligible: Literal[False]

Outer return tuple; không nested catalog dict/span list/keep. Không mutable provenance. Không mutate adapter_result, source_text hay catalog mapping.

Quote literal exact, no regex/NFC/NFD/case/CRLF/whitespace normalization; offset [start,end) là Python Unicode code point. evidence empty => missing. Với evidence nonempty, tìm start đầu; tiếp tục tìm từ start+1 để tính occurrence chồng nhau: lần hai tồn tại => ambiguous/span None (ví dụ aaa trong aaaa); không cần quét thêm. Một occurrence => matched/span; không có => not_found/span None. Quote không cần chứa Txxxx.

Quote và catalog độc lập. Reason precedence: missing_evidence, evidence_not_in_source, evidence_ambiguous; **chỉ quote matched** mới dùng invalid_technique_id, unknown_technique_id, catalog_inactive, catalog_active_and_quote_matched. Giữ cả quote_status và catalog_status. ID empty/malformed/lowercase/space/look-alike là valid string item nhưng catalog not_checked/invalid_technique_id. Active subtechnique có parent inactive/orphan bị loader từ chối parent_conflict; không tuyên bố trạng thái “inactive kể cả parent inactive”.

Taxonomy finite/code-only: invalid_source_text, input_too_large, invalid_adapter_result, source_mismatch, invalid_catalog. TtpAuditError str/repr chỉ code; không raw source/item/path/marker. String empty là content result policy; missing/wrong type là structural fail.

## Matrix acceptance

| Nhóm | Ca bắt buộc | Evidence kỳ vọng |
|---|---|---|
| Source binding | A/B cùng quote khác hash; mismatch fallback/list rỗng | source_mismatch trước empty/quote return |
| UTF-8 | emoji, CRLF, NFC/NFD | hash exact bytes; code-point span exact, no normalization |
| Projection | malformed hash/types; mode/flag pair sai | invalid_adapter_result code-only |
| Mixed list | technique/malware/actor hợp lệ, duplicate | only techniques; item_index gốc/order giữ |
| Bound | 501 mixed items trước lọc; long source/value/evidence | input_too_large trước filtering |
| Content | empty ID/evidence; malformed/lowercase/space/look-alike | not_checked or missing result, không raise |
| Quote | absent/one/overlap aaa-in-aaaa | not_found/matched/ambiguous đúng |
| Lifecycle | active/inactive/unknown/subtechnique | lookup giữ unverified/false |
| Immutability | attempt mutate record/span/provenance + deep-copy input | frozen/tuple/scalars; input unchanged |
| Path thực | ScriptedProvider → run_extraction C2 và C3 semantic list mixed → public audit | calls không tăng; C3 top-level true nhưng technique false |
| Safety/regression | marker, socket/DB/provider guard; adapter/catalog/grounding/evaluate/eval_cli | no side effect; C1–C3 unchanged/C4 reject |

Không gán F1, precision hay quality model/TTP cho fixture. Demo chỉ chứng minh wiring/contract.

## Ranh giới

Offline fake only: không model/egress/cloud/secret/SQLite/W05/API/UI/OpenCTI/lab/deploy. TLP:GREEN không tự cho phép cloud. UNVERIFIED: semantics, C4/RAG, real model/corpus/gold/F1, catalog release khác, runtime/production.
