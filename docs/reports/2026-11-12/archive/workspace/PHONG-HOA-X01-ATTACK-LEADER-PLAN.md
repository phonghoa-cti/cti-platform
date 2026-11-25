# X01-ATTACK — nghiệm thu tài liệu và giao triển khai

Ngày 11/11/2026. Leader chấp nhận nghiên cứu/brief sau R1–R5, với phần chốt thực thi dưới đây có ưu tiên khi bản brief còn mơ hồ. **Đây là nghiệm thu tài liệu, chưa có code/test catalog hoặc tương thích MITRE thật.**

## Căn cứ nghiệm thu

- Request Research: 9332bb17-2329-486c-838d-0555bb9eadbc; thread 25f27e04-2e54-4103-83b4-e05205a69690.
- PHONG-HOA-X01-ATTACK-RESEARCH.md SHA256 06ED25C4BEC9885D08A74A96A0C309BE57C2CB93F6F9C6A9DBD68DFA20938342.
- PHONG-HOA-X01-ATTACK-IMPLEMENTATION-BRIEF.md SHA256 D60701A0B4254367639130C1D5B92A79D9150C1096DAC3C717DE61F0127435D8.
- Hai hash đã kiểm lại đúng. Đã đọc đủ hai tài liệu, đối chiếu review R1–R5 và mã/spec liên quan. Nguồn MITRE đã được Leader đọc ở lượt review trước; không coi đọc tài liệu là chạy thư viện/snapshot.
- R1: Research:19–29 đã tách ADM khỏi TAXII và phân biệt thông tin release với pin.
- R2: Research:35–41, Brief:67–73 đã chốt synthetic-only, đọc có giới hạn, strict JSON, taxonomy.
- R3: Research:43–49, Brief:73 đã chốt canonical versions và graph; phần thời gian/duplicate bên dưới loại bỏ mâu thuẫn còn lại.
- R4: Brief:27–67 đã bỏ raw input/ambiguous, giữ catalog/result bất biến và semantic unverified.
- R5: Brief:7–23,77–94 đã có tree/scope/ADR/PROGRESS/interpreter/evidence; phần import bên dưới sửa lệnh python -c chưa đưa source vào sys.path.
- Source vẫn sạch tại 8694fa7244d181f421bb2733ded7bf9ae218ea93; tree/branch mới chưa tồn tại. Python dùng chung đã kiểm 3.12.13/pytest 9.2.0. Không có Leader khác đang xử lý; AI Agent rảnh khi xem danh sách cuộc làm việc. Lịch phục hồi vẫn bật.

## Giao việc

Owner CTI AI Agent, Sol medium theo cấu hình hiện có; một worker, không giao tiếp bot/subagent khác. Mục tiêu: library restricted catalog ngoại tuyến và fixture tổng hợp, chuẩn bị bước kiểm mã ATT&CK của X01; chưa bật C4 hoặc đưa semantic item vào draft.

Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md và ADR template trên đúng base. Dùng research và implementation brief nói trên; không nghiên cứu lại toàn bộ X01. Tạo git worktree riêng từ source:
- Source chỉ đọc: `$WORKSPACE/cti-platform-ai-llm-adapter`.
- Base: 8694fa7244d181f421bb2733ded7bf9ae218ea93.
- Tree được sửa: `$WORKSPACE/cti-x01-attack-offline`.
- Branch: feat/x01-attack-offline-20261111.

Phạm vi file theo brief: attack_catalog.py, test_attack_catalog.py, extractor/attack/fixtures/*.json và README, extractor/attack/README.md, một ADR số chưa dùng, docs/PROGRESS.md. Không sửa các module adapter/eval/grounding/store hiện có, lock/dependency, RUNS, tài liệu/review Leader. Không thêm CLI/UI, không push/PR/merge/deploy/cài package, không mạng/model/lab/secret/dữ liệu thật.

## Ba điểm chốt trước khi code

### 1. Thời gian, duplicate, lifecycle

Đổi TechniqueRecord.modified từ datetime ở Brief:40 sang **str UTC đã validate, giữ phần lẻ gốc**. Policy restricted: YYYY-MM-DDTHH:MM:SS[.1..18 chữ số]Z, ngày/giờ thực hợp lệ, không offset/naive/leap second. So theo thời gian thực với toàn bộ precision, không dùng datetime làm mất phần nhỏ hơn microsecond. Test hai versions khác sau chữ số lẻ thứ 6 và .1/.10 biểu diễn cùng thời điểm.

“Exact duplicate” nghĩa toàn bộ object JSON bằng nhau về cấu trúc, không phụ thuộc thứ tự key; không bỏ field tùy ý rồi coi hai payload khác nhau là trùng. Cùng id/cùng thời điểm khác payload => duplicate_conflict; ordering input không đổi kết quả. Nếu history có revoked=true rồi version mới revoked=false/vắng mặt, reject duplicate_conflict; newest revoked phải inactive. Deprecated không suy ra permanent nếu chuẩn không yêu cầu.

Parent policy trong review/research giữ nguyên. Active child có đúng một active parent không phải child. Inactive child có thể không có edge; nếu có edge current vẫn kiểm refs, source-child/target-nonchild, prefix và uniqueness, nhưng target có thể inactive. Đừng hồi sinh record/cạnh lịch sử.

### 2. Pin, lỗi và phạm vi parser

Chỉ nhận kind=synthetic và provenance=hand-authored-test-fixture; kind=official là **invalid_pin trước file I/O** ở lát cắt này. Không triển khai/tải official metadata hay bịa hash/tag/commit. Pin.version là nhãn fixture ASCII control-free dài 1..64 (ví dụ synthetic-1); sha256 lowercase đúng 64 hex; source_url/release_tag/commit đều None. Validate kiểu trước membership/regex; không str/coerce object. max_bytes sai kiểu hoặc ngoài 1..64 MiB cũng invalid_pin.

Provenance của fixture bắt buộc được mô tả trong fixtures/README.md + manifest hash; có thể lưu trong custom root x_phonghoa_provenance nhưng không mở rộng SnapshotPin API chỉ để nhét nhiều metadata chưa dùng. Một mẫu hợp lệ chứng minh kind/generator/purpose và MITRE metadata null; các fixture lỗi có chủ đích ghi rõ trường bị phá. Không dùng tên/nội dung mô tả technique thật; mã Txxxx chỉ minh họa.

Attack-pattern dùng STIX id canonical type--UUID (không ép UUID version ngoài nhu cầu syntax), name non-empty <=256 Unicode chars; domain list non-empty, mỗi phần tử là một trong enterprise-attack/mobile-attack/ics-attack. Validate domain trước lọc non-Enterprise. Ref mitre-attack đúng một, fullmatch ASCII ID; flags strict bool. Với relevant relationship, bắt buộc id canonical relationship--UUID, spec_version=2.1, modified cùng quy tắc, relationship_type, source_ref/target_ref đúng kiểu; lifecycle missing=false. Quan hệ loại khác chỉ kiểm minimum shape rồi bỏ qua. Đây là restricted loader, không full STIX validation.

Bảo đảm mọi lỗi input đã nêu trả AttackCatalogError code an toàn, không traceback nội bộ trong str/repr, không raw path/payload/marker. Không catch lỗi lập trình một cách mù quáng. JSON vượt khả năng parser (ví dụ nesting quá sâu/number quá lớn) cũng chuyển lỗi parse an toàn; test có giới hạn, không gây cạn RAM.

Lookup invalid input => invalid_technique_id; active/inactive/unknown dùng reason_code catalog_active/catalog_inactive/unknown_technique_id. Normalized/external/name/parents chỉ lấy từ record đã validate; unknown external_id/name/is_subtechnique=None, parents=(); invalid normalized_id=None. Tất cả kết quả semantic unverified, eligible false. Mapping trong frozen catalog phải copy rồi khóa, không chỉ annotation Mapping trên dict mutable.

### 3. Kiểm đúng source và bằng chứng

Dùng `$WORKSPACE/cti-platform-start/.venv/Scripts/python.exe` và ruff.exe tương ứng, không sửa/cài vào môi trường chung. Tất cả lệnh chạy cwd tree mới. pytest.ini sẽ đưa core/extractor của cwd vào path khi pytest; **python -c không đọc pytest.ini**. Sau GREEN, kiểm import theo mẫu:

~~~python
from pathlib import Path
import sys
checkout = Path.cwd().resolve()
sys.path[:0] = [str(checkout / "core"), str(checkout / "extractor")]
import phonghoa_extractor.attack_catalog as module
assert Path(module.__file__).resolve() == checkout / "extractor/phonghoa_extractor/attack_catalog.py"
print(module.__file__)
~~~

RED test trước implementation, lưu log thật/exit; sau đó GREEN catalog, regression đúng 5 file Brief:88, demo active/inactive/unknown/invalid và C4 vẫn từ chối. Ruff check/format trên file mới, diff-check base..HEAD và working tree. Giữ các module bị cấm giống base. Không chạy full suite/UI/browser/lab vì không đổi phần đó. Không lặp check khi source không đổi trừ lỗi cụ thể.

Bàn giao commit cục bộ sạch, base/HEAD/branch/diffstat; raw command/exit/count; fixture/provenance hash + manifest; kết quả test lỗi đọc input, no-egress, immutable, version precision và graph. Chạy self-review tập trung rồi trả Leader nghiệm thu, không tự mượn kết quả cũ làm test mới.

Đầu ra:
- `$WORKSPACE/PHONG-HOA-X01-ATTACK-RESULT.md`.
- `$WORKSPACE/x01-attack-evidence`.

Giữ nguyên tree/branch để Leader kiểm. Nêu UNVERIFIED rõ: MITRE snapshot/compatibility thật, tích hợp adapter/C4/RAG, semantic TTP/model/corpus thật, W05/OpenCTI/lab/production. Bước sau nghiệm thu sẽ chọn kiểm catalog thật hoặc tích hợp audit từ nghiên cứu còn phù hợp; chưa tự mở rộng trong task này.
