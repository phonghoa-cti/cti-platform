# X01-ATTACK — nghiệm thu sau rework R1/R2

Ngày 11/11/2026. **PASS cục bộ, fixture tổng hợp**. Không đồng nghĩa C4/RAG hoặc tương thích MITRE thật.

- Task X01-ATTACK-IMPLEMENT; request rework d23a3050-d38e-40e7-ab4f-acc286e152fd; thread 9f96a7bd-dc43-42c5-8406-9c04903eeb3e.
- Tree `$WORKSPACE\cti-x01-attack-offline`; branch feat/x01-attack-offline-20261111.
- Base 8694fa7244d181f421bb2733ded7bf9ae218ea93; reviewed implementation a5663b12d37bcec6a75b639409096fe4943192fd; accepted HEAD **4e894c37df3ad53c16022909ae6df113dd89aa04**.
- Leader đọc toàn diff rework: 3 file +109/-3, đúng scope. R1 so cấu trúc JSON đệ quy phân biệt boolean/number, giữ thứ tự key không quan trọng và numeric equality; R2 bắt lỗi đường dẫn tại biên đọc file, không catch toàn loader.
- Leader chạy mới trên HEAD: nguyên probe 13 ca + 2 ca numeric equality = **15 passed, exit 0**, 0.36s. Log `leader-x01-attack-review/rework-green-head-4e894c3.log`.
- Probe SHA256 giữ nguyên **688B06F844B0DAA96E902AB73A9737517D0D2975D04C850965F3C54C5BC9CC35**. RED Leader trước sửa: 9 failed/4 passed.
- Evidence worker đọc và đối chiếu: catalog **104 passed**, probe13 passed; catalog/ruff/format/diff exit 0. Không nhận 122 regression cũ là test mới.
- Manifest rework: **17/17 khớp**, gồm 15 log, báo cáo và probe. Báo cáo SHA256 56c5cdf819e43bf50872cbaf4f115e598755e702d6d3dd446ac42b569004d231.
- Leader chạy mới Ruff check/format và diff-check a5663b1..HEAD: exit 0. Tree triển khai sạch; source cti-platform-ai-llm-adapter sạch tại base8694fa7. Không sửa source sản phẩm trong lượt nghiệm thu.
- Không lặp full suite, 122 regression, UI/browser vì không đổi các module liên quan. Không push/PR/merge/deploy/model/lab.

Lệnh kiểm mới (cwd tree triển khai):
~~~powershell
& '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider ../leader-x01-attack-review/test_attack_catalog_leader_r1.py extractor/tests/test_attack_catalog.py::test_exact_json_duplicate_preserves_json_number_equality -q --tb=short
~~~

Nghiệm thu dựa trên diff, test nguyên trạng và evidence đúng SHA; không chỉ dựa báo cáo worker. Không còn finding bắt buộc mở trong phạm vi R1/R2.

Giới hạn: chỉ hỗ trợ pin synthetic; snapshot MITRE thật/license/NOTICE, adapter/C4/RAG, ngữ nghĩa TTP, model/corpus, W05/OpenCTI/lab/production chưa kiểm. Các trạng thái lookup vẫn semantic unverified và operational_draft_eligible=false.

Bước kế đủ điều kiện: **X01-ATTACK-REAL-NEXT**, CTI Research khảo sát dữ liệu Enterprise MITRE công khai và lập brief compatibility nhỏ nhất; không sửa loader để giả dữ liệu thật thành synthetic. Lịch phục hồi còn bật, chu kỳ30 phút; đã đọc lại lúc08:31 giờ Việt Nam, next08:56:14. Đây chỉ là trạng thái lịch, không phải kiểm phục hồi việc bỏ dở.
