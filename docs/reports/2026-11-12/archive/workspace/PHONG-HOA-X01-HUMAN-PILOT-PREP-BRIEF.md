# X01-HUMAN-PILOT-PREP — chuẩn bị pilot cho hai người gán nhãn

Nhiệm vụ nghiên cứu/tài liệu tiếp sau nghiệm thu Gold Pilot, 11/11/2026. Root `$WORKSPACE`.

## Mục tiêu và source

Chuẩn bị một gói hướng dẫn thực hành đủ rõ để hai người có thể gán nhãn độc lập cho 5 báo cáo CTI. Căn cứ backlog `extractor/dataset/GUIDELINE.md`, `docs/specs/X01-ai-extractor.md`. Không tạo thêm công cụ đánh giá trước khi xác định dữ liệu/người gán nhãn thật.

Source chỉ đọc `<root>\cti-x01-gold-pilot`, branch `feat/x01-gold-pilot-readiness-20261111`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`. Nghiệm thu tại `PHONG-HOA-X01-GOLD-PILOT-ACCEPTANCE-20261111.md`; hợp đồng chính xác `PHONG-HOA-X01-GOLD-PILOT-LEADER-PLAN.md`. Tái dùng `PHONG-HOA-X01-GOLD-DATASET-RESEARCH.md` và các nguồn TRAM đã dẫn, không nghiên cứu lại validator.

## Hai đầu ra được phép viết

1. `<root>\PHONG-HOA-X01-HUMAN-PILOT-SOURCES.md`: mục tiêu 5 báo cáo ứng viên (ưu tiên 3 tiếng Việt/2 tiếng Anh, tối thiểu 2 tiếng Việt nếu nguồn phù hợp). Mỗi mục có title, URL chính thức, publisher, ngày báo cáo/ngày đọc, ngôn ngữ, lý do phù hợp tiêu chí 300–3000 từ và có IOC hoặc mô tả hành vi, tình trạng truy cập, khả năng trùng/translation. Phải mở nguồn và kiểm nội dung liên quan, không dùng riêng search snippet. Nếu thiếu nguồn đạt thì trả đúng số đã kiểm và lý do, không bịa đủ5. Chỉ link/metadata và diễn giải ngắn, không lưu raw toàn bài/IOC list, không lấy malware/sample hoặc chạy nội dung web.

   Ghi riêng bằng chứng về quyền sử dụng từng nguồn: liên kết tới điều khoản/licence nếu quan sát được, phần chưa rõ; không suy licence code TRAM hoặc public URL là quyền lưu/phân phối raw. Quyền chưa rõ => `unknown/link-only`, không tự gán TLP:CLEAR/GREEN chỉ từ việc public. TLP không có marking => chưa xác định; đề xuất cách người phụ trách xác nhận trước nhập dữ liệu. Không đưa dữ liệu đó vào validator bằng cách bịa provenance/rights/TLP. Mọi nguồn chỉ là ứng viên, chưa là corpus được duyệt.

2. `<root>\PHONG-HOA-X01-HUMAN-PILOT-RUNBOOK.md`: tiếng Việt, quy trình ngắn từ xác nhận quyền/TLP → lưu raw hợp lệ tại local → chuẩn hóa CRLF/CR/LF và tính hash/span code point → hai người nhận cùng văn bản nhưng không thấy nhãn nhau → kiểm mỗi annotation → so agreement → adjudication (con người giải quyết nhãn khác nhau) sau khi đã giữ bản nhãn độc lập. Tái dùng normalizer/catalog/CLI hiện có; chỉ dẫn lệnh đầy đủ với đường dẫn, flags, safe output và ý nghĩa exit0/2/1. Phân biệt v1 schema mới với GUIDELINE labels cũ; không thêm ghi_chu/key ngoài schema, không coi no_findings là nhãn chưa làm. Nêu 80% trong guideline cũ chỉ là tiêu chí thảo luận, validator không có cổng80%; báo cáo agreement không là model F1 hay semantic truth.

   Một ví dụ văn bản tổng hợp rất ngắn để minh họa Unicode/defang/evidence, ghi rõ là giả, không phải nhãn hai người thật. Không sinh file annotation thực hoặc đặt tên người gán nhãn. Phân biệt schema structural READY với quyền/độc lập/semantic chưa xác minh. Liệt kê gọn các điều kiện con người cần cung cấp sau này (quyền hợp lệ, người gán, quyết định bất đồng), không hỏi người dùng qua bot. Chưa triển khai scorer/adjudication/UI, chưa sửa GUIDELINE hoặc schema.

## Phạm vi và kiểm tra

Một CTI Research làm trực tiếp, không giao bot khác. Nghiên cứu web bằng công cụ được phép, ưu tiên nguồn tác giả/cơ quan chính thức; không đăng nhập, gửi bài/mail, model/cloud, tải raw có quyền chưa rõ hoặc tạo account. Không sửa repo/source/RUNS/review; không tạo worktree/commit, không chạy test implementation, không push/PR/merge/deploy/lab.

Trước/sau ghi hai tài liệu kiểm source HEAD/status đúng và sạch. Đối chiếu CLI và schema từ mã đã nghiệm thu, kiểm từng URL được dùng, dẫn nguồn ngay tại claim. Bàn giao hash hai file, điều đã quan sát và những gì chưa xác minh. Không cần bằng chứng gọi model hoặc test sản phẩm vì nhiệm vụ chỉ chuẩn bị pilot. Nếu cần thay đổi code mới, chỉ ghi gap/đề xuất riêng cho Leader quyết định, không tự triển khai.
