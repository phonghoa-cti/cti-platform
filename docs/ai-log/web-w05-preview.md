# AI log — WEB-W05-PREVIEW

Ngày kiểm: 10/11/2026. Phạm vi: `portal/web/**`, chỉ đọc ba fixture tổng hợp X01.

## Nguồn và lựa chọn

- [Next.js support policy](https://nextjs.org/support-policy): chọn Next.js `16.4.6`, nhánh 16.x Active LTS;
  dùng App Router và static prerender, không beta.
- [React versions](https://react.dev/versions) và [versioning policy](https://react.dev/community/versioning-policy):
  chọn React/React DOM `19.3.1`, stable latest channel.
- [Tailwind CSS 4.3](https://tailwindcss.com/blog/tailwindcss-v4-3): chọn `tailwindcss` và
  `@tailwindcss/postcss` `4.3.5`.
- TypeScript `6.0.3` thay vì 7.0.2 vì `typescript-eslint` đi cùng `eslint-config-next 16.4.6` chưa hỗ trợ
  TypeScript 7; đây là phiên bản ổn định tương thích với cổng lint thực tế.
- Dùng lại trực tiếp token, mật độ, panel, tag và focus của `docs/design/DESIGN.md`. Không thêm shadcn/ui vì repo
  chưa có bộ component để tái sử dụng và lát cắt chỉ cần component nhỏ; không thêm chart/auth.

## TDD và kiểm chứng

- Đỏ: `frontend-evidence/red-test.log` — 3 suite thất bại vì adapter/evidence/component chưa tồn tại.
- Xanh: `npm test` — 4 file, 11 test đạt.
- `npm run typecheck`, `npm run lint`, `npm run build` đều exit 0 ở lần kiểm cuối.
- Trình duyệt thật cổng 3002: `/` chuyển 307 tới `/duyet`; chọn draft 2 và 1; evidence emoji nhận focus đúng;
  VI/EN hoạt động; không có link; nút duyệt vô hiệu. Ảnh full-page ở `frontend-evidence/`.
- Giới hạn: bề mặt trình duyệt cấp sẵn là 1280×720 và không có điều khiển viewport; 360 px và 1440 px chỉ được
  kiểm bằng CSS responsive/static review, chưa có ảnh trình duyệt thật nên ghi **UNVERIFIED**.

Không có request ghi, auth giả, OpenCTI giả, `dangerouslySetInnerHTML`, endpoint API hay secret.

## Rework R1 — lỗi sao chép (11/11/2026)

- [MDN Clipboard.writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText): Promise chỉ
  resolve sau khi clipboard đã được cập nhật; API chỉ dùng trong secure context và có thể từ chối bằng
  `NotAllowedError`.
- [W3C Clipboard API, writeText](https://www.w3.org/TR/clipboard-apis/#dom-clipboard-writetext): thuật toán từ
  chối Promise bằng `NotAllowedError` khi kiểm tra quyền ghi thất bại.
- TDD đỏ: `frontend-evidence/clipboard-red-test.log` — 2/5 test thất bại và Vitest bắt 2 unhandled rejection
  khi API không có hoặc quyền bị từ chối, exit 1.
- TDD xanh: `frontend-evidence/clipboard-green-test.log` — 5/5 test đạt, exit 0. Test kiểm API không có,
  Promise reject, chỉ báo thành công sau resolve, thử lại thành công và không gọi clipboard trước click.
- Hồi quy: `npm test` đạt 4 file/13 test; `npm run typecheck`, `npm run lint`, `npm run build` đều exit 0.
  Log: `clipboard-full-test.log`, `clipboard-typecheck.log`, `clipboard-lint.log`, `clipboard-build.log`.
- Không log IOC/lỗi thô, không đọc clipboard, không tự điều hướng và không thêm fallback. Lỗi dùng `role=alert`,
  thành công dùng `role=status`; thông báo có bản VI/EN.
- **UNVERIFIED:** không chạy lại trình duyệt vì test tự động đã tái hiện trực tiếp boundary Clipboard API còn
  bề mặt browser không cung cấp cách tái hiện permission reject hoặc resize; viewport thật 360/1440 vẫn chưa kiểm.
