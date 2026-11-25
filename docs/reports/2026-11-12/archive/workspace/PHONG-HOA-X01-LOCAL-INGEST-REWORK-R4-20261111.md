# X01 local ingest — nghiệm thu R1–R3, còn R4

Root: `$WORKSPACE`.

Target `cti-x01-ingest-local`, branch `feat/x01-ingest-local-20261111`, HEAD `732685f7f774fee925840cb7d97b894547bfd119`. Source `cti-x01-gold-pilot` vẫn sạch tại `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`; target sạch, rework diff-check exit 0.

## Kết quả độc lập

R1–R3 đã được xác nhận sửa theo diff và probe gốc: code list/dict trả lỗi đóng; wait/terminate lỗi vẫn thử thu hồi; không xác nhận child dừng thì giữ temp; ancestor reparse tĩnh bị chặn. Bộ test gồm 107 ca repo và 6 probe Leader đạt **113 passed**, exit 0, log `leader-local-ingest-review/rework-green.log`.

Probe gốc SHA-256 giữ nguyên `a1896975905607b0cb607b7e5a76a2d22256f8828bd9ee003b37b7f7ed0e11e9`. Manifest root 25/25 và rework 11/11, không thiếu/thừa/sai hash. Chỉ kiểm lại phần mới, không nghiệm thu lại toàn dự án. Evidence `leader-local-ingest-review/rework-verification.json`.

## R4 — đường dẫn tương đối dưới cwd UNC vượt ranh giới local

`extractor/phonghoa_extractor/local_ingest.py:110` chỉ từ chối UNC dựa trên chuỗi `path` do caller truyền. `_validate_ancestor_chain()` nhánh relative lấy `Path.cwd()` rồi gọi lstat mà không phân loại cwd. Nếu cwd là `\\server\share\folder`, `Path('synthetic.txt')` vẫn vượt kiểm tra và được đọc. Các node UNC bình thường không phải symlink/reparse nên kiểm thuộc tính không thay thế kiểm local/UNC. Đây là đường dẫn tĩnh, không phải hostile mutation đã loại khỏi phạm vi.

Probe mới `<root>\leader-local-ingest-review\test_ingest_unc_cwd.py`, SHA-256 `3ef10d378663e3557a5f11ab52588398c96b4464e3d80b9ea833d29d799deffa`:

```powershell
& '<target>\.venv\Scripts\python.exe' -B -m pytest -o addopts= -q -p no:cacheprovider --tb=short '<root>\leader-local-ingest-review\test_ingest_unc_cwd.py'
```

**1 failed**, exit 1: public ingest không raise LocalIngestError. `Path.cwd/lstat/_read_capped` được mô phỏng, không mở kết nối mạng hoặc tạo share; log `leader-local-ingest-review/unc-cwd-red.log`. Input chỉ là chuỗi tổng hợp.

## Sửa tối thiểu và tiêu chí

- Phân loại đường dẫn hiệu lực trước mọi stat/read: relative input cần xét cwd; UNC bị từ chối ngay bằng input_not_regular. Không dùng resolve để chạm share trước kiểm tra. Giữ kiểm ancestor lexical, không cho `..` làm bỏ qua ancestor chưa kiểm.
- Regression RED→GREEN cho simple relative, relative có `..`, Windows rooted-relative khi cwd UNC; explicit UNC vẫn bị chặn. Absolute local path không phụ thuộc cwd UNC vẫn được phép. Các kiểm UNC là fault-injection không dùng network thật. Giữ positive local relative/absolute.
- Không mở rộng thành chống mọi mapped drive, hostile TOCTOU hay sandbox mạng; không nhận các thuộc tính đó là đã kiểm. Không đổi contract/CLI/shape, parser PDF hoặc cleanup đã nghiệm thu.
- Một CTI AI Agent Sol medium trực tiếp trên target/branch hiện có; allowlist đúng `extractor/phonghoa_extractor/local_ingest.py` và `extractor/tests/test_local_ingest.py`. Không sửa source, probe/log/review/ledger/plan Leader, dependency hoặc fixture; không giao tiếp.
- Giữ nguyên hai probe và kiểm SHA trước/sau. Chạy hai file test ingest repo + hai probe Leader; không cần chạy lại 39 ca C1 hoặc toàn repo vì chỉ đổi preflight path. Ruff check/format hai file, diff-check/scope; commit local Conventional Commit, target/source sạch. Demo local relative TXT một lần đủ; không lặp PDF hay model/lab.
- Cập nhật report `PHONG-HOA-X01-LOCAL-INGEST-RESULT.md`, evidence `x01-local-ingest-evidence/rework-r4/` và manifest hai chiều. Báo exact SHA/test counts/exit/scope/limitations. Không push/PR/merge/deploy, real corpus/cloud/lab/runtime network.

Chưa nghiệm thu toàn implementation cho đến khi R4 đạt. Model/PDF đối kháng, hard RAM/network isolation, Windows junction thật và lab/production vẫn chưa xác minh.
