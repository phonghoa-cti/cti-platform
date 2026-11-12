# X01-OFFLINE-QA — kiểm độc lập luồng bản nháp cục bộ

Ngày 10/11/2026. Owner: CTI QA Security, Sol medium. Đây là kiểm chứng thực tế, không phải consultation.

## Đích và phạm vi

Xác định luồng văn bản tổng hợp → IOC có evidence/span → draft pending → SQLite → danh sách phân trang →
đọc chi tiết có đạt tiêu chí ngoại tuyến hay còn lỗi cụ thể. Đây là mốc tích hợp nhiều phần nối tiếp đã sửa,
nên cần góc kiểm độc lập; không mở cuộc pentest HTTP hoặc rà soát toàn repo.

Repo đọc: `$WORKSPACE\cti-platform-start`.
Ref duy nhất: `d03fa10523b45b94182038b5b46fed8231319e6f`, nhánh `feat/x01-draft-queue-20261110`.
Đầu ra riêng cùng thư mục cha repo: `PHONG-HOA-X01-OFFLINE-QA-RESULT.md` và `x01-offline-qa-evidence/`.

Không sửa repo, nhánh, source/tests hoặc DB/log bằng chứng cũ. Mọi mẫu/DB mới chỉ ở thư mục evidence riêng.
Kiểm SHA và git status đầu/cuối; nếu ref thay đổi thì báo, không tự checkout/reset. Không gọi worker khác.

## Nguồn và bằng chứng dùng lại

Đọc AGENTS, docs/PROGRESS.md, docs/specs/X01-ai-extractor.md, W05-draft-offline-contract.md,
extractor/draft/README.md. Tái sử dụng nghiên cứu nguồn trong PHONG-HOA-OFFLINE-CONTINUATION-PLAN.md,
PHONG-HOA-X01-QUEUE-BRIEF.md và PHONG-HOA-X01-W05-CONTRACT-BRIEF.md ở thư mục cha repo.
Các nguyên tắc đã chọn: stdlib Python 3.12; SQLite transaction/mode=ro; code point [start,end) trên nguyên text;
reuse core normalize và evidence token boundary; dữ liệu nguồn không là chỉ thị, luôn pending.

Leader vừa tự chạy **77 store/queue tests đạt** tại ref này, log `x01-queue-evidence/13-leader-store-queue.log`.
Engineer toàn suite 192 test đạt, Ruff/format/diff-check đạt; Leader đã đọc log và code. Không chạy lại toàn
suite hoặc chỉ lặp các ca sẵn có rồi gọi đó là review độc lập. Chọn vài ca còn thiếu đáng kiểm sau khi đọc source.

## Tập trung kiểm

1. Grounding và roundtrip: các token đã defang, Unicode/emoji/xuống dòng, quote lặp/biên token, rejected/allowlist
   và findings không bị đổi/mất; source hash khớp text đã lưu. Mẫu chỉ tổng hợp, không tải dữ liệu thật.
2. Ranh giới JSON và SQLite: dữ liệu sai bị từ chối đúng, lỗi không phá bản ghi cũ; phân biệt trường hợp
   đang được builder tạo ra với đầu vào JSON sửa tay, DB hỏng hoặc DB do người có quyền local sửa.
3. Chạy một luồng CLI riêng đủ các bước với DB mới: save nhiều draft→list trang→chọn ID→get; đối chiếu payload.
   Kiểm có lựa chọn ít nhất một ca không trùng test sẵn. Không cần lặp hàng loạt lock/hardlink đã có bằng chứng.
4. Summary và lỗi không vô tình trả toàn văn/evidence; các lệnh đọc không làm thay đổi DB;
   output không trùng file DB; kiểm cụ thể nếu thấy code có đường tránh, không nêu rủi ro tưởng tượng.
5. Đọc docs so với runtime: xác nhận giới hạn được nói đúng. Chưa có auth/quyền/approve/UI/OpenCTI là ngoài
   phạm vi hiện tại, không báo thành lỗ hổng HTTP. Không suy từ test xanh thành chống mọi prompt injection.

Giới hạn đã biết và được ghi rõ: schema hiện tại chưa khóa mọi kind/item.status ngoài IOC kept;
trước mở API phải có validator cho loại được hỗ trợ. Nếu đề cập, phân biệt việc cần làm trước tích hợp
với lỗi mới trong luồng offline. Không báo lại như phát hiện mới nếu không chứng minh tác động mới.

## Bàn giao

- Verdict PASS / NEEDS_FIX / UNVERIFIED trong đúng phạm vi, không khẳng định dự án hoàn thành.
- Mỗi lỗi: mức độ, file:line, SHA, đầu vào/các bước tái hiện, kết quả thực tế/mong đợi và gợi ý sửa tối thiểu.
  Phân biệt lỗi cần sửa trước mốc offline với hardening dành cho bước HTTP.
- Liệt kê phép kiểm thực sự đã chạy, lệnh/exit, artifact, phần chỉ đọc và phần chưa xác minh.
- Không commit hoặc sửa hộ; Leader quyết định rồi giao Engineer nếu cần. Nếu không có lỗi chặn, nêu
  tối đa một bước phần mềm ngoại tuyến hữu ích tiếp theo dựa trên khoảng trống đã có, không tự triển khai.
- Không mạng/model, secret, lab, push/PR/merge/deploy, malware hoặc thay quyền. Không mở browser/UI.
  Khi một nguyên nhân lỗi công cụ lặp hai lần, đổi cách hoặc báo rõ thay vì vòng retry.
