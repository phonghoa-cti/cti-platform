# X01-GOLD-PILOT — nghiệm thu cục bộ sau R1–R5

11/11/2026, Leader: **PASS trong phạm vi validator/readiness offline**. Không phải nghiệm thu corpus gold hay chất lượng AI.

- Target `cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`.
- Rework từ `9d278cfc1f9cbc2b6236b06c8e1c7541d7e7aed5`: đúng 3 file, +233/−39; toàn nhánh vẫn thuộc allowlist.
- Source `cti-x01-c4-eval` giữ `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`. Leader kiểm source/target đều sạch, diff-check base..HEAD exit 0.
- Leader đọc diff library/test: kiểm type trước set/hash; URL lỗi/userinfo/control bị từ chối; kiểm ancestor reparse; enumeration dùng scandir có giới hạn; fingerprint kiểm size và chuyển I/O lỗi thành mã đóng. Không thêm dependency, không sửa C1–C4/catalog.

## Kiểm chứng độc lập

Python 3.12.13 ở `cti-platform-start/.venv/Scripts/python.exe`; PYTHONPATH core/extractor target, PYTHONDONTWRITEBYTECODE=1.

Lệnh mới: `python -m pytest x01-gold-pilot-leader-review/test_gold_pilot_leader.py cti-x01-gold-pilot/extractor/tests/test_gold_pilot.py -q -p no:cacheprovider --tb=short --junitxml=x01-gold-pilot-leader-review/rework-acceptance.xml`.

**61 passed, 0 failed/errors/skipped, exit 0**: nguyên 27 probe Leader + 34 test repo. Probe giữ SHA-256 `e472ff28687beca7341b06e63a9ba86768d3be17db70ad3404f3e8b56c4c02c6`. So với RED Leader trước đó 26 fail/1 pass, R1–R4 đã đóng bằng chạy lại thật. Log/XML đặt trong `x01-gold-pilot-leader-review/`.

Leader kiểm manifest hai chiều, hash và size: root 194/194; rework 85/85; thiếu/thừa/sai đều 0. Bốn dataset manifest.json từng bị bỏ sót nay có mặt. File kiểm `x01-gold-pilot-leader-review/rework-manifest-check.json`. R5 đóng.

Worker evidence đã đọc và đối chiếu hash: Ruff check/format đạt; demo READY 0/0, NOT_READY 2, INVALID 2; READY deterministic; hash inventory đầu vào trước/sau cùng `afea9457368935b4cf5ad2ea05f97652be3486403dfdb3a8b59953c8f6f0bc07`. Kiểm writer no-clobber/post-link cleanup nằm trong 61 test mới. Không chạy lại 349 regression cũ vì các producer/catalog không đổi, không gán kết quả cũ cho HEAD mới.

Manifest root SHA-256 `9df4b73fe39140f00d29b134d1ddc6316ac7ffdebb4c796e2de66bc1617f600a`; rework `9acc16ee3b4f470f437d7bc02227baa24787a13381765c59adff9f688b192f11`.

## Giới hạn và quyết định tiếp

Reparse ancestor đã kiểm bằng fault injection. Junction Windows thật chưa kiểm: worker báo thao tác bị chặn trước khi chạy, Leader không đổi cách để vượt chặn. Không xác minh quyền raw corpus, hai người gán nhãn độc lập, semantic TTP, adjudication, model/RAG quality, hostile mutation, crash/power-loss, lab/OpenCTI/production. Không push/PR/merge/deploy.

Nguồn backlog đã đọc: `extractor/dataset/GUIDELINE.md` cần pilot 5 báo cáo, hai người gán độc lập trước bộ khoảng 40 báo cáo; `docs/specs/X01-ai-extractor.md` còn yêu cầu đánh giá đủ 4 cấu hình trên dataset. Validator hiện chỉ chứng minh cơ chế; không tự tạo nhãn rồi coi là người thật.

Bước đủ điều kiện tiếp theo: **X01-HUMAN-PILOT-PREP**, Research chuẩn bị danh sách 5 nguồn ứng viên và runbook cho pilot hai người. Chỉ nghiên cứu/tài liệu, tái dùng TRAM và schema đã chốt; không triển khai thêm scorer/adjudication trước khi có dữ liệu và quyết định phù hợp. Các điều kiện cần con người phải ghi rõ, không tự suy quyền hoặc danh tính.

Đã xem thread một lần: không Leader khác đang xử lý, AI worker idle. Automation tiếp tục dự án enabled=true, chu kỳ30 phút; latest14:26 completed NOTHING NEW, next14:56 giờ Việt Nam; giữ vì dự án còn active. Đây là trạng thái điều phối, không bằng chứng worker đang chạy hay dự án hoàn tất.
