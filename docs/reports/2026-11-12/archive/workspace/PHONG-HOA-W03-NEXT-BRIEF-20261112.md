# W03-NEXT — nghiên cứu lỗ hổng liên quan công nghệ

CTI Research làm trực tiếp, **research-only**, không code, không worker/bot con.
Root `$WORKSPACE`.
Base mới đã nghiệm thu **273196e2d23b36172d57cc61b289522786d61b2a**, tree **cti-w04-technology-integration**, chỉ đọc. Không sửa source/tree/ledger, không checkout/reset/cherry-pick. Kết quả nghiên cứu không tự là phép triển khai.

## Mục tiêu

Chọn lát cắt W03 nhỏ nhất hữu ích có thể kiểm cục bộ trước lab: công nghệ doanh nghiệp → danh sách CVE liên quan theo tên vendor/product → thứ tự ưu tiên rõ nguồn/giới hạn. Chuẩn bị contract và brief Backend/Frontend độc lập; Leader quyết định trước triển khai.

## Tận dụng cái đã có

Đọc AGENTS/PROGRESS đúng SHA, docs/specs/W03-lo-hong-anh-huong.md, api-portal.md mục /cves, W04-technology-local-contract.md; root PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md, PHONG-HOA-W04-TECHNOLOGY-RESEARCH-20261111.md và leader-w04-technology-integration-acceptance-20261112/ACCEPTANCE.md.
Tìm nghiên cứu F01/CVE/OpenCTI đã có và đúng ref/PR nếu cần, không xemmain là toàn bộ. Không làm lại Technology CRUD hoặc nghiên cứu CPE cơ bản đã có.

Baseline đã có TechnologyStore riêng, vendor/product trim+casefold (không NFKC/alias), software_version chỉ hiển thị. APItechnology có id/version/actor/audit, quyền IT/analyst/admin; W03 spec cho Leader đọc summary nhưng không mutate. API-portal cũ gộp technology vào assets đã bị contract W04 mới thay thế: không hồi sinh enum/storage cũ.

## Câu hỏi phải chốt bằng nguồn

1. OpenCTI Vulnerability/CVE connector có thực sự cung cấp vendor/product/KEV/EPSS/CVSS/published/vendor-advisory và liên kết sản phẩm theo dạng nào? Đọc docs/source/schema chính thức, ghi ref/ngày/URL. Không suy từ tên connector rằng đã có mapping dùng được. Nếu thiếu thì đề xuất normalized read port + fixture tổng hợp; live adapter là bước sau.
2. Nguồn CISA KEV, FIRST EPSS/CVSS: ý nghĩa, khoảnggiátrị, unknown/null, ngày thu thập, hạn KEV là thông tin nguồn (không tự coi deadline bắt buộc của SME), điều kiện tái sử dụng/dẫn nguồn. Phân biệt KEV=false với không có dữ liệu; không dùng điểm thiếu như0 khi mô tả.
3. Matching theo spec: chỉ vendor/product casefold exact, không regex/prefix/alias/CPE/range. Software_version hiển thị kèm “cần kiểm tra phiên bản”; không khẳng định cài đặt bị ảnh hưởng chỉ từ tên. Một CVE liên quan nhiều asset, nhiều phiên bản; định nghĩa dedupe và nguồn giải thích.
4. Priority KEV→EPSS→CVSS→mới hơn: missing/dateinvalid/tie ổn định/CVEID thứ tự; metricfinite/ranges/type; ngày cần deterministicclock để kiểm overdue.
5. Contract đề xuất GET /api/cves (query kev/status/asset/search/pagination chỉ phần cần cho lát cắt): exactDTO/nullable fields, bounds, nguồn/as_of/match_reason, lỗi/readunavailable/empty khác nhau, Leaderredaction/roles, snapshotConsistency khi technology bị sửa/xóa, payloadcap khớp limits. Chỉ fixture công khai/tổng hợp, không dữ liệu hạn chế.
6. Status SQLite/audit là tiêu chí W03 tiếp theo: đề xuất granularity CVE toàn doanh nghiệp hay cặp technology/CVE, lịch sử khi xóa/đổi công nghệ, optimisticversion, quyền, note và rollback. API-portal cũ chưa chốt các chi tiết này; nêu tradeoff và khuyến nghị, **không tự triển khai**. Ưu tiên đầu tiên read-only nếu nó giải phóng Backend/Frontend song song mà không tạo status giả hay nút ghi chưa hoạt động.
7. UI reuse DESIGN/tab/provider/W02pattern; tooltip tiếngViệt cho KEV/EPSS/CVSS, filter/ranking/empty/unavailable/403/summaryLeader; không redesign.

## Đầu ra

Root **PHONG-HOA-W03-RESEARCH-20261112.md**, evidence **w03-research-evidence/** nếu cần. Báo nguồn chính thức đã mở trực tiếp, phần reuse, phần thiếu/chưa biết, phương án khuyến nghị và giới hạn. Có bảng scope giai đoạnđầu/sau, contract đề xuất, acceptance matrix (dataquality/auth/matching/ranking/readfail/stalecontext), brief ngắn Backend Solmedium và Frontend Solmedium trên tree riêng, integrationgate.

Không tạo worktree hoặc sửa code/dependency/gateway/DB/ledger; không push/PR/merge/deploy/lab, không chạy OpenCTI/NVD/feed thật hoặc đọcsecret. Có thể duyệt tài liệu/source chính thức bằng công cụ web được cấp. Không tự yêu cầu người dùng cấp quyền nếu có thể hoàn tất nghiên cứu trong phạmvi này; ghi rõ unknown đểLeader chọn.

Done khi có quyết định có nguồn và contract đủ cho Leader review/chốt, không gọi báo cáo là test/runtime/implementation.
