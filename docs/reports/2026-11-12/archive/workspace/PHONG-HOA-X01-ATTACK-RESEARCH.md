# X01 ATT&CK offline — restricted catalog

Ngày đối chiếu: 11/11/2026 (Asia/Saigon). Mã chỉ đọc: `cti-platform-ai-llm-adapter` tại `8694fa7244d181f421bb2733ded7bf9ae218ea93`. Lượt này chỉ sửa tài liệu: không tải snapshot, cài package, tạo tree/commit, chạy code/test/model/lab hay sửa source.

## Kết luận

**Chọn thư viện nội bộ stdlib + fixture STIX hoàn toàn synthetic.** Nó lập *restricted catalog* (catalog giới hạn chỉ cho lookup mã ATT&CK Enterprise), không phải full STIX validator và chưa tương thích catalog MITRE thật. Không cần chờ người dùng chọn snapshot.

| Mức | Có thể kết luận | Không được suy ra |
|---|---|---|
| Syntax | mã ASCII `Tdddd`/`Tdddd.ddd` hợp lệ | mã tồn tại |
| Catalog fixture | đúng một `attack-pattern` active trong fixture+pin synthetic | đúng ngữ nghĩa hành vi/TTP |
| Semantics | luôn `unverified` | C4/RAG hoàn tất hoặc được đưa vào draft vận hành |

Lookup/quote textual match không phải RAG và không chứng minh TTP. `operational_draft_eligible` luôn `false`.

## Nguồn và so phương án

| Cách | Nguồn/giấy phép | Khả năng tái sử dụng và giới hạn | Quyết định |
|---|---|---|---|
| A. stdlib restricted catalog | [ATT&CK STIX Data](https://github.com/mitre-attack/attack-stix-data), [USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md), [STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html) | Không dependency; fixture synthetic tự tạo, không sao chép MITRE data/license; deterministic, test được fail-closed | **Chọn** |
| B. `stix2` MemoryStore | MITRE USAGE minh họa load local versioned; cần chọn/pin package, license/SBOM | Hữu ích query graph lớn nhưng thêm dependency và chưa được cài/chạy/tương thích | Không chọn slice này |
| C. ATT&CK Data Model (ADM) | [ATT&CK Specification](https://mitre-attack.github.io/attack-data-model/schemas/), [Technique Schema](https://mitre-attack.github.io/attack-data-model/schemas/sdo/technique.schema/) | ADM là schema/model, không đồng nghĩa TAXII; có thể đọc local/offline nhưng thêm toolchain/schema-policy | Không chọn slice này |

TAXII là cơ chế nhận dữ liệu qua mạng riêng, ngoài scope offline; không gộp nó với ADM. ATT&CK index ngày kiểm liệt kê Enterprise v20.1 (05/11/2026) và v20.0 (13/10/2026) [index](https://github.com/mitre-attack/attack-stix-data/blob/master/index.md). Đây chỉ là thông tin nguồn, không là fixture/pin và không chứng minh v20.1 đã được tải/chạy.

## Chuẩn nguồn và policy Phong Hỏa

ATT&CK specification mô tả technique là `attack-pattern`; sub-technique có `x_mitre_is_subtechnique=true`, một cạnh `subtechnique-of` từ child tới parent, và format `Txxxx.yyy`. Các quy tắc fail-closed dưới đây (bounds, canonical version, reject conflict/orphan) là **policy restricted catalog Phong Hỏa**, không phải yêu cầu đầy đủ của MITRE/OASIS.

`ground_techniques()` chỉ là khả năng nối tương lai bằng active-ID set. `llm_adapter.py` tiếp tục giữ semantic item riêng/không eligible; `eval/run.py` giữ C1–C3 và C4 exit 2. Slice không sửa các file đó, SQLite/W05/API/UI/STIX exporter hay `score_techniques()`.

## Fixture pin và loader contract

Fixture JSON bundle synthetic có provenance bắt buộc `{kind:"synthetic", generator:"hand-authored-test-fixture", purpose:"restricted-catalog-test", mitre_release:null, source_url:null, release_tag:null, commit:null}`. Không dùng bytes/tên/release/tag/commit MITRE thật. `SnapshotPin` phân biệt `kind:"synthetic"|"official"`: synthetic bắt buộc metadata MITRE null; official (không implement) bắt buộc metadata non-empty và NOTICE/license là task compatibility sau.

Trước file I/O, validate pin: str thật, enum known, ASCII/control-free bounds (metadata 1..256, URL 1..2048), SHA lowercase 64 hex; không `str()` object. `max_bytes` là int không bool, 1..64 MiB. Đọc binary tối đa `max_bytes+1`, rồi hash exact, UTF-8 strict, JSON strict (duplicate key/NaN/Infinity => reject). I/O chỉ code an toàn, không exception text/path/raw JSON; không ghi/mạng/partial index.

Root phải `{type:"bundle", objects:list}`; member phải object có `type` string. Object khác `attack-pattern`/`relationship` chỉ minimum shape rồi bỏ qua: không phải full STIX validator. Attack-pattern được index cần `id` `attack-pattern--UUID`, `type`, `spec_version:"2.1"`, string `name`, UTC `modified` có fractional precision, list external refs, string-list `x_mitre_domains`. Missing/sai domain là lỗi; chỉ index object có `enterprise-attack`, domain hợp lệ khác bỏ qua. Đúng một ref `source_name="mitre-attack"` có external ID fullmatch. Lifecycle fields vắng=false/có mặt bool; sub-technique flag bắt buộc bool và khớp dạng dotted ID.

Thứ tự error: `invalid_pin` → `snapshot_not_found|snapshot_io_error|snapshot_too_large` → `snapshot_hash_mismatch` → `invalid_utf8` → `invalid_json` → `invalid_bundle` → `invalid_member|invalid_attack_pattern|invalid_relationship` → `duplicate_conflict` → `parent_conflict`. `AttackCatalogError.__str__/__repr__` chỉ code.

## Canonical version và parent graph

Canonicalize attack-pattern và relationship theo STIX id trước lookup/graph. Duplicate relevant fields hoàn toàn giống nhau dedupe. Cùng id phải giữ external ID; chọn `modified` UTC mới nhất, giữ fractional precision, không theo array order; equal-time khác payload => conflict. Newest revoked không được hồi sinh. Hai STIX IDs cùng external ID => conflict.

Canonicalize relationship giống vậy; chỉ edge current, không revoked/deprecated, `subtechnique-of`, valid source/target được graph. Non-relevant relationship bỏ qua. Active child cần đúng một parent active/indexed/non-subtechnique, source=child,target=parent,prefix khớp. Dangling/self/sai hướng/multi-parent/prefix mismatch/parent inactive/active orphan => `parent_conflict`; duplicate same edge collapse; parent không có parent. Inactive child có thể thiếu edge, nhưng edge current vẫn validate.

Policy này chỉ cho fixture, không tuyên bố bao phủ catalog MITRE. Test version đảo thứ tự/equal-time khác payload/newest revoked/hồi sinh/inactive edge/orphan/inactive parent/duplicate edge/prefix mismatch.

## Kết quả và giới hạn

`AttackCatalog`/record immutable. Lookup nhận object, không echo/coerce raw. Chỉ ASCII fullmatch, không trim/newline/Unicode. Invalid -> `normalized_id=None`, `not_checked`; conflict khiến loader thất bại, không status ambiguous. Result chỉ có normalized ID, syntax/status/reason, synthetic pin provenance, external/name/subtechnique/parents; không supplied input, `keep`, evidence hay raw source. Mọi result `semantic_status="unverified"`, `operational_draft_eligible=false`.

Chưa kiểm: implementation/test, real MITRE snapshot/compatibility, RAG/C4/model, semantic benchmark, W05/OpenCTI/lab.
