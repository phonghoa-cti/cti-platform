# W05 Selection Integration — review Leader ngày 11/11/2026

Kết luận: **PASS phần mã tích hợp và HTTP; NEEDS_EVIDENCE R1/R2 trước nghiệm thu trọn brief**. Không phát hiện lỗi triển khai mới trong diff được giao. Không yêu cầu sửa UI/API/core hoặc dependency.

## Phạm vi và bằng chứng đã kiểm

- Tree: `$WORKSPACE\cti-w05-selection-integration`.
- Branch `feat/w05-selection-integration-20261111`, HEAD `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`, base `43737c000561c4d676705dbb564223a7bfa3596e`; working tree sạch.
- Diff 8 file, +550/-16 đúng phạm vi. Gateway thêm allowlist v1 và body cap 65536; legacy giữ 8192. Runner chỉ thêm fixture/scenario; giữ lifecycle/cleanup đã nghiệm thu.
- UI subtree thực tế `dffcc2fa8f11a24ea34f5fe4c71e995bd68549f2`; diff `portal/web` (gồm package lock) và `requirements-api.lock` từ base rỗng.
- Manifest worker: 26 mục, 0 mismatch. JUnit worker: 182 test, 0 fail/error/skip; UI raw log: 89 test đạt. Đây là bằng chứng đọc lại, không phải Leader chạy lại 182/89.
- Leader chạy mới `node --test tools/local_integration/tests/test_gateway.mjs`: **9/9, exit 0**; gồm boundary/chunked và R1/R2 gateway cũ.
- Leader chạy mới `.venv/Scripts/python.exe -X utf8 -B tools/local_integration/tests/run_selection_matrix.py`: **113 checks/10 scenarios PASS, exit 0**.
- Leader đọc matrix, capture script, audit JSON, STEPS và xem hai ảnh save-refresh/decision-refresh: giữ xác nhận và khóa hành động đúng. Audit có payload hash trước/sau giống nhau, selection v1 `[1]`, review v2, hash selection/final audit giống nhau.
- Leader kiểm hiện tại bằng `Get-NetTCPConnection -State Listen`: **0 listener** trên 6 cổng được liệt kê; truy vấn process có command line chứa tree không trả process. Quan sát hiện tại không chứng minh mọi PID/temp của các lần chạy trước.
- `git status --short` rỗng và `git diff --check` exit 0 sau các kiểm tra mới.

## R1 — sửa diễn giải và hoàn thiện bằng chứng cleanup

`w05-selection-integration-evidence/cleanup.log` viết “Windows connect_ex 10035 means connection refused”. Điều này sai: 10035 là WSAEWOULDBLOCK, chưa đủ kết luận kết nối bị từ chối; WSAECONNREFUSED là 10061. Nguồn Microsoft: https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2 . Không có bằng chứng đang rò tài nguyên; đây là lỗi phép kiểm/kết luận.

Yêu cầu:

1. Giữ raw log cũ, thêm correction rõ; sửa diễn giải trong report/STEPS để không coi 10035 là bằng chứng cổng đã đóng.
2. Khi chạy các browser case R2, ghi danh sách PID/port/temp thực sự do từng run sở hữu (không token/key/environment). Sau `close()`, dùng trạng thái listener hệ điều hành và PID liveness thực; kiểm chính xác temp đã ghi không tồn tại. Không kết luận “closed” chỉ vì timeout/10035 và không dừng process không thuộc run.
3. Báo riêng quan sát mới và giới hạn bằng chứng lịch sử, cập nhật manifest. Không cần chạy lại toàn suite.

## R2 — thiếu bằng chứng browser cho thao tác tải lại và trang mẫu

STEPS mới mô tả ảnh sau POST thành công/GET503; phần không replay POST được viện dẫn từ Vitest. Trang mẫu cũng viện dẫn test UI cho “không POST”. Brief yêu cầu browser thực cho các luồng này; ảnh tĩnh và unit test chưa ghi nhận request khi người dùng bấm tải lại.

Yêu cầu kiểm có giới hạn trên HEAD trên, bằng Trình duyệt tích hợp được cấp:

1. Với `selection-save-refresh-503`, thao tác save rồi bấm “Tải lại trạng thái” một lần; lưu trace method/path/status sạch chứng minh chỉ GET phát sinh khi retry, tổng POST selection vẫn 1, decision 0; confirmation/snapshot/khóa không lùi. Audit cùng run vẫn đúng một selection event và chưa có decision.
2. Với `selection-decision-refresh-503`, approve rồi bấm “Tải lại trạng thái” một lần; trace chứng minh tổng decision POST vẫn 1, không selection POST từ browser (fixture đã có selection v1), retry chỉ GET; terminal confirmation còn nguyên, audit chỉ một final decision.
3. Mở `/duyet/mau` trong lượt quan sát riêng/reset network log và ghi nhận không request `/api/drafts*` hoặc `/api/v1/drafts*`; không suy từ nội dung nhãn hay Vitest. Dùng trace của bề mặt browser nếu có. Nếu công cụ không quan sát được network, dùng bộ đếm method/path/status ở harness chỉ phục vụ kiểm, không ghi header/body/token, không đổi UI/API; ghi rõ giới hạn nếu vẫn không thể chứng minh.
4. Không cần fault tự hồi phục 200: brief chỉ yêu cầu tải lại an toàn, có thể GET tiếp tục503. Không mở rộng chức năng, không sửa UI để phục vụ test.

## Ranh giới rework

- CTI Engineer / Sol medium, cùng tree; không giao tiếp worker khác, không sửa RUNS/review Leader.
- Ưu tiên chỉ bổ sung evidence/report: `w05-selection-integration-evidence/rework-evidence/`, report hiện hữu và manifest. Nếu cần bộ đếm riêng thì helper ở evidence; nếu buộc sửa harness, chỉ `tools/local_integration/` với test cần thiết và commit cục bộ, báo diff chính xác.
- Không lặp 182 Python, 89 UI, build hoặc HTTP113 đã đạt nếu source không đổi. UI/lock/core/API/settings giữ nguyên. Không mạng bên ngoài, JWT thật, secret, lab, OpenCTI, push/PR/merge/deploy.
- Trình duyệt phải là bề mặt được cấp; không thay bằng browser tự mở từ shell. Cleanup chỉ tài nguyên sở hữu; không xóa glob thư mục hoặc dừng process theo tên.
- Báo head/dirty, lệnh và exit, trace/count/audit cùng run, cleanup chính xác, manifest; phân biệt PASS và UNVERIFIED.

## Điều chỉnh brief của Leader

Brief ghi chung “invalid index422” quá rộng. API đã nghiệm thu phân biệt lỗi cấu trúc/duplicate422 và chỉ số không eligible403; `[999] -> 403` trong matrix đúng contract hiện hữu. Không yêu cầu Backend đổi hành vi để khớp câu viết tắt này.

Automation tiếp tục dự án vẫn bật; đã đọc trạng thái ở đầu lượt, lần scheduled05:26 trả NOTHING NEW và lần kế tiếp05:56 giờ Việt Nam. Callback rework sẽ nối tiếp; dự án chưa hoàn thành, production/lab còn UNVERIFIED.
