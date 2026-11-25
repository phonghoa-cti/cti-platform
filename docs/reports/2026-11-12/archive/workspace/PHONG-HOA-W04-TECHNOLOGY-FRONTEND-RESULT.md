# Kết quả W04-TECHNOLOGY-FRONTEND

## Kết luận

**PASS cục bộ.** Đã thêm tab Công nghệ CRUD mẫu theo DESIGN hiện có, provider typed/fixture tách riêng và HTTP adapter strict dùng fetch giả. Chỉ `/tai-san/mau` được inject provider công nghệ; `/tai-san` thật vẫn giữ domain/CIDR và không xuất hiện tab Công nghệ.

- Base bắt buộc: `8a767314b654d39c1ddc2995b7919c44a5b7027a`.
- Branch: `feat/w04-technology-frontend-20261111`.
- Commit/HEAD: `2419b29656092edcf2bb20b0d7c62a12fa0774c0` — `feat(portal): add sample technology assets`.
- Diff `base..HEAD`: 13 file, 1.337 dòng thêm, 5 dòng xóa.
- Trạng thái sau commit: sạch (`git status --short` không có output).

## Phạm vi đã làm

- `portal/web/data/technologies.ts`: `TechnologyItem/Input/Provider`, fixture hữu hạn có nhãn dữ liệu tổng hợp, CRUD/duplicate/stale và defensive copy. Fixture chỉ mô phỏng duplicate ASCII đã định trước; Backend vẫn là thẩm quyền `casefold`.
- `portal/web/data/technologies-http.ts`: wire exact keys với `software_version` là chuỗi và `version` là strict safe integer; parser UTC `Z`, code-point bounds, actor 512 pass/513 fail, body/content-type/UTF-8/size strict; chỉ map đúng status/code contract.
- `portal/web/components/technology-panel.tsx`: form nhà cung cấp/sản phẩm/phiên bản phần mềm/ghi chú; bảng tách nhãn **Phiên bản phần mềm** và **Lần sửa**; loading/rỗng/invalid/401/403/409/503; xác nhận xóa và optimistic version.
- Mutation bất định không retry, khóa thao tác cho tới khi GET đối soát xong. Mutation đã commit nhưng refresh lỗi giữ notice đã lưu và chỉ cho GET retry.
- Context ownership vô hiệu callback create/update/delete và refresh cũ sau đổi tab/provider/unmount; reset `saving/loading/form/notice` của provider cũ; quay lại cùng tab domain kích hoạt GET thay vì replay mutation.
- `assets-sample-client.tsx` inject hai provider mẫu ổn định cho `/tai-san/mau`; `AssetsHttpClient` của `/tai-san` không nhận technology provider.
- VI/EN có cấu trúc dịch; dùng lại toàn bộ class/tab/bảng/form/focus/responsive của thiết kế incumbent, không sửa CSS/global layout/DESIGN.
- `docs/PROGRESS.md` ghi rõ bằng chứng cục bộ và giới hạn chưa kiểm.

## RED → GREEN

Tests được viết trước mã sản phẩm. Các RED hành vi đã quan sát: 2 suite thiếu module; 5 parser-field fail; 3 provider-switch saving fail; 1 provider-removal fail; 1 unknown-reconcile-lock fail; 1 same-tab reload fail. Tất cả đã GREEN; chi tiết tại `w04-technology-frontend-evidence/RED-GREEN.md`.

## Kiểm chứng tươi

| Lệnh | Exit | Count/kết quả |
|---|---:|---|
| `npm test -- --run tests/technologies.test.ts tests/technologies-http.test.ts tests/technology-panel.test.tsx tests/assets-app.test.tsx tests/assets-http.test.ts tests/assets-http-client.test.tsx` | 0 | 6/6 file, 111/111 test pass. |
| `npm run typecheck` | 0 | Không lỗi TypeScript. |
| `npm run lint` | 0 | Không lỗi/cảnh báo ESLint. |
| `npm run build` | 0 | Compile/type/static generation thành công; 9/9 static pages. |
| `git diff --cached --check` | 0 | Không lỗi whitespace. |
| `git status --short` sau commit | 0 | Không output; sạch. |

Evidence: `w04-technology-frontend-evidence/RED-GREEN.md` và `w04-technology-frontend-evidence/VERIFICATION.md`.

## Nghiệm thu độc lập sau commit

CTI Frontend đã đọc trực tiếp diff `8a767314..2419b296`, kiểm allowlist và chạy lại trên chính HEAD:

- Focused technology + assets: **111/111 PASS**, exit `0`.
- `npm run typecheck`: exit `0`; `npm run lint`: exit `0`.
- `npm run build`: exit `0`, compile/type/static generation **9/9** trang, gồm `/tai-san` và `/tai-san/mau`.
- `git diff --check 8a767314..HEAD`: exit `0`; `git status --short`: sạch.
- Không có đường dẫn `portal_api`, gateway, core, deploy hoặc `PHONG-HOA-RUNS` trong diff.
- Review không phát hiện lỗi nghiêm trọng trong phạm vi; vẫn giữ nguyên mọi mục UNVERIFIED bên dưới vì không chạy API thật, browser hoặc lab.

## Trạng thái tiêu chí

### PASS

- Wire TechnologyView exact keys; không có `version_id`; `software_version` và record `version` tách nghĩa.
- Parser strict integer/timestamp/code point/created_by/body/content-type/error mapping.
- CRUD mẫu, duplicate/stale/forbidden, loading/empty/invalid/401/403/409/503.
- Không retry/double-submit mutation; committed-refresh và unknown-mutation chỉ GET recovery.
- Callback/refresh cũ không ghi state/notice/loading vào context mới.
- `/tai-san/mau` opt-in technology; `/tai-san` thật giữ nguyên.
- Focused tests, typecheck, lint, build, diff-check và commit sạch.

### FAIL

- Không có tiêu chí trong phạm vi bị FAIL.

### UNVERIFIED / giới hạn

- Fixture và fetch đều là tổng hợp/mock cục bộ; fixture không phải bộ chuẩn hóa Unicode production và không thay quyền/casefold Backend.
- Chưa nối technology route thật, gateway hoặc database Backend; chưa kiểm API/auth thật.
- Theo brief không chạy browser, network, lab, Cloudflare/JWKS/HTTPS, OpenCTI hoặc production.
- Không chạy full 222/W02 suite vì không sửa W02/domain adapter; focused assets regression đã đạt.

## Học thêm

- **Optimistic concurrency:** client gửi phiên bản bản ghi đã đọc; server từ chối nếu người khác đã sửa trước, tránh ghi đè im lặng.
- **Context ownership:** mỗi request thuộc một tab/provider cụ thể; callback cũ bị bỏ qua khi người dùng đã chuyển ngữ cảnh.
- **Unknown mutation outcome:** mất phản hồi không chứng minh thao tác thất bại; cách an toàn là GET đối soát, không tự gửi lại POST/PUT/DELETE.
- **Unicode code point:** một ký tự hiển thị có thể dùng hai UTF-16 code unit; `Array.from` phù hợp hơn `.length` cho bound của hợp đồng này.

## Rework F1–F3 ngày 12/11/2026

**PASS cục bộ.** Rework bắt đầu từ HEAD sạch `2419b29656092edcf2bb20b0d7c62a12fa0774c0` và kết thúc ở commit `cfb612f05f6ae57952362580e35ad59d2aff0a3f` (`fix(portal): harden technology recovery`). Diff rework gồm 6 file, 221 dòng thêm và 20 dòng xóa; worktree sau commit sạch.

- F1: GET list có cap hữu hạn `18.700.011` byte, tính từ 1.000 DTO tối đa kể cả surrogate JSON escape; mutation/error vẫn giữ cap 1 MiB. Regression bao phủ Content-Length/stream không header, sát/vượt cap và danh sách 1.000 DTO; 1.001 vẫn bị parser từ chối.
- F2: notice committed giữ nguyên qua mọi GET retry loading/failure và chỉ clear sau GET thành công, cho create/update/delete; mutation count không tăng.
- F3: panel cùng provider giữ pending/unknown qua rời/quay lại tab; GET thành công sớm khi mutation còn pending không mở khóa. Provider mới reset độc lập; callback/notice cũ vẫn bị context guard loại bỏ; không replay mutation và không thêm persistence qua full reload.
- Probe/fixture Leader không bị sửa; SHA256 đã đối chiếu đúng hợp đồng.

### RED → GREEN rework

- Probe base: exit `1`, 4/4 fail.
- F1 tests mới trước code: exit `1`, 3 fail/35 pass.
- F2/F3 tests mới trước code: exit `1`, 4 fail/2 pass/18 skipped.
- Probe cuối: exit `0`, 4/4 pass.
- Focused cuối: exit `0`, 6/6 file và 120/120 test pass.

### Kiểm chứng rework

| Lệnh | Exit | Count/kết quả |
|---|---:|---|
| Probe Leader nguyên bản từ cwd nghiệm thu | 0 | 1/1 file, 4/4 pass. |
| Focused technology + assets | 0 | 6/6 file, 120/120 pass. |
| `npm run typecheck` | 0 | Không lỗi TypeScript. |
| `npm run lint` | 0 | Không lỗi/cảnh báo ESLint. |
| `npm run build` | 0 | Build thành công; 9/9 trang tĩnh. |
| `git diff --check 2419b296..HEAD` | 0 | Không lỗi whitespace. |
| `git status --short` | 0 | Không output; sạch. |

Raw log và bảng đối chiếu: `w04-technology-frontend-evidence/rework-*.log` và `w04-technology-frontend-evidence/REWORK-VERIFICATION.md`.

### Trạng thái rework

- **PASS:** F1–F3, 4 probe độc lập, focused regression, typecheck, lint, build, diff-check, commit sạch.
- **FAIL:** không có tiêu chí trong phạm vi bị fail.
- **UNVERIFIED:** dữ liệu vẫn là fixture/fetch mock cục bộ; chưa tích hợp API/gateway thật, browser, lab hoặc production. Không thay đổi wire/design/phạm vi và không chạy full suite ngoài focused được yêu cầu.

### Nghiệm thu độc lập rework

CTI Frontend đã đọc trực tiếp delta `2419b296..cfb612f0` và chạy lại trên chính commit: probe Leader nguyên bản **4/4**, focused **120/120**, typecheck/lint/build/diff-check đều exit `0`, build **9/9** trang và worktree sạch. Hash probe/fixture vẫn đúng; diff không chạm Backend, gateway, dependency, route thật hoặc `PHONG-HOA-RUNS`. Các giới hạn UNVERIFIED ở trên không đổi.
