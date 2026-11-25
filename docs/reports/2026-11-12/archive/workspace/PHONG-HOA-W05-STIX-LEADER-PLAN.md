# W05-STIX — quyết định Leader và giao Backend, 11/11/2026

## Kết luận review
**ACCEPTED nghiên cứu với phần chốt Leader dưới đây; chưa PASS implementation.**
Request rework `b5f931a6-ff70-4e3c-a713-3db2a6ad98b8`.
Đã đọc cả hai tài liệu và kiểm hash:
- Research `9E24A3335B2CE27EBB6FF079D77538326A049B2C5D81D45656B132D865B40A8D`.
- Brief `89B7CF6E85693CB4009A8F02344120865C99F4FDBC79FF8268756AF4641B1DF7`.

R1 mã RED/timestamp chuẩn, R3 tám IOC và R4 không Indicator đã sửa đúng hướng kiểm trước. R2 giữ UUIDv5 có ngoại lệ khuyến nghị, không gọi strict nguyên vẹn. R5 thống nhất không ghi đè; R6 bổ sung config, BEGIN và docs. Phần còn mơ hồ về hai output, namespace, reviewer field và publish primitive được chốt trực tiếp dưới đây, không giao thêm vòng nghiên cứu.

Source mới kiểm sạch tại `cti-w05-selection-integration`, HEAD `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`. Không có Leader khác đang làm ở cuộc khác khi kiểm một lần đầu lượt. Tự động tiếp tục vẫn enabled, lượt gần nhất 05:56 ICT trả NOTHING NEW; không xem đó là chứng minh phục hồi việc bỏ dở.

## Mục tiêu và người thực hiện
Task `W05-STIX-IMPLEMENT`, CTI Backend / Sol medium, không giao tiếp hoặc giao việc bot khác.
Tạo worktree mới `$WORKSPACE\cti-w05-stix-offline`, branch `feat/w05-stix-offline-20261111`, từ exact base trên. Chỉ một worker sửa tree mới. Nếu tree/branch đã tồn tại hoặc source khác/bẩn, kiểm chủ sở hữu và báo cụ thể, không reset/clean/ghi đè.
Đầu ra là converter CLI offline đọc final approved snapshot, xuất một bundle STIX 2.1. Tái dùng nghiên cứu và helper hiện hữu, không nghiên cứu lại UI/auth. Phần chốt này có ưu tiên hơn các câu mâu thuẫn trong research/brief.

## 1. Một output có đầy đủ provenance
**Không tạo sidecar manifest**, không làm transaction hai file. CLI giữ `--db --id --exporter-config --output [--timeout]`.
Thông tin truy nguồn nằm trong một `Report.external_references`:
- `source_name="phong-hoa-approved-snapshot"`.
- `external_id` là SHA256 của JSON canonical provenance dưới đây.
- `description` là chuỗi JSON canonical provenance, không URL cần truy cập.
Provenance schema v1 exact: `format_version="1"`, `source_sha256` (text), `payload_sha256` (JSON canonical toàn payload), `draft_id`, `approved_audit_id`, `review_version`, `selection_version`, `selected_indices`, `selected_sha256`, `decided_at` (UTC chuẩn), `exporter_config_sha256`, `source_tlp`, `stix_tlp`.
Không xuất reviewer subject hoặc hash của subject. Tra ngược người duyệt bằng DB + final audit ID, tránh tạo thêm định danh người bên ngoài DB. Getter thêm `decided_by_subject: str` trong snapshot nội bộ (repr=False), đối chiếu audit trong transaction; serializer không đưa field đó vào artifact/stdout/log. Snapshot payload phải độc lập với connection; frozen dataclass không có nghĩa nested dict không đổi: defensive copy/validate ở biên serializer, không dùng frozen để bỏ kiểm.
Không xuất source.name tùy ý, raw text, evidence, findings, lý do hay client actor. Giá trị email trong SCO là IOC được duyệt, khác với email người duyệt.

CLI stdout thành công exact: `{"draft_id":N,"bundle_sha256":"...","object_count":N}`, exit0; lỗi nghiệp vụ exit1, mã lỗi an toàn một dòng stderr. --help/argparse usage có thể exit2, ghi rõ trong contract. Không tự retry thao tác gửi/import vì không có mạng.

## 2. Snapshot và chính sách
Dùng readonly SQLite URI, không immutable=1 để bỏ qua WAL; BEGIN trước mọi schema/data read cần nhất quán. Kiểm schema v2; payload; review approved; người tạo và người duyệt tồn tại/khác nhau; đúng một final approve audit với actor/time/status/version khớp và reason NULL. Kiểm expected/previous/new review version, selection version/event/hash/canonical indices, eligible subset không rỗng theo contract lõi. Không reread ngoài transaction.
Mọi mismatch fail closed. Không lấy selection client/current pointer mới làm authority. Tamper DB có thể phá tính nhất quán để bị phát hiện; không hứa chống quản trị viên sửa đồng bộ DB/hashes.
Tách input validation khỏi I/O; timeout finite >=0, id nguyên dương không bool, mapping/config strict. Không sửa policy/migration/schema hiện có.

## 3. STIX và ID v1
Bundle chỉ `type,id,objects`; **không timestamp/spec_version cho Bundle**. Marking là literal chuẩn, không tự tham chiếu object_marking_refs.
Objects thứ tự ổn định: marking, Identity, các SCO theo final index sau dedup, Report.
Mark Identity/SCO/Report; Report.created_by_ref trỏ exporter Identity; không tự gắn common property không áp dụng cho SCO.
Report name/description là nội dung tĩnh nói xuất dữ liệu đã duyệt ngoại tuyến, không khẳng định đã quan sát/độc hại/nhập OpenCTI. Report created=modified=published=decided_at chuẩn UTC; giữ độ chính xác ít nhất millisecond nếu có. Identity created=modified=config.created, tuyệt đối không lấy timestamp draft.
Config exact như brief; namespace UUID hợp lệ không nil và khác namespace SCO. identity_class chỉ organization, name không rỗng, created có timezone hợp lệ, TLP equality như brief; dùng fixture synthetic minh bạch, không tự tạo config cho tổ chức thật.

SCO ID: namespace chuẩn OASIS `00abedb4-aa42-466c-9c01-fed23315a9b7`; UUIDv5 trên canonical JSON của đúng ID-contributing properties. Value/string mapping reuse normalize. File chỉ một hash đúng thuật toán tương ứng. Kiểm test against known standard vectors hoặc tính bằng đường tham chiếu độc lập, không chỉ gọi lại implementation.
SDO/Bundle: từ config.id_namespace_uuid sinh child namespace bằng UUIDv5 với name chính xác `phonghoa:w05:stix:1:identity`, `phonghoa:w05:stix:1:report`, `phonghoa:w05:stix:1:bundle`. Identity ID UUIDv5(child, configSHA). Report ID UUIDv5(child, provenanceSHA). Bundle ID UUIDv5(child, canonical JSON ordered object IDs). Type prefix STIX chuẩn, ba child namespace khác nhau và không bằng SCO. Khác payload/nguồn/TLP/config/decision metadata phải đổi Report/Bundle; SCO giữ dedup chuẩn. Khi nội dung provenance giống nhau hoàn toàn, re-export là cùng identity nội dung, không bịa DB identity mới.
Canonical bytes UTF8, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False; final bundle thêm newline. Với SCO ID chỉ thuộc tính chuỗi/dict cố định trong scope, đối chiếu RFC8785/OASIS, từ chối surrogate không mã hóa UTF8. Không dùng serializer JSON chứa float để tự nhận JCS tổng quát.
Tám IOC: ipv4,ipv6,domain,url,email,md5,sha1,sha256; loại khác/kind không hỗ trợ không được len lỏi qua getter giả. Không Indicator/pattern/ObservedData/relationship/TTP.

## 4. Xuất nguyên tử, không clobber
Mục tiêu local NTFS trong thư mục tin cậy, do caller kiểm soát. Bảo vệ cả DB, -wal/-shm/-journal, exporter config và alias của chúng; target directory/symlink/reparse alias không hỗ trợ phải fail closed. Kiểm samefile và normalized path kể cả target chưa tồn tại, không tạo parent ngoài ý muốn.
Ghi đầy đủ bytes đã validate vào temp exclusive cùng parent, flush/fsync, đóng handle. Publish bằng `os.link(temp, output)` tạo hardlink đích mới, rồi bỏ tên temp mình tạo. Đích tồn tại: đọc regular file an toàn, so byte-identical thì thành công không sửa; khác nội dung lỗi. Nếu race làm đích xuất hiện giữa check/publish, xử lý FileExistsError bằng cùng quy tắc compare. Không fallback sang os.replace, truncate, unlink đích, hay exclusive-create trực tiếp đích rồi ghi dần. Nếu filesystem không hỗ trợ link, fail closed.
Test Windows thực tế bằng hai worker thread/process đồng bộ Barrier/Event: cùng nội dung hai lần thành công/đích hoàn chỉnh; khác nội dung đúng một winner, loser không sửa winner. Inject write/link/cleanup errors; không xóa temp người khác. Nếu publish đã thành công nhưng unlink temp thất bại, không giả vờ output không tồn tại: lỗi riêng nêu publication đã có và cleanup chưa xong, không xóa output. Không hứa atomic chống người có quyền đổi directory đồng thời/crash/powerloss/network share; ghi rõ giới hạn.

Nguồn đã mở: https://docs.python.org/3.12/library/os.html#os.link (hỗ trợ Windows); publish/race semantics cần test thật trên filesystem đang dùng, chưa được research chứng minh.

## 5. Dependency/validator và phạm vi file
Được phép tạo venv riêng trong tree mới, cài dependency từ nguồn chính thức, không cài global/đổi env tree cũ. Tests sản phẩm/validator không gọi mạng.
Pin `stix2-validator==3.3.2` đã thấy trên PyPI ngày 11/11/2026: https://pypi.org/project/stix2-validator/3.3.2/ . Chưa xác minh package bytes/CLI cục bộ. Worker lấy metadata/hash từ nguồn official, tạo lock có hash mọi transitive dep theo uv đang dùng; kiểm version bằng importlib.metadata và executable --help (đừng nhầm --version 2.1 là version package).
- Tạo root `requirements-stix-test.in` và `requirements-stix-test.lock` (thay đường extractor/ trong brief) để nhất quán repo; validator chỉ test dependency, không runtime CLI.
- Giữ byte-identical requirements-api.in/lock và portal/web/package-lock.json. Không SDK STIX runtime.
- Phải chạy validator toàn bộ MUST/schema/ref và profile strict-except-103 đã xác minh flag/version; negative tests invalid marking/ref/schema phải fail. Không skip validator để báo PASS; nếu blocker package cụ thể, trả bằng chứng và phần đã làm, không bịa PASS.
- Offline runtime serializer có validation nội bộ/ref/type bắt buộc trước publish; validator độc lập kiểm artifact tests/demo.

File code được sửa: store.py; mới stix_export.py thư viện/CLI và test_stix_export.py/test_stix_export_cli.py; tests fixture synthetic riêng khi cần. Không sửa test cũ trừ cần thêm regression đọc snapshot ở test_selection.py, không xóa/làm yếu assertion cũ.
Docs cho phép: docs/PROGRESS.md, docs/specs/W05-draft-offline-contract.md (chỉ bổ sung phần export), mới docs/adr/0016-w05-stix-offline-export.md, extractor/draft/STIX-EXPORT.md, exporter-config.example.json synthetic trong extractor/draft/examples/stix/.
Không thay core normalization, API/UI/gateway, schema/migrations/compose, root RUNS, research/review/plan, evidence cũ. Không push/PR/merge/deploy/lab/secret/LLM hoặc đọc DB thật.

## 6. Kiểm tra và bàn giao
TDD theo nhóm rủi ro: authority/tamper/schema/state; tám mapping/TLP; deterministic/provenance/ID; CLI/config/output; read-interleaving WAL; publication race và failure. Đỏ trước xanh có log; test không chỉ mirror implementation.
Chạy targeted mới + selection/review/store/queue/CLI regression; do sửa helper store và thêm deps test, chạy full Python một lần sau hoàn tất (không lặp nếu chưa thay mới). Ruff check/format đúng file; git diff --check. Không chạy UI/build/browser vì UI không đổi.
Demo tổng hợp: tạo hai IOC → bỏ một → người khác approve → export bundle; chỉ SCO đã chọn; JSON/validator/provenance khớp; re-export byte-identical; lỗi giữ output/DB không đổi. Không cần listener.
Bằng chứng tại `$WORKSPACE\w05-stix-evidence`; báo cáo `$WORKSPACE\PHONG-HOA-W05-STIX-RESULT.md`. Chỉ ghi hai vị trí ngoài tree này; không secret/raw thật. Lưu exact commands, exit codes, counts, hashes, RED/GREEN, schema/ID/race checks, manifest bằng chứng. Commit cục bộ Conventional Commits sau kiểm; báo HEAD/base/diffstat/clean status và source còn sạch.
Phân biệt PASS cục bộ với chưa kiểm OpenCTI/import/reviewer-author mapping thật/Cloudflare/lab/production. Hoàn thành lát cắt này không đóng toàn dự án.
