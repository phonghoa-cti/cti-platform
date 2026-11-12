# X01-GOLD-PILOT — Leader review R1–R5

11/11/2026, 14:39 giờ Việt Nam. **NEEDS_REWORK**, chưa nghiệm thu.

Target `cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `9d278cfc1f9cbc2b6236b06c8e1c7541d7e7aed5`. Base/source `cti-x01-c4-eval` vẫn tại `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`. Cả hai status sạch. Diff 7 file thuộc allowlist; diff-check base..HEAD exit 0. Không sửa source sản phẩm khi review.

Hợp đồng: `PHONG-HOA-X01-GOLD-PILOT-LEADER-PLAN.md`, SHA-256 `d596cd2ca65c074c94a598924d61d9b90f9d33d70e8323645ab0163acc621def`.

## Bằng chứng mới

- Python 3.12.13: `cti-platform-start/.venv/Scripts/python.exe`.
- Leader chạy lại `pytest cti-x01-gold-pilot/extractor/tests/test_gold_pilot.py -q -p no:cacheprovider`: 9/9 đạt, exit 0.
- Leader chạy `pytest x01-gold-pilot-leader-review/test_gold_pilot_leader.py -q -p no:cacheprovider --tb=short --junitxml=x01-gold-pilot-leader-review/probe-red.xml`: **26 failed / 1 passed**, exit 1.
- PYTHONPATH là core/extractor target, PYTHONDONTWRITEBYTECODE=1. Probe dùng dữ liệu tổng hợp trong pytest tmp_path, không dữ liệu thật.
- Probe SHA-256 `e472ff28687beca7341b06e63a9ba86768d3be17db70ad3404f3e8b56c4c02c6`; giữ nguyên khi rework. Log `x01-gold-pilot-leader-review/probe-red.log`.
- JUnit worker ghi 9/9 và 349/349, 0 skip. Leader xác minh file/hash nhưng không chạy lại 349 vì producer/catalog không đổi.
- Worker manifest: 104 mục đều khớp hash, nhưng thực có 108 file bằng chứng ngoài chính manifest. Thiếu bốn dataset manifest nêu ở R5.
- CLI unknown argument thực chạy trả JSON an toàn đúng yêu cầu: probe duy nhất PASS. Không đưa argparse vào finding dựa trên suy đoán.

## Findings và sửa tối thiểu

### R1 — kiểm kiểu trước phép tra set/hash (P1)

`extractor/phonghoa_extractor/gold_pilot.py:256,297,303,331,332,385–389,444`.

16 ca list/dict ở manifest.provenance, source_license, storage_right, language, tlp, IOC type/role và quote_sha256 gây TypeError thay vì GoldPilotError. Ví dụ quote_sha256 được nhét vào tuple rồi tra set trước khi kiểm hash. Đây là lỗi đầu vào JSON dự kiến, không được thoát bằng traceback.

Kiểm exact type/bounds trước membership/hash, rồi dùng mã invalid_manifest/invalid_record/invalid_annotation tương ứng. Rà toàn bộ trường enum/hash mới cùng lỗi này, không bắt rộng mọi Exception để che lỗi lập trình. Thêm regression repo cho list/dict và các primitive sai kiểu. CLI phải trả mã đóng/exit 2, không echo nội dung, không tạo output.

### R2 — URL lỗi và userinfo/control (P1)

`gold_pilot.py:283–294`.

- URL `https://[SYNTHETIC_PRIVATE_MARKER/` làm urlsplit ném ValueError; CLI exit 1 và traceback thay vì JSON invalid_record/exit 2.
- `https://@example.invalid/` được nhận vì username rỗng bị coi là false, dù userinfo bị cấm.
- URL chứa DEL U+007F cũng được nhận, trái yêu cầu không control.

Kiểm URL đóng và chuyển lỗi parse dự kiến thành invalid_record, phân biệt userinfo hiện diện với chuỗi truthy. Từ chối control trong URL/publisher theo contract; giữ URL HTTPS hợp lệ. Không gọi mạng.

### R3 — chặn reparse trên tổ tiên trước resolve/open (P1)

`gold_pilot.py:108–128,205–244,540–548,653–656`.

Chỉ lstat chính dataset/file/output.parent; không duyệt ancestor. Bốn probe inject bit Windows REPARSE lên thư mục cha của dataset, pin, snapshot và output vẫn được nhận/publish. Đây là fault injection có kiểm soát, không phải bằng chứng đã thử junction thật.

Kiểm lexical ancestors trước resolve/open/enumerate; sau đó containment đúng hợp đồng. Áp dụng đồng nhất dataset, file con, pin, snapshot và output parent. Output unsafe/missing parent trả unsafe_output; I/O permission lỗi trả io_failure, không đổi mã sang invalid_inventory chỉ vì dùng chung helper. Duy trì từ chối symlink/junction/hardlink và regular-file policy. Bổ sung test ancestor cùng một test junction Windows thật nếu môi trường cho phép, cleanup chỉ liên kết/temp đã tạo; không xóa target qua junction. Nếu không tạo được, ghi giới hạn thay vì giả PASS.

### R4 — giới hạn duyệt và I/O fingerprint (P2)

`gold_pilot.py:214,223–235,606–609`.

`sorted(iterdir())` lấy hết mục trước kiểm cap; vòng children cũng chỉ kiểm cap sau khi đã duyệt tất cả. Probe 105 file raw cho thấy đọc cả 105 mục trước từ chối, dù cap toàn dataset là 22. Dùng bounded enumeration thực (ví dụ os.scandir streaming), dừng ngay ở mục vượt cap, chỉ sort danh sách đã giới hạn; không listdir/iterdir vật hóa cả directory trước. Kiểm giới hạn bytes/file ngay trong vòng đọc, mọi nhánh root/child đều giới hạn.

Fingerprint đọc lại bằng read_bytes không giới hạn/không đổi lỗi: PermissionError được inject ở lần đọc manifest tại bước fingerprint thoát nguyên văn. Tái dùng bytes/hashes đã đọc có giới hạn hoặc đọc lại có giới hạn và map lỗi I/O an toàn. Không yêu cầu chống hostile mutation ngoài phạm vi. Giữ fingerprint tính bytes gốc bao gồm .gitignore và không phụ thuộc newline chuẩn hóa của raw.

### R5 — hoàn thiện kiểm thử và manifest bàn giao (P2)

`x01-gold-pilot-evidence/manifest.json` bỏ sót:

- `demo/invalid/dataset/manifest.json`
- `demo/not-ready/dataset/manifest.json`
- `demo/official/dataset/manifest.json`
- `demo/ready/dataset/manifest.json`

Chỉ loại chính manifest tổng hợp bằng đường dẫn đầy đủ; không loại mọi basename manifest.json. Kiểm hai chiều: file thiếu/thừa và hash/size. Bổ sung regression RED→GREEN cho R1–R4; báo số kiểm thử hiện tại chính xác. Không gọi 349 cũ là kết quả mới.

## Bàn giao rework

Một CTI AI Agent Sol medium sửa trực tiếp trên target hiện tại, không giao tiếp agent khác. Có thể sửa library, CLI nếu cần, repo test và spec/ADR/PROGRESS trong allowlist hiện hữu; không sửa probe/log/review/plan/RUNS của Leader hoặc source C4.

Chạy nguyên 27 probe Leader và toàn test_gold_pilot.py; Ruff check/format ba file Python, diff-check rework và base..HEAD. C1–C4/catalog không đổi nên không lặp 349/full suite, trừ khi phát hiện tác động thật mới. Demo CLI READY hai output mới byte-identical, NOT_READY, INVALID có JSON an toàn; hash input bất biến. Kiểm pre-link failure/no-clobber, post-link cleanup warning giữ semantics. Commit cục bộ sạch, cập nhật result và evidence/rework-r1-r5/ với RED/GREEN, command/exit/JUnit, manifest đủ. Giữ mọi giới hạn corpus/model/TTP thật/lab/production; không push/PR/merge/deploy/mạng/model.
