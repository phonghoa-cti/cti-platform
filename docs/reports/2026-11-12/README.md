# Phong Hỏa — quá trình và kết quả đến 12/11/2026

**Bản chốt lúc 08:56 giờ Việt Nam, ngày 12/11/2026. Dự án đã có nhiều luồng chạy cục bộ và được nghiệm thu từng phần; chưa hoàn thành toàn bộ MVP, chưa chạy trên lab hoặc production.** Người dùng yêu cầu đẩy kết quả hiện tại lên GitHub và ghi lại quá trình. Lượt này bảo toàn mã, lịch sử và tài liệu; không thay đổi hành vi sản phẩm.

## Đọc bản nào trước

- [Nhánh và mã commit đã chốt](BRANCHES.md): 52 nhánh kết quả, từ 42 thư mục mã sạch. Nhánh tài liệu này có nền tích hợp portal `f5d2315e94b7f83e44360a04b67902cb5b0ba4bd`.
- [Toàn bộ 133 commit sau PR #46](COMMITS.md), giữ cả các vòng sửa lỗi và tích hợp.
- [89 đầu việc](TASKS.md): sổ hiện ghi 84 đã nghiệm thu trong phạm vi riêng, 3 có vướng mắc, 2 đã giao. Đây không phải tỷ lệ hoàn thành sản phẩm.
- [413 tài liệu quá trình](ARCHIVE.md): nghiên cứu, brief, báo cáo, review, nghiệm thu và kế hoạch. [Manifest nguồn](source-manifest.json) cho biết hash bản gốc và bản công bố.
- [Kiểm tra lần công bố](VERIFICATION.md), [sổ việc tại thời điểm chốt](ledger-snapshot.json), [ảnh chụp trạng thái Git](git-snapshot.json).
- [Bộ kiểm sổ điều phối đã có](workflow/README.md) được lưu cùng script và test để tái sử dụng; nó chỉ đọc sổ, không tự giao việc.

Các nhánh AI, ingest và portal phát triển riêng; việc có đủ nhánh trên GitHub không có nghĩa toàn bộ chúng đã nằm trong một bản chạy chung. `main` vẫn là nền `3ff7daf93469dd13692fd1f7aec83a323e2ebb43`; hai PR [#1](https://github.com/phonghoa-cti/cti-platform/pull/1) và [#46](https://github.com/phonghoa-cti/cti-platform/pull/46) còn mở khi kiểm tra. Không merge hoặc deploy trong lượt công bố này.

## Diễn biến công việc

### Nền trước ngày 10/11

Repo có thư viện chuẩn hóa IOC, trích xuất bằng biểu thức chính quy, tính điểm, allowlist, đặc tả F01–F08/W00–W05/A01, thiết kế portal và tài liệu học. PR #46 bổ sung quét dấu hiệu chèn lệnh, đối chiếu IOC với văn bản nguồn và đo precision/recall/F1. Nền triển khai sau này là `36259c118f519d3ac9cfc1f7b79e7180c2448a88`; không chỉ nhìn `main` rồi viết lại phần đã có trong PR.

### Ngày 10/11 — nghiên cứu, chia phạm vi và dựng các luồng nhỏ

Leader đối chiếu OpenCTI, connector, STIX, nguồn CTI, ranh giới TLP và các công cụ phát triển; lập quy trình nghiên cứu → chọn giải pháp → mô tả hợp đồng dữ liệu → triển khai → kiểm chứng. Cách làm và nguồn gốc nằm trong [working agreement](archive/workspace/PHONG-HOA-WORKING-AGREEMENT.md), [nghiên cứu workflow](archive/workspace/PHONG-HOA-ORCHESTRATION-RESEARCH-20261110.md) và [kế hoạch song song](archive/workspace/PHONG-HOA-PARALLEL-PLAN.md).

Các phần Backend, AI, Frontend, tích hợp và QA dùng thư mục mã riêng. Theo quyết định được ghi ngày 10/11, Frontend chuyển sang Codex/Sol; lab để sau. Đã triển khai X01 từ văn bản tổng hợp đến IOC có bằng chứng, bản nháp và hàng chờ SQLite; chuẩn bị adapter AI ngoại tuyến, lõi W05 và giao diện ban đầu. Đồng thời chuẩn bị cấu hình OpenCTI và nguồn demo nhưng chưa khởi động dịch vụ thật.

### Ngày 11/11 — nối duyệt, xuất kết quả, đánh giá AI và quản lý tài sản

W05 phát triển từ lõi duyệt sang API, giao diện, chọn/bỏ chọn IOC, audit bất biến và xuất STIX từ bản đã duyệt. Tiếp đó kiểm một luồng văn bản → extractor → cùng cơ sở dữ liệu → chọn/duyệt qua HTTP → xuất STIX; sau này thêm nhập TXT/PDF và kiểm duyệt trên trình duyệt. Những lỗi tải lại sau khi lưu được sửa theo hướng chỉ đọc lại bằng GET, không tự gửi lại yêu cầu ghi khi chưa rõ kết quả.

Nhánh AI bổ sung catalog ATT&CK chính thức được cố định phiên bản/hash, truy hồi ngoại tuyến, audit TTP, evaluator C2–C4 và báo cáo. Bộ kiểm dữ liệu pilot được xây để phát hiện dữ liệu chưa đủ điều kiện. Các thử nghiệm này dùng dữ liệu tổng hợp hoặc provider giả lập; chúng kiểm được cơ chế và hợp đồng, chưa chứng minh chất lượng mô hình trên báo cáo thật.

W02 nối giao diện tra cứu IOC với API cục bộ, kiểm quyền, chuẩn hóa, allowlist và TLP. W04 bổ sung domain/CIDR rồi tài sản công nghệ, kiểm trùng, sửa/xóa, phiên bản và audit. Các luồng phục hồi lỗi được đối chiếu cả dấu vết HTTP và SQLite để tránh kết luận chỉ từ ảnh giao diện.

### Ngày 12/11 — lỗ hổng liên quan và trạng thái xử lý

W03-R bổ sung danh sách CVE tổng hợp liên quan đến tài sản công nghệ, xếp hạng, lọc, phân trang và góc nhìn tổng hợp. QA phát hiện lỗi dữ liệu hợp đồng, callback cũ và bộ lọc KEV. Sau sửa, ca bật → tắt → bật bộ lọc cho 3 → 16 → 3 CVE được đối chiếu trên trình duyệt; các lần đọc giữ nguyên dữ liệu SQLite. Chi tiết tại [nghiệm thu W03-R](archive/workspace/leader-w03-final-acceptance-20261112/ACCEPTANCE.md).

W03-S1 bổ sung trạng thái theo cặp công nghệ/CVE, ghi chú và lịch sử. Backend sửa kiểm dữ liệu đầu vào và dữ liệu lưu hỏng; Frontend sửa khóa ghi khi chưa biết kết quả, callback cũ, phân trang lịch sử, dữ liệu wire, đổi hoa/thường và đóng/mở màn hình lúc yêu cầu còn chờ. Bản Backend `4f7100cf` và Frontend `2448b860` đã được nghiệm thu cục bộ.

Trong tích hợp, bộ mô phỏng lỗi từng làm lỗi lan sang bản ghi khác/lịch sử; đã ràng buộc theo đúng đường dẫn trạng thái. Các lượt A/B bổ sung bằng chứng phục hồi sau khi lưu và sau khi kết quả lưu chưa rõ, bao gồm đóng/mở lại màn hình, khóa ghi và chỉ một lần PUT/một audit. Một lỗi checkout Windows làm byte xuống dòng của fixture thay đổi cũng được tái hiện, sau đó sửa bằng quy tắc LF riêng cho fixture.

Giới hạn tên sản phẩm được thống nhất 256 ký tự, kiểm biên 256/257 cùng Unicode và biên vendor 128/129. Delta tích hợp `867bdcae` đã được nghiệm thu; HEAD hiện tại `f5d2315e` chỉ bổ sung tài liệu sau đó. Sổ vẫn để W03-S1 ở trạng thái đã giao, chờ chốt báo cáo/cleanup và nghiệm thu toàn hạng mục; chưa có báo cáo đóng việc tại đường dẫn đã giao khi chốt bản này. W03-S2 mới được giao nghiên cứu lọc trạng thái và số tổng hợp, chưa có báo cáo nghiên cứu tại đường dẫn đã giao và chưa triển khai.

## Kết quả sử dụng được và mức bằng chứng

Các con số kiểm thử dưới đây lấy từ biên bản từng mốc, không phải lượt chạy lại toàn bộ ngày công bố. `PASS cục bộ` chỉ có hiệu lực với phạm vi, SHA và dữ liệu đã ghi.

| Phần | Kết quả hiện có | Mức kiểm chứng và giới hạn |
|---|---|---|
| X01 nháp/hàng chờ | Văn bản → IOC có bằng chứng → nháp → SQLite | Nghiệm thu ngoại tuyến `e83bb3f5`; chưa gọi LLM thật |
| W05 duyệt/chọn/xuất | Lõi duyệt, quyền, chọn IOC, audit và STIX từ trạng thái duyệt bất biến | STIX `ed829a03`: Leader chạy 14 probe; hồ sơ 77 test Backend. Chưa nhập OpenCTI |
| X01 → W05 → STIX | Cùng dữ liệu xuyên extractor, API duyệt và xuất | `cf9e6094`: Leader từng chạy 54 test, 59 kiểm tra E2E, 113 kiểm tra selection; local CLI/HTTP |
| TXT/PDF → duyệt | Nhập có provenance, phục hồi GET sau lỗi tải lại, không gửi ghi lặp | `4655d9ae`, nghiệm thu browser cục bộ; không suy ra lab hoặc dữ liệu thật |
| AI C2–C4/ATT&CK | Adapter giả lập, retrieval, audit, evaluator và reporter | `5e0cbf4d`: 18 probe + 7 writer checks của Leader, 181 test trong hồ sơ worker; semantic/model quality chưa xác minh |
| Pilot dữ liệu | Validator và kiểm điều kiện sẵn sàng | `1fc3986e`: Leader chạy 61 test; chưa có corpus được hai người gán nhãn |
| W02 tra cứu IOC | `/tra-cuu` dùng API cục bộ; nguồn mẫu tách riêng | Runtime `50277102`, docs `aeff542a`; browser/API cục bộ, xác thực thật chưa kiểm |
| W04 tài sản | Domain/CIDR và công nghệ, CRUD, chống xung đột, audit | Technology `273196e2`: Leader chạy 51 HTTP assertions + 1 gateway test, đối chiếu 58 hash và bằng chứng desktop; brand/keyword/CSV còn thiếu |
| W03-R | CVE liên quan công nghệ, KEV, phân trang, detail/summary | `7ff6eb3a`, nghiệm thu desktop cục bộ; dữ liệu CVE tổng hợp, không chứng minh phiên bản cài đặt bị ảnh hưởng |
| W03-S1 | Trạng thái/lịch sử, kiểm xung đột, phục hồi sau ghi | HEAD `f5d2315e`; các phần A/B và product256 đã có nghiệm thu riêng; toàn S1 vẫn chờ đóng việc |
| Hạ tầng/demo | Cấu hình và tài liệu chuẩn bị nguồn/OpenCTI | Chưa boot lab, chưa kiểm import/workbench/quyền thực tế/RAM/queue |

Các biên bản trọng tâm: [W05-STIX](archive/workspace/PHONG-HOA-W05-STIX-ACCEPTANCE-20261111.md), [X01–W05 E2E](archive/workspace/PHONG-HOA-X01-W05-STIX-E2E-ACCEPTANCE-20261111.md), [C4](archive/workspace/PHONG-HOA-X01-C4-EVAL-ACCEPTANCE-20261111.md), [pilot](archive/workspace/PHONG-HOA-X01-GOLD-PILOT-ACCEPTANCE-20261111.md), [W04 Technology](archive/workspace/leader-w04-technology-integration-acceptance-20261112/ACCEPTANCE.md), [W03 A/B](archive/threads/48f883ae-6d18-46a9-83fa-cc7436de1f5d/PHONG-HOA-W03-DELTA-REVIEW-AND-NEXT.md), [product256](archive/threads/ac95b575-9df8-4f39-bb20-f27be0abf7e9/PHONG-HOA-W03-PRODUCT256-ACCEPTANCE-NEXT.md).

## Phần còn mở

1. Chốt báo cáo và bằng chứng cleanup W03-S1, rồi quyết định nghiệm thu toàn hạng mục; không tự nâng trạng thái chỉ vì mã đã được push.
2. Nghiệm thu nghiên cứu W03-S2 trước khi chọn hợp đồng cho lọc trạng thái/tổng hợp. Danh sách task tiếp tục giữ chủ sở hữu và các lần giao đã có.
3. Kiểm viewport thật 360/1440; bằng chứng desktop hiện chủ yếu 1280×720. Hạn chế này là trạng thái đã ghi trong sổ, không phải phép kiểm khả năng trình duyệt mới của lượt công bố.
4. Pilot báo cáo thật cần quyền sử dụng nguồn, hai người gán nhãn độc lập và người hòa giải bất đồng; không dùng nhãn do AI tự tạo để thay thế.
5. Lab/OpenCTI, feed thật, LLM thật, Cloudflare/JWKS/HTTPS, tải/vận hành và production còn chưa xác minh. Phần còn lại của W01, W04 và các spec MVP tiếp tục theo backlog; số task đã accepted không chứng minh tất cả đặc tả hoàn thành.

Hai lịch tiếp tục Phong Hỏa còn bật khi kiểm ngày 12/11. Lịch định kỳ có các lượt gần đây chạm giới hạn 15 phút; việc có lịch và thông báo đã giao không phải bằng chứng worker đang chạy. Lượt công bố giữ lịch hiện hành và không thay đổi quyền hoặc yêu cầu tự động hóa.

## Phạm vi công bố và cách tái sử dụng

Người dùng cho phép push kết quả hiện tại trong yêu cầu ngày 12/11. Các dòng “không push/PR” trong tài liệu lịch sử mô tả quyền của lượt cũ; yêu cầu mới chỉ cho phép lần công bố này, không tự cấp quyền merge, phát hành hay push các thay đổi tương lai. Nhánh tài liệu lấy nền portal hiện tại để có thể đọc cùng source; các nhánh khác được lưu độc lập, không gộp mã chưa được kiểm tích hợp.

Đọc [hướng dẫn tích hợp cục bộ](../../../tools/local_integration/README.md) từ repo, chọn SHA của luồng cần thử ở BRANCHES, rồi dùng hướng dẫn/test trên đúng nhánh đó. Không lấy số test của một nhánh gán cho nhánh khác. Các báo cáo cũ giữ đường dẫn evidence gốc dưới ký hiệu portable; danh mục archive nói rõ dữ liệu nào được công bố và dữ liệu nào chỉ còn cục bộ.

**Hai khái niệm khi đọc hồ sơ:** commit là một bản ghi mã không đổi, còn branch là tên trỏ tới commit và có thể tiến lên. Nghiệm thu cục bộ chứng minh hành vi trong môi trường đã thử; nó khác với kiểm trên lab và phát hành cho người dùng thật.
