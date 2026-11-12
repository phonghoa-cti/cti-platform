# X01-ATTACK — nghiệm thu nghiên cứu, yêu cầu sửa R1–R5

Ngày 11/11/2026. Kết luận: **NEEDS_REWORK cho hai tài liệu**, chưa giao implementation. Hướng stdlib + catalog ngoại tuyến được giữ; phạm vi và quyết định dưới đây do Leader chốt.

## Bằng chứng đã đọc

- Research SHA256: 5E5B42279213BD50532DF7E1BA82F7C7A9A8F87150323D3D629B83CAC09835B6.
- Brief SHA256: E48F8C664EFE61C83C6DCBC7FE186A2BBDD4840498CBD2732A1AF43C858EC991.
- Source `$WORKSPACE/cti-platform-ai-llm-adapter`: HEAD 8694fa7244d181f421bb2733ded7bf9ae218ea93, status rỗng. Đã đối chiếu grounding.py:68, llm_adapter.py:301, evaluate.py:57, eval/run.py:394 và pytest.ini.
- Python có sẵn tại `$WORKSPACE/cti-platform-start/.venv/Scripts/python.exe`: 3.12.13, pytest 9.2.0; ruff.exe tồn tại. Tree AI không có .venv. Đây là kiểm môi trường, chưa chạy test catalog.
- Đã xem các cuộc đang mở trước ghi sổ: không có Leader Phong Hỏa khác đang chạy; Research đã idle. Lịch tiếp tục vẫn bật; không coi lịch/biên nhận là bằng chứng thực thi.

## R1 — đối chiếu nguồn và so phương án đúng bản chất

Research:38,46. Index MITRE hiện liệt kê v20.1 ngày 05/11/2026 cùng v20.0 ngày 13/10/2026; nếu giữ v20.0 phải nói đây là ví dụ phiên bản, không ngụ ý mới nhất hoặc đã pin. Nguồn: https://github.com/mitre-attack/attack-stix-data/blob/master/index.md

Không gộp ATT&CK Data Model và TAXII rồi kết luận cả hai không offline/deterministic. Tách thư viện/mô hình dữ liệu khỏi cách tải qua mạng; sửa so sánh dựa nguồn chính thức, giữ tối đa ba phương án. Có thể so stdlib, stix2 MemoryStore, ATT&CK Data Model; TAXII là cơ chế nhận dữ liệu ngoài phạm vi. MITRE USAGE có hướng load local versioned: https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md

Đọc đặc tả chính thức mới được USAGE dẫn tới:
https://mitre-attack.github.io/attack-data-model/schemas/
https://mitre-attack.github.io/attack-data-model/schemas/sdo/technique.schema/
Phân biệt quy tắc chuẩn với policy fail-closed riêng của Phong Hỏa. Không ghi rằng đã chạy/cài một thư viện.

## R2 — loader và pin phải đủ cụ thể

Brief:31–38,59,71,73,87. Hiện “malformed item có thể ảnh hưởng mapping” chưa là contract kiểm được. Chốt:

- Chỉ triển khai library + fixture nhỏ hoàn toàn tổng hợp trong lát cắt đầu; không tải/đóng gói snapshot MITRE thật. Ghi rõ synthetic trong provenance; không bịa release/tag/commit MITRE cho fixture. Chọn thiết kế pin có phân biệt nguồn synthetic/official và quy tắc trường bắt buộc tương ứng. Real-catalog compatibility để UNVERIFIED và làm việc kế sau.
- Pin sai kiểu/enum/hash/metadata trả code ổn định, trước đọc file; không gọi str() lên object tùy ý. Chốt bounds đơn giản cho metadata và max_bytes (int thật, không bool, 1..64 MiB).
- Đọc binary tối đa max_bytes+1, không chỉ kiểm stat rồi đọc vô hạn. Lỗi I/O có code an toàn. Không ghi file, không mạng, không partial index.
- JSON strict: từ chối duplicate keys và NaN/Infinity; root type=bundle, objects=list; mọi phần tử phải là object có type string. Object không thuộc hai loại cần thiết chỉ kiểm cấu trúc tối thiểu rồi bỏ qua; không giả là full STIX validator.
- Với attack-pattern: chốt id/STIX type, spec_version, name, modified, external refs, x_mitre_domains và boolean fields. Chỉ index Enterprise; domain thiếu/sai kiểu bị từ chối, domain hợp lệ khác được bỏ qua. revoked/deprecated vắng mặt = false; nếu có phải bool. x_mitre_is_subtechnique bắt buộc bool; ID dạng cha/con phải nhất quán. Không dựa vị trí external ref; đúng một ref mitre-attack hợp lệ.
- Chốt chính xác error taxonomy và thứ tự kiểm; thêm ca sai kiểu list/dict/null/bool/number, duplicate JSON key, oversized input, pin mismatch trước parse. Không yêu cầu đầy đủ mọi trường STIX không phục vụ lookup.

## R3 — canonical version và parent graph

Brief:66,73,85–86. Cần quyết định rõ để tránh hai implementer cho hai kết quả khác nhau:

- Canonicalize theo STIX id trước lookup. Bản lặp hoàn toàn giống nhau được dedupe; cùng id + cùng thời điểm modified nhưng nội dung khác => duplicate_conflict. Cùng id phải giữ external ID nhất quán; chọn modified mới nhất theo thời gian UTC thực, không theo thứ tự mảng. So thời gian không được mất độ chính xác phần lẻ. Không cho revoked=true rồi hồi sinh cùng id ở version mới. Hai STIX ids cùng external ID => conflict.
- Relationship subtechnique-of cũng canonicalize theo id/modified trước áp dụng revoked/deprecated. Chỉ cạnh hiện hành, không inactive, tham gia graph. Nêu field/type bắt buộc; quan hệ không liên quan bỏ qua.
- Policy lát cắt: mỗi active sub-technique phải có đúng một parent active, đã index và không phải sub-technique. Parent được lấy từ source_ref/target_ref, sau đó kiểm ID prefix nhất quán; không tạo cạnh từ dấu chấm. Dangling/self-edge/sai hướng/nhiều parent/mismatch => parent_conflict. Cạnh trùng cùng cặp không tạo thêm parent. Technique cha không được có cạnh cha.
- Inactive child có thể thiếu cạnh hiện hành; nếu có cạnh hiện hành thì vẫn kiểm hình dạng/refs và không cho nhiều parent. Không suy ra mã thay thế hoặc làm child active nhờ parent.
- Thêm bảng ca cho version đảo thứ tự, equal-time khác payload, revoked newest, hồi sinh, inactive edge, active orphan, parent inactive, duplicate same edge, parent khác/prefix lệch. Đây là policy restricted lookup, không tuyên bố bao phủ catalog MITRE thật.

## R4 — kiểu trả về và lỗi không được mâu thuẫn

Brief:41–60,63–67. supplied_id:str không đáp ứng input object. Bỏ supplied_id khỏi kết quả; normalized_id chỉ giữ đúng mã đã qua kiểm (5 hoặc 9 ký tự ASCII), invalid => None. Không coerce/trim/echo raw object hoặc raw input dài. Dùng fullmatch để không nhận newline cuối.

Định nghĩa AttackCatalog và record tối thiểu, bất biến từ bên ngoài, provenance cần trả. Khi conflict làm loader thất bại toàn bộ thì bỏ status ambiguous khỏi lookup; chỉ active/inactive/unknown/not_checked. Lookup luôn semantic_status=unverified và operational_draft_eligible=false; không thêm keep=true hoặc evidence. Error str/repr chỉ code ổn định, không basename/path/raw JSON/exception text. Thêm ca input object gây lỗi nếu bị str() và kiểm không lộ marker.

## R5 — brief có thể giao trực tiếp

- New tree chốt: `$WORKSPACE/cti-x01-attack-offline`.
- Branch: feat/x01-attack-offline-20261111, base 8694fa7244d181f421bb2733ded7bf9ae218ea93. Tree chưa tồn tại khi Leader kiểm. Không ghi tree AI nguồn.
- Bỏ data/<version> files khỏi scope lát cắt synthetic. Cho phép docs/PROGRESS.md theo AGENTS; thêm một ADR ngắn cho lựa chọn restricted stdlib catalog theo template repo (chọn tên chưa tồn tại khi triển khai). Giữ adapter/grounding/evaluator/store/UI và dependency nguyên trạng.
- Từ cwd tree mới, dùng Python/ruff của cti-platform-start theo đường dẫn tuyệt đối nêu trên, không sửa/cài vào môi trường đó. pytest.ini đưa core/extractor của cwd vào import path; ghi lệnh kiểm import source path trước tests để chứng minh không chạy nhầm tree.
- TDD catalog RED→GREEN; regression bốn file đã nêu + grounding nếu cần do có dùng lại. Không bắt lặp full suite/UI/browser không liên quan.
- Kết quả tại `$WORKSPACE/PHONG-HOA-X01-ATTACK-RESULT.md`; raw log/manifest tại `$WORKSPACE/x01-attack-evidence`. Report command/exit/count, base/head/diff/status, nguồn fixture synthetic, demo lookup active/inactive/unknown/invalid; git commit cục bộ sạch, không push/merge.
- Ghi rõ bounds, giao diện lỗi và tests là yêu cầu triển khai tương lai; việc sửa tài liệu này không phải implementation/test.

## Giao sửa

CTI Research sửa đúng PHONG-HOA-X01-ATTACK-RESEARCH.md và PHONG-HOA-X01-ATTACK-IMPLEMENTATION-BRIEF.md trong workspace Leader, đóng R1–R5 nhất quán. Không sửa review này/RUNS/repo, không tạo tree/commit, không chạy code/test, không tải snapshot bulk hoặc cài dependency. Trả mapping R1–R5 tới dòng mới, SHA256 hai tài liệu, Git source trước/sau. Không giao bot khác. Leader sẽ kiểm lại rồi mới giao AI Agent/Sol medium.
