# Nghiên cứu lại cách điều phối Claude và áp dụng vào Phong Hỏa

Ngày kiểm: 10/11/2026. Yêu cầu: tự làm và giao tiếp việc trong phạm vi đã cho phép, không buộc người dùng nhắc sau mỗi mốc.

## Kết luận và nguyên nhân đã xác định

Có thể áp dụng cách quản lý mục tiêu, giao việc, nghiệm thu và tự nối việc. Không thể khẳng định đã sao chép cơ chế chặn kết thúc lượt của Claude sang OpenMausBot.

Lỗi hiện tại thuộc Leader: đã tự thu mục tiêu “tiếp tục dự án, lab để sau” thành đích gần nhất “tạo/lưu/đọc bản nháp”. Khi đích này đạt, Leader kết thúc mà không quay về backlog sản phẩm. Các câu liệt kê UI/auth/OpenCTI còn thiếu không thay cho việc chọn đầu việc tiếp theo. Báo cáo QA tự động là sự kiện để tiếp tục xử lý, không phải yêu cầu dừng dự án.

Bằng chứng tại Phong Hỏa:

- `PHONG-HOA-OFFLINE-CONTINUATION-PLAN.md` có đích gần nhất và ba bước, nhưng chưa có sổ tổng với mục tiêu mẹ vẫn mở sau khi các bước con đạt.
- Skill đã có quy tắc “đạt thì giao tiếp”, nhưng ví dụ và tài liệu nguồn còn tập trung vào bộ 16–17/10; không có kiểm tra được chạy trước khi kết thúc lượt.
- Lượt 23:08 đã chốt đúng bằng chứng kỹ thuật tại `e83bb3f`, nhưng không có nhiệm vụ kế tiếp được tiếp nhận. Danh sách thread kiểm 23:12: Engineer/QA/Research đều không có việc đang chạy; một thread Engineer cũ đã closed.

## Nguồn gốc đã đọc và kiểm

| Nguồn | Phiên bản quan sát | Điều rút ra |
|---|---|---|
| `E:\LMS_PILOT_INPUTS\G06-B01\VAN_HANH_CLAUDE\CLAUDE.md`, mục 7, 9 | Đọc trực tiếp | Trước kết thúc phải kiểm còn lời hứa chưa thực hiện; phiên mới đọc quy tắc và điểm tiếp tục. |
| `E:\LMS_PILOT_INPUTS\G06-B01\QUY_TAC_GOC.md` | Mtime 04/11 | Tách điều phối/người sửa/nghiệm thu; quyết định dựa vào Git và bằng chứng. Quyền deploy riêng của LMS không mang sang Phong Hỏa. |
| `$USER_HOME\.claude\skills\lms-orchestration\SKILL.md` | Mtime 10/11 13:47, đọc đủ 6 nguyên tắc và bước 1–7 | Đây là skill được bộ ổ E dẫn tới. Có sổ trạng thái, cô lập DB/cổng, kiểm sống/chết, tiếp tục cùng việc, kiểm toàn sản phẩm và chọn model theo chi phí. |
| `E:\LMS_PILOT_INPUTS\G06-B01\VAN_HANH_CLAUDE\RUNS.md` | Mtime 10/11 22:58 | Các hàng M143K→M143K2 chứng minh việc “báo xong” vẫn có thể bị từ chối; VIS-CLOCK/DASH-FIX accepted và UI chờ duyệt được ghi riêng. Đây là nhật ký, không phải Leader chạy lại test LMS. |
| `E:\LMS_PILOT_INPUTS\G06-B01\KE_HOACH_KIEM_THU_TONG.md` | Mtime 09/11 22:36 | Danh sách rủi ro còn mở quyết định việc tiếp; chỉ lab/người thật bị chặn thì vẫn làm các phần độc lập. |
| `E:\LMS_PILOT_INPUTS\G06-B01\RESUME_NEXT_SESSION.md` | Mtime 10/11 22:38 | Đọc mục đầu, các mục liên quan và phần cuối. File resume có thể chậm hơn RUNS; phải đối chiếu ref/bằng chứng, không tin tên “mới nhất”. Không đọc toàn bộ lịch sử không liên quan. |
| `E:\LMS_PILOT_INPUTS\G06-B01\VAN_HANH_CLAUDE\tools\stop_gate.py` | SHA256 `30c75c03263f56ba6b76b033c5e9ab5ee1fa20f0a98d72e1f72172905c0209ff` | Script chặn khi có queued nhưng không running/verifying. Đã đọc toàn mã và kiểm cấu hình chỉ phần Stop: có 2 command hook, có đăng ký stop_gate.py. Chưa chạy lại toàn harness Claude. |
| `...\VAN_HANH_CLAUDE\memory_C\feedback_enforce_not_just_note.md` | Bài học 22/10 | Ghi nhớ thụ động từng thất bại; cần phép kiểm cụ thể và nơi ứng dụng thực thi nó. |

SHA256 skill lms-orchestration: `79d99a0ecd301b8d6df952d928c99eca5dc45ab7240d6a4751f075cef207ed53`.

Có sửa đổi mâu thuẫn ngay trong skill: bước 3 còn quy tắc Astra xhigh, nhưng bước 5c ngày 09–10/11 đã sửa thành chọn theo loại việc/quota và bớt chạy lại test. Phong Hỏa giữ Astra điều phối, Sol medium triển khai, Terra nghiên cứu theo yêu cầu hiện hành; không sao chép model/cron/lệnh resume --last của LMS.

## Đối chiếu nguồn chính thức

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents), 26/11/2025: nêu lỗi agent thấy một số tính năng đã có rồi tuyên bố xong. Giải pháp dùng danh sách tính năng và bản bàn giao trạng thái giữa các lượt. Phù hợp với lỗi thu nhỏ mục tiêu của Leader.
- [Anthropic: Harness design for long-running application development](https://www.anthropic.com/research/harness-design-long-running-apps), 24/03/2026: tách lập kế hoạch, làm và đánh giá; bàn giao có cấu trúc. Không có cơ sở dùng model tự chấm làm chứng cứ duy nhất.
- [Claude Code: Stop hooks](https://code.claude.com/docs/en/hooks#stop): ứng dụng có thể nhận quyết định block và tiếp tục lượt; có bảo vệ tránh vòng lặp. File Python riêng không tự có tác dụng nếu không được ứng dụng gọi.

## Khả năng tái sử dụng và giới hạn

1. **Dùng ngay:** mục tiêu mẹ và tiêu chí sản phẩm tách khỏi task; sổ trạng thái; ghi thread/request/ref; đọc bằng chứng đúng SHA; chọn việc kế trước kết thúc lượt; chặn một nhánh không chặn toàn bộ.
2. **Thay bằng cơ chế sẵn có:** OpenMausBot đã tự trả kết quả đồng đội và gọi Leader tiếp tục. Dùng xác nhận giao việc làm bằng chứng `dispatched`; không nói `running` khi mới xếp hàng. Không thêm cron/poll để đợi bot.
3. **Không sao chép:** kết nối trình duyệt/daemon LMS, Telegram, tài khoản/quota, lệnh deploy, quyền lịch sử, thay model hàng loạt, khởi chạy công cụ khác thay đồng đội hiện có.
4. **Cần kiểm chứng riêng:** công cụ hiện có chưa cung cấp cấu hình Stop hook tương đương cho OpenMausBot. Bộ kiểm tra cục bộ sẽ là bước Leader phải chạy theo quy trình, không được mô tả là ứng dụng tự chặn kết thúc. Không sửa chương trình OpenMausBot hoặc cấu hình Claude để lách giới hạn.

Script Claude cũng có giới hạn thấy ngay từ mã: hàng chờ rỗng nhưng mục tiêu chưa đạt sẽ không bị chặn; lỗi đọc file được cho qua; regex Markdown không kiểm phụ thuộc. Vì vậy không bê nguyên script. Dùng JSON có mục tiêu đang mở và trạng thái rõ; thiếu việc tiếp thì yêu cầu lập kế hoạch, không kết luận xong.

## Quyết định áp dụng

Chọn giải pháp nhỏ: **sổ tổng JSON + quy tắc trong working agreement + bộ kiểm tra chỉ đọc + callback đồng đội hiện có**. Không cài một hệ điều phối mới, không chạy vòng lặp vô hạn, không thêm bot.

- `PHONG-HOA-RUNS.json`: mục tiêu dự án, tiêu chí chưa đạt, nhiệm vụ, phụ thuộc, bằng chứng, lý do chặn và xác nhận giao việc. Leader là người duy nhất cập nhật.
- `PHONG-HOA-WORKING-AGREEMENT.md`, mục 11: chu trình quyết định và điều kiện nhường lượt/kết thúc.
- Engineer: viết và kiểm bộ kiểm tra sổ; có ca tái hiện đúng lỗi “task con đạt, mục tiêu mẹ còn mở, hàng chờ rỗng”.
- Research: xác định lát cắt tiếp của W05 sau nền SQLite, so giải pháp sẵn có trước khi chốt brief triển khai. Không chờ lab hoặc UI để nghiên cứu lõi duyệt/audit.

Sau khi hai việc trả về, Leader kiểm bộ kiểm tra; chọn phương án từ nghiên cứu; giao Engineer triển khai phần đã đủ tiêu chí. Nếu một kết quả về trước, xử lý phần đó, không dựng hàng chờ mới trùng nhiệm vụ đang làm.

## Thế nào mới chứng minh thay đổi có tác dụng

Chưa chỉ dựa vào tài liệu này để nói “đã giải quyết hoàn toàn”. Cần: bộ kiểm tra qua các ca âm tính; receipt giao việc thật; callback về được nghiệm thu; sau mốc đạt phải có nhiệm vụ kế được tiếp nhận hoặc lý do dừng thuộc người dùng. Chỉ hoàn tất dự án khi tiêu chí cấp dự án có bằng chứng, không lấy số test làm phần trăm tiến độ.

## Bổ sung sau yêu cầu lúc 23:22

Người dùng chỉ rõ việc phải canh Leader vẫn chưa được giải quyết bằng quy tắc và script kiểm tra. Vì vậy đã bổ sung lịch thực hiện công việc dự phòng mỗi 30 phút và khi OpenMausBot khởi động, ID `79621896-f322-47a8-80d7-072739a2314b`. Khi Leader không đang làm và mục tiêu còn mở, lịch phải nghiệm thu/lập brief/giao tiếp việc theo sổ; nếu công việc đang có người xử lý thì bỏ qua, không tạo bản sao. Chi tiết: `PHONG-HOA-AUTONOMOUS-CONTINUATION.md`. Callback vẫn nối ngay sau kết quả. Đây là cơ chế khôi phục sau khi bỏ dở, không là Stop hook; cần bằng chứng lần chạy tự động đầu tiên trước khi kết luận vận hành đã được kiểm.
