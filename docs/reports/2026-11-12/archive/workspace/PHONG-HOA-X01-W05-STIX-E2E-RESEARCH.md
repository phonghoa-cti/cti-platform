# X01 → W05 → STIX — nghiên cứu seam E2E ngoại tuyến nhỏ nhất

Ngày kiểm: 11/11/2026 (Asia/Saigon). Trạng thái: **nghiên cứu/khuyến nghị**, chưa sửa source, chưa tạo worktree, chưa mở listener/browser và chưa chạy integration.

## Câu hỏi và kết luận

Cần chứng minh một file `.txt` UTF-8 tổng hợp đi qua extractor C1 thật, được lưu vào SQLite với tác giả tổng hợp, analyst bỏ một IOC rồi lưu và duyệt qua API HTTP thật, sau đó CLI STIX đọc **cùng DB/cùng draft** và chỉ xuất snapshot đã duyệt. Không được tạo `payload_json` viết tay hoặc gọi thẳng builder rồi coi là CLI extractor.

**Chọn:** tái dùng `tools/local_integration/LocalRun`, thêm đúng một scenario và một ma trận E2E chạy tuần tự. Scenario gọi `extractor/draft/run.py`, `extractor/draft/store.py save` và `extractor/draft/stix_export.py export-approved` bằng `subprocess.run([...], shell=False, timeout=...)`; selection/approve đi qua gateway loopback và `/api/v1`. Đây là **CLI + HTTP integration**, không phải browser E2E, OpenCTI integration hay lab validation.

## Source được đối chiếu

- Source readonly: `cti-w05-stix-offline`.
- Branch: `feat/w05-stix-offline-20261111`.
- Exact HEAD: `ed829a0344b2d3d4392fae933e41a9c44fdcd853`.
- `git status --short --branch` trước nghiên cứu: chỉ dòng branch, không có file đổi.
- Brief đầu vào SHA-256: `4E797D2C1DC4D08EEB5C175CB4FACBD375E4B248B4ABCECA96FB2518A5AB39CF`.
- W05 STIX đã được Leader nghiệm thu local tại `PHONG-HOA-W05-STIX-ACCEPTANCE-20261111.md`; W05 selection integration đã được nghiệm thu local tại `PHONG-HOA-W05-SELECTION-INTEGRATION-ACCEPTANCE-20261111.md`.

## Luồng hiện có và khe hở chính xác

| Chặng | Code/lệnh hiện có | Mức kiểm hiện có | Khe hở của chuỗi này |
|---|---|---|---|
| File → draft C1 | `extractor/draft/run.py:29-48` đọc UTF-8, gọi `build_regex_draft`, ghi JSON Unicode; builder tại `extractor/phonghoa_extractor/drafts.py:19-49` tính SHA-256 từ bytes UTF-8, evidence/span, TLP và `model=regex-C1` | CLI/unit đã có | Chưa được dùng để seed draft của cùng run selection/STIX |
| Draft → SQLite | `extractor/draft/store.py:65-68` gọi `save_draft` | CLI/unit đã có | CLI `save` chưa nhận `created_by_subject`; mặc định `None` không đủ điều kiện export approved |
| Fixture tích hợp | `tools/local_integration/runner.py:187-215` | HTTP/browser selection đã nghiệm thu | Runner gọi `build_regex_draft()` và `store.save_draft()` trực tiếp; vì vậy bằng chứng hiện tại bỏ qua cả hai CLI đầu vào |
| UI/API review | Gateway allowlist v1 tại `tools/local_integration/gateway.mjs:6-8,85-106`; ma trận selection tại `tools/local_integration/tests/run_selection_matrix.py:65-228` | HTTP thật; browser thật đã được nghiệm thu riêng | Chưa dùng draft sinh từ file/CLI và chưa nối exporter trong cùng temp DB |
| Approved → STIX | CLI tại `extractor/draft/stix_export.py:35-63`; exporter đọc final audit và publish không ghi đè | 77 test STIX và nghiệm thu local | Chưa chạy sau chuỗi extractor → API trên cùng draft/DB |

Do đó **chưa có bằng chứng toàn chuỗi**. Hai acceptance hiện hữu chứng minh các đoạn kề nhau nhưng không chứng minh nguồn draft của browser/HTTP là output CLI extractor, cũng không chứng minh bundle cuối lấy đúng draft đó.

## Hai cách đã so

| Cách | Thành phần thật / giả | Ưu điểm | Chi phí, giới hạn | Quyết định |
|---|---|---|---|---|
| A. Mở rộng `LocalRun`, seed bằng CLI subprocess, review qua HTTP gateway, export bằng CLI | Extractor CLI thật; store CLI thật; FastAPI/JWT/role/Origin/SQLite/gateway HTTP thật; STIX CLI thật. UI không khởi động, không browser. RSA/JWT/role đều synthetic nhưng được xác minh thật trong harness. | Tái dùng lifecycle/PID/temp/fixture; deterministic; tự động; một DB và một draft; không thêm framework | Cần thêm tùy chọn `--created-by-subject` cho CLI store và scenario/test nhỏ. Không tái chứng minh DOM/browser. | **Chọn** |
| B. Khởi động UI và thao tác browser rồi gọi exporter | Giống A, thêm Next UI và browser thật | Bằng chứng trực quan cùng draft | Lặp lại hành vi UI đã nghiệm thu, phụ thuộc thao tác browser/capture, khó làm ma trận âm deterministic; vẫn không chứng minh OpenCTI | Không chọn cho lát cắt nhỏ nhất; chỉ dùng nếu Leader yêu cầu một capture demo mới |

Không chọn script in-process gọi `build_regex_draft/save_draft/save_selection/decide/export_approved` vì cách đó bỏ qua CLI, gateway, HTTP serialization, Origin và exit contract — đúng các seam cần chứng minh.

## Thiết kế seam được khuyến nghị

1. Thêm `stix-e2e` vào allowlist scenario của `LocalRun`; không đổi scenario cũ.
2. Trong temp root do run sở hữu, ghi chính xác một input UTF-8 tổng hợp có Unicode và hai IOC `.example`, ví dụ `Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n`.
3. Gọi CLI C1 bằng `sys.executable` với `--language vi --tlp TLP:GREEN`; gọi CLI store với `--created-by-subject e2e-author-sub`. Parse stdout JSON để lấy draft ID; không tự đọc/ghi `payload_json`.
4. Khởi động API/gateway như harness hiện có, JWT admin tổng hợp. Dùng HTTP GET v1 để xác nhận source hash, Unicode, TLP, model, hai IOC eligible và span/evidence; POST selection `[1]`, rồi POST approve với version vừa commit.
5. Trước approve, gọi CLI export và yêu cầu fail an toàn/no output. Sau approve, gọi CLI export với `extractor/draft/examples/stix/exporter-config.example.json` (TLP:GREEN) **trước `LocalRun.close()`**.
6. Parse bundle: đúng marking + Identity + một `domain-name` cho `evil-two.example` + Report; không có `evil-one.example`, raw source, evidence hay reviewer subject. Provenance trong Report phải khớp draft ID, `source.sha256`, selection version/indices/hash và audit ID từ cùng DB.
7. Hash input/draft payload/DB và SQLite sidecar inventory ngay trước và sau export; exporter không đổi chúng. Re-export cùng target phải idempotent cùng bytes/mtime; target khác đã chứa bytes khác phải fail và giữ bytes cũ.
8. Chỉ sau khi ghi summary/hash redacted ra evidence mới thoát context để cleanup owned PID/listener/temp. Không ghi JWT, key, subject thật, raw input hay dữ liệu thật vào evidence.

## Fixture và invariant bắt buộc

- Toàn bộ dữ liệu synthetic; hai domain dùng suffix dành cho ví dụ `.example`.
- UTF-8/Unicode: hash `source.sha256` phải bằng SHA-256 **bytes của file input**, `stored.text` phải bằng nội dung giải mã UTF-8, và mỗi `span` phải cắt đúng IOC trong chuỗi Python.
- TLP: CLI nhận `TLP:GREEN`; stored payload, exporter config, marking STIX và provenance phải giữ mapping GREEN đã có. TLP không cấp quyền chia sẻ/import.
- Payload bất biến: `payload_json`, `items[*].keep`, source hash và text không đổi sau save selection, approve và export.
- Quyền export: chỉ final approve audit; selected subset `[1]`; Report provenance và bundle hash nối đúng cùng draft/audit/selection.
- Audit: đúng một selection event và một approve event; version tiến `0 → 1 → 2`; actor từ JWT synthetic của harness, không từ body.
- Publisher: pending/rejected không xuất (pending kiểm trong E2E; rejected tái dùng regression đã nghiệm thu), existing different không bị ghi đè, identical re-export không đổi bytes.

## Fail cases: mới và tái dùng

| Case | Cần chạy trong lát cắt mới? | Lý do |
|---|---:|---|
| Export pending trước review | Có | Chứng minh cùng draft chưa có quyền export |
| Bỏ một IOC → approve → bundle chỉ còn IOC kia | Có | Mục tiêu tích hợp chính |
| Existing different bytes không bị ghi đè; identical idempotent | Có | Kiểm publisher ngay trên artifact cùng run |
| Source/draft/DB/sidecar không đổi bởi export | Có | Ranh giới read-only của cùng DB |
| Rejected không xuất | Không lặp | Đã có regression STIX 77 test và acceptance local; có thể chạy test targeted nếu source liên quan đổi |
| Refresh 503 không replay POST | Không lặp | Đã được Leader nghiệm thu browser + audit tại `PHONG-HOA-W05-SELECTION-INTEGRATION-ACCEPTANCE-20261111.md` |
| Cleanup PID/listener/temp | Có một kiểm lifecycle cho scenario mới; tái dùng test runner hiện có | Scenario mới phải không phá ownership hiện có |

## Nguồn tái sử dụng, nguồn mới và khả năng dùng lại

| Trạng thái | Nguồn | Áp dụng / giới hạn |
|---|---|---|
| Reused, repo | `PHONG-HOA-W05-STIX-ACCEPTANCE-20261111.md`, `PHONG-HOA-W05-SELECTION-INTEGRATION-ACCEPTANCE-20261111.md` | Chứng minh từng đoạn local đã đạt; không suy thành toàn chuỗi |
| Reused, official | [OASIS STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html), [FIRST TLP 2.0](https://www.first.org/tlp/) | Mapping/ID/TLP đã chốt, không nghiên cứu lại |
| **New, official** | [Python 3.12 `subprocess`](https://docs.python.org/3.12/library/subprocess.html) | `run()` là API khuyến nghị cho tiến trình hữu hạn; dùng argv list, `shell=False`, timeout, capture return code/stdout/stderr. Không biến subprocess thành shell command từ dữ liệu ngoài. |
| **New, official** | [Python 3.12 `tempfile`](https://docs.python.org/3.12/library/tempfile.html) | `TemporaryDirectory` quản lý cleanup; phù hợp lifecycle sẵn có. Vẫn phải kiểm cleanup lỗi/ownership trên Windows như runner hiện tại. |
| Reused, repo | `tools/local_integration/runner.py`, selection matrix, STIX CLI/tests | Không cần evaluator, fixture framework, importer hay outbox thứ hai |

Repo không có `LICENSE` ở root tại HEAD đã đọc; đây là source nội bộ cùng repo, nhưng trạng thái giấy phép phân phối ra ngoài vẫn **UNVERIFIED** và không ảnh hưởng việc tái dùng nội bộ cho task này.

## Điều chưa kiểm

- Chưa chạy scenario đề xuất, chưa tạo worktree/code/test/evidence; nghiên cứu không phải bằng chứng integration.
- Chưa kiểm browser cùng draft trong chuỗi mới; browser selection cũ là bằng chứng riêng.
- Chưa kiểm OpenCTI ImportFileStix/workbench, mapping reviewer sang Identity thật, metrics chất lượng X01/C2–C4, dataset thật, Cloudflare/JWKS/HTTPS thật, network share, crash/power-loss, lab, deploy hay production.
- W05 spec đầy đủ vẫn còn bước “thấy Report trên OpenCTI”; output STIX local chỉ là artifact chuẩn bị cho bước đó.
