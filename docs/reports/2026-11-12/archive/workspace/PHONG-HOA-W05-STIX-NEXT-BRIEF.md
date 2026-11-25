# W05 — nghiên cứu chuyển snapshot đã duyệt thành STIX ngoại tuyến

## Mục tiêu và phạm vi

CTI Research nghiên cứu và giao lại **hai tài liệu đủ cho Backend/Sol medium triển khai một lát cắt nhỏ**. Không triển khai code, không giao tiếp worker khác. Nối yêu cầu W05: duyệt tạo Report + object STIX, người duyệt được ghi nhận và chỉ các mục được duyệt đi tiếp. Phần browser/selection đã nghiệm thu cục bộ; OpenCTI/lab vẫn để sau.

Root: `$WORKSPACE`.

Source chỉ đọc: `<root>\cti-w05-selection-integration`, branch `feat/w05-selection-integration-20261111`, HEAD `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`. Kiểm HEAD/status trước và sau. Không dùng main thay source này. Nếu thấy khác hoặc bẩn, chỉ báo phạm vi thay đổi; không reset/sửa tree.

Đọc có chọn lọc:

- `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-duyet.md`, `docs/specs/W05-draft-offline-contract.md` và phần dữ liệu của X01.
- Store/selection/audit/helper đọc snapshot và test thực tế; dùng `rg` tìm file/function, không đoán tên helper.
- `deploy/demo/fixtures/README.md`, `demo-bundle.json`, `deploy/demo/README.md`, pin validator đã có và thư viện STIX/chuẩn hóa hiện có; không tạo bộ chuyển trùng chức năng.
- Root: `PHONG-HOA-W05-SELECTION-INTEGRATION-ACCEPTANCE-20261111.md`, nghiên cứu/brief W05-EDIT và SELECTION-API khi cần hiểu invariant, không audit lại phần đã accepted.
- Kiểm xem nghiên cứu hoặc PR đang mở đã làm đúng phần này bằng nguồn đọc được; không tạo PR hay suy main là toàn bộ sản phẩm. Nếu không truy cập được, ghi giới hạn cụ thể.

## Câu hỏi cần giải quyết

1. So tối đa3 phương án: converter/CLI đọc approved snapshot xuất bundle offline; outbox bền vững để nối gửi sau; tích hợp import OpenCTI. Chọn lát cắt nhỏ nhất có ích hiện nay, ưu tiên converter offline nếu đủ spec. Tách phần cần lab, không biến nghiên cứu thành triển khai import.
2. Đối chiếu nguồn chính thức OASIS STIX2.1, OpenCTI import/mapping, thư viện/validator được đề xuất và FIRST TLP2.0. Ghi URL/ref/ngày truy cập, cái gì tái dùng, cái gì chưa chắc. Không dựa blog/AI report thay nguồn gốc; không cần nghiên cứu lại UI/auth.
3. Đầu vào phải là draft đã approved cùng snapshot/hash trong **final audit**; không lấy `items.keep` hay selection mới từ client làm quyền xuất. Chốt read transaction nhất quán, kiểm hash/version, dữ liệu hỏng, pending/rejected/legacy v1/v2, fail closed và không ghi/migrate DB khi đọc. Chốt helper thực sự có thể tái dùng và phần cần bổ sung nhỏ nhất.
4. Mapping IOC được hỗ trợ hiện tại (domain,URL,IP,hash theo code): SCO/Indicator/Report/relationship cần gì, pattern escaping, IDs, references, timestamps và dedup. Không tự suy threshold để mọi IOC thành malicious Indicator; giải thích lựa chọn semantics theo STIX/OpenCTI. Không thêm TTP chưa hỗ trợ.
5. Bảo toàn nguồn/evidence/provenance, reviewer subject opaque và identity mapping server-side/offline tin cậy. Không nhận email/actor tự khai để giả người duyệt; không đưa subject thành UUID tùy tiện hoặc xuất secret. Nêu trường nội bộ và trường STIX chuẩn rõ.
6. TLP2.0 và mapping vào STIX/OpenCTI: không hạ mức AMBER/RED thành công khai; phân biệt AMBER+STRICT nếu spec/code hỗ trợ, mặc định hiện hữu. Việc tạo artifact offline không cho phép gửi cloud hay chia sẻ cho người ngoài. Không thêm chính sách sản phẩm mới khi không có nguồn/spec.
7. Khả năng tái hiện/idempotency: xuất lặp cùng approved snapshot phải có quy tắc ID/thời gian ổn định được nêu rõ; không dùng giờ hiện tại vô tình đổi object mỗi lần. Atomic file output, không ghi đè file tốt khi validation thất bại; lỗi CLI rõ, không lộ nguồn/raw secret trong lỗi. Giữ DB immutable.
8. Dependency/validator: tái dùng pin hiện có nếu phù hợp; nếu cần pin mới nêu căn cứ/lock/hash và đề xuất bước triển khai cục bộ sau, không cài trong lượt nghiên cứu.

## Hai đầu ra duy nhất

- `<root>\PHONG-HOA-W05-STIX-RESEARCH.md`: hiện trạng, lựa chọn có nguồn, reuse/gap, quyết định khuyến nghị và giới hạn.
- `<root>\PHONG-HOA-W05-STIX-IMPLEMENTATION-BRIEF.md`: base exact, tree/branch riêng đề xuất (chưa tạo), file scope, interface/CLI/mapping/schema/lỗi, acceptance matrix, TDD và lệnh offline cần chạy, demo với draft hai IOC bỏ một mục rồi approve → bundle chỉ có mục đã duyệt. Handoff lab sau tách riêng.

Ma trận tối thiểu phải bao phủ output validator/reference hợp lệ, hash/payload/DB không đổi, đúng approved selection, pending/rejected/self-authorship boundary phù hợp store, snapshot/version/hash bị sửa, duplicate/empty/Unicode/escaping, TLP và identity, từng IOC type hỗ trợ/không hỗ trợ, xuất lặp, lỗi không hỏng output. Không hứa chất lượng sản phẩm từ fixture tổng hợp.

Không sửa repo/RUNS/báo cáo cũ, không tạo worktree/commit hoặc chạy test implementation, không listener/network tới OpenCTI/LLM, không secret/lab/push/PR/merge/deploy. Đọc tài liệu chính thức trên web được phép. Báo hash hai tài liệu, HEAD/status nguồn trước/sau và những gì chưa xác minh; đây là research/brief, không phải PASS implementation.
