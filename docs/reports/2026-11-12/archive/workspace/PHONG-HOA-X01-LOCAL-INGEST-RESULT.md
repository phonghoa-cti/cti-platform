# Kết quả — X01 local ingest

Trạng thái: **PASS R1–R3 trong phạm vi offline/synthetic đã giao**.

## Rework R1–R3

- R1: child result `code` list/dict và enum sai đều thành mã đóng
  `pdf_child_invalid_result`; CLI exit 1, không traceback/raw marker/output.
- R2: wait/terminate OSError không còn bỏ qua kill/reap. Temp chỉ bị xóa sau
  khi xác nhận process đã dừng; nếu kill/final wait vẫn không xác nhận được,
  `pdf_child_failed` được trả và thư mục owned được giữ. Fault-injection đã quan
  sát trạng thái giữ này rồi test tự dọn fixture tổng hợp; temp còn lại cuối lượt 0.
- R3: mọi ancestor lexical của đường dẫn absolute/relative được lstat trước leaf;
  symlink/reparse/non-directory bị từ chối trước read bằng `input_not_regular`.
- Probe Leader nguyên trạng: RED 5 failed/1 passed → GREEN 6 passed; hash trước/
  sau cùng `a1896975905607b0cb607b7e5a76a2d22256f8828bd9ee003b37b7f7ed0e11e9`.

## Mục tiêu và phương án

CLI mới nhận file regular local `.txt` UTF-8 strict hoặc PDF có lớp text, tạo
envelope provenance bao quanh draft C1 `pending`. Phương án tái sử dụng
`build_regex_draft()` không đổi shape C1, `os.link` no-clobber đã có mẫu trong
repo và `pypdf 7.0.1` pin/hash; không thêm model, mạng, OCR, decrypt, converter,
SQLite/W05/UI/OpenCTI.

Parent đọc/hash đúng một bản bytes, rồi PDF child chỉ đọc snapshot private của
bytes đó. Parent áp timeout/reap, result byte cap, strict JSON/schema và tự kiểm
lại page/text bounds trước khi dựng canonical text/ranges. Output được ghi temp,
flush+fsync và publish một lần bằng hard-link; không overwrite/fallback.

## Git và phạm vi

- Source readonly: `cti-x01-gold-pilot`, HEAD/base
  `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`, status sạch trước/sau.
- Target: `cti-x01-ingest-local`.
- Branch: `feat/x01-ingest-local-20261111`.
- HEAD local: `8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- Commits: `910ced5 feat: add offline local ingest`; `732685f fix: harden
  local ingest lifecycle boundaries`; `8a16758 fix: reject UNC-dependent local
  ingest paths`.
- Rework R4 diff: 2 file, `+66/-1`; allowlist đủ 2, ngoài allowlist 0.
- Tổng base..HEAD: 19 file, `+1565/-0`.
- HEAD tree R4: `5a316c0060bc697f6ec1e6001e932a8f6db27c38`.
- Target status sạch sau commit/demo. Không push/PR/merge/deploy.

Không đổi `extractor/draft/run.py`, `drafts.py`, `evidence.py`, `grounding.py`,
C1–C4/gold fixtures, RUNS/Leader docs/source tree.

## TDD và kiểm chứng

TDD (test trước code):

1. RED collection: hai module mới chưa tồn tại, exit 2.
2. RED publication: lỗi fsync trước hard-link bị phân loại sai, exit 1.
3. RED lifecycle/result: ba ca temp-init, terminate lỗi và result vượt cap, exit 1.
4. GREEN test mới: 60 passed, exit 0.

Kiểm cuối trên tree đã commit:

- `pytest` hai module mới + `test_drafts.py` + `test_draft_cli.py` +
  `test_grounding.py`: **107 passed**, exit 0.
- Probe Leader nguyên trạng: **6 passed**, exit 0.
- Ruff check: exit 0; Ruff format-check: exit 0, 5 file formatted.
- `git diff --cached --check`: exit 0.
- C1 regression nằm trong 39 test cũ của bộ 99; source C1 không đổi.
- Race barrier không sleep: 1 passed; đúng một winner, loser `output_exists`,
  winner bytes/mtime giữ nguyên, temp 0.
- Timeout fault injection: 2 passed; terminate→reap và
  terminate→kill→reap, temp ownership được dọn.
- PDF child thật: fixture hai trang/blank-middle/whitespace/encrypted/malformed/
  zero-page; đây là fixture tổng hợp tối thiểu.

### Rework R4 — UNC cwd

- Probe UNC RED nguyên trạng: **1 failed**, exit 1; relative input dưới UNC cwd
  không phát sinh `LocalIngestError`.
- Regression nội bộ RED: **3 failed, 2 passed**, exit 1; relative, `..` và
  rooted-relative đều tới `lstat`.
- GREEN chọn lọc: **5 passed**, exit 0.
- Kiểm cuối: hai test ingest **74 passed**, exit 0; hai probe Leader nguyên
  trạng **7 passed**, exit 0.
- Ruff check/format-check, `git diff --check` và staged diff-check: exit 0.
- Effective path phụ thuộc cwd bị từ chối theo cú pháp nếu cwd là UNC, trước mọi
  stat/read và không gọi `resolve`; absolute local không hỏi cwd.
- Không chạy lại full C1 suite hoặc PDF demo theo brief R4.

## Dependency

- Python 3.12.13; pytest 9.2.0; Ruff 0.17.4.
- `pypdf 7.0.1`, wheel 416136 byte, SHA-256
  `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`.
- Download only-binary/no-deps/require-hashes; install offline no-index từ
  wheelhouse vào đúng target `.venv`.
- PyPI JSON ngày 11/11/2026 có `vulnerabilities: []`; đây chỉ là metadata tại
  thời điểm kiểm, không phải bảo đảm CVE-free.

Sự cố bootstrap đã xử lý: lệnh đầu ghép thừa target nên tạo `.venv` trong thư
mục con mới; đã chuyển nguyên venv về đúng `<target>\.venv`, xóa thư mục con
rỗng và xác nhận source/target sạch. Không lặp lỗi cùng cách.

## Demo tại HEAD

- TXT hai lần: exit 0/0, SHA output cùng
  `9617ee8acfca39b5cff1177d7a5b9fee7d2a0c017f7899e491a8a8d54614df93`.
- PDF hai lần: exit 0/0, SHA output cùng
  `0ec6e266c5ef7a233b3bb96b8572fdbebdc9b7e4a8b390c47260506dd4492dff`.
- Input SHA trước/sau giống nhau; draft span và PDF ranges `[0,22]`, `[25,53]`
  khớp literal canonical text.
- Temp PDF mới sau demo: 0; temp output còn lại: 0.

Evidence: `x01-local-ingest-evidence/`; rework tại `rework-r1-r3/` và
`rework-r4/`. Manifest R4 liệt kê 6/6 file ngoài chính nó. Manifest root liệt kê
32/32 file ngoài chính nó; hash lỗi 0, file chưa liệt kê 0, file thiếu 0. Wheel
và cả hai manifest rework đều được root manifest bind bằng SHA-256.

## UNVERIFIED

- Hard RAM limit và OS network sandbox trên Windows.
- Hostile filesystem mutation ngoài race publish thông thường.
- Parser safety với PDF đối kháng/bomb và chất lượng PDF thật/đa ngôn ngữ.
- OCR, completeness/layout/byte-coordinate của PDF.
- Corpus thật/hai người gán nhãn, model/RAG quality, cloud/lab/production.

Fixture PDF và timeout thành công **không** được dùng làm bằng chứng cho các mục
trên.

## Học thêm

- **Snapshot binding**: hash và parser cùng dùng một bản bytes đã chốt, tránh
  file gốc đổi giữa hai bước.
- **No-clobber**: publish không ghi đè file đích đã tồn tại, kể cả hai writer đua.
- **Reap process**: chờ child kết thúc để hệ điều hành thu hồi trạng thái process.
- **Provenance**: metadata nối output với đúng input/hash/cách xử lý đã dùng.
