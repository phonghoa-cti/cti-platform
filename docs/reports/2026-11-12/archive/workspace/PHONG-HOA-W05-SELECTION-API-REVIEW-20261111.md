# W05 Selection API — nghiệm thu Leader

Ngày 11/11/2026. **ACCEPTED LOCAL API**, request `8a1bba17-6309-4cc8-9c90-c348aca5f2e9`.

- Base `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`; HEAD `812dae1ffbdc8e8866342cc075d925fdc99ef12d`, branch `feat/w05-selection-api-20261111`, tree `cti-w05-selection-api`.
- Đối chiếu với `PHONG-HOA-W05-SELECTION-API-LEADER-PLAN.md`: 10 file, +1009/-19, đúng scope; đã đọc toàn diff code/test mới và contract/ADR. Tree bàn giao và tree nguồn sạch; nguồn vẫn b9c35bb. Không có finding cần rework trong phạm vi đã kiểm.
- Bốn thao tác v1 tái sử dụng Principal/quyền/Origin hiện có; read detail dùng một transaction, mutation trả selection của lần commit; wrapper legacy giữ sáu trường. Safe integer, version cap trước ghi, body stream limit, mapping missing-DB/row và policy khớp quyết định Leader.

## Kiểm chứng độc lập

Từ `cti-w05-selection-api`, dùng interpreter đã có tại `cti-w05-backend/.venv/Scripts/python.exe`. Interpreter của `cti-platform-start` thiếu FastAPI; lượt kiểm import đầu exit 1, không cài hoặc sửa môi trường đó. Đã chuyển sang môi trường API có sẵn trước chạy kiểm sản phẩm.

Lệnh dưới chạy nhóm API/core liên quan cùng probe của Leader; không chạy lại full suite:

```powershell
..\cti-w05-backend\.venv\Scripts\python.exe -X utf8 -B -m pytest -c pytest.ini -p no:cacheprovider -o addopts= -q ..\w05-selection-api-evidence\leader_api_probe.py portal_api\tests\test_w05_api.py extractor\tests\test_selection.py -k 'leader_ or v1_ or combined_detail or v2_list or decision_with_selection or public_version_cap or missing_database_has' --junitxml=..\w05-selection-api-evidence\leader-review.xml
```

Kết quả mới: **56 passed, 113 deselected, 3.10s, exit 0**. Có 19 ca probe Leader bổ sung, kiểm role thật trên cả bốn thao tác; creator lưu được nhưng không tự approve; kiểu expected_version ở decision; decision body quá giới hạn không ghi; cap/no-op qua HTTP; số quá lớn trong các trường lồng; audit event thiếu bị từ chối khi detail/save/decision và DB không đổi. Nhóm repo còn kiểm snapshot xen writer có kiểm soát, response/legacy, strict validation và header/error. Các probe chỉ dùng DB/JWT tổng hợp, không listener hoặc mạng.

`git diff --check` mới: exit 0. Không sửa code sản phẩm khi review, không lặp lint/build/browser vì chưa có thay đổi mới sau kết quả worker.

## Bằng chứng worker đã đối chiếu

- JUnit `targeted-final-postformat.xml`: 150 tests, 0 failures/errors/skipped.
- JUnit `full-python-final-postformat.xml`: 447 tests, 0 failures/errors/skipped. Đây là suite do Backend chạy; Leader xác minh artifact, không nhận là đã tự chạy lại 447 ca.
- Manifest `manifest.sha256`: **5/5** file khớp SHA256. File Leader thêm sau đó không thuộc manifest worker, không sửa manifest gốc.
- Đã đọc demo summary: changed/no-op/stale, empty approve, reject/approve cùng snapshot audit, payload byte-identical và items.keep không đổi. Không chạy lại demo riêng vì nhóm kiểm mới đã bao phủ rủi ro cần nghiệm thu.
- Báo cáo worker SHA256 `F573CF6527D48B72A2750151B731F392B5EC2C2D79C652D8F9AA4E3EDEB2336A`.
- Probe Leader `w05-selection-api-evidence/leader_api_probe.py` SHA256 `DCBD8BE5CF558273A0DEFAA41E8778767415560A713E81E944848FA679ABD6E8`; log `leader-review.log`, JUnit `leader-review.xml` cùng thư mục.

## Giới hạn và bước nối

Nghiệm thu API in-process tại đúng SHA; không khẳng định kiểm hết mọi đầu vào hoặc có bảo đảm production. UI vẫn gọi `/api/drafts`, parser khóa version cũ và checkbox API còn disabled; API v1 chưa đồng nghĩa người dùng đã sửa lựa chọn qua giao diện. Gateway v1, browser/UI, Cloudflare/JWKS thật, lab, OpenCTI và production **UNVERIFIED**.

Đã xem một lần các cuộc đang mở: không có Leader khác hoạt động; thread Backend đã idle và báo cáo đã về. Lịch tiếp tục vẫn enabled mỗi 30 phút; lượt gần nhất 03:56 giờ Việt Nam trả NOTHING NEW. Không xem lịch/guard là bằng chứng phục hồi bỏ dở đã được kiểm.

Bước kế: nghiên cứu và brief nhỏ cho UI lựa chọn trên thiết kế có sẵn, dùng contract tại 812dae1. Mục tiêu dự án vẫn active; không push/PR/merge/deploy.
