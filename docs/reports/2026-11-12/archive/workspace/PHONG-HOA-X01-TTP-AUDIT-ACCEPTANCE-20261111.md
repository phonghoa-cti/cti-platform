# X01-TTP-AUDIT — nghiệm thu độc lập 11/11/2026

**PASS phạm vi audit ngoại tuyến.** Không có finding cần rework trong phạm vi đã giao.

## Phạm vi và trạng thái trực tiếp kiểm

- Request: 7fa37f39-e40c-42dd-a585-b242f1219504; thread: 29dead5e-0480-4060-aba3-9287ccfaef36.
- Implementation: `$WORKSPACE\cti-x01-ttp-audit`.
- Branch: `feat/x01-ttp-audit-20261111`.
- Base: `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`.
- HEAD: `b896ad343a2e9876559649b1182c0a4feeecaaa5`.
- Diff chính xác 4 file +682/-0: module audit mới, test mới, ADR0005, PROGRESS.
- Source `cti-x01-attack-official` vẫn ở base; cả hai tree sạch trước/sau kiểm.
- Không sửa code sản phẩm hoặc tạo commit khi review; không push/merge/deploy.

## Bằng chứng Leader tự chạy

Python 3.12.13: `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`.
Cwd implementation tree. Lệnh/cwd/HEAD/stdout/exit lưu tại `leader-x01-ttp-audit-review/fresh-tests.log`.

- Pytest mới: **281 passed in 11.77s**, exit 0, không skip. Bao gồm 53 module + 217 regression bắt buộc + 11 probe bổ sung.
- Regression đúng 5 file: llm_adapter, attack_catalog, grounding, evaluate, eval_cli.
- Probe mới dùng public loader cho synthetic và asset MITRE v20.1 đã pin; public ScriptedProvider → run_extraction C2/C3 → audit. Mỗi provider đúng một call; snapshot provenance và span Unicode đúng; C3 top-level IOC eligibility không nâng quyền technique.
- Probe kiểm valid empty/fallback, đúng biên 1 MiB UTF-8, 500 mixed items, 8192 byte field, enum sai kiểu, output giữ nguyên khi input bị sửa sau call.
- Ruff check, format --check cho 2 file Python đổi; git diff --check base..HEAD: đều exit 0.
- Không lặp full suite hoặc toàn official compatibility suite. Public official seam mới không phải requalification toàn loader.

Worker evidence manifest **5/5 khớp**; report SHA `6EDCC903E8D3834C11E38174539EA26360AF7DEAE85B69774611C739A148A615`; manifest SHA `6C7DBFFDA95C233FF32C6AE3E1FD74E34DB1EBEA5714658829534F432BC706E9`.
Worker log chủ yếu là bản ghi tóm tắt lệnh/kết quả; Leader dùng lần chạy trực tiếp trên HEAD để xác nhận 270 test được báo.

Leader artifact SHA-256:
- fresh-tests.log: `11A9AE13F6E9B7BB2D3398845ACB42F27B8A069FCED4700EAD37A0A792CDB0C2`
- fresh-quality.log: `C3F0DB027A86F817821D82CACCBF8DAF70B6278F32CDE10BD3EF772316C93162`
- test_leader_seam.py: `710D6FB7AF569B2B835065374B4A948749BB9F677049919E56AEA51C760929CD`

Hai lệnh đọc phụ ban đầu tìm conftest/guard ở sai thư mục không có file; không dùng làm bằng chứng kiểm thử. Guard sau đó đọc từ workspace root đúng chỗ. Các lệnh pytest/Ruff/Git nêu trên có exit thực, không suy diễn từ exit của lệnh khác.

## Kết luận và giới hạn

Projection exact native types, source hash trước output, validate toàn mixed list, quote literal có overlap, catalog status độc lập, output frozen/scalar/tuple và reason precedence khớp contract đã duyệt. Không có call mạng/DB/provider trong audit.

Hash chỉ kiểm tính nhất quán với văn bản được truyền vào; quote và catalog active không chứng minh ngữ nghĩa. Technique vẫn unverified/eligible=false. Model thật, corpus hai người gán nhãn, precision/recall/F1 TTP, C4/RAG, W05/OpenCTI/lab/production vẫn UNVERIFIED.

## Nối việc

X01 spec yêu cầu báo cáo đánh giá; evaluator hiện bỏ semantic items và chưa xuất audit mới. Bước nhỏ tiếp theo là nghiên cứu cách nối audit opt-in vào artifact đánh giá C2/C3, giữ nguyên hành vi mặc định và không tính F1 TTP từ dữ liệu chưa được gán nhãn. Chỉ giao nghiên cứu/brief, chưa coi implementation đã xong.

Leader đã xem các cuộc đang mở một lần đầu lượt: không có Leader khác xử lý Phong Hỏa, không giao trùng. Lịch dự phòng được đọc lúc 09:34 ICT: vẫn enabled, kỳ kế 09:56, lượt gần nhất NOTHING NEW; giữ vì mục tiêu dự án active. Đây không phải bằng chứng tự phục hồi một việc bị bỏ dở.
