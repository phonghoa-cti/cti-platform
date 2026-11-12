# X01-GOLD-PILOT-IMPLEMENT — quyết định và hợp đồng cuối của Leader

Ngày 11/11/2026. **Chấp nhận nghiên cứu sau R1–R5 kèm phần chốt dưới đây để triển khai.** Đây là nghiệm thu tài liệu, chưa có code/test gold-pilot.

## Căn cứ và phạm vi

Root = `$WORKSPACE`.

- Research SHA-256 `6FCF48CD2B7833CFB4F4E066CBC155B8A2424DA9453016EC6DA6E5DFFB97536A`.
- Implementation brief SHA-256 `B54959EC60F76C2AB18FA2C9537AD3D0485896B6EBB7EA8FADCE3DA2799E6024`.
- Hai hash khớp callback `aad3f362-0182-415f-888d-a987c821f1a0`. Leader đọc toàn văn, đối chiếu review R1–R5 và code hiện có. Source kiểm fresh vẫn sạch tại `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`.
- Giữ phương án validator/readiness offline, 5 record. Research đã sửa reuse catalog, trạng thái, evidence, inventory và target. Bản rút gọn còn thiếu DTO/output exact và vài bounds; Leader chốt tại đây, không giao thêm một vòng nghiên cứu.
- Nguồn TRAM annotation/best practices đã được Leader mở và kiểm trong lượt trước; không nghiên cứu lại. Chỉ kế thừa nguyên tắc gán nhãn độc lập/adjudication, không suy ra quyền từng raw report.

Một worker CTI AI Agent, GPT-5.6 Sol medium, làm trực tiếp không giao bot/agent khác. Tạo target `<root>\cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111` từ source read-only `<root>\cti-x01-c4-eval` exact base trên. Target chưa tồn tại khi Leader kiểm. Nếu có sẵn thì kiểm ownership/base/status, không reset hay ghi đè.

Đọc AGENTS.md, docs/PROGRESS.md, X01 spec và hai tài liệu nghiên cứu/brief. Quyền triển khai cục bộ đã có; không xin lại giữa các bước đã giao. Viết spec/test RED trước implementation, GREEN và kiểm liên quan, commit cục bộ, demo đúng HEAD, evidence. Không push/PR/merge/deploy, model/mạng/cloud/lab, dữ liệu thật, dependency, C1–C4/HTTP/DB/UI.

Allowlist giữ nguyên brief: library `extractor/phonghoa_extractor/gold_pilot.py`, CLI `extractor/dataset/check_gold_pilot.py`, test `extractor/tests/test_gold_pilot.py`, synthetic fixtures `extractor/tests/fixtures/gold_pilot/**`, spec `docs/specs/X01-gold-pilot-v1.md`, ADR `docs/adr/0010-x01-gold-pilot-readiness.md`, `docs/PROGRESS.md`. Không sửa file cũ khác, sổ/review/acceptance Leader. Tài liệu và giải thích bằng tiếng Việt.

## Schema cuối (ưu tiên file này khi tài liệu cũ viết tắt)

Mọi key liệt kê là bắt buộc trừ mục ghi optional; reject key khác ở mọi cấp. Tên viết tắt `schema/id` trong research nghĩa là `schema_version` và `id`. Không coerce string/number/bool.

- `ID64`: str fullmatch ASCII `[a-z0-9][a-z0-9-]{0,63}`; `ID32` tương tự max32; `HASH`: str 64 lowercase hex. `DATE`: str exact YYYY-MM-DD và calendar-valid. Chuỗi text sử dụng không chứa NUL/lone surrogate. `bool` đúng kiểu; integer là `type(x) is int`, không bool.
- Manifest keys: `schema_version="gold-pilot-v1"`, `dataset_id:ID64`, `purpose="human-annotation-pilot"`, `provenance="synthetic-fixture"|"human-supplied"`, `document_count:int=5`.
- Record keys: `schema_version="gold-pilot-v1"`, `id:ID64`, `source`, `language="vi"|"en"`, `tlp="TLP:CLEAR"|"TLP:GREEN"`, `raw`, `duplicate_group:ID64`, `split="pilot"`, `attack`; optional `translation_of:ID64` (null không hợp lệ).
- Source exact keys: `url` (str 1..2048 code points, HTTPS, có host, không userinfo/control/whitespace), `publisher` (str 1..256, không control), `published_date:DATE`, `retrieved_at:DATE`, `source_license` thuộc public-domain/cc-by-4.0/cc-by-sa-4.0/publisher-permission/unknown, `storage_right` thuộc repo-allowed/local-only/link-only/prohibited. published <= retrieved; không dùng ngày hiện tại. Đây là khai báo, không xác nhận quyền thật.
- Raw exact keys `present:bool, sha256:HASH|null`. present=true bắt buộc hash/file `raw/<id>.txt`, kiểm đúng hash normalized LF. false bắt buộc null, không file và không annotation. Local/repo-allowed được phép absent (NOT_READY); link-only bắt buộc absent; unknown licence bắt buộc link-only; prohibited luôn INVALID.
- Attack exact keys `version:str, sha256:HASH`; version phải bằng `pin.version` của catalog đã load, không so release_tag và không ép thêm chữ v. Chỉ Enterprise catalog của loader hiện có. Synthetic-fixture chỉ synthetic pin, human-supplied chỉ official pin. Official hiện chỉ exact v20.1; không mở rộng support.
- Annotation exact keys `schema_version="gold-pilot-v1"`, `id:ID64`, `annotator_id:ID32`, `annotated_at:DATE`, `attack_version:str`, `raw_sha256:HASH`, `iocs:list`, `ttps:list`; optional `no_findings:bool`. Date >= record.retrieved_at, version/hash bằng record. Hai list tối đa256 mỗi loại; no_findings=true iff cả hai list rỗng; false/absent chỉ hợp lệ khi ít nhất một item tồn tại.
- IOC exact keys `type:str` trong tám giá trị `IocType` hiện có, `value:str` 1..2048, `role="attacker"|"victim"|"benign"`, `evidence:list`. normalize(value) phải khớp type/value đã khai. Không thêm support private/special IP mà normalizer từ chối. Duplicate canonical(type,value,role) trong annotation là INVALID.
- TTP exact keys `attack_id:str`, `evidence:list`. Gọi validate_technique; chỉ catalog_status active hợp lệ. Malformed/unknown/inactive INVALID. Duplicate ID INVALID; parent/sub distinct, không suy diễn quan hệ semantic.
- Evidence list 1..16 mỗi item; exact keys `start:int,end:int,quote_sha256:HASH`; 0<=start<end<=len(normalized_text), end-start<=2048. Quote SHA bằng UTF-8 substring. IOC substring là token và normalize(substring)==item type/value. TTP chỉ kiểm substring/hash, semantic luôn unverified. Duplicate tuple trong item INVALID, overlap giữa item khác nhau hợp lệ.
- Text raw decode UTF-8 strict, đổi CRLF/CR thành LF, không strip/NFC/NFKC; hash/span theo text đó. Giới hạn bytes kiểm trên file gốc trước decode. JSON strict no BOM/duplicate/nonfinite/recursion; bắt lỗi Unicode/JSON an toàn, không echo dữ liệu qua exception normalizer.

## Inventory, trạng thái và phép đo

Dataset root là directory. Bắt buộc manifest.json, records/, annotations/, raw/; optional .gitignore và adjudications/, suggestions/ rỗng. Không directory con sâu hơn, file lạ/orphan; metadata tên `<id>.meta.json`, annotation `<id>.<annotator_id>.json`, raw `<id>.txt`. Đúng5 metadata ID khác nhau, 0..2 annotation/record; >2 hoặc duplicate annotator INVALID. Bounded enumeration tối đa22 file, dừng sớm khi vượt cap; tổng bytes <=8MiB, JSON <=256KiB, raw <=512KiB, .gitignore <=4KiB. Pin <=16KiB và snapshot <=64MiB ngoài dataset. Không đọc file lớn rồi mới kiểm cap. .gitignore chỉ hash bytes, không diễn giải nội dung.

Kiểm lstat và Windows reparse trước resolve trên paths/ancestors, không theo symlink/junction; reject file nlink!=1 hoặc nonregular. Input snapshot/pin cũng phải regular an toàn. Directory traversal từ chối, containment resolved bắt buộc. Không hỗ trợ hostile mutation giữa kiểm tra và mở file, network share hay crash/power-loss guarantee.

translation_of trỏ original có thật khác ID, cùng group, original không có translation_of; không cycle/chain. Chỉ pilot, không hứa đã phát hiện trùng nội dung hoặc dev/holdout leakage.

Record reasons theo thứ tự cố định `NEEDS_RIGHTS`, `NEEDS_LOCAL_RAW`, `NEEDS_SECOND_ANNOTATION`:
- NEEDS_RIGHTS iff licence unknown hoặc storage link-only.
- NEEDS_LOCAL_RAW iff raw absent.
- NEEDS_SECOND_ANNOTATION iff số annotation <2 (cả trường hợp0).

Sau khi tất cả input hiện có được kiểm hợp lệ, record reasons rỗng => record READY_FOR_ADJUDICATION; ngược lại NOT_READY. Record với hai no-findings vẫn READY về hồ sơ, cả hai dimension both_empty. **NO_FINDINGS_ONLY chỉ là dataset reason**, không record reason (làm rõ dòng research còn nhập nhằng).

Dataset reasons theo thứ tự `RECORDS_NOT_READY`, `NO_FINDINGS_ONLY`: reason đầu iff có record NOT_READY; reason sau chỉ iff cả5 READY và tổng IOC union + TTP union ==0. Dataset READY iff reasons rỗng. Không ngưỡng agreement 80%.

Mỗi record đủ điều kiện tính set attacker IOC triples và exact TTP IDs; dimension có union>0 => available, ratio=round(intersection/union,6); union0 => both_empty, ratio=null, counts0. Record NOT_READY => unavailable, intersection/union/ratio đều null. Cohort cộng counts của record READY duy nhất, evaluated_record_count đếm các record đó; 0 record => unavailable/nulls; có record nhưng union0 => both_empty/counts0. Đây là agreement giữa nhãn khai báo, không precision/recall/model F1.

## Public API và report exact

Giữ `validate_gold_pilot(dataset: Path, snapshot: Path, pin_path: Path) -> GoldPilotReadiness`. Kết quả frozen dataclass giữ `status`, `payload:bytes`, `dataset_root:Path`, `protected_inputs:tuple[Path,...]` (toàn bộ dataset files + pin + snapshot). Payload xây từ dữ liệu đã kiểm; đường dẫn chỉ nằm trong DTO nội bộ, không serialize vào report. Hàm không ghi file.

`write_readiness(report: GoldPilotReadiness, output: Path, *, protected_inputs: tuple[Path,...]=()) -> WriteResult` gộp input bảo vệ có sẵn trong DTO với tuple bổ sung, caller không thể vô hiệu hóa bảo vệ bằng tuple rỗng. `WriteResult` frozen có `published:bool=True`, `cleanup_warning:bool`. CLI dùng đúng API, không có validation bypass riêng. DTO không phải cơ chế authentication với mã Python thù địch trong cùng process.

Payload JSON exact root keys:
`schema_version="gold-pilot-readiness-v1"`, `status`, `reasons`, `dataset_id`, `provenance`, `document_count=5`, `dataset_input_sha256`, `attack_pin_sha256`, `attack_snapshot_sha256`, `catalog_kind="synthetic"|"official"`, `records`, `cohort`, `limitations`.

Record output exact keys: `id,status,reasons,ioc_agreement,ttp_agreement,ttp_catalog_status,semantic_status`. ttp_catalog_status=`active` nếu có ít nhất một TTP đã validate trong record, `no_techniques` nếu không; không suy semantic. semantic_status=`unverified`. Agreement exact keys `status,intersection,union,ratio` theo mục trên. Cohort exact keys `evaluated_record_count,ioc_agreement,ttp_agreement,deduplication="declared-only"`. Records sắp lexical ID. Limitations là list cố định theo thứ tự: `declared-rights-only`, `annotator-independence-unverified`, `declared-deduplication-only`, `not-gold`, `no-semantic-ttp-validation`, `no-model-quality-claim`.

dataset_input_sha256 = SHA256 UTF-8 JSON compact ensure_ascii=True của list các cặp `[relative_posix_path,sha256(original_file_bytes)]` sắp lexical path, không LF. Bao gồm mọi file chấp nhận kể cả .gitignore; không bao gồm empty dirs. Pin hash tính bytes gốc; snapshot hash từ bytes loader kiểm. Report bytes = json.dumps(payload_dict,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8') + b'\n'. Không raw, quote, value, URL, publisher, annotator IDs, path, free-text version, exception, timestamp hoặc evaluator.git_ref.

## Lỗi và writer

GoldPilotError.code đóng: invalid_arguments, invalid_inventory, invalid_manifest, invalid_record, invalid_annotation, invalid_raw, invalid_pin, invalid_catalog, invalid_technique, unsafe_output, io_failure. Library giữ code an toàn. Missing required path/file là invalid_* tương ứng; permission/read/write/fsync lỗi là io_failure. AttackCatalogError snapshot_io_error -> io_failure, các lỗi catalog còn lại -> invalid_catalog; invalid pin DTO/JSON -> invalid_pin. Không in traceback cho input/I/O dự kiến.

CLI args --dataset --attack-snapshot --attack-pin --report bắt buộc; --help được phép. Invalid arguments chỉ stderr JSON `{"error":"invalid_arguments"}` +LF, exit2, không echo argv. Trình tự: validate args/paths + bounded inventory; strict pin/load catalog; manifest/records/annotations theo lexical ID; build report; writer output preflight/publish. CLI stdout READY/NOT_READY một JSON `{"status":"..."}` +LF sau publish. Invalid_* stderr `{"error":"<code>"}` +LF, exit2, không report; io_failure tương tự exit1. NOT_READY publish thành công exit2; READY publish thành công exit0.

Writer từ chối output đang tồn tại, bên trong dataset, alias lexical/resolved/samefile của mọi input, parent không tồn tại/unsafe. Temp same parent, flush/fsync, os.link no-clobber là commit point. Lỗi trước commit giữ input/output cũ, cleanup temp owned best effort. Sau os.link thành công, cleanup temp lỗi => WriteResult(published=True,cleanup_warning=True), stderr `{"warning":"cleanup_incomplete"}`; exit vẫn theo READY/NOT_READY, không báo io_failure giả như chưa publish. Worker phải dọn đúng temp owned trong evidence run cuối hoặc báo rõ còn gì; không xóa ngoài ownership. Không os.replace/overwrite trong lát này.

## Kiểm tra và bàn giao

Test RED trước code gồm happy/partial/invalid/rights/provenance, JSON/size/types, Unicode CRLF/emoji, IOC token mismatch, inactive/unknown TTP, no-findings/cohort, translation, links/aliases, fingerprint mutation, before/after link fault, API/CLI parity và hash input bất biến. Các case synthetic không giả hai người thật. Fault injections vào writer không được đổi output semantics.

Trong target: `$py='<root>\cti-platform-start\.venv\Scripts\python.exe'`; PYTHONPATH trỏ core/extractor target. Set `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT=<root>\x01-attack-real-research-evidence\enterprise-attack-20.1.json`, file đã có; kiểm size55,277,605/hash539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5. Không copy/download. Với asset env, regression official không skip.

Chạy new test_gold_pilot.py rồi đúng 6 regression files trong brief, Ruff check/format trên3 Python files, diff-check base..HEAD, source/target status. Không tự thêm full suite khi không có vấn đề mới. Demo READY, NOT_READY, INVALID bằng fixture giả; một compatibility demo input giả nhưng pin official có thể gọi library với manifest human-supplied chỉ như test dữ liệu khai báo, ghi rõ không corpus/humans thật. Chạy hai output mới byte-identical, giữ input hashes. Không cần chạy model/browser.

Result `<root>\PHONG-HOA-X01-GOLD-PILOT-RESULT.md`; evidence `<root>\x01-gold-pilot-evidence\`: commands/exit/JUnit, RED/GREEN, demo, fingerprint/input hashes, manifest, base/HEAD/branch/diffstat/status. Local commit đúng scope, source sạch không đổi; target sạch. Không đặt evidence tạm ngoài allowlist source; lưu evidence tại root đã giao. Self-review trước bàn giao, Leader sẽ kiểm độc lập; không tự ghi nghiệm thu.

UNVERIFIED: quyền raw corpus thật, hai annotator thật độc lập, semantic TTP, corpus gold/model/RAG quality, chữ ký catalog release, hostile file mutation, crash/power-loss, cloud/lab/OpenCTI/production. Những giới hạn này không chặn kiểm cơ chế offline đã giao.
