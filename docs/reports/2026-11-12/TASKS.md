# Toàn bộ đầu việc tại thời điểm chốt

Sổ nguồn cập nhật 2026-11-12T08:40:15.848671+07:00; 89 đầu việc, thống kê {"accepted": 84, "blocked": 3, "dispatched": 2}.

`accepted`: đã ghi nhận nghiệm thu trong sổ, chỉ trong phạm vi evidence đi kèm; `dispatched`: đã giao, không chứng minh đang chạy hoặc đã xong; `blocked`: có vướng mắc. Lượt công bố này không nghiệm thu lại toàn bộ sản phẩm và không đổi trạng thái task.

| ID | Phụ trách | Trạng thái đã ghi | Nội dung |
|---|---|---|---|
| `X01-OFFLINE` | Leader | accepted | Mốc bản nháp ngoại tuyến |
| `WORKFLOW-GUARD` | CTI Engineer | accepted | Bộ kiểm tra quyết định tiếp tục |
| `W05-NEXT-RESEARCH` | CTI Research | accepted | Chọn lát cắt duyệt bản nháp tiếp theo |
| `W05-IMPLEMENT` | CTI Backend | accepted | Triển khai lát cắt W05 đã được chọn |
| `W05-VERIFY` | Leader | accepted | Nghiệm thu luồng W05 và chọn bước kế trong backlog |
| `UI-IMPLEMENT` | CTI Frontend | accepted | Portal W05 preview theo hợp đồng offline |
| `LAB-VERIFY` | CTI Engineer | blocked | Khởi động và kiểm OpenCTI trên lab |
| `AI-NEXT` | CTI AI Agent | accepted | Chọn lát cắt AI/agent offline và brief |
| `AI-IMPLEMENT` | CTI AI Agent | accepted | Adapter LLM C2/C3 với provider giả lập |
| `W05-API-NEXT` | CTI Research | accepted | Nghiên cứu và brief HTTP/auth nối portal với W05 |
| `W05-API-IMPLEMENT` | CTI Backend | accepted | API W05 có JWT/role/Origin và quyết định cục bộ |
| `UI-API-INTEGRATION` | CTI Frontend | accepted | Client W05 gọi API và quản lý trạng thái duyệt |
| `UI-RESPONSIVE-VERIFY` | CTI Frontend | blocked | Kiểm viewport thật 360 và 1440 |
| `AI-EVAL-NEXT` | CTI Research | accepted | Nghiên cứu nối evaluator C2/C3 ngoại tuyến |
| `AI-EVAL-IMPLEMENT` | CTI AI Agent | accepted | Evaluator C2/C3 trên dữ liệu tổng hợp |
| `W05-LOCAL-INTEGRATION-NEXT` | CTI Engineer | accepted | Nghiên cứu đường nối UI/API cục bộ và brief kiểm browser |
| `W05-LOCAL-INTEGRATION-IMPLEMENT` | CTI Engineer | accepted | Harness UI API SQLite cục bộ với JWT tổng hợp |
| `W05-EDIT-NEXT` | CTI Research | accepted | Nghiên cứu lõi lưu lựa chọn IOC của người duyệt |
| `W05-EDIT-IMPLEMENT` | CTI Backend | accepted | Lõi lưu lựa chọn IOC với version và audit |
| `W05-SELECTION-API-NEXT` | CTI Research | accepted | Nghiên cứu hợp đồng API cho lựa chọn IOC |
| `W05-SELECTION-API-IMPLEMENT` | CTI Backend | accepted | API v1 đọc/lưu lựa chọn IOC và quyết định cùng snapshot |
| `W05-SELECTION-UI-NEXT` | CTI Research | accepted | Nghiên cứu luồng chọn/lưu IOC và brief UI v1 |
| `W05-SELECTION-UI-IMPLEMENT` | CTI Frontend | accepted | UI chọn/lưu IOC và quyết định bản đã lưu qua API v1 |
| `W05-SELECTION-INTEGRATION` | CTI Engineer | accepted | Tích hợp selection v1 qua gateway cục bộ và kiểm browser/audit |
| `W05-STIX-NEXT` | CTI Research | accepted | Nghiên cứu gói STIX ngoại tuyến từ snapshot đã duyệt |
| `W05-STIX-IMPLEMENT` | CTI Backend | accepted | Xuất STIX ngoại tuyến từ final audit đã duyệt |
| `X01-W05-STIX-E2E-NEXT` | CTI Engineer | accepted | Lập brief nối văn bản nguồn qua duyệt đến STIX |
| `X01-W05-STIX-E2E-IMPLEMENT` | CTI Engineer | accepted | Kiểm văn bản qua CLI, duyệt HTTP đến STIX trong cùng run |
| `X01-ATTACK-NEXT` | CTI Research | accepted | Nghiên cứu kiểm mã ATT&CK từ snapshot ngoại tuyến |
| `X01-ATTACK-IMPLEMENT` | CTI AI Agent | accepted | Bộ tra cứu mã ATT&CK ngoại tuyến với fixture tổng hợp |
| `X01-ATTACK-REAL-NEXT` | CTI Research | accepted | Nghiên cứu tương thích snapshot Enterprise ATT&CK chính thức |
| `X01-ATTACK-REAL-IMPLEMENT` | CTI AI Agent | accepted | Đọc snapshot MITRE Enterprise 20.1 chính thức ngoại tuyến |
| `X01-TTP-AUDIT-NEXT` | CTI Research | accepted | Nghiên cứu nối catalog và bằng chứng kỹ thuật AI |
| `X01-TTP-AUDIT-IMPLEMENT` | CTI AI Agent | accepted | Kiểm mã ATT&CK và câu trích đúng nguồn ngoại tuyến |
| `X01-TTP-EVAL-NEXT` | CTI Research | accepted | Nghiên cứu nối audit technique vào báo cáo C2/C3 |
| `X01-TTP-EVAL-IMPLEMENT` | CTI AI Agent | accepted | Đưa audit technique vào báo cáo C2/C3 ngoại tuyến |
| `X01-EVAL-REPORT-NEXT` | CTI Research | accepted | Nghiên cứu bảng kết quả C1-C3 và provenance |
| `X01-EVAL-REPORT-IMPLEMENT` | CTI AI Agent | accepted | Xuất bảng báo cáo C1-C3 từ artifact ngoại tuyến |
| `X01-C4-RETRIEVAL-NEXT` | CTI Research | accepted | Nghiên cứu thành phần truy hồi ATT&CK cho C4 ngoại tuyến |
| `X01-C4-RETRIEVAL-IMPLEMENT` | CTI AI Agent | accepted | Triển khai truy hồi ATT&CK lexical và context ngoại tuyến |
| `X01-C4-ADAPTER-NEXT` | CTI Research | accepted | Nghiên cứu nối context ATT&CK trước generation ngoại tuyến |
| `X01-C4-ADAPTER-IMPLEMENT` | CTI AI Agent | accepted | Nối context ATT&CK vào adapter C4 và audit ngoại tuyến |
| `X01-C4-EVAL-NEXT` | CTI Research | accepted | Nghiên cứu evaluator và kết quả C4 ngoại tuyến |
| `X01-C4-EVAL-IMPLEMENT` | CTI AI Agent | accepted | Triển khai evaluator và báo cáo C4 ngoại tuyến |
| `X01-GOLD-DATASET-NEXT` | CTI Research | accepted | Nghiên cứu chuẩn bị dữ liệu đánh giá có nguồn và nhãn |
| `X01-GOLD-PILOT-IMPLEMENT` | CTI AI Agent | accepted | Triển khai kiểm hồ sơ dữ liệu thử ngoại tuyến |
| `X01-HUMAN-PILOT-PREP` | CTI Research | accepted | Chuẩn bị nguồn và hướng dẫn pilot hai người |
| `X01-HUMAN-PILOT-EXECUTE` | Leader | blocked | Pilot dữ liệu với hai người gán nhãn độc lập |
| `X01-LOCAL-INGEST-NEXT` | CTI Research | accepted | Nghiên cứu nạp văn bản và PDF cục bộ |
| `X01-LOCAL-INGEST-IMPLEMENT` | CTI AI Agent | accepted | Triển khai nạp text/PDF cục bộ thành draft có nguồn gốc |
| `X01-INGEST-QUEUE-NEXT` | CTI Research | accepted | Nghiên cứu đưa envelope TXT/PDF vào hàng chờ W05 |
| `X01-INGEST-QUEUE-IMPLEMENT` | CTI Backend | accepted | Nhập bản nạp TXT/PDF vào hàng chờ W05 có nguồn gốc và người tạo |
| `X01-INGEST-BROWSER-PREP` | CTI Engineer | accepted | Chuẩn bị kiểm chứng cùng bản nạp qua giao diện và xuất STIX |
| `W02-LOOKUP-VIEW` | CTI Frontend | accepted | Giao diện tra cứu IOC có trạng thái và dữ liệu thử rõ ràng |
| `W02-LOOKUP-API-RESEARCH` | CTI Research | accepted | Chốt API tra cứu IOC chỉ đọc và brief triển khai |
| `X01-INGEST-QUEUE-QA` | CTI QA Security | accepted | Kiểm độc lập importer TXT/PDF trước nối browser |
| `X01-INGEST-BROWSER-HARNESS` | CTI Engineer | accepted | Viết phần điều khiển demo nạp và duyệt trong tree riêng |
| `W02-LOOKUP-API-IMPLEMENT` | CTI Backend | accepted | API tra cứu IOC chỉ đọc theo hợp đồng đã chốt |
| `W02-LOOKUP-HTTP-ADAPTER` | CTI Frontend | accepted | Kết nối HTTP theo hợp đồng cho view tra cứu W02 |
| `X01-INGEST-BROWSER-HARNESS-QA` | CTI QA Security | accepted | Kiểm độc lập hậu kiểm và vòng đời bộ demo |
| `X01-INGEST-BROWSER-INTEGRATION` | CTI Engineer | accepted | Nối importer đã sửa với harness đã kiểm để chạy demo browser |
| `W02-LOCAL-INTEGRATION` | CTI Frontend | accepted | Nối giao diện tra cứu với API cục bộ và kiểm browser |
| `W04-ASSETS-NEXT` | CTI Research | accepted | Nghiên cứu quản lý tài sản cục bộ và liên kết tra cứu W02 |
| `W04-ASSETS-IMPLEMENT` | CTI Backend | accepted | Lõi tài sản domain/CIDR và API cục bộ có audit |
| `W04-ASSETS-FRONTEND` | CTI Frontend | accepted | Giao diện tài sản mẫu, HTTP adapter và hiển thị asset-match W02 |
| `W04-ASSETS-BACKEND-QA` | CTI QA Security | accepted | Kiểm độc lập quyền, giao dịch và snapshot W04 |
| `W04-LOCAL-INTEGRATION` | CTI Engineer | accepted | Nối giao diện tài sản với API và kiểm cùng dữ liệu cục bộ |
| `W04-INTEGRATION-PREP` | CTI Engineer | accepted | Chuẩn bị gateway/runner W04 và ma trận HTTP độc lập với UI |
| `W04-TECHNOLOGY-NEXT` | CTI Research | accepted | Nghiên cứu tài sản công nghệ W04 làm đầu vào W03 |
| `W04-TECHNOLOGY-BACKEND` | CTI Backend | accepted | CRUD công nghệ SQLite/API/quyền/audit |
| `W04-TECHNOLOGY-FRONTEND` | CTI Frontend | accepted | Tab công nghệ mẫu và HTTP adapter |
| `W04-TECHNOLOGY-INTEGRATION` | CTI Engineer | accepted | Nối công nghệ với API/gateway và kiểm cục bộ |
| `W03-NEXT` | CTI Research | accepted | Nghiên cứu CVE liên quan công nghệ và ưu tiên vá |
| `W03-READ-BACKEND` | CTI Backend | accepted | W03 read-only backend |
| `W03-READ-FRONTEND` | CTI Frontend | accepted | W03 read-only frontend |
| `W03-READ-FRONTEND-QA` | CTI QA Security | accepted | Kiểm độc lập ứng viên Frontend W03 |
| `W03-READ-BACKEND-QA` | CTI QA Security | accepted | Kiểm độc lập Backend W03 |
| `W03-READ-INTEGRATION` | CTI Engineer | accepted | W03 nối tra cứu lỗ hổng với API và kiểm trình duyệt |
| `W03-FILTER-FIX` | CTI Frontend | accepted | W03 bỏ Chỉ KEV phải hiển thị tất cả |
| `W03-STATUS-NEXT` | CTI Research | accepted | Nghiên cứu trạng thái xử lý và lịch sử theo công nghệ/CVE |
| `W03-STATUS-BACKEND` | CTI Backend | accepted | W03-S1 backend trạng thái và lịch sử |
| `W03-STATUS-FRONTEND` | CTI Frontend | accepted | W03-S1 frontend trạng thái và lịch sử |
| `W03-STATUS-INTEGRATION-PREP` | CTI Engineer | accepted | W03-S1 gateway và HTTP chuẩn bị độc lập |
| `W03-STATUS-FRONTEND-QA` | CTI QA Security | accepted | Kiểm độc lập bản sửa Frontend W03-S1 F5/F6 |
| `W03-STATUS-INTEGRATION` | CTI Engineer | dispatched | W03-S1 ghép giao diện và kiểm lưu trạng thái/lịch sử trên browser |
| `W03-PRODUCT-LIMIT-REVIEW` | CTI Research | accepted | Đối chiếu product128 của W03 với product256 của W04/status |
| `W03-PRODUCT-BOUNDARY-FIX` | CTI Backend | accepted | Thống nhất affected product W03 lên256 code point |
| `W03-STATUS-DELTA-QA` | CTI QA Security | accepted | Kiểm độc lập delta product256, lỗi wire fixture và remount khóa ghi W03-S1 |
| `W03-STATUS-S2-NEXT` | CTI Research | dispatched | Nghiên cứu lọc trạng thái và tổng hợp W03-S2 |
