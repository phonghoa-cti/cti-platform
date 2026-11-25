# Nghiệm thu W05 Selection Integration — 11/11/2026

**PASS cục bộ.** Nghiệm thu commit `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2` trên branch `feat/w05-selection-integration-20261111`. Rework R1/R2 chỉ bổ sung bằng chứng; HEAD không đổi, working tree sạch, không commit rỗng.

## Bằng chứng Leader đã đối chiếu

Review mã và kiểm chạy ở lượt trước: `PHONG-HOA-W05-SELECTION-INTEGRATION-REVIEW-20261111.md`. Leader đã chạy mới gateway **9/9** và HTTP selection **113 checks/10 scenarios**, đều exit 0. Không chạy lại các suite này trong lượt nghiệm thu vì source không đổi.

Lượt này đọc trace/capture/verify helper, audit JSON, correction và ảnh sau retry trong `w05-selection-integration-evidence/rework-evidence/`. Helper trace gọi gateway nguyên bản, chỉ quan sát method/path/status; không thay logic API/UI, không ghi token/body/header. Kết quả:

| Ca kiểm | Bằng chứng đã đối chiếu |
|---|---|
| Save rồi tải lại | Giữa hai marker chỉ hai GET503; tổng selection POST1, decision POST0. Audit pending/review1/selection1, một event `[1]`. |
| Duyệt rồi tải lại | Giữa hai marker chỉ hai GET503; tổng decision POST1, selection POST0 từ browser. Audit approved/review2/selection1, một final decision; hash/indices khớp selection. Ảnh sau retry còn xác nhận đã duyệt. |
| Trang mẫu | Trace lượt riêng chỉ marker sau load; không request drafts legacy/v1. |
| Cleanup | Ba run có ba listener khớp đúng PID API/gateway/UI trước close; sau close không listener, child PID, API thread hoặc temp owned. |

Leader chạy `verify-rework.py`: PASS retry2/2, POST counts1/0 và0/1, sample API0, cleanup3/3, exit0. Leader còn đối chiếu riêng mapping port↔PID trước close và kiểm trạng thái hệ điều hành hiện tại: cả ba run đều **0 listener, 0 process theo PID đã ghi, temp chính xác không tồn tại**. Không suy từ socket10035.

Manifest worker hiện có **43/43 mục khớp hash**. UI subtree vẫn `dffcc2fa8f11a24ea34f5fe4c71e995bd68549f2`; diff từ base43737 đối với `portal/web` và `requirements-api.lock` rỗng. `git diff --check` exit0. JUnit182 và Vitest89 là raw bằng chứng worker đã đối chiếu ở lượt trước, không gọi đó là Leader chạy lại.

## R1/R2 đã đóng

- R1: raw cleanup cũ được bảo toàn, cách diễn giải10035 được sửa và không còn được dùng để chứng minh đóng cổng. Bằng chứng mới có ownership trước/sau, kiểm trạng thái hệ điều hành và temp đúng đường dẫn.
- R2: có trace request của browser bao quanh thao tác retry thực, audit cùng run và ảnh; không dùng unit test thay chứng cứ browser cho các ca này.
- Lượt instrumentation đầu thất bại được giữ rõ trong observations, không tính là run PASS.

## Giới hạn và bước tiếp

PASS này áp dụng loopback, JWT/JWKS và SQLite tổng hợp. Chưa xác minh Cloudflare/JWKS/HTTPS thật, lab, OpenCTI, dữ liệu thật hoặc production. Chưa chứng minh viewport360/1440. Giữ ghi nhận9advisory moderate từ lock hiện hữu; không đổi dependency trong lát cắt tích hợp.

W05 spec còn yêu cầu tạo Report và object STIX sau duyệt. Bước kế được chọn là **nghiên cứu bộ chuyển snapshot đã duyệt thành gói STIX ngoại tuyến**, tái dùng fixture/validator hiện có; chỉ nghiên cứu và lập brief trước khi giao triển khai. Không mở đường ghi OpenCTI hay tự xuất/chặn dữ liệu lên hệ thống thật. F07 blocklist là chức năng khác, chưa đưa vào nhiệm vụ này.

Đã kiểm các cuộc mở: không có Leader khác đang làm; Engineer đã idle. Automation tiếp tục vẫn bật, lần05:56 hoàn tất NOTHING NEW, lịch kế06:26 giờ Việt Nam. Chưa có bằng chứng phục hồi việc bỏ dở tự động; không nâng trạng thái đó thành PASS. Dự án vẫn active.
