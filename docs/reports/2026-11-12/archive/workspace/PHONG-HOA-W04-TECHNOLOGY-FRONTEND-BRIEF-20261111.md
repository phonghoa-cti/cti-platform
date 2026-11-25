# W04-TECHNOLOGY-FRONTEND — độc lập Backend

CTI Frontend, một Sol medium trực tiếp, không giao bot/worker khác. Root `$WORKSPACE`.

## Mục tiêu/base

Thêm tab Công nghệ theo DESIGN hiện có vào màn tài sản mẫu, provider thay được và HTTP adapter strict/test fetch giả lập theo **`PHONG-HOA-W04-TECHNOLOGY-CONTRACT-20261111.md`**. Không chờ Backend; không tự đổi wire. `software_version` chuỗi, `version` số bản ghi; JSON không có version_id. Đọc nghiên cứu và contract Leader, AGENTS/PROGRESS/design/spec trên đúng ref.

Tree mới `cti-w04-technology-frontend`, branch `feat/w04-technology-frontend-20261111`, base accepted `8a767314b654d39c1ddc2995b7919c44a5b7027a`. Không sửa source/integration/Backend tree; không lấy code Backend chưa nghiệm thu.

## Phạm vi và trải nghiệm

- File mới `portal/web/data/technologies.ts`, `technologies-http.ts`, component/panel technology, fixture/test tương ứng; chỉnh `components/assets-app.tsx` tối thiểu để có tab khi được cung cấp technology provider, có thể thêm sample client wrapper; `app/tai-san/mau/page.tsx`, messages vi/en và mục riêng docs/PROGRESS nếu cần.
- Không mở rộng domain `AssetType` thành technology, không thay W02/domain HTTP adapter hoặc model cũ. Technology provider/item/input riêng; có thể dùng AssetDataError semantic hiện có. Không sửa DESIGN/global layout/CSS/dependency/backend/gateway/runner/RUNS/plan.
- Route `/tai-san/mau` inject provider công nghệ mẫu; `/tai-san` HTTP hiện hữu giữ nguyên đến lượt integration. Không trộn technology giả vào trang dữ liệu thật. HTTP adapter mới chỉ kiểm với fixture, chưa wiring gateway thật.
- Tab Công nghệ: form nhà cung cấp/sản phẩm/phiên bản phần mềm/ghi chú; bảng phân biệt "Phiên bản phần mềm" và "Lần sửa"; sửa/xóa có xác nhận/optimistic version. Theo màu/khoảng cách/tab/font sẵn có, không redesign.
- Trạng thái loading/rỗng/invalid/401/403/409/503; committed-refresh giữ đã lưu + GET retry; unknown-mutation chưa rõ kết quả + GET đối soát, không replay/double-submit. Chuyển tab, đổi provider hoặc unmount không cho request cũ ghi dữ liệu/notice/loading vào context mới, gồm lỗi refresh sau mutation.
- Input frontend chỉ hỗ trợ nhập; Backend là thẩm quyền canonical/casefold/quyền. Không viết thư viện casefold mới để giả đồng nhất Python. Provider mẫu dùng fixture hữu hạn được nêu rõ; Unicode identity/duplicate đặc biệt dùng phản hồi backend tổng hợp định trước trong test; không tuyên bố fixture là bộ chuẩn hóa production.
- Parser exact keys/safe integers/timestamp/code point bounds/created_by512 như contract; malformed/truncated/oversize/content-type/error lạ với mutation → unknown, GET→unavailable. Map đúng cặp status/code; không retry mutation kể cả timeout.

## Kiểm và bàn giao

RED→GREEN cho tab/provider/HTTP: CRUD/duplicate/stale/forbidden, software vs record version, actor512/513, Unicode code point bounds, invalid/unknown response, no replay, double submit, create/update/delete callback và refresh cũ sau switch/provider/unmount. Regression tests domain/CIDR cũ phải giữ. Chạy focused technology+assets tests, typecheck/lint/build, diff-check; không lặp full222/W02 suite không bị chạm.

Dùng dependency local đã có (copy nếu cần như baseline); không cài hoặc sửa lock. Không browser trong task độc lập này; bàn giao để Leader/Engineer kiểm sau tích hợp. Root `PHONG-HOA-W04-TECHNOLOGY-FRONTEND-RESULT.md`, evidence `w04-technology-frontend-evidence/`; commit/base/diff/exit/count/clean status và giới hạn fixture/HTTP mock rõ. Không push/PR/merge/deploy/lab/secret.
