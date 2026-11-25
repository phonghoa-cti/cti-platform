# X01-EVAL-REPORT — nghiệm thu nghiên cứu và kế hoạch triển khai

Ngày 11/11/2026. **PASS nghiên cứu R1–R4**, triển khai chưa được kiểm chứng.

## Cơ sở chấp nhận

- Đã đọc lại toàn bộ hai tài liệu sau rework, đối chiếu với source/artifact đã kiểm ở review trước. Source vẫn sạch tại `984bd2136872f4c5fba4118e33cf02b5ca615f2d`.
- Research SHA-256 `07016952DF0E0DF66A19639E7701059AFA2281A680860B26CE5659EC22108BDB`.
- Implementation brief SHA-256 `7D0632AD78802C5A2B094D49D2A7B4400BEED31627ED5D3F8236F7D25F900E68`.
- R1: research 15–23,39–42 / brief 21–23 tách C1 không có document config, exact envelope và payload bounded.
- R2: research 41–48 chốt zero denominator, aggregate/mode/document TTP invariants, input-byte SHA và six decimals.
- R3: research 50–54 / brief 27–29 giới hạn vocabulary/grammar, không render CTI/path/URL hoặc cú pháp tự do.
- R4: research 58–60 / brief 31,35–49 chốt output mới/sibling, no-clobber, commit point, lỗi CLI/I/O và demo/checks.
- Không chạy test reporter ở bước nghiên cứu; reporter chưa tồn tại. Không lặp test evaluator đã nghiệm thu.

## Quyết định và phạm vi

Chọn reporter CLI stdlib tách khỏi evaluator: ít thay đổi, tái dùng JSON/metrics hiện có. Không thêm thư viện bảng hoặc đưa renderer vào evaluator. Một worker **CTI AI Agent / Sol medium**, không giao bot/helper khác. Bắt đầu từ base đã chấp nhận, TDD → implementation → kiểm liên quan → demo → self-review → commit cục bộ → báo cáo/evidence. Không dừng xin duyệt lại các bước này; không push/PR/merge/deploy.

Root: `$WORKSPACE`.

- Source chỉ đọc: `$WORKSPACE\cti-x01-ttp-eval`.
- Base: `984bd2136872f4c5fba4118e33cf02b5ca615f2d`.
- Target mới: `$WORKSPACE\cti-x01-eval-report`.
- Branch mới: `feat/x01-eval-report-20261111`. Leader kiểm target/branch chưa tồn tại lúc giao; nếu hiện trạng đổi, kiểm trước khi tạo, không ghi đè tree của người khác.
- Python: `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`.
- Report: `$WORKSPACE\PHONG-HOA-X01-EVAL-REPORT-RESULT.md`.
- Evidence: `$WORKSPACE\x01-eval-report-evidence`.

Đọc AGENTS/spec/PROGRESS, research và implementation brief đã pin ở trên. Quyền làm nhiều file/commit cục bộ trong phạm vi này đã có; không cần hỏi lại theo quy tắc chờ chung trong AGENTS. Mọi cấm secret/cloud/model thật/DB/W05/OpenCTI/lab vẫn giữ.

Cho sửa đúng `extractor/eval/report.py`, `extractor/tests/test_eval_report.py`, `extractor/eval/README.md`, `docs/PROGRESS.md`; fixture mới nhỏ trong `extractor/tests/fixtures/eval_report/` nếu cần. Cho một ADR mới dùng số kế tiếp còn trống nếu quy tắc repo yêu cầu ghi quyết định reporter; không sửa ADR cũ. Không sửa evaluator/adapter/catalog/core/dependencies/locks/dataset/artifact cũ/RUNS/Leader review.

## Làm rõ để worker không phải đoán

1. C2/C3 root 1.0 exact: `schema_version,config,purpose,dataset_sha256,fixture_manifest_sha256,provider_policy,mock_only,evaluator,document_count,documents,micro_all,micro_by_result_mode,by_type,limitations`. 1.1 thêm `ttp_audit`. C1 và document envelopes dùng bảng research. Score exact: `tp,fp,fn,precision,recall,f1`; provider policy exact `destination,egress`; evaluator exact `git_ref,python`; C1 ttp exact `status=not_evaluated`.
2. Phân biệt bool/int bằng type check; numeric bounds áp dụng trước arithmetic; depth/mỗi collection/string có bound như research, parser lỗi không traceback. Nested prediction phải object; raw/grounding audit phải list các object bounded; không tái chấm payload. Source/fixture có path/hash theo producer, chỉ kiểm shape/type/hash/bounds và không render path. C2/C3 metadata không dùng để render vẫn đúng primitive/container theo source; string rỗng chỉ bị cấm ở định danh bắt buộc, không cấm mọi payload string.
3. `by_type` chỉ nhận các key thuộc tám loại thực trong core: `ipv4,ipv6,domain,url,email,md5,sha1,sha256`; cho subset/empty đúng artifact. Không thêm unknown type label. Python version dùng ASCII `[0-9]+\.[0-9]+\.[0-9]+`; fullmatch mọi grammar. Catalog kind `synthetic` hoặc `official` đúng SnapshotPin nguồn; version `[A-Za-z0-9._-]{1,64}` áp dụng cả hai kind và render code span, không làm link. Catalog exact bảy trường `kind,version,sha256,source_url,release_tag,commit,provenance`; nullable fields/type theo pin producer, toàn bộ catalog dùng so cohort, chỉ kind/version/hash cần trình bày. Không tải snapshot hoặc gọi loader/catalog trong reporter.
4. TTP top exact `enabled,catalog,metric_note,counts`; counts exact `technique_items,quote_status,catalog_status`; quote enum `matched,missing,not_found,ambiguous`, catalog enum `active,inactive,unknown,not_checked`. Document audit item phải object có fields của serializer hiện tại; kiểm projection enums/flags để thống kê, không xác minh nội dung quote/source/technique. Counts phản ánh artifact, không chứng minh semantic truth hay tính xác thực producer.
5. Mọi input hash trong report tính từ chính bytes đã parse, không reread để tính hash. Sort configs để đảo thứ tự --input vẫn ra cùng bytes. Giữ metrics artifact sau validation; tính expected chỉ nhằm phát hiện mâu thuẫn. Zero denominator = 0.0, output fixed six decimals như brief. Known limitations được đối chiếu với literal producer rồi render thông báo cố định.
6. Success stdout JSON exact `{"configs":[...],"output":"operand đã nhận"}`. Stderr lỗi là một dòng fixed như brief; không echo operand lỗi. `--help` exit 0. `argparse` không cho viết tắt option. Input/output alias có thể qua hardlink/symlink/resolution; kiểm trước mọi publish. Sibling khác tên được phép. Overwrite chỉ có khi cờ rõ; no-overwrite phải dùng no-clobber, không check-then-replace.
7. Commit point là link/replace thành công. Trước đó lỗi phải giữ old output/input. Sau commit, nếu temp cleanup lỗi: trả lỗi I/O theo research, không xóa output vừa publish và không nói rollback thành công. README/report mô tả tình huống này; test bằng fault injection có cleanup owned sau test. Không hứa bảo vệ hostile directory mutation hoặc power loss.

## Kiểm tra và bàn giao

- Dùng interpreter tuyệt đối ở trên cho pytest và `-m ruff`; không dùng Python/Ruff ngẫu nhiên trên PATH. TDD reporter theo matrix brief; regression `extractor/tests/test_eval_cli.py`; Ruff check/format chỉ files đổi; git diff --check. Không lặp full suite/model/browser/lab.
- Demo C1 1.0 và C2+C3 1.1; có thể tái dùng read-only `PHONG-HOA-X01-C1-SMOKE-RESULT.json` và `x01-ttp-eval-evidence/demo-c2-audit.json`, `demo-c3-audit.json`. Có thể tạo synthetic evidence mới trong evidence/inputs bằng evaluator cục bộ đã có. Không chỉnh baseline cho thuận reporter. C1+C2+C3 1.0 phải có positive test, và cần positive test schema 1.1 official catalog metadata, không cần tải asset MITRE.
- Test negative đúng matrix, đặc biệt aggregate/mode/TTP mismatch, grammar/Markdown, safe argparse, alias, no-overwrite race, failure trước/sau commit. Rerun bytes identical, input bytes/hash bất biến. Nếu filesystem không hỗ trợ hardlink, trả I/O an toàn, không thay bằng overwrite.
- Report có base/head/branch, file diff, lệnh/exit/count, RED→GREEN, demo/input/output hashes, manifest bằng chứng, trạng thái sạch source/target; phân biệt fresh và kế thừa. Commit cục bộ Conventional Commits sau self-review, giữ tree/branch để Leader kiểm độc lập.
- PASS chỉ cho tính năng offline đã thực chạy. Chất lượng model/corpus thật, semantic TTP, C4/RAG, OpenCTI/lab/production chưa được xác minh.

Đã kiểm một lần các cuộc mở lúc 10:32 ICT: không có Leader khác đang làm, AI Agent rảnh. Automation tiếp tục việc còn mở vẫn enabled; lần 10:26 trả NOTHING NEW; không xem trạng thái lịch là proof chạy sản phẩm.
