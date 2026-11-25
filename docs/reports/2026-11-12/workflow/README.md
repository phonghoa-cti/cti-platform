# Workflow continuation guard

`check_continuation.py` là cổng quy trình **chỉ đọc** để Leader kiểm sổ công việc trước khi nhường hoặc kết thúc một lượt. Công cụ không sửa sổ, không gửi việc, không đổi trạng thái và không thực thi bất kỳ nội dung nào trong JSON.

Đây **không phải Stop hook của OpenMausBot** và không tự cưỡng chế engine tiếp tục. Leader phải chủ động gọi lệnh và xử lý quyết định trả về.

## Cách chạy

Từ workspace Phong Hỏa:

```powershell
cti-platform-start\.venv\Scripts\python.exe workflow\check_continuation.py --ledger PHONG-HOA-RUNS.json
```

Stdout luôn là một JSON UTF-8 có ba trường:

```json
{"decision":"PLAN_NEXT","task_ids":[],"reasons":["..."]}
```

| Decision | Exit | Ý nghĩa |
|---|---:|---|
| `INVALID` | 2 | File/schema/ID/phụ thuộc/trạng thái hoặc bằng chứng bắt buộc không hợp lệ. |
| `PAUSED` | 0 | Người dùng đã tạm dừng và sổ có lý do. Không đề nghị giao mới. |
| `COMPLETE` | 0 | Dự án ghi complete, mọi tiêu chí verified có evidence và mọi task accepted. |
| `REVIEW` | 1 | Có task reported cần nghiệm thu. |
| `REPLAN` | 1 | Có task failed/stalled cần chẩn đoán và lập lại kế hoạch. |
| `DISPATCH` | 1 | Có task queued đủ phụ thuộc và owner không bận; tối đa một task cho mỗi owner. |
| `YIELD` | 0 | Sổ ghi có task dispatched/running cùng receipt hợp lệ. Đây không phải kiểm tra sống trực tiếp. |
| `BLOCKED` | 0 | Mọi task chưa accepted đều blocked với lý do, owner và điều kiện mở lại. |
| `PLAN_NEXT` | 1 | Mục tiêu mẹ còn active nhưng không có việc có thể giao/đang chạy; cần đối chiếu backlog và chuẩn bị việc kế. |

Exit `1` nghĩa là Leader còn hành động quy trình phải làm trước khi nhường lượt; không phải lỗi chạy chương trình. Exit `2` là dữ liệu đầu vào không an toàn để ra quyết định.

## Quy tắc chính

- Xác thực toàn bộ schema và đồ thị phụ thuộc trước khi ra quyết định.
- `receipt.outcome=accepted` chỉ xác nhận giao việc; không biến task thành `accepted`.
- Mọi trường enum phải là chuỗi thuộc tập cho phép; list/dict/null/bool/number đều là `INVALID`, không được làm CLI traceback.
- `running` cần receipt và `observation` có nguồn, thời điểm cùng `status` đúng bằng `running`. `idle`, `completed`, `failed`, `queued`, trạng thái lạ hoặc sai kiểu đều là `INVALID` để Leader đối chiếu lại công việc thật.
- Task `accepted` cần evidence. Task `blocked` cần `reason`, `owner` và `unblock_condition`.
- Với `DISPATCH`, task được sắp theo priority giảm dần và chỉ chọn tối đa một task cho mỗi owner.
- Task độc lập vẫn có thể được chọn khi một task lab/UI khác đang blocked.
- Khi dự án còn `active`, danh sách task rỗng hoặc toàn task con đã accepted vẫn trả `PLAN_NEXT`, tuyệt đối không suy diễn thành `COMPLETE`.
- `accepted_results` chỉ phục vụ chống xử lý lại báo cáo cũ; không tự tạo hoặc đổi trạng thái task.

## Kiểm thử

```powershell
cti-platform-start\.venv\Scripts\python.exe -m unittest workflow.test_check_continuation -v
cti-platform-start\.venv\Scripts\python.exe -m ruff check workflow\check_continuation.py workflow\test_check_continuation.py
cti-platform-start\.venv\Scripts\python.exe -m ruff format --check workflow\check_continuation.py workflow\test_check_continuation.py
```

Test dùng file tạm, không ghi `PHONG-HOA-RUNS.json`. Demo với sổ thật phải so SHA256 trước và sau để chứng minh lượt chạy không sửa file.

## Giới hạn

- Công cụ chỉ biết dữ liệu đã ghi trong sổ; không chứng minh worker thật sự còn sống, callback chắc chắn sẽ về hay bằng chứng nghiệp vụ là đúng.
- `observation.status=running` là quy ước dữ liệu tối thiểu, không phải phép kiểm tra live; nguồn observation vẫn do Leader chịu trách nhiệm ghi và kiểm chứng.
- Công cụ không thay review của Leader, không tự đọc backlog ngoài sổ và không tự lập brief.
- `BLOCKED`, `YIELD`, `PAUSED` có exit `0` vì có thể nhường lượt đúng quy trình; chúng không đồng nghĩa dự án hoàn tất.
- Chỉ `COMPLETE` mới biểu thị mục tiêu đã hoàn tất theo dữ liệu hợp lệ trong sổ, và dữ liệu đó vẫn cần Leader chịu trách nhiệm cập nhật/nghiệm thu.
