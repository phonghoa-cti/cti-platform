# X01-LOCAL-INGEST-IMPLEMENT — gói triển khai của Leader

## Mục tiêu và nguồn

Một CTI AI Agent dùng Sol medium làm trực tiếp, không giao tiếp. Người dùng nhận CLI cục bộ nạp UTF-8 TXT/PDF có lớp text thành envelope chứa draft C1 pending, provenance và evidence đúng canonical text. Hoàn tất liên tục đến test, self-review, commit local, demo tại HEAD và báo cáo; không dừng ở mỗi mốc.

Root tuyệt đối: `$WORKSPACE`.

- Source readonly `<root>\cti-x01-gold-pilot`, base `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`.
- Tạo riêng `<root>\cti-x01-ingest-local`, branch `feat/x01-ingest-local-20261111`, đúng base. Leader đã kiểm target chưa tồn tại; kiểm lại trước tạo, không reset/xóa tree có sẵn.
- Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md và skill TDD phù hợp. Dùng nghiên cứu đã nghiệm thu, không nghiên cứu lại toàn dự án.
- `<root>\PHONG-HOA-X01-LOCAL-INGEST-RESEARCH.md` SHA-256 `09c845f62cab64bf5babdeae8dd2ce5c8144cef902744344ec09417b57d2f237`.
- `<root>\PHONG-HOA-X01-LOCAL-INGEST-IMPLEMENTATION-BRIEF.md` SHA-256 `38a4dab5b53122ea94166afc6c86faebc2abe48227a2722b878b7105962e5462`.
- `<root>\PHONG-HOA-X01-LOCAL-INGEST-ACCEPTANCE-20261111.md` ghi giới hạn nghiệm thu tài liệu.

Giữ phương án B cùng toàn bộ contract/allowlist/tests trong brief. Những chốt dưới đây giải quyết điểm còn mơ hồ và có ưu tiên hơn brief; không phải yêu cầu mở rộng tính năng.

## Chốt triển khai

1. **Một bản bytes cho hash và parser.** Parent mở input regular local, đọc tối đa max_raw_bytes+1; hash chính bytes đó. PDF child chỉ đọc private snapshot được ghi từ bytes đã băm, không mở lại file gốc. Display name lấy basename gốc, không tên temp. Test hook thay file gốc sau snapshot phải chứng minh kết quả/hash vẫn từ snapshot; không sửa file thật. Không đọc URL/UNC/network share, không theo symlink/reparse input; lỗi `input_not_regular`. Private snapshot/result chỉ trong temp do lượt tạo, xóa sau khi child đã dừng/reap. Không ghi raw vào evidence ngoài fixture tổng hợp được phép.
2. **Validation và lỗi nền.** Thêm mã đóng `invalid_input`, `invalid_limits`, `invalid_input_name`, `input_read_failed`, `text_total_limit`, `output_cleanup_failed`; không echo dữ liệu. Path API phải là Path; limits đúng IngestLimits, exact-int fields trong bounds đã chốt (bool/list/dict/null/float bị từ chối). Validate limits/path/name trước I/O, rồi thứ tự lỗi brief. TXT phải tuân max_total_codepoints; không cắt ngầm. Basename từ chối NUL, C0/DEL, slash/backslash và Unicode không encode UTF-8 strict. I/O lỗi đọc/snapshot trả input_read_failed. Khởi động/exit bất thường hoặc cleanup child thất bại trả pdf_child_failed, ghi giới hạn cleanup trong evidence nếu còn tài nguyên. Không blanket catch BaseException hay lộ traceback/parser warning.
3. **Child hữu hạn và dữ liệu rõ ràng.** Parent có thể dùng find_spec để nhận biết dependency, không import/parser PDF ở parent. Child chạy sys.executable của target với script tuyệt đối; không shell, không converter khác. Timeout lấy limits.pdf_timeout_seconds (15 chỉ là default/max), deadline monotonic. stdin/stdout/stderr dùng DEVNULL, không để child thừa kế console. Toàn PdfReader/page enumeration/extraction ở child. Parent đọc result tối đa limit+1 bytes, strict JSON (duplicate key/nonfinite bị từ chối), exact schema/types trước dùng; không `read_bytes()` vô hạn rồi mới so size. Successful result `{ok:true,pages:[str,...]}`; failed result `{ok:false,code:<allowed PDF code>}`. Parent kiểm lại page/count/UTF-8/text bounds và dựng canonical/ranges/hash từ pages, không tin hash/path/cap do result tự khai. Worker được chọn helper nội bộ nhỏ để test deterministic timeout/result/lifecycle.
4. **Publish và cleanup đúng trạng thái.** os.link là điểm output được tạo thành công; mọi lỗi trước đó giữ output/input cũ. Không fallback replace hoặc tự retry output. Temp unlink sau link thất bại: giữ output hợp lệ, trả `output_cleanup_failed` exit 1, không nói output chưa được tạo, không xóa target đã publish. Test cả lỗi trước và sau điểm publish; tài liệu CLI ghi rõ trường hợp này. Chỉ dọn tài nguyên có ownership, không recursive-delete đường dẫn tự dựng chưa kiểm.
5. **CLI tối thiểu.** Giữ flags trong brief; `--language` chỉ vi/en, `--tlp` nhận đúng năm canonical token của drafts.py, default TLP:AMBER. Lỗi cú pháp/enum trả exit 2 và mã đóng `invalid_arguments`, không in input/path/unknown argument thô. `--help` được phép in hướng dẫn. Thành công stdout exact summary với output_created=true; exit 1 cho lỗi ingest/publish. JSON output ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2, final LF. Không metadata runtime/timestamp làm mất deterministic bytes.
6. **Scope tài liệu và quyền.** Bổ sung đúng `docs/adr/0011-x01-local-ingest.md` (theo TEMPLATE) vào allowlist để ghi quyết định kiến trúc theo AGENTS; không phải thay đổi spec/model/UI. Cho phép commit local Conventional Commit sau checks xanh. Các câu cấm ADR/commit trong research brief được thay bằng mục này. Cho phép tải dependency chính thức và cài trong target .venv theo mục sau, không cài toàn máy/source. Không push/PR/merge/deploy, lab/listener/browser/real corpus/model/cloud/secret. Không sửa RUNS, acceptance, review, Leader plan hoặc source tree.

## Bootstrap và dependency

Python 3.12.13 đã quan sát: `$USER_HOME\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe`. Dùng đường dẫn này với `-m venv <target>\.venv`, rồi mọi lệnh bằng `<target>\.venv\Scripts\python.exe`. Không dùng PATH mơ hồ hoặc sửa venv ở source. pytest.ini đã có pythonpath core/extractor.

Runtime PDF chỉ pypdf==7.0.1, không extras, không sdist build. Wheel chính thức đã đối chiếu metadata: tên pypdf-7.0.1-py3-none-any.whl, size 416136, SHA-256 `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`. Dùng pip download `--only-binary=:all: --no-deps --require-hashes` theo lock, vào `<root>\x01-local-ingest-evidence\wheelhouse`; kiểm bytes/hash, sau đó install `--no-index --find-links <wheelhouse> --only-binary=:all: --no-deps --require-hashes`. Không fallback package/version khác khi sai hash. Giữ lock hai hash metadata nếu brief yêu cầu, nhưng đường cài chỉ chọn wheel.

Test tools riêng target: pytest==9.2.0, ruff==0.17.4 (đúng phiên bản Leader quan sát trong môi trường kiểm hiện hữu); cho phép pip cài từ PyPI cùng dependencies của test tools, lưu versions vào evidence. Kiểm advisory metadata chính thức tại lúc cài; báo đúng nguồn/phạm vi, không hứa CVE-free. Ghi dependency-provenance bằng kết quả thực: metadata, byte hash, install/version; thay câu “chưa tải/cài” trong tài liệu repo khi đã thực sự chạy, giữ rõ nghiên cứu trước đó chỉ metadata. Bootstrap được dùng mạng tới PyPI/pythonhosted; runtime/test/demo phải offline.

## Kiểm chứng và bàn giao

TDD RED trước implementation, GREEN sau; chỉ fixture tổng hợp trong allowlist. Có thể tạo dữ liệu edge case tại tmp_path của test, không cần thêm fixture cố định ngoài danh sách. Không tạo PDF bomb. Encrypted fixture chỉ để xác nhận reject; tạo fixture bằng test utility không phải decrypt capability của runtime. Mọi thay đổi phải tự review theo các bất biến trong brief và plan này.

Chạy hai test mới + `test_drafts.py`, `test_draft_cli.py`, `test_grounding.py`; Ruff check/format-check năm Python file mới; diff-check và allowlist. Bổ sung kiểm no-regression cho code cũ bằng git diff base..HEAD -- các file cấm, không chạy lại toàn C2–C4/gold suite khi không đổi. Targeted tests phải có source snapshot binding, limits sai kiểu, reduced timeout, strict/capped result, publication race/alias và cleanup trước/sau publish; không chỉ mock happy path. Test actual PDF child với fixture tổng hợp tối thiểu; ghi kiểm nào thực chạy và kiểm nào fault injection.

Sau checks xanh, commit local; chạy demo TXT và PDF ở HEAD vào hai output mới/lần, so byte-identical, input hashes trước/sau, span/range invariants, child/temp cleanup. Không cần lặp cả suite sau commit nếu code không đổi; ghi SHA của code đã test và HEAD để kiểm equivalence. Không nhận số test từ tài liệu cũ.

Report `<root>\PHONG-HOA-X01-LOCAL-INGEST-RESULT.md`; evidence `<root>\x01-local-ingest-evidence\` theo brief, thêm manifest SHA-256 hai chiều (trừ chính manifest) và version/install logs. Artifact chứa dữ liệu chỉ synthetic, không secrets. Bàn giao base/branch/HEAD, diff files/count, TDD/test counts/exit, demo/cleanup, source+target status. Chốt rõ hard RAM/network isolation, hostile mutation, PDF đối kháng/thật, model/corpus/lab vẫn UNVERIFIED; timeout thành công không chứng minh sandbox.

Nếu lỗi công cụ/môi trường cùng nguyên nhân: tối đa hai lần rồi đổi cách trong scope hoặc trả blocker cụ thể. Không tự dùng agent khác, tăng quyền, đổi model hoặc mở rộng file scope. Leader sẽ kiểm độc lập kết quả rồi chọn bước phụ thuộc tiếp.
