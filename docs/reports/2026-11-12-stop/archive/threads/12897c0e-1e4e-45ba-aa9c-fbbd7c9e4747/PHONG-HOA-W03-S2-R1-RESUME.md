# W03-S2 — nối vòng sửa R1

Ngày 12/11/2026, Leader kiểm một lần danh sách cuộc việc: Backend ec2f0709-b0f2-46ed-823d-9a461e1f1912 idle, không thấy Leader khác đang xử lý. Git hiện tại 82f8a6acc8f357645f7105a2cc84b46bf58f4e4f, status sạch. Báo cáo R1 ở đường dẫn đã giao chưa có; chưa có bằng chứng request 2d59493c-6708-4048-8113-39b731357f72 thực hiện sửa. Không suy ra worker đã chạy hay hoàn thành từ receipt queued.

## Mục tiêu và lựa chọn

Hoàn tất đúng sửa lỗi R1 tại ranh giới giải mã cursor (mã giữ vị trí phân trang), để dữ liệu đầu vào không hợp lệ trả 422 trước khi đọc dữ liệu. Tái sử dụng nghiên cứu/hợp đồng S2 đã được Leader chốt ngày 12/11; không chọn lại kiến trúc. Sửa validator cục bộ được chọn vì giữ nguyên lỗi 503 của nguồn dữ liệu và hợp đồng API đã giao. Không đổi generic exception handler để che lỗi đầu vào.

## Đầu vào bắt buộc

- Tree duy nhất được sửa: $WORKSPACE\cti-w03-status-s2-backend.
- Branch feat/w03-status-s2-backend-20261112; HEAD quan sát nêu trên. Đọc AGENTS.md và tài liệu trên branch này. Giữ mọi thay đổi có trước, không reset.
- Review gốc: $THREADS\9ab7082c-db6a-43f8-a0f5-41f731c1fac0\PHONG-HOA-W03-S2-REVIEW-R1.md.
- Probe Leader: cùng thư mục review, probe_w03_s2_cursor.py. Đọc cách nhận tham số trước khi chạy; giữ nguyên bằng chứng cũ.
- Hợp đồng: $THREADS\c10d07c4-917a-4f70-bd33-56abccf3066d\PHONG-HOA-W03-S2-DECISION-AND-BACKEND-BRIEF.md và docs/specs/W03-status-view-local-contract.md trong tree.

## Thực hiện và kiểm

Một CTI Backend dùng Sol medium trực tiếp, không giao worker lồng. Đây là lần nối đầu tiên của vòng sửa chức năng R1 chưa có kết quả, không lặp hai lần phục hồi triển khai đã kết thúc ở 82f8a6ac.

1. Thêm ca hồi quy trước sửa: context.view=[], kev={}, status=[], kev=1, ngày không tồn tại 2026-99-99, kev=NaN, q chứa U+D800. Bảy ca phải 422 invalid_cve_status_query trước dependency, no-store/Vary và DB không đổi; control hợp lệ vẫn 200. Lưu RED đúng assertion, rồi sửa để GREEN.
2. Kiểm riêng dataset-only, technology-only, status-only và UTC-date-only thay đổi với fixture mới hoặc khôi phục baseline, để từng trường hợp tự chứng minh 409. Không dùng trạng thái bẩn từ ca trước.
3. Chỉ sửa portal_api/cves_status_view.py, portal_api/tests/test_cves_status_view_api.py, docs/PROGRESS.md; chỉ làm rõ contract nếu cần cho validation đã chốt. Giữ W03-R/S1, route, UI, gateway, dependency và fixture có schema không đổi.
4. Chạy nhóm S2 + W03-R + S1, probe Leader ghi output mới, Ruff/format và git diff --check trên delta commit. Dùng môi trường Python có sẵn đã chạy thành công ở tree cti-w03-read-backend nếu tree này chưa có .venv; không dùng Python PATH. Không cần lặp full suite có bốn lỗi STIX thiếu validator đã ghi nhận. Không cài dependency.
5. Commit cục bộ, báo SHA, diff, tree status, lệnh/exit/test count, raw evidence và giới hạn. Nếu môi trường gây lỗi cùng nguyên nhân hai lần thì dừng cách đó, trả nguyên nhân và phần đã làm. Không thay quota/model hoặc sửa RUNS.

Không push/PR/merge/deploy/live feed/cloud LLM/lab/secret. Không đụng gateway cũ hoặc thư mục dữ liệu thử đã bị từ chối xóa trong review gốc. Frontend chưa được mở phụ thuộc.

## Bàn giao

Ghi báo cáo mới ở $THREADS\12897c0e-1e4e-45ba-aa9c-fbbd7c9e4747\PHONG-HOA-W03-S2-BACKEND-R1-RESULT.md; raw evidence trong w03-s2-r1-evidence cùng thư mục. Không ghi đè report/log cũ. Kết quả trả về Leader để review phần mới; chưa tuyên bố toàn W03 hoặc dự án hoàn thành.
