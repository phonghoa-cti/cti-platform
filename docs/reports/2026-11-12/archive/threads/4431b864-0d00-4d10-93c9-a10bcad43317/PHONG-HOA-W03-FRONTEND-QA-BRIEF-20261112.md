# W03-READ-FRONTEND-QA — rà soát ứng viên trước tích hợp

## Mục tiêu và căn cứ
Kiểm độc lập phần mới/rủi ro của Frontend W03 ở đúng commit; trả kết luận có cách tái hiện, không sửa sản phẩm. Tái dùng nghiên cứu và hợp đồng đã chốt trong PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md. Không mở thêm phạm vi thiết kế hoặc nghiên cứu nguồn thật.

ROOT = $WORKSPACE
OUT = $THREADS\4431b864-0d00-4d10-93c9-a10bcad43317
Source chỉ đọc: ROOT\cti-w03-read-frontend
Base: 273196e2d23b36172d57cc61b289522786d61b2a
Candidate: 5c968c74cc53c5798bcf8adaf8695dacfd86ffd4
Branch: feat/w03-read-frontend-20261112

Đọc AGENTS.md/PROGRESS/spec W03 đúng source, ROOT\PHONG-HOA-W03-IMPLEMENT-BRIEF-20261112.md (hợp đồng r1 ưu tiên DTO lịch sử), ROOT\PHONG-HOA-W03-FRONTEND-RESULT.md và ROOT\w03-frontend-evidence. Giữ thiết kế sẵn có.

## Intake Leader, 12/11/2026 khoảng 01:28 Việt Nam
- Danh sách cuộc làm việc: Backend W03 running, Frontend W03 idle; QA không có lượt W03 đang mở. Lần tìm lời nhắn gần nhất của cuộc Leader chính là 01:00, đã nhường lượt; chưa có ghi nhận review W03 trong sổ.
- Đã đối chiếu Git HEAD đúng candidate, status sạch, diff 14 file (+1398/-1); diff --check exit 0.
- Đã đối chiếu SHA256 hai fixture đúng báo cáo: detail adcc16640ae425fd91955048ff17ddc60a3fb9476421d36531a2f596f40dd309; summary fbccb17fca29d4dc00db16a4ce80156acc29a52ed437c36d48e246adaab96994.
- Báo cáo SHA256 c60b18b74d598e16d893ffd9d35abfbc3bee3d8090106ec206f016b0b1eb9c25. 344 tests/typecheck/lint/build là lời báo của Frontend, Leader chưa chạy lại.
- Chưa accepted. Đọc trạng thái assignment trực tiếp bị giới hạn vì nơi giao là cuộc chính; không suy diễn callback đã xử lý. Báo cáo/file/Git là căn cứ intake này. Không giao lại việc lập trình hay thay receipt Frontend/Backend.

## Phạm vi kiểm
Một CTI QA Security Sol medium tự làm, không giao tiếp/worker con. Source chỉ đọc: không đổi HEAD/index/branch, không sửa tests/deps/cache có chủ đích. Probes mới và artifact chỉ đặt OUT\w03-frontend-qa-evidence; nếu cần sandbox dùng một bản sao riêng trong OUT. Không đọc/sửa tree Backend đang hoạt động.

Ưu tiên:
1. Parser detail/summary: không chấp nhận rò trường tài sản trong summary, giới hạn kiểu/null/0/URL/ngày và kích thước body, dữ liệu không tin cậy được render an toàn.
2. Request ownership: đổi provider/filter/view, tải trang, mở/đóng detail, unmount; callback A không thay data/loading/notice/options của B. Summary không gọi Technology API, không giữ/hiện metadata detail cũ.
3. Pagination/snapshot409: bỏ cursor/selection cũ, chỉ tải lại do thao tác người dùng, không trộn trang khác snapshot. GET-only, no fixture fallback ở route thật, không replay/retry ngầm.
4. Đối chiếu r1 và UI hiện có; kiểm các cạnh thực sự chưa được test. Mỗi phát hiện cần file:line, tác động, input/tương tác tái hiện, expected/actual, test/probe output và sửa tối thiểu. Không báo lệch ràng buộc dựa vào suy đoán nếu hợp đồng W04 cho phép.
5. Chạy focused W03 hiện có nếu cần baseline; thêm probes độc lập theo rủi ro, không lặp 344-test/build chỉ để tăng số lượng. Không chạy browser hoặc server vì chưa tới tích hợp. Không sửa sản phẩm ngay cả khi thấy lỗi.

## Bàn giao
Ghi OUT\PHONG-HOA-W03-FRONTEND-QA-RESULT.md và evidence trong OUT\w03-frontend-qa-evidence (commands, exit/count, hashes). Kết quả phân PASS/FAIL/UNVERIFIED; nêu hành vi cố ý không kiểm và lý do. Đối chiếu source HEAD/status trước/sau để chứng minh không sửa source.
Nếu PASS chỉ có nghĩa candidate frontend/component đạt phạm vi đã kiểm. API/gateway/browser/feed/OpenCTI/lab/production chưa được chứng minh. Nếu FAIL trả finding cụ thể cho Leader giao sửa cùng thread Frontend.
Không sửa RUNS/brief, không push/PR/merge/deploy, cloud/LLM thật, secrets, lab, dependencies hoặc quyền. Không thử lại quá hai lần cùng lỗi.
Sau kết quả Leader kiểm chứng; chỉ khi cả Frontend và Backend accepted mới giao Engineer tích hợp trên tree riêng.
