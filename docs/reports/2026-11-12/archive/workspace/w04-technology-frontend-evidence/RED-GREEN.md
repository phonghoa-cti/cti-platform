# W04 Technology Frontend — bằng chứng RED → GREEN

Ngày chạy: 11/11/2026 (Asia/Saigon). Worktree: `cti-w04-technology-frontend`.

## RED đã quan sát trước mã sản phẩm

| Chu kỳ | Lệnh focused | Kết quả RED đúng nguyên nhân |
|---|---|---|
| Provider + HTTP ban đầu | `npm test -- --run tests/technologies.test.ts tests/technologies-http.test.ts` | Exit 1; 2 suite fail vì chưa có `@/data/technologies` và `@/data/technologies-http`. |
| Parser technology fields | `npm test -- --run tests/technologies-http.test.ts` | Exit 1; 5 fail, 29 pass: parser cũ chấp nhận leading/trailing whitespace, blank và Unicode control/format. |
| Đổi provider khi mutation đang chờ | `npm test -- --run tests/technology-panel.test.tsx -t "provider change"` | Exit 1; 3 fail, 1 pass, 16 skipped: `saving` cũ khóa nút thêm của provider mới. |
| Gỡ provider tùy chọn | `npm test -- --run tests/technology-panel.test.tsx -t "falls back"` | Exit 1; 1 fail, 19 skipped: tab domain chưa được chọn lại. |
| Khóa trong lúc GET đối soát | `npm test -- --run tests/technology-panel.test.tsx -t "locks after"` | Exit 1; 1 fail, 19 skipped: nút thêm mở lại trước khi GET hoàn tất. |
| Quay lại cùng tab domain | `npm test -- --run tests/technology-panel.test.tsx -t "shows technology only"` | Exit 1; 1 fail, 19 skipped: `type` không đổi nên effect không reload, màn kẹt loading. |

Lần RED đầu tiên cũng phát hiện dependency copy mới chỉ có 6/334 mục. Đây là lỗi môi trường, không tính là RED hành vi; dependency sau đó được liên kết cục bộ từ tree W04 hiện có, không cài gói và không sửa lockfile.

## GREEN tương ứng

- Provider/HTTP: 2 file, 29/29 pass sau implementation đầu tiên.
- Parser strict: 34/34 pass sau khi bắt buộc display string đã trim và từ chối Unicode `Cc/Cf/Cs`.
- Provider switch: 4/4 selected pass sau khi reset form/notice/loading/saving theo context owner.
- Provider removal: 1/1 selected pass.
- Unknown reconcile: 1/1 selected pass; GET đang chờ vẫn giữ khóa, mutation không gửi lại.
- Quay lại cùng loại asset: 1/1 selected pass sau khi chỉ gọi lại GET, không replay mutation.
- GREEN cuối toàn nhóm focused: 6 file, 111/111 pass.
