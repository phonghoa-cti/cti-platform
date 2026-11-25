# X01-INGEST-QUEUE-IMPLEMENT — Leader plan và nghiệm thu research

Ngày 11/11/2026. Owner triển khai: CTI Backend, GPT-5.6 Sol medium, một worker, không giao tiếp cho bot khác.

## Nghiệm thu tài liệu

Research rework R1–R4 được chấp nhận **ở mức thiết kế**, kèm các quyết định thực thi bên dưới. Không có test importer hay migration mới đã chạy.

- `PHONG-HOA-X01-INGEST-QUEUE-RESEARCH.md`: SHA-256 `c4e9f8209f16bab3384c3ad60f0ce41e062b333255572239edf05530ff8eb3ed`.
- `PHONG-HOA-X01-INGEST-QUEUE-IMPLEMENTATION-BRIEF.md`: SHA-256 `a506b0cb1c9234db520c2a3bec156b76c0c437f5d60ea38c2618c6c4f67c3b2c`.
- Leader đã đọc hợp đồng đã sửa, đối chiếu creator/policy/schema/migration trong source và kiểm hash. R1: creator bắt buộc và duplicate khác creator conflict. R2: tương thích v2/v3, migration riêng rồi atomic insert. R3: literal UTF-8, caps/page và giới hạn integrity. R4: paths, API, lỗi, tests và bàn giao đã cụ thể.
- Kiểm source mới: W05 HEAD `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; producer HEAD `8a16758601647fb3dbf935abecc2435f3b7a3fb6`; cả hai `git status --short` rỗng. Repo AGENTS và các điểm so `STORE_SCHEMA_VERSION` đã đọc. Không sửa source.

## Mục tiêu và đường dẫn

Root `$WORKSPACE`.

Đọc brief/research/plan dưới root. Tạo target `<root>\cti-x01-ingest-queue`, branch `feat/x01-ingest-queue-20261111`, từ `<root>\cti-x01-w05-stix-e2e` đúng HEAD nêu trên. Nếu target/branch đã tồn tại có owner hoặc thay đổi khác, báo thay vì reset/ghi đè. Producer `<root>\cti-x01-ingest-local` chỉ đọc theo SHA nêu trên, không sửa hoặc merge.

Đầu ra: file kết quả TXT/PDF đã có được nhập vào hàng chờ W05 cùng thông tin nguồn; nhập lại không tạo bản sao; người tạo không tự duyệt. Không mang PDF parser/model vào W05. Nghiên cứu đã so ba phương án, chọn importer độc lập để tái dùng store và giữ phạm vi nhỏ.

## Quyết định bổ sung có hiệu lực

1. **Migration race:** lấy `BEGIN IMMEDIATE` rồi đọc lại version/hình dạng schema trước DDL trong chính transaction migration, không chỉ đọc lại ở transaction insert. Hai process cùng thấy v2 trước khóa phải kết thúc bằng migration hợp lệ hoặc lock error hữu hạn, không stale-DDL. Giữ hai giai đoạn migration rồi insert như brief; lỗi insert sau migration có thể để lại v3 nhưng không để draft/provenance mồ côi.
2. **Reader và writer:** new binary đọc DB v2/v3 đúng semantics selection v2, không migrate trong reader. Review/selection là thao tác ghi khi người dùng chủ động gọi, nên không diễn giải bảng compatibility thành cấm các thao tác đó. Payload/audit/API/STIX contract cũ bất biến. Legacy get/list và yêu cầu migrate riêng của review/selection/export giữ như cũ.
3. **Lỗi CLI:** research có `invalid_arguments`, brief gộp argument lỗi. Chốt `invalid_arguments`, exit 2, stderr `Lỗi: invalid_arguments` cho parse/timeout sai; `--help` exit 0. Subject sai là `invalid_created_by_subject`, exit 1. Creator được kiểm trước đọc envelope như thứ tự trong research. Các lỗi khác dùng đúng bộ mã hữu hạn đã liệt kê; không raw path/CTI/SQL/traceback. Phân biệt DB locked với schema/database invalid mà không suy từ chuỗi lỗi người dùng.
4. **JSON/API:** reject mọi chuỗi không encode UTF-8 strict kể cả key; depth theo research, xử lý parser recursion/giới hạn integer bằng lỗi đóng. Library nhận Mapping như signature nhưng phải kiểm shape/type rõ; từ chối kiểu không JSON và input lặp tham chiếu thay vì recursion vô hạn. Không coerce bool/float thành int. Không làm biến đổi input.
5. **Provenance:** `get_ingest_provenance` trả DTO frozen, `page_text_ranges` là tuple của tuple hoặc None; draft có thật nhưng chưa có provenance trả `DraftNotFoundError`. Truy vấn draft+provenance để kiểm hash trong cùng read transaction. Dedupe dựa trên canonical envelope, cùng creator mới duplicate; khác creator conflict không tiết lộ ID.
6. **Paths:** tiếp nối guard đã kiểm: reject UNC/network syntax và ancestor reparse trước đọc file, bao gồm đường relative khi cwd là UNC; DB mở mode rw sau kiểm tra existing regular file, không tự tạo DB thiếu. Không gọi đây là bảo đảm chống hostile TOCTOU hay mapped-drive/network isolation.

## Phạm vi file

Được sửa/tạo trong target:

- `extractor/phonghoa_extractor/store.py`
- `extractor/phonghoa_extractor/ingest_queue.py`
- `extractor/ingest_queue/__init__.py`, `extractor/ingest_queue/run.py`
- `extractor/tests/test_ingest_queue.py`, `extractor/tests/test_ingest_queue_cli.py`
- Các test có tên cụ thể trong brief: store/store_cli/queue/queue_cli/draft_cli/review/selection/stix_export/stix_export_cli; chỉ sửa khi cần bổ sung v2/v3 regression, không hạ assertion cũ.
- `docs/specs/W05-draft-offline-contract.md`, `docs/adr/0017-x01-ingest-envelope-provenance.md`, `docs/PROGRESS.md`, `extractor/draft/README.md`.

Fixtures mới ưu tiên dựng trong tmp_path/test helper của hai test mới. Không đổi dependency/lock, UI, HTTP/API, PDF loader, core, producer, RUNS hoặc review Leader. Ngoài target chỉ ghi report/evidence được giao.

## Thực hiện và kiểm chứng

Đọc AGENTS/spec/PROGRESS và skill TDD của worker; làm liền mạch preflight → test RED → code GREEN → regression → self-review → commit local → demo đúng HEAD → evidence. Phạm vi này đã được Leader giao, không dừng xin người dùng duyệt lại lựa chọn kỹ thuật có thể đảo ngược.

Target interpreter là `<root>\cti-x01-ingest-queue\.venv\Scripts\python.exe`, Python 3.12.13. Bootstrap từ base interpreter của `<root>\cti-platform-start\.venv\Scripts\python.exe` (`sys._base_executable`), không dùng PATH mặc định hoặc sửa môi trường source. Tái dùng các dependency/lock API và STIX hiện có, ưu tiên cache cục bộ; không thêm/nâng thư viện. Nếu không dựng được env đủ checks, báo nguyên nhân cụ thể, không nhận PASS với skip.

- Chạy đúng các nhóm test và Ruff/diff trong brief; tất cả là bắt buộc, không chỉ gợi ý.
- Thêm regression in-process `portal_api/tests/test_w05_api.py` vì thay store schema; không listener/browser/HTTP matrix ngoài tiến trình, không lặp UI/build.
- Test hai migrator cạnh tranh, lỗi migration và insert/commit từng giai đoạn; read-only v2/v3; creator conflict; input xấu/Unicode; path alias. Không dùng sleep để giả race; mỗi phép kiểm phải có assertion kết quả dữ liệu.
- Demo tổng hợp ở HEAD: TXT và PDF envelope → import → list/get/provenance; retry cùng creator duplicate; khác creator conflict; approve bằng creator bị chặn; approve bằng analyst khác qua core hiện có thành công; export STIX chỉ chứa lựa chọn đã duyệt. Dữ liệu chỉ synthetic, không tự approve dữ liệu thật. Không mở listener/model/cloud/OpenCTI/lab.
- Bảng demo cho người không đọc code gồm thao tác, mong đợi, kết quả thực tế, trạng thái và file bằng chứng. Ghi rõ CLI/core demo không phải browser cùng luồng.

Report `<root>\PHONG-HOA-X01-INGEST-QUEUE-RESULT.md`; evidence `<root>\x01-ingest-queue-evidence\`, manifest hash hai chiều; có lệnh, exit, count, SHA/base/diff, nguồn trước/sau và cleanup owned. Cho phép envelope/DB tổng hợp khi cần, không dữ liệu thật/secret. Không để temp/process mồ côi; không xóa đầu ra người khác. Chỉ commit trong target sau checks đạt; không push/PR/merge/deploy.

## Điểm kết thúc

Trả report và exact commit để Leader nghiệm thu; không tự tuyên bố dự án hoàn thành. Bước phụ thuộc sau đó là chứng minh cùng bản nạp đi qua giao diện duyệt và đầu ra; nếu cần thêm harness phải có phạm vi riêng. Model thật, chất lượng CTI/semantic, quyền corpus, lab/OpenCTI/production vẫn chưa được chứng minh bằng lát cắt này.
