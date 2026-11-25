# W03-S1 recheck — Backend đạt, Frontend cần sửa hai lỗi còn lại

12/11/2026, kiểm source sạch đúng Backend `4f7100cf83e57b1cb30a12472ed71a0cd985a413`, Frontend `13b8025274a70ec88dc21dd9ca7f51c68961e881`. Delta tương ứng 3 file +229/-24 và 4 file +168/-54, đúng allowlist, diff-check sạch. Không đổi source đồng đội.

## Kết quả Leader chạy mới

- Backend 49 test source + 8 probe gốc = **57 PASS**, exit0, `backend-probes-recheck.log`. Lần thử chỉ gọi probe ngoài root không nạp pytest.ini nên lỗi import trước tests; giữ riêng `backend-recheck-setup-error.log`, không tính là lỗi product. Command đã dùng đúng source như vòng trước.
- Frontend 7 probe gốc = **7 PASS**, exit0, `frontend-probes-recheck.log`.
- 13 mục hash (9 artifact gốc Leader +4 mục SHA256SUMS Backend) khớp; probe gốc không đổi. Không lặp full174/151/typecheck/build; các số đó lấy từ báo cáo/evidence đồng đội, không gọi là lượt Leader chạy.
- Wire từ API Backend thật trong test: tạo status v1, đổi display vendor/product `Fortinet/FortiOS` → `FORTINET/FORTIOS` bằng TechnologyStore.update hợp lệ. GET status và history đều200; record snapshot cũ giữ nguyên, review_required=true. **1 PASS**, exit0, `test_wire_casefold.py`, `casefold-api-proof.log`, `casefold-api-wire.json`. Đây là API in-process với fixture tổng hợp, chưa qua gateway/browser.
- Đưa hai wire đó qua parser Frontend và chạy thêm tình huống close/reopen: **3 FAIL**, exit1, `frontend-recheck.test.tsx`/`frontend-recheck-red.log`. Lỗi fixture URL ban đầu xảy ra trước test được giữ riêng tại `frontend-recheck-fixture-setup.log`; sau sửa đường dẫn cả3 test thực sự chạy.

## B1/B2 Backend — ACCEPTED_LOCAL

Strict body validation trước dependency, ngày thực và persisted relation/status/audit đã được sửa; 8 lỗi gốc đóng. Review diff và regression mới xác nhận kiểm audit chain trước PUT, giữ snapshot cũ hợp lệ và rollback/non-mutation khi dữ liệu hỏng. Nghiệm thu input Backend tại4f7100cf; chưa nghiệm thu gateway, UI hoặc toàn W03-S1.

## Frontend — REWORK_REQUIRED, chỉ hai nguyên nhân

**F5 MEDIUM: exact display equality phá identity casefold.** `sameRelation` so vendor/product nguyên văn. Backend giữ cùng identity khi chỉ đổi hoa/thường, nhưng Frontend từ chối cả status và history hợp lệ. Cần giữ semantics khóa W04 (casefold) và snapshot cũ, không đổi contract hoặc dùng lowercase đơn giản rồi nhận là Unicode casefold đầy đủ. Quyết định triển khai cho lượt sửa: ở frontend xác nhận relation bằng technology_id+CVE ID được yêu cầu, tiếp tục validation từng field và version/dataset; vendor/product display là snapshot, không dùng exact display equality để loại response. Backend là bên xác thực khóa vendor_key/product_key trong DB. Không thêm field wire, dependency hay tự triển khai bản sao chuẩn hóa Unicode ở UI. Quy tắc review_required đúng iff saved technology_record_version hoặc dataset_id khác; nếu hai giá trị bằng nhau nhưng snapshot display/software_version khác thì reject cross-field sai. Khi version cũ khác thì cho snapshot cũ hợp lệ. ID/CVE sai luôn reject như probe gốc.

**F6 HIGH: pending bị kẹt sau close/reopen gặp409.** PUT từ instance cũ còn chạy; mở lại cùng relation/provider nhận pending. Khi PUT cũ trả conflict, clearOperation chỉ xóa map, không thông báo instance mới; nó giữ pending vĩnh viễn, không GET context mới. Cần cập nhật trạng thái thao tác dùng chung và thông báo đúng subscriber hiện tại, để conflict yêu cầu re-entry/GET mới; không cho callback cũ trực tiếp sửa màn hình mới. Các lỗi known-failure khác cũng không được để pending ma; unknown vẫn giữ khóa tới GET thành công. Probe kiểm PUT đúng1, GET3 và không tự replay.

## Quyết định nối việc

Backend accepted; Frontend chưa accepted. Giao Frontend sửa hai nguyên nhân trong tree/thread cũ. Giao Engineer đầu việc độc lập chuẩn bị gateway/HTTP trên tree mới từ Backend accepted, không ghép candidate Frontend chưa đạt và không chạy browser. Phần ghép UI/browser vẫn chờ cả Frontend và prep đạt. Đã kiểm threads một lần: không có Leader khác đang xử lý; đã đọc hai lịch liên quan, giữ enabled vì project còn mở.
