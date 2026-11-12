# X01-C4-EVAL — nghiệm thu ngoại tuyến

Ngày 11/11/2026. **PASS trong phạm vi evaluator/reporter C4 synthetic, fake_offline**.
Không đồng nghĩa chất lượng model/RAG/TTP hoặc hoàn thành dự án.

Root: `$WORKSPACE`.

- Task `X01-C4-EVAL-IMPLEMENT`, rework request `98cc2bd2-57e4-43f7-9c8d-ccb91dc902cf`.
- Target `root\cti-x01-c4-eval`, branch `feat/x01-c4-eval-20261111`, HEAD `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`, sạch.
- Source `root\cti-x01-c4-adapter` giữ nguyên `654443e6ede6557f0629fc0886ca56fff782b193`, sạch.
- Rework so `7ece3c3a47541c40e7baa430792d631bc22c623d`: đúng 4 file, +113/-7; diff-check exit 0. Leader đọc toàn bộ diff code/test và đối chiếu review R1–R4.

## Kiểm chứng mới do Leader chạy

Interpreter `root\cti-platform-start\.venv\Scripts\python.exe`; PYTHONPATH target root/core/extractor; PYTHONDONTWRITEBYTECODE=1.

1. `python -m pytest -q -p no:cacheprovider root\x01-c4-eval-leader-evidence\test_c4_review_probe.py --tb=short --junitxml=...\probe-green-5e0cbf4.xml`: **18 passed in 11.83s**, exit 0. Probe nguyên trạng SHA-256 `0041669CDF155CAB72DBC6F2C082F534A9B7ACB20F2ECD86FD303565F5DB5147`.
2. `python root\x01-c4-eval-leader-evidence\verify_c4_rework_writer.py`: **7/7 PASS**, exit 0. Bốn audit lệch và ba fallback sai bị chặn trước publish, không tạo output/temp. Thư mục tạm do phép kiểm tạo được dọn.
3. Đối chiếu manifest rework: **22/22 hash khớp**. Đọc JUnit worker `final-tests.xml`: **181 test, 0 failure/error/skip**; không chạy lại suite này.
4. Đối chiếu bytes/hash: C1 và Markdown C1–C3 cũ giữ nguyên; C2/C3 bằng nhau sau khi bỏ duy nhất evaluator.git_ref; hai output C4 cùng SHA-256 `23972a91ab9d8a82093a8726acd58a038c985d1f71d80d6e18f53dfe6cef2f3f`.
5. Ruff check/format và hai demo reporter ở HEAD mới có evidence worker, exit 0; đây là bằng chứng đã đọc, không gọi là Leader chạy lại.

| Finding | Kết luận |
|---|---|
| R1 | Audit C4 bind đúng source SHA, catalog SHA/version/kind; từ chối mismatch trước render/publish. |
| R2 | Fallback chỉ nhận hai mã retryable của adapter: provider_error/invalid_response. |
| R3 | JSON integer quá dài ở metadata/labels trả lỗi CLI một dòng; không traceback; input/output được giữ. |
| R4 | Report cuối rỗng bị chặn trước bất kỳ provider generate nào. |

Bằng chứng Leader tại `root\x01-c4-eval-leader-evidence\`; worker tại `root\x01-c4-eval-evidence\rework-r1-r4\`.
Không còn finding trong phạm vi review này. Không sửa mã sản phẩm, không push/PR/merge/deploy.

## Giới hạn và bước nối

Model/provider thật, semantic TTP/RAG, corpus được con người gán nhãn, OpenCTI/lab/production vẫn chưa xác minh.
GUIDELINE hiện mô tả khoảng 40 báo cáo và thử gán nhãn độc lập, nhưng dataset đang có chỉ sáu mẫu tổng hợp; evaluator hiện chỉ nhận synthetic-smoke.
Chọn bước nghiên cứu `X01-GOLD-DATASET-NEXT`: xác định hợp đồng dữ liệu, nguồn gốc và quy trình gán nhãn/kiểm dữ liệu đủ dùng cho đo chất lượng sau này. Không tự coi nhãn AI sinh là gold, không bật model thật.
Lịch tiếp tục `79621896-f322-47a8-80d7-072739a2314b` đã đọc lại: enabled=true, mỗi 30 phút/startup; giữ vì project còn active. Việc lịch chạy NOTHING NEW không chứng minh phục hồi bỏ dở trọn chu kỳ.
