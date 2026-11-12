# W05-LOCAL-INTEGRATION-NEXT — nghiên cứu cách chạy và brief triển khai

Chủ sở hữu: CTI Engineer, Sol medium; tự làm, không giao bot/agent khác. Đây là nhiệm vụ đọc/nghiên cứu và viết đúng hai tài liệu, chưa triển khai. Leader đã nghiệm thu client và API riêng; ưu tiên tiếp theo là một luồng browser → API → SQLite tổng hợp chạy cục bộ, trước corpus/model thật. Không nghiên cứu lại metric AI hoặc API contract đã chốt.

## Nguồn và hiện trạng

Workspace: `$WORKSPACE`.

- Backend: `cti-w05-backend`, SHA `02b0efe09ed9f3ac0bea63ba5ba5cc43663aac04`. Đọc AGENTS.md, docs/PROGRESS.md, docs/specs/api-portal.md, portal_api/settings.py/app.py/auth.py (hoặc đúng tên module hiện có), demo/tests JWT tổng hợp và dependency manifest. Không sửa tree.
- UI: `cti-portal-web`, SHA `a791a3f2be19b4c1593f82706c47b5dca97ab51a`. Đọc AGENTS.md, portal/web/README.md, next config/package, data/api-client.ts, cùng PHONG-HOA-UI-API-RESULT.md. Đọc exact SHA bằng git show nếu HEAD đổi; không sửa tree.
- Tái sử dụng PHONG-HOA-W05-API-RESEARCH.md, PHONG-HOA-W05-API-IMPLEMENTATION-BRIEF.md, PHONG-HOA-W05-API-LEADER-ADDENDUM.md và PHONG-HOA-UI-API-INTEGRATION-BRIEF.md tại workspace.
- `/duyet` gọi URL tương đối `/api/drafts*`, hiện404 do chưa routing. `/duyet/mau` chỉ mẫu và không gọi API. API kiểm Origin đúng bằng PORTAL_ORIGIN; settings hiện chỉ nhận HTTPS. Local UI trước chạy HTTP127.0.0.1:3002. JWT phải xác minh chữ ký/issuer/audience/expiry và role server-side, không thay bằng Principal giả.

## Câu hỏi phải giải quyết

So sánh tối đa ba phương án dựa nguồn chính thức còn phù hợp (Next.js rewrite/proxy/HTTPS dev, FastAPI proxy, MDN Origin, Cloudflare Access JWT theo phần liên quan). Chọn một cách nhỏ nhất có thể triển khai/kiểm trong môi trường được cấp; ghi rõ điểm chưa biết. Kiểm dependency/runtime đã có bằng lệnh đọc; không cài mới.

1. Cách đưa UI và `/api/drafts*` về cùng scheme/host/port và giữ method/path/query/body/status/Origin/cache. Nếu dùng proxy, không viết lại Origin để lách403; không nuốt Set-Cookie/header lỗi hay trả cache dữ liệu người khác.
2. Giải quyết HTTP local so với HTTPS hiện tại mà không tắt TLS validation, bỏ kiểm Origin hoặc thay trust store. Nếu đề xuất chế độ HTTP test chỉ loopback, phải tách rõ khỏi cấu hình production, nêu thay đổi cần Leader review, invariant fail-closed và phép thử chứng minh không dùng nhầm. Đây là phương án nghiên cứu, chưa được sửa policy. Không dùng workaround giả HTTPS hoặc chấp nhận chứng chỉ bằng cách bỏ kiểm tra.
3. Harness tổng hợp dùng JWT ký thật/JWKS fixture và DB tạm. Private key/token không xuất vào browser/log/báo cáo; browser không tự khai role hoặc impersonate qua header. Có thể tái sử dụng phần fixture đang có; mô tả auth mô phỏng khác Cloudflare SSO thật ở đâu. Nêu rõ các danh tính test và cách kiểm403/self-review/401/409.
4. Bề mặt browser tích hợp được cấp là nơi kiểm UI. Nghiên cứu khả năng hiện có/metadata, không mở browser khác, không điều khiển trình duyệt riêng của người dùng, không giả viewport. Nếu HTTPS/loopback không chạy được trên bề mặt này, ghi blocker chính xác và phần integration có thể kiểm qua HTTP client; không gọi đó là browser E2E.
5. Một người sửa một tree. Đề xuất base/path/branch riêng cho bước triển khai; tôn trọng no-merge và không sửa các tree đã nghiệm thu. Nếu cần ghép artifact UI/API, nêu phương pháp và provenance exact SHA để Leader quyết định, không thực hiện bây giờ.

## Hai đầu ra được phép

Tại workspace trên:

- `PHONG-HOA-LOCAL-INTEGRATION-RESEARCH.md`: so sánh tối đa3 cách, nguồn chính thức/phiên bản/ngày đọc, phần tái sử dụng, đề xuất và giới hạn. Khoảng100–180 dòng là đủ.
- `PHONG-HOA-LOCAL-INTEGRATION-IMPLEMENTATION-BRIEF.md`: tự đủ để một worker thực hiện sau Leader duyệt kỹ thuật. Exact refs/tree/scopes, interface/config, vòng đời tiến trình loopback, cleanup chỉ tiến trình/DB do harness tạo, acceptance matrix và lệnh kiểm. Không đặt secret thật hoặc private key vào file.

Acceptance cần bao phủ: list/detail/approve/reject với audit DB thật tổng hợp; không tự duyệt/không đủ quyền; JWT sai/hết hạn; Origin thiếu/sai; version conflict; POST thành công nhưng refresh lỗi vẫn giữ UI success; sample không gọi API; no-store/error; không double-submit; dừng sạch tiến trình do mình tạo. Tách unit/in-process, HTTP integration, browser tổng hợp và Cloudflare/lab thật.

Không sửa repo/RUNS/skill/review; không mở listener, tạo chứng chỉ, đổi trust store/quyền, install, cloud/model/secret, lab, push/PR/merge/deploy. Chỉ đọc nguồn online công khai và cấu hình dự án không chứa secret. Báo exact output/hash, refs đọc, lệnh đã chạy và chưa kiểm; không báo nghiên cứu là implementation.
