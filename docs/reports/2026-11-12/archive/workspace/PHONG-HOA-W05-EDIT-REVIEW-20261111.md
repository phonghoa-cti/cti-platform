# W05-EDIT — review độc lập của Leader

## Nghiệm thu sau rework — 03:45 ngày 11/11/2026

**ACCEPTED LOCAL CORE** tại `b9c35bb45cbf1000c1324ba46f1f162e0c02be44`.
Request sửa `4d56cb0a-9b86-451f-9f1d-5cd58d9eac77`; R1–R3 đã đóng.

- Leader đọc toàn bộ diff rework 2 file +201/-9: kiểm v1 riêng, so đủ key UNIQUE và kiểm NOT NULL của các cột audit selection bắt buộc. Không thấy thay đổi ngoài phạm vi.
- Chạy mới trên HEAD này: selection repo 30 ca + probe Leader nguyên trạng 10 ca = **40/40 passed, exit 0**, 1.71 giây. Bằng chứng `w05-selection-evidence/leader-rework-acceptance.log` và `.xml`. Không dùng con số 37 ở lần chạy trung gian của worker làm số kiểm cuối.
- Probe vẫn có SHA256 `0ad3b3d243a74b2a8fc751a7dbcca3a7aeb66952ae1a8824eee422332cf65f42`. Các ca từng lỗi đều đạt; v1 hợp lệ, v2 nhiều save, UNIQUE đúng có DESC, read-interleaving, migration terminal/rollback và corruption có bằng chứng phù hợp.
- Manifest worker **26/26 khớp**. JUnit nhóm selection/review/store/queue/CLI ghi **186 tests, 0 failures/errors/skips**; log ghi 186 passed trong 9.89 giây. Đây là bằng chứng worker đã kiểm, không phải Leader chạy lại cả nhóm. Full399 thuộc commit trước rework; không phải full suite tại b9c35bb.
- Tree selection sạch; tree tích hợp nguồn vẫn `d94afb1e24929f64f82a921cd29307be175fb04e`. Không sửa mã sản phẩm trong review, không push/PR/merge/deploy.

Phạm vi nghiệm thu: lõi SQLite chọn/bỏ chọn IOC, version/audit/policy và kiểm dữ liệu được giao. **Chưa nghiệm thu HTTP/UI cho selection**: parser hiện còn giới hạn version0/1 và chưa trả effective selection. OpenCTI/lab/production chưa kiểm. Việc kế là nghiên cứu hợp đồng API ở `PHONG-HOA-W05-SELECTION-API-NEXT-BRIEF.md`; dự án vẫn active, lịch dự phòng vẫn bật. Đã kiểm một lần các cuộc đang mở, không có Leader khác đang làm.

## Lịch sử review vòng đầu

Ngày 11/11/2026, 03:34 giờ Việt Nam. **REWORK REQUIRED** tại commit
`cf7120a429c08acd94ca20f9d0758cb8307ee288`, branch `feat/w05-selection-local-20261111`.
Request được review: `70252b3b-042a-45c2-9aea-4f8197d8b784`.

## Bằng chứng đã kiểm

- Đọc diff store/test và báo cáo; HEAD đúng, working tree sạch, phạm vi 6 file +864/-21.
- Manifest gồm 9 đầu ra khớp SHA256, gồm báo cáo. Khớp hash chỉ chứng minh file được nhận đúng; không tự chứng minh từng tiêu chí PASS.
- Chạy 14 test selection của repo cùng 10 ca Leader: **18 passed, 6 failed, exit 1** trong 0.82 giây.
  Log `w05-selection-evidence/leader-review.log`, JUnit `leader-review.xml`, probe `leader_selection_probe.py`.
- Bốn ca Leader đạt: getter nhìn snapshot cũ nhất quán dù writer commit giữa lần đọc draft và event (WAL, hook đồng bộ, không sleep); migrate v1 approved/rejected giữ snapshot lịch sử NULL và payload; lỗi commit v1→v2 rollback mọi ALTER, byte-identical DB.
- Báo cáo worker ghi targeted 104 nhưng log `02-green-targeted.log` chứa **103 dấu test đạt**, không có dòng tổng kết/exit. Log full có 399 dấu test đạt; đây là evidence worker, không phải Leader chạy lại full. Không cộng test của các lần khác nhau thành một suite.
- Không chạy lại full/UI/build/browser; không sửa mã sản phẩm, không mở listener, không dùng dữ liệu thật.

## R1 — Medium: làm yếu kiểm tra version của dữ liệu v1

`cti-w05-selection/extractor/phonghoa_extractor/store.py:668`, `:675`, `:679`.
Nhánh đọc v1 trả row 12 trường, nên bỏ qua kiểm tra selection version. Kiểm tra cũ pending=0 / terminal=1 đã bị bỏ/nới thành terminal>=1.
Probe chứng minh get/list chấp nhận pending version 3, get chấp nhận approved version 2 trong DB schema v1 hợp lệ. Đây là regression đối với chốt #7 của Leader, không phải version selection v2 hợp lệ.

Sửa: giữ invariant v1 rõ ràng; chỉ áp dụng version tăng theo selection cho v2. Test get/list pending sai và get terminal sai, cùng positive v1 pending0/terminal1 và v2 nhiều lần save.

## R2 — Medium: kiểm UNIQUE bỏ qua cột DESC, chấp nhận ràng buộc yếu hơn

`store.py:312`–`:318`, gọi tại `:463`/`:465`.
`_has_unique_index` bỏ toàn bộ cột có DESC=1 trước so sánh. Vì thế UNIQUE(draft_id, selection_version, actor_subject DESC) bị nhận là UNIQUE(draft_id, selection_version); tương tự review_version.
Probe dựng bảng cùng tên/cột/FK/CHECK nhưng dùng UNIQUE ba cột: `migrate_store` v2 vẫn trả thành công. Bảng này cho phép nhiều event cùng draft/version khi actor khác, nên không bảo đảm lịch sử mà code dựa vào.

Sửa: so đầy đủ các key column của unique index, không bỏ cột vì thứ tự DESC; vẫn từ chối partial/expression/extra key không tương đương. Có positive cho unique đúng hai cột (kể cả DESC nếu hỗ trợ tương đương), negative cho hai biến thể extra DESC của probe. Không tuyên bố đây là tấn công HTTP hoặc chống người sửa trực tiếp DB; đây là lỗi phát hiện schema không đúng contract.

## R3 — Medium: schema selection thiếu NOT NULL vẫn được nhận

`store.py:444`–`:471`.
Validator chỉ kiểm tên cột, vài CHECK/UNIQUE/FK; chưa kiểm NOT NULL của các cột bắt buộc trong bảng selection. Probe bỏ NOT NULL của actor_subject, các phần khác giữ nguyên: migration idempotent vẫn trả thành công. Contract audit yêu cầu actor bắt buộc nhưng database đã được chấp nhận không cưỡng chế điều đó.

Sửa: xác minh các ràng buộc NOT NULL bắt buộc của bảng selection (draft/version/action/time/actor/JSON/hash), không chỉ tên cột. Test thiếu từng nhóm ràng buộc với DB không bị thay đổi khi từ chối. Không chỉnh schema hỏng một cách im lặng.

## Bàn giao sửa có giới hạn

- CTI Backend, một implementer Sol medium, tiếp tục đúng tree `cti-w05-selection` từ cf7120a; không tạo implementation khác, không giao thêm bot/agent.
- Giữ toàn bộ phạm vi/cấm trong `PHONG-HOA-W05-EDIT-LEADER-PLAN.md`. Chỉ store, tests liên quan và tài liệu tiến độ/contract khi cần làm rõ. Không chạm API/UI/harness/dependency/tree nguồn.
- RED trước sửa: chạy probe Leader nguyên trạng, ghi log riêng của worker. Không sửa probe/log/XML/review của Leader. Thêm regression tương đương vào repo; đưa ca read-interleaving đồng bộ vào repo để không còn phụ thuộc probe bên ngoài.
- GREEN: probe Leader 10/10, selection và review/store/queue/CLI liên quan; ghi count từ summary/JUnit cùng exit code và lệnh/cwd. Ruff check/format, diff-check. Không cần lặp full399/UI/build/browser cho ba sửa validator này trừ khi phạm vi thay đổi hoặc phát sinh lỗi mới có lý do.
- Bổ sung kiểm có ý nghĩa cho các invariant selection mới mà suite cũ không kiểm: thiếu event/pointer lệch/hash sai và indices không eligible đều fail closed, không mutation. Dùng fixtures tổng hợp; không mở rộng tính năng.
- Chỉnh ma trận acceptance theo tên test/bằng chứng thật, sửa count targeted và phân biệt evidence cũ với kết quả mới. Cập nhật báo cáo worker, evidence/manifest mới trong `w05-selection-evidence/rework-r1-r3/`.
- Commit cục bộ, tree sạch; báo HEAD/diff/count/exit và giới hạn. Không push/PR/merge/deploy.

Chưa nghiệm thu core selection; HTTP/UI cho draft đã edit, OpenCTI/lab và production vẫn chưa xác minh. Dự án còn active; lịch tiếp tục dự phòng giữ bật.
