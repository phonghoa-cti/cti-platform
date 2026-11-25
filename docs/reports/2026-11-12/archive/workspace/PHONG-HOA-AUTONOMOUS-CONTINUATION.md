# Phong Hỏa: tự nối việc và khôi phục khi bỏ dở

Ngày 10/11/2026. Người dùng yêu cầu tìm cách làm việc liên tục như Claude trên ổ E, không phải canh nhắc. Bản này bổ sung cơ chế gọi Leader trở lại cho nghiên cứu và quy trình đã có; không thay phạm vi sản phẩm.

## Hai đường tiếp tục

1. **Đường chính:** đồng đội trả kết quả thì Leader được gọi lại ngay trong cuộc đã giao. Leader kiểm chứng, cập nhật sổ tổng và giao bước kế; không chờ lịch định kỳ.
2. **Đường dự phòng:** lịch `Phong Hỏa — tự tiếp tục việc còn mở`, ID `79621896-f322-47a8-80d7-072739a2314b`, gọi Leader mỗi 30 phút và khi OpenMausBot khởi động. Mỗi lượt dùng model/máy hiện tại của Leader, giới hạn 15 phút, bỏ qua lượt định kỳ chồng nhau, mang báo cáo trước sang lượt kế. Mục đích là làm tiếp công việc bị bỏ dở, không chỉ nhắc người dùng.

Lịch được tạo thành công bằng chức năng có sẵn của OpenMausBot. Đọc lại cấu hình là bằng chứng đã bật; chưa phải bằng chứng một chu kỳ tự động đã thực hiện được công việc. Lịch không cưỡng chế chặn kết thúc lượt như Stop hook của Claude.

## Tránh giao trùng và sửa đè

- Trước mỗi lần phục hồi, xem một lần các cuộc làm việc đang mở. Nếu Leader đang làm Phong Hỏa ở cuộc khác, kết thúc lượt dự phòng, không sửa sổ và không giao thêm.
- Đối chiếu task ID, receipt request/thread và trạng thái thực tế. Đang được tiếp nhận/đang làm thì giữ nguyên, chờ đường trả kết quả sẵn có; không tạo bản sao worker.
- Nếu mọi việc làm được đang có người làm thì kết thúc lượt dự phòng không báo cáo lặp. Không gọi hỏi trạng thái từng bot, không đợi trong lệnh và không tạo lịch phụ để chờ kết quả.
- Nếu ghi dispatched/running nhưng thread đã idle/failed, đọc báo cáo và bằng chứng để xác định đã xong hay gặp lỗi. Không chờ vô hạn dựa vào sổ cũ.
- Leader là vai trò duy nhất sửa `PHONG-HOA-RUNS.json`. Tính năng bỏ qua chồng lịch chỉ bảo vệ các lượt của chính lịch; kiểm các cuộc Leader khác vẫn cần thực hiện. Hiện chưa có khóa giao dịch xuyên mọi cuộc trò chuyện, nên không tuyên bố chống mọi cuộc đua.

## Việc phải làm khi không có ai đang xử lý

Đọc working agreement mục 11, sổ tổng, brief và bằng chứng liên quan. Sau khi bộ kiểm tra được nghiệm thu, dùng nó để đối chiếu quyết định. Nếu chưa nghiệm thu, đọc bằng tay; không chạy mã đang được Engineer sửa.

- Có kết quả mới: nghiệm thu đúng SHA/phạm vi, ghi evidence; không lặp lại accepted_results.
- Cần sửa: brief cụ thể vào đúng cuộc của người đã làm; tối đa hai lần thử lại cùng lỗi, rồi đổi cách xử lý.
- Có việc đủ điều kiện: giao thật, lưu request/thread đã được tiếp nhận rồi nhường lượt.
- Mục tiêu còn active nhưng hàng chờ rỗng: đọc spec/backlog, chọn việc nhỏ hữu ích, dùng nghiên cứu đã có hoặc giao nghiên cứu còn thiếu. Đây là PLAN_NEXT, không phải COMPLETE.
- Chỉ một phần chờ lab/UI: tiếp tục các phần độc lập. Nếu tất cả còn lại bị chặn, ghi lý do/người giải/điều kiện mở, chỉ báo khi có thay đổi.

Không mở rộng quyền push/PR/merge/deploy, cloud/LLM thật, lab, mua dịch vụ hay truy cập dữ liệu. Người dùng đã giao Codex làm UI thay Antigravity ngày 10/11/2026. Dùng CTI Frontend, Backend, AI Agent và Engineer theo `PHONG-HOA-PARALLEL-PLAN.md`; một người Sol medium trên một working tree riêng.

## Dừng và bằng chứng vận hành

Khi người dùng yêu cầu tạm dừng, tạm ngưng lịch này và đọc lại trạng thái. Khi toàn bộ mục tiêu có bằng chứng đạt, tạm ngưng lịch này rồi xác nhận enabled=false và nextRunAt=null. Giữ nguyên các lịch khác. Không coi xong một task là hoàn thành mục tiêu.

Sau lần tự tiếp tục đầu tiên, ghi thời điểm, quyết định và receipt/bằng chứng vào sổ. Chỉ từ đó mới có bằng chứng vận hành thực tế. Không chỉnh trạng thái thử nghiệm thành đạt chỉ vì lịch đã bật.

Nguồn: `PHONG-HOA-ORCHESTRATION-RESEARCH-20261110.md`; cấu hình lịch được tạo và đọc lại ngày 10/11/2026. Bộ kiểm tra và nghiên cứu W05 đang được giao từ trước, không giao lại bởi bản bổ sung này.

## Kiểm lại ngày 11/11/2026

Leader đã nghiệm thu guard R1/R2: 32/32 unittest, exit 0; từ nay dùng guard trên sổ thật. Lịch giữ ID/chu kỳ 30 phút/startup/overlap=skip; nội dung đã cập nhật theo guard đã nghiệm thu và đọc lại trạng thái enabled=true, nextRunAt=2026-11-10T17:26:14.862Z (00:26:14 ngày 11/11 giờ Việt Nam). Không tạo lịch trùng.

Lượt scheduled 23:56:14 ngày 10/11 hoàn tất với NOTHING NEW; lượt manual 23:27 cũng vậy. Chỉ xác nhận lịch đã gọi Leader, chưa đủ xác nhận phục hồi công việc bỏ dở hoặc tránh trùng đúng mọi trường hợp. Bằng chứng nghiệm thu/nối việc thực tế: PHONG-HOA-LEADER-ACCEPTANCE-20261111.md và receipt mới trong PHONG-HOA-RUNS.json. Dự án vẫn active; giữ lịch.
