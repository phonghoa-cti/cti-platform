# X01-EVAL-REPORT-NEXT — Leader review R1–R4

Ngày 11/11/2026. Kết luận: **NEEDS_REWORK nghiên cứu/hợp đồng**, chưa giao implementation.
Giữ phương án A: reporter stdlib offline, một cohort tương thích, không đổi evaluator.

## Ref và bằng chứng đã kiểm

- Source `cti-x01-ttp-eval`, HEAD `984bd2136872f4c5fba4118e33cf02b5ca615f2d`; `git status --short` rỗng, exit 0.
- Research SHA-256 `88423661B8F29D58DD8E2B784E8D3F9820F89F644C18986BF7A12C270DA03D01`.
- Implementation brief SHA-256 `94871AC97280F1D8B4CE5FA54CA2FBF4D804AB751353FE54163EC9B50E9BF6FC`.
- Đọc source `extractor/eval/run.py:185–241,310–493` và `extractor/phonghoa_extractor/evaluate.py:16–32,63–65`.
- Inventory chỉ đọc bằng Python 3.12 từ `PHONG-HOA-X01-C1-SMOKE-RESULT.json` và hai `x01-ttp-eval-evidence/demo-c{2,3}-audit.json`, exit 0: mỗi artifact có 6 documents; C1 document có đúng `id,language,prediction,score,source`, không có `config`. C2/C3 document có `config` và khác nhau tại `raw_audit`/`grounding_audit`.
- Một lệnh đọc nhầm `extractor/evaluate.py` báo file không tồn tại; đã tìm đúng `extractor/phonghoa_extractor/evaluate.py` bằng rg và đọc thành công. Không phải lỗi sản phẩm.
- Chưa chạy implementation hoặc test reporter vì reporter chưa tồn tại. Các tình huống dưới đây là finding khi đối chiếu hợp đồng, không phải tuyên bố test đã thất bại.

## R1 — schema/projection phải nhận được artifact thật

Brief:42 yêu cầu mọi document có `config equals root`, nên loại C1 hợp lệ. Đồng thời “exact/unknown keys” tại Brief:44 mâu thuẫn với “validated only enough” tại :42; bound cho strings/maps/lists chưa có số cụ thể.

Sửa hai tài liệu:

- Tách rõ C1, C2, C3 và 1.0/1.1; C1 document không cần/không thêm config. Ghi đủ keysets của root/document/score/provenance được reporter sử dụng, thay vì chỉ dẫn số dòng source.
- Chọn validation của **projection cần dùng**: root và document envelope đúng contract; các nested payload không trình bày như prediction/raw_audit/grounding_audit chỉ kiểm cấu trúc/bounds đã nêu, không tái triển khai extractor hoặc grounding. Nói rõ phần không kiểm ngữ nghĩa, không tuyên bố strict toàn bộ payload nếu chỉ kiểm projection.
- Chốt số cụ thể cho kích thước/list/map/string/numeric/depth, đọc giới hạn `MAX_BYTES+1`, xử lý recursion/Unicode/huge numeric an toàn. Không cấm mọi string rỗng vì nested content có thể hợp lệ; chỉ bắt nonempty ở field thực sự yêu cầu.
- Dùng positive fixtures/artifact C1 và cả hai cấu hình C2/C3, bao gồm audit/fallback hợp lệ; malformed cases phải sửa từ fixture hợp lệ.

## R2 — metric/count phải nhất quán và đủ provenance

Research:56 chỉ kiểm công thức khi mẫu số dương; source Score quy định denominator 0 trả 0.0. Một artifact có top-level TP/FP/FN khác tổng document nhưng tự có P/R/F1 đúng công thức vẫn qua contract hiện tại. Tương tự mode có document nhưng ghi not_available, hoặc TTP counts tự cộng đúng nhưng khác danh sách audit.

Sửa hai tài liệu:

- Validate denominator-zero đúng source; không chữa hoặc thay metric artifact. Được tính giá trị kỳ vọng chỉ để kiểm invariant, không chấm lại IOC/gold.
- `document_count == len(documents)`, IDs unique; aggregate TP/FP/FN bằng tổng document scores. Mỗi mode score bằng tổng đúng partition; not_available khi và chỉ khi partition rỗng. Giữ quyết định không suy tổng per-type thành micro.
- Với 1.1, top technique_items và từng status count bằng thống kê từ document ttp_audit; enum/flags cần dùng được kiểm, semantic unverified và eligible false. Đây là consistency, không semantic truth.
- Chốt format hiển thị, ví dụ P/R/F1 sáu chữ số thập phân, counts số nguyên; tolerance kiểm 1e-12.
- Provenance report phải có SHA-256 **bytes của từng input artifact đã đọc**, bên cạnh dataset/fixture/evaluator/catalog. Không dùng filename/path làm định danh trong Markdown. Giữ giới hạn C1 không có evaluator/provider metadata và cohort 1.0/1.1 riêng biệt.
- Thêm test aggregate mismatch, mode empty/nonempty, zero denominator, top TTP vs document mismatch, input-hash repeatability.

## R3 — Markdown không được nhận cú pháp từ label không tin cậy

Research:64 / Brief:54 chỉ escape backslash, pipe, newline/control. Label chứa `[x](https://example.invalid)`, backtick, `<img ...>` hoặc URL có thể tạo markup/link ngoài ý muốn. Theo [GFM](https://github.github.com/gfm/#autolinks-extension-) và [raw HTML](https://github.github.com/gfm/#raw-html), xử lý pipe không xử lý các lớp cú pháp này.

Chọn giải pháp nhỏ nhất: đóng vocabulary IOC types/config/mode/status, grammar cho hashes/ref/Python và chỉ render provenance cần thiết. Field version tự do cần quy tắc trình bày literal rõ ràng, không link/HTML; có thể dùng code span sau validation phù hợp. Không in URL/provenance free-text/quote/IOC/path nếu không cần. Ghi thuật toán hoặc rule cụ thể; test links/images/backticks/HTML/entities/bare URL, pipe/newline/control bị từ chối hoặc hiển thị literal an toàn. Không thêm Markdown dependency/runtime/browser cho bước này.

## R4 — đường dẫn, publish và lỗi CLI phải thống nhất

Research:50 `resolve(strict=True)` cho mọi path sẽ không nhận output mới; Brief:56 lại cho tạo parent mới. “output within input directory” không rõ và có thể chặn report nằm cạnh các JSON input hợp lệ. `os.replace` luôn thay file đích tồn tại, nên kiểm `exists` rồi replace không bảo đảm `--overwrite` trước một file vừa xuất hiện. Đây là suy luận từ [Python os.replace](https://docs.python.org/3.12/library/os.html#os.replace), chưa chạy race test reporter.

Sửa hai tài liệu:

- Input là regular file tồn tại, resolve strict; output có thể chưa tồn tại và dùng resolution phù hợp. Chặn samefile/lexical/resolved alias và directory, nhưng cho phép output là sibling khác tên trong thư mục input. Không nhận directory input nên bỏ quy tắc cấm toàn bộ thư mục cha.
- Không overwrite: publication phải không thay file vừa xuất hiện, dùng primitive no-clobber phù hợp Windows và có nguồn chính thức; không fallback từ lỗi sang replace. Có --overwrite mới dùng atomic replace sau kiểm alias. Giới hạn rõ local filesystem; hostile directory mutation/crash durability không được nhận đã giải quyết.
- Quy định validation trước tạo output parent, cleanup temp thuộc lần chạy, không sửa input/old output khi thất bại trước publish; phân biệt commit point thành công với lỗi cleanup sau publish để không hứa rollback không có.
- Chốt missing/unreadable input và write failure là exit 1 I/O; invalid CLI/schema/cohort/path/existing output without overwrite là exit 2; race destination-exists xử lý như no-overwrite conflict. Generic stderr kể cả argparse invalid token; --help exit 0. Test không rò marker/path qua parse error.
- Cho phép worker tạo synthetic evidence mới **ngoài source trong evidence folder được chỉ định**, chạy CLI evaluator cục bộ để sinh bộ 1.0 tương thích nếu cần. Không cần hỏi lại. Cho phép commit cục bộ; không push/PR/merge/deploy.
- Ghi exact evidence path, lệnh pytest targeted + test_eval_cli regression, Ruff check/format và diff-check; demo C1 1.0 và C2+C3 1.1, input hashes trước/sau và report rerun byte-identical. Không chạy full suite hay lặp kiểm cũ không liên quan.

## Điều kiện trả lại

CTI Research chỉ sửa hai tài liệu đã giao. Giữ base/target/branch và phương án A; không sửa repo/RUNS/Leader review, không implementation/test/worktree/commit, không giao bot khác. Trả mapping R1–R4 tới section/line mới, SHA-256 hai file và git HEAD/status source trước/sau. Research vẫn không phải bằng chứng reporter chạy được.

Automation tiếp tục việc còn mở được kiểm lúc 10:23 ICT: vẫn enabled; project active, giữ automation. Lịch/receipt không chứng minh worker đang chạy hoặc phục hồi bỏ dở đã được kiểm.
