# X01 C1 ngoại tuyến — kế hoạch triển khai

> Worker: CTI Engineer, Sol medium; tự triển khai từng bước, không giao việc tiếp cho bot khác. Dùng quy trình test trước và kiểm chứng hiện có.
> Người dùng cho phép tiếp tục dự án; máy lab được để sau. Đây là phạm vi Leader chọn, không phải một yêu cầu mới do người dùng mô tả riêng.

**Goal:** Một lệnh chạy regex IOC trên bộ mẫu tổng hợp Việt/Anh và xuất JSON kết quả tái hiện được, không cần lab hoặc AI.
**Architecture:** Dùng lại phonghoa_core.extract.extract_iocs cùng phonghoa_extractor.evaluate; CLI chỉ đọc văn bản/mẫu cục bộ và ghi kết quả.
**Tech Stack:** Python 3.12, stdlib, pytest/ruff có sẵn.
**Spec:** docs/specs/X01-ai-extractor.md (C1 và Task7), extractor/dataset/GUIDELINE.md.
**Base:** 9cf935cddcb9f84bd8045cbd62f228121041d1a6 tại checkout cti-platform-start cùng thư mục kế hoạch.
**Nhánh mới:** feat/x01-c1-offline-20261110 từ base trên; giữ nguyên nhánh F01 và không thay các file deploy.

## Nghiên cứu và lựa chọn
- PHONG-HOA-INITIAL-RESEARCH.md mục3 khuyến nghị baseline IOC riêng trước LLM; không suy luận chất lượng TTP từ regex IOC.
- X01 đã định nghĩa C1, CLI extractor/eval/run.py; evaluate.py đã có Score, score_iocs, score_sets, micro_average.
- Chọn wrapper CLI dùng lại mã hiện có; chưa làm mô hình, RAG, giao diện hoặc toàn pipeline X01.
- Tập mẫu tổng hợp chỉ là kiểm tra kỹ thuật (smoke), không thay tập40báo cáo/2người gán nhãn và không làm bằng chứng luận văn.

## Phạm vi và giao diện
- Thêm extractor/eval/run.py: chạy trực tiếp từ repo bằng .venv Python, không cần PYTHONPATH thủ công.
- Lệnh mục tiêu: .venv/Scripts/python.exe extractor/eval/run.py --config C1 --dataset extractor/dataset/synthetic-smoke --output <file.json>.
- Chỉ C1; C2–C4 trả lỗi chưa hỗ trợ, không gọi mạng.
- Bộ mẫu theo GUIDELINE: raw/<id>.txt + raw/<id>.meta.json; labels/<id>.json.
- Khoảng6mẫu ngắn Việt/Anh tự tạo, dùng domain .example, không có báo cáo thật hoặc URL được tải.
- Metadata ghi synthetic=true, tác giả hệ thống, ngôn ngữ, mục đích smoke. Không giả làm dữ liệu đã được người gán nhãn độc lập.
- Kết quả: config, purpose=synthetic-smoke, số tài liệu, nguồn/SHA256 input, dự đoán từng tài liệu và TP/FP/FN/P/R/F1; tổng micro và theo loại IOC.
- Gold chuẩn hóa; prediction chỉ từ văn bản, không nhìn nhãn để lọc. Theo quy ước hiện có chỉ gold attacker được chấm chính; giải thích regex không hiểu vai nên victim/benign có thể tạo FP.
- TTP ghi not_evaluated, không đưa điểm0 vào kết quả và không suy ra TTP từ IOC.
- Thêm extractor/eval/README.md: cách chạy, ý nghĩa chỉ số, giới hạn; cập nhật docs/PROGRESS.md. Test ở extractor/tests/test_eval_cli.py.
- Không sửa thuật toán extractor/core hoặc tối ưu theo nhãn để nâng điểm trong task này; ghi các giới hạn quan sát được.

## Tiêu chí và kiểm chứng
- [ ] Test trước: CLI đọc mẫu→dự đoán→chấm→JSON với số đếm tự tính cho ca nhỏ.
- [ ] Có ca defang/hoa thường/trùng, victim/benign, văn bản rỗng, nhãn thiếu/hỏng, yêu cầu C2 chưa hỗ trợ.
- [ ] Nhãn hoặc nguồn hỏng phải báo lỗi có tên file, exit khác0; không âm thầm bỏ bản ghi hay xuất PASS cho tập rỗng.
- [ ] Kết quả hai lần chạy cùng input khớp các trường nội dung/số đo; không yêu cầu thời gian thực thi bằng nhau nếu có đo.
- [ ] Một ca có FP/FN thật để chứng minh bộ chấm; không chỉ test toàn đúng và không điều chỉnh nhãn theo prediction.
- [ ] Không gọi mạng/mở URL/chạy nội dung mẫu; không secret/LLM/OpenCTI.
- [ ] Chạy test mới và regression extractor/core cần thiết, Ruff file thay đổi, diff-check; không lặp Compose/registry/STIX không liên quan.
- [ ] Chạy lệnh demo thật, lưu kết quả và bản tóm tắt tại thư mục cha repo, để người dùng mở từ chat.
- [ ] Commit cục bộ, checkout sạch; báo SHA, lệnh, exit, số mẫu/test và hạn chế. Không push/PR/merge/deploy.

## Bàn giao
- PHONG-HOA-X01-C1-RESULT.md: kết quả, file đổi, số đo chỉ trên mẫu, hướng dẫn chạy lại và phần còn thiếu.
- PHONG-HOA-X01-C1-SMOKE-RESULT.json: output lệnh thật.
- x01-c1-evidence/: log kiểm chứng, không secret.
- X01 toàn bộ và lab/F01 vẫn chưa hoàn thành.
