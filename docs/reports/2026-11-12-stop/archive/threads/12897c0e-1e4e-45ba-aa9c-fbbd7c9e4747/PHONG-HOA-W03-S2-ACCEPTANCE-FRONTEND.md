# W03-S2 — nghiệm thu Backend và giao Frontend

Ngày 12/11/2026. ROOT = $WORKSPACE.

## Nghiệm thu Backend cục bộ

Chấp nhận W03-STATUS-S2-BACKEND tại **3e6934037879860c8abb5f6d797381dbe3225633**, branch feat/w03-status-s2-backend-20261112. Leader đối chiếu HEAD/tree sạch, diff R1 từ 82f8a6acc8f357645f7105a2cc84b46bf58f4e4f đúng ba file +122/-9. Report R1 trong thư mục này có SHA256 84E125691F4578DA7980F6DA8353B7E7E4FA2DA835419BAEA126154F662444A1, khớp báo cáo nhận về.

Leader đọc decoder/tests và raw evidence, chạy mới probe gốc tại leader-r1-verify: control200 và bảy malformed cursor422 trước dependency, DB không đổi, exit0. Chạy mới bốn test drift riêng status/dataset/Technology/UTC-date: cả bốn qua, exit0. Diff-check committed delta exit0; cuối kiểm HEAD và tree không đổi. Raw output/result tại leader-r1-verify cạnh tài liệu này. Không chạy lại toàn suite: 138 test và Ruff/format là bằng chứng Backend đã cung cấp và đã đọc, không phải số test Leader vừa chạy. RED gốc đã tái hiện ở review trước; log RED worker là bản tổng hợp lỗi, không suy thành transcript đầy đủ.

Giữ nghiệm thu phần candidate đã review trước ở PHONG-HOA-W03-S2-REVIEW-R1.md: quyền/DTO/snapshot/không ghi DB được đối chiếu với các kiểm hiện có, lần này tập trung phần thiếu R1 và drift. Chỉ nghiệm thu API/test trong tiến trình cục bộ, dữ liệu tổng hợp. Chưa chứng minh gateway/browser S2, feed thật, OpenCTI, Cloudflare/JWKS/HTTPS, lab hoặc production. Bốn test STIX thiếu validator vẫn là giới hạn môi trường của full suite cũ. Không đụng process/temp cũ đang bị chặn cleanup.

## Nguồn và lựa chọn cho bước tiếp

Tái sử dụng nghiên cứu S2 đã nghiệm thu và quyết định ngày 12/11 tại $THREADS\c10d07c4-917a-4f70-bd33-56abccf3066d\PHONG-HOA-W03-S2-DECISION-AND-BACKEND-BRIEF.md. Đọc contract chính xác và fixture từ commit trên, cùng docs/design/DESIGN.md, W03 spec, docs/PROGRESS.md và AGENTS.md. Nguồn SQLite/OWASP/CISA và giới hạn nằm trong nghiên cứu/decision đã chốt; không cần chọn lại API hay nghiên cứu lại cùng vấn đề.

Mục tiêu: người dùng lọc CVE theo trạng thái xử lý và hiểu số cần xử lý/quá hạn, giữ thiết kế và luồng hiện có. Chọn adapter riêng cho GET /api/cves/status-view và mở rộng giao diện hiện tại; không đổi nghĩa parser W03-R, không dựng lại portal. Frontend không tự tính dữ liệu tổng hợp bằng các trang đã tải và không gọi S1 cho từng dòng để suy ra trạng thái.

## Giao W03-STATUS-S2-FRONTEND

Một CTI Frontend/Sol medium trực tiếp, không worker lồng. Tạo tree riêng ROOT\cti-w03-status-s2-frontend, branch feat/w03-status-s2-frontend-20261112 từ **3e6934037879860c8abb5f6d797381dbe3225633**. Nếu đã có tree/dirty, giữ nguyên và báo, không reset. Không sửa tree Backend.

Đầu vào contract: docs/specs/W03-status-view-local-contract.md; fixtures portal_api/tests/fixtures/w03-status-view-detail.json, w03-status-view-leader.json, w03-status-view-error.json. Giữ các fixture Backend chỉ đọc. Tái dùng portal/web/components/cve-app.tsx, cve-status-panel.tsx, cve-http-client.tsx, cve-sample-client.tsx và data/cves.ts, cve-status.ts. Phạm vi sửa portal/web/data/cves-status-view* mới; các file data/cves*, components/cve* liên quan tối thiểu; style W03 hiện có; tests/fixtures W03-S2 mới; docs/PROGRESS.md. Không sửa backend/gateway/lockfile/dependencies/auth hoặc chức năng W02/W04/W05. Không redesign.

### Hành vi bắt buộc

1. HTTP adapter GET cùng origin /api/cves/status-view, chỉ nhận 200 đúng schema; kiểm đúng cả detail/summary/error wire và bounds. Không thêm identity header, không fallback sample, không tự retry. Giữ W03-R parser/provider/hợp đồng cũ hoạt động. Dùng fixtures đã chốt để kiểm wire, không bản JSON tự đoán thiếu field.
2. Detail có bộ lọc Tất cả/Chưa ghi nhận/Mới ghi nhận/Đang xử lý/Đã xử lý/Không ảnh hưởng/Cần rà soát tương ứng absent/unset/open/patching/patched/not_affected/review_required. Nếu nhãn trạng thái S1 hiện có khác, tái dùng nhãn đó nhất quán. Status theo từng công nghệ của CVE; một CVE nhiều công nghệ phải cho thấy trạng thái riêng, không gộp thành một trạng thái gây hiểu nhầm. review_required là cờ độc lập, vẫn hiển thị cùng persisted status. Status null không có nghĩa đã an toàn.
3. Leader-only summary không hiển thị bộ lọc asset/status, không gửi hai query key này, không gọi technology/S1 history/detail hoặc dựng metadata relation bị lược. Dùng response.view để chặn rò dữ liệu khi đổi quyền; không suy quyền từ trường tự đặt trong browser. Mixed role dùng detail theo response Backend.
4. Hiển thị matched_cves, kev_cves, actionable_cves, overdue_kev_cves, as_of_date đúng response. Nói rõ phạm vi các bộ đếm theo bộ lọc cơ sở trước lọc trạng thái và phân trang; ngày theo UTC do API trả. Ghi ngắn trạng thái do người dùng ghi nhận chưa chứng minh đã vá; hạn KEV tham khảo không phải nghĩa vụ pháp lý của SME. Nhãn sample/API rõ ràng, không gọi dữ liệu mẫu là feed thật.
5. Đổi query/status/asset/kev hoặc quyền phải bỏ chuỗi trang cũ; stale response không được ghi đè lựa chọn mới, giữ khóa pagination theo đúng request. 409 status_snapshot_changed bỏ cursor/danh sách cũ và cho tải lại trang đầu rõ ràng; không ghép hai snapshot. 401/403/404/422/503/network và empty/loading có nội dung phù hợp. Có thao tác tải lại GET cho số tổng hợp/trạng thái đã đổi.
6. Giữ nguyên an toàn S1: unknown POST không tự gửi lại, khóa đang chờ/khôi phục không bị mất do thay provider hoặc remount. Sau lưu S1 đã được xác nhận, phải đánh dấu dữ liệu danh sách cũ và cho tải lại bằng GET; ưu tiên nút tải lại rõ ràng để không mở rộng vòng đời mutation. Không tuyên bố danh sách đã cập nhật khi chưa đọc thành công. Mọi callback mới chỉ báo confirmed success, không biến lỗi mạng thành thành công.
7. Giữ bố cục/kiểu chữ/màu theo thiết kế hiện tại, nhãn tiếng Việt và keyboard/accessibility sẵn có. Không tự đổi màn hoặc làm mới mỹ thuật ngoài phạm vi.

### Kiểm và đầu ra

Viết test hành vi trước sửa; RED/GREEN cho các điểm mới có rủi ro. Test adapter exact wire detail/leader/errors; schema sai; không identity/fallback/retry; filter reset; multi-relation/status unset/stale; summary đúng scope; cursor409 và race khi đổi filter; role chuyển summary không leak; S1 unknown/lock và confirmed save rồi GET refresh. Tái dùng kiểm cũ thay vì viết bản sao. Chạy vitest phần W03/S1 liên quan, npm run typecheck, npm run lint, npm run build tuần tự, git diff --check BASE..HEAD. Không chạy lại Backend/full suite/browser cũ. Nếu có lỗi môi trường, ghi lệnh và nguyên nhân, không cài/chuyển công cụ ngoài brief.

Đây là nghiệm thu component/adapter; không đòi truy cập browser trong task này. Engineer sẽ nối gateway và kiểm browser sau hai đầu vào được Leader nghiệm thu. Không nhận test DOM là bằng chứng browser thật. Commit cục bộ/tree sạch; trả SHA, delta, lệnh/exit/count và raw output nguyên vẹn.

Báo cáo ở $THREADS\12897c0e-1e4e-45ba-aa9c-fbbd7c9e4747\PHONG-HOA-W03-S2-FRONTEND-RESULT.md; evidence ở w03-s2-frontend-evidence cạnh đó. Không sửa RUNS. Không push/PR/merge/deploy, chi tiền, quyền truy cập, lab/live feed/LLM thật/secret. Tối đa hai lần cùng nguyên nhân lỗi rồi trả blocker cụ thể.
