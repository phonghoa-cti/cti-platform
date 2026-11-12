# X01-TTP-EVAL — review nghiên cứu 11/11/2026

**NEEDS_REWORK — tài liệu, chưa giao implementation.** Giữ phương án A: audit opt-in trong evaluator hiện có.

Request `528090b3-f0cf-4449-9631-3ee2854ce665`; thread `d38e5666-5818-41a7-939c-94900ff90911`.
Đọc trọn hai tài liệu; hash thực:
- Research: `B6D5D9E443DF1A9CA6C325848E982F114352C97BC45EA6BC70D2B37DA120A99F`.
- Implementation brief: `4732C53F332E775EAB4C43509EF1CEA38E4B8A3FC7F2E28E785162DCA9CC5B80`.
Source trực tiếp kiểm vẫn `b896ad343a2e9876559649b1182c0a4feeecaaa5`, branch `feat/x01-ttp-audit-20261111`; status/diff-check sạch.
Đây là static review hợp đồng và nguồn chính thức, không chạy lại 281 test hoặc tuyên bố implementation mới đạt.

## R1 — số lần thử provider đang mâu thuẫn fallback

Research:40 và Brief:35 yêu cầu đúng một provider call/document. Code `extractor/phonghoa_extractor/llm_adapter.py:116` lặp attempt 1,2 rồi fallback tại 128. Một `run_extraction` invocation có thể gọi provider hai lần; sửa adapter để đạt criterion hiện tại sẽ phá policy đã nghiệm thu.

Sửa cả hai tài liệu:
- Một adapter invocation/document; không có call nào do audit thêm vào.
- Normal completed: provider 1; retry rồi completed: 2; hai retryable failures rồi regex_fallback: 2, audit=[].
- Nonretryable/refusal vẫn theo policy cũ, abort không output.
- Test so bật/tắt audit giữ attempts/errors/result_mode/predictions/IOC score, và counter audit không tăng provider calls. Thêm fixture riêng temp cho ba nhánh, không sửa baseline.

## R2 — hash/span của text đọc và newline

Research:65, Brief:36 dùng đúng text đã đọc là hợp lý, nhưng câu “không normalize CRLF” dễ khiến implementer kỳ vọng giữ bytes gốc. `eval/run.py:207` dùng Path.read_text với newline mặc định; CRLF và CR đơn được dịch thành LF trước adapter. [Python open newline](https://docs.python.org/3.12/library/functions.html#open) xác nhận hành vi này.

Chốt tương thích: **giữ cách đọc hiện tại**, audit cùng str với adapter, không thêm normalization; không đổi sang newline='' trong lát cắt này. Nêu rõ source.sha256 là hash UTF-8 của text sau universal-newline reading; dataset_sha256 vẫn hash bytes file theo logic hiện hữu. Source hash không được gọi là raw-file hash.

Test ghi fixture bằng write_bytes chứa emoji/CRLF/CR/NFC/NFD, tự tính expected text/hash/span sau bước đọc hiện tại. Chứng minh raw bytes hash khác text hash với CRLF, adapter/audit/document source hash bằng nhau, không đọc lại source. Không tạo text chứa CRLF bằng write_text mặc định trên Windows rồi tưởng đã kiểm exact bytes.

## R3 — pin JSON cần contract strict và giới hạn rõ

Research:61 nói bảy field nhưng SnapshotPin có **tám** field: kind, version, sha256, source_url, release_tag, commit, provenance. Constructor dataclass không tự kiểm type annotations; shape/type validation phải tường minh, semantic pin validation do public loader. [Python dataclasses](https://docs.python.org/3.12/library/dataclasses.html) mô tả giới hạn type checking này.

Brief:21 chưa chốt duplicate keys, nonfinite và read bound. JSON mặc định nhận duplicate key (giữ giá trị cuối) và NaN/Infinity; [Python json](https://docs.python.org/3.12/library/json.html) cũng khuyên giới hạn input không tin cậy.

Chốt cho pin file mới:
- Đọc binary tối đa **16 KiB + 1**, vượt giới hạn từ chối trước parse. UTF-8 strict, không BOM.
- JSON root exact dict, đúng tám keys, không duplicate key ở bất kỳ object nào; reject NaN/Infinity/-Infinity; deep/numeric parsing failure về lỗi an toàn, không traceback.
- Các trường base exact str, source_url/release_tag/commit chỉ str hoặc None theo loại pin; bool/number/list/dict không được coerce. Public load_catalog tiếp tục xác minh mọi enum/shape/hash/provenance và official exact pin; không sửa loader.
- Chỉ nạp catalog một lần trước document loop. Pin invalid không được gọi provider hay writer.
- Test 16 KiB/16 KiB+1 (padding hợp lệ), UTF-8/BOM/duplicate/nonfinite/deep/extra/missing/wrong types/hash mismatch, marker không xuất hiện stderr.
- CLI runtime error vẫn `Lỗi: offline_eval_failed`, exit 1, output và inputs bất biến; giữ handling usage exit2 riêng.

## R4 — chốt đủ library và artifact để không tự đoán

Research:42/Brief:23 gọi v1.1 nhưng chưa ghi rõ root schema_version; library chỉ được nhắc ở mô tả.

Chốt:
- Public evaluator giữ signature cũ và thêm keyword-only `attack_catalog: AttackCatalog | None = None`; None disabled. Exact AttackCatalog là object từ trusted public loader; sai kiểu fail trước provider. Library không tự load file hoặc lặp loader; CLI là nơi parse pin/load một lần.
- Khi enabled, root `schema_version="1.1"`; khi disabled giữ "1.0", không thêm field mới.
- `ttp_audit.catalog` đúng tám field public pin đã validate.
- Counts exact: `technique_items` và `quote_status` với matched/missing/not_found/ambiguous; `catalog_status` với active/inactive/unknown/not_checked. Tất cả key luôn có integer >=0, kể cả zero; mỗi map tổng bằng technique_items. Duplicate tính theo item, không dedupe; không denominator/rate hoặc semantic metric.
- documents[].ttp_audit giữ đầy đủ public TechniqueAudit projection; span tuple serialize array/null, giữ item_index gốc.
- Thêm ví dụ artifact nhỏ có một item và zero/fallback, test schema/keyset/count invariant. C3 top-level eligibility hiện hữu không đổi, mọi technique false.
- C1/C2/C3 mặc định so đúng baseline cho cờ đầy đủ đã tài liệu hóa; chỉ loại evaluator.git_ref khi so hai HEAD khác. Việc allow_abbrev=False cần ghi rõ rút gọn không còn được nhận, không tuyên bố toàn CLI byte-compatible.

## R5 — phạm vi/bàn giao còn thiếu hoặc trái quy ước

Brief:14 cấm PROGRESS/ADR trong khi AGENTS yêu cầu cập nhật PROGRESS và ADR cho quyết định kiến trúc.
- Cho phép docs/PROGRESS.md; thêm ADR ngắn `docs/adr/0006-x01-evaluator-technique-audit.md` nếu chưa tồn tại, không sửa ADR0005.
- Giữ code scope run.py, test_eval_cli.py, eval/README.md; test_ttp_audit.py chỉ khi seam cần, không sửa code audit/catalog/adapter/grounding/fixture baseline.
- Viết absolute root/source/target. New target `$WORKSPACE\cti-x01-ttp-eval`, branch `feat/x01-ttp-eval-20261111`, exact base như trên; không dùng tree tồn tại chưa xác minh ownership/base/clean.
- Chốt report `$WORKSPACE\PHONG-HOA-X01-TTP-EVAL-RESULT.md`, evidence `$WORKSPACE\x01-ttp-eval-evidence\`.
- Demo dùng path có thật: `extractor/attack/fixtures/synthetic-catalog.json` và pin tạo trong temp từ đúng fixture provenance/hash; responses baseline `extractor/eval/fixtures/c2c3`. Có demo bổ sung temp với semantic items để không chỉ chứng minh [].
- Ruff check/format mọi Python thực đổi, không chỉ hai file cố định nếu đổi test_ttp_audit. Raw stdout/stderr/cwd/command/exit; hash artifacts, local Conventional Commit, giữ tree. Không full/official suite lặp theo thói quen.

## Rework

CTI Research chỉ sửa đúng **hai tài liệu nghiên cứu/implementation brief** đã giao. Không sửa source, RUNS, review này; không implementation/test/commit/worktree/asset download/model/lab/delegate. Trả bảng R1–R5 → dòng đã sửa, SHA mới, source HEAD/status trước/sau. Không đổi phương án A hoặc nghiên cứu lại phần catalog/audit đã accepted.

Đã xem một lần các thread: không Leader khác đang xử lý; Research idle. Lịch tiếp tục đọc 09:45 ICT vẫn enabled, kỳ kế 09:56; giữ vì dự án active. Rework tài liệu không làm mất nghiệm thu audit b896ad3 trước đó.
