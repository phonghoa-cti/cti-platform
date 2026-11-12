# X01-C4-RETRIEVAL — review độc lập của Leader

Ngày 11/11/2026. Kết luận: **NEEDS_REWORK — R1**. Chưa nghiệm thu implementation.

## Ref và phạm vi

- Root: `$WORKSPACE`.
- Target `root\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, HEAD `4067598c87772dac88af309b01d127f748f369fd`.
- Source chỉ đọc `root\cti-x01-eval-report`, HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`.
- Diff 7 file, +729/-1, trong phạm vi. Hai working tree sạch khi kiểm; Leader không sửa source.
- Hợp đồng ưu tiên: `PHONG-HOA-X01-C4-RETRIEVAL-LEADER-PLAN.md`, mục 2.

## R1 — mô tả bản đã bị thay thế vẫn làm hỏng catalog

Vị trí trên HEAD được kiểm: `extractor/phonghoa_extractor/attack_catalog.py:355` gọi `_description(item, code)` trong `_parse_pattern` cho mọi phiên bản, trước `_canonical_patterns` (`:381`). `_build_records` (`:512`) chỉ nhận mô tả đã kiểm sớm đó.

Ca lỗi thực: cùng STIX ID/external ID có bản ngày 10/11 với description null/list/number/surrogate/quá 32 KiB và bản ngày 11/11 với description hợp lệ. Public `load_catalog` trả `invalid_attack_pattern`, trong khi hợp đồng yêu cầu chỉ kiểm/project description của bản canonical được chọn. Đảo thứ tự input vẫn lỗi. Một bản cũ không còn được dùng vì thế chặn toàn bộ truy hồi dù bản hiện tại hợp lệ.

Probe độc lập: `leader-x01-c4-retrieval-review/test_canonical_description_probe.py`; SHA-256 `D636C4BA3C2DE1AA14139E11A015CA0B9179D6F9565BC384F704B6787F7409AB`. **10 failed / 8 passed**, exit 1. Năm loại description cũ × hai thứ tự input tái hiện cùng lỗi. Các control bản mới lỗi vẫn bị chặn, bản mới missing/empty không lấy mô tả cũ, và oracle giới hạn byte JSON đều đạt.

Sửa nhỏ nhất: dời kiểm/project description sang sau khi chọn canonical, dùng raw của đúng bản hiện tại. Không nới validation khác, không thay duplicate/conflict/lifecycle/parent graph, không lấy fallback từ bản cũ. Mô tả hiện tại sai vẫn phải lỗi code-only. Giữ lookup và pinned fixtures nguyên trạng. Không cần sửa thuật toán retrieval.

## Kiểm đã chạy bởi Leader

1. Probe, CWD root, `PYTHONPATH=root\cti-x01-c4-retrieval\extractor`:

   `root\cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider --tb=short leader-x01-c4-retrieval-review/test_canonical_description_probe.py`

   Exit 1, 10 failed / 8 passed. Log `leader-x01-c4-retrieval-review/01-probe-red.log` và exit riêng.

2. Regression mới trên target, env `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT=root\x01-attack-real-research-evidence\enterprise-attack-20.1.json`:

   `root\cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_attack_retrieval.py`

   Exit 0; ba file đều đạt, không có skip trong output. Log `leader-x01-c4-retrieval-review/02-targeted.log` và exit riêng. Không chạy lại full repo 662 hoặc scoped 428; các số đó thuộc báo cáo worker trước rework.

3. Manifest worker: **33/33** mục khớp hash, 0 mismatch (`03-manifest-check.json`). Report SHA `2D61CD2A1F5C8ECA7E4415C4D11D76061F3885DCEECDE58F4302A25F978FCF03`; manifest SHA `AFE15FE5CB20D0EFD1530DAAA7839BD5F320EE9DE9029009B0D60D10771473F6` khớp callback.

4. Oracle độc lập thử từng byte budget từ 256 đến whole JSON đầy đủ, có dấu quote, backslash, newline/tab, tiếng Việt, emoji và combining character. Kết quả cắt mô tả là prefix dài nhất đúng budget; raw description không đổi. Đây là kiểm cơ chế, không phải chất lượng ngữ nghĩa.

## Yêu cầu bàn giao rework

- CTI AI Agent tiếp tục đúng target/branch hiện tại, Sol medium, không giao tiếp cho bot khác.
- Chỉ sửa catalog và regression catalog; cập nhật PROGRESS/ADR hiện hữu nếu cần ghi rõ chính sách canonical. Báo cáo/evidence ngoài repo.
- Thêm regression repo RED → GREEN cho R1; chạy nguyên probe Leader, giữ hash; chạy ba file catalog/official/retrieval với asset thật và không skip. Ruff check/format các file Python thay đổi, diff-check, tự review, commit local sạch.
- Không lặp full 662/evaluator/UI/build vì phạm vi không đổi các phần đó; chỉ mở rộng nếu có regression thực.
- Lưu exact command/exit/count, base→rework HEAD, diff, manifest rework riêng trong `x01-c4-retrieval-evidence/rework-r1/`; cập nhật `PHONG-HOA-X01-C4-RETRIEVAL-RESULT.md` phân biệt số test trước/sau sửa. Không sửa probe/log/review/RUNS của Leader.
- Source tree giữ đúng base và sạch. Không network/model/dependency/DB/W05/API/UI/C4 CLI/lab/push/PR/merge/deploy.

## Tiếp tục và giới hạn

Threads đã kiểm một lần ở đầu lượt: không có Leader khác đang xử lý Phong Hỏa, worker đã trả kết quả. Automation tiếp tục còn enabled, dự án active nên giữ nguyên. Nhận callback không phải bằng chứng worker còn chạy; không coi YIELD là dự án hoàn tất.

UNVERIFIED: semantic/TTP quality, multilingual recall, model/full C4, corpus thật, lab/OpenCTI/production. Không gộp các kết quả cục bộ thành tuyên bố hoàn thành dự án.
