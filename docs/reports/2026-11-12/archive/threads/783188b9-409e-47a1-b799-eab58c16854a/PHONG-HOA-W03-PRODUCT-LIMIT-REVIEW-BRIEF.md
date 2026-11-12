# W03/W04 — đối chiếu giới hạn tên sản phẩm

CTI Research: nghiên cứu có nguồn, chỉ đọc, một báo cáo ngắn, không code/worker con/browser demo. Đây là quyết định kỹ thuật trong phạm vi local đã giao, không chờ người dùng chọn giới hạn.

TREE=$WORKSPACE\cti-w03-status-integration
PIN=d09929311b4b6447aac8b2ec6adac5999beda25d
OUT=$THREADS\783188b9-409e-47a1-b799-eab58c16854a
Engineer đang kiểm browser trong TREE: chỉ dùng git show PIN:path hoặc đọc file đã cố định; không chạy test sửa cache/DB hay ghi source, không đọc tree khác đang làm.

Đọc AGENTS, docs/PROGRESS; docs/specs/W03-read-local-contract.md (affected vendor/product128), W03-status-local-contract.md, W04-technology-local-contract.md (product256); portal_api/cves.py:_product, cves_status.py:_validate_context, technologies.py; parser UI liên quan; nghiên cứu W03/W04 đã có ở thư mục cha TREE và OUT/PHONG-HOA-W03-STAGE-A-REVIEW.md. Lỗi đã tái hiện và capture nằm tại $THREADS\662556d5-bef1-4bf9-b1f8-ce0ad295308c\w03-status-evidence-stage-a\wire-fixtures\product-256-repro.json.

Trả lời: (1) 128 có lý do từ nguồn/format hay chỉ lựa chọn local? (2) technology hợp lệ256 có thể tạo relation/status hợp lệ theo hợp đồng hiện tại hay phải coi chưa được hỗ trợ? Phân biệt fixture vi phạm dataset contract với lỗi người dùng bình thường. (3) Khuyến nghị giải pháp nhỏ nhất thống nhất luồng và rủi ro tương thích, không hạ cổng kiểm chỉ để ghi PASS. Đối chiếu nghiên cứu/nguồn chính thức đã có; chỉ tìm nguồn mới khi cần, không gửi dữ liệu hạn chế ra ngoài.

Đầu ra duy nhất OUT/PHONG-HOA-W03-PRODUCT-LIMIT-REVIEW-RESULT.md, tối đa khoảng2 trang: nguồn/link hoặc ref:path:line, phần tái dùng/chưa rõ, khuyến nghị, file allowlist cần sửa và ca kiểm 128/129/256/257, Unicode/code point, vendor128, body cap/pagination và parser nếu liên quan. Nếu đề xuất đổi product lên256, nêu chính xác contract/capture gate đang kỳ vọng503 cần đổi sau fix; không coi chỉ đổi một dòng loader là hoàn tất. Không triển khai, không sửa sổ, không push/PR/merge/deploy hoặc tạo thêm scope S2.
