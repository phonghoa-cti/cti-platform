# X01-TTP-AUDIT-NEXT — review Leader và yêu cầu R1–R3

Ngày 11/11/2026. **NEEDS_REWORK tài liệu**, chưa giao triển khai.
Request đã trả: `4352741d-a087-4a25-b1e1-4c05b6b3cd1e`; thread `d6aabc06-ecb9-4f74-96d1-d2a82d66701a`.

Root: `$WORKSPACE`.
Source chỉ đọc: `cti-x01-attack-official`, HEAD `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`.

Hai tài liệu được review:
- Research SHA-256 `D9AFCC2F01BB786A57E44DD488775A506B9CC9DBA48F70D9F23E22738A9627D0`.
- Implementation brief SHA-256 `5CA264049E6149B32FF62B22B10BB463D27C582DC0B4FD205569D608C3912D44`.

Giữ phương án B: hàm audit thuần, opt-in sau adapter; tái dùng catalog/lookup đã nghiệm thu; không thay default C1–C3, không thêm CLI/dependency. Không coi catalog/quote matched là đúng nghĩa TTP hay hoàn tất RAG/C4.

## R1 — ràng buộc đúng nguồn và định nghĩa phần input được kiểm

**Finding quan trọng:** Research:47–49,65 và Brief:31–39 không quy định đối chiếu `adapter_result.source.sha256` với `source_text`, dù brief giao nghiên cứu yêu cầu source mismatch. Adapter thực đã có hash tại `llm_adapter.py:253`. Ví dụ: output sinh từ nguồn A, truyền nguồn B cũng có cùng quote; chỉ kiểm quote sẽ xác nhận nhầm nguồn. Thiếu quy tắc cả khi list rỗng/fallback.

Chốt của Leader:
- API nhận **dict chuẩn** từ adapter; sửa annotation cho khớp phạm vi. Đây là kiểm một tập trường cần cho audit, không tuyên bố xác thực toàn bộ adapter result hay nguồn gốc mật mã của object trong RAM.
- Các trường bắt buộc: `schema_version == "1.0"`, `config` exact str C2/C3, `mock_only is True`, `source` dict đúng một key sha256 (exact str, ASCII lowercase 64 hex), `provider` dict có `destination == "fake_offline"` và `egress is False`, `result_mode`, `model_items_used`, `unverified_semantic_items`.
- `model_completed` đi cùng `model_items_used is True`; `regex_fallback` đi cùng False và semantic list rỗng. Cặp khác bị từ chối. Provider có các metadata name/model_id do adapter sinh; không copy chúng thành quyền hay xác thực danh tính.
- Các field top-level khác (IOC, purpose, language, TLP, attempts, warnings, error_codes...) và metadata provider ngoài hai field trên được phép tồn tại, không được kiểm/diễn giải bởi audit. Ghi rõ phạm vi này; đừng gọi toàn result “strict exact schema”. Không đọc top-level eligibility để quyết định quyền technique.
- Source exact str không rỗng, tối đa 1 MiB UTF-8, không normalization. Kiểm bound ký tự trước encode để tránh tạo bản UTF-8 vô hạn; lỗi encode Unicode trả lỗi an toàn. Tính SHA-256 UTF-8 và so với declared hash **trước mọi return rỗng/quote matching**. Hash malformed: invalid_adapter_result; hash đúng dạng nhưng không bằng: source_mismatch.
- Mỗi output record có `source_sha256` đã so và `config`. Hash là consistency check, không chứng minh provider hay văn bản có nguồn tin cậy.

## R2 — thống nhất lỗi cấu trúc, lỗi nội dung và danh sách trộn

**Finding:** Research:56–57,61 hứa trả record cho missing/wrong-type nhưng Research:65 và Brief:32–33 lại yêu cầu raise; evidence phải 1..8192 nhưng vẫn cần empty/missing_evidence. Brief:31 nói lọc technique còn :32 bắt mọi kind là technique; output adapter thực có cả malware/actor (`llm_adapter.py:301–317`).

Chốt của Leader:
- `unverified_semantic_items` là list chuẩn, tối đa 500 **trước lọc**. Mỗi phần tử dict chuẩn, đúng bốn key kind/value/evidence/operational_draft_eligible; kind exact str trong technique/malware/actor; value/evidence exact str, từng field tối đa 8192 UTF-8 bytes; eligibility **is False**, không bool coercion.
- Thiếu key, extra key, sai kiểu, unknown kind, eligibility sai: raise invalid_adapter_result cho cả call, không trả một phần. Validate cấu trúc/bounds tất cả item trước tạo kết quả.
- Với string hợp lệ về kiểu/bound: ID empty/malformed/lowercase/space/look-alike trả catalog not_checked/invalid_technique_id; evidence empty trả quote missing/missing_evidence. Vì vậy bound evidence là **0..8192**, không 1..8192. Empty string là ca kiểm phòng lỗi ở audit, không tuyên bố public adapter bình thường phát sinh nó.
- Malware/actor qua kiểm cấu trúc rồi bỏ khỏi kết quả technique; không audit nghĩa hay tạo record technique giả. Giữ thứ tự technique và duplicate; thêm `item_index` bằng vị trí trong list gốc để truy vết khi lọc.
- Error taxonomy hữu hạn: invalid_source_text (kiểu/rỗng/Unicode source), input_too_large (mọi bound vượt), invalid_adapter_result (cấu trúc/kiểu/encoding semantic field), source_mismatch, invalid_catalog (catalog sai type). str/repr lỗi chỉ code, không raw text/path, không coercion.
- Catalog là object do public `load_catalog` đã kiểm, không phải dữ liệu model. Kiểm đúng type AttackCatalog; không xây lại loader hay hứa xác thực catalog tự dựng/đã bị can thiệp trong RAM. Loader error xảy ra ngoài seam giữ nguyên. Active-child/inactive-parent bị loader từ chối parent_conflict; sửa hàng “inactive kể cả parent inactive” để không mâu thuẫn policy đã nghiệm thu.

## R3 — immutable output, quote lặp chồng nhau và tiêu chí kiểm

**Finding:** Research:49/Brief:36 mô tả frozen record nhưng catalog dict/span list vẫn có thể sửa; “nhiều lần” chưa chốt occurrence chồng nhau. Ví dụ quote `aaa` trong source `aaaa` có hai vị trí, str.count sẽ đếm một.

Chốt của Leader:
- Ghi dataclass frozen với type từng field. `evidence_span` là tuple[int,int] hoặc None; outer return tuple. Bỏ nested mutable catalog dict, dùng ba scalar như lookup: `pin_kind`, `snapshot_version`, `snapshot_sha256`. Các trường khác: item_index, kind literal technique, value/evidence bounded str, source_sha256, config, quote_status, catalog_status, reason_code, semantic_status literal unverified, operational_draft_eligible literal False.
- Exact literal, tính cả occurrence chồng nhau: tìm lần đầu, tìm lần hai từ start+1; có lần hai => ambiguous/span None, không cần quét toàn bộ. Empty xử lý riêng. Không regex/NFC/NFD/case/CRLF normalization.
- Quote và catalog được đánh giá độc lập. Reason precedence: missing_evidence, evidence_not_in_source, evidence_ambiguous; chỉ khi quote matched mới dùng invalid_technique_id / unknown_technique_id / catalog_inactive / catalog_active_and_quote_matched. Giữ cả hai status.
- Bổ sung acceptance cases: A/B cùng quote nhưng khác source hash; mismatch ở fallback/list rỗng; UTF-8 hash emoji/CRLF/NFC-NFD; malformed hash/types và cặp mode/flag sai; mixed kinds + original index; cap trước lọc; empty string khác missing/wrong type; overlapping quote; mutation attempt lên record/span/provenance; C3 top-level true nhưng mọi technique false.
- Demo phải dùng public ScriptedProvider → run_extraction C2 **và** C3, semantic items trộn hợp lệ, rồi audit public; calls không tăng. Invalid input dùng mutation có nhãn fault injection. Không gán output không thể do adapter sinh là integration thành công.
- Giữ tests liên quan: new test_ttp_audit, test_llm_adapter, test_attack_catalog, test_grounding, test_evaluate, **test_eval_cli** cho claim regression C1–C3/C4. Không cần lặp official suite 166 chỉ vì tài liệu đổi; official compatibility đã nghiệm thu riêng. Nếu thêm official demo thì phải cấp đúng asset/hash và ghi rõ thực chạy, không gọi skip là PASS. Ruff/format áp dụng mọi file Python thực đổi. Trong rework nghiên cứu này **không chạy test/code**.

## Nguồn và phạm vi kiểm của Leader

Leader đã đối chiếu trực tiếp source public adapter/catalog và đọc hai tài liệu, không chạy implementation chưa tồn tại. Ngày 11/11/2026 mở lại:
- [MITRE ATT&CK Data & Tools](https://attack.mitre.org/resources/attack-data-and-tools/): STIX machine-readable và truy cập dữ liệu.
- [MITRE STIX USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md#access-local-content): local copy static, dùng lại loader hiện có.
- [Lewis et al. RAG](https://arxiv.org/abs/2005.11401): retrieval tham gia generation; post-hoc lookup không đáp ứng điều đó (nhận định áp dụng của Leader).
Các quy tắc hash/schema/bounds/quote/error ở trên là **quyết định thiết kế Phong Hỏa**, không gán cho MITRE.

## Rework được giao

CTI Research chỉ sửa đúng hai tài liệu đã trả, đồng bộ R1–R3; không sửa review này/RUNS/repo, không tạo worktree/commit, không test/model/lab/dependency/download. Giữ nguồn và quyết định tái dùng còn phù hợp; không nghiên cứu framework mới. Trả mapping R1–R3 → file:line, hai SHA-256, HEAD/status trước-sau và giới hạn research-only. Sau nghiệm thu Leader mới giao một CTI AI Agent/Sol medium triển khai.
