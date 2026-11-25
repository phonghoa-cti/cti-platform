# W04 — Frontend làm song song Backend

Task `W04-ASSETS-FRONTEND`, CTI Frontend / Sol medium, một writer, không giao tiếp bot khác. Người dùng yêu cầu tăng tốc ngày 11/11 lúc 21:15; phần UI dựa hợp đồng đã chốt đủ độc lập để bắt đầu trước Backend hoàn tất.

Root: `$WORKSPACE`.

## Nguồn và ranh giới

- Backend đang làm `cti-w04-assets-local`, giữ nguyên request `9d5f3b39-1394-443d-a3d5-2b7d2ca0b20c`, không đọc file đang sửa để đoán hợp đồng, không chạm tree đó.
- Tạo tree riêng `cti-w04-assets-frontend`, branch `feat/w04-assets-frontend-20261111`, từ `cti-w02-local-integration@aeff542a20ecc6fe436a0884801fdd69ab0435f6`. Baseline này đủ UI/W02; không đợi/cherry-pick Backend chưa nghiệm thu. Nếu đích có sẵn, kiểm owner/HEAD/dirty và giữ chỉnh sửa cũ, không reset/xóa.
- Đọc AGENTS.md, docs/PROGRESS.md, docs/design/DESIGN.md, docs/specs/W04-tai-san.md trong baseline; nghiên cứu `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md` và hiệu chỉnh ưu tiên ở `PHONG-HOA-W04-IMPLEMENT-BRIEF-20261111.md`. Không nghiên cứu lại toàn dự án. Có câu hỏi hợp đồng thực sự chưa chốt thì nêu cụ thể, vẫn làm phần độc lập.
- Giữ thiết kế SOC console tối, màu/font/panel có sẵn; không redesign W02/W05. Dùng skill UI phù hợp trước edit; không cài công cụ mới chỉ để làm UI. Kiểm browser bằng bề mặt được cấp nếu cần; không tự mở browser khác/chiếm desktop. Backend không dùng browser trong nhiệm vụ hiện tại.

## Đích và luồng người dùng

1. Màn `/tai-san/mau` dùng nguồn dữ liệu tổng hợp, nhãn rõ “Dữ liệu mẫu — thay đổi chỉ trong phiên thử”. Hai tab Tên miền / Dải IP, bảng và thêm/sửa/xóa có xác nhận tên đối tượng. Công nghệ/từ khóa/CSV/phơi nhiễm chưa trong lát cắt, không hiển thị nút giả như đã hoạt động. Giữ trạng thái rỗng, loading, invalid, unauthorized/forbidden, unavailable, conflict tách biệt.
2. Dùng interface `AssetsDataSource` để view thay nguồn được, có provider mẫu và HTTP adapter `/api/assets` theo hợp đồng nghiên cứu + hiệu chỉnh. Lưu note, canonical value từ response; UI không tự tuyên bố canonical/đã lưu trước response. Form dùng label/focus/keyboard rõ, thông báo tiếng Việt; client chỉ validation tiện dụng, API vẫn là thẩm quyền. Không hard-code role trong client thành cơ chế bảo vệ.
3. Mutation POST/PUT/DELETE không tự retry, chống double-submit. Thành công mutation rồi GET refresh lỗi phải phân biệt “đã lưu, chưa tải lại” với “lưu thất bại”; chỉ retry GET. Timeout/mất kết nối sau mutation là kết quả chưa rõ, không tự gửi lại hoặc hiển thị thành công giả. Dùng version/expected_version, gặp409 giữ nội dung người dùng để họ so với bản mới, không tự ghi đè. Không retry vô hạn hoặc nuốt lỗi thành empty.
4. Cập nhật parser/view W02 nhận `asset_match` ở allowlisted/not_found theo hiệu chỉnh, giữ nguyên các invariant khác và strict extra-key/type/TLP/score checks. Cho phép riêng tên asset tới253, không nới source/related128. Với not_found có asset-match, giữ thông tin đó trong view thay vì mất khi đổi thành `{state:'not-found'}`. Hiển thị “Thuộc tài sản của bạn” kèm tên và “Chưa tìm thấy dữ liệu đe dọa” khi phù hợp; không gọi “an toàn”/“đã chặn”. Dùng 3 fixture tổng hợp tự tạo từ hợp đồng: allowlisted+asset, not_found+asset URL-path, found+asset. Ghi rõ chưa phải fixture chạy ra từ Backend; sẽ đối chiếu sau khi Backend trả kết quả.
5. HTTP adapter chỉ cùng origin, kiểm response chính xác/bounds/timeouts như W02. Không nhúng JWT/identity/roles giả vào production; giữ transport/header hợp đồng hiện có. Backend feature opt-in đang chưa được nối runtime; không tự sửa gateway/server hoặc bật `/tai-san` giả thành luồng thật. Route mẫu và test adapter là phạm vi nghiệm thu hiện tại.

## File được sửa

Chỉ trong tree mới:
- `portal/web/app/tai-san/mau/page.tsx` mới; nếu cần route hỗ trợ mẫu, giới hạn dưới `app/tai-san/mau/`.
- `portal/web/components/assets*.tsx`, `portal/web/data/assets*.ts` và fixture assets mới.
- `portal/web/data/ioc-lookup.ts`, `ioc-lookup-http.ts`, `portal/web/components/ioc-lookup.tsx`: chỉ mở rộng asset metadata/hiển thị theo hợp đồng, không refactor toàn bộ.
- `portal/web/app/globals.css`: bổ sung style assets có phạm vi, giữ token/layout W02/W05.
- `portal/web/tests/assets*.test.ts(x)`, bổ sung hai test ioc-lookup hiện có.
- Nếu cần bổ sung chuỗi ngôn ngữ trong file i18n có sẵn, chỉ khóa W04/asset label; bảo toàn VI/EN.
- `docs/PROGRESS.md` trong branch, `portal/web/README.md` chỉ hướng dẫn màn mẫu và giới hạn tích hợp.

Không sửa portal_api/core, tools/local_integration, package/lock/dependency, repo nguồn, RUNS hoặc plan. Ngoài allowlist báo Leader lý do, vẫn tiếp tục phần không bị chặn.

## Kiểm và trả kết quả

Test hành vi trước (RED→GREEN): form create/edit/delete confirmation, loading/error/403, conflict giữ input, no POST replay sau refresh lỗi, unknown mutation outcome, request cũ không ghi đè context mới; parser chấp nhận đúng ba asset states và vẫn từ chối payload sai. Không viết lại thuật toán chuẩn hóa core bằng JS chỉ để khớp test.

Dùng dependencies hiện có theo cách làm W02 đã chấp nhận; không cài vào tree nguồn. `npm test` một lần sau các test tập trung RED→GREEN, `npm run typecheck`, `npm run lint`, `npm run build`, `git diff --check`. Nếu baseline/toolchain có lỗi, báo lệnh/exit/nguyên nhân cụ thể, không sửa rộng ngoài task. Chỉ thêm kiểm browser khi có thể làm bằng bề mặt đã cấp: ít nhất màn mẫu và một luồng sửa/xóa; ghi viewport thật, không giả mobile bằng CSS. Browser bị chặn không chặn việc hoàn thành code/component checks, nhưng ghi UNVERIFIED rõ.

Trả commit cục bộ, base/HEAD, diff/status sạch, lệnh/exit/count, artifact và các giới hạn. Báo cáo root `PHONG-HOA-W04-ASSETS-FRONTEND-RESULT.md`; evidence root `w04-assets-frontend-evidence/`. Không push/PR/merge/deploy, gọi dịch vụ ngoài hoặc tự nối backend chưa nghiệm thu.

## Điều kiện nối

Leader nghiệm thu từng phần rồi giao một tree tích hợp từ hai SHA đã đạt: đối chiếu fixture backend với parser, bật store và gateway đúng quyền, nối màn thật, kiểm browser cùng một DB. Đây là phụ thuộc tích hợp, không phải lý do để UI mẫu/adapter và Backend phải làm tuần tự. Mốc W04 chỉ được gọi hoàn chỉnh theo lát cắt sau khi luồng thật đó đạt.
