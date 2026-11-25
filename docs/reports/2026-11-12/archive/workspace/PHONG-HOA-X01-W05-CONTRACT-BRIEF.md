# X01-W05-CONTRACT — Bước 3, hợp đồng và mẫu tích hợp

Ngày 10/11/2026. Owner: CTI Engineer, Sol medium. Một người sửa checkout, không giao việc tiếp.

## Đích và hiện trạng

Người phát triển W05 có một tài liệu xác định chính xác dữ liệu bản nháp hiện có, mẫu đọc lại thật,
và các việc còn thiếu để nối màn duyệt; không phải đoán từ ví dụ API chưa đầy đủ.

Checkout tuyệt đối:
`$WORKSPACE\cti-platform-start`.
Base đã nghiệm thu `165c6ca8abd2555348ad323e616dc6cf10b6f199`; tạo nhánh
`docs/x01-w05-contract-20261110` sau khi kiểm sạch, giữ nhánh store.
Leader vừa chạy 42 test store/CLI đạt; đọc log 157 test toàn suite đạt, Python 3.12.13.

Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/W05-duyet.md, docs/specs/api-portal.md,
docs/specs/X01-ai-extractor.md, docs/design/DESIGN.md và các module drafts/store/evidence.
Kế hoạch quyền/phạm vi: PHONG-HOA-OFFLINE-CONTINUATION-PLAN.md ở thư mục cha checkout.

## Nghiên cứu đã có và lựa chọn của Leader

- Leader đối chiếu GitHub ngày 10/11/2026: vẫn 2 PR mở,
  [#1](https://github.com/phonghoa-cti/cti-platform/pull/1) head `8d9d7df54e90a1811b58a713cfe7ec56072ed0a7`,
  [#46](https://github.com/phonghoa-cti/cti-platform/pull/46) head `36259c118f519d3ac9cfc1f7b79e7180c2448a88`.
  Local HEAD kế thừa baseline; không quay về main, không merge PR.
- portal hiện chỉ có .gitkeep. api-portal mô tả dự kiến, chưa phải endpoint đang chạy.
- Giữ schema offline 1.0 và bổ sung đặc tả cầu nối để bảo toàn evidence/hash/findings/status;
  không ép dữ liệu về ví dụ API rút gọn rồi làm mất trường. Không thêm một định dạng lưu trữ thứ hai.
- [Python 3.12 str](https://docs.python.org/3.12/library/stdtypes.html#text-sequence-type-str): chỉ số theo Unicode code point.
- [ECMAScript String iterator](https://tc39.es/ecma262/multipage/text-processing.html#sec-string.prototype-%symbol.iterator%):
  iterator đi theo code point; slice trực tiếp dùng chỉ số chuỗi UTF-16. Leader đã đọc nguồn ngày 10/11/2026.
  Giữ span [start,end) trên text đã lưu; hướng dẫn Array.from(text).slice(start,end).join('') cho lấy quote,
  hoặc đổi sang offset UTF-16 khi API hiển thị cần. Không normalize/refang/trim text trước khi lấy span.
- Dùng lại quy tắc W05: chỉ Analyst/Admin, text chỉ hiển thị dạng text, mọi quyết định cần con người.
  Không biến header email từ client thành chứng minh xác thực; phần HTTP phải xác minh danh tính ở bước riêng.

## Phạm vi chỉnh sửa

Chỉ tài liệu và mẫu tổng hợp: thêm `docs/specs/W05-draft-offline-contract.md`,
`docs/design/W05-draft-handoff.md`, `extractor/draft/examples/` (tối đa ba JSON và README);
sửa phần drafts của `docs/specs/api-portal.md` để liên kết phụ lục, README draft và PROGRESS.
Không sửa code chạy/test hiện có, không dependency; nếu thấy lỗi code, báo tái hiện cụ thể trước.
Mọi sửa API doc là đề xuất trên nhánh local chờ review, không công bố API đã tồn tại.

## Nội dung bắt buộc

1. Bảng từng trường ở draft tạo mới và draft đã lưu: kiểu, nullable, ý nghĩa, ai tạo;
   source.name/sha256, id/created_at, schema_version/status, language/TLP/text,
   items (kind/type/value/span/evidence/keep/warning/status), findings, injection_warning, model/cost_tokens.
   Source hash là SHA-256 của text UTF-8 thực sự lưu, không hứa là hash byte file gốc.
2. Phân biệt rõ trạng thái thực tế và tương lai: hiện chỉ pending + IOC; item.status khác draft.status;
   keep là gợi ý chọn, không phải con người đã duyệt. Null span không có liên kết tô sáng.
   Không suy ra có TTP/malware/actor từ ví dụ API. Không hứa store đang chặn mọi giá trị kind/status lạ;
   ghi việc cần siết schema tại biên API trước khi tích hợp và tiêu chí từ chối loại chưa hỗ trợ.
3. Ba mẫu hợp đồng: bản nháp thường, cảnh báo/allowlist/rejected, rỗng. Mẫu phải dùng dữ liệu tổng hợp
   và được save/get bằng implementation hiện tại. Nếu phải thêm item rejected thủ công để phủ tình huống,
   ghi đúng đó là fixture dựng để kiểm hợp đồng, không phải kết quả tự trích. Không bịa span.
4. Quy ước Unicode với ví dụ có emoji trước IOC và dấu tiếng Việt; chỉ số code point không phải byte
   hay ký tự hiển thị tổ hợp. Thử ví dụ Python và JavaScript nếu có Node sẵn; nếu thiếu Node chỉ nêu chưa chạy JS,
   không cài phần mềm. Ghi kết quả ở bằng chứng, không triển khai giao diện hoặc helper frontend.
5. Handoff Antigravity: người dùng/luồng xem nguồn→xem mục→hiểu cảnh báo; tham chiếu DESIGN.md;
   trạng thái rỗng/lỗi/không đủ quyền/pending/không có span; tiêu chí render text an toàn.
   Tài liệu này là gói sẵn bàn giao, chưa gửi hay thực thi vì chưa có Antigravity trong roster.
6. Ma trận khoảng trống: liệt kê/lọc/paging, đọc chi tiết HTTP, xác thực/quyền, lịch sử sửa/duyệt/từ chối,
   người đề xuất/người duyệt, đo sửa đổi, OpenCTI. Không tự đặt endpoint đang chạy, không mở auth,
   không phê duyệt mẫu. TLP/injection_warning không là phép gửi cloud hoặc bằng chứng dữ liệu an toàn.

## Kiểm chứng và bàn giao

- Không cần thêm test cho văn bản. Kiểm JSON parse, schema và roundtrip ba mẫu bằng save/get thật;
  không sửa DB cũ. DB/log thử trong `x01-w05-contract-evidence/` ở thư mục cha, không commit DB.
- Đối chiếu bảng trường với mẫu và source thực; kiểm liên kết/tên file, ví dụ Unicode, git diff --check.
  Không lặp toàn suite cho thay đổi chỉ docs/fixtures; báo suite 157 test là bằng chứng base.
- Commit local sạch; trả SHA, diff, lệnh/exit, điểm đã kiểm và chưa kiểm. Cập nhật PROGRESS đúng trạng thái.
- Báo cáo ngoài repo: `PHONG-HOA-X01-W05-CONTRACT-RESULT.md`; log trong thư mục evidence nêu trên.
- Không push/PR/merge/deploy, mở HTTP, sửa UI, cloud, OpenCTI, lab; không gọi worker khác.
  Tối đa hai lần thử cùng một blocker rồi báo rõ.

Leader nghiệm thu xong sẽ chọn phần triển khai tiếp còn độc lập với lab dựa trên ma trận khoảng trống,
không lấy việc hoàn thành tài liệu làm bằng chứng W05 hoặc toàn bộ X01 đã chạy.
