# W03 Frontend QA — nghiệm thu báo cáo, chưa nghiệm thu sản phẩm

Ngày 12/11/2026. Request QA: 361cd753-519d-45f3-9e4d-a0d3c7d33650.
Candidate Frontend: 5c968c74cc53c5798bcf8adaf8695dacfd86ffd4; base 273196e2d23b36172d57cc61b289522786d61b2a.

Leader đối chiếu báo cáo với hợp đồng r1 và source, xác minh ba SHA256 report/probe/commands khớp FINAL-VERIFICATION.md, chạy lại nguyên ba probe ngoài source. Kết quả: 3 test, 0 pass, 3 fail assertion, exit 1; không phải lỗi tải bộ kiểm. Artifact mới: probe-results.json, probe-run.log, input-hashes.json cùng thư mục này. Source sau kiểm đúng HEAD, status sạch. Không chạy lại focused39/full344/typecheck/build; số baseline39 là bằng chứng QA.

Nghiệm thu đầu ra QA có hiệu chỉnh diễn giải:
- F1: parser cho phép notice tự do, trái thông báo cố định r1; code render notice. Đây là thiếu kiểm hợp đồng/biện pháp phòng vệ UI. Chưa chứng minh Backend có thể trả dữ liệu tài sản cho leader hoặc vượt quyền thực tế. Fix literal hoặc copy cố định không thay thế kiểm quyền server.
- F2: response có CVE trùng và match trùng được nhận. Probe hiện ghép cả hai điều kiện, vì vậy rework phải tách regression từng loại và thêm thứ tự ID giảm. Không được chỉ sửa một nửa để probe ghép xanh.
- F3: thay provider detail sang provider chưa xác định/summary đồng thời thay technologyProvider tạo 1 request Technology do response detail cũ. Đây là vi phạm điều kiện chỉ gọi sau detail của context hiện tại; chưa là bằng chứng vượt quyền API thật.

Frontend FAIL, chưa được tích hợp. QA task được accepted chỉ đối với báo cáo/bằng chứng. Giao sửa cùng Frontend tree/thread; QA kiểm Backend độc lập trên source cố định.

Backend candidate a49486caf39942019259e41514457bdb85498347 đã được cuộc chính intake lúc 01:30. Leader lượt này xác minh HEAD/status sạch, đọc r1-final.log và hợp đồng, chưa chạy lại345 test hoặc accepted Backend. Backend QA tập trung rủi ro quyền/dữ liệu/snapshot và non-mutation.

Hai lịch Phong Hỏa vẫn enabled; mục tiêu dự án chưa đạt. Lịch định kỳ trả instructionsTruncated=true; không tự sửa lịch từ bản thiếu. Không push/PR/merge/deploy, live feed/LLM/lab hoặc quyền mới.
