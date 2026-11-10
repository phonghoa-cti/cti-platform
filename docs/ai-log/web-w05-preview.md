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
