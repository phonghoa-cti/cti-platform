# X01-GOLD-DATASET-NEXT — Leader review R1–R5

Ngày: 11/11/2026. Kết luận: **REWORK tài liệu**, giữ phương án 3, chưa giao implementation.

## Bằng chứng và quyết định

- Source chỉ đọc `cti-x01-c4-eval`, HEAD `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`; Leader kiểm fresh HEAD và `git status --short`: sạch.
- Research SHA-256 đầu vào: `5BA7ACE25CE6206F011EB32A1597E2C213EEF84F988CB63CCEBDBAF46D2A3128`.
- Brief SHA-256 đầu vào: `5BEFC9AD50E29381A741DC6320D2793ADCA82824CE37494B83EC172794AB18AA`.
- Đã kiểm các cuộc mở: chỉ Leader cuộc hiện tại đang chạy; Research đã trả kết quả, idle. Không giao trùng.
- Lịch tiếp tục vẫn enabled, chu kỳ 30 phút; lượt 13:56 trả NOTHING NEW, lượt kế 14:26 giờ Việt Nam. Đây không phải bằng chứng chạy validator.
- Tái sử dụng normalizer và catalog đã nghiệm thu. Không tải corpus, gọi model, đổi C1–C4, phát hành hay mở lab.

## R1 — Pin/catalog trái mã nguồn và nguồn annotation chưa kiểm được

Brief:72 yêu cầu `kind=mitre-attack-stix-pin`, URL `github.com/...` rồi hoãn parser. Mã thật `attack_catalog.py:17-24,132-183` nhận `kind=synthetic|official`; pin official đã duyệt có `version=20.1`, `release_tag=v20.1`, URL immutable `raw.githubusercontent.com/.../f59b03ec.../enterprise-attack-20.1.json`. `load_catalog` tại :517 và `validate_technique` tại :567 đã có. Research:112 yêu cầu active membership nhưng brief chỉ regex. Làm theo brief hiện tại sẽ từ chối asset hợp lệ và không thực hiện kiểm catalog mà research hứa.

Chốt sửa:

- CLI có đủ `--dataset --attack-snapshot --attack-pin --report`. Đọc pin JSON strict tối đa 16 KiB đúng bảy field của `SnapshotPin`; tạo DTO rồi tái dùng `load_catalog` và `validate_technique`. Không parser STIX thứ hai, không sửa catalog/evaluator, không tải asset. Giữ cap snapshot 64 MiB của loader.
- Dùng `attack.version == pin.version` thay tên release nhập nhằng; annotation dùng `attack_version`, bỏ lỗi chính tả `attck_release`. Metadata SHA bằng pin và bytes snapshot đã kiểm. Pin official hiện chỉ v20.1 được hỗ trợ theo code; không hứa mọi release.
- TTP malformed/unknown/inactive không được READY; chốt là INVALID với mã an toàn trong lát này. Parent/sub là ID khác nhau, không tự suy parent. Active membership chỉ chứng minh tồn tại trong catalog, semantic vẫn unverified.
- Manifest thêm provenance khai báo `synthetic-fixture|human-supplied`; phản ánh nguyên enum trong report. Chỉ synthetic-fixture được dùng synthetic pin; human-supplied phải official. Fixtures phải ghi rõ là dữ liệu giả, không phải hai người thật hay corpus gold.
- Link `https://ctid.io/tram/annotation/` không đọc được ở lần kiểm Leader; không kết luận mọi đường truy cập đều lỗi. Thay bằng trang chính thức đã mở thành công từ README TRAM:
  - https://github.com/center-for-threat-informed-defense/tram/wiki/Data-Annotation
  - https://github.com/center-for-threat-informed-defense/tram/wiki/Data-Annotation-Best-Practices-Guide
- Guide phân biệt pilot luyện tập có thể thảo luận, double annotation để đo agreement phải độc lập, sau đó adjudication. Đưa đúng phân biệt vào nghiên cứu; không gán cho nguồn khẳng định về schema riêng hay quyền từng báo cáo. Terms of Use không có nội dung đọc được trong lần kiểm Leader, không coi link là bằng chứng quyền raw CTI.

## R2 — Schema và trạng thái chưa nhất quán

Research:76 dùng `UNKNOWN` + local-only trái enum/policy :88. `translation_of` không có bảng optional keys; no_findings mô tả khác nhau. Brief đòi hai annotation cố định và raw, nhưng đồng thời có NEEDS_LOCAL_RAW/NOT_READY; test missing raw nói không report. Đường thiếu dữ liệu vì vậy không có một hành vi xác định. Kiểm ngày tương lai theo ngày chạy làm kết quả thay đổi dù input giữ nguyên.

Chốt phạm vi nhỏ:

- Đúng 5 metadata record. Mỗi record cho 0–2 annotation; >2, duplicate annotator, file orphan hoặc sai filename/id là INVALID. Thiếu annotation hợp lệ là NOT_READY, không lỗi parser. Hai ID khác nhau chỉ là khai báo, không chứng minh hai người độc lập.
- `raw.present=false` dùng `raw.sha256=null`, không có raw file và không có annotation cho record đó. Với present=true, file bắt buộc và hash phải đúng; missing/hash mismatch là INVALID. Local-only/repo-allowed có thể chưa có raw để tạo hồ sơ NOT_READY. Link-only buộc absent; unknown licence buộc link-only; prohibited/TLP ngoài CLEAR/GREEN là INVALID.
- Record reasons là danh sách enum đóng sắp thứ tự cố định, phân biệt NEEDS_RIGHTS, NEEDS_LOCAL_RAW, NEEDS_SECOND_ANNOTATION. Chốt rõ mỗi điều kiện. Không có ngưỡng 80%; dataset chỉ READY nếu cả 5 record đủ và có ít nhất một IOC hoặc TTP union; toàn bộ no-findings trả NOT_READY với lý do riêng.
- Agreement chỉ tính record đủ hai annotation hợp lệ với raw, rights declaration và catalog tương ứng; record thiếu điều kiện có trạng thái unavailable, không gán 0 hay both_empty. Cohort phải có evaluated_record_count và đối chiếu tổng từ các record đủ điều kiện.
- Bảng schema exact keys/types/bounds bắt buộc cho mọi object, gồm `language=vi|en`, provenance, translation_of optional, hash nullable, bool/int exact, value/source URL bounds. Ví dụ metadata hợp lệ dùng licence enum hợp lệ, không diễn giải là đã có quyền thật.
- Ngày là calendar-valid YYYY-MM-DD; published <= retrieved và annotated >= retrieved. Bỏ phụ thuộc đồng hồ hệ thống; không thêm as-of CLI trong lát này.
- `split=pilot` duy nhất cho lát này; dev/holdout là thiết kế sau, không tuyên bố đã kiểm leakage của chúng. translation_of chỉ tới record gốc hiện có, khác ID, cùng duplicate_group, không chuỗi/vòng translation. Duplicate detection vẫn declared-only.
- `no_findings=true` iff cả hai list rỗng; false/absent yêu cầu ít nhất một list có phần tử. Cho phép overlap evidence của các item khác nhau; duplicate evidence trong cùng item bị từ chối.

## R3 — Evidence chưa buộc IOC vào đoạn trích và hash báo cáo chưa buộc vào nhãn

Một annotation có thể trỏ tới câu bất kỳ có hash đúng, khai IOC không nằm trong câu, rồi đạt READY theo brief hiện tại. Hash manifest/pin trong report cũng không thay đổi khi raw/annotation thay đổi nhưng counts giống nhau.

Chốt sửa:

- IOC evidence trong schema v1 là span của chính token IOC (có thể defanged), không phải toàn câu. Mỗi substring phải qua `phonghoa_core.ioc.normalize(raw: str) -> Ioc` và bằng type/value của item đã chuẩn hóa. Không viết normalizer mới, không dùng policy operational allowlist để bỏ nhãn victim/benign. Role vẫn là người khai, không chứng minh semantic.
- TTP evidence là đoạn văn: chỉ kiểm UTF-8/LF/code-point bounds và quote hash; không suy đúng ngữ cảnh từ catalog hoặc quote. Giữ semantic unverified.
- Chốt hash raw là UTF-8 của text sau CRLF/CR -> LF, không NFC/NFKC/strip; giới hạn bytes raw phải kiểm trước decode/normalization. Reject NUL/lone surrogate trong chuỗi sử dụng; JSON reject BOM, duplicate keys, non-finite, wrong exact types, recursion/oversize bằng lỗi an toàn.
- Thêm `dataset_input_sha256`: SHA-256 của JSON UTF-8 compact của danh sách `[relative_posix_path, sha256(original_file_bytes)]` sắp lexical path, không LF. Inventory gồm mọi file được chấp nhận trong dataset (kể cả .gitignore nếu có); không render danh sách/path. Hash thay đổi khi raw/metadata/annotation bytes đổi, kể cả giữ nguyên counts. Pin-byte hash và snapshot hash riêng; chốt exact serialization và một test fingerprint mutation.

## R4 — Inventory/writer/error contract cần hữu hạn, không thêm tính năng suggestions

Brief vừa muốn reject vừa đếm suggestions, sample output không có count; không giới hạn tổng file/độ sâu. `resolve` rồi kiểm có thể mất dấu symlink/reparse ancestor. Output cần bảo vệ pin/snapshot ngoài dataset, và phân biệt lỗi trước với sau publish.

Chốt sửa:

- Trong lát này chỉ manifest, records, annotations, raw, optional .gitignore; adjudications/suggestions nếu có chỉ được directory rỗng. Không đọc/đếm model suggestions. Không nested directories dưới records/annotations/raw; filename đúng grammar; không orphan. Max 22 regular files, tổng dataset bytes <=8 MiB; .gitignore <=4 KiB; JSON 256 KiB/file, raw 512 KiB/file. Đặt cap trước đọc, bounded read max+1. External pin/snapshot tính riêng theo cap ở R1.
- Kiểm lexical path/ancestor bằng lstat/reparse trước resolve rồi containment. Reject symlink/junction/reparse và hardlink file theo phạm vi đã tuyên bố, trên input và output parent. Không tuyên bố chống hostile concurrent directory mutation; không thay permissions/trust.
- Output nằm ngoài dataset, parent đã tồn tại, không được alias input dataset/pin/snapshot (lexical/resolved/samefile khi tồn tại). Không overwrite. Same-dir temp + flush/fsync + os.link no-clobber; thành công os.link là commit point. Cleanup temp lỗi sau publish không được báo rằng output chưa ghi; report hoàn chỉnh giữ nguyên và diagnostic enum hữu hạn nếu cần. Trước commit lỗi thì không tạo report/không đổi file cũ. Không swallow lỗi publish.
- CLI: 0 ready; 2 invalid hoặc not-ready; 1 I/O. INVALID không report; NOT_READY có report hợp lệ. Chốt closed error codes, thứ tự preflight, stdout/stderr không raw/path/exception. Library API và writer phải dùng cùng contract; report JSON exact keys cho READY/NOT_READY, số liệu thống nhất, sorted keys/separators/LF cố định.
- Kiểm failure/no-clobber/aliases với hash inputs + output cũ; deterministic rerun ở output mới; không thêm network/dependency/API/UI.

## R5 — Giao việc chưa tự đủ và test đặt ngoài testpaths

`pytest.ini` hiện chỉ thu core/tests, extractor/tests, connectors, mcp-server; đường `extractor/dataset/tests` trong brief không được `make test` tự chạy. Brief chưa có target tuyệt đối, API signatures, command Python đúng môi trường, nơi result/evidence, và quên PROGRESS theo AGENTS.md.

Chốt cho brief cập nhật:

- Root Leader: `$WORKSPACE`.
- Source read-only `<root>\cti-x01-c4-eval` tại base trên; target mới `<root>\cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111` (chưa tạo).
- Allowlist: `extractor/phonghoa_extractor/gold_pilot.py`, `extractor/dataset/check_gold_pilot.py`, `extractor/tests/test_gold_pilot.py`, `extractor/tests/fixtures/gold_pilot/**`, `docs/specs/X01-gold-pilot-v1.md`, `docs/adr/0010-x01-gold-pilot-readiness.md`, `docs/PROGRESS.md`. Chỉ synthetic fixtures nhỏ. Không sửa file cũ khác/dependency/config/tests/PROGRESS ngoài target.
- Chốt public library signature/return/error/writer rõ ràng; API và CLI có test parity. Đọc spec, AGENTS và PROGRESS trước code. Một worker Sol medium, không giao thêm bot, không sửa probe/review/sổ Leader.
- Interpreter tuyệt đối `<root>\cti-platform-start\.venv\Scripts\python.exe`, PYTHONPATH tới core/extractor của target. Commands RED/GREEN, targeted new tests; regression liên quan `test_attack_catalog.py`, `test_attack_catalog_official.py`, `test_evaluate.py`, `test_eval_cli.py`, `test_eval_report.py`, `test_c4_eval_contract.py`; Ruff check/format trên file đổi; diff-check base..HEAD. Không mặc định lặp full repo vì production cũ không đổi; mở rộng khi failure/rủi ro mới cần.
- Pin fixture official đã có trong `extractor/tests/fixtures/attack_official/official-pin.json`; chỉ đọc asset official đã tồn tại nếu cần compatibility demo, không tải/copy 55 MB. Dùng synthetic loader/fixture cho unit matrix, ghi rõ kiểm nào official nào synthetic.
- Result `<root>\PHONG-HOA-X01-GOLD-PILOT-RESULT.md`; evidence `<root>\x01-gold-pilot-evidence\` gồm command/exit/JUnit, demo ready/not-ready/invalid, input non-mutation, hash manifest, base/HEAD/diff/status. Source và target sạch sau commit; không push/PR/merge/deploy.

## Điều kiện đóng review

Research chỉ sửa đúng hai tài liệu đã được giao, đồng bộ R1–R5 và examples/matrix/UNVERIFIED; không tạo target, code, test, commit, tải corpus hay sửa sổ. Trả bảng R1–R5 -> file:line, SHA-256 hai file, source HEAD/status cuối. Leader sẽ kiểm contract rồi mới giao implementation.

Tài liệu, nguồn và Git đã được kiểm; **chưa có implementation hay test gold-pilot**. Quyền corpus thật, độc lập người gán, đúng ngữ cảnh TTP, gold/model quality, lab/production vẫn chưa được xác minh.
