# W03-S1 — chưa đạt nghiệm thu, 12/11/2026

Leader đã đọc báo cáo, diff và mã đúng hai candidate sạch: Backend `b8957e63acc7497ba835e06c05e52f4b16ef136c`, Frontend `e31f0b40ac7ed8a8acb31968485c281fc2b3b7b0`. Base chung `7ff6eb3af21d8de65836bfbf707396ae5690de0b`. Hai diff trong allowlist; chưa ghép, chưa sửa source của đồng đội.

Các kết quả W03-R và nghiên cứu đã accepted được giữ nguyên. Đây chỉ là review phần status/history mới theo `PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md` (SHA-256 `542887d06ba34b5774e9a72a2a69c18c4b1631883408918adf7ef7981e0fb264`).

## Kiểm trực tiếp của Leader

- Backend: chạy 14 test status hiện có cùng 8 probe độc lập; 14 PASS, 8 FAIL assertion, exit 1. `backend-probes.log` và `test_backend_probes.py` là bằng chứng. Python lấy từ venv W03 read backend; source import từ status backend.
- Frontend: 7 probe độc lập đều FAIL assertion, exit 1. `frontend-probes.log` và `frontend-probes.test.tsx` là bằng chứng. Lần đầu setup ngoài root lỗi trước khi có test, được giữ riêng tại `frontend-harness-setup.log`; sau đổi setup sang thư mục review, cả 7 test đã thực sự chạy. Không tính lỗi setup là lỗi sản phẩm.
- Không chạy lại full 377/143; các số đó là báo cáo của đồng đội, không phải kết quả chạy mới của Leader. Không có browser mới hoặc tích hợp API/UI trong lượt này.

## Backend cần sửa

**B1 — HIGH, validation đầu vào trước dependency.** `expected_technology_record_version=true` và `1.0` đều được nhận như integer 1, trả 200 và ghi. Note chứa NUL gặp nguồn lỗi trả 503 thay vì 422; body chưa được validate trọn trước gọi port. Sửa strict kiểu/range và thứ tự theo brief, không chỉ kiểm tập key.

**B2 — HIGH, dữ liệu lưu hỏng phải dừng đọc/ghi.** Ngày không tồn tại `2026-02-30T00:00:00Z` vẫn GET/history 200; PUT tiếp trả 200 thay vì 503, cho dữ liệu hỏng đi vào audit mới. Status lưu `bogus` trả 422 client error thay vì 503. Context JSON của record trỏ technology 999/CVE khác vẫn GET 200. Cần calendar validation, phân biệt lỗi request/persisted row và bind record/audit với khóa relation được đọc. Kiểm trước DML, giữ SQL snapshot nguyên khi lỗi.

## Frontend cần sửa

**F1 — HIGH, khóa khi chưa biết kết quả ghi.** PUT không rõ kết quả rồi GET lỗi nhưng nút Lưu vẫn enabled với response/note cũ. Chưa đủ điều kiện cho mutation mới; giữ khóa tới GET thành công và không khẳng định PUT cũ thành công từ GET.

**F2 — HIGH, quyền cập nhật màn hình của callback.** Đang PUT cho A, chuyển technology sang B và đã hiển thị B, response A về làm panel mang ID B hiển thị record/context A. Cần kiểm owner provider/relation/generation cho mọi completion/refresh/error/finally.

**F3 — MEDIUM, history 409.** Giao diện báo lịch sử thay đổi nhưng vẫn giữ trang cũ và nút trang sau. Bỏ tập trang/cursor cũ, cho tải lại từ đầu bằng GET có chủ ý.

**F4 — MEDIUM, parser/provider chưa giữ contract.** GET cho relation 1 nhận wire relation 2 vẫn resolve; review_required=true cho phép record của relation khác; history limit101 được nhận; vendor129 được nhận. Cùng nguyên nhân bound đang hardcode200 cho cả ba trường, trong khi W04 vendor128/product256/software_version128. Bổ sung valid controls để không từ chối product201..256 hợp lệ.

## Cách chạy lại

Từ `ROOT/cti-w03-status-backend`:
```powershell
..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m pytest portal_api/tests/test_cves_status_api.py ../leader-w03-status-review-20261112/test_backend_probes.py -q --tb=short
```

Từ `ROOT/leader-w03-status-review-20261112`:
```powershell
.\node_modules\.bin\vitest.cmd run --config vitest.config.ts --reporter=verbose
```

Probe/config/setup/tsconfig giữ nguyên sau review; hash trong `review-manifest.json`. Node_modules tại review là junction tới dependencies Frontend hiện có, không thay package/lockfile. Đồng đội ghi log GREEN vào evidence riêng, không ghi đè log RED của Leader.

## Quyết định

Hai input **REWORK_REQUIRED**. Sửa trong đúng thread/tree cũ, mỗi người Sol medium trực tiếp; chưa giao Engineer tích hợp. Project và hai lịch tiếp tục giữ active; đã đọc trạng thái lịch 03:55 giờ Việt Nam. Lịch định kỳ trả instructionsTruncated=true nên không sửa instruction từ bản preview thiếu. Mobile, nguồn thật/OpenCTI, Cloudflare/JWKS, lab và production vẫn UNVERIFIED.
