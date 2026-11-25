# Kết quả WEB-W05-PREVIEW

Trạng thái: **PASS cục bộ**, ngoại trừ kiểm viewport thật 360/1440 ghi **UNVERIFIED** bên dưới.

## Rework R1 — clipboard (11/11/2026)

- Commit: `9b10223d90e529432d976177e14fdf2b6ce46bb7`
- Commit message: `fix(portal): handle clipboard copy failures`
- Diff: 6 file, 104 dòng thêm, 6 dòng xóa; chỉ component/messages/test R1 và hai đoạn tài liệu được giao.
- Clipboard API không có hoặc `writeText()` reject đều hiện lỗi VI/EN bằng `role=alert`; Promise được bắt nên không
  còn unhandled rejection. Chỉ hiện `role=status` và nhãn “Đã sao chép/Copied” sau khi Promise resolve; người dùng
  có thể bấm lại để thử lại.
- Không log IOC/lỗi thô, không đọc clipboard, không tự điều hướng, không fallback, không nối API/auth/OpenCTI.
- TDD đỏ: `frontend-evidence/clipboard-red-test.log` — 2/5 test fail, 2 unhandled rejection, exit 1.
- TDD xanh: `frontend-evidence/clipboard-green-test.log` — 5/5 test pass, exit 0.
- Cổng cuối: `npm test` 4 file/13 test pass; typecheck/lint/build đều exit 0; `git diff --check` exit 0.
  Log: `clipboard-full-test.log`, `clipboard-typecheck.log`, `clipboard-lint.log`, `clipboard-build.log`.
- **UNVERIFIED:** không chạy lại browser cho permission clipboard vì bề mặt browser không có khả năng tái hiện
  permission reject; viewport thật 360/1440 vẫn chưa có resize hợp lệ. Test tự động đã tái hiện trực tiếp cả hai
  boundary API vắng mặt và Promise reject.

## Git và phạm vi ban đầu

- Nhánh: `feat/portal-w05-preview-20261110`
- Base: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
- Commit: `be364bd87cd87a86b37d83e8a74e1ff3583ea7ec`
- Commit message: `feat(portal): add W05 draft preview`
- Diff: 30 file, 9.262 dòng thêm; chỉ `portal/web/**`, đoạn task trong `docs/PROGRESS.md` và
  `docs/ai-log/web-w05-preview.md`.
- Working tree sau commit: sạch. Không push, PR, merge hay deploy.

## Kết quả chính

- Next.js `/duyet`; `/` chuyển hướng 307 sang `/duyet`.
- Adapter riêng đọc bản sao đúng ba fixture tổng hợp, kiểm shape/ID và báo lỗi thay vì đổi thành hàng đợi rỗng.
- Hàng đợi chọn draft; metadata, nguồn text-only, allowlist, rejected, warning/injection và empty state.
- Evidence cắt theo Unicode code point bằng `Array.from`; chọn IOC làm nổi quote và chuyển focus tới `mark`.
- IOC defang, không link; chỉ copy giá trị gốc khi bấm. Không `dangerouslySetInnerHTML`.
- VI mặc định, EN hoạt động; messages tách `messages/vi.json` và `messages/en.json`.
- Nút duyệt vô hiệu với giải thích rõ; không request ghi, auth giả hoặc OpenCTI giả.

## Phiên bản và nguồn chính thức

- Next.js `16.4.6`: https://nextjs.org/support-policy
- React/React DOM `19.3.1`: https://react.dev/versions và https://react.dev/community/versioning-policy
- Tailwind CSS/PostCSS `4.3.5`: https://tailwindcss.com/blog/tailwindcss-v4-3
- TypeScript `6.0.3` được ghim vì eslint-config-next hiện chưa hỗ trợ TypeScript 7.
- Lockfile: `portal/web/package-lock.json`; không dùng beta, `--force`, chart hoặc auth package.

## Kiểm tra commit preview ban đầu (`be364bd`)

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `npm test` | 0 | 4 file, 11 test pass |
| `npm run typecheck` | 0 | không lỗi |
| `npm run lint` | 0 | 0 error, 0 warning |
| `npm run build` | 0 | Next production build; `/` và `/duyet` static |
| `git diff --cached --check` trước commit | 0 | không whitespace error |

TDD đỏ: `frontend-evidence/red-test.log` ghi 3 suite thất bại vì module sản phẩm chưa tồn tại trước triển khai.
Log xanh: `frontend-evidence/npm-test.log`, `frontend-evidence/build.log`.

## Bằng chứng trình duyệt thật

- Bề mặt browser được cấp: viewport `1280×720`, DPR 1.
- Đã chọn draft #2 và #1; kiểm warning/allowlist/rejected; đổi VI ↔ EN; bấm evidence.
- Đọc lại DOM sau bấm evidence: `activeElement=MARK.evidence-highlight`, quote emoji đầy đủ;
  `document.querySelectorAll('a').length=0`; nút duyệt `disabled=true`.
- Ảnh: `frontend-evidence/desktop-1280-vi-warning.png` (1280×1126 full-page) và
  `frontend-evidence/desktop-1280-en-evidence.png` (1280×861 full-page).
- `/` quan sát 307, `/duyet` 200. Server cổng 3002 đã dừng; không còn listener.

**UNVERIFIED:** công cụ browser không có điều khiển viewport nên chưa có kiểm/chụp trình duyệt thật đúng 360 px và
1440 px. CSS có breakpoint mobile, thứ tự nguồn trước items và đã qua static review, nhưng không được ghi là bằng
chứng hiển thị thật. Chưa nối HTTP/backend, xác thực, quyền Analyst/Admin, quyết định duyệt hay OpenCTI.

## Chạy lại

```powershell
cd portal/web
npm ci
npm test
npm run typecheck
npm run lint
npm run build
npm run dev -- --port 3002
```

Mở `http://localhost:3002/duyet`.

## Học thêm

- **Unicode code point:** JavaScript phải dùng `Array.from` để span Python không lệch khi văn bản có emoji.
- **Defang:** đổi IOC thành dạng không bấm được như `evil[.]example`, nhưng vẫn giữ giá trị gốc cho thao tác copy.
- **Human-in-the-loop:** AI chỉ đề xuất; quyết định ghi cần backend xác thực, quyền và audit nên preview không giả lập.
- **TDD:** test đỏ chứng minh ca kiểm có thể bắt lỗi trước khi code tối thiểu làm nó xanh.
