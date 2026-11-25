# X01 → W05 → STIX — nghiên cứu tích hợp nhỏ nhất

Task `X01-W05-STIX-E2E-NEXT`. Owner CTI Engineer / Sol medium; không giao bot khác.
Mục tiêu: lập brief đủ triển khai một kiểm chứng toàn luồng ngoại tuyến trên các thành phần đã có, bắt đầu từ file văn bản tổng hợp qua extractor C1 thật, kết thúc bundle STIX của đúng snapshot được duyệt. Chỉ nghiên cứu/brief ở lượt này, chưa sửa mã, chưa mở listener/browser/lab.

## Nguồn và trạng thái
Root `$WORKSPACE`.
Source đọc duy nhất `$WORKSPACE\cti-w05-stix-offline`, branch `feat/w05-stix-offline-20261111`, exact HEAD `ed829a0344b2d3d4392fae933e41a9c44fdcd853`, vừa kiểm sạch.
Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, W05-duyet.md, W05-draft-offline-contract.md. Đọc nghiệm thu `PHONG-HOA-W05-STIX-ACCEPTANCE-20261111.md`, `PHONG-HOA-W05-SELECTION-INTEGRATION-ACCEPTANCE-20261111.md`, cùng research/Leader plan STIX và local integration đã có; chỉ phần liên quan, không nghiên cứu lại mapping/UUID/UI/auth.
Code cần đối chiếu: `extractor/draft/run.py`, CLI lưu kho/review hiện có, `extractor/phonghoa_extractor/drafts.py`, `store.py`, `stix_export.py`; `tools/local_integration/runner.py`, `gateway.mjs`, tests/run_selection_matrix.py; API v1 và UI hiện có khi cần.
Tái dùng nghiên cứu official đã kiểm (SQLite transaction, STIX2.1, Python pathlib/os, Origin/browser). Chỉ tìm nguồn primary mới cho quyết định còn chưa rõ; ghi reused/new/unverified. Nghiên cứu trước chọn cách, tối đa 2 cách, tránh tạo evaluator/harness/fixture framework thứ hai.

## Câu hỏi phải giải quyết
1. Luồng hiện có đã nối được tới đâu bằng code/lệnh cụ thể? Fixture harness đang viết draft bằng tay ở đâu? Đề xuất seam nhỏ nhất cho input đi qua build_regex_draft/CLI thật, lưu created_by_subject synthetic và giữ evidence Unicode/source hash/TLP.
2. So reuse harness với một script CLI/API in-process. Chọn đường nhỏ nhất vẫn chứng minh integration; nếu bước nào chỉ mock/in-process thì phân biệt với HTTP/browser. Nếu khuyến nghị browser, dùng đúng trình duyệt tích hợp đã dùng, không tự mở browser khác.
3. Cùng một run/DB: văn bản tổng hợp có ít nhất2 IOC eligible + Unicode; analyst bỏ1→lưu→duyệt; export chỉIOC còn lại, report/provenance/hash/audit/version nối đúng nguồn. Không dùng payload_json viết tay để giả bước extractor. Không vá nguồn sau duyệt.
4. Fail cases có ích: pending/rejected không xuất; lỗi/refresh không gửi lại POST; export khácbytes không ghi đè; DB/source không đổi bởi export; cleanup ownership/PID/temp đúng. Tái dùng bằng chứng unit/gateway/lifecycle hiện có, không lặp mọi suite.
5. Export phải diễn ra trước cleanup DB; evidence lưu redacted an toàn, không ghi JWT/key/reviewer subject hoặc raw nguồn thật. Fixture toàn synthetic; không gọi model thật/OpenCTI/feed.
6. Đề xuất exact new worktree/branch từ HEAD trên, file scope, acceptance matrix, lệnh/expectedresults, cleanup và handoff. Không tạo tree ở nhiệm vụ nghiên cứu. No dependencies/lock changes nếu không có blocker cụ thể; không mở UI/upload/export API tính năng mới.
7. Nêu rõ khoảng trống còn lại của spec W05 (OpenCTI thật và metrics nếu chưa có) để Leader phân biệt xong demo với xong tính năng. Không tự mở thêm scope.

## Hai đầu ra được ghi
- `$WORKSPACE\PHONG-HOA-X01-W05-STIX-E2E-RESEARCH.md`
- `$WORKSPACE\PHONG-HOA-X01-W05-STIX-E2E-IMPLEMENTATION-BRIEF.md`
Không sửa repo/RUNS/review/evidence cũ. Git HEAD/status trước/sau và SHA256 hai tài liệu; không bịa test đã chạy. Không push/PR/merge/deploy, chi tiền, secrets, cloud/LLM thật hoặc lab. Nếu phát hiện kiểm toàn luồng đã có đủ bằng chứng, chỉ ra chính xác để tránh triển khai trùng và đề xuất phần thiếu nhỏ nhất.
